# BÁO CÁO TIẾN ĐỘ DỰ ÁN — TUẦN W1 (WEEKLY STATUS REPORT)

> **Kỳ báo cáo:** Tuần W1 (09/11/2026 – 14/11/2026 | Kickoff bắt đầu Thứ Hai 09/11/2026; Tuần W0 26/10–30/10/2026 là tuần chuẩn bị đã hoàn tất)  
> **Dự án:** N4.2 UTH × VNPT NET  
> **Team Leader / Người lập:** **Phạm Minh Nhựt**  
> **Trạng thái tài liệu:** BẢN CHÍNH THỨC — đối chiếu Jira và bằng chứng thực tế Sprint 1. Kỳ báo cáo kết thúc ngày 14/11/2026.

---

## 1. KẾT QUẢ ĐẠT ĐƯỢC TRONG TUẦN W1

1. **Quản trị Dự án, Jira & Confluence (Phạm Minh Nhựt - Team Lead / PM)**:
   - Hoàn thành cuộc họp Kickoff toàn nhóm với VNPT NET & UTH (`N42-21` - Done).
   - Ban hành TDD v2 và QA Master Test Plan v2 lên Confluence.
   - Thiết lập cấu trúc Jira Sprint 1 đến Sprint 7 (53 thẻ task) trải dài tới mốc Code Freeze trước Tết.
   - Thống nhất cơ cấu 6 thành viên: Phạm Minh Nhựt (Team Lead), Nguyễn Duy Minh (BE3), Ngô Châu Kiệt (QA Lead), Phạm Hoàng Long (BE1), Phạm Tấn Thành (BE2), Lê Khắc Huy (FE).
2. **QA Tooling & Kịch bản (Ngô Châu Kiệt - QA Lead)**:
   - Tiếp nhận và làm chủ công cụ `tools/generator.py` (CLI 3 nguồn: UDP, API, File).
   - Hoàn thành bộ kịch bản chuẩn `KB-01` và `KB-02` (`N42-11`, `N42-12` - Done).
   - Chuẩn bị ma trận kịch bản kiểm thử `KB-03` đến `KB-08`.
3. **Đo kiểm tải thực tế tại máy Local**:
   - Đo thử thông lượng **963.48 msg/s**, tỷ lệ rớt gói được ghi nhận **0.00%** với socket buffer 4MB.
   - Kết quả này **chưa đạt SLA nghiệm thu 1.000 msg/s** và chưa có thời lượng/phương pháp đo đầy đủ trong báo cáo; cần đo lại, không tính là nghiệm thu.

---

## 2. KẾ HOẠCH TUẦN 2 (W2)

- **Team Lead / PM (Nhựt):** Kiểm soát tiến độ Jira Sprint 1, theo dõi CI/CD, chuẩn bị báo cáo tuần 2.
- **BE1 (Long):** Nối parser RFC3164/5424 vào router FastAPI.
- **BE2 (Thành):** Dựng container TimescaleDB và DDL hypertable.
- **BE3 (Minh):** Nạp module luật `rules.yaml` và kiểm thử Sliding Window.
- **QA Lead (Kiệt):** Tiếp tục xây dựng ma trận test KB-03, KB-04 và chạy benchmark định kỳ.
- **FE (Huy):** Khung giao diện NOC Dark Mode trên React 18 Tailwind CSS.
