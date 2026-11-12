# HƯỚNG DẪN CÀI ĐẶT & SỬ DỤNG JENKINS VÀ SONARQUBE TRÊN MÁY MỚI (DỰ ÁN N4.2)

> **Jenkins/SonarQube — cập nhật 12/11/2026:** dùng [JENKINS_SONAR_RUNBOOK.md](JENKINS_SONAR_RUNBOOK.md) cho Python 3.12, job main tự động và Quality Gate bắt buộc. Các hướng dẫn pipeline 4 stage/Python hệ điều hành bên dưới là cấu hình trước thay đổi này; không dùng để xác nhận bản mới đã triển khai. Giữ scanner/server name theo runbook và cấu hình thực tế.

> **GitHub Actions (cập nhật N42-10 ngày 12/11/2026):** xem [GITHUB_ACTIONS_GUIDE.md](GITHUB_ACTIONS_GUIDE.md) cho cấu trúc job, dependency CI, artifact và kiểm chứng. Thay đổi này không đồng nghĩa Jenkins/SonarQube đã được cập nhật hoặc branch protection đã bật.

> **Dự án:** N4.2 — Hệ thống thu thập và phân tích cảnh báo từ router, switch và firewall  
> **Phụ trách hạ tầng CI/CD & QA (Module M8):** Ngô Châu Kiệt (QA Lead)  
> **Đối tượng áp dụng:** Toàn bộ thành viên nhóm kỹ thuật N4.2 khi thiết lập môi trường trên máy mới  

---

## 1. Tổng quan Kiến trúc CI/CD Local

Bên cạnh pipeline tự động trên **GitHub Actions** (`.github/workflows/ci.yml`), dự án N4.2 tích hợp sẵn cụm **PostgreSQL (TimescaleDB) + Jenkins + SonarQube** trong file [`docker-compose.yml`](../docker-compose.yml) ở thư mục gốc. Cả nhóm có thể khởi chạy bằng **1 lệnh duy nhất** để kiểm tra tự động chất lượng mã nguồn, quét bảo mật và đo độ bao phủ kiểm thử (Code Coverage) ngay trên máy cá nhân.

### 1.1. Các tệp cấu hình trong Repository
| Tệp cấu hình | Vị trí | Chức năng |
| :--- | :--- | :--- |
| `docker-compose.yml` | Thư mục gốc | Định nghĩa đồng bộ 4 dịch vụ: `db`, `app`, `jenkins`, `sonarqube` trên mạng nội bộ `n42-network`. |
| `docker/init-db.sql` | `docker/` | Khởi tạo extension `timescaledb` cho DB `n42` và tự động tạo database `sonarqube` riêng trên PostgreSQL. |
| `Dockerfile.jenkins` | Thư mục gốc | Dựng image `jenkins/jenkins:lts-jdk21` tích hợp sẵn `python3`, `python3-venv`, `python3-pip` và `git`. |
| `Jenkinsfile` | Thư mục gốc | Pipeline 4 stages: `Checkout` $\rightarrow$ `Code Quality & AI Kit Validation` $\rightarrow$ `Security Scan & Unit Tests` $\rightarrow$ `SonarQube Analysis`. |
| `sonar-project.properties` | Thư mục gốc | Cấu hình `sonar.projectKey=n42-telecom-alert`, Python `3.12`, báo cáo coverage `coverage.xml` và danh sách thư mục loại trừ. |

### 1.2. Quy hoạch Cổng Dịch vụ (Port Mapping)
| Dịch vụ | Tên Container | Cổng truy cập trên máy (Host) | Cổng nội bộ Docker (`n42-network`) | Ghi chú |
| :--- | :--- | :--- | :--- | :--- |
| **PostgreSQL / TimescaleDB** | `n42-db` | `localhost:5432` | `db:5432` | Chứa DB `n42` (App) và DB `sonarqube` (SonarQube) |
| **FastAPI App** | `n42-app` | `localhost:8080` *(profile `full`)* | `app:8080` | REST API & Swagger UI |
| **Jenkins CI** | `n42-jenkins` | **`http://localhost:8000`** | `jenkins:8080` | Giao diện quản trị Jenkins |
| **SonarQube** | `n42-sonarqube` | **`http://localhost:9000`** | `sonarqube:9000` | Giao diện phân tích mã nguồn (dùng PostgreSQL `n42-db`) |

---

## 2. Quy trình Cài đặt từ đầu trên Máy Mới (4 Bước)

### Bước 1: Khởi chạy cụm dịch vụ bằng Docker Compose
Tại thư mục gốc của repo `telecom-alert-correlation-n42`, mở **PowerShell / Terminal** và chạy:

```powershell
docker compose up -d --build
```
- Lệnh này sẽ tự động:
  1. Khởi tạo `n42-db` (PostgreSQL 16 + TimescaleDB) và chạy `docker/init-db.sql` để tạo sẵn database `sonarqube`.
  2. Khi `n42-db` đạt trạng thái `healthy`, khởi chạy `n42-sonarqube` kết nối trực tiếp vào PostgreSQL (`jdbc:postgresql://db:5432/sonarqube` — hoàn toàn không còn cảnh báo Embedded Database).
  3. Build image `Dockerfile.jenkins` (có sẵn Python 3) và khởi chạy `n42-jenkins` tại cổng `8000`.

Kiểm tra các container đã chạy ổn định (`Up`):
```powershell
docker compose ps
```

---

### Bước 2: Thiết lập SonarQube & Tạo Token (`http://localhost:9000`)
1. Mở trình duyệt truy cập **`http://localhost:9000`** (đợi khoảng 30–60 giây để SonarQube khởi tạo xong 185 bảng dữ liệu trong PostgreSQL).
2. Đăng nhập lần đầu bằng tài khoản mặc định:
   - **Login:** `admin`
   - **Password:** `admin`
3. Đổi mật khẩu mới cho tài khoản `admin` khi hệ thống yêu cầu.
4. **Sinh Token kết nối cho Jenkins**:
   - Nhấn vào biểu tượng **Avatar** (góc trên bên phải) $\rightarrow$ **My Account** $\rightarrow$ tab **Security** (`http://localhost:9000/account/security`).
   - Tại mục **Generate Tokens**:
     - **Name:** `jenkins-n42-token`
     - **Type:** Chọn **`Global Analysis Token`** (hoặc `User Token`)
     - **Expires in:** `No expiration` (hoặc `30 days`)
     - Nhấn **Generate** và **sao chép (Copy)** chuỗi Token vừa hiển thị.

---

### Bước 3: Thiết lập Jenkins (`http://localhost:8000`)

#### 3.1. Mở khóa Jenkins & Cài đặt Plugin mặc định
1. Mở trình duyệt truy cập **`http://localhost:8000`**.
2. Lấy mật khẩu mở khóa lần đầu bằng lệnh trong PowerShell:
   ```powershell
   docker exec n42-jenkins cat /var/jenkins_home/secrets/initialAdminPassword
   ```
3. Dán mã vừa lấy vào trang **Unlock Jenkins** $\rightarrow$ nhấn **Continue**.
4. Chọn **Install suggested plugins** $\rightarrow$ tạo tài khoản Admin cá nhân $\rightarrow$ tại bước **Instance Configuration**, giữ nguyên **Jenkins URL** là `http://localhost:8000/` và nhấn **Save and Finish**.

#### 3.2. Cài đặt Plugin `SonarQube Scanner`
1. Từ trang chủ Jenkins, vào **Manage Jenkins** $\rightarrow$ **Plugins** $\rightarrow$ chọn tab **Available plugins**.
2. Gõ vào ô tìm kiếm: **`SonarQube Scanner`**.
3. Tích chọn plugin **SonarQube Scanner** và nhấn **Install**.

#### 3.3. Thêm Credential chứa Token của SonarQube
1. Vào **Manage Jenkins** $\rightarrow$ **Credentials** $\rightarrow$ **System** $\rightarrow$ **Global credentials (unrestricted)** $\rightarrow$ nhấn **Add Credentials**.
2. Điền thông tin:
   - **Kind:** Chọn `Secret text`.
   - **Scope:** `Global (Jenkins, nodes, items, all child items, etc)`.
   - **Secret:** Dán chuỗi Token của SonarQube đã copy ở Bước 2.
   - **ID:** `sonarqube-n42-token`
   - **Description:** `SonarQube Token for N42`
3. Nhấn **Create**.

#### 3.4. Liên kết Server SonarQube (`SonarQube-N42`)
1. Vào **Manage Jenkins** $\rightarrow$ **System** (`http://localhost:8000/manage/configure`).
2. Cuộn xuống mục **SonarQube servers** $\rightarrow$ nhấn **Add SonarQube**:
   - Tích chọn **Environment variables**.
   - **Name:** `SonarQube-N42` *(Bắt buộc nhập đúng chính xác tên này để khớp với `withSonarQubeEnv('SonarQube-N42')` trong `Jenkinsfile`)*.
   - **Server URL:** `http://sonarqube:9000` *(Sử dụng tên service nội bộ trong mạng Docker `n42-network`, không để dấu `/` ở cuối và không dùng `localhost`)*.
   - **Server authentication token:** Chọn `sonarqube-n42-token`.
3. Nhấn **Save**.

#### 3.5. Cấu hình công cụ `SonarScanner`
1. Vào **Manage Jenkins** $\rightarrow$ **Tools** (`http://localhost:8000/manage/configureTools`).
2. Cuộn xuống mục **SonarQube Scanner installations** $\rightarrow$ nhấn **Add SonarQube Scanner**:
   - **Name:** `SonarScanner` *(Bắt buộc nhập đúng chính xác tên này để khớp với `tool 'SonarScanner'` trong `Jenkinsfile`)*.
   - Tích chọn **Install automatically** (tự động tải từ Maven Central khi chạy build).
3. Nhấn **Save**.

---

### Bước 4: Tạo Pipeline Job và Chạy Kiểm tra Tự động
1. Từ trang chủ Jenkins (`http://localhost:8000`), nhấn **New Item**.
2. Nhập tên Job: **`N42-Telecom-Alert-Correlation`** $\rightarrow$ chọn **Pipeline** $\rightarrow$ nhấn **OK**.
3. Cuộn xuống phần **Pipeline**:
   - **Definition:** Chọn `Pipeline script from SCM`.
   - **SCM:** Chọn `Git`.
   - **Repository URL:** `https://github.com/NhutIT-flu/telecom-alert-correlation-n42.git`
   - **Branches to build (Branch Specifier):** `*/main` *(hoặc nhánh tính năng bạn đang kiểm tra, ví dụ `*/feature/N42-10-ci-pipeline`)*.
   - **Script Path:** `Jenkinsfile`
4. Nhấn **Save**, sau đó bấm **Build Now** ở menu bên trái.
5. Pipeline sẽ tự động thực thi **4 stages**:
   - **Stage 1 (`Checkout`)**: Kéo mã nguồn từ GitHub.
   - **Stage 2 (`Code Quality & AI Kit Validation`)**: Tạo `.venv`, kiểm tra `flake8`, `black --check` (`--max-line-length=120`) và `n42-ai-kit/scripts/validate.py`.
   - **Stage 3 (`Security Scan & Unit Tests`)**: Quét bảo mật `python3 tools/check_sensitive.py .`, chạy `unittest` và `pytest --cov=app --cov-report=xml:coverage.xml`.
   - **Stage 4 (`SonarQube Analysis`)**: Chạy `sonar-scanner` đẩy kết quả phân tích tĩnh và độ bao phủ test sang SonarQube.
6. Khi cả 4 stages hiện màu xanh (`SUCCESS`), truy cập **`http://localhost:9000/dashboard?id=n42-telecom-alert`** để xem báo cáo chất lượng mã nguồn trên SonarQube.

---

## 3. Xử lý Sự cố Thường gặp (Troubleshooting)

1. **Container `n42-sonarqube` tự động tắt sau vài giây (Exit code 137 / 78 trên Windows WSL2 / Linux)**:
   - **Nguyên nhân:** Elasticsearch bên trong SonarQube yêu cầu giới hạn bộ nhớ ảo `vm.max_map_count >= 262144`.
   - **Cách khắc phục (chạy trong PowerShell):**
     ```powershell
     wsl -d docker-desktop -u root sysctl -w vm.max_map_count=262144
     docker compose restart sonarqube
     ```
2. **Jenkins báo lỗi `SonarQube installation defined in this job (SonarQube-N42) does not match any configured installation`**:
   - Vào **Manage Jenkins $\rightarrow$ System $\rightarrow$ SonarQube servers**, kiểm tra trường **Name** đã đặt chính xác là `SonarQube-N42` chưa.
3. **Jenkins báo lỗi `No tool named SonarScanner found`**:
   - Vào **Manage Jenkins $\rightarrow$ Tools $\rightarrow$ SonarQube Scanner installations**, kiểm tra trường **Name** đã đặt chính xác là `SonarScanner` chưa.
4. **Jenkins không kết nối được tới SonarQube khi để URL là `http://localhost:9000`**:
   - Bên trong container `n42-jenkins`, `localhost` là chính container Jenkins. Hãy đổi **Server URL** trong cấu hình SonarQube của Jenkins thành **`http://sonarqube:9000`**.
