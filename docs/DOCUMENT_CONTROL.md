# Quản lý tài liệu dự án N4.2

**Baseline hiện hành:** 09/11/2026 · **Trạng thái:** bản làm việc nội bộ; hồ sơ Word/PDF cần qua đối chiếu manifest và kiểm tra trước phát hành · **Chủ sở hữu:** Team Leader

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

Tài liệu Word/PDF trong `vnpt-proposal/` là hồ sơ dẫn xuất; Markdown trong `vnpt-repos/n42/docs/` là nguồn chuẩn với tài liệu được sinh từ nguồn. Bản phát hành phải được tái sinh sau khi chốt nguồn và kiểm tra nội dung/layout. Theo yêu cầu ngày 07/11/2026, toàn bộ ZIP trong workspace đã được xóa; không có gói ZIP hiện hành.

**Kết quả rà soát và điều khiển phát hành 09/11/2026:**

- `TEST_CASE_SPECIFICATION.md` là đặc tả kế hoạch chi tiết; mã test trong tài liệu không chứng minh đã tự động hóa hoặc đã chạy. RTM phải chỉ rõ coverage dự kiến, evidence và gap.
- Phạm vi baseline nguồn vào là syslog UDP, REST ingest và file; TCP chỉ bổ sung qua quyết định phạm vi và cập nhật SRS/AC/RTM/Jira. Không tuyên bố coverage chức năng 100%. QA chủ trì test/coverage/CI; owner code viết unit test module mình.
- Lưu lịch dự kiến 09/11 làm hồ sơ chuẩn bị. Kickoff thực tế ngày 06/11/2026. Sprint 1 bắt đầu ngày 09/11/2026. Ghi kết quả họp và báo cáo theo bằng chứng đã đối chiếu.
- PDF phải được render và rà trực quan trước khi coi là bản phát hành; nội dung trích xuất chỉ là kiểm tra bổ sung, không thay QA bố cục.
- Bản Word/PDF phát hành chỉ được xem là đồng bộ khi tên tệp khớp manifest, sinh từ nguồn cùng baseline, không còn bản tuần/biên bản sai tên, và đã qua kiểm tra nội dung/hình thức. ZIP đã bị xóa theo yêu cầu, không tái tạo.

**Trạng thái hồ sơ dẫn xuất:** Word/PDF được xem là bản phát hành chỉ sau khi đối chiếu từng tệp với manifest cùng baseline, rà nội dung và bố cục, rồi ghi người rà soát. Có Test Case Specification và RTM trong nguồn; các bản Lead của QA phải chứa cả hai và liên kết đúng phiên bản. Không kết luận bộ Word/PDF đã phát hành chỉ dựa trên việc tệp đã được sinh.

**Đợt tái sinh 09/11/2026:** `Ho_so_Word` và `Ho_so_PDF` được sinh lại từ 27 tệp Markdown hiện có trong `vnpt-repos/n42/docs/` cùng các hồ sơ tham chiếu đã có; `Ho_so_Lead` được tái sinh thành bảng điều hành và 5 tập theo nhóm nội dung. Tổng cộng hiện có 48 cặp DOCX/PDF trong hai bộ hồ sơ. PDF được render và rà bằng contact sheet; sau khi cập nhật lịch Jira, `TEST_PLAN.pdf` và tập Lead kiểm thử được render/rà lại. Renderer DOCX không chạy được vì môi trường thiếu LibreOffice; do đó bố cục Word chưa được xác nhận độc lập, và các hồ sơ vẫn ở trạng thái bản làm việc chờ người rà nội dung/bố cục và sign-off. Danh mục tệp sinh là chỉ mục, không thay chữ ký phát hành.

Toàn bộ ZIP trong workspace đã bị xóa theo yêu cầu của người dùng ngày 07/11/2026 và không được tái tạo. Hồ sơ phân tích–thiết kế có nguồn chuẩn trong `vnpt-repos/n42/docs/`; bản Word/PDF cấp cao nhất nằm trong `vnpt-proposal/` và được sinh bằng `generate_system_analysis.py`.

## 3. Quy tắc sửa đổi

- Mỗi thay đổi về phạm vi, vai trò, mốc, KPI hoặc hợp đồng API phải có quyết định trong `DECISIONS.md` trước khi lan sang tài liệu dẫn xuất.
- Mỗi KPI phải ghi giá trị, đơn vị, thời lượng/phạm vi đo, dữ liệu đầu vào, điều kiện pass và nơi lưu bằng chứng.
- Tài liệu dẫn xuất phải được cập nhật cùng đợt với nguồn; tăng phiên bản/ngày cập nhật và ghi người chịu trách nhiệm.
- Báo cáo tuần/tháng đã gửi được giữ nguyên như hồ sơ; nếu phát hiện sai, thêm ghi chú đính chính có ngày, lý do và người xác nhận.
- Trước khi phát hành DOCX/PDF, kiểm tra nội dung trích xuất, mục lục, bảng, đầu/chân trang và trang cuối.
- Đặc tả Test Case và RTM do QA Lead chủ trì; owner nghiệp vụ/kỹ thuật cung cấp contract, dữ liệu kỳ vọng và xác nhận phạm vi. Repo hiện chưa có `.github/workflows/ci.yml`; QA Lead là owner dự kiến triển khai CI theo kế hoạch nhóm. Khi có workflow, QA/DevOps ghi nội dung check và run evidence; không tuyên bố CI PASS hoặc merge gate khi chưa có bằng chứng.
- Manifest phát hành phải liệt kê từng nguồn, phiên bản/ngày, tệp Word/PDF tương ứng, người rà nội dung và người rà hình thức. Chỉ phát hành sau khi ma trận nguồn–bản dẫn xuất không còn thiếu.

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
| `TEST_CASE_SPECIFICATION.md` | Đặc tả ca kiểm thử chi tiết, điều kiện biên và expected result | QA Lead + owner BE/FE liên quan |
| `RISK_REGISTER.md` | Rủi ro, dấu hiệu kích hoạt và phương án | TL |
| `HANDOVER_CHECKLIST.md` | Bàn giao và nghiệm thu cuối kỳ | TL + QA |
| `DECISIONS.md` | Quyết định kỹ thuật và quản trị | TL |
