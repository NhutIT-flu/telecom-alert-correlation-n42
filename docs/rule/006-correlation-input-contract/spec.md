# Feature Specification: Hợp đồng đầu vào module tương quan

**Feature Branch**: `006-correlation-input-contract` (tên đặc tả; chưa tạo nhánh Git)

**Created**: 2026-11-25

**Status**: Draft — phương án trình leader duyệt, chưa triển khai

**Input**: User description: "Viết spec cho phần đầu vào của module gom nhóm/tương quan/rule."

**Ranh giới**: Đặc tả này sở hữu điều kiện bàn giao sự kiện đã chuẩn hóa từ [005](../005-monitoring-integration/spec.md) sang [003](../003-rule-dispatch-correlation/spec.md). Nơi lưu do [001](../001-alert-data-model/spec.md) sở hữu; thuật toán LinkFlap do [004](../004-link-flap-rule/spec.md) sở hữu. Không định nghĩa lại parser, ngưỡng, vòng đời hoặc frontend.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Rule nhận sự kiện cùng nghĩa (Priority: P1)

Người thiết kế rule muốn một hiện tượng mạng có cùng tên trường, kiểu và ý nghĩa dù log đến từ Cisco hay Juniper.

**Why this priority**: Sai nghĩa field làm gom nhóm và cảnh báo sai dù thuật toán đúng.

**Independent Test**: Đối chiếu mẫu đã gán nhãn của hai hãng tại ranh giới bàn giao.

**Acceptance Scenarios**:

1. **Given** hai log cùng nghĩa trạng thái interface, **When** chuẩn hóa và bàn giao, **Then** chúng có cùng loại sự kiện và cùng quy ước field nghiệp vụ.
2. **Given** lớp tín hiệu chưa xác minh, **When** bàn giao, **Then** không tự điền `physical` để LinkFlap nhận nhầm.

---

### User Story 2 - Xét đủ đầu vào theo từng rule (Priority: P1)

Người thiết kế rule muốn sự kiện thiếu field riêng của một rule vẫn có thể được rule khác đánh giá.

**Why this priority**: Một syslog có thể liên quan nhiều rule với yêu cầu khác nhau.

**Independent Test**: Cho một event thiếu field LinkFlap qua hai rule có yêu cầu khác nhau.

**Acceptance Scenarios**:

1. **Given** event đúng loại nhưng thiếu `interface_name`, **When** xét LinkFlap, **Then** không tạo nhóm giả và ghi lý do; rule khác đủ field vẫn được xét.
2. **Given** không rule nào đăng ký loại event, **When** xét, **Then** ghi kết quả không khớp, không coi là lỗi thực thi.

---

### User Story 3 - Không kết thúc sai khi thiếu căn cứ (Priority: P1)

Người giám sát muốn kết luận khoảng yên chỉ xảy ra khi các đầu vào liên quan đã được xét và khả năng quan sát được chứng minh.

**Why this priority**: Log chưa đọc hoặc không định danh được có thể che giấu lần chuyển mới.

**Independent Test**: Thử log chưa chốt, sai thời gian và thiếu khóa nhóm trước deadline.

**Acceptance Scenarios**:

1. **Given** event liên quan còn chờ chốt, **When** đến deadline, **Then** nhóm bị ảnh hưởng chưa được kết luận phục hồi.
2. **Given** log có thể thuộc thiết bị nhưng không xác định interface, **When** xét khoảng yên, **Then** phạm vi không chắc chắn được đánh dấu, không tự tính là yên.

---

### User Story 4 - Truy vết kết quả bàn giao (Priority: P2)

Người kiểm thử cần biết vì sao event được xét, chưa chốt, không thuộc rule hoặc thiếu dữ liệu, kể cả sau restart.

**Why this priority**: Không có alert không đồng nghĩa rule đã xử lý thành công.

**Independent Test**: So khớp ID, lý do và tiến độ trước/sau worker restart.

**Acceptance Scenarios**:

1. **Given** event thiếu field của một rule, **When** rule đó bỏ qua, **Then** có mã lý do ổn định gắn với event/rule và raw không đổi.
2. **Given** đánh giá chưa commit, **When** worker restart, **Then** event vẫn cần xét và không bị báo hoàn tất.

### Edge Cases

- `parse_status=partial`: rule đủ field vẫn được xét; rule khác có lý do riêng.
- Field cũ và chuẩn mâu thuẫn, hoặc lớp tín hiệu không rõ: không chọn tùy tiện.
- Thiếu device, interface alias chưa xác minh hoặc tên interface trùng giữa thiết bị: không tạo nhóm chung giả.
- Thời gian thiếu, quá tương lai hoặc mâu thuẫn: không dùng giờ nhận hay ID để giả thứ tự nguồn.
- Event chưa chốt hoặc backlog chưa đọc: không ghi đã xử lý hay tính im lặng là khoảng yên.
- Quan sát trạng thái lặp vẫn được bàn giao nếu rule cần baseline/tính bù.
- Lịch sử search-only và replay chủ động không trộn với live.
- JSON đã chuẩn hóa không được giả là raw syslog thiết bị.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Module MUST chỉ nhận sự kiện đã lưu bền vững, có ID ổn định và trạng thái chuẩn hóa đủ điều kiện xét; raw tiếp tục truy vết được.
- **FR-002**: Bản bàn giao MUST phân biệt ID, loại event, scope, device, thời gian sinh/nhận, căn cứ thời gian và field nghiệp vụ; không bịa giá trị chưa biết.
- **FR-003**: Mỗi loại event MUST có quy ước tên field, kiểu và enum chung giữa các hãng khi ngữ nghĩa tương đương; chi tiết hãng không giả làm field chung.
- **FR-004**: `interface_state_change` MUST chỉ sử dụng `interface_name` không rỗng, `interface_state` thuộc `UP/DOWN` và `interface_layer` thuộc `physical/protocol` khi có căn cứ; không tự điền field thiếu để đạt điều kiện rule.
- **FR-005**: Điều kiện đủ MUST được xét theo từng rule: loại event, field cần, field tạo nhóm, scope và yêu cầu thời gian; không áp một bộ field cho mọi rule.
- **FR-006**: Một event MUST được xét bởi mọi rule liên quan trong lượt; thiếu field cho một rule MUST không chặn rule khác. Mỗi revision liên quan được xét tối đa một lần trong lượt.
- **FR-007**: Kết quả đầu vào theo event/rule MUST phân biệt áp dụng, không thuộc rule, thiếu/mâu thuẫn và chưa đủ căn cứ; thiếu đầu vào không được ghi thành handler thành công. Khi các rule đủ dữ liệu đã xét xong, event có thể hoàn tất với diagnostic của rule thiếu dữ liệu; guard ảnh hưởng timer MUST được lưu bền vững trước khi coi event hoàn tất.
- **FR-008**: Khóa nhóm MUST chỉ lấy field đã xác minh; không gộp NULL, alias chưa xác minh, interface trùng tên ở thiết bị khác hoặc lớp tín hiệu khác nghĩa.
- **FR-009**: Rule thời gian MUST dùng thời gian sinh có căn cứ; không dùng giờ nhận hay event ID thay thế thứ tự sinh.
- **FR-010**: Event chưa đủ chốt MUST giữ chưa hoàn tất; event/backlog liên quan chưa xét MUST chặn kết luận khoảng yên của phạm vi ảnh hưởng.
- **FR-011**: Đầu vào thiếu/mâu thuẫn có thể ảnh hưởng timer MUST có diagnostic về mức chắc chắn và phạm vi; không tự coi là không có thay đổi trạng thái.
- **FR-012**: Phạm vi chặn MUST thu hẹp theo căn cứ có được: nhóm nếu đủ khóa, thiết bị nếu chỉ biết thiết bị, nguồn/scope nếu chỉ biết nguồn. Không có căn cứ thu hẹp thì báo phạm vi chưa chứng minh và chặn kết luận liên quan.
- **FR-013**: Hệ thống MUST có mã lý do ổn định cho thiếu thiết bị/field nhóm, enum hoặc lớp mâu thuẫn, thời gian không rõ, chưa chốt, scope không được xét và loại event không được rule hỗ trợ; không sửa raw.
- **FR-014**: Event chuẩn hóa một phần MUST được xét bởi rule đủ dữ liệu; event không chuẩn hóa được MUST vẫn tìm kiếm được và không giả là đã tham gia rule.
- **FR-015**: Chỉ đánh dấu hoàn tất sau khi kết quả, diagnostic cần giữ, state/alert và tiến độ có hiệu lực nhất quán; restart hoặc xét lại cùng ID không tạo kết quả kép.
- **FR-016**: Lịch sử mặc định chỉ tra cứu; replay chủ động MUST có scope riêng, không làm bằng chứng cho live.
- **FR-017**: Hợp đồng MUST phân biệt thuộc tính lưu bền vững với bản có kiểu đưa cho rule; đổi cách lưu/tối ưu sau này không tạo hai nguồn chuẩn mâu thuẫn.
- **FR-018**: Hệ thống MUST thống kê được số event theo kết quả bàn giao, mã lý do và tuổi tồn đọng để phân biệt không khớp với chưa thể xét.

### Key Entities *(include if feature involves data)*

- **Sự kiện đã lưu**: Syslog gốc, bản chuẩn hóa, nguồn, scope và trạng thái theo 001.
- **Bản bàn giao**: Cách nhìn có kiểu của event đã lưu, không phải bản sao lưu trữ thứ hai.
- **Schema loại sự kiện**: Quy ước tên, kiểu, enum và ý nghĩa field theo `event_type`.
- **Yêu cầu rule**: Loại event, field, nhóm và căn cứ thời gian do handler 003 khai báo.
- **Kết quả kiểm tra đầu vào**: Nhãn và mã lý do theo event/rule, khác kết luận cảnh báo.
- **Phạm vi quan sát an toàn**: Nhóm/thiết bị/nguồn hoặc scope có căn cứ để xét timer theo 003/005.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Với ít nhất 40 mẫu Cisco/Juniper đã gán nhãn, 100% field chung và giá trị chưa biết khớp schema mong đợi; không có mapping sai lớp/trạng thái gây alert giả.
- **SC-002**: Với ít nhất 100 event và 5 rule có yêu cầu khác nhau, 100% rule liên quan được xét một lần hoặc có lý do đúng nhãn; thiếu field của một rule không làm bỏ rule khác.
- **SC-003**: Với 1.000 nhóm interface có tên trùng giữa thiết bị, 100% event đủ định danh vào đúng nhóm; không có nhóm NULL/alias suy đoán.
- **SC-004**: Mọi ca thử chưa chốt, backlog, thiếu thời gian/khóa nhóm và mất quan sát đều không tạo kết luận phục hồi sai; lý do và phạm vi chặn khớp nhãn.
- **SC-005**: Tại các điểm gián đoạn trước/sau ghi kết quả, 100% event đã lưu tiếp tục đúng; xét lại cùng ID 10 lần không tạo kết quả nghiệp vụ kép.
- **SC-006**: Trên tải thử LinkFlap của 004, báo cáo riêng nhận→đủ chốt, đủ chốt→hiển thị và số event chờ/thiếu căn cứ; mục tiêu lab của 003 chưa là SLA được chốt.
- **SC-007**: Với 100% event bị bỏ qua/trì hoãn trong bộ thử, người kiểm thử truy được ID, rule, mã lý do và phạm vi ảnh hưởng mà không phải đoán từ việc thiếu alert.

## Assumptions

- Đây là thiết kế prototype để leader duyệt, chưa có implementation hoặc SLA đã nghiệm thu.
- Phần khác sở hữu thu thập, lưu raw và chuẩn hóa theo 001/005; module này không nhận UDP/API/tệp trực tiếp hay parse raw.
- `attributes` là dữ liệu lưu trong event; `fields` là bản chiếu có kiểu cho rule, không phải cột/bảng hoặc nguồn chuẩn thứ hai.
- Tên mã lý do và cách ghi diagnostic cụ thể được chốt ở thiết kế kỹ thuật; các loại kết quả và khả năng truy vết là bắt buộc.
- Người thiết kế đã chọn phương án bảo thủ FR-012 cho prototype: đầu vào thiếu căn cứ ảnh hưởng timer chặn kết luận trong phạm vi xác định được, cho đến khi có lại căn cứ quan sát an toàn. Cần trình leader duyệt và kiểm chứng với log lab; không suy luận UDP giao đầy đủ.
- Rule nghiệp vụ triển khai trong đợt prototype đầu là LinkFlap. Hợp đồng engine vẫn cho phép nhiều rule; các ca dùng nhiều rule trong tài liệu là kiểm chứng khả năng mở rộng bằng handler thử, không là cam kết triển khai 5 rule nghiệp vụ.
- Log quá đệm 3 giây được tính bù trong vùng ảnh hưởng có thể chứng minh của LinkFlap; ngoài vùng có diagnostic rõ, không sửa cảnh báo đã đóng.
- Lỗi code/checkpoint không đọc được làm dừng tiến độ tương quan, giữ event chưa hoàn tất và báo sức khỏe lỗi; không lặng lẽ bỏ rule.
- Cấu hình rule do nhóm phát triển công bố dưới dạng phiên bản trong prototype; người giám sát chỉ xem rule, không đăng ký loại log hoặc sửa tham số qua giao diện.
- Phạm vi chống trùng lặp **giữa các ID đầu vào khác nhau** chưa chốt. Xử lý lại cùng ID ở FR-015 vẫn áp dụng.
