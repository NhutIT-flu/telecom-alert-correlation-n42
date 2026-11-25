# Implementation Plan: Điều phối và tương quan rule
 
**Branch**: `003-rule-dispatch-correlation` là nhãn feature từ setup-plan, chưa xác nhận nhánh Git | **Date**: 2026-11-25 | **Spec**: [spec.md](spec.md)
 
**Input**: Đặc tả hiện có và các tài liệu thiết kế liên quan. Bản plan phục vụ leader review; chưa triển khai ứng dụng.
 
## Summary
 
một worker, registry/dispatcher, handler contract, batch/checkpoint/receipt, coverage và cleanup. Phương án chi tiết ở [engine-design.md](engine-design.md); plan này xác định ranh giới, phụ thuộc, contract và cách kiểm chứng, không lặp lại toàn bộ thuật toán/schema.
 
## Technical Context
 
**Language/Version**: Python 3.12; ruamel.yaml/Pydantic đang dùng cho config, worker chưa có.
 
**Primary Dependencies**: Python worker + PostgreSQL; FastAPI chỉ đọc/điều khiển qua 005. FastAPI/Pydantic/ruamel.yaml theo repo đã xác minh; PostgreSQL application driver/repository và migration cần quyết định trước implementation.
 
**Storage**: PostgreSQL, theo [001](../001-alert-data-model/data-model.md); events, rules, rule_group_states, alerts/evidence/history, pipeline_runtime_status.
 
**Testing**: pytest có test config/startup; chưa có test worker/handler/correlation.
 
**Target Platform**: Docker Compose lab hiện có PostgreSQL 16/TimescaleDB image; Jenkins/CI files hiện có. Chưa khẳng định môi trường đã chạy.
 
**Project Type**: module backend trong hệ thống giám sát syslog.
 
**Performance Goals**: C01–C48; p95 2 giây/p99 5 giây sau đủ chốt trên tải lab là mục tiêu thử.
 
**Constraints**: LinkFlap là rule nghiệp vụ đầu; multi-rule bằng handler thử; guard 006 bền vững trước timer. Không dùng dữ liệu production/secret trong fixture. Chỉ số đã đo phải tách khỏi ước lượng/mục tiêu.
 
**Scale/Scope**: Prototype để trình duyệt; một worker tương quan, một rule nghiệp vụ LinkFlap đầu tiên.
 
## Constitution Check
 
*GATE trước Phase 0 và sau Phase 1: PASS cho bản thiết kế; không phát hiện ngoại lệ cần sửa constitution.*
 
- III–X: state theo nhóm, giờ nguồn, atomic commit, fail-stop, giới hạn tài nguyên, không timer/interface.
- Các nguyên tắc còn lại vẫn áp dụng: không tự cấu hình/khắc phục thiết bị; phân quyền rõ; không ghi kết quả dở hoặc mất syslog đã lưu; không sửa lịch sử closed.
- Governance: application repo đã xác minh trên branch main sạch; docs spec nằm ở thư mục cha ngoài repo. Chưa có ticket N42 cụ thể cho implementation này; plan không tạo branch/commit/PR.
 
## Project Structure
 
### Documentation (this feature)
 
```text
specs/003-rule-dispatch-correlation/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── engine-design.md
├── contracts/
│   └── handler-worker.md
└── quickstart.md
```
 
`tasks.md` thuộc bước $speckit-tasks, không tạo trong plan.
 
### Source Code (application repository)

```text
telecom-alert-correlation-n42/
├── app/models/rule_config.py        # Pydantic config rule hiện có
├── app/services/rule_config_loader.py
├── app/services/rules.yaml          # 3 rule mẫu đều disabled
├── app/main.py                      # Nạp catalog trong FastAPI lifespan
├── app/models/alert_event.py        # Event hiện tại, khác projection 005/006
├── app/store/__init__.py            # Chưa có DB repository
├── tests/test_rules_config.py
└── tests/test_rule_startup.py
```

**Structure Decision**: Chưa có dispatcher, worker, handler LinkFlap, checkpoint, scheduler hoặc CleanupManager. [Bản đồ code và file dự kiến](codebase-mapping.md) chỉ rõ khung module đề xuất; không tạo implementation trước khi ticket/contract được TL và owner duyệt. Startup catalog hiện ở FastAPI; worker riêng đòi bước tách có kế hoạch.
 
## Phase 0: Research and decisions
 
[research.md](research.md) ghi Decision/Rationale/Alternatives và các rủi ro chưa đo. Không còn NEEDS CLARIFICATION bắt buộc cho phương án thiết kế; runtime Python 3.12, CI files và repo path đã xác minh; DB driver, contract chéo nhóm và ngưỡng lab còn phải quyết định trước implementation.
 
## Phase 1: Design and contracts
 
- [data-model.md](data-model.md) ánh xạ entity, validation và transition của feature; tham chiếu schema nguồn 001, không tạo bảng song song.
- [engine-design.md](engine-design.md) là thiết kế kỹ thuật nguồn sở hữu.
- [contracts/](contracts/handler-worker.md) ghi giao tiếp với module khác.
- [quickstart.md](quickstart.md) phân biệt lệnh kiểm tra tài liệu chạy được ngay và tình huống nghiệm thu ứng dụng sau triển khai.
 
**Post-design Constitution Check**: PASS; contract không đổi nguồn sở hữu 001–006, không biến mục tiêu thử thành SLA. Nếu leader thay phạm vi, cập nhật spec/design/plan trước tasks.
 
## Complexity Tracking
 
Không có vi phạm constitution. Phụ thuộc chính: 001 state/progress, 002 lifecycle, 004 LinkFlap, 005 health, 006 input. Những tối ưu như bảng riêng, broker, nhiều worker hoặc index JSONB đại trà chỉ xét sau đo và review riêng.


