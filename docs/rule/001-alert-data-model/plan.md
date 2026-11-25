# Implementation Plan: Dữ liệu sự kiện và cảnh báo
 
**Branch**: `001-alert-data-model` là nhãn feature từ setup-plan, chưa xác nhận nhánh Git | **Date**: 2026-11-25 | **Spec**: [spec.md](spec.md)
 
**Input**: Đặc tả hiện có và các tài liệu thiết kế liên quan. Bản plan phục vụ leader review; chưa triển khai ứng dụng.
 
## Summary
 
raw-first, bảng chung đa hãng, 8 bảng; event/status/index và giao dịch bảo toàn. Phương án chi tiết ở [data-model.md](data-model.md); plan này xác định ranh giới, phụ thuộc, contract và cách kiểm chứng, không lặp lại toàn bộ thuật toán/schema.
 
## Technical Context
 
**Language/Version**: Python 3.12 theo pyproject.toml/requirements.txt; FastAPI/Pydantic hiện có.
 
**Primary Dependencies**: PostgreSQL, JSONB thuộc tính; FastAPI/Python là stack dự kiến. FastAPI/Pydantic/ruamel.yaml theo repo đã xác minh; PostgreSQL application driver/repository và migration cần quyết định trước implementation.
 
**Storage**: PostgreSQL, theo [001](../001-alert-data-model/data-model.md); 8 bảng chung đã mô tả, không thêm bảng theo hãng.
 
**Testing**: pytest hiện có; chưa có test migration/repository cho schema 001.
 
**Target Platform**: Docker Compose lab hiện có PostgreSQL 16/TimescaleDB image; Jenkins/CI files hiện có. Chưa khẳng định môi trường đã chạy.
 
**Project Type**: module backend trong hệ thống giám sát syslog.
 
**Performance Goals**: 100.000 event và 40 truy vấn; 95/100 trang đầu ≤2 giây là mục tiêu lab chưa đo.
 
**Constraints**: schema dùng chung; không bảng theo hãng; không UNIQUE raw/hash; replay scope tách live. Không dùng dữ liệu production/secret trong fixture. Chỉ số đã đo phải tách khỏi ước lượng/mục tiêu.
 
**Scale/Scope**: Prototype để trình duyệt; không suy diễn đã có triển khai hay SLA production.
 
## Constitution Check
 
*GATE trước Phase 0 và sau Phase 1: PASS cho bản thiết kế; không phát hiện ngoại lệ cần sửa constitution.*
 
- II/VII/VIII/X: raw và normalized cùng ID, không xóa log lỗi; FK RESTRICT, history và checkpoint bền vững.
- Các nguyên tắc còn lại vẫn áp dụng: không tự cấu hình/khắc phục thiết bị; phân quyền rõ; không ghi kết quả dở hoặc mất syslog đã lưu; không sửa lịch sử closed.
- Governance: application repo đã xác minh trên branch main sạch; docs spec nằm ở thư mục cha ngoài repo. Chưa có ticket N42 cụ thể cho implementation này; plan không tạo branch/commit/PR.
 
## Project Structure
 
### Documentation (this feature)
 
```text
specs/001-alert-data-model/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── data-model.md
├── contracts/
│   └── persistence.md
└── quickstart.md
```
 
`tasks.md` thuộc bước $speckit-tasks, không tạo trong plan.
 
### Source Code (application repository)

```text
telecom-alert-correlation-n42/
├── app/models/raw_event.py          # RawEvent trong RAM, đã có
├── app/models/alert_event.py        # AlertEvent UUID, chưa là schema events của 001
├── app/store/__init__.py            # Placeholder, chưa có repository
├── app/api/ingest.py                # Nhận API/file vào queue RAM
├── docker/init-db.sql               # Extension TimescaleDB, chưa có bảng ứng dụng
└── tests/test_api_ingest.py         # Test queue/endpoint hiện hành
```

**Structure Decision**: Đường dẫn trên đã xác minh trong repository `../../telecom-alert-correlation-n42` trên branch `main` sạch. Trước triển khai 001 cần chốt với BE2/TL mapping từ AlertEvent UUID hiện tại sang mô hình events BIGINT/raw-first, migration/versioning và quyền ghi. Không coi queue RAM hoặc init-db.sql là persistence đã có. [Bản đồ code](../003-rule-dispatch-correlation/codebase-mapping.md) ghi phụ thuộc liên module.

Biên bản họp bổ sung hướng đổi tên bảng event/alert, `target_ip` và đánh giá dữ liệu thiếu theo từng loại/rule; [đối chiếu với repo](meeting-schema-alignment.md) nêu các quyết định vật lý còn cần TL/BE2/BE3 xác nhận trước migration.
 
## Phase 0: Research and decisions
 
[research.md](research.md) ghi Decision/Rationale/Alternatives và các rủi ro chưa đo. Không còn NEEDS CLARIFICATION bắt buộc cho phương án thiết kế; runtime Python 3.12, CI files và repo path đã xác minh; DB driver, contract chéo nhóm và ngưỡng lab còn phải quyết định trước implementation.
 
## Phase 1: Design and contracts
 
- [data-model.md](data-model.md) ánh xạ entity, validation và transition của feature; đây là tài liệu nguồn đã có, được giữ nguyên.
- [data-model.md](data-model.md) là thiết kế kỹ thuật nguồn sở hữu.
- [contracts/](contracts/persistence.md) ghi giao tiếp với module khác.
- [quickstart.md](quickstart.md) phân biệt lệnh kiểm tra tài liệu chạy được ngay và tình huống nghiệm thu ứng dụng sau triển khai.
 
**Post-design Constitution Check**: PASS; contract không đổi nguồn sở hữu 001–006, không biến mục tiêu thử thành SLA. Nếu leader thay phạm vi, cập nhật spec/design/plan trước tasks.
 
## Complexity Tracking
 
Không có vi phạm constitution. Phụ thuộc chính: 001 data-model, 002 lifecycle, 003 checkpoint, 005 ingestion, 006 input. Những tối ưu như bảng riêng, broker, nhiều worker hoặc index JSONB đại trà chỉ xét sau đo và review riêng.


