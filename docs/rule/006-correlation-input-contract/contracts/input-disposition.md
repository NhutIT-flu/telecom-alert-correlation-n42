# Contract v1: Quyết định bàn giao event cho rule

**Owner:** dispatcher/worker 003. **Input:** [NormalizedEvent](normalized-event.md) và registry snapshot. **Output:** kết quả theo từng candidate revision, diagnostic và guard bền vững khi cần. Handler chỉ được gọi nếu `APPLY`.

| Kind | Khi nào | Tác động |
|---|---|---|
| APPLY | event_type/scope phù hợp, đủ field nhóm và rule, thời gian có căn cứ nếu rule yêu cầu | Tạo/nạp group và gọi handler một lần cho revision |
| NOT_APPLICABLE | Candidate sau filter không phù hợp | Không gọi handler; ghi nếu cần giải thích, không ghi hàng loạt cho mọi rule trong registry |
| INVALID_FOR_RULE | Đúng loại nhưng thiếu/mâu thuẫn field cần thiết | Ghi reason; rule khác đủ vẫn chạy; kiểm tra có guard timer hay không |
| DEFER | Chưa chốt hoặc còn điều kiện đọc/bằng chứng chưa hoàn tất | Event vẫn pending; không gọi handler hoặc coi đã xét |

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
| UNKNOWN_EVENT_TIME | Không có giờ nguồn đáng tin | Không dùng received_at để đếm; guard phạm vi liên quan |
| NOT_FINALIZED_YET | Chưa qua mốc chốt 3 giây | DEFER, pending; chặn deadline liên quan trước khi có kết quả |
| COVERAGE_UNSAFE | Source/clock/backlog không cho phép quiet | Guard health/coverage, không là log transition |

Danh mục code có thể bổ sung theo phiên bản contract; code cũ không được tái sử dụng với nghĩa mới.

## Phạm vi guard và vòng đời

1. Chọn phạm vi hẹp nhất có căn cứ: `group` (đủ device+interface+lớp), `device`, `source` trong một scope, cuối cùng `scope`. Không biến NULL thành một group chung. Source phải là nguồn xác thực/được nhận diện, không chỉ hostname/IP tự khai.
2. Ghi guard cùng diagnostic của event và tiến độ kết quả trong transaction. `raised_at`, scope_kind/key, reason, causal_event_id và rule_id giữ được qua restart. Không dùng state RAM hoặc chỉ heartbeat làm nguồn duy nhất.
3. Trước timer, truy vấn mọi blocker liên quan (event guard chưa release, parse-pending/failed, backlog đủ cutoff và health/coverage). Event đã processed vẫn có thể chặn.
4. Release chỉ khi sửa được ambiguity bằng đường có audit hoặc đã có đoạn quan sát lành mạnh mới được chứng minh. Nếu không thể dựng lại khoảng mờ, `safe_since` bắt đầu từ đoạn lành mạnh mới và phải đủ trọn quiet period của rule. Release ghi `released_at`, reason/evidence, không xóa dấu vết cũ. Không release chỉ vì event processed hoặc worker restart.
5. Không đủ căn cứ xác định nguồn/phạm vi thì báo scope chưa thể chứng minh; ưu tiên an toàn hơn kết luận phục hồi sai. Chỉ mở lại quiet khi căn cứ coverage tương ứng rõ.

## Nhất quán và kiểm chứng

Registry candidate IDs cố định trong receipt trước đánh giá; result transaction ghi disposition/guard, checkpoint, alert/evidence/history và đúng event ID rồi xóa receipt. Retry đọc lại receipt/progress trước khi áp. Mỗi candidate có đúng một disposition cuối trong lượt; event đủ điều kiện mới chuyển processed. `correlation_details` có schema version, giới hạn size và không lưu raw/secret. Nếu truy vấn guard từ event quá chậm, thiết kế bảng riêng phải được leader duyệt cùng migration; không được bỏ kiểm tra guard.

**Ví dụ:** Log interface của device A thiếu `interface_name`: LinkFlap nhận INVALID_FOR_RULE/MISSING_GROUP_FIELD, rule khác đủ field vẫn có thể APPLY; event processed sau commit kết quả, nhưng guard device A còn mở cho timer LinkFlap. Khi nguồn đã quan sát an toàn đủ 60 giây kể từ mốc `safe_since` hợp lệ, timer mới được xét; không suy rằng log thiếu interface là một lần chuyển hoặc không chuyển.
