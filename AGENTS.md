# Hướng dẫn làm việc trong repo N4.2

- Đọc `n42-ai-kit/AGENTS.md` và tài liệu vai trò tương ứng trước khi làm ticket.
- Làm theo Jira về owner, scope, trạng thái và tiêu chí Done; không suy ra tính năng đã hoàn thành từ tài liệu thiết kế.
- Baseline W1 hiện chỉ chạy FastAPI `GET /api/health`. Các module ingest, parser, store, correlation, dashboard và DB repository phải được làm theo ticket.
- Hợp đồng trong `n42-ai-kit/docs/INTERFACES.md` còn là đề xuất v0.9; phối hợp TL và owner liên quan để chốt trước khi tạo phụ thuộc liên module.
- Dùng dữ liệu giả lập. Không đưa credential, log thật hoặc thông tin thiết bị production vào repo.
- Không push thẳng `main`. Giới hạn WIP theo D.2: tối đa hai thẻ mỗi người ở `In Progress`; thẻ thứ ba chỉ sau khi hoàn thành hoặc trả lại một thẻ.
