# Contract v1: Quyết định bàn giao event cho rule

**Owner:** dispatcher/worker 003. **Input:** [NormalizedEvent](normalized-event.md) và registry snapshot. **Output:** kết quả theo từng candidate revision, diagnostic và guard bền vững khi cần. Handler chỉ được gọi nếu `APPLY`.

| Kind | Khi nào | Tác động |
|---|---|---|
| APPLY | event_type/scope phù hợp, đủ field nhóm và rule, thời gian có căn cứ nếu rule yêu cầu | Tạo/nạp group và gọi handler một lần cho revision |
| NOT_APPLICABLE | Candidate sau filter không phù hợp | Không gọi handler; ghi nếu cần giải thích, không ghi hàng loạt cho mọi rule trong registry |
| INVALID_FOR_RULE | Đúng loại nhưng thiếu/mâu thuẫn field cần thiết | Ghi reason; rule khác đủ vẫn chạy; kiểm tra có guard timer hay không |
| DEFER | Chưa chốt hoặc còn điều kiện đọc/bằng chứng chưa hoàn tất | Event vẫn pending; không gọi handler hoặc coi đã xét |

Với LinkFlap, lớp `protocol` đã xác minh là `NOT_APPLICABLE`, kể cả khi bản tin thiếu field khác của rule. Lớp chưa rõ trên bản tin cùng loại là `INVALID_FOR_RULE` với `AMBIGUOUS_INTERFACE_LAYER`. Dispatcher chỉ dùng `DEFER` do còn trong khoảng đệm sắp thứ tự 3 giây khi giờ nguồn đủ điều kiện theo [hợp đồng sự kiện](normalized-event.md#điều-kiện-dùng-thời-gian-suy-ra).

`BLOCKED_FOR_QUIET` là **guard độc lập với disposition**, không phải một trạng thái correlation_status mới. Event có thể processed sau khi các rule đủ dữ liệu đã hoàn tất, nhưng guard vẫn mở nếu log thiếu căn cứ có thể che mất transition. Lỗi handler/schema/DB là lỗi thực thi, không chuyển thành INVALID_FOR_RULE.

## Mã lý do v1

| Code | Áp dụng | Tác động quiet |
|---|---|---|
| UNSUPPORTED_EVENT_TYPE | Không rule đăng ký hoặc parser chưa xác định event_type | Không tự tạo group; nếu có thể là interface change chưa phân loại thì guard theo phạm vi có căn cứ |
| OUT_OF_SCOPE | Search-only/replay khác scope | Không ảnh hưởng live; ghi lý do scope |
| MISSING_DEVICE | Không xác định device_id cần cho group | Guard nguồn/scope liên quan nếu event có thể là interface change |
| MISSING_GROUP_FIELD | Thiếu interface_name hoặc field group khác | Guard device nếu biết device, ngược lại nguồn/scope |
| MISSING_TARGET_IP | Event type/rule yêu cầu IP đích nhưng log không có địa chỉ đích có căn cứ | Chỉ ảnh hưởng rule cần IP; guard timer nếu có thể che dữ kiện kết thúc |
| INVALID_FIELD_VALUE | Enum/kiểu sai hoặc field cũ/chuẩn mâu thuẫn | Guard phạm vi có căn cứ nếu có thể ảnh hưởng rule |
| AMBIGUOUS_INTERFACE_LAYER | Không biết physical/protocol | Guard device/group xác định được, không mặc định physical |
| UNKNOWN_EVENT_TIME | Thiếu giờ nguồn, thiếu căn cứ suy ra, căn cứ mâu thuẫn hoặc kết quả không qua kiểm tra thời gian của nguồn | `INVALID_FOR_RULE` với rule cần giờ nguồn. Nếu bản tin có thể che chuyển trạng thái thì chặn timer tại phạm vi có căn cứ. |
| NOT_FINALIZED_YET | Chưa qua mốc chốt 3 giây | DEFER, pending; chặn deadline liên quan trước khi có kết quả |
| COVERAGE_UNSAFE | Source/clock/backlog không cho phép quiet | Guard health/coverage, không là log transition |

Danh mục code có thể bổ sung theo phiên bản contract; code cũ không được tái sử dụng với nghĩa mới.

## Phạm vi guard và vòng đời

1. Chọn phạm vi hẹp nhất có căn cứ: `group` (đủ device+interface+lớp), `device`, `source` trong một scope, cuối cùng `scope`. Không biến NULL thành một group chung. Source phải là nguồn xác thực/được nhận diện, không chỉ hostname/IP tự khai.
2. Ghi guard cùng diagnostic của event và tiến độ kết quả trong transaction. `raised_at`, scope_kind/key, reason, causal_event_id và rule_id giữ được qua restart. Không dùng state RAM hoặc chỉ heartbeat làm nguồn duy nhất.
3. Trước timer, truy vấn mọi blocker liên quan (event guard chưa release, parse-pending/failed, backlog đủ cutoff và health/coverage). Event đã processed vẫn có thể chặn.
4. Trong prototype, giữ guard của bản tin thiếu hoặc mâu thuẫn dữ liệu khi căn cứ chưa được làm rõ. Event `processed`, worker restart hoặc đủ 60 giây theo đồng hồ không làm hết hiệu lực guard. LinkFlap vẫn xét kết thúc theo 004 khi các điều kiện quan sát đủ và không còn guard ảnh hưởng.
5. Nếu không đủ căn cứ để thu hẹp phạm vi, ghi lý do và chặn kết luận ở scope liên quan.

## Xử lý sau prototype

- Giải quyết dữ liệu mơ hồ bằng cách kiểm tra lại bản tin gốc và tính lại đoạn bị ảnh hưởng khi xác định được trường thiếu. Lưu bằng chứng và lý do gỡ guard.
- Khi không thể dựng lại đoạn mơ hồ, xem xét dùng một syslog hợp lệ mới của chính interface trong đoạn quan sát đủ căn cứ để xác lập `safe_since`. Theo dõi điều kiện gỡ chặn riêng cho từng nhóm nếu guard ban đầu thuộc cả thiết bị. Timer vẫn cần đủ trọn khoảng yên của rule từ mốc an toàn mới.
- Lưu `released_at`, lý do và bằng chứng khi gỡ guard. Hiển thị lý do cảnh báo còn mở khi người giám sát chưa thể xác nhận hết flap.

## Nhất quán và kiểm chứng

Registry candidate IDs cố định trong receipt trước đánh giá; result transaction ghi disposition/guard, checkpoint, alert/evidence/history và đúng event ID rồi xóa receipt. Retry đọc lại receipt/progress trước khi áp. Mỗi candidate có đúng một disposition cuối trong lượt; event đủ điều kiện mới chuyển processed. `correlation_details` có schema version, giới hạn size và không lưu raw/secret. Nếu truy vấn guard từ event quá chậm, thiết kế bảng riêng phải được leader duyệt cùng migration; không được bỏ kiểm tra guard.

**Ví dụ prototype:** Log interface của thiết bị A thiếu `interface_name`. Dispatcher ghi `INVALID_FOR_RULE` / `MISSING_GROUP_FIELD` cho LinkFlap. Rule khác đủ dữ liệu vẫn có thể `APPLY`. Event có thể thành `processed` sau khi ghi kết quả, còn guard thiết bị A tiếp tục chặn timer LinkFlap liên quan.
