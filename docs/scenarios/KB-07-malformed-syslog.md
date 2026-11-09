# KB-07 Malformed Syslog

**Phiên bản:** 1.1 · **QA đặc tả/chạy tích hợp:** Ngô Châu Kiệt — QA Lead · **Code owner theo module (dự kiến):** Phạm Hoàng Long — BE1 (receiver N42-13; To Do); BE2 Phạm Tấn Thành theo module parser/schema. Chưa đối chiếu được ticket Jira riêng cho case malformed trên board hiện tại. · **Trạng thái:** Đặc tả; chưa chạy; BLOCKED chờ implementation/contract · **Liên kết:** TC-ING-003/005; TC-PAR-010/011; AC-02; FR-01/FR-05

## Phân công theo vai trò

- **Code implementation:** Phạm Hoàng Long — BE1 (receiver N42-13; To Do); BE2 Phạm Tấn Thành theo module parser/schema. Chưa đối chiếu được ticket Jira riêng cho case malformed trên board hiện tại. Mỗi BE/FE tự viết và chạy unit/component test cho phần code mình phụ trách, ghi commit và evidence trên Jira.
- **Chuẩn bị fixture, test case, chạy tích hợp/replay và lưu evidence:** Ngô Châu Kiệt — QA Lead; QA xác nhận kết quả sau khi dependencies sẵn sàng, không thay BE/FE viết logic nghiệp vụ.
- **Điều phối tài liệu và quyết định:** Phạm Minh Nhựt — TL/PM ghi nhận scope/acceptance đã được chủ yêu cầu và code owner xác nhận; không tự chốt contract, ngưỡng hoặc semantics kỹ thuật.
- **Lưu ý giao việc:** đây là owner theo phân công module trong tài liệu dự án, không khẳng định Jira đã gán ticket; TL cần đối chiếu Jira trước khi bắt đầu. Không tự ghi PASS khi chưa chạy và có evidence.


> **Hiện trạng baseline:** repo hiện chưa có pipeline nghiệp vụ tương ứng với kịch bản này; đây là đặc tả, không phải báo cáo chạy. Trạng thái thực thi hiện tại: `BLOCKED / NOT RUN`. Chỉ bỏ Blocked khi code/dependency và contract nêu trong case đã sẵn sàng.

> **Đối chiếu Jira (09/11/2026):** xem ticket được nêu tại phần phân công; trạng thái Jira là ảnh chụp tại ngày này, không tự đồng bộ khi ticket đổi trạng thái. Ticket đang `To Do`/`In Progress` không có nghĩa code đã xong.

## Mục tiêu
Đảm bảo payload rỗng, quá cỡ hoặc sai header được xử lý an toàn, không làm dừng receiver và không bị diễn giải thành dữ liệu hợp lệ.

## Tiền điều kiện và reset
Chạy trên loopback/lab cách ly; giới hạn payload lấy từ contract được duyệt. Dùng run ID riêng và theo dõi process/queue/error counter.

## Dữ liệu đầu vào
Seed `KB-07-v1`; các nhóm input: 0 byte, 1 byte không phải syslog, header thiếu PRI, bytes không decode được, payload bằng giới hạn, payload vượt giới hạn 1 byte.

## Kết quả mong đợi
Không crash; input hợp lệ theo kích thước nhưng không parse được phải giữ raw và đánh dấu parse failure/UNKNOWN theo contract. Input vượt giới hạn phải bị từ chối/drop có counter; không ACK thành công nếu chưa đạt semantics đã chốt.

## Thực hiện và evidence
Lưu kích thước/hex fixture, response/counter, process health, raw/event IDs, giới hạn cấu hình và log.


