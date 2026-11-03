# Quản lý tài liệu dự án N4.2

**Baseline hiện hành:** 03/11/2026 · **Trạng thái:** bản làm việc đồng bộ · **Chủ sở hữu:** Team Leader

## 1. Cơ cấu nhóm hiện hành

| Vai trò | Thành viên | Trách nhiệm chính |
|---|---|---|
| Team Leader / PM nội bộ | Phạm Minh Nhựt | Phạm vi, tiến độ, Jira/Confluence, báo cáo PM, rủi ro, quyết định và nghiệm thu |
| BE1 | Phạm Hoàng Long | Syslog và các kênh tiếp nhận |
| BE2 | Phạm Tấn Thành | Chuẩn hóa, lưu trữ và truy vấn |
| BE3 | Nguyễn Duy Minh | Gom nhóm, luật tương quan và API liên quan |
| FE | Lê Khắc Huy | Dashboard và xuất báo cáo |
| QA Lead | Ngô Châu Kiệt | Bộ sinh, kịch bản, CI/kiểm thử và đo tải |

## 2. Thứ tự ưu tiên khi tài liệu không khớp

1. Quy trình chính thức của HKDN UTH–VNPT NET quyết định biểu mẫu, mốc chương trình và yêu cầu gửi PM.
2. `DECISIONS.md` ghi các quyết định nhóm đã chốt, bao gồm tái phân vai ngày 03/11/2026.
3. `PROJECT_CHARTER.md` và `ACCEPTANCE_CRITERIA.md` là baseline phạm vi, lịch và tiêu chí nghiệm thu.
4. `SYSTEM_ANALYSIS_AND_DESIGN.md`, `TECHNICAL_DESIGN_DOCUMENT.md` và `TEST_PLAN.md` diễn giải baseline thành thiết kế và phương pháp kiểm thử; không tự đặt KPI khác.
5. Jira là nguồn sự thật về người nhận việc, hạn và trạng thái thực tế. Báo cáo tuần/tháng là hồ sơ lịch sử, không được sửa để làm đẹp kết quả.

Tài liệu Word/PDF trong `vnpt-proposal/` là hồ sơ điều hành được sinh từ `generate*.js`. Bản ngày 24/10/2026 có cơ cấu cũ và cần cập nhật theo baseline ngày 03/11 trước khi phát hành lại. Không dùng ZIP hoặc PDF cũ nếu chưa đối chiếu ngày phiên bản.

Hồ sơ phân tích–thiết kế đóng gói để phát hành/đọc thuận tiện nằm ngoài repo tại `vnpt-proposal/Phan_tich_thiet_ke_he_thong_N4.2_VNPT.docx` và `.pdf`; nguồn chuẩn, có thể sửa và truy vết là các Markdown trong `vnpt-repos/n42/docs/`. Sau khi sửa nguồn Markdown, chạy `vnpt-proposal/generate_system_analysis.py` để tạo lại cả hai bản phân phối.

## 3. Quy tắc sửa đổi

- Mỗi thay đổi về phạm vi, vai trò, mốc, KPI hoặc hợp đồng API phải có quyết định trong `DECISIONS.md` trước khi lan sang tài liệu dẫn xuất.
- Mỗi KPI phải ghi giá trị, đơn vị, thời lượng/phạm vi đo, dữ liệu đầu vào, điều kiện pass và nơi lưu bằng chứng.
- Tài liệu dẫn xuất phải được cập nhật cùng đợt với nguồn; tăng phiên bản/ngày cập nhật và ghi người chịu trách nhiệm.
- Báo cáo tuần/tháng đã gửi được giữ nguyên như hồ sơ; nếu phát hiện sai, thêm ghi chú đính chính có ngày, lý do và người xác nhận.
- Trước khi phát hành DOCX/PDF, kiểm tra nội dung trích xuất, mục lục, bảng, đầu/chân trang và trang cuối.

## 4. Bộ tài liệu dự án

| Tài liệu | Mục đích | Chủ trì |
|---|---|---|
| `PROJECT_CHARTER.md` | Phạm vi, tổ chức, mốc chính | TL |
| `ACCEPTANCE_CRITERIA.md` | Một chuẩn KPI và quy tắc nghiệm thu | TL + QA |
| `REQUIREMENTS_TRACEABILITY_MATRIX.md` | Truy vết yêu cầu đến thiết kế, test và minh chứng | TL + QA |
| `SYSTEM_ANALYSIS_AND_DESIGN.md` | Bản tổng quan và mục lục phân tích–thiết kế | TL + BE2 |
| `SYSTEM_REQUIREMENTS_AND_USE_CASES.md` | Scope, actor, FR/NFR, business rules và use cases | TL + BE1/BE2 |
| `ARCHITECTURE_DESIGN.md` | Context/container, luồng, lỗi, triển khai, bảo mật, UX | BE1 + BE2 + BE3 |
| `DATA_AND_API_DESIGN.md` | ERD, event/incident/rule schema, API hiện trạng và target | BE2 + BE3 |
| `TECHNICAL_DESIGN_DOCUMENT.md` | Chi tiết kỹ thuật, KPI và các cấu hình cần quyết định | BE2 + BE3 + QA |
| `TEST_PLAN.md` | Kịch bản và phương pháp kiểm thử | QA |
| `RISK_REGISTER.md` | Rủi ro, dấu hiệu kích hoạt và phương án | TL |
| `HANDOVER_CHECKLIST.md` | Bàn giao và nghiệm thu cuối kỳ | TL + QA |
| `DECISIONS.md` | Quyết định kỹ thuật và quản trị | TL |
