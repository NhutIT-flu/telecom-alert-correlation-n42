# Feature Specification: Vòng đời cảnh báo giám sát bằng syslog

**Feature Branch**: Không tạo nhánh trong lần đặc tả này.

**Created**: 2026-11-19

**Status**: Draft — bản đề xuất hoàn chỉnh để người dùng xem xét, chưa triển khai.

**Tích hợp module**: [Feature 003](../003-rule-dispatch-correlation/spec.md) làm rõ điều phối, phiên bản logic/cấu hình và checkpoint. Feature 002 vẫn là nguồn chuẩn của vòng đời; rule không trực tiếp ACK/CLOSE. Các mốc độ trễ đề xuất trong 003 chưa được coi là SLA đã phê duyệt.

**Updated**: 2026-11-20 — bổ sung khoảng quan sát an toàn, owner revision và cold-load recovered chưa đóng; thao tác người qua hợp đồng 005.

**Input**: User description: "Thiết kế hoàn chỉnh phần trạng thái cảnh báo. Hệ thống chỉ giám sát thông qua syslog nhận được; người giám sát xác nhận đã thấy và xác nhận kết thúc; hệ thống nhận diện kết thúc theo điều kiện của rule. Không bao gồm xử lý hay cấu hình thiết bị."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Nhận biết bất thường và phục hồi qua syslog (Priority: P1)

Người giám sát muốn biết cảnh báo mới phát sinh hoặc đã có bằng chứng phục hồi, đồng thời hiểu đó là kết luận từ syslog đã nhận.

**Why this priority**: Đó là chức năng giám sát cốt lõi; thiếu bằng chứng không được hiển thị như đã bình thường.

**Independent Test**: Phát lại các tình huống phát sinh, phục hồi, sai đối tượng, thiếu bằng chứng và không có log mới với kết quả mong đợi đã ghi trước.

**Acceptance Scenarios**:

1. **Given** chưa có cảnh báo chưa đóng cùng rule/nhóm/ngữ cảnh, **When** syslog đủ điều kiện phát sinh, **Then** tạo cảnh báo mới, tín hiệu đang bất thường và chưa được xác nhận.
2. **Given** cảnh báo chưa đóng, **When** bằng chứng/điều kiện thời gian khai báo của đúng phiên bản rule thỏa với mốc chốt an toàn, **Then** ghi nhận kết thúc điều kiện, giữ xác nhận của người giám sát và truy được căn cứ.
3. **Given** nhóm cảnh báo có nhiều đối tượng đang bất thường, **When** mới một đối tượng có bằng chứng phục hồi, **Then** chưa ghi nhận cả nhóm phục hồi; mặc định cần đủ mọi đối tượng còn bất thường.
4. **Given** không có log mới, **When** rule không khai báo điều kiện theo khoảng yên hoặc pipeline/time chưa an toàn, **Then** không tự phục hồi/đóng; rule có khai báo có thể kết thúc điều kiện qua timer an toàn, không tự closed.
5. **Given** cảnh báo của phiên bản rule cũ chưa đóng, **When** bật phiên bản mới hoặc tắt rule cho cảnh báo mới, **Then** cảnh báo cũ vẫn xét vòng đời theo phiên bản đã tạo nó.

### User Story 2 - Xác nhận đã thấy và xác nhận đóng (Priority: P1)

Người giám sát muốn ghi nhận đã thấy cảnh báo và đóng khi đã có bằng chứng kết thúc, mà không thực hiện thao tác lên thiết bị.

**Why this priority**: Phân biệt sự kiện đã được nhìn thấy với việc tín hiệu đã phục hồi, tránh bỏ sót hoặc đóng nhầm.

**Independent Test**: Thử xác nhận/đóng ở từng tổ hợp trạng thái hợp lệ và đối chiếu người thực hiện, thời điểm, kết quả và lịch sử.

**Acceptance Scenarios**:

1. **Given** cảnh báo chưa được xác nhận, **When** người có quyền xác nhận đã thấy, **Then** ghi người/thời điểm xác nhận, giữ nguyên trạng thái tín hiệu; xác nhận lặp không ghi đè người đầu tiên.
2. **Given** cảnh báo tự phục hồi trước khi được nhìn thấy, **When** người giám sát xem danh sách, **Then** thấy đồng thời đã ghi nhận phục hồi và chưa xác nhận.
3. **Given** cảnh báo đã phục hồi nhưng chưa xác nhận, **When** người có quyền chọn xác nhận và đóng, **Then** ghi cả hai bước với cùng người/thời điểm, cùng thành công hoặc cùng không có hiệu lực.
4. **Given** cảnh báo đã phục hồi và đã xác nhận, **When** người có quyền đóng, **Then** ghi trạng thái đóng cùng người/thời điểm, không thay đổi bằng chứng phục hồi.
5. **Given** tín hiệu còn bất thường hoặc người thao tác không có quyền, **When** yêu cầu đóng, **Then** không thay đổi trạng thái và giải thích lý do.
6. **Given** cảnh báo đã đóng, **When** yêu cầu xác nhận/đóng được gửi lại bởi người có quyền, **Then** trả trạng thái hiện tại mà không tạo lịch sử mới hoặc thay người/thời điểm đã ghi.

### User Story 3 - Theo dõi tái xuất hiện và xử lý log đến trễ (Priority: P1)

Người giám sát muốn bất thường tái xuất hiện được thể hiện đúng mà log cũ không làm cảnh báo mới biến mất hoặc tự mở lại cảnh báo đã đóng.

**Why this priority**: Log có thể đến lệch thứ tự; kết luận sai trạng thái gây hiểu nhầm trực tiếp trong giám sát.

**Independent Test**: Phát các chuỗi log theo cả thứ tự thời gian và thứ tự nhận khác nhau, gồm log trùng, timestamp bằng nhau và log thiếu thời gian.

**Acceptance Scenarios**:

1. **Given** cảnh báo đã phục hồi nhưng chưa đóng, **When** bằng chứng mới đủ điều kiện tái phát sinh, **Then** cùng cảnh báo trở về bất thường, giữ xác nhận trước đó và lưu lần tái xuất hiện.
2. **Given** cảnh báo đã đóng, **When** chuỗi bằng chứng mới sau ranh giới phục hồi của lần trước đủ điều kiện phát sinh, **Then** tạo cảnh báo mới với định danh mới, chưa xác nhận; cảnh báo cũ không đổi.
3. **Given** đang có bằng chứng bất thường lúc T2, **When** log cũ đến sau, **Then** xét ảnh hưởng và tính bù trong vùng cho phép; không ghi đè tín hiệu chỉ bằng một log cũ hoặc sửa alert closed.
4. **Given** cảnh báo cũ đã đóng, **When** log trễ thuộc trước hoặc đúng ranh giới phục hồi cuối của lần cũ đến, **Then** lưu log nhưng không tạo lần cảnh báo mới từ log cũ đó.
5. **Given** bằng chứng bất thường và phục hồi không có thứ tự đáng tin cậy hoặc cùng timestamp mâu thuẫn, **When** đánh giá, **Then** không dùng bằng chứng đó để kết luận phục hồi; ưu tiên bảo thủ ở trạng thái bất thường đối với cảnh báo chưa đóng.
6. **Given** thời gian thiếu căn cứ, **When** nhận log, **Then** giữ để tra cứu, không dùng thứ tự nhận để tự kết luận chuyển trạng thái tín hiệu.

### User Story 4 - Lịch sử nhất quán và thao tác đồng thời (Priority: P2)

Người giám sát muốn truy được ai hoặc log nào đã làm đổi trạng thái; thao tác đồng thời và thử lại không làm sai lịch sử.

**Why this priority**: Cần giải thích được kết luận và tiếp tục an toàn sau gián đoạn.

**Independent Test**: Mô phỏng xác nhận đồng thời, đóng đua với tái phát sinh và gián đoạn giữa ghi trạng thái/lịch sử/bằng chứng.

**Acceptance Scenarios**:

1. **Given** hai người cùng xác nhận, **When** cả hai yêu cầu được xử lý, **Then** chỉ có một lần chuyển, giữ người ghi thành công đầu tiên.
2. **Given** người giám sát đang xem cảnh báo đã phục hồi, **When** hệ thống đã ghi nhận tái xuất hiện trước khi thao tác đóng được ghi, **Then** thao tác trên phiên bản cũ bị từ chối và hiển thị trạng thái mới.
3. **Given** một lần chuyển có bằng chứng, **When** lỗi xảy ra giữa các bước lưu, **Then** không có trạng thái mới thiếu lịch sử/bằng chứng; thử lại không nhân đôi cùng lần chuyển.
4. **Given** yêu cầu xem lịch sử, **When** truy xuất, **Then** thấy trước/sau, chủ thể, thời gian ghi/mốc hiệu lực, nguồn quyết định syslog/timer/correction/operator và bằng chứng thật, kể cả hiệu chỉnh có ý nghĩa không đổi cặp trạng thái.
5. **Given** cùng định danh syslog đã được xét, **When** đánh giá lại, **Then** không tạo thêm lần chuyển trạng thái giống nhau.

### User Story 5 - Lọc đúng trạng thái để giám sát (Priority: P2)

Người giám sát muốn lọc độc lập tín hiệu bất thường/phục hồi và việc đã thấy/chưa thấy/đã đóng.

**Why this priority**: Cảnh báo đã phục hồi nhưng chưa ai thấy vẫn cần được nhận biết.

**Independent Test**: Chuẩn bị đủ năm tổ hợp hợp lệ và đối chiếu từng bộ lọc, số đếm và dòng lịch sử.

**Acceptance Scenarios**:

1. **Given** có cảnh báo bất thường và đã phục hồi nhưng đều chưa xác nhận, **When** lọc chưa xác nhận, **Then** trả cả hai.
2. **Given** có cảnh báo đã phục hồi chưa đóng và đã đóng, **When** lọc chờ đóng, **Then** chỉ trả nhóm đã phục hồi chưa đóng.
3. **Given** một yêu cầu đổi trạng thái bị từ chối, **When** người giám sát xem kết quả, **Then** thấy lý do và trạng thái hiện tại, không thấy thông báo thành công giả.

### User Story 6 - Giữ vòng đời khi mất quan sát hoặc state lạnh (Priority: P1)

Người vận hành muốn kết quả có thể tiếp tục và kiểm chứng được khi các module trao đổi dữ liệu hoặc gặp gián đoạn.

**Why this priority**: Thiếu hợp đồng vận hành có thể làm bỏ việc hoặc thay đổi kết luận cảnh báo.

**Independent Test**: Thử gián đoạn nguồn, CLOSE trong lúc state ngoài cache và đổi revision.

**Acceptance Scenarios**:

1. **Given** có khoảng mất quan sát chưa dựng lại được, **When** hệ thống hoạt động lại, **Then** đợi đủ khoảng quan sát an toàn trước kết luận khoảng yên.
2. **Given** cache recovered đã evict và operator đã CLOSE, **When** log mới hoặc timer đến, **Then** giữ bản closed bất biến.
3. **Given** revision mới được công bố khi alert cũ chưa đóng, **When** nhận dữ liệu nhóm đó, **Then** chỉ revision owner cũ được theo dõi cảnh báo.

### Edge Cases

- Phục hồi trước khi xác nhận: giữ cả hai thông tin, không tự coi người giám sát đã thấy.
- Không có log tự nó không chứng minh bình thường. Rule khai báo quiet period có thể kết thúc điều kiện theo quan sát khi pipeline/mốc chốt an toàn; ngữ nghĩa kết thúc từng rule thuộc đặc tả riêng, không tự suy mọi thiết bị đã bình thường.
- Nhiều log cùng nội dung nhưng khác lần nhận: không coi là cùng sự kiện chỉ dựa vào raw; việc thử lại cùng định danh không làm lặp chuyển trạng thái.
- Timestamp bằng nhau có bằng chứng mâu thuẫn: không dùng thứ tự đến hoặc id nội bộ như bằng chứng thứ tự trên thiết bị; không tự phục hồi.
- Log thiếu thời gian hoặc lệch đồng hồ không có ngữ cảnh: lưu để tra cứu, chưa đủ điều kiện đổi tín hiệu.
- Syslog phục hồi sai thiết bị/interface/peer, khác đợt phát lại hoặc khác rule: không đổi cảnh báo.
- Tắt/đổi rule: giữ phiên bản gốc cho vòng đời cảnh báo đang tồn tại; không tự đóng cảnh báo.
- Sau đóng: không sửa hay mở lại bản cũ; syslog trễ cũ không đủ điều kiện tạo bản mới.
- Đóng và tái phát sinh đồng thời: quyết định theo trạng thái/bằng chứng đã ghi tại thời điểm thao tác; không tuyên bố biết trước log chưa nhận hoặc chưa đánh giá.
- Rule không có điều kiện phục hồi rõ: chưa đủ điều kiện sử dụng đầy đủ vòng đời này; không thêm đóng cưỡng bức hoặc tự hết hạn để che thiếu sót.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Cảnh báo MUST giữ độc lập trạng thái tín hiệu và trạng thái xác nhận; MUST không có trạng thái xử lý/cấu hình/khắc phục thiết bị trong phạm vi này.
- **FR-002**: Tín hiệu MUST có hai giá trị đang bất thường và đã ghi nhận phục hồi; xác nhận MUST có ba giá trị mới, đã xác nhận và đã đóng.
- **FR-003**: Hệ thống MUST chỉ cho phép năm tổ hợp: bất thường+mới, bất thường+đã xác nhận, phục hồi+mới, phục hồi+đã xác nhận, phục hồi+đã đóng. Bất thường+đã đóng MUST bị chặn.
- **FR-004**: Khi đủ điều kiện tạo và chưa có cảnh báo chưa đóng cùng khóa, hệ thống MUST tạo định danh mới ở bất thường+mới.
- **FR-005**: Chỉ hệ thống đánh giá syslog MUST được đổi tín hiệu; chỉ người giám sát có quyền MUST được xác nhận/đóng. Danh tính người thao tác MUST được xác định từ ngữ cảnh đã xác thực, không tự khai trong yêu cầu.
- **FR-006**: Điều kiện phát sinh và phục hồi MUST được xác định theo cùng phiên bản rule, khóa đối tượng và ngữ cảnh đã tạo cảnh báo. Phiên bản gốc MUST tiếp tục dùng được đến khi cảnh báo đóng, kể cả khi ngừng tạo cảnh báo mới bằng phiên bản đó.
- **FR-007**: Mỗi lần hệ thống đổi tín hiệu MUST truy được syslog nền, phiên bản rule và thứ tự nguồn. Timer quiet period khai báo MUST ghi thêm khoảng/mốc chốt và mốc hiệu lực; không tạo syslog giả, không coi im lặng ngoài chính sách là phục hồi.
- **FR-008**: Phục hồi MUST không tự xác nhận đã thấy hoặc tự đóng; người giám sát xác nhận MUST không đổi tín hiệu.
- **FR-009**: Hệ thống MUST cho xác nhận ở cả hai trạng thái tín hiệu, giữ người/thời điểm xác nhận đầu tiên và coi thao tác xác nhận lặp là không thay đổi.
- **FR-010**: Đóng MUST yêu cầu tín hiệu đã phục hồi tại thời điểm ghi. Nếu chưa xác nhận, thao tác xác nhận và đóng MUST ghi đủ hai bước cùng người/thời điểm và cùng thành công hoặc cùng không có hiệu lực.
- **FR-011**: Cảnh báo đã đóng MUST giữ nguyên trạng thái, người/thời gian và bằng chứng; thao tác lặp có quyền MUST trả trạng thái hiện tại mà không ghi thêm lần chuyển.
- **FR-012**: Trước khi đóng, bất thường mới đủ điều kiện MUST tái kích hoạt cùng cảnh báo và giữ xác nhận đã có; bằng chứng mới không liên quan hoặc chưa đủ ngưỡng MUST không tự tái kích hoạt.
- **FR-013**: Sau khi đóng, chuỗi bằng chứng mới đủ điều kiện MUST tạo cảnh báo mới chưa xác nhận. Bằng chứng thuộc chu kỳ trước MUST không được tái sử dụng để tự làm đủ ngưỡng cho chu kỳ sau.
- **FR-014**: Mỗi phiên bản rule, nhóm đối tượng và ngữ cảnh MUST có nhiều nhất một cảnh báo chưa đóng, kể cả khi đã phục hồi hoặc đã xác nhận.
- **FR-015**: Log trễ MUST được tính bù nếu ảnh hưởng vùng sống/baseline với dữ liệu đủ; suy luận lại trên cùng đối tượng rồi tổng hợp nhóm, không áp một log cũ trực tiếp lên tín hiệu mới. Không sửa hoặc mở lại bản closed; log trước/đúng ranh giới kết thúc closed không tự tạo episode mới.
- **FR-016**: Timestamp bằng nhau mâu thuẫn MUST không là căn cứ kết luận phục hồi; cảnh báo chưa đóng được xử lý bảo thủ là bất thường khi điều kiện bất thường đã thỏa. Thiếu thời gian đáng tin cậy MUST không được thay bằng thứ tự nhận.
- **FR-017**: Với nhóm nhiều đối tượng, mặc định chỉ ghi nhận phục hồi khi đủ bằng chứng cho mọi đối tượng còn bất thường theo rule; một log bình thường của một đối tượng MUST không tự kết thúc cả nhóm.
- **FR-018**: Mỗi đổi trạng thái hoặc hiệu chỉnh bằng chứng/outcome có ý nghĩa MUST ghi audit bất biến, trước/sau, chủ thể, nguồn, thời gian, phiên bản và chứng cứ. No-op hoặc log thường không đổi cơ sở kết luận MUST không nhân đôi audit.
- **FR-019**: Thời gian log, mốc hiệu lực điều kiện và thời gian hệ thống ghi/xác nhận/đóng MUST được phân biệt; các lần kết thúc/tái kích hoạt và hiệu chỉnh trước vẫn truy xuất được.
- **FR-020**: Trạng thái, lịch sử và bằng chứng của cùng lần chuyển MUST cùng thành công hoặc cùng không có hiệu lực; thử lại sau gián đoạn MUST không nhân đôi cùng lần chuyển.
- **FR-021**: Thao tác thay đổi từ màn hình cũ MUST phát hiện khi trạng thái đã đổi; không được đóng sau một lần tái kích hoạt đã ghi mà người thao tác chưa thấy. Xác nhận/đóng lặp ở trạng thái đích không làm thay đổi MUST có kết quả an toàn.
- **FR-022**: Hệ thống MUST lọc độc lập hai chiều trạng thái; chưa xác nhận gồm cả bất thường và phục hồi, chờ đóng gồm phục hồi chưa đóng, chưa đóng gồm mọi xác nhận chưa đóng.
- **FR-023**: Người giám sát MUST xem được trạng thái hiện hành, mốc bằng chứng gần nhất, người/thời điểm xác nhận và đóng, lịch sử cùng log nguyên nhân; nhãn MUST thể hiện kết luận dựa trên syslog đã nhận.
- **FR-024**: Đợt nhập lịch sử chỉ để tra cứu MUST không đổi trạng thái cảnh báo trực tiếp; khi chủ động phát lại, mọi chuyển trạng thái MUST giới hạn trong đúng ngữ cảnh phát lại đó.
- **FR-025**: Điều kiện kết thúc MUST được khai báo/kiểm chứng trước bật rule. Không có đóng cưỡng bức hoặc tự closed. Quiet period là điều kiện kết thúc nếu rule có khai báo, không phải xác nhận thiết bị bình thường từ nguồn ngoài syslog.
- **FR-026**: Việc ghi thay đổi và tra bằng chứng MUST bảo toàn định danh cảnh báo/sự kiện; cập nhật danh mục hoặc vị trí lưu rule MUST không làm mất tham chiếu phiên bản đã sử dụng.

- **FR-027**: Các outcome kết thúc được hỗ trợ của rule MUST ánh xạ về tín hiệu recovered mà giữ workflow; không tự tạo cảnh báo rule khác. Outcome cụ thể thuộc đặc tả rule.
- **FR-028**: Audit revision MUST tăng cho hiệu chỉnh có ý nghĩa, kể cả signal/workflow không đổi; giữ dấu vết cơ sở trước/sau để người giám sát thấy thay đổi. Không phát sinh revision cho tính lại ra cùng facts.
- **FR-029**: Quyết định timer MUST không bắt buộc có một syslog mới làm nguyên nhân; bằng chứng gốc vẫn bắt buộc, nguồn timer và mốc tính toán phải rõ.
- **FR-030**: Nếu tính bù vô hiệu RECOVER của episode chưa đóng, hệ thống MUST sử dụng ranh giới hợp lệ trước đó để sửa nhận định, không đòi lại ngưỡng của rule sau một ranh giới đã chứng minh sai. Nếu ngưỡng phát sinh cũ chưa còn chứng minh được mà chưa có kết thúc hợp lệ, đánh dấu cần xem xét, không tự xóa/đóng.
- **FR-031**: Trước timer tại một mốc, sự kiện đủ chốt tại cùng mốc MUST được xét trước; timer stale MUST không tạo kết thúc sai. Nguồn mất tin cậy/tồn đọng ảnh hưởng MUST ngăn kết luận khoảng yên.

- **FR-032**: Thời gian không quan sát được MUST không tự tính như khoảng yên; sau khôi phục chỉ kết thúc khi đủ khoảng theo dõi an toàn hoặc dựng lại được bằng chứng quan sát đầy đủ.
- **FR-033**: Thu hồi cache recovered chưa đóng MUST giữ vòng đời/định danh/xác nhận; khi có dữ liệu mới phải kiểm tra bản hiện hành để không ghi đè CLOSE đã commit.
- **FR-034**: Đổi revision MUST không tạo hai cảnh báo cho cùng nhóm logic đang được revision cũ sở hữu; ghim revision cũ đến đóng và chuyển chủ sở hữu theo 003.

### Key Entities *(include if feature involves data)*

- **Cảnh báo**: Định danh sự cố, hai chiều trạng thái, phiên bản hiện hành của trạng thái, rule/nhóm/ngữ cảnh, mốc bằng chứng, thông tin xác nhận và đóng.
- **Rule có vòng đời**: Phiên bản bất biến, điều kiện phát sinh/kết thúc gồm quiet period nếu đã khai báo, khóa nhóm và quy tắc thời gian; outcome của rule không đồng nghĩa trạng thái thiết bị toàn hệ thống.
- **Bằng chứng syslog**: Sự kiện gốc chứng minh phát sinh/tái phát hoặc phục hồi; giữ thời điểm phát sinh riêng với thời điểm nhận.
- **Lịch sử trạng thái và hiệu chỉnh**: Audit có thứ tự của đổi trạng thái hoặc thay đổi cơ sở kết luận; trước/sau, actor, nguồn, effective/recorded time và bằng chứng, không là một dòng cho mọi log.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Bộ kiểm chứng bao phủ đủ 5 tổ hợp hợp lệ, 1 tổ hợp cấm và toàn bộ các đường chuyển được mô tả; 100% kết quả khớp mong đợi, không có đường tự chuyển từ bất thường sang đóng.
- **SC-002**: Trên ít nhất 20 chuỗi gồm phục hồi trước ACK, tái phát, log trễ/cùng timestamp, thiếu thời gian và quiet period, 100% giữ đúng định danh/xác nhận/chứng cứ; chỉ được RECOVER do khoảng yên khi rule khai báo và dữ liệu an toàn.
- **SC-003**: Gửi lại mỗi thao tác xác nhận/đóng và mỗi sự kiện chuyển tín hiệu 10 lần: không tăng số lần chuyển thực, không thay người/thời điểm đã ghi và không nhân đôi bằng chứng cùng vai trò.
- **SC-004**: Trong các tình huống hai người cùng xác nhận, đóng đua với tái kích hoạt và hai bên cùng phát hiện một nhóm, không có hai lần xác nhận đầu, cảnh báo chưa đóng trùng khóa hoặc tổ hợp bất thường+đã đóng; 100% yêu cầu cũ cần thay đổi được phát hiện.
- **SC-005**: Mô phỏng gián đoạn trước ghi, giữa ghi trạng thái/lịch sử và trước phản hồi: 100% lần ghi hoàn tất có đủ lịch sử/bằng chứng, không có lần chuyển ghi dở; thử lại trả kết quả nhất quán.
- **SC-006**: Trên bộ đủ 5 tổ hợp, 100% kết quả và số đếm của bộ lọc bất thường, chưa xác nhận, chờ đóng, đã đóng và chưa đóng khớp tập mong đợi.
- **SC-007**: Với bộ mẫu ít nhất 100 lần chuyển, 100% truy xuất được chủ thể, thời gian, trạng thái trước/sau và bằng chứng bắt buộc; không có tác vụ thay đổi cấu hình hoặc khắc phục thiết bị.

- **SC-008**: 100% kết luận kết thúc/timer lặp của bộ tích hợp, gồm outcome LinkFlap theo 004, giữ đúng tín hiệu/workflow và audit; không tự ACK/CLOSE hoặc tạo cảnh báo rule khác.
- **SC-009**: Các case tính bù làm đổi outcome, vô hiệu recovery và lặp lại cùng facts có đúng audit/version tương ứng; timer không có raw mới vẫn truy được chứng cứ thật, alert closed không bị sửa.

- **SC-010**: 100% bộ thử mất quan sát, recovered eviction rồi CLOSE/tái phát và đổi revision khi alert cũ mở giữ đúng ranh giới, định danh và audit; không kết thúc dựa trên khoảng dữ liệu bị mất.

## Assumptions

- Đặc tả chốt phạm vi giám sát theo yêu cầu người dùng; các mặc định chi tiết dưới đây là đề xuất để xem xét, chưa phải kết quả triển khai.
- Thay mô hình mở/đã giải quyết trước đây bằng hai chiều tín hiệu và xác nhận; không có trạng thái đang xử lý hoặc giao việc khắc phục.
- Xác nhận đã thấy là thông tin của cảnh báo, không phải đã đọc riêng của từng tài khoản. Bất kỳ người giám sát có quyền đều có thể đóng sau phục hồi, không bắt buộc chính người xác nhận đầu.
- Người thực hiện được cung cấp bởi cơ chế danh tính/quyền của hệ thống; xây dựng đăng nhập và quản lý tài khoản nằm ngoài feature này.
- Bất thường tái xuất hiện trước đóng giữ cùng định danh và xác nhận trước đó; sau đóng tạo định danh mới. Không bổ sung chính sách bắt buộc xác nhận lại cho mỗi lần tái phát.
- Mặc định một nhóm nhiều đối tượng cần tất cả đối tượng còn bất thường được phục hồi; không thêm lựa chọn ANY hoặc suy luận nguyên nhân gốc khi chưa có yêu cầu.
- Mỗi rule khai báo điều kiện kết thúc ở đặc tả riêng; [LinkFlap 004](../004-link-flap-rule/spec.md) dùng vòng đời này. Không tự closed; thiếu log/mất gói vẫn là giới hạn của suy luận theo quan sát.
- Đánh giá theo dữ liệu đã nhận; quyền và đồng bộ màn hình theo [005](../005-monitoring-integration/spec.md); tính bù có giới hạn được đặc tả tại 003, có thể phát hiện muộn hoặc hiệu chỉnh alert chưa đóng. Không tái dựng toàn bộ lịch sử và không sửa bản closed.
- Khi nhiều syslog có timestamp bằng nhau mâu thuẫn và không có thứ tự nguồn đáng tin cậy, không kết luận phục hồi; ưu tiên bảo thủ cho cảnh báo chưa đóng. Quy tắc tạo cảnh báo mới sau đóng chỉ dùng chuỗi bằng chứng mới, không dùng log bằng ranh giới cũ.
- Không đổi đồng loạt vị trí lưu rule trong feature này. Rule ở code, file hoặc kho dữ liệu đều phải giữ được định danh phiên bản và điều kiện gốc cho cảnh báo tồn tại.
- Đệm 3 giây đã chọn cần tính riêng trong tổng độ trễ; mục tiêu 2 giây post-chốt ở 003 là đề xuất chưa phê duyệt, không phải cam kết 2 giây sau nhận.
- Phụ thuộc: đặc tả dữ liệu 001, bộ log giả lập có nhãn thời gian/đối tượng, hợp đồng điều kiện tạo/phục hồi của từng rule, quy ước danh tính và quyền xác nhận/đóng.
- [lifecycle-design.md](lifecycle-design.md) diễn giải mã trạng thái, bảng chuyển và thay đổi dữ liệu. Feature này thay phần vòng đời mở/đã giải quyết trong thiết kế dữ liệu 001; không chạy migration.
