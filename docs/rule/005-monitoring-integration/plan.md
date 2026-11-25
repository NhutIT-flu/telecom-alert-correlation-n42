# Implementation Plan: Tích hợp giám sát
 
**Branch**: `005-monitoring-integration` là nhãn feature từ setup-plan, chưa xác nhận nhánh Git | **Date**: 2026-11-25 | **Spec**: [spec.md](spec.md)
 
**Input**: Đặc tả hiện có và các tài liệu thiết kế liên quan. Bản plan phục vụ leader review; chưa triển khai ứng dụng.
 
## Summary
 
UDP/API/file→raw→normalize→worker polling→API/frontend snapshot; auth lab và health. Phương án chi tiết ở [integration-design.md](integration-design.md); plan này xác định ranh giới, phụ thuộc, contract và cách kiểm chứng, không lặp lại toàn bộ thuật toán/schema.
 
## Technical Context
 
**Language/Version**: Python 3.12, FastAPI/Pydantic backend; React 19/Vite frontend theo package.json.
 
**Primary Dependencies**: FastAPI/Pydantic backend, React 19/Vite frontend, Docker Compose PostgreSQL/TimescaleDB hiện có. PostgreSQL application driver/repository và migration chưa có.
 
**Storage**: PostgreSQL, theo [001](../001-alert-data-model/data-model.md); events và pipeline_runtime_status cùng bảng cảnh báo chung.
 
**Testing**: pytest có test UDP/API/parser; frontend có build/lint scripts, chưa xác minh E2E.
 
**Target Platform**: Docker Compose lab hiện có PostgreSQL 16/TimescaleDB image; Jenkins/CI files hiện có. Chưa khẳng định môi trường đã chạy.
 
**Project Type**: dịch vụ backend và giao diện giám sát.
 
**Performance Goals**: I01–I15; chu kỳ frontend 1 giây là mục tiêu thử, không SLA đầu-cuối.
 
**Constraints**: giới hạn đầu vào thử lab; API/health/replay tách quyền; frontend stale/reload. Không dùng dữ liệu production/secret trong fixture. Chỉ số đã đo phải tách khỏi ước lượng/mục tiêu.
 
**Scale/Scope**: Prototype để trình duyệt; không suy diễn đã có triển khai hay SLA production.
 
## Constitution Check
 
*GATE trước Phase 0 và sau Phase 1: PASS cho bản thiết kế; không phát hiện ngoại lệ cần sửa constitution.*
 
- I/II/III/VI/VII/X: raw-first, lịch sử scope riêng, quyền rõ, coverage không giả UDP giao đủ.
- Các nguyên tắc còn lại vẫn áp dụng: không tự cấu hình/khắc phục thiết bị; phân quyền rõ; không ghi kết quả dở hoặc mất syslog đã lưu; không sửa lịch sử closed.
- Governance: application repo đã xác minh trên branch main sạch; docs spec nằm ở thư mục cha ngoài repo. Chưa có ticket N42 cụ thể cho implementation này; plan không tạo branch/commit/PR.
 
## Project Structure
 
### Documentation (this feature)
 
```text
specs/005-monitoring-integration/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── integration-design.md
├── contracts/
│   └── integration.md
└── quickstart.md
```
 
`tasks.md` thuộc bước $speckit-tasks, không tạo trong plan.
 
### Source Code (application repository)

```text
telecom-alert-correlation-n42/
├── app/receiver/{server,protocol,metrics}.py  # UDP receiver đã có
├── app/api/{ingest,health}.py                  # API ingest/health đã có
├── app/models/{raw_event,alert_event,ingest}.py
├── app/services/parser.py                    # Parser RFC3164 hiện hành
├── app/store/__init__.py                      # Repository chưa có
├── frontend/src/{pages,services,types}/       # React/Vite UI đã có
├── docker-compose.yml                        # PostgreSQL/TimescaleDB lab
└── tests/{test_udp_ingestion,test_api_ingest,test_parser}.py
```

**Structure Decision**: Đường dẫn đã xác minh, nhưng API hiện enqueue RAM và trả success trước DB commit, file hiện đọc toàn bộ vào RAM, parser chưa Juniper/canonical interface; frontend hiện có nhiều fixture/mock. Đây là gap giữa 005 và code, không tự sửa khi chỉ cập nhật plan. [Bản đồ code](../003-rule-dispatch-correlation/codebase-mapping.md).
 
## Phase 0: Research and decisions
 
[research.md](research.md) ghi Decision/Rationale/Alternatives và các rủi ro chưa đo. Không còn NEEDS CLARIFICATION bắt buộc cho phương án thiết kế; runtime Python 3.12, CI files và repo path đã xác minh; DB driver, contract chéo nhóm và ngưỡng lab còn phải quyết định trước implementation.
 
## Phase 1: Design and contracts
 
- [data-model.md](data-model.md) ánh xạ entity, validation và transition của feature; tham chiếu schema nguồn 001, không tạo bảng song song.
- [integration-design.md](integration-design.md) là thiết kế kỹ thuật nguồn sở hữu.
- [contracts/](contracts/integration.md) ghi giao tiếp với module khác.
- [quickstart.md](quickstart.md) phân biệt lệnh kiểm tra tài liệu chạy được ngay và tình huống nghiệm thu ứng dụng sau triển khai.
 
**Post-design Constitution Check**: PASS; contract không đổi nguồn sở hữu 001–006, không biến mục tiêu thử thành SLA. Nếu leader thay phạm vi, cập nhật spec/design/plan trước tasks.
 
## Complexity Tracking
 
Không có vi phạm constitution. Phụ thuộc chính: 001 schema, 002 ACK/CLOSE, 003 worker, 004 LinkFlap, 006 boundary. Những tối ưu như bảng riêng, broker, nhiều worker hoặc index JSONB đại trà chỉ xét sau đo và review riêng.


