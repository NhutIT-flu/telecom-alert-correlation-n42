# Nhật ký quyết định kỹ thuật (Decision Log)

> Theo Quy định vận hành nhóm mục D.4: mọi quyết định ghi trong ngày ra quyết định.  
> Khung: Hoàn cảnh - Các phương án - Quyết định - Người quyết - Ngày.  

| # | Ngày | Hoàn cảnh | Các phương án xét | Quyết định | Người quyết |
|---|------|-----------|-------------------|-----------|-------------|
| 1 | 29/10/2026 | Stack chính (mục 1.5 bản đề xuất) | Java/Spring vs Python (FastAPI) + React | Đã chốt: Python (FastAPI + asyncio + Pydantic + TimescaleDB) + React (Vite) | Cả nhóm + Trưởng nhóm |
| 2 | 29/10/2026 | Port syslog lab | 514 (cần root) / 5514 | 5514 (lab an toàn, cấu hình được) | Trưởng nhóm |
| 3 | 30/10/2026 | Lưu trữ giai đoạn đầu | In-memory / TimescaleDB ngay | In-memory W1-W4, chuyển TimescaleDB W5-W6 | Trưởng nhóm |
| 4 | 31/10/2026 | Bộ parser định dạng đầu tiên | Cisco / Huawei / Linux rsyslog | Chốt parser đa vendor: Cisco IOS/Nexus, Huawei NE40E/VRP, Fortinet | BE2 + Trưởng nhóm |
| 5 | 03/11/2026 | Tái cơ cấu phân vai nhóm N4.2 để tối ưu hóa quản trị & vận hành | Giữ nguyên cơ cấu cũ vs Tái cơ cấu theo năng lực thế mạnh | **Chính thức:**<br>1. **Phạm Minh Nhựt**: Đảm nhiệm **Team Leader / PM & Quản trị Jira, Confluence, Quy trình**.<br>2. **Nguyễn Duy Minh**: Đảm nhiệm **Backend Engineer 3 (BE3)** phụ trách M5/M6.<br>3. **Ngô Châu Kiệt**: Đảm nhiệm **QA Lead** phụ trách M8 (Test Tooling, Đo kiểm 1.000 msg/s). | Cả nhóm thống nhất |
| 6 | 03/11/2026 | Cần một baseline chung cho lịch, KPI và báo cáo nghiệm thu | Giữ các cách ghi rời rạc vs hợp nhất tiêu chí hiện có | **Baseline tài liệu:** W1=01–07/11; W2=08–14/11; Daily trước 18:00, leader tổng hợp 19:00–19:15; W12 là checkpoint luật 70%; W13 nghiệm thu luật ≥90% và tải ≥1.000 msg/s trong 1 giờ. Chi tiết ở `ACCEPTANCE_CRITERIA.md`. | Team Leader + QA Lead |

| 7 | 07/11/2026 | Rà soát trạng thái CI theo ảnh cây thư mục và xác nhận của chủ dự án | Ghi workflow như hiện hành vs phân biệt cấu trúc dự kiến và trạng thái repo | Repo hiện chưa có `.github/workflows/ci.yml`; cây thư mục trong ảnh là cấu trúc dự kiến. QA Lead sẽ triển khai pipeline; tài liệu chỉ ghi CI hoạt động sau khi có YAML và run evidence. Required checks/branch protection phải xác minh riêng. | Chủ dự án xác nhận |
| 8 | 09/11/2026 | Năm đầu việc thiếu trong Jira cần được lên lịch theo dependency và checkpoint | Giữ toàn bộ ở backlog vs xếp provisional để làm rõ thứ tự phụ thuộc | Xếp `N42-62` vào S1 vì chặn `N42-14`; `N42-64/65/66` vào S4 để còn thời gian tích hợp/kiểm chứng trước W12; `N42-63` vào S6 sau `N42-34` (S3) và `N42-46` (S5). Đây là kế hoạch tạm: tất cả vẫn `To Do`, chưa estimate; trước khi cam kết, team phải refinement và đánh giá lại capacity. Không đổi status/estimate hoặc tự xác nhận hoàn thành. | Team Leader; chờ team refinement |

## Mẫu thêm dòng mới

| # | Ngày | Hoàn cảnh | Các phương án xét | Quyết định | Người quyết |
|---|------|-----------|-------------------|-----------|-------------|
|   |      |           |                   |           |             |
