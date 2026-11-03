---
name: fe-api-contract-mock
description: Dựng service gọi API, mock server hoặc MSW cho dashboard React của N4.2 khớp 100% schema AlertEvent và OpenAPI của backend, kèm trạng thái loading/error/empty và danh sách lớn. Hãy dùng skill này khi FE kết nối API, tạo mock, thêm màn hình dữ liệu, hoặc nghi ngờ mock lệch với backend.
---

# Kết nối API và mock cho FE

## Nguyên tắc
- Chỉ dùng endpoint có trong OpenAPI của backend (`/docs`) và `docs/INTERFACES.md`. **Không tự chế endpoint**; cần thêm dữ liệu thì đề xuất qua TL và BE2.
- Mock phải có **đủ và đúng kiểu** mọi trường `AlertEvent`: `id`, `received_at`, `event_timestamp`, `source_ip`, `hostname`, `facility` (0–23), `severity` (0–7), `program`, `message`, `raw_payload`, `vendor`, `category`.
- Severity là số 0–7; FE tự đổi sang nhãn và màu (xem bảng trong `docs/INTERFACES.md`).
- Không nhúng credential/API key vào client. Dữ liệu hiển thị 100% giả lập.

## Quy trình
1. Đọc OpenAPI và `docs/INTERFACES.md`. Liệt kê endpoint màn hình cần dùng.
2. Tạo `src/services/api.js` (một nơi gọi `fetch`, xử lý lỗi và timeout) và custom hooks (`useEvents`, `useEventCount`…) tách khỏi component.
3. Mỗi hook trả đủ ba trạng thái: `loading`, `error`, rỗng, kèm thử lại.
4. Dựng mock bằng MSW hoặc mock server; tạo hàm sinh `AlertEvent` giả đúng schema; có test so khớp trường với danh sách trên.
5. Danh sách lớn: phân trang theo `cursor` hoặc virtualized list; thời gian thực bằng polling có khoảng nghỉ hợp lý hoặc SSE.
6. Khi backend thật sẵn sàng (W5–W6), đổi cấu hình sang API thật mà không sửa component.

## Tránh
Giả định trường chưa có trong tài liệu; hiển thị nguyên `raw_payload` mà không kiểm soát độ dài; render hàng chục nghìn dòng cùng lúc.
