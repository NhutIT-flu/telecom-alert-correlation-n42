# Thiết kế module điều phối, rule và gom nhóm

Ngày: 2026-11-19. Cập nhật: tách thuật toán/cấu hình/chính sách LinkFlap sang feature 004; giữ cơ chế chung ở đây. Trạng thái: thiết kế để review, chưa triển khai. [Yêu cầu nghiệp vụ](spec.md), [dữ liệu nền](../001-alert-data-model/data-model.md), [vòng đời cảnh báo](../002-alert-lifecycle/lifecycle-design.md).

## 1. Phương án và phạm vi

| Phương án | Đánh đổi |
|---|---|
| Truy vấn kho sự kiện để xét từng rule | Ít runtime state hơn nhưng tăng chi phí truy vấn khi nhiều log/rule; hữu ích cho tra cứu và kiểm chứng. |
| Worker dùng bộ nhớ và checkpoint PostgreSQL | Chọn cho bản đầu: xử lý nhanh trong RAM, giữ dữ liệu để khôi phục; thêm chi phí ghi checkpoint. |
| Broker và nhiều worker phân tán | Cần khi đo thấy nút thắt/năng lực dự phòng; thêm vận hành, phân vùng và kiểm soát thứ tự. Chưa chọn. |

Một Dispatcher logic, một worker tương quan, một bộ lập lịch và một CleanupManager chung thực thi ban đầu. Dispatcher, Registry và các handler là module trong cùng worker, không phải mỗi thành phần một service. Worker tách khỏi FastAPI; tăng số tiến trình phục vụ HTTP không tự tạo thêm bộ tương quan sở hữu cùng state. Không thêm Redis/Kafka hoặc tiến trình/timer riêng cho từng interface.

## 2. Luồng và trách nhiệm

```mermaid
flowchart TD
    E[Events chuẩn hóa đã lưu] --> D[Dispatcher chung]
    R[Registry phiên bản và đăng ký] --> D
    D --> O[Đệm và thứ tự nguồn theo nhóm]
    O --> H1[Handler rule A]
    O --> H2[Handler rule B]
    T[Lập lịch chung và mốc chốt] --> O
    T --> H1
    T --> H2
    H1 <--> S[Cache state theo khóa nhóm]
    H2 <--> S
    H1 --> L[Lifecycle dùng chung]
    H2 --> L
    L --> C[Commit checkpoint, bằng chứng, cảnh báo, lịch sử, tiến độ]
    C --> P[(PostgreSQL)]
    C --> N[Thông báo sau commit]
```

| Thành phần | Trách nhiệm |
|---|---|
| Registry | Nạp/kiểm tra cấu hình, ghép handler, lập chỉ mục sự kiện và giữ các revision cũ còn cần. |
| Dispatcher | Tra event_type, lọc phạm vi/field và tạo khóa; không tự đếm cửa sổ. |
| Handler | Logic riêng, nhận config bất biến + event + state, trả state mới/kết luận/bằng chứng. Không trực tiếp ghi DB hoặc ACK/CLOSE. |
| State cache | State theo nhóm và dữ liệu dẫn xuất theo schema handler. Không sửa cache đã commit trước giao dịch thành công. |
| CleanupManager | Chạy chung, gọi prune_state/can_evict_state và kiểm tra checkpoint, idle, pending, alert trước thu hồi; không tự kết thúc cảnh báo. |
| Lifecycle | Áp dụng create/append/recover/reactivate theo feature 002, kiểm tra trạng thái hiện tại và tranh chấp với thao tác người. |
| Persistence | Giao dịch, snapshot rule, checkpoint, nguồn pending bền vững và khôi phục. |

Mọi kết luận đưa tới Lifecycle đều là đề nghị: không được dùng alert_id trong cache làm bằng chứng rằng alert vẫn chưa đóng. Lifecycle kiểm tra bản hiện hành khi ghi, không ghi đè ACK/CLOSE từ cache cũ.

## 3. Cấu hình, logic và nơi lưu

- Một handler Python cho một loại thuật toán; mỗi cấu hình/revision có một evaluator được tạo khi nạp. Không tạo evaluator riêng cho mỗi interface.
- Handler giữ cấu hình bất biến, metadata khả năng, schema tham số và phiên bản logic. Không giữ một last_state/window chung trên object handler.
- File cấu hình có phiên bản là nguồn biên soạn bản đầu. Khi công bố, kiểm tra toàn bộ rồi lưu snapshot bất biến trong bảng rules chung để truy vết/khôi phục. Không chỉnh đồng thời cùng định nghĩa qua file và DB/UI.
- Có thể chọn DB làm nguồn biên soạn sau này, nhưng đó là thay đổi quản trị có migration rõ ràng; không vận hành hai nguồn chuẩn đồng thời.
- Giữ field `rules.definition` của thiết kế 001. Thông số riêng nằm tại `definition.parameters`, không thêm một cột parameters khác chứa cùng dữ liệu. Không tạo bảng link_flap_rules, bgp_rules riêng.
- Bổ sung `handler_key`, `handler_revision` dạng TEXT vào snapshot rules. Thay logic hoặc nội dung cấu hình phải tạo rules.version mới và lưu đúng handler_revision; không thay code dưới cùng định danh revision đã công bố.
- Cấu trúc/kiểu tham số được kiểm tra bằng schema do handler cung cấp; thiếu field, sai kiểu/range, field lạ hoặc subscription không tương thích phải bị từ chối. Không chạy code/SQL tùy ý từ cấu hình.
- Nạp và kiểm tra khi khởi động/công bố có kiểm soát, không đọc/parse file hay JSONB cấu hình cho từng log. Bản đầu chưa hot reload hoặc có UI quản trị rule.

Mẫu cấu hình và schema tham số của LinkFlap đã chuyển sang [004 mục 2](../004-link-flap-rule/link-flap-design.md). Điều kiện đếm/kết thúc không là mặc định của engine; handler khai báo schema và outcome của mình. Bản nháp có thể hoàn thiện trước công bố, snapshot đã công bố chỉ thay bằng revision mới.

## 4. Hợp đồng dữ liệu và điều phối

Đầu vào là projection đã kiểm tra của event được lưu: id, event_type, event_time/time_status, device_id, scope, interface_name/interface_state/interface_layer khi có. Projection đọc một lần từ field chuẩn hóa/attributes rồi truyền cho các handler, không yêu cầu mỗi rule tự parse lại raw hoặc JSONB.

- Registry lưu event_type → danh sách revision ứng viên. Mỗi revision là hợp của đăng ký phát sinh/phục hồi và được loại trùng trước gọi.
- Phạm vi có thể kiểm tra bằng filter được hỗ trợ; bộ điều phối không quét regex raw cho mọi rule. Khả năng đọc syslog từng hãng thuộc tầng chuẩn hóa.
- Rule cùng hiện tượng có thể dùng cho router/switch/firewall nếu parser đã chứng minh ánh xạ tương đương; tên hãng không tự bảo đảm tương thích.
- Cần giữ revision đang bật và revision cũ có alert chưa đóng. Revision cũ chỉ theo dõi đúng nhóm đang tồn tại; không tạo cảnh báo đầu tiên cho nhóm mới khi bị tắt.
- Thiếu field cho một rule: ghi lý do bỏ qua có thể tổng hợp đếm, không cần log cảnh báo vận hành cho từng sự kiện thiếu giống nhau; event vẫn giữ, rule khác còn đủ field vẫn xét.
- Không có rule phù hợp là kết quả đã xét không khớp, không phải lỗi hệ thống. Lỗi code/DB không được coi như trường hợp này.
- Tập registry cố định trong một batch. Khi có revision mới, bản chưa đánh giá dùng registry công bố ở đầu batch; bản đã hoàn tất không tự đánh giá lại bằng revision mới. Thử lại sau lỗi giữ registry cũ trong cùng lượt vận hành; đổi revision để khắc phục cần thao tác phục hồi có kiểm soát, không lặng lẽ đổi giữa batch.

## 5. Khóa nhóm, instance và quyền sở hữu

Khóa logic:

```text
(rule_key, config_version, handler_revision, correlation_scope, group_values)
```

`rules.id` đại diện cho bộ định danh revision khi lưu checkpoint, còn group_values chỉ chứa các giá trị group_by. Giới hạn kiểu/độ dài key được kiểm tra, không dùng raw message làm khóa. Ví dụ nhóm interface cần device_id + interface_name đã chuẩn hóa; không tự đổi alias hoặc thay device_id bằng sender_ip/hostname có thể trùng. Khóa riêng từng handler nằm trong tài liệu rule.

Một handler phục vụ nhiều group state: A/Gi0/0, A/Gi0/1 và B/Gi0/0 độc lập. Tạo hoặc nạp state khi có event liên quan; không cấp trước window cho toàn bộ inventory. Cùng nhóm chỉ có một luồng cập nhật; bản đầu phải có khóa sở hữu worker để chạy nhầm hai process không xử lý cùng dữ liệu. Cách dùng khóa/lease cụ thể chốt ở plan.

## 6. Các rule sử dụng engine

[Feature 004 — LinkFlap](../004-link-flap-rule/spec.md) và [thiết kế chi tiết](../004-link-flap-rule/link-flap-design.md) là nguồn chuẩn cho thuật toán đếm, cấu hình, payload state, phạm vi tính bù, outcome và chính sách dọn của rule đó.

Engine không chứa ngưỡng/cửa sổ hay điều kiện kết thúc mặc định áp cho mọi handler. Một rule mới tuân hợp đồng mục 11, công bố schema/config hợp lệ và dùng cơ chế chung ở mục 7, 8, 12.

## 7. Checkpoint và khôi phục

Bổ sung **một bảng chung `rule_group_states`**, không bảng riêng theo rule/interface. Sáu bảng dữ liệu/lịch sử từ 001/002 vẫn giữ; bảng thứ bảy này là checkpoint thuật toán.

| Cột | Kiểu đề xuất | Vai trò |
|---|---|---|
| `rule_id` | UUID, FK rules.id, RESTRICT | Revision cấu hình/logic đã công bố. |
| `correlation_scope` | TEXT, NOT NULL | live hoặc replay cụ thể. |
| `group_values` | JSONB object, NOT NULL | Giá trị đúng group_by; cùng hai cột trên tạo PK. |
| `state_schema_version` | INTEGER >0 | Phiên bản cấu trúc state; không tự đọc payload cũ như schema mới. |
| `state_payload` | JSONB object, NOT NULL | State riêng theo schema handler, đủ ngữ cảnh/đường khôi phục, ranh giới và kết quả cần tiếp tục; không chỉ dữ liệu dẫn xuất. |
| `last_event_id` | BIGINT, NOT NULL, FK events.id, RESTRICT | Event cuối được áp dụng; chỉ tham chiếu, không phải MAX-id cursor. |
| `last_event_time` | TIMESTAMPTZ, NULL được | Mốc nguồn có căn cứ của nhóm; nhóm nhiều đối tượng vẫn cần mốc từng đối tượng trong payload. |
| `checkpoint_version` | BIGINT >0 | Phiên bản engine tăng sau mỗi thay đổi state có hiệu lực, khác state_schema_version và alerts.state_version. |
| `next_check_at` | TIMESTAMPTZ, NULL được | Deadline theo thời gian nguồn để phục hồi lịch sau restart; không cộng sẵn reorder delay. |
| `updated_at` | TIMESTAMPTZ, NOT NULL | Lần lưu checkpoint thành công gần nhất. |

Schema/giới hạn payload do handler kiểm tra. Cột JSONB này phục vụ lưu/khôi phục, không được truy xuất liên tục để tính rule trong DB; worker tính trên state RAM rồi ghi snapshot nhóm thay đổi. JSONB không miễn chi phí ghi: serialization, WAL, index và cập nhật tuple phải đo.

Các event_id nằm trong payload cũng là bằng chứng cần cho lần đạt ngưỡng sau. FK last_event_id không tự bảo vệ mọi event ref trong JSONB: trước khi có dọn dữ liệu tự động phải kiểm tra các tham chiếu checkpoint hoặc thiết kế lưu refs chuẩn hóa. Bản đầu giữ nguyên chính sách lab không tự xóa; không xóa raw còn được checkpoint/cảnh báo dùng.

Không lưu workflow_status/ACK/CLOSE vào payload như nguồn chuẩn. Tham chiếu alert trong cache nếu có chỉ là gợi ý; Lifecycle kiểm tra trạng thái DB để tránh sửa alert đã đóng. Giữ độc lập thuật toán và xác nhận người dùng.

### Giao dịch batch

1. Chọn batch từ events đủ parse đang pending, đăng ký/đệm theo group và chính sách mục 12. Event chưa đủ chốt vẫn pending, không đánh dấu processed chỉ vì đã vào RAM. Khóa quyền xử lý; không dùng MAX(id) làm tiến độ vì thứ tự cấp id không bảo đảm thứ tự commit.
2. Đánh giá tuần tự trên bản state tạm (copy-on-write) của batch. Mọi event trong batch thấy kết quả tạm trước nó, nhưng cache đã commit chưa bị sửa. Các rule đủ field được gọi đủ; skip có lý do không phải exception.
3. Một giao dịch ghi checkpoint cuối của mỗi nhóm đã thay đổi, các alert/evidence/history cần thiết và trạng thái hoàn tất của **đúng các event id** trong batch. Các lần chuyển lịch sử trung gian vẫn ghi đủ; không coalescing mất create/recovery/reactivate.
4. Chỉ sau commit mới thay cache bằng state mới và gửi thông báo. Crash trước commit: pending + checkpoint cũ để chạy lại; crash sau commit trước cache swap: reload DB, không chạy lại event đã hoàn tất.
5. Ghi cùng một group nhiều lần trong batch có thể chỉ checkpoint state cuối. Batch giảm round-trip/commit, không giảm số row update nếu mọi event thuộc nhóm khác nhau. Batch size/độ chờ phải chốt bằng mục tiêu độ trễ, không chờ hàng giây chỉ để gom nhiều log.

Bộ thực thi trộn event và deadline theo thời gian nguồn, không dồn tất cả timer về cuối batch: deadline d<t chạy trước event t, tại d==t xử lý mọi event t trước timer. Điều này áp dụng cả khi xử lý backlog sau gián đoạn.

Timer, tính bù và prune có thay đổi cần lưu cũng đi qua giao dịch này; timer không tạo raw/event giả. Ghi lại checkpoint_version/next_check_at để lần hẹn lặp không nhân đôi kết quả. State mới phải được serialize–restore kiểm chứng. Không lấy checkpoint rồi append lại toàn bộ log đã có vào nó: khi rebuild phải khởi từ baseline của đoạn và tập ID xác định; không nhận nhầm pending khác thành đã áp dụng.

Khởi động lại nạp snapshot rule và handler revision cần thiết, checkpoint và cảnh báo chưa đóng trước nhận việc. Nhóm lạnh có thể nạp khi truy cập, nhưng thiếu revision/schema hoặc liên kết checkpoint hỏng phải báo lỗi, không mặc định cửa sổ rỗng. Không chỉ replay vài phút để đoán lại trạng thái dài hạn; raw dùng cho điều tra/rebuild có kiểm soát, không phát sinh lại side effect của event đã hoàn tất.

### Lỗi, retry và giới hạn bản đầu

- Lỗi input đã kiểm tra (thiếu field/không hỗ trợ) có kết quả skip. Lỗi handler bất ngờ/DB khiến rollback toàn batch, giữ cache cũ, ghi thông tin lỗi và dừng tiến độ worker; thu thập vẫn lưu raw/normalized vào pending theo sức chứa.
- Không tiếp tục xử lý nhóm sau trong khi đã bỏ qua một event lỗi có thể làm sai cửa sổ; không đánh dấu processed chỉ vì các rule khác thành công. Đây là lựa chọn fail-stop để bảo toàn kết quả của bản đầu.
- Sau lỗi commit có kết quả không rõ, phải đọc lại tiến độ/checkpoint, không áp dụng lại mù quáng. Lỗi tạm có retry giới hạn; lỗi logic cần sửa có kiểm soát và không được tự sửa revision cũ đã công bố.
- Muốn rule lỗi không trì hoãn rule khác cần thêm durable work/receipt theo event–revision và serialization theo group. Đây là bước mở rộng có chi phí ghi và vận hành, chưa có trong giao dịch chung hiện tại.

## 8. CleanupManager chung và quản lý cache

### 8.1. Chính sách và phạm vi

Một CleanupManager trong engine gọi chính sách từng handler; không tạo bộ dọn riêng cho mỗi rule/interface và không bắt buộc kế thừa một class dọn nặng. Handler chỉ đề xuất prune và cho phép evict; engine kiểm tra checkpoint/quyền sở hữu/concurrency. Dọn RAM tách với retention DB, không xóa raw, lịch sử, checkpoint cần khôi phục hoặc đổi tín hiệu.

| Thông số | Giá trị hiện tại | Nguồn |
|---|---|---|
| Reorder delay | 3 giây | Đã chọn |
| cleanup_interval_seconds | 5 giây | Mặc định đề xuất |
| cache_idle_seconds | 60 giây | Mặc định đề xuất |

Timer điều kiện rule đánh thức theo deadline, không bị buộc chờ chu kỳ dọn 5 giây. Idle dùng thời gian truy cập phía engine/đồng hồ đơn điệu; hết hạn cửa sổ dùng watermark nguồn. Dữ liệu nào làm thay đổi thời hạn thuật toán do handler quyết định; truy cập có thể giữ cache nóng dù kết luận không đổi.

### 8.2. Hai mức dọn

- Prune: bỏ dữ liệu hết hạn khi handler xác nhận không còn cần cho tính tiếp/tính bù. Chưa đạt điều kiện phát sinh không đủ lý do xóa. Giữ ngữ cảnh hoặc đường nạp lại đã kiểm chứng.
- Evict: chỉ bỏ toàn bộ entry RAM nếu handler xác nhận không còn dữ liệu thuật toán cần giữ nóng, không pending/in-flight, không alert chưa đóng, đủ idle, checkpoint an toàn và generation không đổi. Recovered nhưng chưa closed vẫn là chưa đóng.
- Nhóm có alert có thể prune phần không còn cần, nhưng bản đầu chưa evict toàn bộ. Đánh giá kết thúc bằng on_time/Lifecycle trước, không dùng cửa sổ rỗng như một lệnh RECOVER.

### 8.3. Mỗi lượt dọn

1. Xét các group đang trong cache, chia lô nếu cần, không quét toàn inventory.
2. Lấy watermark an toàn, gọi prune_state và kiểm tra schema/baseline.
3. Xem điều kiện handler can_evict_state và các guard chung ở trên.
4. State chưa checkpoint đúng generation thì lưu thành công hoặc giữ lại; không thu hồi khi DB lỗi/commit chưa rõ.
5. Trước xóa entry, xác nhận còn cùng cache entry/generation và không xuất hiện việc mới; nếu đổi thì bỏ quyết định cũ.
6. Evict RAM, tăng metrics. Không cần UPDATE DB cho mọi lần quét; snapshot còn mốc cũ có thể được prune khi đọc, miễn đủ khôi phục.

### 8.4. Nạp lại sau thu hồi

Nạp checkpoint và ngữ cảnh liên quan theo schema/chính sách handler. Không append lại dữ liệu đã có trong checkpoint hoặc coi pending chưa chốt là đã áp dụng. Timeline riêng cho LinkFlap chuyển sang [004 mục 5.1](../004-link-flap-rule/link-flap-design.md).

### 8.5. Quá tải và chỉ số

Queue RAM là tín hiệu tăng tốc; events pending mới là nguồn bền vững. Queue/cache đầy không được âm thầm mất dữ liệu chưa checkpoint. Theo dõi groups/observations, prune/evict/reload, skip theo pending/alert/dirty, thời gian dọn, backlog và RSS. Xóa object không bảo đảm Python trả RSS cho OS ngay.

Khi có nhiều worker, mỗi worker chỉ dọn partition mình sở hữu. Thay đổi TTL an toàn không đổi điều kiện phát hiện; không dùng tự hết hạn cache làm thời gian đóng alert.

## 9. Chi phí và giới hạn ước lượng

CPU/tổng ghi tăng theo E×k (E là sự kiện, k là số rule ứng viên trung bình); thuật toán phức tạp có thêm chi phí riêng. RAM phụ thuộc số nhóm giữ nóng, payload state, đệm chưa chốt và lịch; không nhân thẳng RAM của một state với thời gian chạy.

Đo riêng parse/dispatch/evaluate, số group, serialization/checkpoint, evidence/history, batch/commit, backlog và API/thông báo. JSONB snapshot, WAL và index vẫn có chi phí dù đường tính chính chạy trong RAM. Một cảnh báo mỗi nhóm không đồng nghĩa chỉ ghi một dòng mỗi nhóm trong toàn thời gian sự cố.

[Mô hình 1.000 interface của LinkFlap và giới hạn microbenchmark cũ](../004-link-flap-rule/link-flap-design.md) nằm tại 004 mục 6. Không dùng phép mô phỏng bộ đếm để cam kết ngân sách toàn worker hoặc production.

## 10. Quan sát và nghiệm thu

Đo input/s, evaluated/s, candidates/event, group cache nóng/lạnh, số nạp/evict, kích thước state/checkpoint, RSS/CPU, số ghi event/evidence/state, batch duration, backlog count/oldest age, lỗi từng revision và độ trễ p50/p95/p99.

Đo riêng received→đủ chốt và đủ chốt→hiển thị; SC-006 chỉ đề xuất p95 2 giây/p99 5 giây cho đoạn sau. Tổng độ trễ có khoảng chờ 3 giây/tồn đọng và chưa là SLA. Dùng cả tải đều và tải dồn theo mô hình của rule cần đánh giá, nhiều mức số rule ứng viên và toàn bộ checkpoint/evidence, không suy từ microbenchmark.

| Mã | Tình huống | Expected result |
|---|---|---|
| C01 | Hai config cùng handler khác ngưỡng | Tách identity, state và kết quả. |
| C02 | Sai kiểu/range/field/subscribe | Từ chối công bố, không nạp một phần. |
| C03 | Đổi nội dung giữ version | Từ chối, yêu cầu revision mới. |
| C04 | Một event khớp hai rule và hai selector của cùng rule | Hai revision được xét, mỗi revision một lần. |
| C05 | Log recovery không thỏa trigger | Vẫn đến revision cần theo dõi. |
| C06 | Rule cũ tắt còn alert | Tiếp tục nhóm cũ, không mở nhóm mới. |
| C07 | Thiếu field một rule | Skip có lý do, rule khác đủ field vẫn xét, raw còn. |
| C08 | A/Gi0/0, A/Gi0/1, B/Gi0/0 xen kẽ | Không trộn nhóm. |
| C09 | Cache eviction rồi event mới | Khôi phục baseline/window/chu kỳ từ checkpoint. |
| C10 | Crash trước commit hoặc sau commit trước swap | Rollback hoặc khôi phục bản đã commit, không đếm đôi. |
| C11 | Lỗi một handler trong batch | Rollback batch, dừng tiến độ/báo lỗi, đầu vào vẫn lưu. |
| C12 | Event id nhỏ commit muộn | Không bỏ sót do MAX-id cursor. |
| C13 | Group recovered, ACK/CLOSE và tái phát | Theo feature 002; không ghi đè thông tin người. |
| C14 | Log trễ/cùng timestamp/unknown time | Tính bù khi đủ căn cứ; không đoán thứ tự hay sửa alert đóng, raw còn. |
| C15 | Search-only/replay khác scope | Không tác động live hoặc scope khác. |
| C16 | Thiếu recovery hoặc recovery không tương thích | Draft tắt được giữ; bật bị từ chối. Tham số riêng phải khớp handler. |
| C17 | Hàng chờ/cache đầy | Không âm thầm mất dữ liệu đã lưu; thấy backlog/health. |
| C18 | Hai worker cùng chạy ngoài dự kiến | Chỉ một chủ sở hữu tiến độ, không nhân đôi state. |
| C19 | Tải dồn và tải đều theo kịch bản đã chọn | Đối chiếu đủ event, đo p95/p99 gồm DB/UI. |
| C20 | Handler/schema revision mất khi restore | Báo lỗi, không mặc định state rỗng. |
| C21 | Lệch thứ tự trong 3 giây | Chốt theo event_time, không theo received_at. |
| C22 | Interface không gửi log tiếp | Watermark/lịch vẫn xử lý log cuối và deadline khi dữ liệu an toàn. |
| C23 | Transition mới đúng deadline | Áp event trước timer, dời hạn, không kết thúc thoáng qua. |
| C24 | Pipeline/time không an toàn | Không kết luận quiet recovery theo khoảng không quan sát. |
| C25 | Correction của alert closed | Giữ alert/history; đánh dấu event/diagnostic, không reopen/xóa. |
| C26 | Checkpoint lỗi/generation đổi lúc dọn | Giữ entry, không mất cập nhật hoặc pending. |
| C27 | Cùng CleanupManager phục vụ nhiều handler | Prune/evict theo hợp đồng riêng, guard cuối thuộc engine. |
| C28 | Handler sửa input/cache hoặc ghi IO | Vi phạm hợp đồng bị test phát hiện; rollback không lộ state dở. |
| C29 | Timer sau restart/lặp cùng state | Một quyết định có hiệu lực, ghi timer/effective_at không tạo raw giả. |
| C30 | State serialize–restore và eviction | Đánh giá tiếp tương đương, không cộng lại observations hai lần. |
| C31 | Evidence/outcome đổi nhưng trạng thái chưa đổi | Có correction audit/version có ý nghĩa, không tạo lịch sử cho no-op. |
| C32 | Resume với deadline 80 và event mới tại 90 | Xét timer 80 trước event 90; không bỏ mất quiet period chỉ vì xử lý nhiều việc cùng batch. |

Các case C01–C32 kiểm chứng cơ chế chung. Ca thuật toán LinkFlap chuyển sang LF01–LF20 tại [004 mục 7](../004-link-flap-rule/link-flap-design.md). Các case là yêu cầu cho test triển khai sau, chưa được chạy trên ứng dụng. Đặc tả, ví dụ JSON và tính nhất quán tài liệu có thể kiểm tra ngay; không tạo worker hoặc migration ở bước specify.

## 11. Hợp đồng Handler

### 11.1. Metadata và cấu hình chỉ đọc

| Thành phần | Bắt buộc / ý nghĩa |
|---|---|
| handler_key, handler_revision | Loại thuật toán và revision bất biến |
| supported_event_types | Các loại sự kiện chuẩn hóa được phép đăng ký, đủ cả trigger/recovery |
| required_fields | Theo event_type; gồm yêu cầu event_time có căn cứ nếu thuật toán cần |
| required_group_fields | Identity tối thiểu do loại handler quy định |
| parameter_schema | Kiểu/range/field và validator liên trường; engine gọi khi nạp |
| state_schema, state_schema_version | Payload và serialize–restore đúng phiên bản |
| supported_outcomes | Outcome cố định được code hỗ trợ, không tùy ý thêm bằng cấu hình |

Metadata do code cung cấp, không cho cấu hình chọn đường import hoặc chạy mã tùy ý. Một evaluator gắn config/revision bất biến, không giữ last_state/window riêng của interface trong object dùng chung.

### 11.2. Kiểu đầu vào

NormalizedEvent gồm event_id, event_type, event_time, received_at, time_status, device_id, correlation_scope và fields projection có kiểu. Raw vẫn ở events, handler không parse lại hoặc tự đọc DB.

RuleState gồm envelope engine sở hữu (rule_ref, group_key, schema/checkpoint version) và payload riêng handler. Handler chỉ đề xuất payload mới; không sửa identity/version/nhóm khác. Snapshot phải thực sự chỉ đọc hoặc copy-on-write; chỉ đóng băng object ngoài mà dict/list bên trong còn sửa được là chưa đủ.

EvaluationContext gồm rule_ref/group_key, parameters và recovery policy đã kiểm tra, watermark nguồn, now hệ thống, mode=live/rebuild. Mốc đếm dùng event_time; timer nguồn dùng watermark; idle TTL thuộc engine dùng clock đơn điệu. Không cung cấp DB session, socket hay callback gửi thông báo cho handler.

State chuẩn lưu phải serialize được (object/list/giá trị JSON có schema, timestamp UTC không mất chính xác, event ID đúng kiểu). Cấu trúc tối ưu tạm trong handler không được trở thành tham chiếu không thể khôi phục. Không thêm hàm IO riêng ở từng rule.

### 11.3. Năm thao tác

~~~python
initial_state(context) -> RuleState
evaluate(event, state, context) -> RuleResult
on_time(state, context) -> RuleResult
prune_state(state, context) -> PruneResult
can_evict_state(state, context) -> EvictionDecision
~~~

| Thao tác | Precondition và trách nhiệm | Cấm |
|---|---|---|
| initial_state | Chỉ khi thực sự không có checkpoint; tạo state ban đầu theo schema handler | Nuốt lỗi restore và khởi tạo rỗng |
| evaluate | Event hợp lệ đã chuẩn bị thứ tự hoặc replay; cập nhật state và mọi điều kiện liên quan | Bỏ toàn bộ lượt vì kết luận chưa đổi, sửa cache đã commit |
| on_time | Watermark an toàn đến deadline; đánh giá kể cả không có log, kết quả lặp an toàn | Tự cộng thêm reorder delay, tự tạo timer/thread, giả làm syslog mới |
| prune_state | Trả state còn đủ semantics tương lai/tính bù hoặc đường khôi phục | Tạo ACTIVATE/RECOVER, xóa raw/alert/checkpoint |
| can_evict_state | Đề xuất allowed + reason từ nhu cầu thuật toán | Tự xóa cache, bỏ qua guard engine |

Default an toàn: on_time=NONE, prune=giữ nguyên, can_evict=false nếu handler chưa định nghĩa chính sách. evaluate và schema không có mặc định giả thành công. Không bắt buộc kế thừa CleanupManager; cùng hợp đồng đủ để manager gọi.

### 11.4. Kết quả

| RuleResult field | Ngữ nghĩa |
|---|---|
| new_state | Payload/snapshot sau tính toán; NONE vẫn có thể thay state |
| decision | NONE / ACTIVATE / RECOVER |
| evidence_ids | ID syslog hỗ trợ kết luận; phải đúng group/scope/lớp |
| reason_code | Lý do có cấu trúc, không raw/stack trace tùy ý |
| effective_at | Khi điều kiện đạt theo dữ liệu; timer là deadline tính toán, không phải timestamp một log mới |
| outcome | NULL nếu không cần, hoặc một outcome đã khai báo trong metadata |
| next_check_at | Deadline theo thời gian nguồn hoặc NULL; engine giữ lịch |

ACTIVATE là đề nghị: Lifecycle tạo, bổ sung hoặc tái kích hoạt theo bản DB hiện hành. RECOVER không ACK/CLOSE. Engine gắn decision_source=syslog/timer/correction từ cách đánh giá, không tin nguồn tự khai từ client.

PruneResult gồm new_state, removed_items, reason_code; không có decision đổi alert. EvictionDecision gồm allowed, reason_code; engine vẫn kiểm tra dirty/checkpoint, pending/in-flight, idle, alert và generation.

effective_at là mốc đạt điều kiện, recorded_at là lúc hệ thống thực ghi. Evidence timer phải trỏ đến quan sát thật và khoảng/mốc chốt trong audit, không tạo event giả. Ngữ nghĩa outcome cụ thể thuộc handler; không đồng nhất mọi RECOVER với thiết bị đã UP.

### 11.5. Lỗi và kiểm chứng

Thiếu field/không hỗ trợ là skip có lý do do engine phân biệt; schema/result sai hoặc exception handler là lỗi thực thi, không phải NONE. Rollback theo mục 7.

Mỗi handler phải có test metadata/config, nhóm độc lập, input không bị sửa, đầu vào không đổi kết luận, biên thuật toán, timer không log mới/timer lặp nếu hỗ trợ, các outcome khai báo, serialization, prune/restore, eviction, rebuild và rollback. Engine kiểm tra shape/invariant trước ghi, không thể tự chứng minh thuật toán Python đúng chỉ bằng schema.

## 12. Thời gian nguồn, đệm và tính bù chung

### 12.1. Đệm và mốc chốt

event_time là căn cứ thuật toán; received_at dùng đo tiếp nhận/độ trễ. Sắp trong cùng nhóm theo thời gian nguồn; timestamp bằng nhau chỉ dùng sequence nguồn nếu thực sự có căn cứ, không dùng event_id/thứ tự nhận để đoán.

Engine giữ log chưa chốt khoảng 3 giây, là lựa chọn hiện tại dùng chung. Khi UTC/ngữ cảnh nguồn đủ tin cậy và không backlog ảnh hưởng, mốc tham chiếu là now_UTC-3 giây. Xử lý các event đủ điều kiện trước timer tới mốc đó; mốc tiến cả lúc im lặng khi an toàn. Watermark không bảo đảm sẽ không còn log cũ đến nữa.

Thời gian unknown, quá tương lai hoặc mâu thuẫn phải có diagnostic/guard; không giữ vô hạn trong heap rồi coi là dữ liệu trễ bình thường. Pipeline/time không an toàn thì không dùng khoảng im lặng kết luận recovery. Reorder delay áp một lần, không cộng cả trong handler và scheduler.

### 12.2. Phạm vi theo handler

Handler quy định horizon, dữ liệu ảnh hưởng, baseline/ngữ cảnh cần đọc và cách dựng lại; engine không dùng một cửa sổ cố định cho mọi rule. [004 mục 4](../004-link-flap-rule/link-flap-design.md) quy định cụ thể vùng sống và lookback LinkFlap.

Ngoài phạm vi ảnh hưởng: giữ raw và late_out_of_horizon. Thiếu ngữ cảnh: correction_incomplete; thứ tự mâu thuẫn: ordering_ambiguous. Không suy dữ liệu rỗng hoặc kết luận đã khôi phục chính xác toàn lịch sử. Retention phải bảo vệ mọi ref dùng cho checkpoint/bằng chứng như mục 7.

### 12.3. Dựng lại và hòa giải kết quả

1. Chốt snapshot/vùng ảnh hưởng, đúng revision/scope/group; chỉ dùng dữ liệu đã áp dụng hoặc batch đang xét, không tự coi pending khác đã xử lý.
2. Nạp đủ ngữ cảnh, chèn theo thứ tự nguồn và dựng lại trên state tạm từ đầu đoạn hợp lệ. Không cộng log DB vào buffer đã chứa cùng dữ liệu.
3. Xét mọi điểm/kết luận bị ảnh hưởng theo handler, không chỉ timestamp log vừa đến.
4. mode=rebuild trộn event/deadline theo nguồn: d<t thì timer d trước event t; d==t thì mọi event t trước timer. Handler không IO; không ghi tác động trung gian máy móc.
5. So với kết quả đã công bố; có thể phát hiện muộn hoặc hiệu chỉnh evidence/outcome/nhận định của alert chưa đóng theo 002. effective_at có thể cũ hơn created_at, không ghi lùi thời gian hệ thống.
6. Ghi correction source, before/after, reason, bằng chứng và phiên bản cùng giao dịch state/progress. Facts không đổi thì không tạo audit/version có ý nghĩa.
7. Nếu recovery cũ bị vô hiệu, quay về ranh giới hợp lệ trước đó với audit. Nếu activation cũ chưa chứng minh được và chưa có kết thúc hợp lệ: evidence_review_required, không tự xóa/hủy/đóng.
8. Alert closed bất biến; ghi late_conflict_closed ở diagnostic sự kiện, không reopen. Không cam kết tái dựng mọi incident lịch sử.

Chi phí tính bù phụ thuộc số quan sát/ngữ cảnh và log trễ; phải đo cùng đường ghi/checkpoint. Các test engine ở mục 10 kiểm tra cơ chế; test thuật toán riêng nằm trong từng feature rule.
