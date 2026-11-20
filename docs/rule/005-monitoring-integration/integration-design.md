# Thiết kế hợp đồng tích hợp giám sát

Ngày: 2026-11-20. Trạng thái: đề xuất, chưa triển khai/đo tải.
[Yêu cầu nghiệp vụ](spec.md), [schema 001](../001-alert-data-model/data-model.md),
[vòng đời 002](../002-alert-lifecycle/lifecycle-design.md),
[engine 003](../003-rule-dispatch-correlation/engine-design.md),
[LinkFlap 004](../004-link-flap-rule/link-flap-design.md).

## 1. Phương án và ranh giới

| Phương án | Quyết định/đánh đổi |
|---|---|
| Polling PostgreSQL + frontend polling API | Chọn bản đầu: ít thành phần, nguồn kết quả bền vững, thêm độ trễ chu kỳ đọc |
| NOTIFY/SSE hoặc WebSocket | Để sau khi có nhu cầu giảm chu kỳ; wake-up không thay việc đọc bù/snapshot |
| Broker/outbox và nhiều worker | Chưa chọn; cân nhắc khi cần tải/HA hoặc bảo đảm phát từng thông báo |

UDP/API/file → lưu raw → chuẩn hóa → lưu field/status → worker chủ động nhận việc theo 003
→ commit alert/evidence/history/checkpoint → API đọc snapshot → frontend.
Handler không gọi frontend hoặc mở DB. FastAPI không sở hữu correlation state.
Heartbeat và receipt là dữ liệu hệ thống trong pipeline_runtime_status, không tạo events giả.

## 2. Hợp đồng sự kiện và chuẩn hóa v1

### 2.1. Projection

| Nguồn lưu | Field đưa vào engine | Kiểm tra |
|---|---|---|
| events.id | event_id | Định danh BIGINT do server cấp, không là thứ tự nguồn |
| event_type | event_type | Loại nghiệp vụ chuẩn; interface_state_change khi đúng nghĩa |
| event_time/event_time_raw/time_status | Tương ứng | UTC có căn cứ; unknown không tự thay bằng received_at |
| received_at | received_at | Giờ server lúc nhận |
| device_id/correlation_scope | Tương ứng | Danh tính/nguồn được server xác định |
| attributes.interface_name | interface_name | Chuỗi không rỗng, tên chuẩn trong thiết bị, không gộp alias tùy tiện |
| attributes.interface_state | interface_state | UP hoặc DOWN |
| attributes.interface_layer | interface_layer | physical hoặc protocol, có bằng chứng ánh xạ |

~~~json
{
  "event_type": "interface_state_change",
  "attributes": {
    "interface_name": "GigabitEthernet0/0",
    "interface_state": "DOWN",
    "interface_layer": "physical"
  }
}
~~~

- Field cũ attributes.state chỉ được adapter hỗ trợ chuyển sang interface_state khi giá trị
  up/down ánh xạ rõ; nếu cả hai có và mâu thuẫn thì partial/diagnostic, không chọn tùy tiện.
  Biểu diễn lưu chuẩn chỉ dùng interface_state; raw đầu vào giữ nguyên.
- Giá trị văn bản được ánh xạ enum tại biên; không lower-case/đổi alias interface.
  Thông điệp LINK và LINEPROTO được parser xác định lớp, không mặc định physical khi thiếu.
- Hãng/OS/type dựa inventory/message có căn cứ, lưu nguồn nhận diện. Cisco/Juniper phải
  có fixture thật từ lab hoặc giả lập đã gán nhãn trước bật mapping; format khác giữ raw.
- Byte lỗi giữ raw_bytes, text escape chỉ phục vụ hiển thị. JSON đã chuẩn hóa giữ nguyên
  JSON text ở raw_message, source_metadata.raw_kind=normalized_json; không giả raw thiết bị.
- Source tự khai thời gian/thiết bị được kiểm tra, không nhận correlation_status, actor,
  received_at hoặc workflow như quyền ghi. partial chỉ vào rule đủ field; unknown-time không
  đủ cho cửa sổ thời gian và tạo diagnostic/time guard theo 003.
- source_metadata.normalization_schema_version=1 và parser_revision xác định adapter đã dùng.
  Chuẩn hóa lại chỉ trước hoàn tất tương quan/bằng chứng theo 001; không sửa lịch sử đã công bố.

### 2.2. Time policy

Cấu hình nguồn lab có timezone/year inference, căn cứ clock_trusted và thời hạn kiểm chứng;
không có policy đáng tin thì không bật quiet recovery cho nguồn đó. Inferred phải có nguồn
bổ sung rõ, không tự dùng giờ nhận làm giờ thiết bị. Timestamp quá tương lai theo giới hạn
cấu hình hoặc sequence mâu thuẫn tạo diagnostic và guard nhóm/scope; không treo vô hạn heap.
Đánh giá độ lệch không phân biệt chắc chắn được trễ vận chuyển với clock sai; không tuyên bố
đã đo offset thiết bị chỉ từ received_at-event_time, không polling thiết bị trong phạm vi này.

## 3. Tiếp nhận và giới hạn

| Kênh | Hành vi |
|---|---|
| UDP lab | Một datagram syslog là một lần nhận; lưu raw trước parse, không có ACK ứng dụng |
| Log đơn văn bản/JSON | Xác thực nguồn, kiểm tra kích thước/envelope, lưu rồi trả event_id |
| File text/JSON Lines | Streaming theo dòng/lô có giới hạn, gán import_id/số dòng do server, trả kết quả phần đã lưu |

Giá trị thử: max_event_bytes=16.384, max_request_bytes=1.048.576,
max_file_bytes=52.428.800 và import_batch_events=500. Cấu hình kiểm tra số nguyên dương,
quan hệ giới hạn và tài nguyên trước khởi động. UDP phải đọc đủ datagram trong giới hạn
vận chuyển để phát hiện quá kích thước; không coi phần bị cắt thành syslog đầy đủ.
Đầu vào quá giới hạn bị từ chối/đếm rejected, chưa được coi là event đã chấp nhận.

API có phản hồi: chỉ trả accepted sau commit raw; lỗi DB trả lỗi lưu, không thành công giả.
Một dòng lỗi định dạng nhưng trong giới hạn vẫn lưu raw rồi parse failed/partial; tệp
quá giới hạn hoặc lỗi ghi giữa chừng trả partial/error với import_id, accepted_count và
failed_line/range khi xác định được. Không rollback/xóa phần đã báo lưu thành công của lô trước.
Truy vết bằng events.source_metadata.import_id/line_number; không thêm bảng jobs ở bản đầu.

File và dữ liệu khai lịch sử nhận scope replay riêng ngay từ đầu, mặc định search-only.
Đánh giá chủ động cần quyền correlation:replay và chỉ đổi pending trong scope đó.
API live chỉ cho nguồn events:ingest:live được cấu hình; không tin scope tùy ý trong body.

Gửi lại cùng raw bằng lần nhận mới có thể tạo event mới. Bản đầu chưa hứa idempotency
truyền/nhập toàn tệp khi phản hồi bị mất; kết quả theo import_id cho biết phần đã lưu
khi client còn định danh. Không áp dedup hash làm mất log lặp thật.

Khi không thể lưu/đầy dung lượng: API từ chối rõ, collector tăng dropped/storage_error
và health degraded/error; UDP không backpressure được về thiết bị, không hứa giữ gói chưa lưu.
Giới hạn bộ nhớ của ingest/normalizer độc lập với ngân sách correlation tại 003.

## 4. Danh tính và quyền lab

Bản đầu dùng principal/token cấu hình phía server, secret cấp qua môi trường hoặc secret mount,
không commit token thật. Token nhận qua Authorization, không đặt URL hoặc log; token người
dùng trên frontend giữ trong bộ nhớ phiên, không nhúng vào bundle. So sánh credential an toàn,
response lỗi không lộ secret. TLS khi truy cập ngoài môi trường localhost tin cậy.

| Profile/capability | Quyền mặc định |
|---|---|
| viewer | events:read, alerts:read, health:read |
| operator | Quyền viewer + alerts:ack, alerts:close |
| ingest principal | events:ingest:live và/hoặc events:ingest:history theo cấu hình nguồn |
| maintenance capability | correlation:retry, correlation:replay, correlation:rebuild được cấp riêng, không mặc định cho viewer/operator |

Mỗi request được kiểm tra quyền phía server; actor_id từ principal đã xác thực.
Không nhận actor/status/scope do body tự khai như bằng chứng quyền. Maintenance chỉ phục hồi
xử lý/đánh giá lịch sử, không cấu hình thiết bị hoặc UI sửa rule.
UDP lab giới hạn nguồn/mạng được phép; sender_ip không tự là định danh xác thực của thiết bị.
Không thêm bảng tài khoản hoặc đăng ký tài khoản; mô hình danh tính production là bước riêng.

## 5. Giao tiếp API và đồng bộ màn hình

### 5.1. Bề mặt tối thiểu

| Giao tiếp | Hợp đồng |
|---|---|
| POST /ingest/events | Nhận văn bản hoặc JSON đã chuẩn hóa; trả ID sau commit, scope do server cấp |
| POST /ingest/files | Nhập có giới hạn; trả import_id và số dòng đã lưu/lỗi, không hứa job nền đầy đủ |
| GET /events | Bộ lọc 001, cursor thời gian+id, giới hạn trang, scope được kiểm tra |
| GET /alerts, GET /alerts/{id} | Snapshot đã commit, state_version, outcome và bằng chứng/metadata |
| GET /alerts/{id}/history, GET /alerts/{id}/events | Timeline/bằng chứng, phân trang ổn định, không đổi state |
| POST /alerts/{id}/ack, POST /alerts/{id}/close | expected_state_version bắt buộc cho thay đổi; actor từ auth, semantics theo 002 |
| POST /events/{id}/retry | correlation:retry, reason/request_id; chỉ đưa failed lại pending theo receipt/registry cũ |
| POST /replays/{scope}/evaluate | correlation:replay, scope nhập lịch sử tồn tại và có quyền; không đổi thành live |
| POST /correlations/rebuild | correlation:rebuild; request_id/reason/causal_event_id, revision/scope/group và range trong horizon; không sửa raw hoặc bản closed |
| GET /health | Health pipeline/backlog/freshness, không lộ config/secret |

Chi tiết transport: 400 đầu vào không hợp lệ, 401 chưa xác thực, 403 thiếu quyền,
404 không tìm thấy trong phạm vi được phép, 409 version/failed state xung đột,
413 quá kích thước, 503 không lưu/không sẵn sàng. Retry và ACK/CLOSE đã đạt đích trả snapshot
hiện hành khi có quyền, không nhân đôi audit. Không nhận signal_status do client đặt.

### 5.2. Frontend polling

- active_view_refresh_ms=1000 là giá trị thử; chỉ một request đang chạy cho cùng view,
  không chồng request khi server chậm. Response về trễ từ bộ lọc cũ không được ghi đè view mới.
- Bản đầu tải lại snapshot trang hiện hành và bộ đếm theo filter, không dùng MAX(id) như
  cursor cập nhật. Phân trang history/event dùng keyset theo 001.
- Mất kết nối: giữ dữ liệu trước, gắn stale/last_successful_refresh_at, hiển thị lỗi ngắn.
  Retry có khoảng chờ tăng dần tối đa 10 giây; khi trở lại/đổi view/ACK thành công thì tải
  snapshot mới, không áp optimistic CLOSE mà chưa có phản hồi server.
- Lỗi 409 buộc tải lại; 401/403 hiển thị hết phiên/thiếu quyền; rỗng không là lỗi.
  Tín hiệu/mức độ dùng chữ và màu, thao tác có nhãn/keyboard; không dùng màu làm căn cứ duy nhất.
- Không yêu cầu worker gửi từng transition trực tiếp. Nếu commit xong worker dừng,
  lần GET tiếp vẫn thấy dữ liệu. Timeline DB giữ trung gian ngay cả khi UI không nhìn thấy
  từng thay đổi giữa hai lần poll. Muốn thông báo có phát lại phải thiết kế riêng.

## 6. Health và coverage bền vững

Schema pipeline_runtime_status thuộc 001 mục 13. Đây là bảng chung cấp pipeline:
component, scope, instance_id, status, heartbeat_at, coverage_started_at, details và updated_at.
Bản đầu có writer được chỉ định cho collector, normalizer, correlator; không để các API worker
tự ghi đè cùng heartbeat. Quyền ghi health thuộc service principal/DB role tương ứng.
Component session/owner cũ không được ghi sau khi mất quyền; chuyển owner qua đường kiểm soát.

- heartbeat_interval_seconds=1; heartbeat_stale_seconds=3, dùng giờ DB/server tin cậy.
  Gap >3 giây giữa hai lần ghi hoặc service restart không có chứng cứ liên tục phải reset
  coverage_started_at; status healthy không tự nối qua khoảng trống.
- Khi degraded/error/stopped hoặc coverage chưa biết, coverage_started_at=NULL.
  Lần đầu healthy lại đặt mốc mới. Healthy không có nghĩa backlog đã drain; timer còn phải
  kiểm tra raw parse-pending/failed/workset theo 003.
- Mỗi heartbeat dùng giao dịch ngắn, không đánh dấu processed hoặc tạo raw event.
  Nếu DB lỗi không ghi được thì API/engine coi heartbeat cũ là stale, service báo lỗi local.
- Readiness correlator khác coverage nguồn: correlator restart rồi xử lý đủ receipt/input có thể
  dùng lại coverage upstream được chứng minh; không lấy giờ process start mới để xóa đoạn đó.
- coverage đã xác nhận đến đâu được checkpoint trong envelope engine để rebuild đoạn cũ;
  bản runtime hiện hành không chứng minh các gap quá khứ đã bị ghi đè. Thiếu căn cứ thì
  unknown/quan sát lại, không tự hợp nhất các đoạn healthy rời.
- Receipt nằm tại details.inflight của row component=correlator như 003 mục 13;
  health update phải giữ receipt/rebuild request, không thay cả JSONB.
  Receipt clear cùng transaction kết quả. Row này không bị retention xóa khi còn inflight.
- Live API đơn lẻ và file không tự tạo cam kết quan sát liên tục của một thiết bị.
  Nguồn muốn quiet recovery phải có time/coverage policy được xác minh cho lab.
  Bản đầu không suy deadline wall-clock cho replay search-only.

Rebuild sau correction_incomplete là thao tác riêng: kiểm tra quyền/range/budget, ghi audit
trên event nguyên nhân và một request vào runtime details.rebuild_request (bản đầu một request
đang chờ mỗi scope; request khác trả conflict). Worker xử lý theo mode rebuild và hòa giải 003;
clear request/kết quả/audit cùng checkpoint. request_id trùng trên event nguyên nhân trả kết quả
đã lưu; không đánh dấu lại event processed thành pending hoặc bỏ qua idempotency thông thường.
Thiếu dữ liệu tiếp vẫn incomplete; không tự quét toàn lịch sử.

Replay chủ động chọn revision, source_start_at/evaluation_start_at và source_end_at có căn cứ.
Log trigger phải sau evaluation_start_at/ranh giới hợp lệ của replay; có thể dùng baseline trước.
activated_at live không loại log lịch sử. Quiet theo event-time chỉ chạy nếu input context
được cấp quyền và xác nhận coverage_complete cho đoạn đó; mặc định không dùng clock hiện tại
hoặc im lặng sau EOF làm bằng chứng phục hồi. Thiếu coverage có thể tạo alert nhưng không tự hết.

GET /health kết hợp freshness/health rows, backlog và reason; phân biệt API available,
correlation ready và observation safe. Màn hình không đổi health pipeline thành trạng thái
thiết bị DOWN/UP. Từng nhóm có guard riêng nếu clock/order mâu thuẫn.

## 7. Kiểm chứng tích hợp và phạm vi tiếp theo

| Mã | Tình huống | Kết quả |
|---|---|---|
| I01 | UDP/API/file hợp lệ và lỗi byte/format | Raw đúng, nguồn/ID/scope và parse status đúng |
| I02 | Quá event/request/file limit hoặc DB lỗi giữa lô | Từ chối/partial rõ, không thành công giả hoặc mất phần đã lưu |
| I03 | JSON đã tách và field cũ/mâu thuẫn | raw_kind đúng, một schema chuẩn hoặc diagnostic |
| I04 | Cisco/Juniper cùng hiện tượng và sai lớp | Cùng mapping đúng; không gộp physical/protocol |
| I05 | Source tự đặt actor/scope/status hoặc thiếu quyền | Từ chối/ghi trường server, không vượt quyền |
| I06 | Tệp search-only và replay chủ động | Scope tách, không thay live |
| I07 | Worker tự nhận sau normalization commit | Không cần gọi rule trực tiếp; rollback không tạo dữ liệu sẵn sàng giả |
| I08 | Commit alert xong worker dừng trước thông báo | GET/poll vẫn thấy snapshot/history |
| I09 | Response view cũ, reconnect, request chậm | Không ghi đè filter mới/chồng request, stale/refresh đúng |
| I10 | ACK/CLOSE stale/no-op và retry cùng request_id | Theo 002/003; không nhân audit, đúng actor/quyền |
| I11 | Heartbeat stale/gap/instance cũ/DB không ghi health | Observation unsafe, chặn quiet, health không tạo events |
| I12 | Backlog raw hoặc failed trước deadline | Không suy healthy=đã xử lý hết; giữ barrier |
| I13 | Correlator restart với/không đủ coverage | Dựng lại đoạn được chứng minh hoặc quan sát lại |
| I14 | Secret/dữ liệu mẫu, trạng thái lỗi/rỗng và keyboard | Không lộ secret; hiểu đúng trạng thái, dùng được thao tác |
| I15 | Rebuild có quyền, trùng request_id, thiếu history hoặc vượt horizon | Hữu hạn/idempotent/audit; giữ processed, không sửa raw/closed |

SC-001 ↔ I01–03; SC-002 ↔ I03–04; SC-003 ↔ I05/I10;
SC-004–005 ↔ I08–10; SC-006 ↔ I11–13; SC-007 ↔ I10/I15;
SC-008 ↔ I02/I06. FR-022/023 còn được kiểm tra I14 và review phạm vi.
Các ca là tiêu chí cho bước triển khai, chưa chạy trên ứng dụng. Không phát sinh migration,
endpoint, frontend hoặc kết nối Jira/GitHub trong lần cập nhật tài liệu.

Thứ tự plan: chốt schema/limits và fixture → ingest/normalizer → worker/health → API/quyền
→ frontend polling → fault/load tests. Chốt retention production, HA, danh tính production,
notification replay và tối ưu phân vùng trong nhiệm vụ riêng khi có yêu cầu.
