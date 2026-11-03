---
name: write-parser-tests
description: Viết unit test cho parser/chuẩn hóa syslog (RFC 3164, RFC 5424, Cisco IOS, Huawei VRP, Linux) với bộ ≥200 sự kiện mẫu mỗi hãng theo tiêu chí nghiệm thu của N4.2. Hãy dùng skill này khi BE2 hoặc ai đó viết/sửa parser, thêm định dạng log mới, sửa lỗi parse, hoặc nói "test cho parser".
---

# Test cho parser

Mỗi parser (một `BaseNormalizer`) bắt buộc có test riêng. Tiêu chí nghiệm thu: **chuẩn hóa đúng theo bộ test, ≥200 sự kiện mẫu mỗi hãng**.

## Cấu trúc
```text
tests/parsers/test_<vendor>.py
tests/parsers/fixtures/<vendor>.jsonl     # mỗi dòng: {"raw": "...", "expected": {...}}
```

## Quy trình
1. Đọc parser và `docs/INTERFACES.md` (`RawEvent`, `AlertEvent`, thang severity 0–7).
2. Tạo fixtures ≥200 dòng từ Loghub **đã làm sạch** hoặc từ bộ sinh của QA. Thay IP/hostname thật bằng dải mẫu (10.x, 192.168.x, 203.0.113.x). Không dùng credential thật.
3. Viết test tham số hóa (`pytest.mark.parametrize` hoặc đọc jsonl) kiểm tra: `severity`, `facility`, `hostname`, `program`, `event_timestamp` (UTC), `vendor`, `category`.
4. Thêm ca biên bắt buộc: hostname có khoảng trắng, thiếu trường, timestamp lỗi, tiền tố PRI sai, chuỗi rỗng, Unicode, dòng rất dài.
5. Ca lỗi: gói dị dạng phải đi vào quarantine/`ParseError`, **không** ném exception ra ngoài pipeline.
6. Test chống ReDoS: một dòng độc hại dài phải parse xong trong ngưỡng thời gian cố định (ví dụ <100 ms).
7. Chạy `pytest tests/parsers -q`; báo số mẫu đạt/tổng.

## PR
`test: them kiem thu parser <vendor> (N42-x)`. Parser cần **2 reviewer**. Nếu ai nói "không cần test", từ chối khéo và nhắc tiêu chí nghiệm thu.
