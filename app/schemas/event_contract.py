"""Định nghĩa hợp đồng dữ liệu API v1.0 (API & Event Contract v1).

Căn cứ:
  - docs/N42-62_DESIGN.md
  - docs/DATA_AND_API_DESIGN.md
  - n42-ai-kit/docs/INTERFACES.md
"""

from __future__ import annotations

import base64
import ipaddress
import json
from datetime import datetime, timezone
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.alert_event import AlertEvent

SEVERITY_LABELS: dict[int, str] = {
    0: "EMERGENCY",
    1: "ALERT",
    2: "CRITICAL",
    3: "ERROR",
    4: "WARNING",
    5: "NOTICE",
    6: "INFORMATIONAL",
    7: "DEBUG",
}


class EventView(BaseModel):
    """Mô hình dữ liệu thu gọn đại diện cho một sự kiện cảnh báo trả về cho giao diện Dashboard (FE)."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=False,
    )

    id: UUID = Field(description="Định danh duy nhất của sự kiện cảnh báo")
    event_timestamp: datetime = Field(description="Thời điểm xảy ra sự kiện theo log (UTC)")
    received_at: datetime = Field(description="Thời điểm hệ thống tiếp nhận (UTC)")
    source_ip: str = Field(description="Địa chỉ IP nguồn gửi bản tin")
    hostname: str = Field(description="Tên thiết bị mạng phát sinh cảnh báo")
    facility: int = Field(ge=0, le=23, description="Mã phân loại dịch vụ RFC 5424 (0-23)")
    severity: int = Field(ge=0, le=7, description="Mức độ nghiêm trọng RFC 5424 (0-7)")
    severity_label: str = Field(description="Nhãn mức độ nghiêm trọng (CRITICAL, ERROR, WARNING...)")
    vendor: str = Field(description="Hãng sản xuất thiết bị: cisco, huawei, fortinet, linux, unknown")
    program: Optional[str] = Field(default=None, description="Tên tiến trình/tiện ích phát sinh")
    mnemonic: Optional[str] = Field(default=None, description="Mã định danh cảnh báo của hãng")
    category: str = Field(default="unknown", description="Phân loại nghiệp vụ")
    message: str = Field(default="", description="Nội dung thông điệp cảnh báo đã bóc tách")
    parse_status: str = Field(default="parsed", description="Trạng thái bóc tách (parsed hoặc fallback)")

    @field_validator("received_at", "event_timestamp", mode="before")
    @classmethod
    def validate_timezone_aware(cls, v: object) -> datetime:
        if isinstance(v, str):
            v = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if not isinstance(v, datetime):
            raise ValueError("Value must be a datetime object or valid ISO string")
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            raise ValueError("Datetime must be timezone-aware")
        return v.astimezone(timezone.utc)

    @classmethod
    def from_alert_event(cls, event: AlertEvent) -> EventView:
        """Chuyển đổi từ AlertEvent nội bộ sang DTO EventView cho client."""
        return cls(
            id=event.id,
            event_timestamp=event.event_timestamp,
            received_at=event.received_at,
            source_ip=event.source_ip,
            hostname=event.hostname,
            facility=event.facility,
            severity=event.severity,
            severity_label=SEVERITY_LABELS.get(event.severity, "UNKNOWN"),
            vendor=event.vendor,
            program=event.program,
            mnemonic=event.mnemonic,
            category=event.category,
            message=event.message,
            parse_status=event.parse_status,
        )


class EventIngestRequest(BaseModel):
    """Mô hình dữ liệu tiếp nhận một bản tin cảnh báo qua REST Ingest API."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    raw_message: str = Field(
        min_length=1,
        max_length=65535,
        description="Nội dung thô của bản tin syslog (RFC 3164 / RFC 5424)",
    )
    source_ip: Optional[str] = Field(
        default=None,
        description="Địa chỉ IP nguồn (tùy chọn, nếu bỏ trống server sẽ lấy từ socket client)",
    )

    @field_validator("source_ip", mode="before")
    @classmethod
    def validate_optional_ip(cls, v: object) -> Optional[str]:
        if v is None or v == "":
            return None
        if not isinstance(v, str):
            raise ValueError("source_ip must be a string")
        try:
            ip = ipaddress.ip_address(v.strip())
            return str(ip)
        except ValueError as e:
            raise ValueError(f"Invalid IP address: {v}") from e


class EventIngestBatchRequest(BaseModel):
    """Mô hình tiếp nhận nhiều bản tin cảnh báo theo lô (Batch Ingest)."""

    model_config = ConfigDict(extra="forbid")

    items: List[EventIngestRequest] = Field(
        min_length=1,
        max_length=1000,
        description="Danh sách các bản tin cảnh báo cần nạp (tối đa 1000 bản tin mỗi request)",
    )


class EventIngestResponse(BaseModel):
    """Mô hình phản hồi sau khi tiếp nhận bản tin cảnh báo thành công."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["persisted", "queued"] = Field(
        description="Trạng thái tiếp nhận: persisted (ghi CSDL bền vững) hoặc queued (vào hàng đợi RAM)"
    )
    event_id: Optional[UUID] = Field(
        default=None,
        description="Định danh của sự kiện sau khi ghi CSDL thành công (khi status=persisted)",
    )
    receipt_id: Optional[UUID] = Field(
        default=None,
        description="Biên lai tiếp nhận vào hàng đợi (khi status=queued)",
    )
    received_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Thời điểm máy chủ tiếp nhận bản tin (UTC)",
    )


class EventListQuery(BaseModel):
    """Mô hình tham số truy vấn cho endpoint GET /api/v1/events."""

    model_config = ConfigDict(extra="forbid")

    from_time: datetime = Field(description="Mốc thời gian bắt đầu (UTC)")
    to_time: datetime = Field(description="Mốc thời gian kết thúc (UTC)")
    hostname: Optional[str] = Field(default=None, description="Lọc theo tên thiết bị")
    severity: Optional[int] = Field(default=None, ge=0, le=7, description="Lọc theo mức độ nghiêm trọng (0-7)")
    vendor: Optional[str] = Field(default=None, description="Lọc theo hãng thiết bị")
    limit: int = Field(default=50, ge=1, le=500, description="Số lượng bản tin tối đa trên một trang (1-500)")
    cursor: Optional[str] = Field(default=None, description="Con trỏ phân trang của trang trước đó")


class EventListResponse(BaseModel):
    """Mô hình phản hồi danh sách sự kiện kèm con trỏ phân trang cho Dashboard."""

    model_config = ConfigDict(extra="forbid")

    items: List[EventView] = Field(default_factory=list, description="Danh sách các sự kiện cảnh báo")
    next_cursor: Optional[str] = Field(
        default=None,
        description="Con trỏ để tải trang tiếp theo (null nếu đã là trang cuối)",
    )
    has_more: bool = Field(default=False, description="True nếu còn dữ liệu ở các trang tiếp theo")
    total_matched: Optional[int] = Field(default=None, description="Tổng số bản tin khớp bộ lọc (nếu có tính)")


# ==============================================================================
# TIỆN ÍCH MÃ HÓA / GIẢI MÃ CURSOR PHÂN TRANG (Cursor Pagination Helpers)
# ==============================================================================


def encode_cursor(event_timestamp: datetime, event_id: UUID) -> str:
    """Mã hóa cặp (event_timestamp, event_id) thành chuỗi URL-safe Base64 cursor."""
    if event_timestamp.tzinfo is None:
        event_timestamp = event_timestamp.replace(tzinfo=timezone.utc)
    ts_str = event_timestamp.astimezone(timezone.utc).isoformat()
    payload = json.dumps({"ts": ts_str, "id": str(event_id)})
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")


def decode_cursor(cursor_str: str) -> tuple[datetime, UUID]:
    """Giải mã chuỗi Base64 cursor thành cặp (event_timestamp, event_id).

    Raises:
        ValueError: Nếu định dạng cursor không hợp lệ hoặc dữ liệu bị sửa đổi.
    """
    try:
        raw = base64.urlsafe_b64decode(cursor_str.encode("ascii")).decode("utf-8")
        data = json.loads(raw)
        ts = datetime.fromisoformat(data["ts"])
        event_id = UUID(data["id"])
        return ts, event_id
    except Exception as e:
        raise ValueError(f"Invalid pagination cursor: {cursor_str}") from e
