# Contract v1 — Correlation rule module

**Status**: Thiết kế của lượt plan; không ghi nhận producer/TL/QA đã bàn giao.
**Paths**: Tương đối implementation root trong [plan](../plan.md).

## Public module surface (Python 3.12)

Các chữ ký sau là hợp đồng để implementation/tasks bám theo, không phải code đã tồn tại.

| Thành phần dự kiến | Chữ ký / chức năng |
| --- | --- |
| app/models/correlation.py | CorrelationEvent, InterfaceObservation, InterfaceSnapshot, InterfaceObservationResult, RuleInput, RuleContext, RuleOutcome, TimerCommand, ProcessingReceipt, SourceProgressProof, DetectionDecision, InternalCommand |
| app/services/correlation/engine.py | RuleDescriptor; Rule protocol; CorrelationEngine.register(rule: Rule) -> None |
| CorrelationEngine | async process_event(event: CorrelationEvent) -> ProcessingReceipt |
| CorrelationEngine | async process_timer(timer: TimerCommand) -> ProcessingReceipt |
| External CommandSink adapter | async apply(command: InternalCommand) -> CommandApplyReceipt; do bên nhận Link Down cung cấp, chưa là engine API bản đầu |
| Shared observer trong engine.py | observe_interface(before: InterfaceSnapshot, event: CorrelationEvent) -> InterfaceObservationResult |
| Rule protocol | descriptor() -> RuleDescriptor; validate_config(config: CorrelationRule) -> ValidatedRuleConfig |
| Rule protocol | process_event(input: RuleInput, state: RuleState, context: RuleContext) -> RuleOutcome |
| Rule protocol | on_timer(timer: TimerCommand, state: RuleState, context: RuleContext) -> RuleOutcome |
| app/services/correlation/link_flap.py | LinkFlapRule, LinkFlapState, LinkFlapConfig |
| app/services/correlation/adapter.py | adapt_interface(event: AlertEvent, observation: InterfaceObservation, ingress: IngressMetadata) -> CorrelationEvent |
| app/store/correlation.py | CorrelationStore.transaction(entity: EntityKey, owner: OwnerToken) -> synchronous UoW context |
| app/services/correlation/runtime.py | CorrelationRuntime.start() / stop() async, bounded event worker, timer/outbox tick |

EntityKey/OwnerToken/IngressMetadata/RuleState/ValidatedRuleConfig là các typed records/protocol cùng module model/engine, được định nghĩa cụ thể khi implement; không trộn OwnerToken với timer generation. UoW có các thao tác load/stage/commit state, receipt, timers, progress và outbox; không cần repository riêng cho từng bảng.

RuleDescriptor gồm rule_id, rule_version, state_schema_version, subscribed_event_types, entity_kind, key_fields, config validator và supports_timers. Registry compile vào Python, không load code động từ YAML. Duplicate registration hoặc enabled rule thiếu handler phải fail-fast.

RuleInput gồm CorrelationEvent và observation_result tùy loại sự kiện. InterfaceObservationResult có INITIAL/REPEATED/TRANSITION, before/after và transition tùy chọn. Rule không dùng interface có observation_result=null; không phải giả lập UP/DOWN để tham gia registry.

RuleContext gồm config đã validate/pin, epoch, entity snapshot phù hợp loại thực thể, proof/health, clock và ownership/version metadata. Rule không tự query DB hoặc đổi context.

## Link Flap processing

- Evaluation time = received_at. Dùng deque cục bộ để prune <t−60s; lưu immutable next_state.
- process_event có thể trả NO_ACTION và state mới; engine vẫn commit.
- Due timers xử lý trên snapshot trước observe. Sau đó mọi rule nhận cùng immutable result. Rule lỗi khiến UoW rollback.
- Generation chỉ tăng khi lịch nghiệp vụ thay; repetition tăng shared version không khiến timer hợp lệ bị bỏ.
- Đủ R=120s nhưng proof/quality thiếu trả blocked reason và giữ episode, không gọi alert RECOVERED.
- Kết thúc cuối DOWN thêm InternalCommand LINK_DOWN_RECONCILE; LinkFlapRule không trực tiếp tạo Link Down.
- Runtime nhận CommandSink theo target_rule_id từ host integration; phía nhận reconciliation và lưu command_id receipt cùng effect trong transaction. Thiếu adapter thì giữ pending có lỗi quan sát được. Bản đầu không có CorrelationEngine.process_command/Rule.on_command vì chưa xây luật Link Down.

## Catalog/config migration

Giữ CorrelationRule/RuleConfiguration strict, extra=forbid; thêm parameters JSON object mặc định rỗng. LF handler validate parameters bằng LinkFlapConfig strict; không phải nơi chứa biểu thức/DSL.

Catalog đề xuất 0.2.0, riêng LF:

```yaml
rule_id: RULE_LINK_FLAP_01
name: Link Flap
enabled: false
window_seconds: 60
threshold: 5
group_by: [device_id, interface_id]
match:
  event_type: INTERFACE_STATUS_OBSERVED
  status_kind: OPER_STATUS
count:
  mode: state_changes
  field: status
parameters:
  recovery_seconds: 120
  time_basis: RECEIVED_TIME
action:
  create_incident: true
  incident_severity: MAJOR
  title: Cổng mạng đổi trạng thái liên tục
```

Không đổi hai rule PSU/BGP hoặc bật chúng. Existing catalog không có parameters vẫn đọc được. LF enabled cần cấu hình runtime hợp lệ; unknown params, bool/float/string thay số nguyên, R≤W hoặc EVENT_TIME phải reject. Validator dùng tham số config; release profile hiện chỉ chấp nhận 5/60/120 đã chốt, không tự cho đổi nghiệp vụ.

Producer capabilities phải xác nhận canonical fields, stable ingress identity/time, ordered durable delivery, progress và durable store. Không lấy union của field names trong BaseModel làm bằng chứng producer đã cung cấp. supported_event_fields hiện có vẫn được kiểm tra; registry thêm capability gate.

## ProcessingReceipt và failure

| status | Ý nghĩa |
| --- | --- |
| COMMITTED | State và mọi ý định được commit; không khẳng định alert bên ngoài đã áp dụng |
| DUPLICATE | ID + canonical content đã commit khớp; không thêm hiệu lực |
| INVALID / ID_COLLISION / ORDER_ERROR | Không mutate state nghiệp vụ; báo lý do, quarantine/health theo mức ảnh hưởng |
| STALE_TIMER | Sai episode/epoch/generation hoặc episode đã kết thúc; no-op |
| RECOVERY_BLOCKED | Chưa đủ proof/health; giữ lịch/blocked reason để xét lại |
| RETRYABLE_ERROR | Timeout/conflict/DB tạm thời; retry giữ ID/time; không ACK như thành công |

Receipt có event/message ID, entity/order, committed_version nếu có và reason code; không ghi raw nhạy cảm trong lỗi.

## Lifecycle / tương thích

Giữ app.state.rule_configuration và /api/health. Khi tất cả rule disabled, startup chỉ nạp catalog như cũ; không đòi DSN. Khi enabled nhưng thiếu adapter/store/proof, startup lỗi rõ ràng, không serve với engine giả.

Lifespan tạo runtime, restore/catch up rồi start worker; shutdown ngừng nhận, đợi UoW đang chạy, dừng tick/outbox và đóng tài nguyên. Với asyncio.to_thread, cancellation không dừng chắc thread: commit/receipt quyết định kết quả cuối, retry idempotent nếu caller mất ACK.

Không thêm endpoint dashboard/ingest hoặc đổi AlertEvent public. Chỉ export symbols thực sự cần cho host integration.

