# Data Model — Link Flap và correlation module

**Spec**: [spec.md](spec.md). **Contracts**: [rule module](contracts/rule-module.md), [ingress/progress](contracts/ingress-and-progress.md), [delivery](contracts/decision-delivery.md).
Đây là logical model để implement; chưa tạo bảng hoặc đổi public AlertEvent.

## Quy ước chung

- UTC aware datetime trong Python; TIMESTAMPTZ ở PostgreSQL, JSON timestamp chuẩn UTC với tối đa 6 chữ số phần lẻ. Không dùng float/round-to-second cho cửa sổ.
- EntityKey = (entity_kind, canonical_key). canonical_key là JSON array string không mơ hồ, ví dụ ["SW-01","if-0001"]; interface dùng device_id+interface_id. Entity khác tự định nghĩa key qua descriptor.
- event_id có phạm vi toàn module, ổn định từ durable ingress. Source epoch khác processing epoch của ordering/config.
- State schema, rule/config version và time_basis lưu bền vững; immutable config snapshot+hash được pin cho đợt, không chỉ giữ đường dẫn YAML mutable.
- Đầu vào/snapshot dùng frozen nested models và tuple; không chuyển tiếp AlertEvent mutable hoặc nested dict/list dùng chung tới rule.

## Record nghiệp vụ

| Record | Trường chính | Validation / quan hệ |
| --- | --- | --- |
| CorrelationEvent | schema_version=1, event_id, event_type, entity_kind/key, source_id/epoch/sequence, ordering_seq, processing_epoch, received_at, payload, raw_ref, evidence_event_id? | IDs không rỗng; sequence integer strict; UTC aware; entity/payload khớp; received_at/order không giảm trong epoch |
| InterfaceObservation | device_id, interface_id, interface_name?, status_kind=OPER_STATUS, status=UP/DOWN, event_timestamp?, vendor?, mnemonic? | Canonical ID từ producer mapping; tên hiển thị không làm key; timestamp thiết bị không dùng tính thời gian |
| InterfaceSnapshot | status UNKNOWN/UP/DOWN, status_since?, last_transition_at?, last_observed_at?, last_event_id?, version, data_quality | INITIAL đặt status_since, transition_at vẫn null; repetition không đổi status_since/transition_at |
| TransitionEvidence | event_id, received_at, from_status, to_status | from/to đã biết và khác nhau; cùng key; event tạo transition đúng một lần |
| LinkFlapState | schema/version, config_snapshot/hash, processing_epoch, time_basis, transitions tuple, window_as_of, active_episode?, stream_counters | Q chứa toàn bộ transition hợp lệ tại as-of, không cap 5; state được lưu cả khi NO_ACTION; counter DECISION và COMMAND riêng, nằm ngoài active_episode |
| ActiveEpisode | episode_id, episode_started_at, detected_at, last_transition_at, recovery_due_at, total_transition_count, timer_generation, episode_seq, recovery_blocked_reason? | start là Q đầu tại trigger; total khởi tạo len(Q); due=last+120s; total không giảm |
| TimerCommand | rule_id, entity, episode_id, processing_epoch, generation, due_at, expected_state_version? | Episode/epoch/generation quyết định stale; version conflict phải reload, không tự loại timer |
| SourceProgressProof | source/epoch, proof_version, barrier_cursor, admitted_through, health, known_gap/outage, trusted_clock, published_at | Chỉ producer có thẩm quyền phát; raw≤barrier không còn chưa kiểm định; health có version |
| RuleOutcome | next_state, decisions tuple, timer_changes tuple, commands tuple | NO_ACTION vẫn có thể đổi state; không thực hiện side effect trực tiếp |
| OutboxMessage | message_id, kind, rule/entity, stream_seq, episode_id/seq, payload, delivery metadata | ID xác định; số đếm tuyệt đối; stream riêng theo kind để decision consumer không bị gap bởi command |

## Baseline và lifecycle

| Trước | Quan sát / điều kiện | Sau / effect |
| --- | --- | --- |
| UNKNOWN | UP hoặc DOWN đầu | Baseline; 0 transition |
| UP/DOWN | Cùng trạng thái | Repeated; cập nhật last_observed, không đổi due/total |
| UP/DOWN | Trạng thái ngược | Một transition, prune thời gian <t−60s rồi thêm t |
| Chưa có episode | Q đạt 5 | Tạo episode; total=len(Q); start=Q đầu; detected=t; due=t+120s |
| Episode mở | Transition mới trước due | Update cùng episode, total+1, due mới, generation+1 |
| Episode mở | Timer đạt due và proof/quality đủ | RECOVERED/LAST_OBSERVED; STABLE_UP hoặc STABLE_DOWN; clear episode/Q, giữ baseline |
| Episode mở | Event đúng/sau due, đủ proof | Timer cũ trước event; event thuộc theo dõi mới |
| Episode mở | Thiếu proof/backlog | Chờ; không tự kết thúc. Áp dụng dữ liệu trước hạn theo thứ tự rồi xét lại |
| Episode mở | Gap/outage/quality lỗi đã biết | Giữ mở có lý do, yêu cầu reconciliation; không tự hết lỗi sau 120s |
| Không còn state và thiếu lịch sử | Restart | UNKNOWN/DEGRADED, giữ hồ sơ mở bên alert; không tạo recovery giả |

At recovery, window count báo 0 as-of deadline (R>W) và total cuối giữ nguyên. last_known_status là snapshot ngay trước event cùng deadline. Workflow bên Alert Manager không thuộc LinkFlapState.

## Persistence: năm bảng PostgreSQL thường

| Bảng dự kiến | Key / trường | Index / ràng buộc |
| --- | --- | --- |
| correlation_entity_states | PK(entity_kind,entity_key); snapshot JSONB, rule_states JSONB, processing_epoch, last_applied_ordering_seq, version, owner_id, fencing_token, lease_expires_at | JSON chứa schema version và config snapshot từng rule; row lock cho UoW; version/fence conditional update |
| correlation_event_receipts | event_id PK; source_id/epoch/sequence, entity, processing_epoch, canonical_payload JSONB, payload_sha256, ordering_seq, committed_at, processing_result | UNIQUE(source_id,source_epoch,source_sequence); lookup độc lập entity; unique(entity,processing_epoch,ordering_seq) theo hợp đồng journal; result chỉ ghi khi commit |
| correlation_source_progress | PK(source_id,source_epoch); proof fields, proof_version, admission cursor, applied/replay checkpoint được upstream xác nhận | Proof không được tự suy từ event max; index phù hợp source/epoch; update health/proof phối hợp cùng lock order |
| correlation_timers | PK(rule_id,entity_kind,entity_key); episode_id, epoch, generation, due_at, claim_owner/until | due_at index; replace generation atomically; claim không thay kiểm tra UoW |
| correlation_outbox | message_id PK; kind, rule/entity, stream_seq, episode_id/seq, payload JSONB, attempts, next_attempt_at, lease, acknowledged_at | UNIQUE(kind,rule_id,entity_kind,entity_key,stream_seq); index pending/due; gửi đúng stream head |

Không dùng hypertable cho các metadata mutable/unique này. alert_events/grouped_incidents hiện chưa có implementation; không tự tạo chúng ở migration module. Consumer production có mapping/receipt/open-slot riêng theo delivery contract.

Counter cấp theo đầy đủ (message_kind,rule_id,entity_kind,entity_key), tăng cùng UoW ghi message và không reset khi recovery/đổi episode. COMMAND không tiêu thụ sequence DECISION. Receipt command thuộc CommandSink phía nhận và commit cùng effect của phía đó; không đưa command thiếu ingress sequence vào correlation_event_receipts.

### Một unit of work

1. Lock progress row cần dùng trước, rồi entity row theo thứ tự cố định; tạo entity row bằng insert-on-conflict khi chưa có. Mọi đường timer/event/claim ownership dùng cùng lock order.
2. Kiểm tra ownership/fencing, epoch/order và global receipt; race cùng event_id khác entity bị unique constraint chặn, rollback rồi đọc receipt để phân loại.
3. Tính timer đủ điều kiện trước event, tạo immutable snapshot một lần, chạy các rule; không await HTTP/notification.
4. Lưu snapshot và mọi rule state, receipt/checkpoint, timers, outbox cùng transaction; final write kiểm tra expected version/token và lease hợp lệ. Token takeover cũng dùng khóa entity, không cấp trong RAM.
5. Commit mới ACK. Lỗi rollback toàn bộ; retry loại tạm thời bằng identity cũ. Collision ghi diagnostic/quarantine riêng sau rollback, không mutate baseline/Q đã commit.

Không đọc proof từ cache không khóa rồi commit recovery trong khi source đã đổi health. Adapter cập nhật progress phải dùng cùng transaction store/lock discipline; không cung cấp được bảo đảm này thì chưa đạt production gate.

### Retention và restore

Không prune baseline chỉ vì interface im lặng. Không xóa episode/timer/outbox pending. Receipt TTL chỉ được có sau khi replay horizon và durable full-prefix checkpoint chứng minh input cũ không tái áp dụng; bản đầu chưa thêm tự động TTL. Không khẳng định checkpoint mới nhất của riêng interface là proof source đầy đủ.

Restore snapshot/state/config/timer/outbox/progress trước, lấy lại ownership, catch up raw journal qua adapter rồi mới xét recovery. Thiếu journal/state phải chờ reconciliation có audit; việc replay 60s gần nhất không thay quy trình này.

