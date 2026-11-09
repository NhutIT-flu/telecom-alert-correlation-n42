# KB-01 Link Flap

**Phiên bản:** 1.1 · **QA đặc tả/chạy tích hợp:** Ngô Châu Kiệt — QA Lead · **Code owner theo module (dự kiến):** Nguyễn Duy Minh — BE3 (rule, grouping, incident/dedup); Phạm Hoàng Long — BE1 (Cisco IOS/Nexus parser, Jira N42-23; currently To Do); BE2 Phạm Tấn Thành (AlertEvent schema dependency, N42-15; To Do) · **Trạng thái:** Đặc tả; chưa chạy; BLOCKED chờ implementation/contract · **Liên kết:** TC-COR-001–004; AC-05/AC-06; FR-09

## Phân công theo vai trò

- **Code implementation:** Nguyễn Duy Minh — BE3 (rule, grouping, incident/dedup); Phạm Hoàng Long — BE1 (Cisco IOS/Nexus parser, Jira N42-23; currently To Do); BE2 Phạm Tấn Thành (AlertEvent schema dependency, N42-15; To Do). Mỗi BE/FE tự viết và chạy unit/component test cho phần code mình phụ trách, ghi commit và evidence trên Jira.
- **Chuẩn bị fixture, test case, chạy tích hợp/replay và lưu evidence:** Ngô Châu Kiệt — QA Lead; QA xác nhận kết quả sau khi dependencies sẵn sàng, không thay BE/FE viết logic nghiệp vụ.
- **Điều phối tài liệu và quyết định:** Phạm Minh Nhựt — TL/PM ghi nhận scope/acceptance đã được chủ yêu cầu và code owner xác nhận; không tự chốt contract, ngưỡng hoặc semantics kỹ thuật.
- **Lưu ý giao việc:** đây là owner theo phân công module trong tài liệu dự án, không khẳng định Jira đã gán ticket; TL cần đối chiếu Jira trước khi bắt đầu. Không tự ghi PASS khi chưa chạy và có evidence.


> **Hiện trạng baseline:** repo hiện chưa có pipeline nghiệp vụ tương ứng với kịch bản này; đây là đặc tả, không phải báo cáo chạy. Trạng thái thực thi hiện tại: `BLOCKED / NOT RUN`. Chỉ bỏ Blocked khi code/dependency và contract nêu trong case đã sẵn sàng.

> **Đối chiếu Jira (09/11/2026):** xem ticket được nêu tại phần phân công; trạng thái Jira là ảnh chụp tại ngày này, không tự đồng bộ khi ticket đổi trạng thái. Ticket đang `To Do`/`In Progress` không có nghĩa code đã xong.

## Mục tiêu
Xác nhận chuỗi thay đổi trạng thái của cùng thiết bị/giao diện được gom theo đúng cửa sổ thời gian và ngưỡng.

## Tiền điều kiện và reset
Dùng rule version đã được duyệt, có `threshold_count=5`, `window_seconds=60` theo AC. Xóa dữ liệu thử hoặc dùng `run_id` riêng; đồng hồ và múi giờ được ghi nhận.

## Dữ liệu đầu vào
Seed cố định `KB-01-v1`; thiết bị giả lập `10.10.1.10`, interface `Gi0/1`. Gửi 5 event UP/DOWN xen kẽ tại T+0, 10, 20, 30, 40 giây. Biến thể biên: chỉ 4 event; biến thể ngoài cửa sổ: event thứ 5 tại T+61 giây.

## Kết quả mong đợi
Chuỗi 5 event trong cửa sổ tạo đúng một incident, liên kết đủ 5 event IDs và lưu rule version/evidence. Bốn event không tạo incident; event ở giây 61 không bị gộp vào cửa sổ đã hết hạn.

## Thực hiện và evidence
Replay theo seed; lưu rule/config hash, sent/accepted/persisted IDs, incident ID, matched event IDs, timestamps và log. Ghi PASS chỉ khi có run record gắn commit/môi trường.


