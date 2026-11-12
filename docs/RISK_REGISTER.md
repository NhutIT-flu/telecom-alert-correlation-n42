# Sổ rủi ro dự án N4.2

**Chủ sở hữu sổ:** Team Leader · **Rà soát:** họp tuần và trước các mốc W4/W6/W8/W12/W13

| ID | Rủi ro | Xác suất / ảnh hưởng | Dấu hiệu kích hoạt | Giảm thiểu / phương án dự phòng | Chủ trì |
|---|---|---|---|---|---|
| R-01 | Parser vendor lệch mẫu thực tế | Trung bình / Cao | Bộ test có trường bắt buộc sai hoặc tỷ lệ parse giảm | Chốt fixture có nhãn; thêm test theo vendor; giữ nguồn/format ưu tiên nếu scope đổi | BE2 |
| R-02 | Pipeline không đạt 1.000 msg/s | Trung bình / Cao | Checkpoint tải có drop hoặc latency vượt ngưỡng | Benchmark sớm; tách đo ingest khỏi persistence; lưu cấu hình máy và profile tải; báo TL trước W12 | BE1 + QA |
| R-03 | Kết quả tải không tái lập | Trung bình / Cao | Thiếu event ID, duration, cấu hình hoặc đối soát sent/received | QA chuẩn hóa lệnh chạy, dữ liệu và mẫu báo cáo; không ghi Pass nếu thiếu | QA |
| R-04 | Luật tương quan không đạt checkpoint W12 | Trung bình / Cao | Detection <70% hoặc FP cao trên bộ đã gắn nhãn | BE3 và QA rà từng KB; W12 TL chốt scope bằng decision log; giữ tiêu chí W13 đã duyệt | BE3 + QA + TL |
| R-05 | Hợp đồng API lệch giữa BE và FE | Trung bình / Trung bình | Frontend phải sửa adapter ngoài kế hoạch | Chốt OpenAPI v1.0 tại W8; thay đổi có version, mock và TL duyệt trước merge | BE2 + FE |
| R-06 | Báo cáo tiến độ nhầm checkpoint là nghiệm thu | Trung bình / Cao | Kết quả dưới KPI bị ghi Pass hoặc thiếu thời lượng đo | Áp dụng `ACCEPTANCE_CRITERIA.md`; tách trạng thái thử nghiệm, checkpoint và nghiệm thu | TL + QA |
| R-07 | Tài liệu dẫn xuất giữ cơ cấu cũ | Cao / Cao | Có bản ghi Duy Minh là TL hoặc Kiệt là BE3 sau 03/11 | Document control; cập nhật nguồn sinh và PDF/DOCX cùng đợt; đánh dấu bản cũ superseded | TL |
| R-08 | Trễ mốc do phụ thuộc chéo hoặc nghỉ thành viên | Trung bình / Cao | Thẻ quan trọng treo >3 ngày hoặc handoff trễ | Mỗi module có owner/reviewer; chia nhỏ và bàn giao; TL cập nhật forecast, báo PM nếu ảnh hưởng mốc | TL |
| R-09 | Dữ liệu/credential thật lọt vào repo | Thấp / Cao | Secret scanner hoặc review phát hiện dữ liệu nhạy cảm | Chỉ dùng dữ liệu giả lập/public đã duyệt; cách ly và báo TL; thu hồi credential nếu có | QA + TL |
| R-10 | Đóng băng W13 nhưng còn lỗi nghiệm thu | Trung bình / Cao | Critical test fail ở W12 hoặc không có máy sạch rehearsal | Rehearsal trước W13; khóa scope; phân loại lỗi chặn/không chặn; W16-W18 xử lý lỗi và bàn giao | TL + QA |

## 1. Cách vận hành

Mỗi rủi ro mới phải có owner, tín hiệu đo được, ngày rà soát và phương án. TL cập nhật sau cuộc họp tuần; vấn đề đã xảy ra chuyển thành issue Jira nhưng vẫn giữ liên kết R-ID để theo dõi nguyên nhân và phòng ngừa tái diễn.
