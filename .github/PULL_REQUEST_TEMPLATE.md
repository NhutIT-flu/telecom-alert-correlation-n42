## 📌 Liên kết Jira Issue
- Ticket: `[N42-XX]` (Ví dụ: `[N42-10] Syslog UDP Receiver Baseline`)
- Link Jira: https://nhutp2945-1793259952237.atlassian.net/browse/N42-XX

## 🎯 Mục tiêu Thay đổi (Summary of Changes)
<!-- Tóm tắt ngắn gọn mục tiêu kỹ thuật và các thay đổi chính trong Pull Request này -->

## 🧩 Module Tác động
- [ ] Module M1: Syslog UDP Receiver (5514)
- [ ] Module M2: Multi-Vendor Log Parser (Cisco / Huawei / Fortinet)
- [ ] Module M3: In-Memory / Queue Buffer
- [ ] Module M4: TimescaleDB Storage & DDL
- [ ] Module M5: Correlation Rules Configuration (`rules.yaml`)
- [ ] Module M6: Real-Time Correlation Engine & REST API
- [ ] Module M7: NOC Web Dashboard (React / WebSocket)
- [ ] Module M8: QA Generator, Benchmark 1.000 msg/s & Test Suites
- [ ] DevOps / CI/CD / Documentation

## 🔍 Loại Thay đổi (Type of Change)
- [ ] `feat`: Bổ sung tính năng kỹ thuật mới
- [ ] `fix`: Sửa lỗi hệ thống
- [ ] `refactor`: Tái cấu trúc mã nguồn (không đổi logic bên ngoài)
- [ ] `test`: Bổ sung hoặc cập nhật bộ kiểm thử
- [ ] `docs`: Cập nhật tài liệu kỹ thuật
- [ ] `perf`: Cải thiện hiệu năng xử lý

## ✅ Checklist Kiểm thử & Chất lượng (Engineering DoD)
- [ ] **Code Quality**: Tuân thủ chuẩn PEP 8 (`flake8` / `black`), không có cú pháp thừa hoặc debug prints.
- [ ] **Bảo mật & RFC 5737**: Đã chạy `python tools/check_sensitive.py` và kết quả **PASSED** (100% không leak IP thật, credentials hoặc API key).
- [ ] **Unit Tests**: Đã bổ sung unit test tương ứng và chạy `python -m unittest discover -s tests` pass 100%.
- [ ] **Interface Contract**: Đảm bảo đúng chuẩn I/O và cấu trúc schema đã thống nhất trong tài liệu kỹ thuật TDD.
- [ ] **Git Branching**: Nhánh tạo đúng quy chuẩn `feature/N42-xx-<mo-ta-ngan>`.

## 📸 Bằng chứng Kiểm thử (Test Evidence)
<!-- Chèn ảnh chụp màn hình terminal test pass hoặc log chứng minh tính năng hoạt động -->
```powershell
# Dán kết quả test tại đây
```
