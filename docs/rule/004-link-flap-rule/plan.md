# Implementation Plan: Rule LinkFlap
 
**Branch**: `004-link-flap-rule` là nhãn feature từ setup-plan, chưa xác nhận nhánh Git | **Date**: 2026-11-25 | **Spec**: [spec.md](spec.md)
 
**Input**: Đặc tả hiện có và các tài liệu thiết kế liên quan. Bản plan phục vụ leader review; chưa triển khai ứng dụng.
 
## Summary
 
UP↔DOWN mỗi chuyển một lần; N=5 trong (T−60,T]; quiet60 và outcome UP/DOWN. Phương án chi tiết ở [link-flap-design.md](link-flap-design.md); plan này xác định ranh giới, phụ thuộc, contract và cách kiểm chứng, không lặp lại toàn bộ thuật toán/schema.
 
## Technical Context
 
**Language/Version**: Python 3.12; config Pydantic/ruamel.yaml hiện có, handler LinkFlap chưa có.
 
**Primary Dependencies**: Python handler theo contract 003; PostgreSQL checkpoint chung. FastAPI/Pydantic/ruamel.yaml theo repo đã xác minh; PostgreSQL application driver/repository và migration cần quyết định trước implementation.
 
**Storage**: PostgreSQL, theo [001](../001-alert-data-model/data-model.md); bảng chung rules/rule_group_states/alerts/evidence; không bảng riêng LinkFlap.
 
**Testing**: pytest có test rules.yaml; chưa có test transition/quiet.
 
**Target Platform**: Docker Compose lab hiện có PostgreSQL 16/TimescaleDB image; Jenkins/CI files hiện có. Chưa khẳng định môi trường đã chạy.
 
**Project Type**: module backend trong hệ thống giám sát syslog.
 
**Performance Goals**: LF01–LF26; tải 1.000 interface/900.000 chuyển/giờ để đo, chưa nghiệm thu.
 
**Constraints**: physical layer, baseline không đếm, log lặp vẫn xét; LinkDown riêng; cấu hình ví dụ đang disabled. Không dùng dữ liệu production/secret trong fixture. Chỉ số đã đo phải tách khỏi ước lượng/mục tiêu.
 
**Scale/Scope**: Prototype để trình duyệt; một handler LinkFlap trên nhiều nhóm interface.
 
## Constitution Check
 
*GATE trước Phase 0 và sau Phase 1: PASS cho bản thiết kế; không phát hiện ngoại lệ cần sửa constitution.*
 
- V/VI/VIII/IX/X: tách device+interface, late correction, coverage-safe recovery, prune/evict an toàn.
- Các nguyên tắc còn lại vẫn áp dụng: không tự cấu hình/khắc phục thiết bị; phân quyền rõ; không ghi kết quả dở hoặc mất syslog đã lưu; không sửa lịch sử closed.
- Governance: application repo đã xác minh trên branch main sạch; docs spec nằm ở thư mục cha ngoài repo. Chưa có ticket N42 cụ thể cho implementation này; plan không tạo branch/commit/PR.
 
## Project Structure
 
### Documentation (this feature)
 
```text
specs/004-link-flap-rule/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── link-flap-design.md
├── contracts/
│   └── link-flap.md
└── quickstart.md
```
 
`tasks.md` thuộc bước $speckit-tasks, không tạo trong plan.
 
### Source Code (application repository)

```text
telecom-alert-correlation-n42/
├── app/services/rules.yaml          # RULE_LINK_FLAP_01 disabled, group_by hostname/interface
├── app/models/rule_config.py        # Generic count.state_changes config
├── app/models/alert_event.py        # Chưa có interface_name/state/layer canonical
├── app/services/parser.py           # RFC3164 header + vendor, chưa bóc interface semantics
├── tests/test_rules_config.py       # Kiểm tra YAML, chưa test transition LinkFlap
└── tests/fixtures/rules/           # Candidate/review cases, chưa là engine runtime
```

**Structure Decision**: Rule YAML là mẫu chưa chạy. 004 chỉ nên có handler/fixtures/test riêng sau khi BE2/TL chốt event projection và registry migration; chưa bật YAML hoặc tái dùng `hostname` làm device identity. [Bản đồ code](../003-rule-dispatch-correlation/codebase-mapping.md).
 
## Phase 0: Research and decisions
 
[research.md](research.md) ghi Decision/Rationale/Alternatives và các rủi ro chưa đo. Không còn NEEDS CLARIFICATION bắt buộc cho phương án thiết kế; runtime Python 3.12, CI files và repo path đã xác minh; DB driver, contract chéo nhóm và ngưỡng lab còn phải quyết định trước implementation.
 
## Phase 1: Design and contracts
 
- [data-model.md](data-model.md) ánh xạ entity, validation và transition của feature; tham chiếu schema nguồn 001, không tạo bảng song song.
- [link-flap-design.md](link-flap-design.md) là thiết kế kỹ thuật nguồn sở hữu.
- [contracts/](contracts/link-flap.md) ghi giao tiếp với module khác.
- [quickstart.md](quickstart.md) phân biệt lệnh kiểm tra tài liệu chạy được ngay và tình huống nghiệm thu ứng dụng sau triển khai.
 
**Post-design Constitution Check**: PASS; contract không đổi nguồn sở hữu 001–006, không biến mục tiêu thử thành SLA. Nếu leader thay phạm vi, cập nhật spec/design/plan trước tasks.
 
## Complexity Tracking
 
Không có vi phạm constitution. Phụ thuộc chính: 003 engine/handler, 002 lifecycle, 005/006 canonical event. Những tối ưu như bảng riêng, broker, nhiều worker hoặc index JSONB đại trà chỉ xét sau đo và review riêng.


