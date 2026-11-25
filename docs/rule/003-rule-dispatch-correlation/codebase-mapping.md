# Bản đồ code và khung module rule đề xuất

**Ngày đối chiếu:** 2026-11-25. **Ứng dụng:** `C:/Projects/vnpt/telecom-alert-correlation-n42`, Git branch `main`, working tree sạch lúc đọc. Tài liệu này phân biệt **đã có** và **dự kiến**; không thay đổi code ứng dụng. Các hợp đồng trong `n42-ai-kit/docs/INTERFACES.md` còn đề xuất v0.9, cần TL và owner BE1/BE2/BE3 thống nhất trước khi code liên module theo `AGENTS.md`.

## 1. File đã có và vai trò hiện tại

| Đường dẫn trong repo ứng dụng | Hiện trạng xác minh | Liên quan đặc tả |
|---|---|---|
| `app/models/raw_event.py` | RawEvent dataclass với bytes/source_ip/received_at/channel | 001/005, đầu tiếp nhận |
| `app/receiver/server.py`, `protocol.py`, `metrics.py` | UDP receiver, queue RAM và số đo tiếp nhận | 005 |
| `app/api/ingest.py`, `app/models/ingest.py` | API/file ingest vào queue RAM; phản hồi 201 sau enqueue, chưa sau DB commit | 001/005, gap raw-first |
| `app/services/parser.py` | RFC3164 Cisco/Huawei/Linux; fallback và không có interface semantic mapping/Juniper | 005/006, gap canonical |
| `app/models/alert_event.py` | AlertEvent UUID, event_timestamp không nullable, parse parsed/fallback, không device_id/interface fields | 001/005/006, contract hiện khác spec |
| `app/models/rule_config.py`, `app/services/rule_config_loader.py` | Pydantic/YAML rule catalog và kiểm tra cấu hình | 003/004, có thể tái sử dụng sau mapping |
| `app/services/rules.yaml` | 3 rule mẫu LinkFlap/PSU/BGP đều disabled; LinkFlap group_by hostname/interface | 004, không phải handler đã chạy |
| `app/main.py` | Nạp catalog trong FastAPI lifespan; chưa có worker tương quan tách riêng | 003 |
| `app/store/__init__.py` | Placeholder, chưa có repository | 001/003 |
| `docker/init-db.sql` | Chỉ tạo extension TimescaleDB và DB SonarQube, chưa tạo 8 bảng ứng dụng | 001 |
| `frontend/src/pages/CorrelationAlertsPage.tsx`, `src/types/alert.ts`, `src/services/` | UI/type/service frontend hiện có; cần đối chiếu API thật | 002/005 |
| `tests/test_rules_config.py`, `test_rule_startup.py` | Test catalog/startup, không kiểm tra correlation/LinkFlap runtime | 003/004 |
| `tests/test_api_ingest.py`, `test_parser.py`, `test_udp_ingestion.py` | Test đầu vào hiện hành, chưa chứng minh raw DB commit hoặc canonical Juniper | 001/005/006 |

Stack thực tế: Python 3.12 (pyproject/requirements), FastAPI/Pydantic v2, ruamel.yaml, pytest; PostgreSQL 16/TimescaleDB qua Docker Compose; frontend React 19/Vite. Chưa thấy PostgreSQL application repository/driver trong requirements hoặc migration các bảng của 001. Code đã có nhiều hơn mô tả baseline W1 trong README/AGENTS; cần cập nhật trạng thái tài liệu repo theo ticket, không coi các module còn thiếu là đã hoàn thành.

## 2. Các bất đồng contract cần leader và owner quyết định

| Chủ đề | Code hiện có | Thiết kế 001–006 | Quyết định trước code phụ thuộc |
|---|---|---|---|
| ID event | AlertEvent UUID tạo khi parse; API ingest UUID khi enqueue | events.id BIGINT ổn định từ raw commit | BE1/BE2/TL chọn mapping ID, tránh hai ID không liên kết |
| Trạng thái parse | parsed/fallback; fallback event_timestamp=received_at | pending/success/partial/failed; unknown time=NULL và guard | BE2/TL chốt adapter/version, không coi fallback time là giờ thiết bị |
| Giao nhận | `Pipeline.subscribe` v0.9; queue RAM hiện tại | Worker tự polling event đã commit | TL/BE1/BE2/BE3 chốt migration; không nối handler trực tiếp vào queue chưa bền vững rồi tuyên bố đạt spec |
| Field LinkFlap | YAML hostname/interface/link_state, match Cisco mnemonic | device_id/interface_name/interface_state/interface_layer, hãng dùng chung | BE2/BE3 chốt canonical mapping; không bật rule hiện tại khi thiếu các field đó |
| Hãng lab | Parser Cisco/Huawei/Linux | Cisco/Juniper cho fixture đầu 005/006 | TL/BE2 xác định scope parser và fixture Juniper; không ghi là đã hỗ trợ |
| Cấu hình | rule_id/window/threshold/group_by/match/count/action | rules revision/handler_key/definition/recovery/outcome | BE3/TL chọn versioned migration/adapter; không sửa YAML mẫu âm thầm |
| DB/lifecycle | Chưa có bảng/alert API/worker | 8 bảng, two-axis lifecycle, receipt/checkpoint/guard | BE2/BE3/TL chốt migration, owner và thứ tự triển khai |
| Biên bản họp: tên bảng/target_ip/đầy đủ | Tài liệu repo đề xuất `alert_events`/`grouped_incidents`, model chưa có target_ip, fallback điền giá trị thay | Tên logic `events`/`alerts`, raw-first, partial/diagnostic theo từng rule | Xem [đối chiếu chi tiết](../001-alert-data-model/meeting-schema-alignment.md); exact tên vật lý và nơi lưu target_ip cần TL/BE2/BE3 chốt |
| Ingest API | `/api/v1/events/ingest`, `/import-file` | 005 nêu surface dự kiến `/ingest/events`, `/ingest/files` | BE1/TL xác nhận route chính thức, giữ contract FE/QA |

Đây là **xung đột thiết kế với baseline code**, không là lỗi implementation trong ticket hiện hành. Chưa sửa bất kỳ file ứng dụng nào. User đã để mở chống trùng giữa hai ID tiếp nhận khác nhau; không đưa nó thành blocker của prototype.

## 3. Khung file đề xuất cho module rule (chưa tạo)

```text
app/
├── correlation/
│   ├── __init__.py
│   ├── contracts.py          # NormalizedEvent, RuleResult, Context, disposition
│   ├── registry.py           # nạp revision, đăng ký event_type, owner resolution
│   ├── dispatcher.py         # candidate/filter/group key, per-rule input check
│   ├── worker.py             # poll, lock, receipt, retry, transaction boundary
│   ├── scheduler.py          # watermark/deadline, event-before-timer tie
│   ├── state_cache.py        # group state, checkpoint/cold-load, generation
│   ├── cleanup.py            # prune/evict guard chung
│   ├── history.py            # bounded late correction/rebuild context
│   └── handlers/
│       ├── __init__.py
│       ├── base.py           # metadata + 5 thao tác
│       └── link_flap.py      # chỉ rule nghiệp vụ đầu
├── services/
│   ├── rule_config_loader.py # giữ file hiện có, bổ sung migration có version
│   └── rules.yaml            # giữ disabled cho đến khi contract được duyệt
└── store/
    ├── __init__.py
    └── correlation.py        # repository/transaction theo schema đã duyệt
tests/
├── test_correlation_contract.py
├── test_correlation_worker.py
├── test_link_flap.py
└── fixtures/correlation/
```

Đây là **đề xuất phân chia trách nhiệm**, không yêu cầu tạo tất cả file ngay. Khi lập tasks, có thể gộp file để giữ prototype nhỏ; không được gộp mất ranh giới logic/transaction. Worker nên chạy như tiến trình riêng, không nhân state khi FastAPI có nhiều process; cách entrypoint và DB driver phải chốt theo repo/ticket.

## 4. Thứ tự tích hợp đề xuất

1. TL/BE2/BE3 duyệt contract event, ID, thời gian, scope, field interface và nguồn cấu hình; cập nhật tài liệu interface/Jira/RTM theo quy trình repo.
2. BE1/BE2 hoàn thiện raw commit, canonical parser, persistence/migration và khả năng tra event pending. Đừng để phản hồi enqueue bị hiểu là DB accepted.
3. BE3 làm adapter/projection có kiểu, registry/dispatcher rồi LinkFlap handler trên fixture; sau đó worker receipt/checkpoint/lifecycle/timer/guard, test restart và tải.
4. FE đấu nối API cảnh báo/health thực tế sau khi backend công bố contract; QA đối chiếu C/LF/I cases và số đo.

Repo `AGENTS.md` và `n42-ai-kit/AGENTS.md` yêu cầu ticket, owner, acceptance/test case và RTM trước khi code thay đổi hành vi. Tài liệu này không tạo file ứng dụng hoặc tự nhận ticket/branch/PR.
