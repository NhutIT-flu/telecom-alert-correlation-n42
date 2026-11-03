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

## Mẫu thêm dòng mới

| # | Ngày | Hoàn cảnh | Các phương án xét | Quyết định | Người quyết |
|---|------|-----------|-------------------|-----------|-------------|
|   |      |           |                   |           |             |
