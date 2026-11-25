# Data model: Vòng đời cảnh báo

Nguồn schema chi tiết là [lifecycle-design.md](lifecycle-design.md) và [001](../001-alert-data-model/data-model.md); tài liệu này là bản đồ entity/transition cho plan, không tạo bảng khác.

| Entity | Field chính | Ràng buộc/quan hệ |
|---|---|---|
| alerts | id, rule_id, scope, group_values, signal_status, workflow_status, state_version, signal_event_id/at, recovered/acknowledged/closed at/by, rule_result | FK rule/event; active+closed cấm; closed cần recovered và actor/timestamp; one unclosed per revision/group/scope theo index đề xuất |
| alert_events | alert_id, event_id, evidence_role, is_current, linked_at, updated_at | PK(alert_id,event_id,evidence_role), role trigger/recovery/correction; liên kết nhiều-nhiều; closed không đổi |
| alert_state_history | alert_id, state_version, action, from/to signal/workflow, actor, causal_event_id, effective_at, recorded_at, details | PK(alert_id,state_version), append-only, version liên tục và snapshot khớp dòng cuối |
| events | id, event_time, scope, raw, correlation_details | Bằng chứng thật; timer có causal_event_id NULL nhưng evidence gốc còn |
| rules | id, rule_key, version | Revision bất biến được alert giữ |

## Chuyển trạng thái hợp lệ

AN=active+new; AA=active+acknowledged; RN=recovered+new; RA=recovered+acknowledged; RC=recovered+closed. System tạo AN, recover AN→RN hoặc AA→RA, reactivate RN→AN hoặc RA→AA. Operator ACK AN→AA/RN→RA; CLOSE từ RA→RC, RN→RA→RC trong một transaction. Active+closed không tồn tại. No-op không thêm history/version. Sau RC không sửa; episode mới cần alert ID mới.

## Validation

expected_state_version trên ACK/CLOSE, actor lấy danh tính xác thực; cùng transaction ghi alert snapshot/history/evidence. Kiểm tra quyền và causal evidence không thể chỉ bằng FK/CHECK. Coverage/timer từ 003/005/006 quyết định liệu recovery có được đề nghị; Lifecycle không tự suy thiết bị đã tốt. Tái phát trước CLOSE giữ ID/ACK. Các ca T01–T39 ở thiết kế nguồn.
