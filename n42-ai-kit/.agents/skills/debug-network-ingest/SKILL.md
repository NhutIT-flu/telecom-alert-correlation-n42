---
name: debug-network-ingest
description: Chẩn đoán lỗi nhận syslog UDP/TCP và ingest bất đồng bộ (mất gói, không nhận được log, queue đầy, event loop bị chặn, cổng 5514). Hãy dùng skill này khi BE1 hoặc QA báo không nhận được sự kiện, mất gói khi phát tải, tiến trình treo/sập, hoặc độ trễ tăng bất thường ở tầng thu thập.
---

# Chẩn đoán lỗi thu thập

Đi **đúng thứ tự**, mỗi bước kiểm tra xong mới sang bước sau.

1. **Event loop bị chặn**
   - Bật chế độ debug asyncio (`PYTHONASYNCIODEBUG=1`) để thấy callback chạy chậm.
   - Tìm code đồng bộ trong `async`: I/O file, regex nặng, `time.sleep`, truy vấn DB đồng bộ. Chuyển sang `asyncio.to_thread` hoặc API async.
2. **Queue đầy**
   - Kiểm tra `qsize()` và `maxsize` của `asyncio.Queue`. Queue đầy nghĩa là consumer (pipeline BE2) chậm hơn producer.
   - Quyết định chính sách khi đầy (bỏ gói mới, đếm số bị bỏ) và ghi lại bằng bộ đếm metric; không để chặn receiver.
3. **Socket, cổng, firewall**
   - Kiểm tra cổng 5514 đang nghe (Windows: `netstat -ano | findstr 5514`; Linux: `ss -lunp | grep 5514`).
   - Trong Docker: ánh xạ cổng `5514:5514/udp` (chú ý `/udp`), mạng giữa container.
   - UDP mất gói do bộ đệm nhận của hệ điều hành nhỏ: xem xét tăng `SO_RCVBUF`.
4. **Định dạng gói thô**
   - Log nguyên văn byte nhận được (cắt ngắn, không ghi dữ liệu nhạy cảm), kiểm tra PRI `<n>`, mã hóa, kích thước, ký tự xuống dòng (TCP cần tách khung).

## Báo cáo
Nguyên nhân đã xác định (hoặc bước đã loại trừ), bằng chứng (log, số đếm), cách sửa, test tái hiện bằng `pytest` + `pytest-asyncio`. Chỉ gửi dữ liệu giả lập tới `127.0.0.1`/mạng lab, không tới thiết bị thật.
