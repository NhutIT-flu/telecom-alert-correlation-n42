# CỔNG THÔNG TIN & ĐIỀU LỆ DỰ ÁN N4.2 (PROJECT CHARTER)

> **Mã dự án:** `VNPT-NET-UTH-2026-N4.2`  
> **Cơ quan bảo trợ & hướng dẫn:** Trung tâm Điều hành Khai thác Mạng — VNPT NET  
> **Cơ sở đào tạo:** Trường ĐH Giao thông Vận tải TP.HCM (UTH) — Học kỳ Doanh nghiệp HK26  
> **Mốc sống còn:** **CODE FREEZE 30/01/2027 (W13 - Trước Tết Nguyên Đán)**  
> **Team Leader / PM & Quản trị:** **Phạm Minh Nhựt**  
> **Trạng thái:** BASELINE NỘI BỘ CỦA NHÓM — chưa có xác nhận/phê duyệt từ Cố vấn VNPT NET  

---

## 1. TỔNG QUAN & BỐI CẢNH BÀI TOÁN NOC (MÔ PHỎNG)

- **Bài toán mô phỏng:** Log nhiều định dạng và cảnh báo lặp làm việc tra cứu, phân nhóm và đánh giá mối liên hệ khó hơn.
- **Bối cảnh dự án:** Đây là dự án doanh nghiệp phối hợp UTH × VNPT NET, hướng tới hỗ trợ công tác giám sát và phân tích cảnh báo trong quy trình NOC. Các vấn đề nêu trên là bài toán mục tiêu; không xem là kết quả khảo sát hoặc số liệu vận hành nội bộ nếu chưa có nguồn xác nhận từ VNPT.
- **Mục tiêu N4.2:** Xây dựng và kiểm chứng giải pháp thu thập, chuẩn hóa, lưu/truy vấn, tương quan cảnh báo và dashboard. Giai đoạn hiện tại dùng dữ liệu giả lập trong lab; tích hợp production cần VNPT thẩm định/phê duyệt. Throughput, detection và giảm nhiễu theo `ACCEPTANCE_CRITERIA.md`.

---

## 2. MA TRẬN TRÁCH NHIỆM RACI (TÁI CƠ CẤU 6 THÀNH VIÊN)

| Module / Nhiệm vụ | Nhựt (Team Lead / PM) | Minh (BE3) | Kiệt (QA Lead) | Long (BE1) | Thành (BE2) | Huy (FE) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Quản trị dự án, Jira, Confluence, Báo cáo HKDN** | **A / R** | I | I | I | I | I |
| M1: Syslog Ingestion (UDP 5514) | C | C | C | **A / R** | C | I |
| M2: Multi-Vendor Parser Engine | C | C | C | **A / R** | C | I |
| M3: Queue Buffer In-Memory | C | C | I | C | **A / R** | I |
| M4: TimescaleDB Hypertable DDL | C | C | I | I | **A / R** | I |
| M5: Cấu hình Luật tương quan (`rules.yaml`) | C | **A / R** | I | I | C | I |
| M6: Correlation Engine & API | C | **A / R** | C | I | C | C |
| M7: Web Dashboard React (NOC Dark Mode) | C | I | C | I | I | **A / R** |
| M8: QA Tooling, Đo tải 1.000 msg/s & CI/CD | **A** | I | **R** | C | C | C |
| Nghiệm thu & Bảo vệ Đề tài Hội đồng | **A / R** | R | R | R | R | R |

> *Ghi chú RACI:*  
> - **A (Accountable):** Người chịu trách nhiệm phê duyệt cao nhất và giải trình kết quả (Team Lead Phạm Minh Nhựt).  
> - **R (Responsible):** Người trực tiếp thực thi kỹ thuật.  
> - **C (Consulted):** Người được tham vấn chuyên môn.  
> - **I (Informed):** Người nhận thông tin cập nhật tiến độ.

### Danh sách thành viên chính thức nhóm N4.2 (UTH × VNPT NET)
1. **Phạm Minh Nhựt** (MSSV: `082205017237`) — **Team Leader / PM & Quản trị Dự án**
2. **Nguyễn Duy Minh** (MSSV: `083205002424`) — **Backend Engineer 3 (BE3)**
3. **Ngô Châu Kiệt** (MSSV: `083205002376`) — **QA Lead (Chất lượng & Đo tải)**
4. **Phạm Hoàng Long** (MSSV: `0822065010353`) — **Backend Engineer 1 (BE1)**
5. **Phạm Tấn Thành** (MSSV: `082205009270`) — **Backend Engineer 2 (BE2)**
6. **Lê Khắc Huy** (MSSV: `082205014597`) — **Frontend Engineer (FE)**

---

## 3. LỘ TRÌNH 18 TUẦN & MỐC SỐNG CÒN

- **W1–W4 (01/11 – 28/11/2026):** Khởi động, TDD v2, Test Plan v2, Tool generator M8, Dựng khung FastAPI & React, Quản trị Jira Sprint 1.
- **W5–W8 (29/11 – 26/12/2026):** Parser đa vendor, TimescaleDB hypertable, Batch insert.
- **W9 (27/12/2026):** **ĐÁNH GIÁ CHÉO GIỮA KỲ (MẪU 4 - THANG ĐIỂM 100).**
- **W9–W12 (27/12/2026 – 23/01/2027):** Động cơ tương quan Sliding Window, WebSocket Stream, Dashboard NOC.
- **W13 (30/01/2027):** **CODE FREEZE TOÀN BỘ MÃ NGUỒN TRƯỚC TẾT NGUYÊN ĐÁN.**
- **W14–W15 (31/01 – 13/02/2027):** Nghỉ Tết Nguyên Đán; không phát triển tính năng. Soak test chỉ chạy nếu đã có giám sát và được nhóm thống nhất.
- **W16–W18 (14/02 – 06/03/2027):** Hoàn tất Monthly Report 4, hồ sơ bàn giao, demo và đánh giá chéo cuối kỳ; nghiệm thu và bảo vệ trước hội đồng VNPT NET & UTH.
- **W13 (24–30/01/2027):** Nghiệm thu tải cuối ở mức **ít nhất 1.000 msg/s liên tục trong 1 giờ** và luật tương quan phát hiện đúng **ít nhất 90%** trên bộ 8–10 kịch bản chuẩn. Mốc 70% tại W12 là checkpoint để quyết định giữ hay thu hẹp phạm vi.
