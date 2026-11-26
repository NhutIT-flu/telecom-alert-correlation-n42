# Feature Specification: Dữ liệu sự kiện và cảnh báo mạng đa hãng

**Feature Branch**: Không tạo nhánh trong lần đặc tả này.

**Created**: 2026-11-19

**Status**: Draft — chờ người dùng phê duyệt.

**Cập nhật 2026-11-19**: Phần vòng đời cảnh báo được làm rõ bởi [002-alert-lifecycle](../002-alert-lifecycle/spec.md): giám sát syslog, hai chiều tín hiệu/xác nhận, không có hoạt động khắc phục thiết bị.

**Rule chuyên biệt**: [Feature 004 — LinkFlap](../004-link-flap-rule/spec.md) sở hữu điều kiện đếm/kết thúc và dữ liệu thuật toán; dùng lại các thực thể chung, không thêm bảng riêng.

**Cập nhật module**: [003-rule-dispatch-correlation](../003-rule-dispatch-correlation/spec.md) làm rõ cấu hình/logic, đăng ký nhiều rule, state theo đối tượng và checkpoint. Bảng rules giữ snapshot công bố; file cấu hình là nguồn biên soạn bản đầu, không phải hai nguồn chỉnh sửa song song. Có thêm thực thể trạng thái nhóm bền vững, không có bảng riêng cho từng loại rule.

**Updated**: 2026-11-20 — thống nhất dữ liệu interface, trạng thái lỗi/thử lại và bảo toàn state sau eviction; tích hợp feature 005.

**Cập nhật 2026-11-26** ghi nhận chính sách [mức độ nghiêm trọng của cảnh báo](#quy-ước-gán-mức-độ-nghiêm-trọng) trong prototype LinkFlap.

**Input**: User description: "Thiết kế chi tiết từng bảng cho hệ thống thu thập và phân tích syslog từ router, switch, firewall; giải thích vai trò từng thành phần. Lưu cả syslog thô và dữ liệu chuẩn hóa, hỗ trợ Cisco, Juniper và mở rộng nhiều hãng."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Giữ sự kiện và bằng chứng gốc (Priority: P1)

Người giám sát muốn xem lại mọi sự kiện đã được lưu bền vững, gồm nội dung gốc và thông tin đã nhận diện, kể cả khi log thiếu trường hoặc chưa hỗ trợ hãng.

**Why this priority**: Mất bản gốc hoặc bỏ log lỗi sẽ làm mất bằng chứng và không thể chuẩn hóa lại.

**Independent Test**: Đưa vào bộ mẫu có nhãn gồm log đầy đủ, thiếu trường, chưa nhận diện và không giải mã được; đối chiếu đầu vào với dữ liệu truy xuất.

**Acceptance Scenarios**:

1. **Given** một log hợp lệ, **When** tiếp nhận rồi chuẩn hóa, **Then** một sự kiện giữ cả bản gốc và dữ liệu đã tách, có định danh ổn định.
2. **Given** log thiếu thời gian hoặc hostname, **When** chuẩn hóa, **Then** bản gốc vẫn còn, trường chưa biết để trống và trạng thái thể hiện xử lý một phần.
3. **Given** log hãng chưa hỗ trợ hoặc không giải mã được, **When** đã lưu đầu vào thành công, **Then** truy xuất được đầu vào gốc cùng lý do lỗi.
4. **Given** sự kiện không thỏa luật nào, **When** đánh giá xong, **Then** sự kiện vẫn tìm được và được ghi nhận đã xét luật.

### User Story 2 - Tìm kiếm thống nhất trên nhiều hãng (Priority: P1)

Người giám sát muốn tìm theo thiết bị, hãng, thời gian, mức độ và loại sự kiện mà không cần biết cấu trúc log từng hãng.

**Why this priority**: Đây là cách sử dụng chính của kho log và cơ sở cho luật áp dụng trên các hiện tượng tương đương.

**Independent Test**: Dùng bộ Cisco và Juniper có kết quả mong đợi đóng băng; thực hiện truy vấn đơn và kết hợp, đối chiếu định danh sự kiện.

**Acceptance Scenarios**:

1. **Given** hai log đổi trạng thái interface từ hai hãng, **When** chuẩn hóa, **Then** có cùng loại sự kiện nghiệp vụ nhưng vẫn giữ tên interface và mã thông điệp của hãng.
2. **Given** nhiều hãng và thiết bị, **When** lọc kết hợp thời gian, thiết bị và mức độ, **Then** chỉ trả các sự kiện thỏa đồng thời điều kiện.
3. **Given** log chưa xác định thiết bị, **When** tìm nhóm chưa nhận diện, **Then** vẫn xem được bản gốc và nguồn nhận, không gán thiết bị theo người tải tệp lên.
4. **Given** nhiều sự kiện cùng timestamp, **When** chuyển trang trên tập dữ liệu cố định, **Then** thứ tự ổn định, không lặp hoặc bỏ sót.

### User Story 3 - Truy vết cảnh báo đến luật và sự kiện (Priority: P1)

Người giám sát muốn biết phiên bản luật nào tạo cảnh báo và chính xác những sự kiện nào đã đóng góp.

**Why this priority**: Cảnh báo phải giải thích được; chỉnh luật sau này không làm sai lịch sử.

**Independent Test**: Dùng một tập sự kiện thỏa hai luật và hai nhóm của cùng luật; kiểm tra cảnh báo, phiên bản và tập bằng chứng.

**Acceptance Scenarios**:

1. **Given** một nhóm sự kiện thỏa luật, **When** tạo cảnh báo, **Then** có định danh sự cố duy nhất, mức độ riêng, đúng phiên bản luật và đầy đủ sự kiện đóng góp.
2. **Given** một sự kiện thỏa hai luật, **When** cả hai luật tạo cảnh báo, **Then** sự kiện liên kết được cả hai mà không sao chép sự kiện.
3. **Given** cùng sự kiện được xét lại, **When** ghi kết quả cho cùng cảnh báo, **Then** không nhân đôi liên kết bằng chứng.
4. **Given** luật được thay đổi, **When** xem cảnh báo cũ, **Then** vẫn thấy nội dung phiên bản đã tạo cảnh báo.
5. **Given** cảnh báo chưa đóng có cùng luật, nhóm và ngữ cảnh đánh giá, **When** có bằng chứng mới đáp ứng luật, **Then** bổ sung hoặc đổi tín hiệu trên cùng cảnh báo; chỉ sau khi người giám sát xác nhận đóng thì lần phát sinh mới đủ điều kiện có định danh mới, theo feature 002.

### User Story 4 - Tiếp tục sau gián đoạn và giữ lịch sử (Priority: P2)

Người vận hành muốn tiếp tục xử lý sau gián đoạn và không mất lịch sử khi đổi thông tin thiết bị hoặc ngừng dùng luật.

**Why this priority**: Lỗi ở bước xử lý sau không được làm mất đầu vào đã lưu.

**Independent Test**: Dừng ở các mốc sau lưu raw, trước ghi chuẩn hóa và giữa ghi cảnh báo; chạy lại rồi đối chiếu. Thử đổi danh mục và ngừng dùng luật.

**Acceptance Scenarios**:

1. **Given** đầu vào đã lưu nhưng chưa chuẩn hóa, **When** hoạt động lại, **Then** còn dữ liệu chờ để xử lý tiếp.
2. **Given** thao tác ghi cảnh báo không hoàn thành, **When** xử lý lại, **Then** không có cảnh báo ghi dở hoặc sự kiện hoàn tất trước khi lưu đủ bằng chứng.
3. **Given** danh mục thiết bị đổi hostname/hãng/hệ điều hành, **When** xem sự kiện cũ, **Then** vẫn thấy thông tin đã ghi nhận lúc chuẩn hóa.
4. **Given** thiết bị, luật hoặc sự kiện đang được dùng làm bằng chứng, **When** yêu cầu xóa, **Then** không xóa ngầm lịch sử liên quan.
5. **Given** tệp lịch sử chỉ để tra cứu có timestamp trùng log trực tiếp, **When** luồng trực tiếp xét luật, **Then** không dùng các sự kiện trong tệp làm bằng chứng hoặc làm tăng ngưỡng đếm.

### User Story 5 - Thống nhất dữ liệu và tiếp tục sau lỗi (Priority: P1)

Người vận hành muốn kết quả có thể tiếp tục và kiểm chứng được khi các module trao đổi dữ liệu hoặc gặp gián đoạn.

**Why this priority**: Thiếu hợp đồng vận hành có thể làm bỏ việc hoặc thay đổi kết luận cảnh báo.

**Independent Test**: Dùng hai mẫu hãng, một field cũ, lỗi retry và nhóm recovered cold-load.

**Acceptance Scenarios**:

1. **Given** cùng hiện tượng từ hai hãng, **When** chuẩn hóa, **Then** có cùng trường/trạng thái/lớp hoặc lý do chưa đủ căn cứ.
2. **Given** sự kiện failed được đưa lại chờ có audit, **When** thử lại, **Then** giữ ID/raw và không nhân đôi bằng chứng.
3. **Given** nhóm recovered bị thu hồi, **When** nạp lại, **Then** giữ đúng cảnh báo và xác nhận hiện hành.

### User Story 6 - Hiểu và truy vết mức độ nghiêm trọng của cảnh báo (Priority: P1)

Người giám sát muốn biết mức độ của cảnh báo và phiên bản rule đã gán mức đó, để ưu tiên xem cảnh báo và hiểu các bằng chứng khi tra lại.

**Lý do ưu tiên.** LinkFlap có thể được phát hiện từ nhiều bản tin mang các mức khác nhau. Người giám sát cần một mức thống nhất cho cảnh báo và vẫn thấy được mức của từng bản tin khi tra cứu.

**Kiểm thử độc lập.** Dùng hai chuỗi đủ ngưỡng LinkFlap với severity syslog khác nhau. Tạo cảnh báo, thay đổi trạng thái, rồi công bố một phiên bản rule thử có mức khác và đối chiếu cảnh báo trước và sau thay đổi.

**Kịch bản nghiệm thu**

1. **Given** LinkFlap đã cấu hình mức `Warning (4)` và chuỗi đủ 5 lần chuyển trong 60 giây có bản tin `Error (3)` hoặc bản tin chưa biết severity, **When** hệ thống tạo cảnh báo, **Then** cảnh báo mang `Warning (4)` và mức của các bản tin vẫn truy xuất được theo bằng chứng.
2. **Given** cảnh báo LinkFlap đã được tạo, **When** có ACK, phục hồi (`recovered`), tái phát khi cảnh báo chưa đóng, hiệu chỉnh bằng chứng hoặc CLOSE hợp lệ, **Then** hệ thống áp dụng thay đổi theo 002 và giữ mức độ đã gán cho cùng cảnh báo.
3. **Given** rule thử có phiên bản cũ ở mức `4` và phiên bản mới ở mức `3`, **When** phiên bản mới tạo một cảnh báo sau khi cảnh báo cũ đã đóng, **Then** cảnh báo cũ giữ mức `4` và cảnh báo mới có mức `3`, mỗi mức truy được về đúng phiên bản.
4. **Given** một phiên bản rule thiếu mức độ hoặc khai báo `-1`, `8` hay `4.5`, **When** nhóm thử công bố phiên bản đó, **Then** hệ thống từ chối công bố, chỉ rõ trường và lý do không hợp lệ. Phiên bản hợp lệ đang hoạt động tiếp tục được sử dụng.

### Edge Cases

- Thiếu năm/múi giờ: giữ chuỗi gốc; chỉ suy ra khi có ngữ cảnh rõ ràng, không tự lấy năm hiện tại cho tệp lịch sử.
- Sự kiện đến trễ: giữ riêng thời gian phát sinh và tiếp nhận; không sửa thời gian phát sinh cho khớp lúc nhận.
- Relay, NAT, hostname hoặc IP trùng: để thiết bị chưa xác định nếu nhận diện mơ hồ.
- Hai lần nhận có cùng nội dung có thể là hai sự kiện thật; không khử trùng chỉ bằng raw/hash.
- Thiếu trường cần để xét hoặc gom nhóm: không tự điền giá trị để làm luật thỏa.
- Nhiều bên xử lý cùng nhóm: không tạo hai cảnh báo đang mở cùng khóa gom.
- Chuẩn hóa lại: không thay đổi âm thầm dữ liệu đã dùng làm bằng chứng. Lần đầu chỉ chuẩn hóa lại sự kiện chưa hoàn tất tương quan.
- Tệp lịch sử mặc định chỉ để tra cứu. Khi chủ động đánh giá lịch sử, phải tách khỏi luồng trực tiếp và các đợt nhập khác.
- Byte không giải mã được và đầu vào chỉ gồm dữ liệu đã xử lý: giữ đúng đầu vào đã nhận, không tự tuyên bố có log gốc thiết bị nếu nguồn không cung cấp.
- Lưu bền vững không bảo đảm nhận đủ log từ thiết bị: mất gói trước điểm lưu là rủi ro của bước thu thập.

- Tên trường trạng thái khác nhau giữa nguồn và projection; không có căn cứ lớp vật lý/giao thức.
- Lỗi tạm retry và lỗi logic failed phải được chọn lại có kiểm soát, không mắc kẹt hoặc coi là đã xử lý.
- Cache recovered bị thu hồi rồi người giám sát CLOSE trước khi có log mới; cold-load phải đọc snapshot hiện hành.
- Syslog bằng chứng có severity khác nhau hoặc chưa xác định severity. Điều kiện rule quyết định khi nào tạo cảnh báo, còn mức của cảnh báo lấy từ phiên bản rule tương ứng.
- Kết thúc flap với trạng thái quan sát cuối là `DOWN` vẫn giữ mức độ đã gán. Kết quả `flap_stopped_down` được ghi riêng theo 004.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Mỗi sự kiện MUST có định danh ổn định, nguồn, thời điểm tiếp nhận và đầu vào gốc; bản gốc MUST được lưu trước khi chuẩn hóa.
- **FR-002**: Hệ thống MUST bảo toàn đầu vào khi chuẩn hóa/giải mã lỗi; bản hiển thị không được thay thế bằng chứng gốc.
- **FR-003**: Hệ thống MUST phân biệt chuẩn hóa đang chờ, thành công, một phần, thất bại; trường chưa biết MUST không bị điền giá trị giả.
- **FR-004**: Mọi hãng MUST dùng chung quy ước sự kiện, có thông tin chuẩn hóa và chi tiết nguồn riêng; log hãng chưa hỗ trợ MUST vẫn được lưu.
- **FR-005**: Thiết bị MUST có định danh quản lý ổn định; sự kiện được phép chưa nhận diện thiết bị; nhận diện mơ hồ MUST không tự gán sai.
- **FR-006**: Sự kiện MUST giữ hostname báo trong log và thông tin hãng, hệ điều hành, loại thiết bị đã xác định lúc chuẩn hóa, không bị thay theo danh mục về sau.
- **FR-007**: Hệ thống MUST phân biệt thời gian phát sinh, tiếp nhận, chuỗi thời gian gốc và căn cứ xác định; luật thời gian MUST không dùng thời gian thiếu căn cứ như thời gian thiết bị chính xác.
- **FR-008**: Người giám sát MUST lọc kết hợp theo thời gian nhận/phát sinh, thiết bị, hãng, mức độ, mã/loại sự kiện, trạng thái; MUST tìm được nội dung thông điệp và thuộc tính nghiệp vụ, với thứ tự kết quả ổn định.
- **FR-009**: Luật MUST có định danh logic, phiên bản, điều kiện, tiêu chí gom nhóm, mức độ cảnh báo và trạng thái sử dụng; nội dung phiên bản đã lưu MUST không bị ghi đè.
- **FR-010**: Cảnh báo MUST tham chiếu đúng một phiên bản luật, giữ nhóm đối tượng, mức độ riêng, thời gian bằng chứng đầu/cuối và thời gian tạo/cập nhật. Tín hiệu bất thường/phục hồi và xác nhận mới/đã thấy/đã đóng MUST độc lập theo feature 002; định danh cảnh báo là định danh sự cố.
- **FR-011**: Cảnh báo MUST có ít nhất một sự kiện phát sinh; sự kiện MUST có thể tham gia nhiều cảnh báo và có vai trò phát sinh hoặc phục hồi. Mỗi liên kết cùng cảnh báo–sự kiện–vai trò MUST duy nhất theo feature 002.
- **FR-012**: Cùng phiên bản luật, nhóm và ngữ cảnh đánh giá MUST có nhiều nhất một cảnh báo chưa đóng, kể cả đã phục hồi. Chỉ đóng sau phục hồi và xác nhận của người giám sát; sau đóng không tự mở lại bản cũ, theo feature 002.
- **FR-013**: Hệ thống MUST phân biệt xét luật đang chờ, đã xét, lỗi và chủ động bỏ qua; không có cảnh báo không đồng nghĩa chưa xử lý.
- **FR-014**: Ghi cảnh báo, liên kết bằng chứng và ghi nhận hoàn tất xét luật cho sự kiện MUST cùng thành công hoặc không có hiệu lực; xét lại cùng định danh MUST không nhân đôi bằng chứng.
- **FR-015**: Hệ thống MUST ngăn xóa ngầm thiết bị còn lịch sử, phiên bản luật được tham chiếu và sự kiện làm bằng chứng. Lab mặc định không tự xóa theo thời gian.
- **FR-016**: Sự kiện không thỏa luật hoặc không chuẩn hóa được MUST vẫn tìm được. Chuẩn hóa lại MUST giữ định danh/bản gốc và chưa được sửa bằng chứng đã hoàn tất tương quan.
- **FR-017**: Mỗi luật logic MUST chỉ có một phiên bản đang bật; cảnh báo cũ tiếp tục tham chiếu phiên bản cũ.
- **FR-018**: Dữ liệu mẫu MUST là dữ liệu lab/giả lập, không chứa thông tin đăng nhập hoặc log/định danh production.
- **FR-019**: Tệp lịch sử MUST mặc định không tạo cảnh báo và MUST được tách ngữ cảnh ngay khi tiếp nhận, kể cả khi chỉ để tra cứu; không được làm bằng chứng đếm cho luồng trực tiếp. Khi chủ động đánh giá lịch sử, chỉ tương quan trong cùng đợt phát lại. Chính sách dữ liệu đến muộn và thời hạn lưu production không được tự coi là đã chốt.

- **FR-020**: Kết quả xử lý sự kiện MUST ghi được tình trạng log trễ, tính bù đủ/không đủ hoặc ngoài phạm vi; event_time/received_at và raw không bị sửa để hợp thức thứ tự.
- **FR-021**: Cảnh báo MUST giữ kết quả rule và audit nguồn syslog/timer/correction/operator, mốc hiệu lực riêng với thời gian ghi; không tạo event giả cho timer.
- **FR-022**: Checkpoint MUST khôi phục quan sát/baseline và lịch đánh giá, không chỉ N mốc; dọn RAM MUST không xóa raw/checkpoint và phải cho phép cold-load/tính bù an toàn.
- **FR-023**: Hiệu chỉnh có ý nghĩa MUST được audit cùng kết quả/checkpoint, kể cả trạng thái không đổi; cảnh báo closed và lịch sử cũ không bị sửa ngầm.

- **FR-024**: Cùng loại sự kiện interface MUST có tên trường, kiểu, trạng thái và lớp tín hiệu thống nhất giữa các hãng; giá trị không biết MUST không được suy đoán để đủ điều kiện rule.
- **FR-025**: Sự kiện lỗi MUST phân biệt lỗi tạm chưa hoàn tất với lỗi cần khắc phục; đưa lại chờ xét MUST có dấu vết, giữ định danh và không nhân đôi kết quả.
- **FR-026**: Thu hồi state đã phục hồi nhưng chưa đóng MUST không xóa dữ liệu cần nạp lại hoặc thay đổi định danh/xác nhận; bằng chứng và ranh giới chu kỳ vẫn được bảo vệ.
- **FR-027**: Mốc kích hoạt phiên bản rule và lịch sử đưa lại sự kiện lỗi MUST được lưu đủ để truy vết, không tự thay phiên bản đánh giá trong một lượt thử lại.

- **FR-028**: Sức khỏe và workset pipeline MUST có định danh thành phần/ngữ cảnh, freshness, căn cứ quan sát và tiến độ bền vững riêng với syslog; ghi heartbeat không được làm mất receipt chưa hoàn tất.
- **FR-029**: Mỗi phiên bản rule được công bố MUST có đúng một mức độ cảnh báo bằng mã nguyên từ `0` đến `7`. Hệ thống MUST từ chối công bố phiên bản thiếu hoặc khai báo sai mức, ghi rõ lý do và giữ nguyên phiên bản hợp lệ đang hoạt động nếu có.
- **FR-030**: Khi tạo cảnh báo, hệ thống MUST gán mức từ đúng phiên bản rule đã đánh giá. LinkFlap trong prototype MUST dùng `Warning (4)`. Severity khác nhau hoặc chưa xác định trên các syslog bằng chứng không thay đổi mức được gán.
- **FR-031**: Cùng một cảnh báo MUST giữ mức độ được gán lúc tạo qua ACK, phục hồi, tái phát, hiệu chỉnh bằng chứng, CLOSE và thay đổi phiên bản rule. Thay đổi mức trong cấu hình MUST tạo phiên bản mới và chỉ áp dụng cho cảnh báo do phiên bản đó tạo.
- **FR-032**: Khi tra cứu một cảnh báo, người giám sát MUST xác định được mức của cảnh báo và phiên bản rule đã gán mức. Khi xem bằng chứng, mức của từng bản tin MUST được phân biệt rõ với mức cảnh báo. Mức chưa xác định của syslog phải được biểu diễn rõ.

### Quy ước gán mức độ nghiêm trọng

Mã nhỏ hơn biểu thị mức độ cao hơn. Prototype dùng **Warning (4)** cho LinkFlap vì syslog cho thấy interface dao động nhưng chưa đủ để đánh giá tác động dịch vụ. Các mức còn lại trong bảng là gợi ý để review khi thiết kế thêm rule.

| Mức | Tiêu chí đề xuất | Ví dụ |
|---|---|---|
| Warning (`4`) | Bất thường cần theo dõi, mức ảnh hưởng dịch vụ chưa rõ | Interface đạt ngưỡng LinkFlap. |
| Error (`3`) | Bằng chứng cho thấy một kết nối hoặc chức năng cụ thể bị gián đoạn | Một rule tương lai xác nhận kết nối gián đoạn vượt ngưỡng. |
| Critical (`2`) | Bằng chứng đủ theo tiêu chí ảnh hưởng nghiêm trọng đã được nhóm định nghĩa | Mất nhiều kết nối trọng yếu theo điều kiện của một rule tương quan tương lai. |

### Key Entities *(include if feature involves data)*

- **Thiết bị**: Định danh ổn định, tên, hostname cấu hình, hãng, loại, hệ điều hành, địa chỉ quản trị chính và trạng thái sử dụng; không lưu thông tin đăng nhập.
- **Sự kiện**: Một syslog với đầu vào gốc, dữ liệu nhận diện, nguồn/ngữ cảnh, thời gian và trạng thái xử lý; có thể chưa biết thiết bị.
- **Phiên bản luật**: Nội dung bất biến của một luật logic; điều kiện, gom nhóm, mức độ. Được phép bật/tắt.
- **Cảnh báo**: Kết quả thỏa một phiên bản luật, có định danh sự cố, mức độ đã gán khi tạo, hai chiều trạng thái và khoảng thời gian bằng chứng; không sao chép sự kiện.
- **Liên kết cảnh báo–sự kiện**: Ghi sự kiện nào góp vào cảnh báo nào, vai trò phát sinh/phục hồi và thời điểm liên kết; mỗi cặp kèm vai trò duy nhất.
- **Lịch sử trạng thái**: Ghi thứ tự thay đổi, trước/sau, chủ thể và bằng chứng theo feature 002; bổ sung vào năm thực thể nền.
- **Checkpoint trạng thái nhóm**: Phiên bản thuật toán và trạng thái đếm/nhận định cần khôi phục theo feature 003; tách khỏi lịch sử và xác nhận người giám sát.

- **Sức khỏe pipeline và work receipt**: Trạng thái thành phần/đoạn quan sát cùng tập công việc chưa hoàn tất; bảng chung bổ sung cho hợp đồng 005 và worker 003.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Bộ 1.000 đầu vào có nhãn đã lưu bền vững, gồm log đầy đủ, thiếu trường, hãng chưa hỗ trợ và lỗi giải mã: 100% truy xuất được đúng đầu vào gốc/trạng thái; không bỏ log chỉ vì chuẩn hóa lỗi.
- **SC-002**: Trên 100.000 sự kiện giả lập của ít nhất hai hãng, 40 truy vấn có kết quả đóng băng trả đúng 100% định danh; phân trang trên tập cố định không lặp/bỏ sót.
- **SC-003**: Trên cùng bộ dữ liệu, ít nhất 95/100 lượt tìm kiếm chuẩn trả trang đầu tối đa 50 sự kiện trong 2 giây; ghi rõ máy thử và truy vấn. Đây là mục tiêu đề xuất cho lab, chưa phải kết quả đo hoặc cam kết production.
- **SC-004**: 100% cảnh báo của bộ kịch bản truy được đúng phiên bản luật và tập bằng chứng; sự kiện tham gia hai cảnh báo vẫn chỉ có một bản trong kho sự kiện.
- **SC-005**: Xét lại cùng tập định danh 10 lần và mô phỏng hai bên xử lý cùng nhóm: không tăng số liên kết cùng vai trò, không có hai cảnh báo chưa đóng cùng phiên bản luật, nhóm, ngữ cảnh; lịch sử chuyển thực không bị nhân đôi theo feature 002.
- **SC-006**: Ở ba điểm gián đoạn — sau lưu đầu vào, trước ghi chuẩn hóa, giữa ghi cảnh báo — 100% đầu vào đã lưu còn truy xuất được; không có kết quả ghi dở được coi là hoàn tất.
- **SC-007**: Sau đổi danh mục thiết bị hoặc tạo phiên bản luật, 100% mẫu lịch sử vẫn giữ đúng thông tin đã ghi nhận và nội dung phiên bản ban đầu.

- **SC-008**: Bộ mẫu timer/correction của 002/003 giữ đúng outcome, mốc hiệu lực và thời gian ghi; timer không tạo raw giả, lặp facts không tăng audit revision.
- **SC-009**: Với state bị evict và log trễ sau đó, 100% case khôi phục chung ở 003 và rule LinkFlap ở 004 khôi phục đúng baseline/bằng chứng, không đếm đôi hoặc xóa dữ liệu bền vững.

- **SC-010**: Bộ mẫu interface Cisco XRv đã gán nhãn, gồm giá trị cũ, trường thiếu và sai lớp, cho đúng 100% kết quả chuẩn hóa hoặc lý do không đủ điều kiện trong prototype, theo hợp đồng 005. Bộ mẫu của hãng thứ hai được dùng khi kiểm chứng mở rộng.
- **SC-011**: Trong bộ thử lỗi tạm, lỗi logic, đưa lại chờ xét và cold-load cảnh báo recovered chưa đóng, 100% giữ định danh/bằng chứng, health/receipt và không nhân đôi kết quả.
- **SC-012**: Với mọi chuỗi thử đủ ngưỡng LinkFlap, gồm chuỗi có severity bằng chứng khác nhau hoặc chưa biết, 100% cảnh báo mới có mức `Warning (4)` và người kiểm thử truy được mức của từng syslog theo bằng chứng.
- **SC-013**: Trong tất cả ca ACK, phục hồi, tái phát, hiệu chỉnh bằng chứng, CLOSE và đổi phiên bản, mỗi cảnh báo hiện có giữ đúng mức ban đầu. Mỗi cảnh báo mới truy được về đúng mức của phiên bản đã tạo nó.
- **SC-014**: Tất cả cấu hình thiếu mức hoặc có mã ngoài `0–7` hay giá trị không nguyên trong bộ thử đều bị từ chối với lý do cụ thể. Cấu hình hợp lệ đang hoạt động vẫn tiếp tục được dùng.

## Assumptions

- Prototype dùng [mô hình database hiện tại](database-proposal.md) làm cơ sở thiết kế.
- Người dùng là người giám sát và vận hành lab. Hợp đồng danh tính/giao diện thuộc [005](../005-monitoring-integration/spec.md); vòng đời và engine tiếp tục ở 002/003.
- Giả định một sự kiện được tham gia nhiều cảnh báo; mỗi cảnh báo do một phiên bản luật tạo ra. Chưa có thực thể sự cố độc lập.
- Lần đầu ưu tiên điều kiện bằng nhau kết hợp, đếm trong khoảng thời gian và gom theo thuộc tính xác định được. Luật chuỗi, nguyên nhân gốc và sửa toàn bộ bằng chứng lịch sử là bước sau.
- Cảnh báo chưa đóng tiếp tục được theo dõi; phục hồi theo syslog chưa đồng nghĩa đóng. Hết cửa sổ đếm không tự kết luận phục hồi; quy tắc đầy đủ nằm ở feature 002.
- Tệp lịch sử mặc định chỉ tra cứu; mỗi đợt phát lại chủ động có ngữ cảnh riêng. Luật thời gian dùng thời điểm phát sinh có căn cứ, không tự thay bằng thời điểm nhận.
- Chưa có thời hạn lưu được duyệt: lab giữ đến thao tác dọn rõ ràng, không xóa dây chuyền bằng chứng. Phải chốt dung lượng/thời hạn trước vận hành lâu dài.
- Danh mục ban đầu chỉ có địa chỉ quản trị chính; quản lý nhiều địa chỉ/site/VRF chưa nằm trong phạm vi. Nhận diện mơ hồ giữ trạng thái chưa biết.
- Thông tin hãng/hệ điều hành/loại trên sự kiện là bản ghi nhận lúc chuẩn hóa; ghi nguồn xác định để phân biệt nội dung log và dữ liệu danh mục.
- Mốc dữ liệu/thời gian ở SC-001 đến SC-003 là đề xuất kiểm chứng, cần xác nhận trước dùng làm nghiệm thu.
- Phụ thuộc prototype: danh mục lab Cisco XRv, mẫu syslog XRv có nhãn, quy ước thuộc tính, ngữ cảnh thời gian và định nghĩa LinkFlap. Dữ liệu giả lập đa hãng vẫn dùng được để kiểm tra mô hình lưu trữ.
- Tài liệu đi kèm `data-model.md` giải thích phương án bảng/field/ràng buộc; chưa phải migration đã chạy hay phương án được duyệt.
- Prototype gán mức độ cố định theo phiên bản rule. Nâng mức động theo vai trò interface hoặc tác động dịch vụ, và sửa trực tiếp mức của cảnh báo hiện hữu thuộc phạm vi xem xét sau prototype. Bố cục, màu sắc và bộ lọc của màn hình thuộc thiết kế frontend riêng.
