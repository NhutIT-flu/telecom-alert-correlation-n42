# Hướng dẫn trợ lý dự án N4.2

Trả lời bằng tiếng Việt, ngắn gọn và đi thẳng vào việc. Tuân thủ `../AGENTS.md` cùng với tài liệu vai trò tương ứng.

## Nhóm và nguồn chuẩn
- Team Leader/PM nội bộ: Phạm Minh Nhựt; BE1: Phạm Hoàng Long; BE2: Phạm Tấn Thành; BE3: Nguyễn Duy Minh; FE: Lê Khắc Huy; QA Lead: Ngô Châu Kiệt.
- Thứ tự ưu tiên tài liệu: quy trình HKDN chính thức; `../../docs/DECISIONS.md`; `../../docs/PROJECT_CHARTER.md` và `../../docs/ACCEPTANCE_CRITERIA.md`; SRS/TDD/RTM; sau đó Jira cho owner, hạn và trạng thái thực tế.
- Các tài liệu trong repo là baseline nội bộ; không suy ra VNPT đã phê duyệt nếu thiếu xác nhận.

## Baseline dự án
Hệ thống lab nhận cảnh báo qua syslog UDP, REST và file; chuẩn hóa, lưu/truy vấn, gom nhóm/tương quan và hiển thị dashboard. TCP syslog chưa thuộc baseline nghiệm thu; chỉ thêm sau quyết định phạm vi và cập nhật yêu cầu/AC/RTM/Jira.

Baseline code W1 chỉ có FastAPI `GET /api/health`; các module ingest, parser, persistence, correlation và dashboard là công việc theo ticket. Dùng dữ liệu giả lập; không kết nối/quét thiết bị thật hoặc đưa credential/log production vào repo/AI.

Timeline chuẩn: W0 26–31/10/2026; W1 01–07/11; W2 08–14/11; kickoff thực tế ngày 06/11 và Sprint 1 bắt đầu ngày 09/11 trong W2. W12 là checkpoint correlation ≥70%; W13 là nghiệm thu mục tiêu ≥90% trên 8–10 kịch bản và ≥1.000 msg/s trong 1 giờ, sau đó code freeze 30/01/2027. Đây là mục tiêu, chưa phải kết quả thực hiện.

## Cổng tài liệu trước khi code
Với thay đổi hành vi, ticket phải liên kết yêu cầu/acceptance, owner, test case có input/expected output/điều kiện biên phù hợp và dòng trong RTM trước khi bắt đầu code. QA Lead chủ trì đặc tả và coverage; BE/FE owner xác nhận contract và expected result; owner code chịu trách nhiệm unit test; QA quản lý tích hợp, CI/workflow và evidence.

## Quy trình làm việc
- Đọc `docs/roles/<VAI>.md` theo vai trò người dùng; không tự nhận tiến độ hoặc kết quả CI/test.
- Không push thẳng `main`; dùng nhánh và commit theo `docs/DECISIONS.md`/`CONTRIBUTING.md`; PR có reviewer và CI xanh mới merge theo policy nhóm.
- WIP tối đa hai thẻ In Progress mỗi người. Đổi schema, scope, API, KPI hoặc owner phải có quyết định và cập nhật các tài liệu liên quan.
- Mỗi parser và rule cần test `pytest` tái lập; cảnh báo khi thay đổi đe dọa mốc W4/W6/W8/W12/W13.
