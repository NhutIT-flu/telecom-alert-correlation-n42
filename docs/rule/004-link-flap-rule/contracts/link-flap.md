# Contract: Handler LinkFlap revision đầu

## Subscription/config
`event_type=interface_state_change`; `group_by=[device_id,interface_name]`; lớp physical. `parameters={window_seconds:60,min_transitions:5,interface_layer:physical}`; `recovery={mode:quiet_period,quiet_seconds:60}`. Snapshot config có handler revision, schema được kiểm tra; ví dụ hiện `enabled=false` vì chưa triển khai.

## Input
Canonical event theo [006](../../006-correlation-input-contract/contracts/normalized-event.md): event_id, event_time tin cậy, device_id, interface_name, interface_state UP/DOWN, interface_layer physical. Thiếu/mâu thuẫn được dispatcher xử lý theo [006 disposition](../../006-correlation-input-contract/contracts/input-disposition.md). Handler không parse raw hoặc tự chọn alias/lớp.

## Evaluation
Quan sát đầu là baseline. Chuyển UP↔DOWN tính một; log lặp vẫn xét/giữ nhưng không đếm. N≥5 trong (T−60,T] → ACTIVATE; cùng episode không tạo alert mới mỗi log. 3 giây reorder chỉ ở engine. Log trễ có thể thay baseline/hai cạnh; yêu cầu thêm history/baseline khi cần, INCOMPLETE nếu không đủ.

## Timer/cleanup
Khi flapping và 60 giây không chuyển trong đoạn an toàn → RECOVER outcome flap_stopped_up hoặc flap_stopped_down, không ACK/CLOSE/LinkDown. Deadline nguồn max(last_transition+60,safe_since+60) khi gap chưa dựng lại; safe_since unknown thì không RECOVER. Prune không xóa baseline/episode context; eviction theo guard 003. Chi tiết LF01–LF26: [link-flap-design.md](../link-flap-design.md).
