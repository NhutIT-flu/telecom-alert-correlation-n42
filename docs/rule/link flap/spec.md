# Feature Specification: Link Flap và module rule dùng chung

**Feature Branch**: Chưa tạo (workspace chưa có repository Git).

**Created**: 2026-11-16

**Status**: Draft — đã ghi nhận lựa chọn nghiệp vụ và nguồn dự án; thiết kế triển khai tại [plan.md](plan.md).

**Input**: Rà soát thiết kế N4.2, hỏi các điểm mơ hồ và chuẩn hóa đặc tả. Người dùng xác nhận phạm vi “triển khai toàn bộ luật link flap cũng như setup cho mudule các rule sau”, chọn RECEIVED_TIME và kết thúc theo quan sát sau 120s. Lượt specify này tạo đặc tả, chưa triển khai mã nguồn.

**Nguồn**: [N4.2 — Đặc tả kỹ thuật Link Flap Detection](<C:/Users/ayemq/Documents/Codex/2026-11-16/referenced-chatgpt-conversation-this-is-an/outputs/N4.2_Dac_ta_ky_thuat_Link_Flap_Detection.md>). Các yêu cầu kế thừa từ nguồn chưa phải bằng chứng hệ thống đã triển khai. Đề xuất không tự trở thành quyết định đã phê duyệt.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Phát hiện đúng dao động từng interface (Priority: P1)

Người vận hành nhận một cảnh báo khi một interface có ít nhất năm lần đổi UP↔DOWN trong 60 giây theo thời gian Collector nhận log.

**Why this priority**: Đây là chức năng chính; đếm bản tin hoặc cộng chéo interface sẽ báo sai.

**Independent Test**: Cấp chuỗi quan sát có baseline/thời gian đã biết, đối chiếu thời điểm phát hiện và số đếm.

**Acceptance Scenarios**:

1. **Given** chưa có baseline, **When** nhận DOWN đầu tiên rồi nhiều DOWN khác ID, **Then** thiết lập baseline DOWN, số chuyển đổi bằng 0 và không mở Link Flap.
2. **Given** baseline UP tại −1s, **When** có trạng thái xen kẽ bắt đầu DOWN tại 0,15,30,45,60s, **Then** mở đúng một đợt tại 60s, tổng 5, bắt đầu đợt tại 0s.
3. **Given** cùng baseline, **When** chuyển đổi tại 0,15,30,45,60.001s, **Then** không kích hoạt; cửa sổ cuối có bốn chuyển đổi.
4. **Given** các thiết bị/interface khác nhau, **When** mỗi khóa có dưới năm chuyển đổi, **Then** không cộng dồn giữa các khóa để kích hoạt.

### User Story 2 - Cập nhật và kết thúc đúng đợt (Priority: P1)

Người vận hành theo dõi một đợt xuyên suốt và biết rõ hết dao động có thể vẫn là DOWN.

**Why this priority**: Tránh cảnh báo trùng và hiểu sai kết thúc Link Flap thành đường truyền đã UP.

**Independent Test**: Dùng một đợt phát hiện tại 40s với tổng 5, kiểm tra cập nhật và các mốc trước/đúng/sau hạn.

**Acceptance Scenarios**:

1. **Given** đợt mở tại 40s, **When** có chuyển đổi tại 50 và 100s, **Then** giữ cùng đợt, tổng 7, cửa sổ tại 100s có 3, hạn mới 220s.
2. **Given** hạn 160s và trạng thái DOWN, **When** nhận DOWN lặp tại 45,100,159s, **Then** tổng và hạn không đổi.
3. **Given** hạn 160s, pipeline khỏe và tiến độ đủ, **When** không có chuyển đổi trước hạn, **Then** kết thúc theo quan sát tại 160s, phân biệt cuối UP/DOWN; cuối DOWN không được mô tả là kết nối đã UP.
4. **Given** hạn 160s, **When** có chuyển đổi tại 159.999s, **Then** giữ đợt và hạn mới 279.999s; nếu chuyển đổi đúng 160s và đủ điều kiện kết thúc thì kết thúc đợt cũ trước, tính chuyển đổi mới cho lần theo dõi tiếp theo.
5. **Given** còn đầu vào nhận trước hạn chưa xử lý hoặc chất lượng suy giảm, **When** đến hạn, **Then** giữ hồ sơ chưa kết thúc và lý do chờ; thời gian trôi qua không tự xóa lỗi chất lượng.
6. **Given** người vận hành đã đánh dấu hồ sơ RESOLVED nhưng đợt kỹ thuật còn hoạt động, **When** có chuyển đổi mới, **Then** cập nhật cùng đợt.
7. **Given** đợt kết thúc cuối DOWN, **When** yêu cầu phối hợp tới Link Down bị trễ và UP đã được ghi nhận, **Then** bên nhận xét trạng thái hiện tại, không tạo Link Down từ DOWN cũ; nếu hiện DOWN thì tôn trọng ngưỡng của Link Down.

### User Story 3 - Thêm rule qua module chung (Priority: P2)

Nhóm phát triển đăng ký thêm rule có state riêng, dùng cùng đầu vào đã chuẩn hóa.

**Why this priority**: Người dùng yêu cầu chuẩn bị module cho các rule tiếp theo.

**Independent Test**: Đăng ký một rule kiểm chứng tối thiểu rồi đối chiếu kết quả Link Flap trước/sau.

**Acceptance Scenarios**:

1. **Given** Link Flap đã đăng ký, **When** thêm rule kiểm chứng cùng loại đầu vào, **Then** hai rule nhận cùng phân loại quan sát và trạng thái trước/sau bất biến; state không ảnh hưởng nhau, kết quả Link Flap không đổi.
2. **Given** hai rule xử lý cùng quan sát, **When** một rule lỗi, **Then** không xác nhận xử lý trọn vẹn hoặc lưu kết quả một phần gây mất chuyển đổi khi thử lại.
3. **Given** rule tương lai dùng loại thực thể khác, **When** khai báo hợp lệ, **Then** hợp đồng module cho phép khóa riêng, không ép mọi rule dùng interface, UP/DOWN hoặc cửa sổ 60s.

### User Story 4 - Giữ kết quả qua retry và restart (Priority: P2)

Người vận hành không nhận thêm đợt cảnh báo do giao lại, xử lý đồng thời hoặc khởi động lại.

**Why this priority**: Luật hoàn chỉnh cần giữ baseline, đợt và hiệu lực quyết định qua lỗi vận hành.

**Independent Test**: So kết quả chuỗi có retry/lỗi giữa chừng/restart với xử lý tuần tự không lỗi.

**Acceptance Scenarios**:

1. **Given** đầu vào đã xác nhận, **When** giao lại cùng ID/nội dung, **Then** không tăng tổng hoặc thêm hiệu lực; cùng ID nhưng nội dung khác phải báo xung đột và giữ kết quả đã xác nhận.
2. **Given** đợt đang mở trước restart, **When** khôi phục đủ dữ liệu, **Then** giữ ID đợt, tổng và hạn; xử lý backlog trước khi kết luận kết thúc.
3. **Given** thiếu state và lịch sử đủ dựng lại, **When** restart, **Then** hiển thị thiếu tin cậy, giữ hồ sơ chưa kết thúc và yêu cầu đối soát.
4. **Given** timer/quyết định cũ giao lại hoặc worker cũ mất quyền xử lý, **When** xử lý, **Then** không ghi đè tổng mới hoặc kết thúc nhầm đợt.
5. **Given** đầu vào sai khóa/trạng thái/cấu hình/thứ tự, **When** kiểm tra, **Then** từ chối có lý do, không đổi state nghiệp vụ; lỗi ảnh hưởng tính đầy đủ phải thể hiện trong chất lượng.
6. **Given** quyết định được giao sai thứ tự, **When** phát hiện thiếu quyết định trước, **Then** chờ/bổ sung đúng thứ tự, không áp dụng recovery làm mất trigger.

### Edge Cases

- So chính xác các biên 60s/120s, kể cả chênh lệch 1ms.
- Received timestamps bằng nhau dùng thứ tự nhận xác định; không dùng thứ tự hoàn tất chuẩn hóa.
- Received time giảm, nguồn đổi hoặc sequence reset không hợp lệ phải chặn phần luồng ảnh hưởng.
- INITIAL DOWN vẫn tạo baseline; Link Down được theo dõi độc lập.
- Worker chưa chạy mà event đến sau hạn phải cho cùng cách chia đợt như worker đã chạy, nếu chất lượng/tiến độ đủ.
- Giữ đúng số đếm khi hơn năm chuyển đổi; quá tải không được bỏ dữ liệu im lặng rồi báo đầy đủ.
- Đổi cấu hình/nguồn không tự kết thúc đợt hoặc trộn cơ sở thời gian.
- Quyết định mở/cập nhật/kết thúc phải có bằng chứng nguồn và trạng thái quan sát cuối để bên nhận diễn giải đúng.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Theo dõi độc lập từng cặp định danh thiết bị/interface ổn định; chỉ nhận OPER_STATUS UP/DOWN cho luật này.
- **FR-002**: INITIAL chỉ tạo baseline; UP/DOWN lặp không tăng đếm; mỗi lần UP↔DOWN tính một chuyển đổi.
- **FR-003**: Bản đầu dùng thời gian Collector nhận lần đầu cho cửa sổ và recovery. Retry/replay giữ thời gian này; không đổi sang thời gian thiết bị theo từng bản tin.
- **FR-004**: Khi chưa có đợt mở, kích hoạt tại chuyển đổi đầu tiên đạt ít nhất 5 chuyển đổi trong [t−60s,t], bao gồm hai đầu.
- **FR-005**: Tối đa một đợt chưa kết thúc cho mỗi khóa luật/thực thể, kể cả khi thiếu tin cậy. Mọi chuyển đổi tiếp theo cập nhật đợt đó dù cửa sổ xuống dưới 5.
- **FR-006**: Kết quả có ID đợt, mốc bắt đầu/phát hiện/chuyển đổi cuối/hạn/kết thúc, số đếm cửa sổ kèm thời điểm tính, tổng đợt, trạng thái cuối và chất lượng. Tổng bắt đầu bằng toàn bộ cửa sổ kích hoạt, chỉ tăng theo chuyển đổi và không giảm khi cửa sổ trượt.
- **FR-007**: Hạn bằng chuyển đổi thật cuối cộng 120s; repetition không kéo dài hạn. Khi đủ điều kiện, xử lý kết thúc trước event đúng hạn.
- **FR-008**: Chỉ tự kết thúc khi mọi đầu vào trước hạn đã áp dụng, có xác nhận tiến độ nhận đến hạn, pipeline khỏe và không có gap/outage/lỗi chất lượng đã biết ảnh hưởng. Không yêu cầu probe/SNMP; kết luận chỉ theo quan sát.
- **FR-009**: Phân biệt kết thúc cuối UP/DOWN và giữ baseline cho lần theo dõi mới. Không rõ/suy giảm thì giữ hồ sơ chưa kết thúc, ghi lý do chờ đối soát.
- **FR-010**: Có điểm phối hợp bền vững với Link Down khi kết thúc cuối DOWN; phía nhận đọc trạng thái hiện tại, chống trùng và tôn trọng down-hold. Adapter kiểm chứng không thay cho Link Down production.
- **FR-011**: Workflow của người vận hành độc lập trạng thái kỹ thuật; đóng hồ sơ xử lý không reset đợt, baseline hoặc bộ đếm.
- **FR-012**: Module chung hỗ trợ đăng ký rule theo loại đầu vào/khóa thực thể, cấu hình và state riêng, xử lý sự kiện/timer. Các rule nhận cùng quan sát trước/sau bất biến. Không cần xây DSL hoặc rule nghiệp vụ khác.
- **FR-013**: Cùng thực thể xử lý theo thứ tự nhận xác định, timer cùng thứ tự nghiệp vụ. Loại timer hết hiệu lực và ngăn worker cũ ghi sau khi mất quyền.
- **FR-014**: Giữ nhất quán baseline, state các rule, tiến độ, lịch hẹn và ý định quyết định/phối hợp qua retry/restart. Chỉ xác nhận sau khi lưu trọn vẹn; lỗi một rule không để lại kết quả một phần.
- **FR-015**: Cùng ID/nội dung không thêm hiệu lực; cùng ID/khác nội dung báo xung đột. Quyết định cũ không ghi đè mới hoặc kết thúc đợt khác; phát hiện thiếu thứ tự trước khi áp dụng tiếp.
- **FR-016**: Đầu vào sai khóa, trạng thái, thứ tự, phiên bản hoặc cấu hình bị từ chối có lý do, không đổi state nghiệp vụ; lỗi ảnh hưởng tính đầy đủ phải thể hiện trong chất lượng.
- **FR-017**: Khôi phục đợt hiện có, xử lý dữ liệu tồn trước recovery. Thiếu state/lịch sử thì chờ xác minh, không suy ra recovery từ thời gian ứng dụng ngừng chạy.
- **FR-018**: Đầu ra phân biệt mở/cập nhật/kết thúc, có ID/thứ tự, nguồn bằng chứng, giới hạn RECEIVED_TIME/LAST_OBSERVED để bên quản lý cảnh báo áp dụng đúng. Lưu/gửi/hiển thị thực tế theo hợp đồng ứng dụng tích hợp.

### Key Entities *(include if feature involves data)*

- **Interface**: Cặp thiết bị/interface, baseline, trạng thái cuối, thời điểm quan sát và chất lượng.
- **Quan sát/chuyển đổi**: ID ổn định, nguồn/thứ tự/thời gian nhận đầu, UP/DOWN, phân loại INITIAL/REPEATED/TRANSITION, bằng chứng gốc.
- **Đợt Link Flap**: ID riêng, tổng đếm, mốc thời gian, trạng thái hoạt động/kết thúc và chất lượng.
- **Rule đăng ký**: Loại đầu vào, khóa thực thể, cấu hình/phiên bản và state độc lập.
- **Lịch hẹn/tiến độ**: Hạn, đợt liên quan, hiệu lực lịch hẹn và bằng chứng đã xử lý đủ đầu vào.
- **Quyết định/yêu cầu phối hợp**: Kết quả có ID/thứ tự để áp dụng một lần hiệu lực; đối soát Link Down là loại riêng.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% tình huống baseline, repetition, cô lập khóa và biên 60s đã xác định cho đúng kết quả; không kích hoạt trước chuyển đổi hợp lệ thứ năm.
- **SC-002**: Mọi chuỗi trong một đợt chỉ có một hồ sơ kỹ thuật trên khóa; tổng và hạn đúng sau mỗi chuyển đổi, không thay bởi repetition.
- **SC-003**: 100% tình huống biên 120s, timer trễ và chất lượng suy giảm cho cùng lifecycle với mô hình theo thứ tự; không trường hợp cuối DOWN nào được kết luận là đã UP.
- **SC-004**: Toàn bộ tình huống retry/lỗi giữa chừng/restart trong nghiệm thu giữ cùng đợt, bộ đếm và hiệu lực như lần chạy không lỗi; thiếu dữ liệu luôn thể hiện chờ xác minh.
- **SC-005**: Thêm một rule kiểm chứng qua đăng ký không sửa thuật toán Link Flap; kết quả Link Flap giữ nguyên và state hai rule độc lập.
- **SC-006**: Mọi trường hợp từ chối/chặn recovery trong nghiệm thu có lý do truy vết được; không có mất dữ liệu im lặng được báo thành xử lý thành công.

## Assumptions

- **Đã xác nhận 16/11/2026**: Toàn bộ luật Link Flap và module cho các rule sau; RECEIVED_TIME; recovery 120s theo quan sát, không cần probe/SNMP.
- **Diễn giải phạm vi**: Bao gồm registry, state, ordering, timer, lưu tiến độ và bàn giao quyết định cần cho luật hoàn chỉnh. Collector/parser vendor, dashboard, Alert Manager thực tế và các rule nghiệp vụ khác là điểm tích hợp ngoài module. Lượt specify không tự triển khai các thành phần này.
- **Kế thừa nguồn**: Ngưỡng 5/60s, biên bao gồm hai đầu, một đợt mở trên khóa; không đổi vì khả năng cấu hình.
- **Phụ thuộc đầu vào**: Một nguồn nhận có thẩm quyền/device, ID/order/time tin cậy và xác nhận tiến độ bao phủ raw chưa chuẩn hóa. Nếu thiếu, kế hoạch phải nêu phần bổ sung; không giả định pipeline đã khỏe.
- **Tính bền vững**: Bản hoàn chỉnh phải đáp ứng retry/restart. Adapter giả chỉ cho kiểm thử độc lập; chưa chọn công nghệ lưu trữ/giao tiếp khi chưa có kiến trúc dự án.
- **Link Down**: Chỉ hợp đồng phối hợp; không tự chốt ngưỡng 30s. Nghiệm thu tích hợp cuối DOWN cần bên sở hữu Link Down thật.
- **Bảo trì/admin shutdown**: Chưa bổ sung suppress; luật tính mọi OPER_STATUS hợp lệ được pipeline chuyển vào. Nếu cần loại bảo trì, phải bổ sung chính sách và nghiệm thu trước production.
- **Chưa duyệt**: Tick 5s, scheduling budget 2s, tải lab và retention trong nguồn còn là đề xuất, chưa là SLA/năng lực đã đo. Chưa cam kết thời gian hiển thị/gửi, tải production hoặc thời gian lưu giữ.
- **Ngoài đợt đầu**: EVENT_TIME/reorder, xác minh vật lý, đa nguồn chưa hợp nhất, DSL và rule nghiệp vụ mới. Khả năng mở rộng kiểm chứng bằng rule thử tối thiểu.
- **Ngữ cảnh cập nhật khi lập plan, 16/11/2026**: Người dùng chỉ định source tại `C:/Projects/vnpt`, repository ứng dụng là `C:/Projects/vnpt/telecom-alert-correlation-n42`; lấy công nghệ từ đây nhưng triển khai theo thiết kế trong chat. Đã đọc source Python3.12/FastAPI/Pydantic2 và target PostgreSQL16/TimescaleDB. Các artifact Spec Kit tiếp tục lưu trong workspace tài liệu hiện tại. Constitution ở đây vẫn là placeholder, không cung cấp nguyên tắc đã duyệt. Chưa dùng nội dung cuộc trò chuyện được nguồn liên kết vì chưa được cung cấp.

