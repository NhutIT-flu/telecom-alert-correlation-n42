# THIẾT KẾ KỸ THUẬT — N4.2

**Mã:** VNPT-NET-N42-TDD · **Baseline:** 03/11/2026 · **Trạng thái:** Thiết kế kỹ thuật cho dự án doanh nghiệp UTH × VNPT NET; bản hiện tại chưa phải hồ sơ chứng nhận production.  
Đọc cùng `ARCHITECTURE_DESIGN.md`, `DATA_AND_API_DESIGN.md` và `SYSTEM_REQUIREMENTS_AND_USE_CASES.md`.

## 1. Stack và hiện trạng code

- Baseline W1: Python/FastAPI với duy nhất `GET /api/health` để xác nhận process khởi động.
- Các nhánh tính năng có thể đi trước nhánh chính. Ref N42-14 tại `671a7fd` có route REST nhận vào RAM. TC-ING-016 kiểm lỗi queue đầy trên commit sửa. Theo dõi trạng thái từng module và bằng chứng tích hợp trên Jira. TCP syslog chỉ thêm sau quyết định phạm vi.
- `docker/init-db.sql` chỉ bật extension TimescaleDB; chưa có migration, bảng nghiệp vụ, seed hoặc repository runtime.
- Xem `DATA_AND_API_DESIGN.md` để tra route theo commit, phiên bản OpenAPI đề xuất và điều kiện sử dụng.

## 2. Module và ownership

| Module | Trách nhiệm | Owner |
|---|---|---|
| M1 | Receiver/ingestion adapters cho UDP, REST và file; raw envelope, validation. TCP là mở rộng có điều kiện sau quyết định phạm vi. | Phạm Hoàng Long (BE1) |
| M2 | Parser/vendor mapping/normalized event | Phạm Tấn Thành (BE2), phối hợp BE1 về raw contract |
| M3 | Bounded queue, batch, backpressure | Phạm Tấn Thành (BE2) |
| M4 | DB repository/migrations/index/retention | Phạm Tấn Thành (BE2) |
| M5 | Rule schema, version, validation và cấu hình luật | Nguyễn Duy Minh (BE3) |
| M6 | Correlation/grouping, incident lifecycle, evidence và API | Nguyễn Duy Minh (BE3) |
| M7 | Operator dashboard theo API contract | Lê Khắc Huy (FE) |
| M8 | Fixtures, scenario runner, load/evidence | Ngô Châu Kiệt (QA) |
| Project | Plan, decisions, acceptance coordination | Phạm Minh Nhựt (TL/PM) |

## 3. Pipeline đích

`Transport Adapter → Input Guard → Raw Envelope → Parser → Validated AlertEvent → Bounded Queue → Correlation + Persistence → Query API → Dashboard`

- Adapter ghi nguồn, received time và monotonic timestamp đo latency.
- Parser không thực hiện I/O; giữ raw và ghi parse status.
- Queue capacity hữu hạn; policy saturation cho UDP/API. TCP chỉ áp dụng sau khi được duyệt phạm vi.
- Nhánh RAM N42-14 enqueue raw trước khi xử lý. Pipeline trên mô tả các bước của thiết kế đích. Với PoC bền vững, hợp đồng N42-62 xác định điều kiện commit và thời điểm phản hồi. QA ghi build, route và policy queue trong từng lần chạy.
- DB batch transaction, bounded retry và idempotency; ack semantics phân biệt accepted/durable.
- Incident giữ rule/version/evidence; quan hệ event–incident dùng bảng nối khi cần nhiều-nhiều.
- UI chỉ truy cập API, không kết nối trực tiếp DB.

## 4. Model và persistence

Baseline W1 chưa có model chuẩn trong code. `n42-ai-kit/docs/INTERFACES.md` chứa schema đề xuất v0.9; TL và các owner liên quan cần chốt tên field/kiểu dữ liệu qua Jira/decision log trước khi code phụ thuộc được merge.

Khi schema được chốt, BE2 tạo migration version hóa và test migration. Chỉ chọn partition key/index sau khi xác nhận schema, phiên bản TimescaleDB và truy vấn dự kiến. Chưa áp retention/compression tự động khi chưa có quyết định và restore test.

## 5. Hiệu năng và phép đo

Các mục tiêu P50<50ms, P99<200ms, 1.000 msg/s trong 1 giờ, CPU ≤60%/4 core, RAM ≤1.5GB, 0.00% observed drops là tiêu chí nghiệm thu phiên bản dự án hiện tại, chưa phải production SLA đã được VNPT cam kết. Bằng chứng cần ghi:

1. Cấu hình máy/container, OS, phiên bản runtime/DB, commit và config.
2. Tốc độ generator, ID gửi/nhận/persisted, duration; phân biệt generator bottleneck.
3. Điểm bắt đầu/kết thúc latency và mẫu đầy đủ để tính percentile.
4. UDP socket/kernel counters và giới hạn quan sát; không kết luận zero loss từ counter không đầy đủ.
5. CPU quota/core, memory scope, warm-up, batch/window, error rate.

Chi tiết pass/fail tại `ACCEPTANCE_CRITERIA.md`, kịch bản tại `TEST_PLAN.md`.

## 6. Security/config

Không commit secret; dùng env có validation. Raw log có thể nhạy cảm nên chỉ synthetic. CORS wildcard chỉ dev; không expose API/DB public. `10.10.0.0/16` là RFC1918 lab private; `203.0.113.0/24` chỉ dành cho documentation.

## 7. Cấu hình chưa được ngầm coi là chốt

Chunk interval, compression/retention, DB connection pool, socket buffer, queue/batch sizes, WebSocket heartbeat/reconnect, TLS và reverse proxy cần ADR, file config và phép đo trước khi ghi là quyết định. Nếu đã có trong config, ghi đúng file/version và xác minh khi chạy.
