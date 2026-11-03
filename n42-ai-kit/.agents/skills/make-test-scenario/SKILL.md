---
name: make-test-scenario
description: Soạn kịch bản kiểm thử chuẩn cho N4.2 (link flap, port scan/brute-force, CPU/RAM quá tải, UPS, BGP neighbor down...) kèm cấu hình bộ sinh dữ liệu giả lập tái lập 100%. Hãy dùng skill này khi QA hoặc BE3 cần tạo, sửa, tài liệu hóa hoặc chạy kịch bản kiểm thử và bộ sinh dữ liệu.
---

# Kịch bản kiểm thử

Lưu mỗi kịch bản ở `docs/scenarios/KB-XX-<ten-khong-dau>.md` với đúng 5 phần:

```markdown
# KB-XX — <Tên kịch bản>
## Mô tả
## Điều kiện kích hoạt
## Dữ liệu đầu vào
## Kết quả kỳ vọng
## Cách kiểm tra
```

## Yêu cầu
- **Tái lập 100%**: cố định seed ngẫu nhiên, ghi tốc độ (msg/s), thời lượng, nguồn gửi (UDP/TCP 5514, `/api/ingest`, file), lệnh chạy bộ sinh.
- Dữ liệu 100% giả lập: IP chỉ dùng 10.x, 192.168.x, 203.0.113.x; không credential thật; không gửi/quét tới thiết bị thật, chỉ chạy trong mạng lab.
- Kết quả kỳ vọng phải đo được: luật nào phải kích hoạt, bao nhiêu sự cố gom nhóm, ngưỡng thời gian.
- Phủ 8–10 kịch bản chuẩn: bình thường, link flap liên tục, port scan/brute-force, CPU/RAM quá tải, sự cố nguồn UPS, BGP neighbor down, bùng nổ cảnh báo, lan truyền đa thiết bị.
- Sau **30/01/2027** không thêm kịch bản mới, chỉ sửa lỗi.

## Bộ sinh dữ liệu
Viết bằng Python async; hỗ trợ RFC 3164/5424, Cisco IOS, Huawei VRP; tham số `--rate`, `--duration`, `--scenario`, `--seed`, `--target`. Phát tải theo mốc 200 → 500 → 1.000 sự kiện/giây × 1 giờ và ghi CPU, RAM, mất gói UDP, độ trễ pipeline.

## PR
`test: them kich ban <ten> (N42-x)`.
