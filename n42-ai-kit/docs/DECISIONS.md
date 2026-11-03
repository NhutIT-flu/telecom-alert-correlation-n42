# DECISIONS — Quyết định kỹ thuật và đề xuất chờ chốt

Trạng thái: `ĐỀ XUẤT` (chờ TL chốt) · `ĐÃ CHỐT` · `THAY THẾ`.
Khi chốt, TL đổi trạng thái và ghi ngày. Mọi file khác phải theo quyết định ĐÃ CHỐT.

| ID | Quyết định | Trạng thái |
|---|---|---|
| D-01 | Thang `severity` lưu trong DB là **số nguyên 0–7 theo RFC 5424** (0 Emergency … 7 Debug). Tên CRITICAL/MAJOR/WARNING… của từng hãng được **map về 0–7** trong parser; FE tự đổi sang nhãn để hiển thị. | ĐỀ XUẤT |
| D-02 | Hypertable `alert_events` phân vùng theo cột **`event_timestamp`** (UTC), không có cột `time` riêng. Cột thiết bị dùng **`hostname`** và **`source_ip`**, không có cột `device`. Index `(event_timestamp DESC, hostname, severity)`. | ĐỀ XUẤT |
| D-03 | Bên giao nhận BE1→BE2 là `RawEvent`; BE2 cung cấp `Pipeline.process(raw)`. Xem `docs/INTERFACES.md`. | ĐỀ XUẤT |
| D-04 | BE3 nhận `AlertEvent` đã chuẩn hóa bằng **subscriber trong tiến trình** (callback bất đồng bộ do pipeline gọi sau khi ghi store); khi khởi động lại có thể nạp lại cửa sổ từ `EventStore.search`. | ĐỀ XUẤT |
| D-05 | Ghi TimescaleDB **theo lô** (`add_many`, batch hoặc `COPY`) để đạt 1.000 sự kiện/giây; không insert từng dòng. | ĐỀ XUẤT |
| D-06 | Quy tắc 2 reviewer áp cho: parser, luật tương quan, code thu thập mạng lõi (`receiver/`). PR khác ≥1 reviewer. | ĐỀ XUẤT |
| D-07 | Khuôn commit: `<type>: mo ta khong dau (N42-x)` (khoảng trắng, không gạch nối). Danh sách type: feat, fix, test, refactor, perf, docs, chore. Sửa lỗi cũng dùng nhánh `feature/...`. | ĐỀ XUẤT |
| D-08 | FE dùng **JavaScript (JSX)** theo ví dụ ban đầu (`services/api.js`); nâng TypeScript sau nếu cả nhóm đồng ý. | ĐỀ XUẤT |
| D-09 | Dải IP mẫu: 10.x và 192.168.x là dải **private**; chỉ `203.0.113.0/24` (cùng 192.0.2.0/24, 198.51.100.0/24) là **TEST-NET**. Ghi đúng như vậy trong mọi tài liệu. | ĐỀ XUẤT |
| D-10 | Nội dung chính thức của Daily (6 mục), Mẫu 2 (7 mục), Mẫu 3 (7 mục), hồ sơ bàn giao (8 hạng mục) chưa có trong repo. TL dán vào `docs/templates/`. Trước đó AI **không được tự đặt tên mục**. | CHỜ TL |
