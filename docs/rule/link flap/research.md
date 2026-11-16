# Phase 0 — Research: Link Flap và module rule chung

**Ngày**: 16/11/2026. **Spec**: [spec.md](spec.md). Nguồn triển khai: `C:/Projects/vnpt/telecom-alert-correlation-n42`.
Đây là kết quả đọc source/tài liệu và nghiên cứu thiết kế; chưa chạy ứng dụng/DB/test hoặc kiểm tra Jira.

## 1. Bằng chứng từ dự án

| Nguồn, tương đối với repository triển khai | Quan sát |
| --- | --- |
| requirements.txt, Dockerfile | Python 3.12; FastAPI ≥0.115; Pydantic ≥2.9,<3; ruamel.yaml ≥0.18.16,<0.19; pytest/pytest-asyncio; chưa có DB driver |
| docker-compose.yml | TimescaleDB dựa PostgreSQL 16; không suy ra container đang chạy |
| app/main.py | Lifespan chỉ nạp catalog vào app.state.rule_configuration; chưa nối pipeline/engine |
| app/models/alert_event.py; app/services/parser.py | AlertEvent strict-extra, mutable; parser sinh UUID mới; chưa có canonical device/interface/status, source order hoặc progress |
| app/models/rule_config.py; app/services/rule_config_loader.py | Config strict, safe YAML 1.2, cấm duplicate keys, kiểm tra supported_event_fields và checksum tùy chọn |
| app/services/rules.yaml | Catalog 0.1.1, ba rule disabled; Link Flap RULE_LINK_FLAP_01 có 5/60, MAJOR, group hostname/interface và đếm link_state |
| app/services/deduplication.py | Fixed processing-time window, RAM và lock cục bộ; không phải detector transition hoặc state bền vững |
| app/store/__init__.py; docker/init-db.sql | Store placeholder; bootstrap chưa có bảng ứng dụng |
| tests/fixtures/rules/review-cases.json | Semantics “first transition notice counts one”; trái baseline-first đã chốt trong chat |
| docs/scenarios/KB-01-link-flap.md | Năm observations được kỳ vọng trigger nhưng chưa có baseline xác định |
| n42-ai-kit/docs/INTERFACES.md | v0.9 đề xuất Pipeline.subscribe/EventStore; replay 60s không đủ phục hồi đợt và outbox |
| AGENTS.md; n42-ai-kit/AGENTS.md; n42-ai-kit/docs/roles/BE3.md | Theo module/owner, synthetic data, test/RTM trước code; schema liên module cần phối hợp. Thiết kế chat là yêu cầu hiện tại, không giả làm TL/QA đã phê duyệt |
| .git/HEAD và ref tương ứng | Đang trỏ feature/N42-18-deduplication-engine, ref 827359f7a7ed8a70459053071954041a0393422f; chưa kiểm chứng working tree sạch |

Không có graphify-out/graph.json; tra cứu trực tiếp bằng rg theo hướng dẫn graphify, không xây graph mới cho lần tra cứu này. README/AGENTS mô tả W1 đã cũ so với source parser/config/dedup hiện có; ưu tiên source khi mô tả hiện trạng.

## 2. Các quyết định

### R01 — Giữ stack và ranh giới module của dự án

**Decision**: Module Python 3.12 trong app/services/correlation, hợp đồng Pydantic v2, pure rule + asyncio orchestration; tiếp tục FastAPI lifespan sẵn có. Không thêm web framework, frontend hoặc microservice.

**Rationale**: Người dùng chỉ định lấy công nghệ từ dự án, hành vi theo chat. Module phải dùng chung cho rule sau.

**Alternatives considered**: Service riêng/DSL tăng triển khai; tái sử dụng DeduplicationWindow làm detector sai trục thời gian và định nghĩa đếm.

### R02 — Lõi nghiệp vụ giữ nguyên các lựa chọn đã chốt

**Decision**: 5 transitions trong [t−60s,t], INITIAL=0, RECEIVED_TIME, R=120s, chỉ transition reset hạn. Rule ID giữ RULE_LINK_FLAP_01; LINK_FLAP là loại luật, không tạo ID thứ hai. Cấu hình vẫn chứa 5/60/120, không đóng đinh thuật toán bằng hằng số không kiểm soát.

**Rationale**: Giữ nhận dạng catalog và yêu cầu người dùng. Runtime validate đúng bộ giá trị phát hành này; R>W là bất biến.

**Alternatives considered**: Đếm transition_notice đầu tiên trái spec; event-time/reorder không thuộc đợt đầu.

### R03 — Envelope chuẩn hóa riêng, không sửa public AlertEvent

**Decision**: Thêm CorrelationEvent và InterfaceObservation bất biến ngoài AlertEvent. Producer cung cấp canonical IDs, OPER_STATUS UP/DOWN và ingress identity/order; adapter chỉ ánh xạ dữ liệu đã chuẩn hóa, không regex message trong rule.

**Rationale**: AlertEvent extra=forbid và có nhiều caller; thay schema toàn hệ thống chưa cần cho lõi. Wrapper giữ evidence UUID và raw_ref để truy vết.

**Alternatives considered**: Thêm optional fields vào AlertEvent sẽ chạm parser/FE/schema rộng; suy device_id từ hostname hoặc interface_id từ tên chưa có mapping sẽ bịa tính ổn định.

### R04 — Identity trước parse; receipt độc lập entity

**Decision**: event_id = định danh ingress ổn định do producer tạo, giữ source_id/source_epoch/source_sequence/received_at khi retry. Không dùng UUID mới mỗi lần parse làm bảo đảm idempotency. Receipt có unique event_id toàn module và bộ source/epoch/sequence, lưu canonical payload/digest.

**Rationale**: Bắt cùng ID đổi entity/status và retry qua restart. Fingerprint gồm schema/type/entity/status/time/source, không gồm processed_at/display enrichment/parser UUID có thể thay sau re-parse.

**Alternatives considered**: ID-only bỏ sót collision; receipt nằm riêng trong entity bỏ sót collision đổi khóa; so mọi metadata tạo collision giả.

### R05 — PostgreSQL transaction cho bản hoàn chỉnh

**Decision**: Metadata dùng bảng PostgreSQL thông thường trong DB Timescale hiện có; thêm psycopg[binary] ≥3.2,<4 khi implement vì repo chưa có driver. Không thêm ORM/pool/Redis/broker chỉ cho module. Test fake store cho lõi, PostgreSQL thật cho persistence/race/restart.

**Rationale**: Cần atomic state+receipt+timer+outbox theo FR-014; RAM prototype không đáp ứng. Không biến lịch in-memory W1–W4 của module khác thành cam kết durability: bản hoàn chỉnh Link Flap chỉ nghiệm thu khi adapter DB xong.

**Alternatives considered**: Chỉ reload 60s hoặc ghi snapshot rồi alert riêng không giữ tổng dài hạn/timer/outbox; DB thứ hai thêm ranh giới commit.

### R06 — DB đồng bộ trong worker thread, không chặn event loop

**Decision**: Engine async gọi một UoW đồng bộ trọn vẹn qua asyncio.to_thread; mỗi UoW có connection riêng và explicit transaction. Rule thuần chạy trong cùng UoW, không await hoặc gọi dịch vụ ngoài transaction. Bắt đầu bằng worker có giới hạn, chưa thêm pool.

**Rationale**: Suy luận thiết kế để giữ một đường thực thi Windows/Linux; tránh yêu cầu đổi event loop của host. Psycopg async không hỗ trợ default Windows Proactor. Chỉ coi ACK thành công khi thread đã commit; hủy coroutine không bảo đảm transaction thread đã dừng, retry vẫn dùng ID gốc.

**Alternatives considered**: AsyncConnection phù hợp Linux nhưng Windows cần Selector policy; gọi DB đồng bộ trực tiếp trong async handler chặn loop. Cả hai không cần cho bản tối thiểu.

### R07 — Một UoW theo entity và ownership có fencing

**Decision**: Khóa entity row, kiểm tra owner token/version/epoch/order, tạo snapshot trước/sau một lần; mọi rule trả outcome. Cùng commit snapshot, state rule, receipt/checkpoint, timer và outbox. Claim/takeover dùng cùng row và tăng fencing token. Không commit state riêng từng rule.

**Rationale**: Rule thứ hai lỗi phải rollback cả baseline. Row lock serialize writer, dispatcher vẫn phải giao đúng thứ tự; lock không sửa upstream order.

**Alternatives considered**: Mutex RAM không chặn process cũ; lease không kiểm tra lúc ghi không đủ. SKIP LOCKED chỉ dùng claim timer/outbox, không bỏ qua event trước của entity.

### R08 — Proof tiến độ bền vững và timer trước event bằng hạn

**Decision**: Lưu proof theo source/epoch, do adapter BE1/BE2 có thẩm quyền công bố từ raw journal/barrier. Recovery ở D cần trusted clock≥D, proof bao phủ ingress received_at≤D, mọi event<D đã áp dụng; event=D đã staging, chạy sau timer. Health/gap/epoch phải được kiểm tra lại lúc commit, không tự nâng frontier từ wall clock hoặc event lớn nhất.

**Rationale**: Giữ semantics đúng khi worker chậm và khi raw còn chờ parse. Proof là dependency thật; adapter fake chỉ chứng minh thuật toán.

**Alternatives considered**: Queue rule rỗng không đủ; áp dụng event=D trước timer đổi cách chia đợt.

### R09 — Một outbox cho decision/command, thứ tự xuyên đợt

**Decision**: Outbox có message_kind DECISION/COMMAND. Stream key gồm kind+rule+entity; stream_seq tăng xuyên episode, episode_seq giữ riêng. Consumer mỗi loại chỉ nhận stream của mình. Decision ID xác định từ stream+seq; counters tuyệt đối. Giao at-least-once, áp dụng idempotent; dispatch stream head, không cho sequence sau vượt bản chưa ACK.

**Rationale**: Recovery đợt A phải được áp dụng trước trigger đợt B; command Link Down cần consumer riêng và không tạo gap giả trong decision stream.

**Alternatives considered**: Sequence chỉ trong episode không bảo vệ thứ tự xuyên đợt; tăng counter tương đối dễ nhân đôi.

### R10 — Migration config và fixture đồng bộ, activation có kiểm tra capability

**Decision**: Giữ loader strict và disabled mặc định. Catalog đề xuất 0.2.0: riêng LF chuyển group_by=[device_id,interface_id], match normalized event_type/status_kind, count.field=status; thêm parameters recovery_seconds=120/time_basis=RECEIVED_TIME. parameters là JSON map ở catalog chung nhưng handler LF phải validate bằng model strict có kiểu; unknown parameter bị reject khi bind. Hai rule khác giữ nguyên và disabled.

**Rationale**: Registry mở rộng không ép tham số recovery của LF lên mọi rule. supported_event_fields phải từ producer thật; bind còn kiểm tra identity/order/progress/store capability, không suy từ field names.

**Alternatives considered**: parameters không validate trái trust boundary; bật YAML trước producer sẽ làm rule tưởng dữ liệu đầy đủ.

Fixture mới có version mới và baseline rõ. Giữ fixture 0.1.1 như historical artifact nếu cần, tạo candidate-0.2.0.yaml/review-cases-0.2.0.json; cập nhật tests chọn cặp mới, không sửa lịch sử thành “đã chạy”.

### R11 — Tích hợp có điều kiện, không mở rộng sản phẩm

**Decision**: Chuẩn bị adapter Pipeline.subscribe + progress, outbox consumer contract và LINK_DOWN_RECONCILE. Nếu chưa có producer thật, phát triển/test lõi với fake có khai báo; production activation từ chối thiếu capability. Khi LF disabled, health/config startup cũ tiếp tục chạy không cần DB.

**Rationale**: Không tự nhận đã hoàn thành Collector, Link Down, Alert Manager hoặc dashboard. Có thể tiến hành implementation module mà chưa nghiệm thu pipeline đầy đủ.

**Alternatives considered**: Mock giả health GOOD để bật production hoặc tạo trực tiếp Link Down từ rule sẽ che dependency thiếu.

### R12 — Các mặc định triển khai được nêu rõ

**Decision**: Worker tick 5s là lựa chọn triển khai đề xuất, không là SLA; all valid OPER_STATUS được đếm, chưa suppress bảo trì. Không tự đặt retention production; giữ receipt/checkpoint/state khi còn khả năng retry/replay hoặc đợt mở. Chưa hứa tải/latency.

**Rationale**: Không có thêm yêu cầu đã duyệt về suppression, retention hoặc hiệu năng. Đo sau khi tính đúng; không xóa dữ liệu để giảm RAM mà vẫn tuyên bố đầy đủ.

**Alternatives considered**: Tự dùng 7 ngày/1.000 interface làm cam kết vượt quá dữ liệu hiện có.

## 3. Nguồn kỹ thuật chính thức đã kiểm tra

- [Psycopg transactions](https://www.psycopg.org/psycopg3/docs/basic/transactions.html): explicit transaction và rollback/commit.
- [Psycopg concurrent operations](https://www.psycopg.org/psycopg3/docs/advanced/async.html): connection sharing/transaction và giới hạn Windows async.
- [PostgreSQL 16 row locking](https://www.postgresql.org/docs/16/explicit-locking.html#LOCKING-ROWS): serialization theo hàng.
- [PostgreSQL 16 SELECT locking clauses](https://www.postgresql.org/docs/16/sql-select.html#SQL-FOR-UPDATE-SHARE): SKIP LOCKED thích hợp queue, không là thứ tự nghiệp vụ.
- [Pydantic models](https://pydantic.dev/docs/validation/latest/concepts/models/#faux-immutability): frozen không bảo đảm nested dict/list bất biến; dùng tuple/frozen nested models cho input.
- [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/): tái sử dụng lifecycle hiện có.

Các quyết định R01–R12 là thiết kế đề xuất của lượt plan dựa trên lựa chọn người dùng/source, không phải ghi nhận phê duyệt nhóm. Không còn lựa chọn công nghệ bị bỏ trống; các dependency thực thi được chỉ rõ tại plan/contracts.

