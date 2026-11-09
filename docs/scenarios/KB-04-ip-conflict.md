# KB-04 IP Conflict

**Phiên bản:** 1.2 · **QA đặc tả/chạy tích hợp:** Ngô Châu Kiệt — QA Lead · **Code owner theo module:** Phạm Hoàng Long — BE1 (Cisco IOS/Nexus parser N42-23; To Do); Nguyễn Duy Minh — BE3 (rule N42-64, Sprint 4; To Do, chưa estimate; grouping dependency N42-18). · **Trạng thái:** Đặc tả; chưa chạy; BLOCKED chờ implementation/contract và xác nhận semantics · **Liên kết:** N42-64; TC-PAR-003; TC-COR-005/006; AC-02; FR-04/FR-09

## Phân công theo vai trò

- **Code implementation:** Phạm Hoàng Long — BE1 (Cisco IOS/Nexus parser N42-23); Nguyễn Duy Minh — BE3 (rule N42-64 ở Sprint 4; grouping dependency N42-18). `N42-64` đang `To Do` và chưa estimate; ngưỡng/grouping semantics cần owner xác nhận trước khi implementation sẵn sàng. Mỗi BE/FE tự viết và chạy unit/component test cho phần code mình phụ trách, ghi commit và evidence trên Jira.
- **Chuẩn bị fixture, test case, chạy tích hợp/replay và lưu evidence:** Ngô Châu Kiệt — QA Lead; QA xác nhận kết quả sau khi dependencies sẵn sàng, không thay BE/FE viết logic nghiệp vụ.
- **Điều phối tài liệu và quyết định:** Phạm Minh Nhựt — TL/PM ghi nhận scope/acceptance đã được chủ yêu cầu và code owner xác nhận; không tự chốt contract, ngưỡng hoặc semantics kỹ thuật.
- **Lưu ý giao việc:** đây là owner theo phân công module trong tài liệu dự án, không khẳng định Jira đã gán ticket; TL cần đối chiếu Jira trước khi bắt đầu. Không tự ghi PASS khi chưa chạy và có evidence.


> **Hiện trạng baseline:** repo hiện chưa có pipeline nghiệp vụ tương ứng với kịch bản này; đây là đặc tả, không phải báo cáo chạy. Trạng thái thực thi hiện tại: `BLOCKED / NOT RUN`. Chỉ bỏ Blocked khi code/dependency và contract nêu trong case đã sẵn sàng.

> **Đối chiếu Jira (09/11/2026):** xem ticket được nêu tại phần phân công; trạng thái Jira là ảnh chụp tại ngày này, không tự đồng bộ khi ticket đổi trạng thái. Ticket đang `To Do`/`In Progress` không có nghĩa code đã xong.

## Mục tiêu
Kiểm tra parser trích xuất chính xác địa chỉ trùng, VLAN/interface và MAC từ cảnh báo Cisco Nexus.

## Tiền điều kiện và reset
Dùng fixture tổng hợp; địa chỉ mạng nằm trong RFC1918. Chuẩn bị hai fixture khác VLAN để bảo đảm grouping key không làm trộn sự kiện.

## Dữ liệu đầu vào
Seed `KB-04-v1`; `<132>2026-11-06T15:04:00+07:00 nexus-dc-01 %IP-4-DUPADDR: Duplicate address 10.10.5.100 on Vlan100, sourced by aabb.ccdd.1234`. Biến thể thứ hai đổi VLAN và MAC.

## Kết quả mong đợi
Normalized event giữ IP `10.10.5.100`, VLAN `Vlan100`, MAC `aabb.ccdd.1234`, raw message và source time. Hai VLAN khác nhau không bị gộp nếu grouping contract phân biệt interface/VLAN. Không có remediation hoặc thao tác thiết bị.

## Thực hiện và evidence
Lưu fixture hash, expected/actual field diff, event IDs, grouping key, parser version và log.


