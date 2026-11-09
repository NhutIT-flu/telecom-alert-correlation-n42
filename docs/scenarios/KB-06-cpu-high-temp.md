# KB-06 CPU High Temperature

**Phiên bản:** 1.2 · **QA đặc tả/chạy tích hợp:** Ngô Châu Kiệt — QA Lead · **Code owner theo module:** Phạm Tấn Thành — BE2 (Huawei parser N42-24); Nguyễn Duy Minh — BE3 (rule N42-66, Sprint 4; To Do, chưa estimate). · **Trạng thái:** Đặc tả; chưa chạy; BLOCKED chờ implementation và xác nhận comparator/severity · **Liên kết:** N42-66; N42-24; TC-PAR-005; AC-02/AC-04; FR-04/FR-11

## Phân công theo vai trò

- **Code implementation:** BE2 Phạm Tấn Thành xác nhận parser/mapping theo N42-24; Nguyễn Duy Minh — BE3 triển khai rule theo N42-66 ở Sprint 4 sau khi comparator, threshold và severity được xác nhận. `N42-66` đang `To Do`, chưa estimate. FE chỉ tham gia nếu UI/API của case được đưa vào scope; dashboard chưa được coi là khả năng hiện có. Mỗi owner tự viết và chạy unit/component test cho phần code mình phụ trách, ghi commit và evidence trên Jira.
- **Chuẩn bị fixture, test case, chạy tích hợp/replay và lưu evidence:** Ngô Châu Kiệt — QA Lead; QA xác nhận kết quả sau khi dependencies sẵn sàng, không thay BE/FE viết logic nghiệp vụ.
- **Điều phối tài liệu và quyết định:** Phạm Minh Nhựt — TL/PM ghi nhận scope/acceptance đã được chủ yêu cầu và code owner xác nhận; không tự chốt contract, ngưỡng hoặc semantics kỹ thuật.
- **Lưu ý giao việc:** đây là owner theo phân công module trong tài liệu dự án, không khẳng định Jira đã gán ticket; TL cần đối chiếu Jira trước khi bắt đầu. Không tự ghi PASS khi chưa chạy và có evidence.


> **Hiện trạng baseline:** repo hiện chưa có pipeline nghiệp vụ tương ứng với kịch bản này; đây là đặc tả, không phải báo cáo chạy. Trạng thái thực thi hiện tại: `BLOCKED / NOT RUN`. Chỉ bỏ Blocked khi code/dependency và contract nêu trong case đã sẵn sàng.

> **Đối chiếu Jira (09/11/2026):** xem ticket được nêu tại phần phân công; trạng thái Jira là ảnh chụp tại ngày này, không tự đồng bộ khi ticket đổi trạng thái. Ticket đang `To Do`/`In Progress` không có nghĩa code đã xong.

## Mục tiêu
Kiểm tra parse cảnh báo nhiệt độ cao, giữ số đo/ngưỡng và biểu diễn severity nhất quán.

## Tiền điều kiện và reset
Dùng Huawei S5700 giả lập; mapping vendor/severity phải có trong parser fixture đã duyệt. Dashboard/WebSocket là target và chưa được xem là khả năng hiện có.

## Dữ liệu đầu vào
Seed `KB-06-v1`; `<131>Nov 06 15:23:00 s5700-01 %%01DEVM/2/CPU_TEMP_ALARM: CPU temperature reached 85 C, threshold 80 C.`

## Kết quả mong đợi
Parser trích xuất temperature=85, threshold=80, severity `MAJOR`, giữ raw và timestamp policy. Sau khi UI/API được triển khai, hiển thị event theo contract; trước đó chỉ kiểm tra phần backend có trong ticket.

## Thực hiện và evidence
Lưu parser version, expected/actual, event ID, UI/API build nếu áp dụng và log.


