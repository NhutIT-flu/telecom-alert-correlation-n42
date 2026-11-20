# Feature Specification: Điều phối và gom nhóm cảnh báo đa rule

**Feature Branch**: Không tạo nhánh trong lần đặc tả này.

**Created**: 2026-11-19

**Status**: Draft — bản thiết kế đề xuất, chưa triển khai hoặc nghiệm thu.

**Updated**: 2026-11-20 — cụ thể hóa nhận việc, lỗi/thử lại, coverage, revision owner, lịch sử tính bù, state lạnh và giới hạn tài nguyên; tích hợp 005, constitution 2.0.0.

**Input**: User description: "Thiết kế hoàn chỉnh module điều phối/gom nhóm: nhiều rule đăng ký loại syslog chuẩn hóa, một sự kiện vào nhiều rule, điều kiện phát sinh/kết thúc riêng; phân biệt thiết bị–interface, tách thông số khỏi logic, cân bằng tốc độ và chi phí. Phạm vi chỉ giám sát qua syslog."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Công bố rule có cấu hình kiểm tra được (Priority: P1)

Người phát triển muốn thêm định nghĩa rule hoặc thay thông số trong phạm vi logic đã hỗ trợ, không cần thiết kế kho dữ liệu riêng cho từng loại rule.

**Why this priority**: Đây là cơ sở mở rộng nhiều rule mà vẫn kiểm soát đúng ý nghĩa và bằng chứng của cảnh báo.

**Independent Test**: Nạp hai định nghĩa cùng loại xử lý với ngưỡng khác nhau, một định nghĩa thiếu trường và một định nghĩa sai kiểu; đối chiếu các rule được công bố và lý do từ chối.

**Acceptance Scenarios**:

1. **Given** hai định nghĩa hợp lệ cùng logic nhưng khác thông số, **When** công bố, **Then** chúng có phiên bản và kết quả độc lập, dùng chung phần thực thi.
2. **Given** thông số sai kiểu, ngưỡng không hợp lệ hoặc đăng ký loại sự kiện không hỗ trợ, **When** nạp, **Then** không áp dụng cấu hình lỗi hoặc áp dụng nửa chừng; có lý do cụ thể.
3. **Given** đổi cấu hình hoặc logic, **When** công bố phiên bản mới, **Then** giữ tham chiếu phiên bản cũ cho cảnh báo và trạng thái cần tiếp tục theo dõi.
4. **Given** rule chưa có điều kiện phục hồi hợp lệ, **When** yêu cầu bật đầy đủ vòng đời, **Then** từ chối; định nghĩa tắt vẫn có thể giữ làm bản nháp.

### User Story 2 - Đưa sự kiện đến đủ các rule liên quan (Priority: P1)

Người giám sát muốn một sự kiện được sử dụng bởi mọi rule phù hợp, bao gồm cả điều kiện phục hồi, mà không phải xử lý theo tên hãng trên giao diện.

**Why this priority**: Điều phối thiếu hoặc sai làm mất cảnh báo hoặc khiến cảnh báo không kết thúc được.

**Independent Test**: Đăng ký hai rule cùng loại sự kiện, một rule không liên quan và một phiên bản cũ còn cảnh báo chưa đóng; đối chiếu danh sách rule thực nhận.

**Acceptance Scenarios**:

1. **Given** sự kiện thuộc hai rule, **When** điều phối, **Then** cả hai được xét, không dừng sau rule đầu tiên và không gọi lặp một phiên bản vì khớp nhiều đăng ký.
2. **Given** log phục hồi không thỏa điều kiện phát sinh, **When** điều phối, **Then** vẫn đến rule đang chờ bằng chứng phục hồi.
3. **Given** một phiên bản ngừng tạo cảnh báo mới nhưng còn cảnh báo chưa đóng, **When** có sự kiện liên quan, **Then** tiếp tục theo dõi bản cũ mà không tạo nhóm mới bằng phiên bản đã tắt.
4. **Given** thiếu thông tin cần cho một rule nhưng đủ cho rule khác, **When** điều phối, **Then** chỉ bỏ qua rule không đủ điều kiện, giữ lý do và tiếp tục rule phù hợp; sự kiện gốc vẫn truy xuất được.

### User Story 3 - Tách trạng thái đúng đối tượng (Priority: P1)

Người giám sát muốn cùng rule theo dõi nhiều đối tượng có kết quả độc lập, kể cả tên đối tượng giống nhau trên thiết bị khác.

**Why this priority**: Gom sai đối tượng gây cảnh báo giả hoặc che mất sự cố.

**Independent Test**: Đưa dữ liệu xen kẽ cho A/Gi0/0, A/Gi0/1 và B/Gi0/0 cùng nhiều phiên bản/ngữ cảnh; đối chiếu kết quả từng nhóm.

**Acceptance Scenarios**:

1. **Given** các đối tượng nêu trên, **When** nhận sự kiện xen kẽ, **Then** mỗi nhóm có trạng thái độc lập theo rule, phiên bản và ngữ cảnh.
2. **Given** tên hoặc thuộc tính nhóm chưa xác minh, **When** tạo khóa, **Then** không tự gộp alias hay các giá trị thiếu.
3. **Given** nhiều đối tượng dùng cùng loại xử lý, **When** thực thi, **Then** dùng chung logic và tách dữ liệu nhóm; không cần tài nguyên thực thi riêng cho từng interface.

### User Story 4 - Quản lý tài nguyên theo nhu cầu (Priority: P2)

Người vận hành muốn chỉ giữ nóng dữ liệu cần thiết cho các nhóm có hoạt động, với chi phí đo được.

**Why this priority**: Số nhóm và lượng dữ liệu cần giữ ảnh hưởng trực tiếp đến độ trễ và chi phí.

**Independent Test**: Chạy nhóm nóng và nhóm lạnh của nhiều loại rule; đo dữ liệu giữ lại, lỗi quá tải và kết quả sau nạp lại.

**Acceptance Scenarios**:

1. **Given** đối tượng chưa có dữ liệu liên quan, **When** khởi động, **Then** không tạo sẵn state cho toàn bộ danh mục.
2. **Given** handler dùng dữ liệu dẫn xuất có giới hạn, **When** tối ưu, **Then** vẫn giữ hoặc khôi phục được ngữ cảnh cần cho tính bù và khôi phục; giới hạn bộ đệm không bị gọi là toàn bộ state.
3. **Given** một nhóm bị đưa khỏi cache, **When** có sự kiện mới, **Then** lấy lại trạng thái bền vững cần thiết.
4. **Given** tải vượt khả năng, **When** tồn đọng tăng, **Then** hiển thị tồn đọng/độ trễ; không âm thầm bỏ sự kiện đã lưu.

### User Story 5 - Tiếp tục chính xác sau gián đoạn (Priority: P1)

Người giám sát muốn worker hoạt động lại mà không quên cửa sổ đang xét hoặc phát sinh lại cảnh báo đã ghi thành công.

**Why this priority**: Chỉ giữ trạng thái trong bộ nhớ làm thay đổi kết quả sau khởi động lại.

**Independent Test**: Dừng trước lúc đủ điều kiện, giữa ghi kết quả và sau ghi trước phản hồi; phục hồi rồi cung cấp bằng chứng còn thiếu, đối chiếu trạng thái/bằng chứng/lịch sử.

**Acceptance Scenarios**:

1. **Given** đã lưu trạng thái đang tích lũy, **When** khởi động lại rồi nhận bằng chứng làm đủ điều kiện, **Then** tạo đúng một cảnh báo với đủ bằng chứng.
2. **Given** lỗi giữa ghi trạng thái xử lý, cảnh báo, bằng chứng và tiến độ, **When** thử lại, **Then** không có phần ghi dở được coi là hoàn tất và không đếm hai lần cùng định danh sự kiện.
3. **Given** kết quả đã lưu nhưng bộ nhớ chưa cập nhật khi worker dừng, **When** hoạt động lại, **Then** dùng trạng thái đã lưu và không tạo lại kết quả.
4. **Given** gặp lỗi logic rule nghiêm trọng, **When** chưa thể xử lý an toàn, **Then** giữ sự kiện chưa hoàn tất, dừng tiến độ tương quan và thông báo lỗi; khâu thu thập vẫn lưu đầu vào. Bản đầu không hứa cách ly lỗi độc lập từng rule.

### User Story 6 - Kết hợp đúng vòng đời giám sát (Priority: P1)

Người giám sát muốn kết luận của rule áp dụng đúng vòng đời đã đặc tả, vẫn xem được bằng chứng và trạng thái công việc riêng.

**Why this priority**: Phát hiện bất thường, phục hồi, xác nhận đã thấy và đóng có chủ thể khác nhau.

**Independent Test**: Phát kết luận tạo/phục hồi/tái phát trong khi xác nhận hoặc đóng; đối chiếu với feature 002 và thử dữ liệu lịch sử riêng.

**Acceptance Scenarios**:

1. **Given** rule kết luận phục hồi, **When** áp dụng, **Then** chỉ thay tín hiệu; không tự xác nhận hoặc đóng.
2. **Given** cảnh báo đã phục hồi nhưng chưa đóng, **When** đủ điều kiện tái phát, **Then** dùng cùng định danh; sau đóng chỉ chuỗi bằng chứng mới đủ điều kiện mới tạo định danh khác.
3. **Given** log đến trễ, **When** còn ảnh hưởng vùng tính bù, **Then** chèn theo thời gian nguồn và tính lại với audit; log thiếu thời gian không tự được sắp thứ tự, cảnh báo đã đóng và scope khác không bị sửa âm thầm.
4. **Given** người giám sát dùng chức năng theo dõi, **When** xem rule hoặc xác nhận cảnh báo, **Then** không sửa đăng ký/logic rule và không thực hiện thao tác lên thiết bị.

### User Story 7 - Sắp thứ tự và hiệu chỉnh có kiểm soát (Priority: P1)

Người giám sát muốn kết luận có căn cứ thời gian và thấy được các hiệu chỉnh khi log cũ đến sau.

**Why this priority**: Kết luận có thể phụ thuộc thứ tự nguồn và lịch sử, khác thứ tự nhận.

**Independent Test**: Hoán vị thứ tự nhận trong/ngoài khoảng chờ 3 giây, thử dữ liệu mâu thuẫn và hiệu chỉnh bằng chứng.

**Acceptance Scenarios**:

1. **Given** sự kiện đến lệch trong khoảng chờ, **When** đủ chốt, **Then** xét theo thời gian nguồn và tiếp tục chốt khi nguồn im lặng nếu an toàn.
2. **Given** dữ liệu trễ còn ảnh hưởng vùng do handler xác định, **When** hiệu chỉnh, **Then** nạp đủ ngữ cảnh và dựng lại đúng nhóm trên trạng thái tạm, không phát tác động trung gian.
3. **Given** thiếu căn cứ hoặc ngoài phạm vi, **When** đánh giá, **Then** giữ dữ liệu cùng lý do/độ đầy đủ, không đoán kết quả.
4. **Given** bằng chứng/kết luận thay đổi có ý nghĩa, **When** ghi, **Then** giữ phiên bản và audit; bản đã đóng bất biến theo 002.

### User Story 8 - Dọn chung theo chính sách từng rule (Priority: P2)

Người vận hành muốn thu hồi dữ liệu nóng an toàn mà không phải tạo bộ dọn riêng theo rule hoặc đối tượng.

**Why this priority**: Dọn sai có thể mất bằng chứng hoặc thay kết quả sau nạp lại.

**Independent Test**: Cho các handler có chính sách giữ dữ liệu khác nhau; thử hết hạn, checkpoint lỗi, pending và cập nhật trong lúc dọn.

**Acceptance Scenarios**:

1. **Given** dữ liệu còn cần cho thuật toán, **When** chưa đủ điều kiện phát sinh, **Then** không xóa chỉ vì chưa có cảnh báo.
2. **Given** handler cho phép và không pending/in-flight/cảnh báo active, đủ idle/checkpoint và điều kiện cold-load an toàn, **When** dọn, **Then** được thu hồi cache, không xóa dữ liệu bền vững.
3. **Given** lỗi lưu hoặc cập nhật mới, **When** chuẩn bị thu hồi, **Then** hủy quyết định cũ.
4. **Given** nhóm có dữ liệu sau thu hồi, **When** nạp lại, **Then** khôi phục ngữ cảnh và không áp dụng hai lần cùng sự kiện.
5. **Given** nhiều loại rule, **When** bộ dọn chung chạy, **Then** gọi chính sách từng handler và áp guard an toàn chung.

### User Story 9 - Thêm handler theo hợp đồng có thể kiểm chứng (Priority: P1)

Người phát triển muốn triển khai một loại rule mới bằng hợp đồng thống nhất, dùng lại cơ chế điều phối, lưu trạng thái, thời gian và dọn dữ liệu.

**Why this priority**: Hành vi không thống nhất giữa các rule làm sai khôi phục và vòng đời.

**Independent Test**: Kiểm tra một handler có nhiều nhóm, xử lý sự kiện/thời gian/dọn state, serialize–restore và dựng lại không phát side effect.

**Acceptance Scenarios**:

1. **Given** handler khai báo metadata, **When** đăng ký, **Then** kiểm tra được khả năng nhận sự kiện, tham số, khóa nhóm, cấu trúc state và kết quả hỗ trợ.
2. **Given** sự kiện không đổi kết luận, **When** handler đánh giá, **Then** vẫn cập nhật state cần thiết và xét điều kiện liên quan, không bỏ toàn bộ lượt vì kết luận chưa đổi.
3. **Given** điều kiện kết thúc phụ thuộc khoảng yên, **When** thời gian đủ và dữ liệu an toàn, **Then** bộ lập lịch chung đánh giá dù không có log mới; các outcome đã khai báo được giữ đúng.
4. **Given** handler dọn dữ liệu hoặc cho phép thu hồi, **When** áp dụng, **Then** engine vẫn bảo vệ checkpoint, baseline, công việc đang chạy và trạng thái cảnh báo hiện hành.
5. **Given** dựng lại để tính bù hoặc lỗi sau đánh giá, **When** chưa commit, **Then** handler không gửi thông báo/ghi DB và không sửa cache đã commit.

### User Story 10 - Nhận việc và thử lại có kiểm soát (Priority: P1)

Người vận hành muốn kết quả có thể tiếp tục và kiểm chứng được khi các module trao đổi dữ liệu hoặc gặp gián đoạn.

**Why this priority**: Thiếu hợp đồng vận hành có thể làm bỏ việc hoặc thay đổi kết luận cảnh báo.

**Independent Test**: Mô phỏng không có việc, backlog nhiều batch, lỗi tạm và failed qua restart.

**Acceptance Scenarios**:

1. **Given** sự kiện chuẩn hóa đã lưu sẵn sàng, **When** worker hoạt động, **Then** chủ động lấy việc mà không cần module chuẩn hóa gọi trực tiếp từng rule.
2. **Given** batch chưa đủ giới hạn hoặc chỉ có timer, **When** có việc sẵn sàng, **Then** không đợi đầy batch hoặc bỏ đói deadline.
3. **Given** lỗi tạm hoặc failed chưa giải quyết, **When** thử lại/khởi động lại, **Then** không bỏ barrier hoặc ghi hoàn tất thiếu kết quả; thao tác phục hồi có audit.

### User Story 11 - Chặn kết thúc khi thiếu quan sát (Priority: P1)

Người vận hành muốn kết quả có thể tiếp tục và kiểm chứng được khi các module trao đổi dữ liệu hoặc gặp gián đoạn.

**Why this priority**: Thiếu hợp đồng vận hành có thể làm bỏ việc hoặc thay đổi kết luận cảnh báo.

**Independent Test**: Giữ log trước deadline chưa chuẩn hóa, clock mâu thuẫn và mất quan sát rồi khôi phục.

**Acceptance Scenarios**:

1. **Given** còn dữ liệu liên quan chưa xét trước deadline, **When** timer đến, **Then** chưa kết luận khoảng yên.
2. **Given** mất khả năng quan sát từ 30 đến 100 và quiet 60, **When** healthy từ 100, **Then** sớm nhất kết thúc tại 160 nếu không dựng lại được khoảng mất.
3. **Given** chỉ worker gián đoạn nhưng dữ liệu và coverage còn đủ, **When** dựng lại, **Then** xét event/deadline theo nguồn mà không giả định khoảng trống mới.

### User Story 12 - Đổi revision và giới hạn cache an toàn (Priority: P1)

Người vận hành muốn kết quả có thể tiếp tục và kiểm chứng được khi các module trao đổi dữ liệu hoặc gặp gián đoạn.

**Why this priority**: Thiếu hợp đồng vận hành có thể làm bỏ việc hoặc thay đổi kết luận cảnh báo.

**Independent Test**: Bật revision mới, cold-load recovered, chạm ngân sách và yêu cầu bổ sung lịch sử.

**Acceptance Scenarios**:

1. **Given** alert cũ chưa đóng, **When** bật revision mới, **Then** nhóm giữ owner cũ và không có alert song song cùng rule logic.
2. **Given** state recovered đã thu hồi, **When** xử lý lại, **Then** đọc vòng đời hiện hành và giữ ranh giới; active còn trong cache.
3. **Given** thiếu lịch sử hoặc chạm hạn mức, **When** đánh giá, **Then** nạp ngữ cảnh có giới hạn hoặc báo thiếu/suy giảm, không đoán kết quả hay bỏ dữ liệu.

### Edge Cases

- Trùng tên đối tượng giữa thiết bị; cùng đối tượng khác revision hoặc scope.
- Thiếu trường, alias chưa xác minh; đăng ký nhiều selector gây gọi lặp hoặc bỏ log phục hồi.
- Timestamp bằng nhau mâu thuẫn, thiếu thời gian hoặc quá tương lai; không dùng thứ tự nhận để đoán.
- Tối ưu bộ đệm dẫn xuất làm mất ngữ cảnh hiệu chỉnh/khôi phục.
- Thu hồi khi còn dữ liệu cần thiết/pending/in-flight/alert active; recovered chưa đóng chỉ được thu hồi nếu cold-load an toàn.
- Hai worker cùng sở hữu nhóm; rollback/crash; event id nhỏ commit muộn.
- Revision cũ còn cảnh báo, code/schema cần restore bị thiếu, rule tắt tạo nhóm mới.
- Deadline trước event trong backlog phải xét trước; cùng mốc event đủ chốt phải xét trước timer.
- Quy tắc ngưỡng/cửa sổ/kết thúc cụ thể của LinkFlap thuộc feature 004, không là mặc định cho mọi rule.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Mỗi rule MUST tách logic thực thi và cấu hình; thay thông số trong khả năng đã hỗ trợ MUST không cần tạo cấu trúc lưu riêng cho loại rule đó.
- **FR-002**: Cấu hình MUST có định danh/phiên bản, tham chiếu phiên bản logic, đăng ký sự kiện, thông tin nhóm, tham số và điều kiện phục hồi; MUST được kiểm tra trước áp dụng.
- **FR-003**: Tham số MUST đúng kiểu, giới hạn, trường bắt buộc và khả năng thực thi; cấu hình không hỗ trợ hoặc thay nội dung mà giữ nguyên phiên bản MUST bị từ chối.
- **FR-004**: Một nguồn biên soạn cấu hình MUST được xác định; các bản công bố dùng cho lịch sử MUST bất biến và không trở thành nguồn chỉnh sửa song song.
- **FR-005**: Người giám sát MUST chỉ xem thông tin rule và thao tác vòng đời được cấp quyền; giao diện đăng ký hoặc chỉnh sửa rule không thuộc phạm vi bản đầu.
- **FR-006**: Điều phối MUST dựa trên loại sự kiện chuẩn hóa và phạm vi đã đăng ký; cùng hiện tượng được hỗ trợ ở các hãng MUST không đòi người giám sát chọn mẫu raw theo hãng.
- **FR-007**: Một sự kiện MUST đến mọi rule liên quan và mỗi phiên bản MUST được gọi nhiều nhất một lần trong cùng lượt đánh giá.
- **FR-008**: Điều phối MUST bao gồm cả điều kiện phát sinh và phục hồi; phiên bản ngừng tạo mới nhưng còn cảnh báo chưa đóng MUST tiếp tục nhận sự kiện cho nhóm đang theo dõi.
- **FR-009**: Sự kiện thiếu trường cho một rule MUST chỉ bị loại khỏi rule đó với lý do; bản gốc vẫn lưu và các rule đủ điều kiện khác vẫn có thể được xét.
- **FR-010**: Trạng thái MUST độc lập theo định danh rule, phiên bản cấu hình/logic, ngữ cảnh và khóa đối tượng; interface phải phân biệt bằng cả thiết bị và tên interface đã chuẩn hóa.
- **FR-011**: Không được đồng nhất một rule với một interface; cách thực thi MUST dùng chung logic và quản lý riêng dữ liệu nhóm, không yêu cầu tài nguyên thực thi riêng cho từng interface.
- **FR-012**: Mỗi handler MUST khai báo và thực hiện điều kiện phát sinh/kết thúc riêng; engine không áp một thuật toán đếm mặc định cho mọi rule. LinkFlap được đặc tả tại feature 004.
- **FR-013**: Các lớp tín hiệu/thuộc tính cần để tách nghĩa MUST được kiểm tra theo handler; không tự gộp đối tượng hoặc alias chưa xác minh.
- **FR-014**: Ngữ nghĩa biên, ranh giới chu kỳ và dữ liệu có thể tái sử dụng MUST được quy định/kiểm chứng cho từng handler, tuân theo vòng đời chung của 002.
- **FR-015**: Tối ưu dữ liệu dẫn xuất có giới hạn MUST giữ hoặc khôi phục được ngữ cảnh cần cho tính bù; không đồng nhất kích thước bộ đệm với toàn trạng thái hoặc số đếm tổng.
- **FR-016**: Hệ thống MUST tạo dữ liệu nhóm khi cần và dọn lịch sử đếm hết hạn, nhưng MUST giữ/khôi phục được trạng thái gần nhất, ranh giới chu kỳ và cảnh báo còn cần theo dõi.
- **FR-017**: Rule MUST chỉ đưa ra kết luận và bằng chứng; việc ghi/tạo/cập nhật cảnh báo, tín hiệu và xác nhận MUST tuân theo một cơ chế vòng đời chung của feature 002.
- **FR-018**: Bản đầu MUST có một luồng sở hữu trạng thái tương quan; cùng khóa nhóm MUST được cập nhật tuần tự, không chạy nhiều bản độc lập làm trộn hoặc nhân đôi kết quả.
- **FR-019**: Sự kiện đầu vào, tiến độ, trạng thái cần khôi phục, kết quả và bằng chứng MUST được lưu bền vững; hàng chờ tạm MUST không là nguồn duy nhất.
- **FR-020**: Trạng thái mới, cảnh báo, bằng chứng, lịch sử và ghi nhận xử lý của cùng lượt MUST cùng có hiệu lực hoặc cùng không có hiệu lực; bộ nhớ MUST không đi trước kết quả lưu thành công.
- **FR-021**: Khởi động lại MUST khôi phục trạng thái và các phiên bản cần dùng trước khi tiếp tục; không được coi chỉ đọc lại một cửa sổ ngắn là đủ cho mọi rule trạng thái dài hạn.
- **FR-022**: Xử lý lại cùng định danh MUST không đếm, tạo cảnh báo hoặc ghi lịch sử hai lần. Việc nhận lại raw với định danh mới không tự được coi là cùng sự kiện.
- **FR-023**: Lỗi dữ liệu có thể giải thích MUST được phân biệt với lỗi logic nghiêm trọng; lỗi nghiêm trọng MUST giữ tiến độ chưa hoàn tất, báo sức khỏe suy giảm và không âm thầm bỏ rule rồi báo hoàn tất.
- **FR-024**: Bản đầu dùng giao dịch chung cho các rule của một lượt; cách ly lỗi và thử lại độc lập từng rule là bước mở rộng, MUST không được tuyên bố đã có trong thiết kế đơn giản này.
- **FR-025**: Log có thứ tự thời gian đáng tin cậy đến trễ MUST được sắp lại/tính bù trong phạm vi liên quan; dữ liệu mâu thuẫn thời gian MUST được đánh dấu, không dùng thứ tự nhận để đoán. Cảnh báo đã đóng không được sửa hoặc mở lại âm thầm.
- **FR-026**: Hệ thống MUST quan sát được tốc độ nhận/xét, số rule ứng viên, nhóm đang theo dõi, tồn đọng, lỗi, độ trễ và tài nguyên; quá tải MUST không làm mất âm thầm sự kiện đã lưu.
- **FR-027**: Dữ liệu lịch sử MUST có ngữ cảnh riêng và mặc định chỉ tra cứu; phát lại chủ động MUST không trộn trạng thái với luồng trực tiếp.
- **FR-028**: Rule thiếu điều kiện phục hồi hợp lệ MUST không được bật tự động đầy đủ; ví dụ cấu hình tắt không được quảng bá như rule đã sẵn sàng vận hành.
- **FR-029**: Cùng khóa MUST tiếp tục được xử lý tuần tự khi mở rộng năng lực; tăng số bản điều phối MUST không tạo đăng ký hoặc kết quả trùng, và chỉ thực hiện sau đo nút thắt.
- **FR-030**: Ước lượng RAM/CPU từ mô phỏng cửa sổ MUST được phân biệt với tài nguyên toàn module, lưu trữ và hiệu năng đã đo thực tế; mọi tiêu chí độ trễ đề xuất MUST được ghi rõ chưa phê duyệt.

- **FR-031**: Sự kiện không làm đổi kết luận MUST vẫn được xét để cập nhật state và điều kiện có liên quan; không bỏ toàn bộ lượt chỉ vì kết quả chưa đổi.
- **FR-032**: Hệ thống MUST dùng khoảng chờ sắp thứ tự 3 giây và mốc chốt thời gian nguồn có căn cứ; mốc phải tiến khi im lặng nếu pipeline/đồng hồ an toàn, không vượt việc đã biết chưa xử lý.
- **FR-033**: Log quá khoảng chờ MUST được kiểm tra theo vùng ảnh hưởng do handler quy định, nạp thêm lịch sử cần thiết và xét mọi kết luận bị ảnh hưởng; không mặc định một horizon cố định cho mọi rule.
- **FR-034**: Tính bù MUST phân biệt phát hiện muộn, hiệu chỉnh bằng chứng và ngoài phạm vi; có audit/idempotency, không tự xóa/đóng cảnh báo vì bộ đếm thay đổi.
- **FR-035**: Log không còn ảnh hưởng phạm vi tính bù hoặc không đủ dữ liệu để chứng minh MUST được giữ với lý do/độ đầy đủ, không báo như đã khôi phục chính xác toàn lịch sử.
- **FR-036**: Điều kiện thời gian của handler MUST chỉ được kết luận khi mốc chốt và an toàn dữ liệu đủ; không suy phục hồi từ im lặng ngoài chính sách đã khai báo.
- **FR-037**: Kết luận của một rule MUST không tự tạo/chỉ đạo rule khác; sự kiện có thể độc lập thỏa nhiều rule qua cơ chế điều phối.
- **FR-038**: Mốc cần đánh giá tiếp MUST dùng thời gian nguồn. Khoảng chờ 3 giây được áp một lần ở engine, không cộng lặp trong rule.
- **FR-039**: Dọn dữ liệu hết hạn và thu hồi toàn bộ cache MUST là hai thao tác riêng; chưa đạt ngưỡng không đủ lý do xóa dữ liệu còn cần.
- **FR-040**: Thu hồi cache MUST yêu cầu không còn dữ liệu thuật toán cần giữ nóng, log chờ, việc đang chạy hoặc cảnh báo active; recovered chưa đóng được thu hồi khi đủ idle/checkpoint/ngữ cảnh và không deadline cần giữ nóng. Cập nhật mới phải hủy quyết định cũ; eviction không đổi vòng đời.
- **FR-041**: Bản đầu MUST dùng một bộ dọn chung với chính sách riêng của rule; chu kỳ dọn 5 giây và idle 60 giây là mặc định đề xuất, không phải tham số phát sinh hoặc kết thúc của rule.
- **FR-042**: Sau thu hồi, state MUST được nạp lại với baseline/quan sát cần thiết; dựng lại không được cộng hai lần dữ liệu hoặc coi log pending là đã áp dụng.
- **FR-043**: Handler MUST khai báo phiên bản, khả năng, field/khóa nhóm, schema tham số/state và các outcome được hỗ trợ; schema gồm cả kiểm tra liên trường khi cần.
- **FR-044**: Hợp đồng handler MUST hỗ trợ khởi tạo, đánh giá sự kiện, đánh giá theo thời gian, đề xuất dọn và cho phép thu hồi; mặc định phải an toàn nếu rule chưa hỗ trợ thao tác tùy chọn.
- **FR-045**: Handler MUST nhận snapshot/context chỉ đọc và trả state/kết luận/bằng chứng/lý do/mốc hiệu lực/lịch tiếp theo; không tự ghi dữ liệu, gửi thông báo, tạo timer hoặc đổi xác nhận người giám sát.
- **FR-046**: Phục hồi theo khoảng yên MUST tham chiếu bằng chứng gốc và mốc đánh giá, không tạo syslog giả hoặc gọi mốc hết thời gian là một log thiết bị mới.
- **FR-047**: Hiệu chỉnh có ý nghĩa MUST có phiên bản và dấu vết trước/sau; lỗi hoặc mâu thuẫn chưa đủ kết luận phải được đánh dấu cần xem xét thay vì xóa cảnh báo.
- **FR-048**: Engine MUST trộn sự kiện và lịch theo thứ tự nguồn: deadline trước một event được xét trước event đó; tại cùng mốc, mọi event đủ chốt được xét trước timer. Công việc hẹn state cũ không tạo kết luận lỗi; không dồn timer về cuối batch làm mất khoảng yên.

- **FR-049**: Worker MUST chủ động nhận dữ liệu sẵn sàng từ nguồn bền vững, chờ có giới hạn khi rỗng và tiếp tục nhận backlog mà không phụ thuộc lời gọi trực tiếp từ module chuẩn hóa.
- **FR-050**: Việc lấy sự kiện, xét deadline và dọn cache MUST được điều phối để một loại công việc không làm bỏ đói loại khác; chỉ đánh dấu hoàn tất khi đủ điều kiện.
- **FR-051**: Lỗi tạm MUST rollback và được thử lại giới hạn; lỗi logic hoặc hết thử lại MUST dừng tiến độ, giữ việc chưa hoàn tất và hiển thị lỗi.
- **FR-052**: Sự kiện failed MUST chặn tiến độ liên quan cả sau restart; đưa lại chờ phải có quyền, lý do, dấu vết và giữ định danh/phiên bản, không tự bỏ qua.
- **FR-053**: Quyền sở hữu nhóm MUST duy nhất và mất quyền MUST ngừng xử lý; dừng có kiểm soát không được tạo kết quả dở hoặc làm mất việc.
- **FR-054**: Suy luận khoảng yên MUST có bằng chứng sức khỏe/coverage và đã xử lý đủ đầu vào liên quan trước deadline; không chỉ dựa vào thời gian hiện tại.
- **FR-055**: Khoảng mất quan sát MUST bị loại khỏi khoảng yên; chỉ dùng lại lịch sử nếu có coverage liên tục chứng minh được, nếu không phải quan sát an toàn lại.
- **FR-056**: Cùng rule logic, nhóm và ngữ cảnh có cảnh báo chưa đóng MUST giữ owner revision cũ; revision mới chỉ nhận nhóm chưa ghim, không tạo cảnh báo song song.
- **FR-057**: Phiên bản mới MUST có mốc kích hoạt; bằng chứng phát sinh trước mốc không tự góp ngưỡng mới, baseline vẫn có thể được tham khảo. Đổi khóa nhóm khi còn cảnh báo cũ phải được chặn hoặc có chuyển đổi riêng được phê duyệt.
- **FR-058**: Handler MUST khai báo ngữ cảnh lịch sử cần thiết; engine cung cấp ngữ cảnh và độ đầy đủ. Thiếu ngữ cảnh phải được nạp thêm có giới hạn hoặc ghi chưa đủ, không tạo kết luận đoán.
- **FR-059**: Giới hạn nhóm/cache/buffer/state/tính bù MUST được kiểm tra trước nhận việc; chạm giới hạn phải ưu tiên dọn hợp lệ rồi giữ việc bền vững và báo suy giảm.
- **FR-060**: Cold-load recovered chưa đóng MUST tìm đúng owner và vòng đời hiện hành; không tin workflow trong checkpoint, không mất baseline/ranh giới hoặc nhân đôi dữ liệu.
- **FR-061**: Hiển thị MUST lấy dữ liệu đã có hiệu lực qua hợp đồng tích hợp; bản đầu không yêu cầu handler gửi trực tiếp hoặc bảo đảm truyền từng thông báo tức thời.
- **FR-062**: Hợp đồng sự kiện, kết quả, state và lịch sử MUST có schema rõ ràng, được kiểm tra khi trao đổi/lưu/nạp; phiên bản không tương thích phải báo lỗi hoặc chuyển đổi có kiểm soát.

### Key Entities *(include if feature involves data)*

- **Định nghĩa rule và phiên bản logic**: Cấu hình bất biến cùng phần thực thi có định danh phiên bản, khả năng và cấu trúc tham số hỗ trợ.
- **Danh mục đăng ký**: Ánh xạ loại sự kiện sang tập phiên bản có thể nhận, gồm rule bật và phiên bản cũ còn nhóm cần theo dõi.
- **Sự kiện chuẩn hóa**: Định danh, loại, thời gian có căn cứ, thiết bị, thuộc tính đối tượng, lớp tín hiệu và ngữ cảnh nguồn.
- **Trạng thái nhóm**: Quan sát gần nhất, lịch sử đếm cần thiết, ranh giới chu kỳ và phiên bản dữ liệu; độc lập với xác nhận người giám sát.
- **Kết luận rule**: Phát sinh, bổ sung, phục hồi hoặc chưa đổi, cùng bằng chứng; không trực tiếp thay xác nhận/đóng.
- **Checkpoint và tiến độ**: Bản trạng thái đã lưu nhất quán với tập sự kiện thực sự hoàn tất để tiếp tục sau gián đoạn.
- **Cảnh báo/bằng chứng/lịch sử**: Các thực thể của feature 001/002, giữ nguyên nguyên tắc truy vết và vòng đời.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Với ít nhất 20 trường hợp định nghĩa hợp lệ/không hợp lệ, 100% được áp dụng hoặc từ chối đúng mong đợi, không có trường hợp nạp một phần cấu hình lỗi.
- **SC-002**: Với bộ ít nhất 100 sự kiện và 5 rule đăng ký khác nhau, tập rule nhận từng sự kiện đúng 100%, không bỏ log phục hồi hoặc gọi trùng cùng phiên bản.
- **SC-003**: Với 1.000 đối tượng có tên trùng giữa thiết bị, 100% kết quả/bằng chứng đúng nhóm và revision/scope; trường thiếu không tạo nhóm dùng chung giả.
- **SC-004**: Bộ thử tài nguyên đối chiếu được dữ liệu giữ lại theo chính sách của từng handler và đo riêng toàn trạng thái, tồn đọng và khôi phục; không lấy giới hạn bộ đệm làm ngân sách toàn hệ thống.
- **SC-005**: Trên kịch bản tải riêng của feature 004, đối chiếu đủ 100% đầu vào/kết quả, đo cả tải đều và tải dồn với nhiều mức số rule ứng viên; không báo hoàn tất khi bỏ dữ liệu.
- **SC-006**: Đo riêng received→đủ chốt và đủ chốt→hiển thị. Mục tiêu lab đề xuất cho đoạn sau là p95 2 giây/p99 5 giây trên tải SC-005; tổng độ trễ có thêm đệm 3 giây và tồn đọng, chưa là SLA được chốt.
- **SC-007**: Ở ba điểm dừng trước commit, sau commit trước cập nhật bộ nhớ và khi state ở ngoài cache, 100% tình huống khôi phục đúng cửa sổ/cảnh báo; thử lại mỗi định danh 10 lần không nhân đôi kết quả.
- **SC-008**: 100% chuyển trạng thái của bộ tích hợp tuân theo feature 002; phục hồi không tự ACK/CLOSE, bản đã đóng bất biến và các đợt replay không ảnh hưởng live.
- **SC-009**: Mọi trường hợp lỗi logic/quá tải của bộ thử đều nhìn thấy được qua sức khỏe, lỗi và tồn đọng; không có sự kiện đã lưu bị báo hoàn tất khi bỏ sót rule vì lỗi thực thi.

- **SC-010**: 100% bộ log trễ và lịch theo thời gian cho kết quả đúng hoặc lý do thiếu căn cứ rõ ràng; giữ thời gian hiệu lực khác thời gian phát hiện và không sửa cảnh báo đã đóng.
- **SC-011**: Bộ dọn/khôi phục đạt đúng mọi trường hợp dữ liệu còn cần, hết hạn, checkpoint lỗi, cập nhật đồng thời và dữ liệu sau eviction; không mất dữ liệu bền vững.
- **SC-012**: Cả 5 thao tác của handler được kiểm chứng với state nhiều nhóm, snapshot không bị sửa, serialize–restore tương đương, timer lặp an toàn và dựng lại không có side effect trung gian.

- **SC-013**: Toàn bộ ca worker rỗng, backlog nhiều batch, failed qua restart, retry và dừng/khởi động lại cho đúng tập sự kiện hoàn tất, không nhân đôi và không bỏ barrier.
- **SC-014**: 100% ca backlog trước deadline, nguồn/time không an toàn và khoảng mất quan sát chặn kết thúc sai; case mất 30–100/quiet 60 không kết thúc trước 160 nếu chưa dựng lại đủ.
- **SC-015**: Trong bộ đổi revision/cold-load/giới hạn tài nguyên, 100% giữ một owner, đúng vòng đời/ranh giới và không mất dữ liệu đã lưu.
- **SC-016**: Bộ yêu cầu lịch sử đủ/thiếu/vượt giới hạn/không tiến triển đều kết thúc hữu hạn, có độ đầy đủ rõ; không áp dụng state/kết quả tạm chưa đủ căn cứ.

## Assumptions

- Đây là thiết kế đề xuất cho giám sát qua syslog, chưa triển khai/kiểm chuẩn; không cấu hình hoặc khắc phục thiết bị.
- Một Dispatcher logic và một worker tương quan tách khỏi xử lý yêu cầu giao diện; không tạo bộ riêng theo hãng/interface/rule.
- Người phát triển quản lý logic và file cấu hình phiên bản; người giám sát chỉ xem rule và dùng quyền vòng đời. Chưa có giao diện sửa rule.
- Khoảng chờ sắp thứ tự 3 giây là lựa chọn hiện tại ở engine, áp một lần. Ngưỡng, cửa sổ, horizon, outcome và điều kiện kết thúc LinkFlap chuyển sang [feature 004](../004-link-flap-rule/spec.md).
- Checkpoint ghi cùng kết quả theo batch nhỏ có giới hạn chờ; chi phí lưu/khôi phục phải đo đầy đủ.
- Lỗi logic nghiêm trọng dừng tiến độ worker để sửa/thử lại, đầu vào vẫn được thu/lưu. Cách ly lỗi độc lập từng rule là bước mở rộng.
- Mục tiêu post-chốt ở SC-006, chu kỳ dọn 5 giây và idle 60 giây là đề xuất để review, chưa phê duyệt nghiệm thu.
- Tính bù theo phạm vi handler với audit, không mặc định tái dựng mọi lịch sử; không thêm trạng thái hủy hoặc sửa bản closed.
- Nhận việc polling, giới hạn batch/retry và ngân sách có giá trị thử trong thiết kế; không phải SLA đã đo. Health/coverage và API/frontend theo [005](../005-monitoring-integration/spec.md). Eviction theo constitution 2.0.0.
- Phụ thuộc: hợp đồng sự kiện chuẩn hóa, nhận diện đối tượng/lớp tín hiệu, phiên bản logic còn truy xuất được và dữ liệu/vòng đời 001/002.
- [engine-design.md](engine-design.md) diễn giải kiến trúc, hợp đồng, checkpoint và chính sách chung. [Thiết kế LinkFlap](../004-link-flap-rule/link-flap-design.md) sở hữu thuật toán và mô hình tài nguyên riêng. Không tạo worker, migration hoặc giao diện ở bước này.
