# Implementation Plan: Hợp đồng đầu vào module tương quan

**Branch**: `006-correlation-input-contract` là nhãn feature do setup-plan trả về; chưa có Git branch trong thư mục đặc tả | **Date**: 2026-11-25 | **Spec**: [spec.md](spec.md)

**Input**: [Feature specification](spec.md), sáu lựa chọn A trong thảo luận. Đây là kế hoạch thiết kế để trình leader; chưa cho phép suy diễn rằng code đã triển khai hoặc benchmark đã chạy.

## Summary

Định nghĩa ranh giới bền vững giữa sự kiện syslog đã chuẩn hóa và worker tương quan: chọn event đủ điều kiện, tạo projection có kiểu, xét khả năng áp dụng theo từng rule, bảo toàn diagnostic/guard cho dữ liệu không chắc chắn, rồi chỉ đánh dấu event hoàn tất cùng kết quả. Đợt prototype đầu có một rule nghiệp vụ LinkFlap; hợp đồng hỗ trợ nhiều handler để không gắn parser với rule. Chọn chính sách bảo thủ: log có thể ảnh hưởng nhưng thiếu căn cứ không được tính là khoảng yên.

## Technical Context

**Language/Version**: Python 3.12 theo `telecom-alert-correlation-n42/pyproject.toml` và `requirements.txt`; Pydantic v2 đã dùng cho AlertEvent.

**Primary Dependencies**: FastAPI/Pydantic và ruamel.yaml đã có; worker tương quan/DB driver/repository chưa có. Cần chốt với TL/BE2/BE3 trước khi triển khai.

**Storage**: PostgreSQL; dùng `events`, `rules`, `rule_group_states`, `pipeline_runtime_status` và bảng cảnh báo/bằng chứng hiện thiết kế ở 001/002. Không thêm bảng cho riêng feature này ở bản đầu.

**Testing**: pytest đã có trong repo; chưa có fixture Juniper/canonical interface, test contract 006 hoặc test worker. Bộ test này thuộc giai đoạn triển khai sau.

**Target Platform**: Docker Compose hiện có PostgreSQL 16/TimescaleDB lab; chưa có worker service riêng trong compose.

**Project Type**: Hợp đồng tích hợp nội bộ của backend/worker, không là public API mới.

**Performance Goals**: Giữ nguyên mục tiêu **đề xuất** ở 003/004: đo nhận→đủ chốt và đủ chốt→hiển thị riêng; p95 2 giây/p99 5 giây cho đoạn sau đủ chốt trên tải lab là mục tiêu thử, không là SLA đã duyệt.

**Constraints**: Reorder 3 giây áp một lần ở engine; một worker sở hữu state; không parse raw trong handler; không đổi event_time/received_at/raw; không đánh dấu processed trước commit; không tự ACK/CLOSE; không giả UDP giao đủ.

**Scale/Scope**: Đợt đầu tập trung LinkFlap với Cisco XRv là thiết bị lab dự kiến. Dùng handler thử để kiểm chứng hợp đồng nhiều rule. Bài tải tham chiếu là 1.000 interface và 900.000 lần chuyển/giờ theo 004.

## Constitution Check

*GATE trước nghiên cứu và sau thiết kế: PASS cho phương án tài liệu; các giả định vận hành chưa là phê duyệt triển khai.*

| Nguyên tắc | Cách đáp ứng / kiểm tra |
|---|---|
| I, II — phạm vi và raw | Chỉ nhận syslog đã lưu; lịch sử search-only không vào live; không bịa field/thiết bị |
| III — tách trách nhiệm | 005 chuẩn hóa, 006 quy định bàn giao, 003 dispatch/handler, 002 lifecycle; handler không IO/ACK/CLOSE |
| IV, V — revision và nhóm | Metadata/schema revision bất biến; tạo khóa nhóm từ field xác minh; không instance mỗi interface |
| VI — thời gian/coverage | Nguồn thời gian có căn cứ, đệm một lần; diagnostic/guard bền vững trước kết luận quiet |
| VII — nhất quán | Receipt, checkpoint, evidence/alert và đúng event ID commit theo 003; không dùng MAX(ID) |
| VIII, IX — vòng đời/dọn | Không sửa closed; guard không bị eviction xóa; state cần khôi phục vẫn bền vững |
| X — hiệu năng | Tải và độ trễ đo riêng; mục tiêu thử không gọi SLA |
| Governance | Repo ứng dụng đã xác minh ở `telecom-alert-correlation-n42` trên main sạch; chưa gắn ticket N42 cụ thể cho thay đổi implementation |

**Không có ngoại lệ constitution được đề xuất.** Sau Phase 1, các contract bên dưới vẫn giữ quyền sở hữu dữ liệu của 001/003/005; không tạo nguồn schema thứ hai.

## Project Structure

### Documentation (this feature)

```text
specs/006-correlation-input-contract/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── normalized-event.md
│   └── input-disposition.md
└── checklists/requirements.md
```

`tasks.md` thuộc bước `$speckit-tasks`, chưa tạo trong plan.

### Source Code (application repository)

```text
telecom-alert-correlation-n42/
├── app/models/{raw_event,alert_event}.py   # Raw/normalized models hiện có
├── app/services/parser.py                 # RFC3164, chưa canonical interface/Juniper
├── app/services/rule_config_loader.py     # Loader rules.yaml
├── app/api/ingest.py                      # Queue RAM, chưa raw DB commit
├── app/store/__init__.py                  # Placeholder
└── tests/{test_parser,test_rules_config}.py
```

**Structure Decision**: Hợp đồng 006 là biên giữa parser/producer của BE2 và worker/dispatcher của BE3; không tạo bảng/service riêng. [Bản đồ code và khung module đề xuất](../003-rule-dispatch-correlation/codebase-mapping.md) ghi khác biệt hiện tại. Đường dẫn ứng dụng đã biết, nhưng schema thay đổi phải được TL/BE2/BE3 duyệt qua Jira/RTM trước code.

Biên bản họp bổ sung `target_ip` và chính sách đánh dấu thiếu dữ liệu. `target_ip` chỉ là field có điều kiện theo event_type/rule, không thành yêu cầu cho LinkFlap; xem [đối chiếu schema](../001-alert-data-model/meeting-schema-alignment.md).

Prototype ghi lý do thiếu dữ liệu và giữ chặn timer liên quan khi căn cứ còn thiếu. Phần xử lý lại syslog thiếu trường, gỡ chặn theo từng interface và hiển thị lý do trên giao diện nằm trong [phạm vi sau prototype](spec.md#phạm-vi-phát-triển-sau-prototype).

## Phase 0: Research and decisions

Kết quả ở [research.md](research.md): lựa chọn xử lý event/rule, diagnostic/guard bền vững, thứ tự thời gian, phạm vi prototype và các phương án không chọn. Không còn placeholder NEEDS CLARIFICATION trong Technical Context; version/thư viện/path mã nguồn được ghi là quyết định phải xác minh trước implementation, không tự suy đoán.

## Phase 1: Design and contracts

- [data-model.md](data-model.md): chỉ ánh xạ entity/field/trạng thái cần cho ranh giới; source of truth vẫn là 001/003/005.
- [contracts/normalized-event.md](contracts/normalized-event.md): projection v1, field theo event_type, tính hợp lệ và quyền sở hữu.
- [contracts/input-disposition.md](contracts/input-disposition.md): kết quả theo event/rule, mã lý do, guard/coverage, thời điểm được đánh dấu hoàn tất.
- [quickstart.md](quickstart.md): kiểm tra tài liệu chạy được ngay và kịch bản nghiệm thu cần chạy sau khi có implementation.

**Post-design Constitution Check:** PASS với cùng 10 nguyên tắc ở trên. Prototype xử lý riêng mỗi ID đầu vào. Ngưỡng time/clock lab, ứng dụng/phiên bản thư viện và chi phí index JSONB còn cần xác minh. Các yêu cầu bảo toàn raw, xử lý lại cùng ID và coverage an toàn tiếp tục áp dụng.

## Complexity Tracking

Không có vi phạm constitution cần biện minh. Prototype chọn một worker, một schema sự kiện chung, một bảng checkpoint chung và không thêm bảng event–rule. Nếu phép đo hoặc yêu cầu cách ly lỗi sau này chứng minh cần workset per-rule, đó là kế hoạch khác có schema/migration riêng.
