# Tiêu chí nghiệm thu dự án N4.2

**Baseline:** 03/11/2026 · **Áp dụng:** W13 nghiệm thu sản phẩm; các lần đo trước là checkpoint · **Chủ trì:** Team Leader và QA Lead

Khách hàng yêu cầu ít nhất hai nguồn hoặc định dạng mẫu, hoặc hai loại thiết bị giả lập. AC-01 theo dõi UDP, REST và file trong kế hoạch nội bộ. Chỉ tiêu định lượng dùng khi nghiệm thu khách hàng cần UTH và mentor VNPT xác nhận sau khi đo baseline.

## 1. Phạm vi nghiệm thu

Đây là dự án doanh nghiệp UTH × VNPT NET nhằm xây dựng giải pháp hỗ trợ quy trình giám sát và phân tích cảnh báo mạng. Các tiêu chí dưới đây nghiệm thu phiên bản phát triển/kiểm chứng trong lab bằng dữ liệu giả lập; tích hợp production cần VNPT thẩm định và phê duyệt riêng. Sản phẩm nhận cảnh báo từ syslog, file và API; chuẩn hóa, lưu, truy vấn/thống kê, gom nhóm và tương quan, rồi hiển thị trên dashboard. Cơ cấu vai trò chuẩn nằm trong `DOCUMENT_CONTROL.md`.

## 2. Tiêu chí chức năng

| Mã | Tiêu chí pass | Bằng chứng tối thiểu | Chủ trì |
|---|---|---|---|
| AC-01 | Ba nguồn trong baseline SRS — syslog UDP, REST ingest và file import — đưa được sự kiện qua pipeline tới điểm lưu đã chốt. Nếu nguồn nào bị loại khỏi release, cần có quyết định phạm vi được ghi nhận; không tự thay UDP bằng TCP | Bộ dữ liệu có mã định danh; log gửi/nhận; kết quả kiểm tra từng nguồn và persistence outcome | BE1 + QA |
| AC-02 | Parser chuẩn hóa đúng 100% trên corpus có nhãn, tối thiểu 200 mẫu cho mỗi định dạng/vendor trong scope; ghi nhận format và nguồn phát của từng mẫu | Corpus version/hash, expected/actual từng field, tổng đúng/sai, mẫu lỗi | BE2 + QA |
| AC-03 | Truy vấn/lọc theo thời gian, thiết bị, mức độ; truy vấn chuẩn trả kết quả dưới 2 giây với bộ dữ liệu 1 triệu sự kiện trong môi trường được ghi rõ | Kịch bản truy vấn, số bản ghi, thời gian chạy, cấu hình máy | BE2 + QA |
| AC-04 | Dashboard hiển thị dòng sự kiện, KPI, sự cố gom nhóm và chi tiết cảnh báo con; xuất báo cáo theo chức năng đã chốt | Video/demo, checklist UI, file xuất | FE + QA |
| AC-05 | Có tối thiểu 5 luật tương quan; tại W12 đạt checkpoint ít nhất 70%; tại nghiệm thu W13 phát hiện đúng ít nhất 90% trường hợp dương tính trong bộ kiểm thử đã gắn nhãn; báo cáo FP và FN riêng | Phiên bản bộ luật và kịch bản, counts TP/FP/FN, kết quả từng KB | BE3 + QA |
| AC-06 | Với kịch bản bão cảnh báo, giảm ít nhất 70% số mục hiển thị; tỷ lệ tính theo công thức ở mục 3 | Số raw event, incident, standalone event trước/sau gom | BE3 + QA |
| AC-07 | Cài lại trên máy sạch trong tối đa 1 giờ từ bộ bàn giao và chạy được các luồng demo | Video có thời gian, phiên bản, cấu hình và log | QA + BE1 |
| AC-08 | Không có credential thật/hardcode và không có IP thiết bị thật; hệ thống chỉ đọc/nhận log | Kết quả secret scan, rà soát cấu hình/dữ liệu | QA + TL |

**Phạm vi nguồn:** baseline theo SRS gồm UDP, REST và file. TCP xuất hiện trong vai trò QA/hợp đồng đề xuất nhưng chưa có FR riêng; cần decision/Jira trước khi đưa TCP vào nghiệm thu.

## 3. Định nghĩa và cách tính

- **Bài tải trung gian:** mốc 200/500/1.000 msg/s; mỗi lần kiểm tra danh định tối thiểu 10 phút.
- **Bài nghiệm thu tải W13:** giữ ít nhất 1.000 msg/s trong 1 giờ liên tục. Pass khi số gửi/nhận đối soát được theo ID, tỷ lệ mất gói quan sát được là 0.00%, P50 < 50 ms, P99 < 200 ms, CPU ≤ 60% trên 4 core và RAM ≤ 1.5 GB. Ghi rõ máy, phiên bản, cấu hình, số gửi/nhận và công cụ đo. Spike 1.500 msg/s trong 2 phút là bài stress riêng, không thay bài danh định.
- **Tỷ lệ phát hiện:** `TP / (TP + FN) × 100%` trên các trường hợp dương tính đã gắn nhãn. Báo cáo FP riêng; không gọi detection rate là accuracy.
- **Tỷ lệ giảm nhiễu:** `(N_raw − (N_incidents + N_unassigned)) / N_raw × 100%`, trong đó incidents và unassigned là các mục còn hiển thị sau xử lý. Không tính event con đã ẩn như một mục hiển thị. Nếu `N_raw = 0`, kết quả là `N/A`, không tính là 100%.
- **Link Flap:** ít nhất 5 chuyển trạng thái UP/DOWN trên cùng thiết bị và giao diện trong cửa sổ trượt 60 giây tạo một incident gốc.
- **Địa chỉ giả lập:** `10.10.0.0/16` dùng cho mạng lab riêng; `203.0.113.0/24` chỉ dùng làm địa chỉ ví dụ tài liệu. Không gọi toàn bộ dải `10.10.x.x` là TEST-NET.

## 4. Quy tắc checkpoint và kết luận

W12 là cổng quyết định phạm vi: dưới 70% thì TL ghi quyết định thu hẹp, cập nhật Jira, rủi ro và báo PM; không tự hạ tiêu chí nghiệm thu cuối. W13 chỉ ghi **Pass** khi đủ AC-01–AC-08 hoặc có ngoại lệ được PM chấp thuận bằng văn bản. Mọi báo cáo phải nêu kết quả đo thực tế, không làm tròn kết quả dưới KPI thành đạt.
