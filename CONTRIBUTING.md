# Hướng dẫn Đóng góp & Quy chuẩn Phát triển Mã nguồn (Contribution Guidelines)
> **Dự án**: N4.2 — Hệ thống thu thập và phân tích cảnh báo từ router, switch và firewall  
> **Chương trình**: Học kỳ Doanh nghiệp UTH × VNPT NET (2026–2027)  
> **Áp dụng**: Toàn bộ 6 thành viên đội ngũ kỹ thuật N4.2

Tài liệu này mô tả quy ước phát triển nội bộ của nhóm N4.2. Đây không phải quy định chính thức của VNPT NET; trạng thái cấu hình repo và các gate vận hành phải được xác minh riêng.

---

## 1. Thiết lập Môi trường Phát triển (Local Setup)

### 1.1. Yêu cầu Tiên quyết
- **Python**: Phiên bản 3.12 trở lên.
- **Docker & Docker Compose**: Để chạy cơ sở dữ liệu chuỗi thời gian PostgreSQL + TimescaleDB.
- **Node.js**: Phiên bản 20+ LTS (dành cho kỹ sư Frontend React).

### 1.2. Khởi tạo Môi trường Python
```bash
# 1. Tạo môi trường ảo cô lập
python -m venv .venv

# 2. Kích hoạt môi trường ảo
# Trên Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Trên Linux / macOS:
source .venv/bin/activate

# 3. Cài đặt các gói phụ thuộc
pip install --upgrade pip
pip install -r requirements.txt
pip install flake8 black
```

### 1.3. Khởi chạy Dịch vụ CSDL
```bash
docker compose up -d db
```

---

## 2. Quy trình Git Flow & Quy chuẩn Nhánh (Branching Model)

Dự án áp dụng mô hình Feature Branching kết hợp cơ chế bảo vệ nhánh chính:

* **Nhánh chính (`main`)**: Nhánh đóng băng mã nguồn ổn định. **Nghiêm cấm push mã nguồn trực tiếp lên nhánh `main`**. Mọi thay đổi đều phải thông qua Pull Request (PR).
* **Nhánh tính năng (`feature/`)**: Nhóm thống nhất tạo nhánh riêng từ `main` theo quy tắc định danh gắn liền với mã thẻ Jira:
  ```text
  feature/N42-<mã-thẻ>-<mô-tả-ngắn-gọn>
  ```
  *Ví dụ hợp lệ*:
  - `feature/N42-10-ci-pipeline` (Kỹ sư QA)
  - `feature/N42-13-syslog-receiver` (Kỹ sư BE1)
  - `feature/N42-15-alertevent-parser` (Kỹ sư BE2)
  - `feature/N42-17-rules-yaml-design` (Kỹ sư BE3)
  - `feature/N42-19-react-vite-setup` (Kỹ sư FE)

---

## 3. Quy chuẩn Thông điệp Commit (Conventional Commits)

Mọi commit phải tuân thủ chuẩn Conventional Commits tiếng Việt không dấu hoặc tiếng Anh:

```text
<loại>: <mô tả ngắn gọn công việc> (N42-<mã-thẻ>)
```

*Các tiền tố (Type) được chấp thuận:*
- `feat:` Bổ sung tính năng mới hoặc module mới.
- `fix:` Sửa lỗi mã nguồn hoặc xử lý ngoại lệ.
- `test:` Bổ sung hoặc cập nhật ca kiểm thử tự động (Unit Test / Integration Test).
- `docs:` Cập nhật tài liệu kiến trúc, tài liệu kỹ thuật hoặc hướng dẫn.
- `refactor:` Tái cấu trúc mã nguồn mà không thay đổi hành vi nghiệp vụ.
- `chore:` Thay đổi cấu hình build, phụ thuộc thư viện hoặc công cụ hỗ trợ.

*Ví dụ hợp lệ*:
```bash
git commit -m "feat: Cai dat Asyncio DatagramProtocol cho Syslog UDP 5514 (N42-13)"
git commit -m "test: Bo sung 10 test case phan tach RFC 3164 cho Cisco va Huawei (N42-15)"
```

---

## 4. Chuẩn mực Chất lượng Mã nguồn (Code Quality Standards)

Trước khi khởi tạo Pull Request, kỹ sư bắt buộc tự kiểm tra trên máy cục bộ:

1. **Chuẩn phong cách (PEP 8 Style Guide)**:
   ```bash
   flake8 app tests tools --count --max-line-length=120
   ```
2. **Kiểm thử Đơn vị (Automated Unit Testing)**:
   Mọi module mới bắt buộc phải có tệp kiểm thử tương ứng trong thư mục `tests/`:
   ```bash
   python -m unittest discover -s tests -p "test_*.py"
   ```
   *Yêu cầu*: kiểm thử tự động thuộc phạm vi thay đổi phải đạt; chỉ ghi kết quả đã chạy và có log/evidence.

---

## 5. Quy chuẩn An toàn Thông tin & Bảo mật (Security Compliance)

Dự án vận hành trên nguyên tắc an toàn dữ liệu viễn thông tuyệt đối:

1. **Dải IP và định danh dữ liệu giả lập**:
   - Bắt buộc sử dụng dải IP thử nghiệm được chuẩn hóa quốc tế theo **RFC 5737 / RFC 1918**:
     - `10.0.0.0/8` (Mạng nội bộ mô phỏng).
     - `192.168.0.0/16` (Mạng quản trị thiết bị mô phỏng).
     - `203.0.113.0/24` (TEST-NET-3 cho IP Wan/Internet giả định).
   - **Tuyệt đối nghiêm cấm**: Sử dụng IP public thực tế hoặc cấu hình thật của VNPT NET.
2. **Không Lưu trữ Thông tin Bí mật (Zero Credential Leak)**:
   - Nghiêm cấm hardcode password, API token, secret key vào mã nguồn. Sử dụng tệp `.env` (đã nằm trong `.gitignore`).
   - Chạy công cụ kiểm tra bảo mật bắt buộc:
     ```bash
     python tools/check_sensitive.py
     ```
     Chỉ khi kết quả báo `[✔] AN TOÀN: Không phát hiện từ khóa nhạy cảm` mới được phép push mã nguồn.

---

## 6. Cổng sẵn sàng trước khi bắt đầu code

Đây là quy ước nội bộ của nhóm, không phải tuyên bố về chính sách chính thức của VNPT NET. Ticket thay đổi hành vi chỉ chuyển sang `In Progress` khi có yêu cầu/tiêu chí chấp nhận, owner, Test Case Specification (input, expected output, positive/negative và boundary cases phù hợp), và dòng truy vết trong `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md`. QA Lead chủ trì test case và coverage; BE/FE owner xác nhận contract và expected result. Unit test thuộc owner code; QA quản lý tích hợp, CI/workflow và evidence. Đặc tả chưa đồng nghĩa với automated coverage hoặc kết quả PASS.

## 7. Quy trình Code Review & Nghiệm thu Pull Request (PR)

1. **Khởi tạo PR**:
   - Điền đầy đủ mô tả công việc, bằng chứng thực thi (kết quả test) và dẫn liên kết thẻ Jira tương ứng.
   - Gắn nhãn (Labels) phù hợp (`backend`, `frontend`, `qa`, `devops`).
2. **Điều kiện Hợp nhất (Merge Criteria)**:
   - Policy nhóm đặt CI xanh làm mục tiêu merge gate. Hiện repo chưa có workflow GitHub Actions; QA Lead dự kiến triển khai checks, ghi run evidence và phối hợp xác minh required checks/branch protection trước khi coi đây là gate đang hoạt động.
   - Secret scan phải chạy bằng công cụ có exit status phù hợp; hiện công cụ cần được sửa/kiểm chứng trước khi dùng làm required check.
   - Nhận được ít nhất **01 phê duyệt (Approval)** chính thức từ **Team Leader (Phạm Minh Nhựt)** hoặc **QA Lead (Ngô Châu Kiệt)**.
3. **Cập nhật Tiến độ Jira**:
   - Khi mở PR: Kéo thẻ từ `In Progress` sang `Code Review`.
   - Sau khi PR được merge vào `main`: Kéo thẻ sang `Done` và đóng thẻ.
