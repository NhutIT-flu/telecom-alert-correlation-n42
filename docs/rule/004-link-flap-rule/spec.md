# Feature Specification: Rule phát hiện LinkFlap

**Feature Branch**: Không tạo nhánh trong lần đặc tả này.

**Created**: 2026-11-19

**Status**: Draft — tách từ feature 003 theo yêu cầu; chưa triển khai hoặc nghiệm thu.

**Input**: User description: "Tách phần rule link flap ra riêng đi."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Phát hiện đúng interface đang flap (Priority: P1)

Người giám sát muốn thấy cảnh báo khi một interface chuyển UP↔DOWN ít nhất 5 lần trong 60 giây, tách biệt từng thiết bị và lớp tín hiệu.

**Why this priority**: Đây là chức năng chính, tránh trộn sự cố hoặc đếm trùng làm phát sinh cảnh báo giả.

**Independent Test**: Đưa các chuỗi xen kẽ cho A/Gi0/0, A/Gi0/1 và B/Gi0/0; đối chiếu định danh, thời điểm đạt ngưỡng và bằng chứng.

**Acceptance Scenarios**:

1. **Given** baseline UP ở giây 0, **When** nhận DOWN tại 5, DOWN lặp tại 6, UP tại 8, DOWN tại 13, UP tại 16, DOWN tại 21, **Then** đạt 5 lần chuyển tại 21; log lặp không tăng đếm.
2. **Given** chưa biết trạng thái trước, **When** nhận quan sát đầu, **Then** chỉ thiết lập baseline, không tự tạo một lần chuyển.
3. **Given** các lần chuyển tại 10,20,30,40,70, **When** xét ở 70, **Then** chỉ còn 4 trong khoảng (10,70], chưa đạt; nếu lần cuối ở 69 thì đủ 5.
4. **Given** hai lớp vật lý/giao thức cùng báo một thay đổi, **When** đánh giá, **Then** chỉ đếm lớp đã chọn; interface trùng tên ở thiết bị khác có kết quả độc lập.

### User Story 2 - Giữ kết quả đúng khi log đến trễ (Priority: P1)

Người giám sát muốn kết luận dựa trên thứ tự xảy ra có căn cứ, đồng thời biết lúc hệ thống phát hiện muộn hoặc chưa đủ dữ liệu để hiệu chỉnh.

**Why this priority**: Log chèn giữa hai quan sát giống nhau có thể làm lộ thêm hai lần chuyển.

**Independent Test**: Hoán vị thứ tự nhận trong và ngoài khoảng chờ 3 giây; thử chèn giữa chuỗi, thay baseline và cần thêm lịch sử.

**Acceptance Scenarios**:

1. **Given** log đến lệch thứ tự trong khoảng chờ 3 giây, **When** đủ điều kiện chốt, **Then** xét theo thời gian nguồn, kể cả khi không có log tiếp theo.
2. **Given** baseline 0 UP và chuỗi 10 DOWN,20 UP,40 DOWN,50 UP,60 UP, **When** nhận trễ 55 DOWN còn trong phạm vi hiệu chỉnh, **Then** dựng lại hai cạnh quanh 55, đạt ngưỡng đầu tại 55 và xét cả cửa sổ kết thúc tại 60.
3. **Given** log trước đầu vùng sống có thể đổi baseline hoặc cửa sổ lịch sử bị ảnh hưởng, **When** kiểm tra, **Then** dùng thêm ngữ cảnh đã lưu để chứng minh; không chỉ xét timestamp log trễ hoặc coi khoảng cache là toàn lịch sử.
4. **Given** thứ tự mâu thuẫn, thiếu lịch sử hoặc log ngoài phạm vi ảnh hưởng, **When** xử lý, **Then** giữ log và lý do; không tự suy số chuyển bằng 0, xóa hoặc đóng cảnh báo.

### User Story 3 - Kết thúc điều kiện flap với trạng thái cuối rõ ràng (Priority: P1)

Người giám sát muốn phân biệt hết flap khi cuối UP và hết flap khi cuối DOWN, đồng thời vẫn tự xác nhận đã thấy và đóng theo vòng đời chung.

**Why this priority**: Hết thay đổi trạng thái không đồng nghĩa đường truyền đã UP hoặc công việc giám sát đã đóng.

**Independent Test**: Mở cảnh báo rồi để yên 60 giây với mỗi trạng thái cuối, thêm log đúng hạn và mô phỏng pipeline không an toàn.

**Acceptance Scenarios**:

1. **Given** cảnh báo đang active và lần chuyển cuối tại 20, **When** đến mốc nguồn 80, đã chốt dữ liệu an toàn và không có chuyển mới, **Then** kết thúc điều kiện flap với outcome UP hoặc DOWN tương ứng; thời điểm ghi có thể khoảng 83 khi không tồn đọng.
2. **Given** chuyển mới đúng giây 80, **When** xét tại hạn, **Then** xét chuyển trước và dời hạn, không phục hồi thoáng qua.
3. **Given** số chuyển giảm dưới 5 nhưng vẫn có chuyển trong 60 giây gần nhất, **When** xét, **Then** chưa kết thúc; nếu chưa từng mở cảnh báo thì không tạo kết luận phục hồi.
4. **Given** cuối DOWN, **When** hết flap, **Then** trả kết quả hết flap–DOWN; không tự tạo LinkDown, xác nhận hoặc đóng cảnh báo.
5. **Given** pipeline, tồn đọng hoặc thời gian chưa đủ tin cậy, **When** không nhận log mới, **Then** không coi khoảng đó là bằng chứng kết thúc.
6. **Given** đã phục hồi hợp lệ, **When** tích lũy đủ 5 chuyển mới sau ranh giới đó, **Then** tái phát theo vòng đời chung; nếu log trễ vô hiệu kết thúc cũ thì hiệu chỉnh episode cũ, không đòi 5 chuyển mới sau ranh giới sai.

### User Story 4 - Thu hồi cửa sổ nhàn rỗi và tiếp tục đúng (Priority: P2)

Người vận hành muốn thu hồi bộ nhớ của interface không còn cần theo dõi nóng, kể cả chưa đủ ngưỡng, mà không mất lịch sử cần dùng.

**Why this priority**: Tiết kiệm tài nguyên nhưng không thay đổi kết quả sau dọn hoặc khởi động lại.

**Independent Test**: Có ba chuyển tại 5,10,20 rồi im lặng; dọn, nạp lại với UP tại 90, thử lỗi lưu và gián đoạn sau chuyển thứ tư.

**Acceptance Scenarios**:

1. **Given** còn 4 chuyển hợp lệ, **When** chạy dọn, **Then** vẫn giữ dữ liệu đó, không xóa vì chưa đạt 5.
2. **Given** các chuyển hết hạn, không log chờ/việc đang chạy/cảnh báo chưa đóng, nhóm đủ nhàn rỗi và trạng thái lưu an toàn, **When** đến lượt dọn, **Then** được thu hồi bộ nhớ; log và trạng thái bền vững vẫn còn.
3. **Given** đã thu hồi sau DOWN ở 20, **When** UP ở 90 được chốt, **Then** nhận diện đúng một chuyển DOWN→UP, không coi là quan sát đầu hoặc cộng hai lần lịch sử.
4. **Given** lưu trạng thái lỗi hoặc có cập nhật mới trong lúc dọn, **When** định thu hồi, **Then** giữ lại dữ liệu để thử lại.
5. **Given** đã lưu bốn chuyển rồi gián đoạn, **When** hoạt động lại và nhận chuyển thứ năm trong cửa sổ, **Then** tạo đúng một cảnh báo với đủ bằng chứng.

### Edge Cases

- Thiếu định danh interface/thiết bị hoặc lớp tín hiệu; không gom trường thiếu thành một nhóm.
- Cùng tên khác thiết bị; alias chưa xác minh; hai thông điệp phản ánh các lớp khác nhau.
- Quan sát không đổi trạng thái vẫn cần cho dựng lại chuỗi hoặc điều kiện khác.
- Timestamp bằng nhau mâu thuẫn, thời gian không rõ hoặc quá tương lai; không đoán bằng thứ tự nhận.
- Log trễ thay hai cạnh, baseline trước vùng sống hoặc ngưỡng tại endpoint mới hơn log đó.
- Cần lịch sử dài hơn 60+3 giây làm việc để chứng minh cửa sổ bị ảnh hưởng.
- Log mới đúng hạn kết thúc; timer cũ, timer lặp hoặc xử lý tồn đọng sau gián đoạn.
- Hiệu chỉnh vô hiệu phát sinh/kết thúc cũ; cảnh báo đã đóng bất biến.
- Cảnh báo recovered nhưng chưa đóng vẫn ngăn thu hồi toàn bộ nhóm ở bản đầu.
- Số mốc ngưỡng giới hạn không phải số đếm tổng hoặc toàn bộ trạng thái.
- UP 5 giây/DOWN 3 giây là giả định tải, không phải thời gian mở/đóng cảnh báo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Rule MUST chỉ dùng sự kiện trạng thái interface đã chuẩn hóa, đủ thiết bị, interface, trạng thái UP/DOWN, lớp tín hiệu và thời gian có căn cứ.
- **FR-002**: Trạng thái MUST độc lập theo phiên bản rule, ngữ cảnh, thiết bị, interface và lớp đã chọn; không tự gộp alias chưa xác minh.
- **FR-003**: Mỗi lần UP↔DOWN có căn cứ MUST tính một lần; không đếm chu kỳ DOWN→UP thành một lần.
- **FR-004**: Quan sát đầu khi chưa biết trạng thái trước MUST chỉ thiết lập baseline.
- **FR-005**: Quan sát lặp MUST không tăng đếm nhưng vẫn được xét/giữ hoặc nạp lại khi cần cho điều kiện và hiệu chỉnh.
- **FR-006**: Ngưỡng phát sinh MUST là ít nhất 5 chuyển trong (T-60 giây,T]; mốc đúng đầu trái bị loại.
- **FR-007**: Cùng episode chưa đóng MUST không tạo thêm định danh cảnh báo chỉ vì ngưỡng tiếp tục đúng; áp vòng đời feature 002.
- **FR-008**: Chỉ lớp tín hiệu được chọn MUST góp vào số chuyển; không cộng đôi vật lý/giao thức.
- **FR-009**: Sự kiện MUST qua khoảng chờ sắp thứ tự 3 giây của cơ chế chung; rule không cộng thêm lần nữa.
- **FR-010**: Log quá khoảng chờ MUST được kiểm tra ảnh hưởng trong vùng sống 60 giây tại mốc chốt và baseline; nếu còn ảnh hưởng thì tính bù đúng nhóm.
- **FR-011**: Tính bù MUST dựng lại các cạnh và mọi cửa sổ bị ảnh hưởng, gồm endpoint mới hơn log trễ; khi cần phải dùng thêm lịch sử và baseline trước đoạn.
- **FR-012**: Log ngoài ảnh hưởng hoặc thiếu căn cứ hiệu chỉnh MUST được giữ với lý do và độ đầy đủ; không được tuyên bố đã dựng lại toàn lịch sử.
- **FR-013**: Thiếu/mâu thuẫn thời gian MUST không bị giải bằng thứ tự nhận để tạo bằng chứng hoặc kết luận phục hồi.
- **FR-014**: Rule đang bất thường MUST kết thúc điều kiện khi 60 giây không ghi nhận chuyển mới, mốc chốt đủ và pipeline/thời gian an toàn.
- **FR-015**: Kết quả kết thúc MUST phân biệt hết flap–UP và hết flap–DOWN theo trạng thái cuối.
- **FR-016**: Cả hai kết quả MUST chỉ đề nghị tín hiệu recovered; không tự xác nhận, đóng hoặc tạo cảnh báo LinkDown.
- **FR-017**: Số chuyển dưới 5, log UP đơn lẻ hoặc dọn cửa sổ MUST không tự đủ để kết thúc; chưa phát sinh thì không có phục hồi.
- **FR-018**: Điều kiện kết thúc MUST được xét dù không có log mới; log đủ chốt đúng deadline MUST được xét trước kết luận thời gian.
- **FR-019**: Tái phát sau kết thúc hợp lệ MUST đòi 5 chuyển mới sau ranh giới hợp lệ; hiệu chỉnh vô hiệu recovery cũ MUST phục hồi cách hiểu episode cũ theo bằng chứng và audit.
- **FR-020**: Hiệu chỉnh có ý nghĩa MUST lưu mốc hiệu lực, lúc phát hiện, bằng chứng và dấu vết trước/sau; nếu phát sinh cũ chưa chứng minh được thì đánh dấu cần xem xét, không tự xóa/hủy/đóng.
- **FR-021**: Cảnh báo đã đóng MUST bất biến; xung đột do log trễ MUST được ghi riêng để xem xét.
- **FR-022**: Dữ liệu nhóm MUST chỉ tạo/nạp khi cần, dùng chung cơ chế thực thi, không cần tiến trình hoặc bộ đếm giờ riêng cho từng interface.
- **FR-023**: Tối ưu giữ 5 mốc ngưỡng MUST không thay thế các quan sát/baseline, ranh giới và bằng chứng cần để khôi phục/tính bù.
- **FR-024**: Dọn mốc hết hạn và thu hồi toàn bộ bộ nhớ nhóm MUST tách biệt; chưa đủ 5 không cho phép xóa 4 mốc còn hợp lệ.
- **FR-025**: Thu hồi MUST chỉ được phép khi hết chuyển hợp lệ, không log chờ/việc đang chạy/cảnh báo chưa đóng, đủ nhàn rỗi và trạng thái đã lưu an toàn; cập nhật mới hoặc lỗi lưu phải hủy thu hồi.
- **FR-026**: Sau thu hồi/gián đoạn MUST khôi phục đúng baseline, quan sát, chu kỳ và kết luận cần thiết; thử lại cùng định danh sự kiện không đếm hoặc tạo cảnh báo hai lần.
- **FR-027**: Rule MUST dùng điều phối, lịch, lưu trạng thái, dọn chung và vòng đời đã đặc tả; không tự tác động thiết bị hoặc gửi dữ liệu trực tiếp cho giao diện.
- **FR-028**: Ngưỡng, khoảng đếm, lớp và điều kiện kết thúc MUST được kiểm tra theo phiên bản trước áp dụng; bản tài liệu tắt không được gọi là rule đã vận hành.

### Key Entities *(include if feature involves data)*

- **Quan sát interface**: Sự kiện chuẩn hóa về UP/DOWN của đúng thiết bị, interface và lớp, với thời gian và định danh nguồn.
- **Baseline và chuyển trạng thái**: Quan sát trước đoạn cùng các cạnh UP↔DOWN được chứng minh.
- **Cửa sổ và trạng thái nhóm**: Các quan sát/mốc còn cần, lần chuyển cuối, giai đoạn theo dõi và ranh giới chu kỳ hợp lệ.
- **Phiên bản LinkFlap**: Thông số đếm, lớp tín hiệu và điều kiện kết thúc gắn logic bất biến theo feature 003.
- **Episode cảnh báo LinkFlap**: Định danh, bằng chứng, outcome và dấu vết hiệu chỉnh; sử dụng thực thể và vòng đời chung 001/002.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% chuỗi kiểm chứng quan sát đầu, log lặp, 5 chuyển/60 giây và biên trái/phải cho đúng kết quả/thời điểm; không mở khi chỉ có 4 chuyển hợp lệ.
- **SC-002**: Với 1.000 interface có tên trùng giữa thiết bị, 100% kết quả và bằng chứng đúng nhóm; sai lớp hoặc thiếu định danh không làm đủ ngưỡng giả.
- **SC-003**: 100% chuỗi lệch thứ tự mẫu, gồm chèn giữa, đổi baseline và đọc thêm lịch sử, cho đúng kết quả hoặc ghi rõ chưa đủ căn cứ; không sửa bản đã đóng.
- **SC-004**: Cả hai trạng thái cuối UP/DOWN đều kết thúc đúng sau 60 giây không chuyển khi dữ liệu an toàn; không tự ACK/CLOSE/LinkDown; log đúng deadline không gây phục hồi thoáng qua.
- **SC-005**: Toàn bộ trường hợp dọn/khôi phục được nêu cho cùng kết quả trước và sau thu hồi, không mất log/bằng chứng; gửi lại mỗi định danh 10 lần không nhân đôi kết quả.
- **SC-006**: Tải 1.000 interface UP 5 giây/DOWN 3 giây, mỗi lần chuyển một sự kiện, đối chiếu đủ 900.000 chuyển/giờ (trung bình 250/giây, đợt đồng bộ 1.000); đo cả tải đều và dồn, không báo hoàn tất khi bỏ dữ liệu.
- **SC-007**: Trên tải SC-006, báo cáo riêng độ trễ tiếp nhận→đủ chốt và đủ chốt→hiển thị; mục tiêu lab đề xuất cho đoạn sau là p95 2 giây/p99 5 giây, chưa phải nghiệm thu. Tổng độ trễ có thêm khoảng chờ 3 giây và tồn đọng.
- **SC-008**: Đối chiếu được tài nguyên của 1.000 nhóm: tối đa 5.000 mốc ở bộ đệm ngưỡng, đo riêng toàn trạng thái và lưu trữ; không tích lũy toàn bộ 900.000 sự kiện trong bộ nhớ theo dõi hoặc lấy mô phỏng nhỏ làm ngân sách toàn hệ thống.

## Assumptions

- Tách nội dung chuyên biệt từ 003; đây là nguồn chuẩn của LinkFlap. [Thiết kế chi tiết](link-flap-design.md) mô tả thuật toán, cấu hình và ca kiểm chứng.
- Phụ thuộc [dữ liệu 001](../001-alert-data-model/spec.md), [vòng đời 002](../002-alert-lifecycle/spec.md), [điều phối/hợp đồng 003](../003-rule-dispatch-correlation/spec.md); không thêm bảng riêng cho rule.
- Người dùng chọn 5 lần chuyển/60 giây, chờ sắp thứ tự 3 giây và hai kết quả UP/DOWN. Quiet 60 giây là phương án hiện tại từ thảo luận; không thay đổi trong lần tách này.
- Bản mẫu chọn lớp vật lý; chỉ ánh xạ hãng/thiết bị đã được chuẩn hóa tương đương mới sử dụng được.
- Chu kỳ dọn 5 giây và idle 60 giây là mặc định đề xuất của module chung, không phải thời gian phát sinh/kết thúc rule hoặc tham số đã được phê duyệt.
- Khoảng yên chỉ phản ánh log đã nhận. Mất gói, pipeline hoặc clock không tin cậy giới hạn suy luận; không kiểm tra trực tiếp thiết bị.
- Tính bù giới hạn vùng ảnh hưởng, không tái dựng mọi sự cố lịch sử. Cảnh báo closed bất biến; chưa thêm trạng thái hủy.
- Mô hình tải có baseline UP trước giờ thử; thời gian UP/DOWN là thời gian lưu trạng thái interface. Tài nguyên đầy đủ và mục tiêu độ trễ chưa được đo trên ứng dụng.
