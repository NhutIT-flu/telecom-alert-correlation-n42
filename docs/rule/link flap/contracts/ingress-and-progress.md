# Contract v1 — Ingress, ordering và progress

**Owners theo tài liệu dự án**: BE1/BE2 cung cấp producer/pipeline; BE3 nhận và cung cấp module correlation. Chưa đối chiếu Jira hiện thời.
Hợp đồng này thay giả định v0.9 “subscribe và replay 60s là đủ” cho phần durability Link Flap theo thiết kế chat.

## Input required

CorrelationEvent gồm schema_version=1; event_id; event_type=INTERFACE_STATUS_OBSERVED; entity_kind=interface; entity_key; source_id/source_epoch/source_sequence; ordering_seq; processing_epoch; received_at; payload InterfaceObservation; raw_ref; evidence_event_id tùy chọn.

InterfaceObservation cung cấp device_id/interface_id canonical, status_kind=OPER_STATUS, status=UP/DOWN; event_timestamp nullable và vendor/mnemonic chỉ là bằng chứng. Không parse body trong rule. Không dùng tên interface/hostname làm canonical ID nếu chưa có mapping authority.

IngressMetadata tạo trước parser: identity ổn định và received_at lần đầu, source sequence trong epoch. Re-parse phải giữ metadata này kể cả AlertEvent.id của parser thay. event_id là ID ingress chuẩn; evidence_event_id là ID đối tượng parser để trace, không dùng làm identity dedup.

parse_status=fallback hoặc thiếu canonical/status phải quarantine trước correlation, không bị coi là baseline hợp lệ. Empty fields/naive time/source order sai đều có mã lỗi.

## Identity và canonical content

Fingerprint SHA-256 của canonical JSON cố định gồm schema/type, entity kind/key, source identity/sequence, processing epoch, UTC received_at, device/interface/status_kind/status, event_timestamp UTC/null và raw_ref ổn định. Serialize key order xác định và timestamps chuẩn microsecond; không tính evidence UUID mới, display name, retry_count, processed_at hoặc parser version.

Cùng event_id/content → duplicate. Cùng ID/content khác hoặc cùng source/epoch/sequence nhưng ID khác → collision; rollback mọi state, giữ bản gốc và diagnostic. Không dùng hash thay kiểm tra schema; có thể đối chiếu canonical content lưu kèm khi collision.

Sửa mapping/status của input đã commit là correction/reconciliation có audit/epoch riêng, không giả làm retry cùng identity.

## Ordering và ACK

- Nguồn có thẩm quyền nhận log theo source_sequence; normalizer có thể song song nhưng admission phải giữ raw order.
- ordering_seq là cursor tăng theo entity trong journal dùng chung; không đòi source_sequence liên tiếp trên từng interface, vì source còn có log entity khác.
- Event cùng received_at dùng ingress order. Clock lùi hoặc đổi nguồn làm received_at giảm phải block luồng ảnh hưởng và reconcile/epoch, không clamp thời gian.
- Producer ACK raw/delivery sau commit module hoặc journal trung gian bền vững có retry. Không coi callback được gọi là đã lưu.
- Các raw không thuộc correlation vẫn phải được pipeline xử lý terminal để source barrier không mắc ở gap giả; raw invalid ảnh hưởng tín hiệu phải có quality/gap thật, không âm thầm đánh dấu đầy đủ.
- Mutex/row lock chỉ serialize ghi, không thay việc chọn đúng next event từ dispatcher.
- Khi thay mode/config/owner, tạo barrier/drain/checkpoint; active episode pin config cũ. Bản đầu không nhận EVENT_TIME.

## Progress proof

SourceProgressProof lưu source_id/source_epoch, proof_version, barrier_cursor, admitted_through (UTC), trusted_clock, ingest_health, source_delivery_health và known_gap/outage. Producer phải chứng minh mọi raw nhận đến admitted_through đã chuẩn hóa/kiểm định và đưa vào lịch, không còn raw trước barrier đang xử lý mà bị bỏ ngoài proof.

Backend correlation lưu proof bền vững và đọc proof version/health dưới khóa cùng UoW recovery. Cập nhật health/gap của pipeline phải phối hợp cùng store/lock order; stale cache không cho phép recovery.

Tại deadline D:

1. Trusted clock ≥D.
2. Admission proof bao phủ received_at≤D, gồm raw và normalized.
3. Mọi event có received_at<D đã áp dụng cho entity.
4. Event=D đã nằm trong lịch nhưng chưa observe; timer chạy trước event đó.
5. Episode/epoch/generation hiện hành, snapshot UP/DOWN hợp lệ.
6. ingest_health=GOOD; không có gap/outage/quality lỗi đã biết. source_delivery_health=UNVERIFIED được phép LAST_OBSERVED; KNOWN_OUTAGE chặn.

admitted_through khác applied checkpoint. Queue rule rỗng, max event time, event source im lặng hoặc wall clock tự trôi không phải proof.

Heartbeat/barrier ingest có thể tiến khi không có log mới, nhưng không xác minh thiết bị/đường truyền UDP. Nếu chưa có implementer/proof thật, runtime không tự synthesize GOOD; test dùng fake phải khai báo rõ.

## Resume, restore và nhiều nguồn

Restore ownership/config/snapshot/state/receipts/timers/outbox/progress trước, tiếp tục durable journal từ checkpoint, bắt kịp backlog rồi đánh giá timer. Replay giữ nguyên identity/received_at.

Mất dữ liệu/clock lỗi cần reconciliation có audit hoặc baseline mới và epoch mới; không gọi reset là recovery. Nhiều Collector chưa có merge/identity chung nằm ngoài bản đầu, phải reject cấu hình cam kết “một nguồn” bị vi phạm.

**Nghiệm thu tích hợp bắt buộc**: raw trước D chưa parse chặn timer; event<D staged chưa apply chặn; event=D chạy sau timer; heartbeat không log vẫn cung cấp barrier; health đổi sau proof phải chặn recovery stale; restart còn backlog không đóng ngay.

