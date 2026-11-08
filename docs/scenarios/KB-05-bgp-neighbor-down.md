# KB-05 BGP Neighbor Down

**Phiên bản:** 1.2 · **QA đặc tả/chạy tích hợp:** Ngô Châu Kiệt — QA Lead · **Code owner theo module:** BE2 Phạm Tấn Thành (parser/vendor scope chờ quyết định tại N42-62); Nguyễn Duy Minh — BE3 (rule N42-65, Sprint 4; To Do, chưa estimate). · **Trạng thái:** Đặc tả; chưa chạy; BLOCKED chờ quyết định parser/vendor và xác nhận retry/window · **Liên kết:** N42-62; N42-65; TC-COR-009; AC-05; FR-09

## Phân công theo vai trò

- **Code implementation:** BE2 Phạm Tấn Thành xác nhận parser/vendor scope qua N42-62; chưa coi Juniper/BGP parser là scope được duyệt. Nguyễn Duy Minh — BE3 triển khai rule theo N42-65 ở Sprint 4 sau khi threshold, retry semantics và time window được xác nhận. `N42-65` đang `To Do`, chưa estimate. Mỗi BE/FE tự viết và chạy unit/component test cho phần code mình phụ trách, ghi commit và evidence trên Jira.
- **Chuẩn bị fixture, test case, chạy tích hợp/replay và lưu evidence:** Ngô Châu Kiệt — QA Lead; QA xác nhận kết quả sau khi dependencies sẵn sàng, không thay BE/FE viết logic nghiệp vụ.
- **Điều phối tài liệu và quyết định:** Phạm Minh Nhựt — TL/PM ghi nhận scope/acceptance đã được chủ yêu cầu và code owner xác nhận; không tự chốt contract, ngưỡng hoặc semantics kỹ thuật.
- **Lưu ý giao việc:** đây là owner theo phân công module trong tài liệu dự án, không khẳng định Jira đã gán ticket; TL cần đối chiếu Jira trước khi bắt đầu. Không tự ghi PASS khi chưa chạy và có evidence.


> **Hiện trạng baseline:** repo hiện chưa có pipeline nghiệp vụ tương ứng với kịch bản này; đây là đặc tả, không phải báo cáo chạy. Trạng thái thực thi hiện tại: `BLOCKED / NOT RUN`. Chỉ bỏ Blocked khi code/dependency và contract nêu trong case đã sẵn sàng.

> **Đối chiếu Jira (09/11/2026):** xem ticket được nêu tại phần phân công; trạng thái Jira là ảnh chụp tại ngày này, không tự đồng bộ khi ticket đổi trạng thái. Ticket đang `To Do`/`In Progress` không có nghĩa code đã xong.

## Mục tiêu
Xác nhận cảnh báo BGP peer down được parse và tương liên kết theo retry threshold đã phê duyệt.

## Tiền điều kiện và reset
Dùng peer giả lập trong `10.10.0.0/16`. Rule version phải ghi rõ số lần retry và time window; kịch bản mặc định kiểm tra ngưỡng 3 lần như Test Case Specification.

## Dữ liệu đầu vào
Seed `KB-05-v1`; ba cảnh báo `BGP_PEER_DOWN` cho cùng hostname và peer `10.10.0.2`, timestamps tăng dần trong cửa sổ của rule; biến thể âm dùng hai cảnh báo.

## Kết quả mong đợi
Hai cảnh báo không vượt ngưỡng; lần thứ ba tạo hoặc cập nhật đúng một incident và lưu cả ba event IDs, peer và rule version. Nếu retry semantics/window chưa được BE3 xác nhận và ghi vào contract/decision, case BLOCKED; TL chỉ cập nhật hồ sơ sau khi owner thống nhất.

## Thực hiện và evidence
Lưu config, event IDs, trigger time, incident/evidence IDs, TP/FP/FN và log.


