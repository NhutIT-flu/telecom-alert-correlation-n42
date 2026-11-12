# Công cụ trong thư mục `tools/`

## `generator.py` — Bộ sinh dữ liệu giả lập Syslog (N42-11, Module M8)

Phát cảnh báo giả lập Cisco / Huawei / Fortinet qua 3 nguồn baseline: **UDP**, **HTTP REST** và **file log**.
Toàn bộ dữ liệu là giả lập; IP thiết bị thuộc dải RFC 1918 (`10.10.x.x`, `192.168.1.x`), IP đối tác minh họa thuộc
`203.0.113.0/24` (RFC 5737). Chỉ dùng thư viện chuẩn của Python, không cần cài thêm gói nào.

Chạy từ thư mục gốc của repo (PowerShell, không cần kích hoạt `.venv`):

```powershell
.\.venv\Scripts\python.exe tools/generator.py --help
```

### Ví dụ nhanh

```powershell
# 1. Ghi 100 bản tin trộn 3 hãng ra file log (không cần server nào đang chạy)
python tools/generator.py --mode file --count 100 --rate 500 --file-path logs/simulated_syslog.log

# 2. Bắn UDP tới receiver cổng 5514 (mặc định 127.0.0.1:5514)
python tools/generator.py --mode udp --count 1000 --rate 500 --vendor mixed

# 3. Gọi REST ingest (mặc định http://127.0.0.1:8000/api/v1/events/ingest, cần backend N42-14 đang chạy)
python tools/generator.py --mode http --count 200 --rate 200 --vendor cisco

# 4. Phát lại tất định (Deterministic Replay): cùng --seed cho cùng chuỗi bản tin
python tools/generator.py --mode file --count 50 --seed KB-08-v1 --file-path logs/replay.log

# 5. Định dạng RFC 5424 thay cho RFC 3164
python tools/generator.py --mode file --count 10 --format rfc5424 --seed 42 --file-path logs/rfc5424.log

# 6. Chạy liên tục theo thời gian (count = 0), dừng bằng --duration hoặc Ctrl+C
python tools/generator.py --mode udp --count 0 --duration 60 --rate 200
```

### Tham số

| Tham số | Mặc định | Ý nghĩa |
| :--- | :--- | :--- |
| `--mode` | `udp` | `udp`, `http` (đồng nghĩa `api`, `rest`) hoặc `file` |
| `--rate` | `500` | Tốc độ mục tiêu (bản tin/giây) |
| `--count` | `500` | Tổng số bản tin; `0` = chạy liên tục tới khi hết `--duration` hoặc nhấn Ctrl+C |
| `--duration` | không giới hạn | Thời gian chạy tối đa (giây) |
| `--vendor` | `mixed` | `cisco`, `huawei`, `fortinet` hoặc `mixed` |
| `--format` | `rfc3164` | `rfc3164` hoặc `rfc5424` |
| `--host`, `--port` | `127.0.0.1`, `5514` | Đích của chế độ UDP |
| `--api-url` | `http://127.0.0.1:8000/api/v1/events/ingest` | Đích của chế độ HTTP |
| `--file-path` | `logs/simulated_syslog.log` | File đầu ra của chế độ file (ghi nối tiếp) |
| `--seed` | không đặt | Số nguyên hoặc chuỗi (ví dụ `KB-08-v1`) để tái lập luồng bản tin |

### Lưu ý khi dùng

- **HTTP:** generator dùng một kết nối keep-alive cho cả đợt phát. Chỉ mã trả về 2xx được tính là gửi thành công; mã khác
  hoặc lỗi kết nối được tính vào số `Lỗi` ở dòng tổng kết. Nếu thấy toàn bộ là lỗi, kiểm tra backend đã chạy và `--api-url`
  đúng với router đang triển khai.
- **Không tự retry POST:** khi mất phản hồi, timeout hoặc body phản hồi bị ngắt, backend có thể đã nhận bản tin.
  Generator ghi `unknown_outcomes` (hiển thị `chưa rõ kết quả`, là một phần của `errors`), không gửi lại payload đó.
  Kết nối mới chỉ được dùng cho bản tin tiếp theo. Retry chỉ được bổ sung sau khi backend có idempotency contract được duyệt.
- **Đối soát:** API Python trả `attempted = sent + errors`; `unknown_outcomes <= errors`, không cộng unknown thêm lần nữa.
  Lỗi connect trước POST là lỗi gửi thông thường. `--count` giới hạn tổng số lượt thử, gồm cả lỗi; không bù bằng bản tin mới.
  `sent` HTTP là số phản hồi 2xx đầy đủ, không chứng minh đã persist. Với UDP, `sent` chỉ là số `sendto` thành công.
- **File:** log được flush định kỳ (mỗi 200 dòng) và khi kết thúc đợt phát.
- **An toàn:** chỉ phát tới loopback hoặc máy lab được phê duyệt, không gửi tới thiết bị thật. Thư mục `logs/` sinh ra khi
  chạy thử chỉ để thử nghiệm cục bộ, không commit lên repo.
- Số `Thông lượng đạt` ở dòng tổng kết là số đo tại máy phát trong lần chạy đó; không phải kết quả nghiệm thu.
- Kiểm thử: `python -m unittest tests.test_generator -v`.

### Exit code cho script QA/CI

| Mã | Ý nghĩa |
| :--- | :--- |
| `0` | Đợt phát kết thúc theo count/duration và không ghi nhận lỗi gửi |
| `1` | Có ít nhất một lỗi gửi hoặc kết quả chưa rõ; hoặc lỗi runtime như URL/file không hợp lệ |
| `2` | Tham số CLI không hợp lệ: rate ≤0, count âm, duration không hữu hạn/≤0, port ngoài 1–65535 |
| `130` | Bị ngắt bởi Ctrl+C; file/kết nối được đóng và SIGINT handler cũ được khôi phục |

`--duration` có thể kết thúc trước `--count` theo chủ đích; mã 0 không xác nhận đã gửi đủ count khi dùng cả hai.
Nếu có `unknown_outcomes`, giữ log/seed/commit và đối chiếu backend trước khi quyết định phát lại, tránh tạo dữ liệu trùng.

### Ca hồi quy N42-11

FR-13/AC-01 và TC-REP-001/TC-ING-007–010: kiểm server nhận POST rồi mất response (không nhận payload lần hai),
timeout/body bị ngắt, lỗi connect, 404/503, hỗn hợp thành công–thất bại và exit code của process thật.
Kiểm tiếp keep-alive 50 bản tin trên một kết nối, mở lại kết nối cho bản tin tiếp theo, count hữu hạn khi toàn lỗi,
flush mỗi 200 dòng, Ctrl+C và tham số biên. Đây là kiểm thử tooling trên server giả lập local, không thay nghiệm thu N42-14.

## `check_sensitive.py` — Quét rò rỉ thông tin nhạy cảm

```powershell
python tools/check_sensitive.py .
```

Báo credential/token hardcode và IP public nằm ngoài dải RFC 1918 / RFC 5737. Chạy trước khi push.
