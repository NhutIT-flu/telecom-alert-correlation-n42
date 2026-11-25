# Data model: State LinkFlap

Không thêm bảng LinkFlap. Cấu hình revision ở rules.definition và checkpoint ở rule_group_states theo [001](../001-alert-data-model/data-model.md); thuật toán ở [link-flap-design.md](link-flap-design.md).

| Entity/field | Vai trò và ràng buộc |
|---|---|
| rules.id, rule_key, handler_revision, definition | Snapshot config: subscription interface_state_change, group_by device_id/interface_name, N=5, W=60s, physical, quiet60; ví dụ vẫn disabled |
| group key | revision + scope + device_id + interface_name; lớp cố định ở config, không alias/NULL |
| handler.phase | unknown/tracking/flapping/recovered; không là workflow alert |
| handler.baseline | Observation trước đoạn cần dựng lại; NULL chỉ khi chưa có căn cứ |
| handler.observations | event ID/time/UP-DOWN/layer trong vùng cần tính bù, gồm log lặp |
| handler.threshold_transitions | Tối đa N mốc dẫn xuất (ID,time,from,to); không thay toàn history/baseline |
| handler.last_observation/last_transition | Mốc thật để xét deadline |
| handler.episode_boundary/last_outcome | Ranh giới recovery còn hợp lệ; outcome flap_stopped_up/down |
| engine envelope/next_check_at | Coverage/safe_since/checkpoint_version và deadline nguồn; không cộng 3 giây hai lần |

## Chuyển giai đoạn

Quan sát đầu → baseline/tracking, không transition. Mỗi UP↔DOWN → thêm một transition; lặp UP→UP không tăng count nhưng vẫn xét. Tại ≥5 mốc trong (T−60,T] → ACTIVATE theo 002. Khi flapping và đủ quiet60 với coverage an toàn → RECOVER outcome theo trạng thái cuối. Nếu gap không dựng lại, deadline=max(last_transition+60,safe_since+60); safe_since unknown không recover. Recovered tái phát bình thường cần 5 mốc sau boundary; correction vô hiệu recovery phải dùng episode cũ. Alert closed bất biến.

## Retention/cache

Prune mốc hết hạn không xóa baseline/quan sát cần tính bù. Active giữ nóng; tracking hết dữ liệu có thể evict sau idle/checkpoint; recovered chưa closed có thể evict nếu đủ guard/cold-load. Event/raw/history vẫn bền vững. Bộ LF01–LF26 ở thiết kế nguồn là expected results, chưa là test đã chạy.
