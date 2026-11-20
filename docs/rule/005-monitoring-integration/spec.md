# Feature Specification: Tích hợp thu thập, chuẩn hóa và màn hình giám sát

**Feature Branch**: Không tạo nhánh trong lần đặc tả này.

**Created**: 2026-11-20

**Status**: Draft — bổ sung hợp đồng tích hợp theo yêu cầu, chưa triển khai hoặc nghiệm thu.

**Input**: User description: "Bổ sung các vấn đề đã đề xuất vào tài liệu hiện có; phần không phù hợp có thể tạo tài liệu mới."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tiếp nhận log qua lab và nhập dữ liệu (Priority: P1)

Người vận hành muốn nhận syslog từ thiết bị lab và gửi log đơn/tệp, giữ được nguồn gốc cùng kết quả tiếp nhận.

**Why this priority**: Các bước phân tích cần đầu vào bền vững, đúng ngữ cảnh và có giới hạn sức chứa.

**Independent Test**: Gửi log lab, một log văn bản, một đối tượng đã chuẩn hóa và tệp có dòng hợp lệ/lỗi; mô phỏng lỗi ghi.

**Acceptance Scenarios**:

1. **Given** đầu vào được chấp nhận, **When** lưu thành công, **Then** truy lại được nguyên bản, nguồn và thời điểm nhận; kênh có phản hồi chỉ báo thành công sau khi lưu.
2. **Given** tệp lịch sử, **When** tiếp nhận, **Then** có ngữ cảnh riêng và mặc định chỉ tra cứu, không tạo cảnh báo trực tiếp.
3. **Given** đầu vào quá giới hạn hoặc lưu thất bại, **When** xử lý, **Then** phản hồi/đếm lỗi rõ, không báo đã tiếp nhận thành công.
4. **Given** nguồn chỉ gửi dữ liệu đã tách trường, **When** lưu, **Then** giữ nguyên đầu vào đã nhận và ghi rõ không có bản syslog gốc thiết bị.

### User Story 2 - Chuẩn hóa thống nhất giữa các hãng (Priority: P1)

Người giám sát muốn cùng hiện tượng từ Cisco/Juniper dùng được cùng rule mà không phải chọn field theo hãng.

**Why this priority**: Sai hợp đồng trường có thể khiến rule bỏ qua toàn bộ dữ liệu hoặc đếm nhầm.

**Independent Test**: Dùng mẫu hai hãng có nhãn, field cũ, lớp vật lý/giao thức, lỗi byte và thời gian thiếu căn cứ.

**Acceptance Scenarios**:

1. **Given** thông điệp cùng hiện tượng có đủ căn cứ, **When** chuẩn hóa, **Then** có cùng tên trường, kiểu, trạng thái và lớp tín hiệu.
2. **Given** tên field cũ được hỗ trợ, **When** chuyển đổi tại biên tiếp nhận, **Then** chỉ có một biểu diễn chuẩn dùng phía sau; raw giữ nguyên.
3. **Given** không rõ lớp/thời gian/thiết bị, **When** xử lý, **Then** giữ unknown và lý do, không tự điền để đủ điều kiện rule.
4. **Given** chuẩn hóa đã lưu nhưng không có lời gọi rule trực tiếp, **When** worker lấy việc, **Then** vẫn xét đúng các sự kiện sẵn sàng theo 003.

### User Story 3 - Xem và đồng bộ trạng thái cảnh báo (Priority: P1)

Người giám sát muốn xem danh sách, bằng chứng, lịch sử và các thay đổi đã lưu, kể cả khi màn hình mất kết nối.

**Why this priority**: Màn hình phải phản ánh kết quả có hiệu lực và không ghi đè thao tác từ trạng thái cũ.

**Independent Test**: Tạo/phục hồi cảnh báo, ngắt màn hình, thay trạng thái rồi kết nối lại; thử thao tác trên bản đã cũ.

**Acceptance Scenarios**:

1. **Given** kết quả đã lưu, **When** màn hình giám sát đang hoạt động làm mới, **Then** hiển thị snapshot hiện hành theo bộ lọc và phiên bản, không có dữ liệu chưa lưu thành công.
2. **Given** mất kết nối, **When** xem màn hình, **Then** thấy trạng thái dữ liệu cũ và lần cập nhật thành công gần nhất; khi kết nối lại phải tải snapshot mới.
3. **Given** bản đang xem đã đổi, **When** xác nhận/đóng, **Then** kiểm tra phiên bản theo 002 và yêu cầu tải lại nếu xung đột, không tự ghi đè.
4. **Given** worker dừng sau khi lưu thành công trước khi có thông báo, **When** màn hình đọc lại, **Then** vẫn tìm được kết quả và lịch sử đã lưu.

### User Story 4 - Phân biệt quyền xem, thao tác và tiếp nhận (Priority: P1)

Người vận hành muốn truy cập và thay đổi được kiểm tra theo danh tính, không tin người thao tác do đầu vào tự khai.

**Why this priority**: ACK/CLOSE, đưa lại sự kiện lỗi và nhập dữ liệu đều ảnh hưởng bằng chứng hoặc tiến độ.

**Independent Test**: Thử danh tính chỉ xem, người giám sát, nguồn nhập và principal có quyền phục hồi sự kiện.

**Acceptance Scenarios**:

1. **Given** chỉ có quyền xem, **When** yêu cầu ACK/CLOSE hoặc đưa lại sự kiện lỗi, **Then** bị từ chối và không có thay đổi.
2. **Given** người giám sát hợp lệ, **When** ACK/CLOSE, **Then** chủ thể từ phiên xác thực và đúng quy tắc 002, không nhận actor tự khai.
3. **Given** nguồn nhập dữ liệu, **When** tự đặt scope live hoặc trạng thái xử lý/đã đóng, **Then** server kiểm tra quyền và tự quyết định trường quản lý.
4. **Given** principal có quyền phục hồi sự kiện, **When** gửi lại cùng định danh thao tác, **Then** chỉ có một audit và không nhân đôi xử lý.

### User Story 5 - Nhìn thấy sức khỏe pipeline và khoảng mất quan sát (Priority: P1)

Người giám sát muốn phân biệt thiết bị không gửi log với hệ thống chưa nhận/xử lý được dữ liệu.

**Why this priority**: Khoảng không quan sát không được làm bằng chứng kết thúc bất thường.

**Independent Test**: Dừng collector/normalizer/worker, ngắt ghi và làm gián đoạn clock; khôi phục với/không đủ dữ liệu.

**Acceptance Scenarios**:

1. **Given** một thành phần không còn báo sức khỏe đúng hạn, **When** hiển thị và xét timer, **Then** báo thiếu quan sát và chặn quiet liên quan theo 003.
2. **Given** pipeline hoạt động nhưng còn raw/sự kiện chưa xử lý trước deadline, **When** đánh giá, **Then** chưa coi đó là khoảng yên.
3. **Given** khôi phục sau gap, **When** kiểm tra lịch sử, **Then** chỉ dựng lại đoạn có căn cứ đầy đủ; đoạn không đủ bắt đầu khoảng quan sát an toàn mới.
4. **Given** dòng nhập tiếp tục khi DB gần đầy, **When** không thể tiếp nhận bền vững, **Then** báo sức chứa/lỗi thay vì thành công giả.

### Edge Cases

- Mất gói trước khi lưu, lỗi byte, đầu vào quá lớn, tệp nhập dở và phản hồi bị mất.
- Dữ liệu đã chuẩn hóa không có raw thiết bị; người gửi tự khai trạng thái/danh tính/scope.
- Field cũ mâu thuẫn field chuẩn, timestamp thiếu năm/múi giờ hoặc trùng mâu thuẫn.
- Cùng log được gửi lại bằng lần nhận mới không mặc định là cùng sự kiện.
- Màn hình mất kết nối, truy vấn rỗng, lỗi tải, thao tác stale hoặc không đủ quyền.
- Heartbeat cũ, instance cũ ghi nhầm, DB không ghi được health, backlog chuẩn hóa và gap coverage.
- Sức khỏe pipeline không chứng minh UDP giao nhận đầy đủ hoặc thiết bị thực tế đã UP.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống MUST hỗ trợ nguồn UDP lab, đầu vào đơn văn bản/đã chuẩn hóa và tệp syslog theo giới hạn được công bố.
- **FR-002**: Đầu vào được chấp nhận MUST lưu bền vững trước chuẩn hóa; phản hồi tiếp nhận thành công chỉ được trả sau lưu.
- **FR-003**: Lỗi byte/chuẩn hóa MUST giữ bằng chứng gốc đã chấp nhận và lý do; đầu vào bị từ chối quá giới hạn phải có kết quả/đếm lỗi rõ.
- **FR-004**: Đợt nhập tệp MUST có định danh nguồn và số dòng để truy vết phần đã lưu; nhập dở không được báo cả tệp thành công.
- **FR-005**: Dữ liệu lịch sử MUST mặc định chỉ tra cứu trong scope riêng; chủ động đánh giá phải có quyền và không trộn live.
- **FR-006**: Dữ liệu đã chuẩn hóa đầu vào MUST giữ đúng bản đã nhận và đánh dấu nguồn; không giả là có nguyên bản thiết bị.
- **FR-007**: Thông tin do nguồn tự khai MUST được kiểm tra; server sở hữu định danh, thời gian nhận, phạm vi, trạng thái xử lý và danh tính thao tác.
- **FR-008**: Cùng loại sự kiện interface MUST có hợp đồng trường/kiểu/trạng thái/lớp duy nhất; chuyển field cũ chỉ thực hiện tại biên.
- **FR-009**: Parser MUST có mẫu Cisco/Juniper được gán nhãn đúng ngữ nghĩa; hãng chưa hỗ trợ vẫn lưu raw và không suy đoán ánh xạ.
- **FR-010**: Field cũ và chuẩn mâu thuẫn, lớp không rõ hoặc thời gian thiếu căn cứ MUST có diagnostic; không tự điền để đạt điều kiện rule.
- **FR-011**: Chuẩn hóa thành công/một phần MUST làm dữ liệu sẵn sàng cho cơ chế nhận việc 003; không phụ thuộc việc gọi từng handler.
- **FR-012**: Người xem MUST tìm/lọc log và cảnh báo, xem snapshot/bằng chứng/lịch sử theo 001/002, với phân trang ổn định và lỗi/rỗng rõ.
- **FR-013**: Màn hình MUST chỉ đọc dữ liệu có hiệu lực, làm mới có chu kỳ giới hạn và tải lại snapshot khi kết nối lại; không yêu cầu truyền mọi thay đổi tức thời trong bản đầu.
- **FR-014**: Màn hình mất kết nối MUST thể hiện dữ liệu cũ và lần cập nhật thành công; không hiển thị như trạng thái trực tiếp vẫn bình thường.
- **FR-015**: ACK/CLOSE MUST kiểm tra quyền/danh tính/phiên bản phía server và áp đúng vòng đời 002; input không tự đổi tín hiệu.
- **FR-016**: Quyền chỉ xem, quyền thao tác, quyền nhập và quyền đưa lại sự kiện lỗi MUST được tách và mặc định từ chối khi thiếu quyền.
- **FR-017**: Đưa lại sự kiện lỗi hoặc yêu cầu dựng lại có kiểm soát MUST có quyền, lý do, định danh thao tác duy nhất và audit theo 001/003; dựng lại không được giả là nhận sự kiện mới.
- **FR-018**: Health collector/normalizer/correlator MUST có scope, instance, thời điểm báo và đầu đoạn healthy liên tục, lưu riêng với syslog.
- **FR-019**: Health quá hạn, lỗi lưu, mất thời gian đáng tin hoặc backlog ảnh hưởng MUST chặn kết luận khoảng yên theo 003; im lặng không tự chứng minh healthy.
- **FR-020**: Khôi phục MUST giữ/đánh dấu được gap quan sát và chỉ dùng lại đoạn có căn cứ; không báo đã phục hồi đầy đủ khi thiếu lịch sử.
- **FR-021**: Hệ thống MUST công bố sức chứa/giới hạn đầu vào, theo dõi từ chối và dừng nhận khi không lưu được; không báo thành công giả.
- **FR-022**: Credential và log mẫu MUST được bảo vệ theo constitution; tài liệu/ví dụ không chứa secret hoặc dữ liệu production.
- **FR-023**: Bản đầu MUST không cung cấp cấu hình/khắc phục thiết bị, chỉnh logic rule qua giao diện, tự đóng hoặc tự đánh giá lịch sử khi nhập.
- **FR-024**: Các chu kỳ và giới hạn thử lab MUST được phân biệt với tiêu chí hiệu năng đã đo; UI hiển thị sức khỏe/độ trễ độc lập với mức độ cảnh báo thiết bị.

### Key Entities *(include if feature involves data)*

- **Đợt/nguồn nhập**: Nguồn lab, định danh đợt và dòng, loại nguyên bản và ngữ cảnh đánh giá.
- **Hợp đồng sự kiện**: Tên trường, trạng thái, lớp và căn cứ chuẩn hóa dùng chung giữa các hãng.
- **Danh tính và quyền**: Người xem, người giám sát và principal nhập/phục hồi với quyền phía server.
- **Snapshot màn hình**: Dữ liệu đã lưu, phiên bản, bộ lọc/phân trang và thời điểm cập nhật.
- **Sức khỏe pipeline**: Thành phần, scope, instance, đầu đoạn healthy, lần báo gần nhất và lý do suy giảm; không là syslog thiết bị.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Trong bộ 1.000 đầu vào hợp lệ/lỗi/đã chuẩn hóa/tệp nhập dở, 100% đầu vào đã báo lưu thành công truy được đúng bản gốc và nguồn; không có thành công giả khi lỗi ghi.
- **SC-002**: Với ít nhất 40 mẫu Cisco/Juniper có nhãn gồm field cũ, sai lớp và thiếu thời gian, 100% khớp kết quả chuẩn hoặc diagnostic mong đợi.
- **SC-003**: Bộ thử quyền bao phủ mọi thao tác với từng nhóm quyền; 100% yêu cầu thiếu quyền bị từ chối mà không đổi dữ liệu.
- **SC-004**: Sau mất kết nối và đọc lại, 100% tình huống màn hình khớp snapshot đã lưu và giữ đúng lịch sử/phiên bản; thao tác stale không ghi đè.
- **SC-005**: Màn hình đang hoạt động có chu kỳ làm mới mục tiêu lab 1 giây; đo tổng độ trễ cùng 003/004, không gọi 1 giây là SLA nhận log đến hiển thị.
- **SC-006**: Toàn bộ ca health cũ, gap, DB lỗi, backlog trước deadline và instance stale đều chặn kết thúc sai, hiển thị lý do và khôi phục đúng đoạn có căn cứ.
- **SC-007**: Thử lại cùng thao tác ACK/CLOSE hoặc đưa lại sự kiện lỗi 10 lần không nhân đôi audit/kết quả; gửi lại input với ID nhận mới được ghi nhận đúng chính sách riêng.
- **SC-008**: Bộ thử giới hạn đầu vào/sức chứa cho kết quả chấp nhận/từ chối rõ 100%, giữ nguyên phần đã lưu và không trộn scope lịch sử với live.

## Assumptions

- Feature mới chỉ sở hữu hợp đồng tích hợp còn thiếu; bảng nền thuộc [001](../001-alert-data-model/spec.md), vòng đời [002](../002-alert-lifecycle/spec.md), engine [003](../003-rule-dispatch-correlation/spec.md), LinkFlap [004](../004-link-flap-rule/spec.md).
- [integration-design.md](integration-design.md) định nghĩa giao tiếp, field, quyền, health và giá trị thử; không triển khai code/SQL trong lần specify.
- Màn hình bản đầu đọc lại trạng thái có chu kỳ; chưa yêu cầu phát lại mọi thông báo tức thời hoặc thêm broker.
- Danh tính lab dùng cấu hình server được bảo vệ; không thêm chức năng đăng ký tài khoản hoặc quản trị rule trên giao diện. Tích hợp danh tính production là nhiệm vụ riêng.
- Tám bảng chung sau khi thêm sức khỏe pipeline; không tạo bảng riêng theo hãng/rule, không tạo syslog giả cho heartbeat.
- Không bảo đảm nhận đủ UDP hoặc khôi phục mọi sự kiện chưa từng được lưu. Retention production, HA và triển khai production chưa được chốt.
