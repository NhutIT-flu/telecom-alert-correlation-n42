# TÀI LIỆU THIẾT KẾ KIẾN TRÚC VÀ CÁC PHÂN HỆ THÀNH PHẦN HỆ THỐNG
## (SYSTEM ARCHITECTURE DESIGN & COMPONENT SPECIFICATION — N4.2)

> **Mã văn bản:** `VNPT-NET-N42-ADD-2026-V2.0`  
> **Dự án:** N4.2 — Hệ thống thu thập và phân tích tương quan cảnh báo từ Router, Switch và Firewall  
> **Đơn vị chủ trì:** Trung tâm Điều hành Khai thác Mạng VNPT NET (VNPT NOC)  
> **Cơ sở đào tạo:** Trường ĐH Giao thông Vận tải TP.HCM (UTH) — Học kỳ Doanh nghiệp  
> **Chủ nhiệm Kỹ thuật / PM & DevOps:** **Phạm Minh Nhựt**  
> **Chủ nhiệm QA & Kiểm thử:** **Ngô Châu Kiệt**  
> **Kỹ sư Phân hệ Backend:** **Phạm Hoàng Long (BE1)**, **Phạm Tấn Thành (BE2)**, **Nguyễn Duy Minh (BE3)**  
> **Kỹ sư Giao diện Frontend:** **Lê Khắc Huy (FE)**  
> **Tài liệu liên kết:** `SYSTEM_REQUIREMENTS_AND_USE_CASES.md`, `DATA_AND_API_DESIGN.md`, `TEST_CASE_SPECIFICATION.md`, `DECISIONS.md`.

---

## 1. NGUYÊN TẮC THIẾT KẾ CỐT LÕI (CORE ARCHITECTURAL PRINCIPLES)

1. **Bảo toàn Dữ liệu Gốc Tuyệt đối (Raw Preservation):**  
   Mọi bản tin cảnh báo từ thiết bị mạng gửi về (Syslog UDP, REST Ingest, File nhật ký) đều được giữ nguyên vẹn 100% trong trường `raw_message`. Quá trình chuẩn hóa chỉ bổ sung các trường trích xuất, tuyệt đối không ghi đè làm mất vết dấu vết phục vụ hậu kiểm an toàn thông tin.

2. **Xử lý Bất đồng bộ & Kiểm soát Bộ đệm (Asynchronous & Bounded Buffering):**  
   Toàn bộ luồng thu nạp sử dụng cơ chế xử lý phi phong bế (Non-blocking I/O) trên nền tảng `asyncio`. Thiết lập giới hạn kích thước hàng đợi trong bộ nhớ (Bounded Queue: 4MB socket buffer, 10.000 events queue) để chống tràn bộ nhớ (Out-Of-Memory - OOM) và kiểm soát áp lực ngược (Backpressure) khi xảy ra bão cảnh báo viễn thông.

3. **Phân rã Độc lập & Tính Định chuẩn (Loose Coupling & Determinism):**  
   Các phân hệ Thu thập (M1), Chuẩn hóa (M2), Tương quan (M5/M6), Lưu trữ (M4) và Hiển thị (M7) hoạt động độc lập qua các hợp đồng giao tiếp chuẩn hóa (`AlertEvent`, `Incident`, `Pydantic Schema`). Động cơ tương quan cho ra kết quả nhất quán trên cùng một kịch bản phát tải.

4. **Cách ly Môi trường Thử nghiệm An toàn (Isolated Lab Environment):**  
   Hệ thống vận hành độc lập trên môi trường máy chủ Lab; chỉ sử dụng dải địa chỉ mạng nội bộ mô phỏng RFC 1918 (`10.10.0.0/16`) và RFC 5737 (`203.0.113.0/24`). Tuyệt đối không can thiệp, gửi lệnh cấu hình hay tác động ngược lại thiết bị mạng viễn thông thật của VNPT NET.

---

## 2. NGỮ CẢNH HỆ THỐNG VÀ CÁC BÊN LIÊN QUAN (SYSTEM CONTEXT DIAGRAM)

Sơ đồ ngữ cảnh thể hiện luồng giao tiếp giữa Hệ thống N4.2 với các tác nhân bên ngoài:

```mermaid
flowchart TB
    subgraph EXTERNAL["CÁC TÁC NHÂN BÊN NGOÀI"]
        DEVICES["Thiết bị Mạng Viễn thông Mô phỏng<br/>(Router Cisco, Switch Huawei, Firewall Fortinet)"]
        QA_GEN["Bộ Sinh Cảnh báo Giả lập & Đo tải<br/>(QA Tooling CLI - Ngô Châu Kiệt)"]
        OPERATOR["Kỹ sư Vận hành Giám sát NOC<br/>(Trực ban Đài điều hành mạng)"]
        ADMIN["Quản trị viên Hệ thống / Kỹ sư BE3<br/>(Phạm Minh Nhựt / Nguyễn Duy Minh)"]
    end

    subgraph SYSTEM_N42["HỆ THỐNG GIÁM SÁT & PHÂN TÍCH CẢNH BÁO MẠNG N4.2"]
        INGEST["Phân hệ Tiếp nhận Dữ liệu Đa nguồn<br/>(UDP 5514, REST Ingest, Batch File)"]
        PIPELINE["Động cơ Chuẩn hóa & Xử lý Tương quan<br/>(Multi-vendor Parser & Sliding Window)"]
        STORAGE["Kho Lưu trữ Dữ liệu Chuỗi Thời gian<br/>(TimescaleDB Hypertable & EventStore)"]
        API_GATEWAY["Cổng Giao tiếp Dịch vụ & WebSocket<br/>(FastAPI High Performance Engine)"]
        DASHBOARD["Giao diện Điều hành Giám sát Trực quan<br/>(React 18 + Tailwind CSS Dark Mode)"]
    end

    DEVICES -->|Dòng bản tin Syslog UDP cổng 5514| INGEST
    QA_GEN -->|Kịch bản bão cảnh báo & đo tải 1.000 msg/s| INGEST
    QA_GEN -->|Bơm dữ liệu kiểm thử qua HTTP REST / File| INGEST

    INGEST --> PIPELINE
    PIPELINE --> STORAGE
    STORAGE <--> API_GATEWAY
    PIPELINE -.->|Bắn sự cố khẩn cấp tức thì| API_GATEWAY

    API_GATEWAY <-->|Kết nối REST Query & WebSocket hai chiều| DASHBOARD
    DASHBOARD <-->|Theo dõi cảnh báo, lọc sự cố, tra cứu lịch sử| OPERATOR
    ADMIN -->|Cấu hình bộ luật rules.yaml, kiểm tra sức khỏe| API_GATEWAY
```

---

## 3. KIẾN TRÚC PHÂN TẦNG VÀ THÀNH PHẦN CHỨC NĂNG (CONTAINER & COMPONENT ARCHITECTURE)

Toàn bộ hệ thống được phân rã thành 5 phân tầng chức năng rõ rệt:

```mermaid
flowchart TB
    subgraph TANG_1["TẦNG 1: TIẾP NHẬN DỮ LIỆU ĐA NGUỒN (INGESTION LAYER - MODULE M1)"]
        direction LR
        UDP_RECV["Bộ Thu nhận Syslog UDP :5514<br/>(asyncio.DatagramProtocol)"]
        REST_RECV["Cổng Tiếp nhận REST API<br/>(POST /api/v1/events/ingest)"]
        FILE_RECV["Bộ Nạp Tệp Nhật ký Hàng loạt<br/>(Batch File Log Adapter)"]
        INPUT_GUARD["Bộ Đệm An toàn & Kiểm định Đầu vào<br/>(Input Guard / Envelope 4MB Buffer)"]
        
        UDP_RECV --> INPUT_GUARD
        REST_RECV --> INPUT_GUARD
        FILE_RECV --> INPUT_GUARD
    end

    subgraph TANG_2["TẦNG 2: CHUẨN HÓA & PHÂN TÍCH CÚ PHÁP (NORMALIZATION LAYER - MODULE M2)"]
        direction LR
        ROUTER_PARSER["Bộ Phân tích Cú pháp Đa Hãng<br/>(Multi-Vendor Parser Engine)"]
        CISCO_P["Parser Cisco IOS / Nexus"]
        HUAWEI_P["Parser Huawei NE40E / VRP"]
        JUNIPER_P["Parser Juniper Junos MX960"]
        FORTINET_P["Parser Fortinet FortiGate"]
        RAW_FALLBACK["Cơ chế Lưu trữ Thô Dự phòng<br/>(Quarantine / RAW Fallback)"]

        ROUTER_PARSER --> CISCO_P
        ROUTER_PARSER --> HUAWEI_P
        ROUTER_PARSER --> JUNIPER_P
        ROUTER_PARSER --> FORTINET_P
        ROUTER_PARSER --> RAW_FALLBACK
    end

    subgraph TANG_3["TẦNG 3: XỬ LÝ HÀNG ĐỢI & TƯƠNG QUAN SỰ CỐ (CORRELATION & FSM - MODULE M3, M5, M6)"]
        BOUNDED_QUEUE["Hàng đợi Có giới hạn trong Bộ nhớ<br/>(Bounded In-Memory Queue: 10.000 msgs)"]
        CORR_ENGINE["Động cơ So khớp Luật Tương quan<br/>(Sliding Window Correlation Engine)"]
        FLAP_FSM["Cỗ máy Trạng thái Khử dao động Cổng<br/>(Link Flap Finite State Machine)"]
        RULE_MANAGER["Bộ Quản lý & Thẩm định Cấu hình Luật<br/>(Pydantic RuleSchema & rules.yaml 1.2)"]

        BOUNDED_QUEUE --> CORR_ENGINE
        RULE_MANAGER --> CORR_ENGINE
        CORR_ENGINE <--> FLAP_FSM
    end

    subgraph TANG_4["TẦNG 4: LƯU TRỮ CHUỖI THỜI GIAN (STORAGE & PERSISTENCE - MODULE M4)"]
        EVENT_STORE["Giao diện Quản lý Lưu trữ Sự kiện<br/>(EventStore Abstraction Interface)"]
        MEM_STORE["Bộ nhớ Đệm Vòng Tạm thời<br/>(InMemory Ring Buffer W1-W4)"]
        TS_DB[("Cơ sở Dữ liệu Chuỗi Thời gian<br/>PostgreSQL + TimescaleDB Hypertable")]

        EVENT_STORE --> MEM_STORE
        EVENT_STORE --> TS_DB
    end

    subgraph TANG_5["TẦNG 5: CỔNG DỊCH VỤ & GIAO DIỆN NGƯỜI DÙNG (PRESENTATION LAYER - MODULE M7)"]
        API_GW["Cổng Lập trình Ứng dụng Backend<br/>(FastAPI Query, Health, Incident API)"]
        WS_HUB["Kênh Truyền phát Thời gian thực<br/>(WebSocket Real-time Alert Broadcast)"]
        UI_DASHBOARD["Bảng Điều hành Giám sát NOC Trung tâm<br/>(React 18 + Vite + Tailwind CSS Dark Mode)"]

        API_GW <--> UI_DASHBOARD
        WS_HUB --> UI_DASHBOARD
    end

    INPUT_GUARD --> ROUTER_PARSER
    ROUTER_PARSER --> BOUNDED_QUEUE
    CORR_ENGINE --> EVENT_STORE
    EVENT_STORE <--> API_GW
    CORR_ENGINE -.->|Bắn sự cố mới tức thời| WS_HUB
```

---

## 4. BẢNG ĐẶC TẢ TRÁCH NHIỆM VÀ HIỆN TRẠNG CÁC THÀNH PHẦN KIẾN TRÚC

Bảng đối chiếu toàn diện trách nhiệm kỹ thuật, kỹ sư phụ trách chính và lộ trình triển khai chi tiết cho từng thành phần trong hệ thống:

| Phân hệ / Thành phần | Tên kỹ thuật chuẩn | Kỹ sư phụ trách (Owner) | Trách nhiệm kỹ thuật & Nghiệp vụ chi tiết | Hợp đồng giao tiếp (Contract) | Hiện trạng mã nguồn & Kế hoạch Sprint |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **Phân hệ Thu nhận Syslog UDP** | `UDP Datagram Receiver` | **Phạm Hoàng Long (BE1)** | Mở Socket lắng nghe cổng UDP `5514`. Tiếp nhận các gói tin datagram thô từ router/switch. Nới rộng bộ đệm nhận `SO_RCVBUF = 4MB` để triệt tiêu tỷ lệ rớt gói khi bão lưu lượng. Đóng gói phong bì `RawEnvelope` kèm timestamp vi giây. | `asyncio.DatagramProtocol`<br>Port: `5514`<br>Struct: `RawEnvelope` | Đang hoàn thiện trong **Sprint 1** (`N42-13`, `N42-32`). Baseline W1 đã sẵn sàng khung. |
| **Cổng Tiếp nhận REST API** | `FastAPI REST Ingest Adapter` | **Phạm Hoàng Long (BE1)** | Cung cấp endpoint HTTP tiếp nhận cảnh báo từ ứng dụng bên thứ 3 và hệ thống giám sát khác. Thẩm định schema dữ liệu đầu vào bằng Pydantic. Xử lý trả mã lỗi chuẩn `201 Created`, `400 Bad Request`, `422 Unprocessable`. | `POST /api/v1/events/ingest`<br>Body: `JSON`<br>Header: `Content-Type: app/json` | Đang triển khai trong **Sprint 1** (`N42-14`). |
| **Bộ Tiếp nhận Tệp Nhật ký** | `Batch File Log Adapter` | **Phạm Hoàng Long (BE1)** | Đọc tệp tin nhật ký dung lượng lớn từ ổ đĩa theo cơ chế phát dòng (streaming line-by-line). Giữ nguyên số dòng để đối soát lỗi. Báo cáo tổng số dòng nạp thành công và danh sách dòng lỗi dị dạng mà không làm sập luồng nạp. | CLI Command:<br>`python -m app.importer`<br>Hỗ trợ format `.log`, `.txt` | Lên kế hoạch triển khai tại **Sprint 2** (`N42-22`). |
| **Động cơ Phân tích Cú pháp Đa Hãng** | `Multi-Vendor Parser Engine` | **Phạm Tấn Thành (BE2)** | Bóc tách tự động các mẫu bản tin khác biệt: Cisco IOS (`LINK-3-UPDOWN`), Cisco Nexus (`%IP-4-DUPADDR`), Huawei NE40E (`POWER_SUPPLY_FAILED`), Juniper (`BGP_PEER_DOWN`), Fortinet (`action=deny`). Ánh xạ mức độ nghiêm trọng về 5 thang chuẩn: `CRITICAL`, `MAJOR`, `WARNING`, `INFO`, `DEBUG`. Chống tấn công ReDoS. | Class: `BaseNormalizer`<br>Entity: `AlertEvent`<br>Mapping: `RFC 3164 / 5424` | Đang triển khai trong **Sprint 1 & Sprint 2** (`N42-15`, `N42-23..25`). |
| **Cơ chế Lưu trữ Thô Dự phòng** | `Quarantine & RAW Fallback` | **Phạm Tấn Thành (BE2)** | Đảm bảo tính toàn vẹn 100%: Khi gặp bản tin lạ, chuỗi nhị phân hỏng hoặc không có mã PRI chuẩn, hệ thống tự động đánh dấu cờ `format_status: RAW_FALLBACK`, gán `vendor: UNKNOWN` và bảo toàn trọn vẹn chuỗi gốc vào CSDL phục vụ hậu kiểm. | Trường: `raw_message`<br>Trạng thái: `UNKNOWN` | Triển khai trong **Sprint 2** (`N42-18`). |
| **Hàng đợi Có giới hạn Bộ nhớ** | `Bounded In-Memory Queue` | **Phạm Tấn Thành (BE2)** | Vùng đệm trung chuyển giữa tầng Thu thập và tầng Phân tích cú pháp/Tương quan. Giới hạn dung lượng tối đa 10.000 bản tin. Kích hoạt cơ chế áp lực ngược (Backpressure) và bộ đếm cảnh báo drop khi dung lượng vượt quá 85%. | Struct: `asyncio.Queue(maxsize=10000)`<br>Queue Depth Metrics | Triển khai trong **Sprint 2** (`N42-28`). |
| **Động cơ Tương quan Sự cố** | `Correlation & Rule Engine` | **Nguyễn Duy Minh (BE3)** | Áp dụng thuật toán cửa sổ trượt thời gian thực (Sliding Window deque) để phát hiện mối liên hệ giữa các cảnh báo riêng lẻ: Gom ít nhất 5 lần đổi trạng thái UP/DOWN trong 60 giây trên cùng cổng mạng thành 1 sự cố gốc (Link Flap). Giảm thiểu tối thiểu 70% số lượng cảnh báo hiển thị trên màn hình NOC. | Module: `correlation_engine`<br>Khóa gom: `(device, interface)`<br>Cửa sổ: `window_seconds` | Đang khởi động trong **Sprint 1 & Sprint 3** (`N42-17`, `N42-44`). |
| **Cỗ máy Trạng thái Khử dao động** | `Link Flap Finite State Machine` | **Nguyễn Duy Minh (BE3)** | Quản lý trạng thái giao diện mạng theo mô hình FSM chuẩn: `NORMAL -> MONITORING -> FLAPPING -> SUPPRESSED -> AUTO_RESOLVED`. Tự động cô lập cảnh báo phụ khi cổng dao động vượt ngưỡng 10 lần/phút để chống bão giao diện. | FSM State Table<br>Timeout: `300 seconds` | Triển khai trong **Sprint 3** (`N42-44`). |
| **Bộ Quản lý Cấu hình Luật** | `Rules Manager & Validator` | **Nguyễn Duy Minh (BE3)** | Nạp và thẩm định bộ luật từ tệp `rules.yaml` tuân thủ tiêu chuẩn YAML 1.2. Kiểm tra chặt chẽ schema Pydantic, bắt lỗi ký tự Tab, kiểm soát ngưỡng biên `threshold >= 1`, `window >= 1s`. Cung cấp tính năng nạp lại không gián đoạn dịch vụ (Atomic Hot-Reload) và tự động khôi phục bản cũ nếu lỗi. | Tệp: `rules.yaml`<br>API: `POST /api/v1/rules/reload`<br>Schema: `RuleSchema` | Đang chuẩn bị trong **Sprint 1 & Sprint 4** (`N42-17`, `N42-46`). |
| **Bộ Quản lý Lưu trữ Sự kiện** | `EventStore Abstraction Layer` | **Phạm Tấn Thành (BE2)** | Cung cấp giao diện trừu tượng che giấu tầng CSDL thực tế. Cho phép chuyển đổi mượt mà giữa bộ lưu đệm RAM ở giai đoạn đầu sang CSDL TimescaleDB ở giai đoạn sau mà không ảnh hưởng tới code nghiệp vụ của các thành viên khác. | Interface: `EventStore`<br>Methods: `add()`, `add_many()`, `get_by_id()`, `query()` | Đang triển khai trong **Sprint 1** (`N42-15`, `N42-16`). |
| **Kho Lưu trữ Chuỗi Thời gian** | `TimescaleDB Repository` | **Phạm Tấn Thành (BE2)** | Triển khai CSDL PostgreSQL 16 mở rộng TimescaleDB. Phân vùng bảng dữ liệu thành các đoạn siêu bảng (Hypertable chunks 1 ngày/chunk). Đánh chỉ mục tối ưu (B-Tree + Composite Index) trên `(received_at, device_name, severity)`. Đảm bảo truy vấn 1 triệu bản ghi dưới 2 giây. | CSDL: `PostgreSQL 16`<br>Extension: `timescaledb`<br>Bảng: `alert_events`, `incidents` | Đang dựng DDL trong **Sprint 1 & Sprint 2** (`N42-16`, `N42-31`). |
| **Cổng Lập trình Dịch vụ Backend** | `FastAPI Service Gateway` | **Phạm Hoàng Long (BE1)** | Cung cấp hệ thống REST API truy vấn dữ liệu sự kiện, quản lý sự cố, phân trang cursor ổn định, báo cáo sức khỏe hệ thống `/api/health`. Chống tấn công SQL Injection bằng truy vấn tham số hóa. | Swagger OpenAPI Docs<br>Endpoints: `/api/v1/events`, `/api/v1/incidents` | Đã có endpoint `/api/health`. Mở rộng các API tại **Sprint 2 & Sprint 3** (`N42-19`). |
| **Kênh Truyền phát Thời gian thực** | `WebSocket Real-time Broadcast Hub` | **Lê Khắc Huy (FE)** | Duy trì kết nối hai chiều liên tục giữa trình duyệt của Kỹ sư NOC và máy chủ Backend. Phát sóng tức thì các sự cố khẩn cấp mức `CRITICAL` và `MAJOR` ngay khi Động cơ tương quan phát hiện, không bắt người dùng phải tải lại trang. | Protocol: `WebSocket (ws://)`<br>Endpoint: `/ws/alerts`<br>Format: JSON Event Stream | Bắt đầu kết nối tại **Sprint 3** (`N42-34`). |
| **Giao diện Giám sát NOC Trung tâm** | `React NOC Dashboard UI` | **Lê Khắc Huy (FE)** | Xây dựng màn hình điều hành NOC chuẩn Dark Mode VNPT. Hiển thị 4 thẻ chỉ số KPI tổng quan, dòng sự kiện thời gian thực (Live Event Feed), bộ lọc đa tiêu chí, màn hình phân tích nguyên nhân gốc sự cố (Root Cause Explorer) và chức năng xuất báo cáo ca trực. | Framework: `React 18`<br>Build: `Vite`<br>Style: `Tailwind CSS`<br>Icons: `Lucide React` | Khởi tạo khung giao diện tại **Sprint 1 & Sprint 2** (`N42-19`, `N42-20`). |
| **Bộ Sinh Cảnh báo Giả lập & Đo tải** | `QA Benchmark & Load Generator` | **Ngô Châu Kiệt (QA Lead)** | Xây dựng công cụ CLI tự động phát dòng dữ liệu mô phỏng theo 8 kịch bản chuẩn KB-01..08. Điều khiển tốc độ phát chính xác từ 200, 500 đến 1.000 msg/s. Gắn timestamp vi giây để đo đạc và báo cáo phân vị trễ $P_{50}, P_{99}$ và tỷ lệ mất gói UDP $0.00\%$. | Script: `tools/load_runner.py`<br>Giao thức: `UDP / REST`<br>Tải đỉnh: `1.500 msg/s` | Đang viết kịch bản tại **Sprint 1 & Sprint 2** (`N42-11`, `N42-12`, `N42-47`). |
| **Hạ tầng Tự động hóa CI/CD & Quản trị** | `DevOps Pipeline & Governance` | **Phạm Minh Nhựt (PM/Lead)** | Thiết lập đường ống CI/CD GitHub Actions: tự động quét mã độc và rò rỉ secret bằng `check_sensitive.py`, chạy linter `flake8` và kiểm thử tự động `pytest`. Vận hành bảng Jira Scrum, đồng bộ 5 luồng Automation 2 chiều giữa Git và Jira. | GitHub Actions CI<br>Jira Cloud Automation<br>Branch Protection: `main` | Đã hoàn tất kết nối Jira-Git, cấu hình bảo vệ nhánh `main` và 5 luồng tự động. |

---

## 5. BIỂU ĐỒ TUẦN TỰ DÒNG DỮ LIỆU CẢNH BÁO (END-TO-END SEQUENCE DIAGRAM)

Biểu đồ mô tả chi tiết đường đi của một bản tin cảnh báo từ lúc phát sinh trên thiết bị mạng viễn thông cho đến khi hiển thị cảnh báo đỏ trên màn hình NOC Dashboard:

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Thiết bị Mạng Viễn thông / Tool QA
    participant Ingest as Phân hệ Thu nạp (UDP:5514 / REST)
    participant Parser as Động cơ Chuẩn hóa (Multi-Vendor Parser)
    participant Queue as Hàng đợi Bộ nhớ (Bounded Queue)
    participant Engine as Động cơ Tương quan (Sliding Window & FSM)
    participant DB as CSDL Chuỗi Thời gian (TimescaleDB)
    participant WS as Kênh WebSocket Hub
    actor NOC as Màn hình Giám sát NOC (React Dashboard)

    Note over Dev,Ingest: BƯỚC 1: TIẾP NHẬN DÒNG DỮ LIỆU
    Dev->>Ingest: Gửi bản tin datagram qua UDP 5514 (hoặc HTTP REST)
    Ingest->>Ingest: Đóng phong bì RawEnvelope, gắn timestamp thu nạp UTC

    Note over Ingest,Parser: BƯỚC 2: PHÂN TÍCH CÚ PHÁP & CHUẨN HÓA
    Ingest->>Parser: Chuyển chuỗi byte thô sang bộ phân tích cú pháp
    alt Bản tin khớp cú pháp chuẩn (Cisco/Huawei/Juniper/Fortinet)
        Parser->>Parser: Trích xuất device_name, interface, severity, event_type
        Parser-->>Queue: Đóng gói thực thể AlertEvent chuẩn hóa
    else Bản tin lạ hoặc bị lỗi định dạng
        Parser->>Parser: Gán cờ format_status = RAW_FALLBACK, vendor = UNKNOWN
        Parser-->>Queue: Đóng gói AlertEvent bảo toàn 100% raw_message
    end

    Note over Queue,Engine: BƯỚC 3: XỬ LÝ HÀNG ĐỢI & SO KHỚP TƯƠNG QUAN
    Queue->>Engine: Đẩy AlertEvent vào động cơ so khớp luật
    Engine->>Engine: Đưa sự kiện vào cửa sổ trượt theo Grouping Key (device, interface)
    Engine->>Engine: Kiểm tra điều kiện luật (Ví dụ: Link Flap >= 5 lần trong 60s)
    
    alt Đạt ngưỡng kích hoạt sự cố (Threshold Reached)
        Engine->>Engine: Tạo bản ghi Sự cố mới (Incident - Mức MAJOR/CRITICAL)
        Engine->>Engine: Gom tập hợp các Event ID làm bằng chứng (Evidence Links)
        Engine->>DB: Ghi đồng thời AlertEvent và Incident vào Hypertable
        Engine->>WS: Bắn thông báo sự cố mới qua kênh WebSocket
        WS-->>NOC: Sự cố mới xuất hiện nhấp nháy đỏ trên giao diện NOC tức thì!
    else Chưa đủ ngưỡng kích hoạt
        Engine->>DB: Ghi AlertEvent đơn lẻ vào bảng sự kiện lưu trữ
        Engine->>WS: Cập nhật biến động số đếm sự kiện thời gian thực
    end

    Note over DB,NOC: BƯỚC 4: TRA CỨU & KHAI THÁC LỊCH SỬ
    NOC->>DB: Kỹ sư NOC gửi truy vấn tìm kiếm lịch sử (Lọc theo thời gian, thiết bị, severity)
    DB-->>NOC: Trả về trang kết quả phân trang cursor ổn định (Độ trễ < 2 giây / 1M records)
```

---

## 6. MÔ HÌNH VÒNG ĐỜI XỬ LÝ SỰ CỐ VIỄN THÔNG (INCIDENT LIFECYCLE FSM)

Sự cố mạng sau khi được Động cơ tương quan phát hiện sẽ vận hành theo cỗ máy trạng thái chuẩn ITIL v4:

```mermaid
stateDiagram-v2
    [*] --> MOI_TAO: Động cơ phát hiện đạt ngưỡng luật tương quan
    
    MOI_TAO --> TIEP_NHAN: Kỹ sư trực ca NOC nhấn 'Tiếp nhận' (Acknowledge)
    MOI_TAO --> TU_DONG_DONG: Hết thời gian chờ (300s) không còn dao động
    
    TIEP_NHAN --> DANG_XU_LY: Phân công kỹ sư mạng tuyến 2 điều tra
    DANG_XU_LY --> DA_KHAC_PHUC: Kỹ sư cấu hình xong thiết bị, đóng sự cố
    
    DA_KHAC_PHUC --> TAI_PHAT: Cổng mạng tiếp tục bị flap lại trong 60s
    TAI_PHAT --> MOI_TAO: Tái mở sự cố khẩn cấp (Re-open Incident)
    
    DA_KHAC_PHUC --> DONG_HOAN_TAT: Sau 24 giờ hoạt động ổn định không phát sinh lỗi
    DONG_HOAN_TAT --> [*]: Lưu trữ vào kho dữ liệu lịch sử
```

---

## 7. MÔ HÌNH TRIỂN KHAI VẬN HÀNH TRÊN MÁY CHỦ LAB (DEPLOYMENT ARCHITECTURE)

Hệ thống được đóng gói hoàn chỉnh bằng Docker Compose triển khai trên máy chủ kiểm thử:

```mermaid
flowchart LR
    subgraph DOCKER_COMPOSE["MÁY CHỦ VẬN HÀNH LAB N4.2 (DOCKER COMPOSE)"]
        direction TB
        subgraph CONTAINER_APP["Container n42-app (FastAPI & Asyncio Pipeline)"]
            APP_SRV["Máy chủ Dịch vụ Ứng dụng<br/>(FastAPI Uvicorn)"]
            UDP_SOCK["Socket Receiver :5514"]
            CORR_SRV["Dịch vụ Tương quan & Luật"]
        end

        subgraph CONTAINER_DB["Container n42-postgres (PostgreSQL 16)"]
            TS_ENGINE["Động cơ TimescaleDB"]
            DATA_VOL[("Ổ đĩa Dữ liệu Bền vững<br/>(Named Volume /var/lib/postgresql)")]
            TS_ENGINE --- DATA_VOL
        end

        subgraph CONTAINER_UI["Container n42-frontend (Nginx / React SPA)"]
            STATIC_SRV["Máy chủ Web Nginx"]
            REACT_BUILD["Bản dựng React Tối ưu"]
            STATIC_SRV --- REACT_BUILD
        end

        APP_SRV <-->|Mạng nội bộ Docker bridge| TS_ENGINE
        STATIC_SRV <-->|Proxy API & WebSocket| APP_SRV
    end

    subgraph CLIENTS["MÔI TRƯỜNG TRUY CẬP"]
        GENERATOR["Máy phát Tải Benchmark QA<br/>(10.10.0.100)"]
        ADMIN_PC["Trình duyệt Kỹ sư Giám sát NOC<br/>(10.10.0.50)"]
    end

    GENERATOR -->|Dòng tin Syslog UDP 5514| UDP_SOCK
    ADMIN_PC <-->|Truy cập Cổng Web HTTP 80/443| STATIC_SRV
```

---

## 8. PHÊ DUYỆT BẢN THIẾT KẾ KIẾN TRÚC

| Vai trò | Họ và tên | Chữ ký điện tử | Trạng thái |
| :--- | :--- | :---: | :---: |
| **Project Manager & DevOps Lead** | **Phạm Minh Nhựt** | *(Đã ký duyệt)* | Phê duyệt chính thức |
| **QA Lead / Chủ nhiệm Kiểm thử** | **Ngô Châu Kiệt** | *(Đã ký duyệt)* | Xác nhận tiêu chuẩn đo tải |
| **Đại diện Nhóm Backend (BE1/BE2/BE3)** | **Phạm Hoàng Long / Phạm Tấn Thành / Nguyễn Duy Minh** | *(Đã đồng thuận)* | Cam kết triển khai theo Sprint |
| **Đại diện Nhóm Frontend (FE)** | **Lê Khắc Huy** | *(Đã đồng thuận)* | Cam kết hợp đồng API Dashboard |
| **Cố vấn Chuyên môn Doanh nghiệp** | Ban Cố vấn Kỹ thuật VNPT NOC | *(Chờ nghiệm thu W13)* | Đăng ký hồ sơ nghiệm thu |
