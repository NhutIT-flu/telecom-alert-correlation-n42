# INTERFACES — Hợp đồng giữa các module

**Trạng thái: ĐỀ XUẤT v0.9 — chờ TL chốt trước W4 (28/11).** Sau khi chốt thành v1.0, mọi thay đổi theo skill `change-alertevent-schema`. Các quyết định liên quan: xem `docs/DECISIONS.md` (D-01 … D-05).

## 1. `AlertEvent` (Pydantic v2)

```python
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class AlertEvent(BaseModel):
    id: UUID
    received_at: datetime          # UTC, lúc hệ thống nhận
    event_timestamp: datetime      # UTC, thời điểm sự kiện (từ log)
    source_ip: str
    hostname: str
    facility: int = Field(ge=0, le=23)
    severity: int = Field(ge=0, le=7)   # RFC 5424, xem bảng dưới
    program: str
    message: str
    raw_payload: str
    vendor: str                    # CISCO | HUAWEI | LINUX | RFC3164 | RFC5424 | UNKNOWN
    category: str                  # do BE2 gán khi chuẩn hóa (bảng mapping do BE2 giữ)
```

| severity | Tên | Gợi ý màu trên FE |
|---|---|---|
| 0 | Emergency | đỏ |
| 1 | Alert | đỏ |
| 2 | Critical | đỏ |
| 3 | Error | cam |
| 4 | Warning | vàng |
| 5 | Notice | xanh |
| 6 | Info | xanh |
| 7 | Debug | xám |

## 2. BE1 → BE2: `RawEvent` và pipeline

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

@dataclass(frozen=True, slots=True)
class RawEvent:
    payload: bytes
    source_ip: str
    received_at: datetime                       # UTC
    channel: Literal["udp", "tcp", "file", "api"]
```

BE1 chỉ tạo `RawEvent` và đưa vào `asyncio.Queue` có giới hạn. BE2 sở hữu pipeline:

```python
class Pipeline:
    async def process(self, raw: RawEvent) -> "AlertEvent | QuarantineRecord": ...
    def subscribe(self, handler: "Callable[[AlertEvent], Awaitable[None]]") -> None: ...
```

Gói không parse được thì trả `QuarantineRecord` (lưu lại để kiểm tra), **không ném exception** làm gián đoạn luồng.

## 3. Parser: `BaseNormalizer`

```python
from abc import ABC, abstractmethod

class ParseError(Exception): ...

class BaseNormalizer(ABC):
    vendor: str

    @abstractmethod
    def can_parse(self, raw: RawEvent) -> bool: ...

    @abstractmethod
    def parse(self, raw: RawEvent) -> AlertEvent: ...   # lỗi → ParseError
```

## 4. Lưu trữ: `EventStore`

```python
from typing import Protocol, Sequence

class EventQuery(BaseModel):
    start: datetime | None = None
    end: datetime | None = None
    hostname: str | None = None
    source_ip: str | None = None
    severity: list[int] | None = None
    q: str | None = None            # tìm full-text trong message
    limit: int = 100
    cursor: str | None = None

class EventStore(Protocol):
    async def add_many(self, events: Sequence[AlertEvent]) -> int: ...
    async def search(self, query: EventQuery) -> "Page[AlertEvent]": ...
    async def count(self, query: EventQuery) -> int: ...
```

W1–W4: `InMemoryEventStore` (ring buffer). W5–W6: `TimescaleDbEventStore`.

## 5. BE2 → BE3: nhận sự kiện

BE3 đăng ký handler qua `Pipeline.subscribe(...)` và giữ cửa sổ trượt trong bộ nhớ. Khi khởi động lại, nạp lại cửa sổ gần nhất bằng `EventStore.search`.

## 6. API cho FE (đề xuất, BE2 chốt trong OpenAPI tại `/docs`)

Đề xuất v0.9 từng dùng `GET /api/events`. Review.2 đề xuất `GET /api/v1/events`, `from/to` bắt buộc, filter thiết bị `hostname` và phản hồi `items` (EventView), `next_cursor`, `has_more`. N42-62 xác nhận tham số và schema trước N42-67/N42-34. Xem [Thiết kế dữ liệu/API](../../docs/DATA_AND_API_DESIGN.md).
Trên baseline W1 hiện chỉ có `GET /api/health`. Các endpoint ingest/query/simulate và correlation trong tài liệu này là đề xuất hoặc ticket chưa triển khai; FE chỉ đấu nối endpoint có trong OpenAPI sau khi backend bàn giao.
FE **không** dùng endpoint nào ngoài OpenAPI của backend.

## 7. DDL tham khảo (TimescaleDB)

```sql
CREATE TABLE alert_events (
    id UUID NOT NULL,
    received_at TIMESTAMPTZ NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    source_ip TEXT NOT NULL,
    hostname TEXT NOT NULL,
    facility SMALLINT NOT NULL CHECK (facility BETWEEN 0 AND 23),
    severity SMALLINT NOT NULL CHECK (severity BETWEEN 0 AND 7),
    program TEXT NOT NULL,
    message TEXT NOT NULL,
    raw_payload TEXT NOT NULL,
    vendor TEXT NOT NULL,
    category TEXT NOT NULL,
    PRIMARY KEY (id, event_timestamp)       -- khóa chính phải chứa cột phân vùng
);
SELECT create_hypertable('alert_events', 'event_timestamp');
CREATE INDEX ON alert_events (event_timestamp DESC, hostname, severity);
```

Bảng của BE3: `correlation_rules` (tham số JSONB) và `grouped_incidents`.
