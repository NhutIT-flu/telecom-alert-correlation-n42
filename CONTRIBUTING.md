# Hướng dẫn Đóng góp & Quy chuẩn Phát triển Mã nguồn (Contribution Guidelines)
> **Dự án**: N4.2 — Hệ thống thu thập và phân tích cảnh báo từ router, switch và firewall  
> **Chương trình**: Học kỳ Doanh nghiệp UTH × VNPT NET (2026–2027)  
> **Áp dụng**: Toàn bộ 6 thành viên đội ngũ kỹ thuật N4.2

Tài liệu này mô tả quy ước phát triển nội bộ của nhóm N4.2. Đây không phải quy định chính thức của VNPT NET; trạng thái cấu hình repo và các gate vận hành phải được xác minh riêng.

---

## 1. Thiết lập Môi trường Phát triển (Local Setup)

### 1.1. Yêu cầu Tiên quyết
- **Python**: Phiên bản 3.12.x, đồng bộ với GitHub Actions và Jenkins.
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

1. **Định dạng và kiểm tra mã nguồn** — chạy từ thư mục gốc repo, bằng Python của môi trường đã cài `requirements.txt`:
   ```bash
   python -m black app tests tools
   python -m black --check --diff app tests tools
   python -m flake8 app tests tools --count --statistics
   ```
   Black tự sửa định dạng ở lệnh đầu; hai lệnh sau chỉ kiểm tra. Xem `git diff` trước khi commit. CI chạy hai lệnh kiểm tra và không tự sửa/commit code.

   Cấu hình chung: Black đọc `pyproject.toml` (120 ký tự, Python 3.12); Flake8 đọc `.flake8` (120 ký tự, bỏ qua W391/E203/E701). `.editorconfig` đồng bộ độ dài dòng và kiểu xuống dòng LF. Không truyền `--line-length` hoặc `--max-line-length` khác trong lệnh riêng của thành viên/CI.

   W391 cho phép dòng trắng dư cuối file; Black vẫn có thể loại bỏ chúng khi format. File vẫn cần ký tự xuống dòng kết thúc dòng cuối. E203/E701 được bỏ qua để tương thích cách Black định dạng; các kiểm tra khác của Flake8 giữ nguyên. Black không luôn rút ngắn được mọi chuỗi/comment dài, nên nếu còn E501 thì xem và sửa dòng đó thay vì bỏ qua toàn bộ E501.

   **VS Code:** cài extension **Black Formatter** của Microsoft (`ms-python.black-formatter`), chọn **Format Document With → Configure Default Formatter → Black Formatter**, bật **Editor: Format On Save** cho Python. Chọn đúng Python 3.12 của môi trường dự án và đặt **Black Formatter: Import Strategy** thành `fromEnvironment` để ưu tiên phiên bản Black đã ghim. Nếu extension thông báo fallback sang Black đi kèm, cài lại `requirements.txt` trong interpreter đã chọn. Xóa đối số độ dài dòng riêng nếu đã cấu hình trong IDE; cấu hình chuẩn nằm trong repo. Không cần thêm pre-commit ở đợt này.

   Tham chiếu: [Black với Flake8](https://black.readthedocs.io/en/stable/guides/using_black_with_other_tools.html), [Black Formatter cho VS Code](https://github.com/microsoft/vscode-black-formatter).
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
   - CI dùng `.github/workflows/ci.yml`; check tổng hợp dự kiến bắt buộc là **Code Quality & Automated Tests**. Chỉ coi merge gate hoạt động sau khi xác minh required checks và thử PR lỗi bị chặn theo [hồ sơ N42-10](docs/N42-10_HANDOVER.md).
   - Secret scan phải đạt và trả exit status phù hợp. Bộ kiểm thử CI xác minh scanner trả khác 0 khi gặp fixture nhạy cảm giả lập; không suy rộng đây là công cụ phát hiện mọi loại secret.
   - Nhận được ít nhất **01 phê duyệt (Approval)** chính thức từ **Team Leader (Phạm Minh Nhựt)** hoặc **QA Lead (Ngô Châu Kiệt)**.
3. **Cập nhật Tiến độ Jira**:
   - Khi mở PR: Kéo thẻ từ `In Progress` sang `Code Review`.
   - Chỉ chuyển thẻ sang `Done` sau review, CI xanh, merge, kiểm chứng Docker, cập nhật docs và demo theo DoD của nhóm; merge đơn lẻ chưa đủ xác nhận hoàn thành.
