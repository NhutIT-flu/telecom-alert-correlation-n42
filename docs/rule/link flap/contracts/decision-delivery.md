# Contract v1 — Decision, outbox và Link Down

## Message/stream

Outbox chung có kind DECISION hoặc COMMAND, message_id xác định, producer rule_id, entity, stream_seq, episode_id, episode_seq và payload. Stream key=(kind,rule_id,entity_kind,entity_key); stream_seq tăng bền vững xuyên đợt, không reset khi recovery.

Decision action gồm ALERT_TRIGGERED/ALERT_UPDATED/ALERT_RECOVERED; NO_ACTION chỉ là outcome nội bộ. Payload có thời gian nghiệp vụ/phát, episode/config/hash/time_basis, counters tuyệt đối, as-of, trạng thái cuối, recovery due/block reason và verification=LAST_OBSERVED.

InternalCommand LINK_DOWN_RECONCILE gồm command_id, target_rule_id=LINK_DOWN, entity, originating_episode_id, requested_at, observed_snapshot_version để trace. Command stream riêng để alert consumer không nhận gap do lọc COMMAND.

IDs tạo xác định từ stream identity/sequence và loại message, lưu cùng transaction state. Retry không sinh ID ngẫu nhiên khác.

Mỗi full stream key có counter riêng trong rule state bền vững, nằm ngoài active_episode. Ví dụ recovery dùng DECISION seq=7, reconcile dùng COMMAND seq=1 thì trigger đợt kế tiếp dùng DECISION seq=8. Test phải bao phủ chuỗi cuối DOWN này để tránh gap giả.

## Ordered delivery và consumer apply

1. Claim stream head chưa ACK, không chỉ claim bất kỳ row bằng SKIP LOCKED. Bản seq n+1 không vượt bản n đang gửi hoặc đang retry.
2. Giao at-least-once, timeout có backoff và lý do theo dõi; không xóa bản chưa xác nhận.
3. Consumer có applied message receipt và last_stream_seq. ID đã áp dụng no-op; nhận gap thì chờ/retry lấy bản thiếu, không tự nhảy.
4. Atomically ghi receipt, episode→incident mapping, hồ sơ/audit và ý định notification phía consumer.
5. Một open slot cho (rule_id,entity) bao gồm ACTIVE và UNKNOWN chưa có ended_at. Workflow RESOLVED/CLOSED không giải phóng slot.
6. Cùng episode trigger retry trả mapping cũ; khác episode xung đột slot thì báo nhất quán cần reconcile, không merge im lặng.
7. Update/recovery chỉ tác động episode đích; số đếm tuyệt đối không ghi đè giá trị mới bởi decision cũ.

Chuỗi cần bảo vệ: A.triggered → A.updated → A.recovered → B.triggered, kể cả delivery đảo/duplicate/crash. Database alert production chưa được implement ở source; module kiểm chứng bằng consumer test có cùng contract, không nhận mock là production đã nghiệm thu.

## Link Down reconciliation

ALERT_RECOVERED cuối DOWN được commit cùng durable command. Handler đích phải vào transaction của entity, chống trùng command_id, đọc snapshot/config/quality/progress **hiện tại**:

- Hiện UP: không tạo Link Down từ DOWN cũ.
- Hiện DOWN: xét status_since hiện tại và down-hold của Link Down; bảo đảm một hồ sơ đúng khi đủ ngưỡng, nếu chưa thì giữ timer độc lập.
- Hiện unknown/degraded: chờ đối soát, không suy UP/DOWN.
- Rule đích chưa đăng ký: giữ pending và lỗi tích hợp có theo dõi, không ACK như đã phối hợp.

Không chọn down-hold 30s thay owner. Link Down bắt đầu theo dõi INITIAL DOWN độc lập; không đợi Link Flap kết thúc. Luật đó nằm ngoài module nghiệp vụ được xây trong scope hiện tại.

Host đăng ký External CommandSink theo target_rule_id. Bên nhận lưu unique command_id receipt atomically cùng effect/timer/decision của Link Down. Module chỉ giao command và ACK outbox sau CommandApplyReceipt thành công; không tiếp nhận command bằng event receipt. Receipt phía nhận gồm command_id, status APPLIED hoặc DUPLICATE và effect version; lỗi/thiếu adapter không trả thành công.

## Workflow, UI và notification boundary

Module không đổi workflow, gửi email hoặc cập nhật dashboard trực tiếp. Consumer phải giữ technical_status khác workflow_status; RECOVERED+STABLE_DOWN hiển thị “hết dao động, trạng thái quan sát cuối DOWN”. Counter cửa sổ luôn kèm as-of; không dùng đồng hồ trình duyệt để sửa lịch sử trigger.

Notification policy trigger/recovery vẫn là đề xuất từ nguồn, chưa tạo kênh gửi hoặc SLA. Idempotent DB effect không đồng nghĩa thông báo bên ngoài exactly-once.

## Nghiệm thu

Crash sau state commit trước delivery; sau consumer commit trước ACK; duplicate/gap/xuyên episode; command trễ sau UP; hai timer worker; consumer unavailable rồi resume phải giữ cùng hiệu lực. Không ghi PASS cho adapter production chưa tồn tại.

