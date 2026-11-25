# Contract: Worker, dispatcher và handler

## Worker input/ownership
Worker lấy event đã lưu theo [006](../../006-correlation-input-contract/contracts/normalized-event.md), giữ registry snapshot cho batch, một owner bằng session advisory lock. Receipt gồm batch_id, exact event_ids, registry_rule_ids, owner_instance_id. Mất lock/connection: dừng ghi, bỏ staged state, reload DB.

## Handler metadata
handler_key/revision, supported_event_types, required_fields/group_fields, parameter_schema, state_schema/version, history_policy, supported_outcomes. Một evaluator/revision phục vụ nhiều group; config chỉ đọc, không DB session/socket/callback.

## Năm thao tác
`initial_state(context)`, `evaluate(event,state,context)`, `on_time(state,context)`, `prune_state(state,context)`, `can_evict_state(state,context)`. State/context deep immutable hoặc copy-on-write. Result có READY/NEEDS_HISTORY/INCOMPLETE, new_state, NONE/ACTIVATE/RECOVER, evidence_ids, reason_code, effective_at, outcome, next_check_at, history_request. Chỉ READY được áp dụng; NEEDS_HISTORY nạp có giới hạn rồi rerun từ snapshot. Handler không ghi DB, timer/thread, notification hoặc ACK/CLOSE.

## Dispatch/result
Registry event_type → candidate revisions; resolver pin owner revision cũ của nhóm có alert chưa closed. Mỗi candidate một lượt; thiếu field rule A không loại rule B. Đánh giá theo thời gian nguồn; deadline trước event t chạy trước t, cùng t event trước timer. Log trễ tính bù theo history_policy. Quyết định bàn giao/guard theo [006](../../006-correlation-input-contract/contracts/input-disposition.md). Batch commit result/checkpoint/evidence/history/exact progress cùng xóa receipt, rồi mới swap cache. Lỗi nghiêm trọng fail-stop.

## Cleanup
Prune và evict tách biệt. Handler chỉ đề xuất, engine kiểm tra pending/inflight, alert active, idle, checkpoint và generation. Active giữ nóng; recovered chưa closed có thể cold-load an toàn. Chi tiết C01–C48: [engine-design.md](../engine-design.md).
