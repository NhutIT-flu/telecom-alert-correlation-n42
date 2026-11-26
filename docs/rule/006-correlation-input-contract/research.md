# Research: Hợp đồng đầu vào tương quan

Ngày 2026-11-25. Đây là tổng hợp phương án thiết kế từ 001/003/005/006 và các lựa chọn A của người thiết kế; không phải benchmark hay quyết định leader đã duyệt.

## R1. Nguồn sự kiện cho worker

- **Decision**: Worker đọc event đã commit, parse success/partial, correlation pending trong scope được phép; projection tạo một lần và handler không parse raw.
- **Rationale**: Giữ raw bền vững, giảm phụ thuộc gọi trực tiếp giữa module, cho phép restart/retry bằng cùng event ID.
- **Alternatives considered**: normalizer gọi từng handler ngay sau parse (mất ranh giới commit/retry); quét toàn DB theo MAX(ID) (không bảo đảm thứ tự commit).
- **Source**: 001 mục 9, 003 mục 13, 005 mục 2.

## R2. Kết quả theo event/rule khi chỉ một rule thiếu field

- **Decision**: Đối với mỗi **candidate revision trong registry snapshot**, lưu disposition và mã lý do trong `events.correlation_details` object có phiên bản. Các rule đủ dữ liệu vẫn chạy; event được processed khi tất cả candidate đã có kết quả và guard cần thiết đã commit. Rule không đăng ký event_type không cần một row kết quả riêng.
- **Rationale**: Hợp với lựa chọn Q3=A và 8 bảng hiện tại; không nhầm processed với “có alert”. Giữ snapshot revision trong work receipt để retry không đổi nghĩa.
- **Alternatives considered**: giữ toàn event pending nếu một rule thiếu field (cản rule khác, có thể kẹt); bảng event–rule mới (tăng write và schema cho prototype).
- **Limit**: `correlation_details` phải có schema/version và size cap; query liên tục theo JSONB cần đo.

## R3. Guard bền vững cho timer khi đầu vào không chắc chắn

- **Decision cho prototype**: Dùng diagnostic bền vững trên event làm bằng chứng của guard nhóm/thiết bị/nguồn/scope, kết hợp trạng thái coverage/checkpoint. Ghi `raised_at`, `scope_kind`, `scope_key`, `reason_code`, `released_at` và căn cứ release có audit. Trước timer, kiểm tra guard chưa release cùng raw parse-pending/failed/backlog/health; không thể định danh nhóm thì không chỉ dựa vào `rule_group_states` của một nhóm. Event processed không tự release guard.
- **Rationale**: Tuân lựa chọn Q2=A mà không thêm bảng thứ chín. Phân loại theo phạm vi nhỏ nhất có căn cứ, không cho timer suy yên khi log bị mất nghĩa.
- **Alternatives considered**: chỉ lưu guard trong group checkpoint (không đại diện được log chỉ biết device/scope); dùng `pipeline_runtime_status.details` làm kho guard (row này chỉ là health/receipt mới nhất); bảng `correlation_input_guards` riêng (truy vấn timer rõ hơn nhưng thêm migration/ghi/cleanup).
- **Risk and gate**: Nếu query blocker theo device/scope qua `correlation_details` vượt mục tiêu tải, đề xuất bảng guard riêng qua review/migration. Không được bỏ guard để đạt tốc độ. Khi căn cứ không thể phục hồi, `safe_since` bắt đầu lại từ đầu đoạn quan sát lành mạnh có chứng cứ và rule phải đủ trọn quiet period mới recover; không đặt release chỉ vì event đã processed. Chưa có đo thực tế.

## R4. Thời gian và log trễ

- **Decision**: Giữ event_time/received_at/time_status khác nghĩa; 3 giây reorder do engine áp một lần. Log trễ trong vùng có thể chứng minh của LinkFlap được tính bù bằng history/baseline; ngoài vùng hoặc thiếu history ghi incomplete/diagnostic.
- **Rationale**: Đúng Q4=A và ngăn mốc nhận thay mốc sinh.
- **Alternatives considered**: bỏ log trễ hoặc dùng received_at làm thứ tự (có thể đổi số transition/cửa sổ sai).
- **Source**: 003 mục 12/17 và 004 mục 4.

## R5. Lỗi và phạm vi rule đợt đầu

- **Decision**: Một worker với LinkFlap là rule nghiệp vụ đầu tiên. Lỗi code/schema/checkpoint nghiêm trọng rollback, fail-stop và giữ việc; không cách ly per-rule trong prototype. File cấu hình phiên bản do nhóm phát triển công bố; operator chỉ xem.
- **Rationale**: Theo Q1/Q5/Q6=A, tránh công bố kết quả thiếu rule sau lỗi.
- **Alternatives considered**: chạy nhiều rule nghiệp vụ ngay, bỏ qua rule lỗi, UI đăng ký rule (đều mở rộng phạm vi).
- **Source**: 003 mục 1/3/7/13, 004 và 006 assumptions.

## R6. Việc chưa được quyết định trong phiên lập kế hoạch

- Repository ứng dụng đã xác minh tại `C:/Projects/vnpt/telecom-alert-correlation-n42`: Python 3.12, FastAPI/Pydantic/ruamel.yaml, pytest và Docker Compose PostgreSQL/TimescaleDB. Chưa có PostgreSQL application driver/repository, worker hoặc canonical interface mapping; xem [bản đồ code](../003-rule-dispatch-correlation/codebase-mapping.md). Script setup-plan chỉ có nhãn feature; thư mục đặc tả ở ngoài Git repo.
- Ngưỡng kiểm tra clock/trust và giới hạn truy vấn guard/history cần số liệu lab. Giá trị mục tiêu hiện tại chỉ là đề xuất.
- Prototype coi **hai ID nhận khác nhau** là hai sự kiện riêng. Việc nhận diện trùng giữa các ID được xem xét sau prototype. Xử lý lại cùng ID vẫn phải nhất quán.
