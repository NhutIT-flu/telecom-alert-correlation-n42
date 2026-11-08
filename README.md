# N4.2 — Hệ thống Thu thập và Phân tích Cảnh báo Mạng Viễn thông
### Telecom Alert Ingestion & Real-Time Correlation System (UTH × VNPT NET)

[![Python 3.12](https://img.shields.io/badge/Python-3.12%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![TimescaleDB](https://img.shields.io/badge/Database-TimescaleDB%20%2F%20PostgreSQL-336791.svg?logo=postgresql&logoColor=white)](https://www.timescale.com/)
[![React 18](https://img.shields.io/badge/Frontend-React%2018%20%2F%20Vite-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Container-Docker%20Compose-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![Jira](https://img.shields.io/badge/Jira-N42%20Project-0052CC.svg?logo=jira&logoColor=white)](https://nhutp2945-1793259952237.atlassian.net/)

---

## 1. Giới thiệu Đề tài

> **Phạm vi trạng thái:** README mô tả mục tiêu sản phẩm. Baseline code hiện chỉ có FastAPI `GET /api/health`; ingest, parser, queue, database, correlation và dashboard chưa được triển khai. KPI dưới đây là tiêu chí mục tiêu trong `docs/ACCEPTANCE_CRITERIA.md`, không phải kết quả đã đo.

Dự án **N4.2** hướng tới xây dựng sản phẩm nghiên cứu trong khuôn khổ **Học kỳ Doanh nghiệp (HK26)** giữa **Trường Đại học Giao thông Vận tải TP.HCM (UTH)** và **VNPT NET**. Môi trường hiện tại dùng dữ liệu giả lập trong lab; không kết nối thiết bị production.

Hệ thống được thiết kế để hỗ trợ phân tích bão cảnh báo và quá tải cảnh báo từ các mẫu log giả lập của thiết bị mạng. Mô tả này là mục tiêu đề tài, không phải kết quả khảo sát hoặc số liệu vận hành của VNPT NET.

### Mục tiêu kỹ thuật cốt lõi:
- **Thông lượng tiếp nhận:** Mục tiêu nghiệm thu là $\ge 1.000\text{ msg/s}$ theo điều kiện đo ở `docs/ACCEPTANCE_CRITERIA.md`.
- **Chuẩn hóa dữ liệu:** Mục tiêu là parser đa định dạng theo corpus có nhãn và schema được duyệt.
- **Khử trùng và gom cụm:** Mục tiêu nghiệm thu giảm nhiễu tối thiểu 70% trên scenario đóng băng; chưa có kết quả đo baseline.
- **Dashboard:** Là thành phần mục tiêu; chưa có frontend trong baseline repo.

---

## 2. Kiến trúc mục tiêu (chưa phải baseline đã triển khai)

```mermaid
flowchart TD
    subgraph DataSources["Tầng thiết bị mạng và nguồn giả lập"]
        direction LR
        cisco["Router Cisco ASR"]
        huawei["Switch Huawei NE"]
        forti["Firewall Fortinet"]
        gen["QA Syslog Generator (>= 1.000 msg/s)"]
    end

    subgraph Ingestion["Tầng Thu thập (M1) và Chuẩn hóa (M2)"]
        udp["UDP Receiver (Port 5514)"]
        parser["Multi-Vendor Parser Engine<br/>(Regex / CEF / Syslog RFC 5424)"]
    end

    subgraph CoreEngine["Queue (M3), Lưu trữ (M4), Luật (M5), Correlation (M6)"]
        queue["Async Queue Buffer / In-Memory Queue"]
        rules["Rule Engine (rules.yaml)"]
        engine["Sliding Window Correlation Engine<br/>(Deduplication & Root Cause Analysis)"]
        db[("TimescaleDB Hypertable<br/>(Time-Series Event Storage)")]
    end

    subgraph Presentation["Tầng Correlation/API (M6) & Dashboard (M7)"]
        api["FastAPI Core Service (REST API & WebSockets)"]
        ui["NOC Operational Dashboard (React Dark Mode)"]
    end

    DataSources -->|UDP Syslog Datagrams| udp
    udp -->|Raw Log Stream| parser
    parser -->|Normalized Events| queue
    queue --> engine
    rules -.->|Load Logic| engine
    engine -->|Batch Insert Hypertable| db
    engine -->|Push Incident Stream| api
    db -.->|Historical Query| api
    api -->|WebSocket / HTTP REST| ui
```

---

## 3. Cấu trúc Dự án (Project Layout)

```text
telecom-alert-correlation-n42/
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md   # Khung mở PR chuẩn doanh nghiệp
├── app/                           # Mã nguồn Backend Core (FastAPI)
│   ├── __init__.py
│   ├── main.py                    # Điểm khởi chạy API Gateway & Routers
│   └── ...                        # Các module target module nghiệp vụ được phát triển theo Jira; QA tooling thuộc QA Lead
├── docker/                        # Khởi tạo extension DB
│   └── init-db.sql
├── Dockerfile                     # Image FastAPI scaffold
├── docs/                          # Hồ sơ thiết kế kỹ thuật chuẩn VNPT NET
│   ├── ARCHITECTURE_DESIGN.md     # Kiến trúc hệ thống tổng thể
│   ├── DATA_AND_API_DESIGN.md     # Thiết kế cơ sở dữ liệu và REST API
│   ├── PROJECT_CHARTER.md         # Điều lệ dự án & cam kết mục tiêu
│   ├── SYSTEM_REQUIREMENTS...     # Đặc tả yêu cầu kỹ thuật & Use cases
│   └── TECHNICAL_DESIGN_DOC...    # Tài liệu thiết kế kỹ thuật (TDD)
├── tests/                         # Bộ kiểm thử tự động (Unit & Integration Tests)
│   ├── __init__.py
│   └── test_health.py             # 2 kiểm tra liveness baseline; chưa có test nghiệp vụ backend
├── tools/                         # Công cụ hỗ trợ DevOps & Kiểm tra an toàn
│   └── check_sensitive.py         # Quét chống rò rỉ credential & IP nhạy cảm
├── .editorconfig                  # Quy chuẩn định dạng mã nguồn nhất quán
├── .gitignore                     # Danh mục loại trừ tệp nháp, cache và môi trường
├── CONTRIBUTING.md                # Quy chuẩn đóng góp mã nguồn & Git Flow
├── docker-compose.yml             # Cấu hình khởi chạy cụm TimescaleDB & Service
├── README.md                      # Tài liệu tổng quan dự án
└── requirements.txt               # Danh mục thư viện phụ thuộc Python
```

---

## 4. Hướng dẫn Khởi chạy Baseline (Getting Started)

### Yêu cầu môi trường:
- **Python**: Phiên bản 3.12 trở lên.
- **Git**: Đã cài đặt Git CLI.
- **Docker & Docker Compose**: (Tùy chọn) để chạy dịch vụ TimescaleDB.

### Các bước cài đặt:

```powershell
# 1. Clone repository
git clone https://github.com/NhutIT-flu/telecom-alert-correlation-n42.git
cd telecom-alert-correlation-n42

# 2. Tạo và kích hoạt môi trường ảo
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Cài đặt các thư viện phụ thuộc
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4. Kiểm tra an toàn thông tin (Quét IP thật và bảo mật)
python tools/check_sensitive.py

# 5. Khởi chạy Backend API Gateway
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Health Check**: `GET http://127.0.0.1:8000/api/health`
- **Tài liệu Swagger OpenAPI**: `http://127.0.0.1:8000/docs`
- **Chạy kiểm thử Unit Test**: `python -m unittest discover -s tests -p "test_*.py"`

---

## 5. Quy chuẩn Đóng góp & Phát triển (Git Flow)

Mọi thành viên tuân thủ [Quy chuẩn Đóng góp (CONTRIBUTING.md)](CONTRIBUTING.md). Các mục CI/review là policy nhóm; trạng thái cấu hình GitHub thực tế phải được kiểm tra riêng:

1. **Nhánh phát triển**: Tạo nhánh từ ticket Jira được giao theo mẫu:
   ```bash
   feature/N42-<id>-<mo-ta-ngan>   # Ví dụ: feature/N42-10-syslog-udp-receiver
   ```
2. **Quy tắc Commit (Conventional Commits)**:
   ```bash
   feat: Bổ sung module UDP receiver lắng nghe port 5514 [N42-10]
   fix: Khắc phục lỗi tràn bộ đệm in-memory queue khi tải cao [N42-13]
   test: Bổ sung 5 ca kiểm thử bóc tách định dạng Huawei syslog [N42-12]
   ```
3. **Quy định An toàn Thông tin (RFC 5737)**: Tuyệt đối không hardcode địa chỉ IP thực, mật khẩu, token hệ thống vào code hoặc tài liệu. IP lab dùng dải riêng RFC1918, ví dụ `10.10.0.0/16`; các dải RFC5737 chỉ dùng minh họa trong tài liệu.
4. **Quy trình Mở Pull Request**: PR phải điền đầy đủ form theo `.github/PULL_REQUEST_TEMPLATE.md`, pass toàn bộ required CI checks đã cấu hình và có evidence và có ít nhất **1 phê duyệt (Approved)** từ Team Leader hoặc QA Lead trước khi được merge vào `main`.

---

## 6. Ban Quản trị & Nhóm Kỹ sư Dự án

| STT | Họ và Tên | MSSV | Vai trò Trách nhiệm | Module Phụ trách |
|:---:|:---|:---:|:---|:---|
| 1 | **Phạm Minh Nhựt** | `082205017237` | **Team Leader / PM & Quản trị Dự án** | Quản trị chung, Jira/Confluence, tiến độ, điều phối |
| 2 | **Nguyễn Duy Minh** | `083205002424` | **Backend Engineer 3 (BE3)** | Correlation, grouping, rules và API liên quan |
| 3 | **Ngô Châu Kiệt** | `083205002376` | **QA Lead** | Test Case/coverage, fixtures, scenarios, CI coordination, load/evidence tooling |
| 4 | **Phạm Hoàng Long** | `0822065010353` | **Backend Engineer 1 (BE1)** | UDP receiver và ingestion adapters |
| 5 | **Phạm Tấn Thành** | `082205009270` | **Backend Engineer 2 (BE2)** | Parser/normalization và persistence/query; owner split cần đối chiếu |
| 6 | **Lê Khắc Huy** | `082205014597` | **Frontend Engineer (FE)** | Dashboard và export |

---
*Dự án thuộc chương trình Học kỳ Doanh nghiệp UTH × VNPT NET. Mọi quyền sở hữu trí tuệ và bảo mật tuân thủ thỏa thuận liên kết đào tạo.*
