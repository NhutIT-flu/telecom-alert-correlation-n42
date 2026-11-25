# Implementation Plan: Vòng đời cảnh báo
 
**Branch**: `002-alert-lifecycle` là nhãn feature từ setup-plan, chưa xác nhận nhánh Git | **Date**: 2026-11-25 | **Spec**: [spec.md](spec.md)
 
**Input**: Đặc tả hiện có và các tài liệu thiết kế liên quan. Bản plan phục vụ leader review; chưa triển khai ứng dụng.
 
## Summary
 
hai chiều signal/workflow, năm tổ hợp hợp lệ, ACK/CLOSE có quyền và history append-only. Phương án chi tiết ở [lifecycle-design.md](lifecycle-design.md); plan này xác định ranh giới, phụ thuộc, contract và cách kiểm chứng, không lặp lại toàn bộ thuật toán/schema.
 
## Technical Context
 
**Language/Version**: Python 3.12, FastAPI/Pydantic hiện có; service lifecycle chưa có.
 
**Primary Dependencies**: PostgreSQL transaction + API thao tác người theo 005. FastAPI/Pydantic/ruamel.yaml theo repo đã xác minh; PostgreSQL application driver/repository và migration cần quyết định trước implementation.
 
**Storage**: PostgreSQL, theo [001](../001-alert-data-model/data-model.md); alerts, alert_events, alert_state_history.
 
**Testing**: pytest hiện có; chưa có test lifecycle/ACK/CLOSE.
 
**Target Platform**: Docker Compose lab hiện có PostgreSQL 16/TimescaleDB image; Jenkins/CI files hiện có. Chưa khẳng định môi trường đã chạy.
 
**Project Type**: module backend trong hệ thống giám sát syslog.
 
**Performance Goals**: Bộ T01–T39, no-op và race đúng 100%; chưa có SLA đã đo.
 
**Constraints**: ACK/CLOSE trên snapshot với expected_state_version; alert_state_history theo version; không thêm xử lý khắc phục. Không dùng dữ liệu production/secret trong fixture. Chỉ số đã đo phải tách khỏi ước lượng/mục tiêu.
 
**Scale/Scope**: Prototype để trình duyệt; không suy diễn đã có triển khai hay SLA production.
 
## Constitution Check
 
*GATE trước Phase 0 và sau Phase 1: PASS cho bản thiết kế; không phát hiện ngoại lệ cần sửa constitution.*
 
- VIII/VII/VI: active+closed cấm; recovered không tự CLOSE; closed bất biến; timer cần coverage.
- Các nguyên tắc còn lại vẫn áp dụng: không tự cấu hình/khắc phục thiết bị; phân quyền rõ; không ghi kết quả dở hoặc mất syslog đã lưu; không sửa lịch sử closed.
- Governance: application repo đã xác minh trên branch main sạch; docs spec nằm ở thư mục cha ngoài repo. Chưa có ticket N42 cụ thể cho implementation này; plan không tạo branch/commit/PR.
 
## Project Structure
 
### Documentation (this feature)
 
```text
specs/002-alert-lifecycle/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── lifecycle-design.md
├── contracts/
│   └── lifecycle.md
└── quickstart.md
```
 
`tasks.md` thuộc bước $speckit-tasks, không tạo trong plan.
 
### Source Code (application repository)

```text
telecom-alert-correlation-n42/
├── app/models/alert_event.py        # Event đã chuẩn hóa; không là alerts lifecycle
├── app/store/__init__.py            # Chưa có repository alert/history
├── app/api/health.py                # Đã có health
├── frontend/src/types/alert.ts      # Type giao diện đang có
├── frontend/src/pages/CorrelationAlertsPage.tsx
└── tests/                            # Chưa có test lifecycle/ACK/CLOSE
```

**Structure Decision**: Đây là điểm tích hợp đã xác minh, không có module lifecycle/DB table/API ACK-CLOSE trong code hiện tại. Sau duyệt, dự kiến tách service lifecycle backend và tests riêng dưới app/tests theo layout hiện hữu; tên file cụ thể phải gắn ticket và contract với FE/BE2. [Bản đồ code](../003-rule-dispatch-correlation/codebase-mapping.md).
 
## Phase 0: Research and decisions
 
[research.md](research.md) ghi Decision/Rationale/Alternatives và các rủi ro chưa đo. Không còn NEEDS CLARIFICATION bắt buộc cho phương án thiết kế; runtime Python 3.12, CI files và repo path đã xác minh; DB driver, contract chéo nhóm và ngưỡng lab còn phải quyết định trước implementation.
 
## Phase 1: Design and contracts
 
- [data-model.md](data-model.md) ánh xạ entity, validation và transition của feature; tham chiếu schema nguồn 001, không tạo bảng song song.
- [lifecycle-design.md](lifecycle-design.md) là thiết kế kỹ thuật nguồn sở hữu.
- [contracts/](contracts/lifecycle.md) ghi giao tiếp với module khác.
- [quickstart.md](quickstart.md) phân biệt lệnh kiểm tra tài liệu chạy được ngay và tình huống nghiệm thu ứng dụng sau triển khai.
 
**Post-design Constitution Check**: PASS; contract không đổi nguồn sở hữu 001–006, không biến mục tiêu thử thành SLA. Nếu leader thay phạm vi, cập nhật spec/design/plan trước tasks.
 
## Complexity Tracking
 
Không có vi phạm constitution. Phụ thuộc chính: 001 alerts/evidence, 003 engine, 004 outcome, 005 API. Những tối ưu như bảng riêng, broker, nhiều worker hoặc index JSONB đại trà chỉ xét sau đo và review riêng.


