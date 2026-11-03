# BIÊN BẢN HỌP KHỞI ĐỘNG DỰ ÁN (PROJECT KICKOFF MINUTES)

> **Mã cuộc họp:** `MEET-N42-2026-W01-KICKOFF`  
> **Thời gian:** 09:00 – 11:30, Chủ Nhật ngày 01/11/2026 (Tuần 1)  
> **Chủ tọa (Team Leader / PM):** **Phạm Minh Nhựt**  
> **Thư ký ghi biên bản:** Ngô Châu Kiệt (QA Lead)  
> **Thành phần tham dự:** Đại diện VNPT NET + Giảng viên UTH + Đủ 6 thành viên nhóm N4.2  

---

## 1. NỘI DUNG VÀ QUYẾT ĐỊNH CHÍNH

1. **Phê duyệt đề tài N4.2**: Thu thập và phân tích cảnh báo từ router, switch, firewall.
2. **Thống nhất Stack công nghệ**:
   - Backend: Python 3.12+ (FastAPI, `asyncio.DatagramProtocol` port 5514).
   - Database: PostgreSQL 16 + TimescaleDB (Hypertable phân vùng 7 ngày).
   - Frontend: React 18 + Tailwind CSS (NOC Dark Mode).
   - QA & CI: Pytest, synthetic generator, secret leak scanner.
3. **Cơ cấu nhân sự & Phân công vai trò**:
   - **Phạm Minh Nhựt:** Đảm nhiệm **Team Leader / PM & Quản trị Jira / Confluence / Điều phối chung**.
   - **Nguyễn Duy Minh:** Đảm nhiệm **Backend Engineer 3 (BE3)** phụ trách Luật tương quan M5 & Correlation Engine M6.
   - **Ngô Châu Kiệt:** Đảm nhiệm **QA Lead** phụ trách Module M8 (Kịch bản kiểm thử KB-01..08, Đo kiểm tải 1.000 msg/s).
   - **Phạm Hoàng Long:** BE1 (Syslog UDP Ingestion M1 & Parser M2).
   - **Phạm Tấn Thành:** BE2 (Queue Buffer In-Memory M3 & TimescaleDB M4).
   - **Lê Khắc Huy:** FE (NOC Dark Mode Web Dashboard M7).
4. **Chốt mốc sống còn (Code Freeze)**:
   - **30/01/2027 (W13 - Trước Tết Nguyên Đán)** đóng băng toàn bộ code.
5. **Quy định Git Flow & Code Review**:
   - Nhánh: `feature/N42-xx-mo-ta`.
   - Bắt buộc CI pass và ít nhất 1 review approved (Team Lead Phạm Minh Nhựt hoặc QA Lead) mới merge `main`.

---

## 2. KẾT LUẬN & CHỮ KÝ XÁC NHẬN

- **Thư ký ghi biên bản:** Ngô Châu Kiệt (Đã ký)
- **Chủ tọa (Team Leader / PM):** Phạm Minh Nhựt (Đã ký)
- **Đại diện Cố vấn VNPT NET:** Chưa có ý kiến phê duyệt/xác nhận tại thời điểm lập biên bản.
