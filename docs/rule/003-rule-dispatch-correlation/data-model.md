# Data model: Engine rule và nhóm

Schema DB nguồn ở [001](../001-alert-data-model/data-model.md). Entity trong worker gồm RegistryRevision, NormalizedEvent, GroupKey, RuleState, RuleResult, HistoryContext và WorkReceipt; không tạo bảng riêng theo rule/interface.

| Entity | Field/identity | Nguồn/quy tắc |
|---|---|---|
| RegistryRevision | rules.id, rule_key, version, handler_key/revision, definition, enabled, activated_at | Snapshot bất biến, metadata/schema handler kiểm tra trước nạp |
| NormalizedEvent | event_id, type, time/status, received_at, device_id, scope, fields | Projection từ events theo [006](../006-correlation-input-contract/contracts/normalized-event.md) |
| GroupKey | rule revision + scope + group_values | Chỉ field đã xác minh; LinkFlap cần device_id+interface_name, lớp chọn trong config hoặc identity |
| RuleState | envelope engine + handler payload + state_schema_version | rule_group_states PK(rule_id,scope,group_values), checkpoint_version, next_check_at, last_event_id; không chứa workflow làm nguồn chuẩn |
| RuleResult | evaluation_status, new_state, decision, evidence, effective_at, reason, next_check_at/history_request | READY mới áp dụng; NEEDS_HISTORY/INCOMPLETE không commit state tạm |
| WorkReceipt | batch_id, exact event_ids, registry_rule_ids, owner_instance_id | pipeline_runtime_status.details.inflight; xóa cùng transaction kết quả |
| Guard | causal event, rule revision, scope_kind/key, raised/released, reason | Prototype trong events.correlation_details theo [006](../006-correlation-input-contract/contracts/input-disposition.md); query trước quiet timer |

## State transitions

Event parse success/partial + correlation pending → defer nếu chưa chốt; khi registry candidates đã xét và result/guard commit → processed; lỗi tạm rollback giữ pending/receipt; lỗi nghiêm trọng → failed nếu DB ghi được và fail-stop. Timer không tạo event giả hoặc cập nhật last_event_id. Cache state chỉ swap sau commit; restart đọc checkpoint/receipt và owner từ DB. Active group giữ nóng; recovered chưa closed evict khi checkpoint/cold-load an toàn; closed không đổi.

## Validation

C01–C48 trong [engine-design.md](engine-design.md) là kịch bản nguồn. Đợt đầu chỉ có LinkFlap nghiệp vụ; multi-rule bằng handler thử. Guard không tự release khi event processed. Không dùng MAX(event_id) làm cursor; trial defaults poll200ms/batch500/retry5 không phải SLA.
