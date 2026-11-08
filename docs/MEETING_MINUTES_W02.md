# Biên bản dự kiến cuộc họp khởi động N4.2

**Mã tài liệu:** MEET-N42-KICKOFF · **Tuần dự kiến:** W2 · **Thời gian dự kiến:** 09:00–11:30, 09/11/2026 · **Chủ trì dự kiến:** Phạm Minh Nhựt · **Thư ký dự kiến:** Ngô Châu Kiệt

**Trạng thái:** DỰ THẢO chương trình họp. Cuộc họp chưa diễn ra tại thời điểm lập bản này. Không dùng nội dung bên dưới làm biên bản đã họp, quyết định đã thông qua hoặc xác nhận tham dự. Thư ký chỉ hoàn tất ngày/giờ thực tế, người tham dự, quyết định, action owner và chữ ký sau cuộc họp.

## 1. Mục tiêu

Xác nhận mục tiêu đề tài, phạm vi lab, vai trò và cách phối hợp; thống nhất các vấn đề cần xin mentor/PM duyệt; lập action log có owner và hạn. Kickoff ngày 09/11 thuộc W2 (08–14/11), không thuộc W1.

## 2. Chương trình dự kiến

| Thời lượng | Nội dung | Kết quả cần ghi nhận | Trạng thái |
|---|---|---|---|
| 10 phút | Mục tiêu, giới hạn lab và quan hệ với quy trình HKDN | Phạm vi được xác nhận hoặc câu hỏi còn mở | Chưa diễn ra |
| 15 phút | Vai trò và RACI | Owner/approver, nội dung cần sửa | Chưa diễn ra |
| 20 phút | Stack, kiến trúc và dữ liệu | Lựa chọn đã duyệt, người quyết, ngày | Chưa diễn ra |
| 15 phút | Test Case Specification, RTM và DoR trước code | QA chủ trì; owner BE/FE xác nhận; ticket gate | Chưa diễn ra |
| 15 phút | Lịch W1–W18, checkpoint và báo cáo | Baseline timeline; rủi ro/mốc phụ thuộc | Chưa diễn ra |
| 15 phút | Git, Jira, PR, review và CI | Xác nhận kế hoạch QA triển khai CI, checks cần có và cách lưu run evidence; required checks/branch protection là việc xác minh riêng | Chưa diễn ra |
| 10 phút | Action log và kết thúc | Owner, due date, bằng chứng/biên bản | Chưa diễn ra |

## 3. Các điểm cần xác nhận

- Kênh baseline: syslog UDP, REST ingest và file. TCP syslog chỉ đưa vào scope nếu có quyết định phạm vi, cập nhật SRS/AC/RTM và Jira.
- Hợp đồng `AlertEvent`, lưu trữ, policy lỗi và API là các quyết định cần ghi rõ trạng thái; không ghi “đã chốt” trước khi nhóm xác nhận.
- M8/QA Lead chịu trách nhiệm đặc tả test/coverage, CI/workflow, tích hợp và evidence; owner BE/FE xác nhận kết quả kỳ vọng và viết unit test module mình. TL điều phối và chịu trách nhiệm phê duyệt quy trình.
- W12 ≥70% là checkpoint; W13 ≥90% detection trên 8–10 scenario và ≥1.000 msg/s trong 1 giờ là mục tiêu nghiệm thu, không phải kết quả hiện tại.

## 4. Hồ sơ sau họp

| Trường | Điền sau cuộc họp |
|---|---|
| Thời gian thực tế | Chưa ghi nhận |
| Người tham dự | Chưa ghi nhận |
| Quyết định và người quyết | Chưa ghi nhận |
| Action / owner / hạn | Chưa ghi nhận |
| Jira/Decision Log link | Chưa ghi nhận |
| Xác nhận thư ký / chủ trì | Chờ xác nhận sau họp |
