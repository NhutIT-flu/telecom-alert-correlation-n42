# ĐẶC TẢ CA KIỂM THỬ — N4.2
## Bản làm việc: kiểm thử hộp đen, giá trị biên và truy vết yêu cầu

> **Mã văn bản:** `N42-TCS-WORKING`  
> **Trạng thái:** Đặc tả/kế hoạch; chưa phải test run record hoặc tài liệu đã được VNPT/UTH phê duyệt. Đối chiếu hiện trạng trong `REQUIREMENTS_TRACEABILITY_MATRIX.md`.  
> **Phương pháp:** Phân vùng tương đương, giá trị biên, bảng quyết định và chuyển trạng thái khi phù hợp với yêu cầu đã chốt.  
> **Dự án:** N4.2 — Hệ thống thu thập và phân tích tương quan cảnh báo từ Router, Switch và Firewall  
> **Quản lý baseline tài liệu/điều phối:** **Phạm Minh Nhựt (Team Leader / PM)**; không thay QA thiết kế test hoặc BE/FE xác nhận contract.  
> **Chủ trì đặc tả kiểm thử, CI và đo kiểm:** **Ngô Châu Kiệt (QA Lead)**; BE/FE owners xác nhận contract và expected result thuộc phần mình.  
> **Phụ trách Kỹ thuật Phân hệ:**  
> - **Nguyễn Duy Minh (BE3 — Correlation Engine, Sliding Window & Rule Validation)**  
> - **Phạm Hoàng Long (BE1 — UDP Syslog Ingestion, High Throughput Buffer)**  
> - **Phạm Tấn Thành (BE2 — Multi-vendor Parser & Normalized Event Storage)**  
> - **Lê Khắc Huy (FE — Real-time NOC Dashboard & Alert Visualizer)**  

---

## Trạng thái, phạm vi và quy tắc sử dụng

- Đây là **bản đặc tả làm việc để review**, chưa được QA/BE/FE ký duyệt và chưa phải bằng chứng thực thi. Trạng thái từng ca trong mục 6 là nguồn theo dõi; trạng thái `BLOCKED` phải nêu dependency/contract còn thiếu.
- Phạm vi lấy từ `SYSTEM_REQUIREMENTS_AND_USE_CASES.md` và `ACCEPTANCE_CRITERIA.md`. Mã FR/NFR/AC/Jira là liên kết truy vết, không tự chứng minh tính năng đã triển khai hoặc ticket đã hoàn thành.
- Giá trị cụ thể chỉ là tiêu chí nghiệm thu khi có nguồn trong yêu cầu/AC/decision đã duyệt. Giá trị ví dụ, giới hạn kỹ thuật đề xuất và giả định phải ghi `PROPOSED / NEEDS OWNER CONFIRMATION`; không dùng làm Pass/Fail khi chưa xác nhận.
- **Vai trò:** QA Lead chủ trì thiết kế test, coverage, fixture, execution record và defect evidence; BE/FE owner xác nhận contract và expected result kỹ thuật của module; TL quản lý tài liệu, điều phối việc xác nhận và ghi nhận quyết định được owner/thẩm quyền phê duyệt. TL không tự chốt threshold, schema, semantics hay kết quả kỹ thuật.
- **Trước khi chạy:** từng ca cần có ID, requirement/AC, priority, điều kiện tiên quyết, môi trường, dữ liệu/seed, bước thực hiện, expected result có thể quan sát, cleanup/reset, trạng thái và evidence cần lưu. Thiếu contract thì `BLOCKED`; chưa chạy thì `NOT RUN`.
- **Trạng thái hợp lệ:** `DRAFT`, `NEEDS OWNER REVIEW`, `READY`, `BLOCKED`, `NOT RUN`, `PASS`, `FAIL`, `INCONCLUSIVE`. `PASS/FAIL` chỉ được ghi sau lần chạy có commit, môi trường, phiên bản fixture/config và evidence.

## MỤC LỤC CHI TIẾT

1. [Tổng quan Phương pháp luận Thiết kế Kiểm thử (Test Design Techniques)](#1-tong-quan-phuong-phap-luan-thiet-ke-kiem-thu)
2. [Ma trận Phân vùng Tương đương đầu vào (Equivalence Partitioning - EP)](#2-ma-tran-phan-vung-tuong-duong-dau-vao-ep)
3. [Phân tích Giá trị Biên Đa chiều (Boundary Value Analysis - BVA)](#3-phan-tich-gia-tri-bien-da-chieu-bva)
4. [Bảng Quyết định Ma trận Tương quan Sự cố (Decision Tables for Correlation)](#4-bang-quyet-dinh-ma-tran-tuong-quan-su-co)
5. [Kiểm thử Chuyển đổi Trạng thái (State Transition Testing - FSM)](#5-kiem-thu-chuyen-doi-trang-thai-fsm)
6. [Đặc tả Chi tiết Từng Ca Kiểm thử (Detailed Test Case Specifications)](#6-dac-ta-chi-tiet-tung-ca-kiem-thu)
   - [6.1 Thu nạp dữ liệu — BE1 (TC-ING)](#61-thu-nap-du-lieu--be1-tc-ing)
   - [6.2 Parser và chuẩn hóa — BE2 (TC-PAR)](#62-parser-va-chuan-hoa--be2-tc-par)
   - [6.3 Tương quan và gom nhóm — BE3 (TC-COR)](#63-tuong-quan-va-gom-nhom--be3-tc-cor)
   - [6.4 Cấu hình luật — BE3 (TC-RUL)](#64-cau-hinh-luat--be3-tc-rul)
   - [6.5 Query và Dashboard (TC-UI)](#65-query-va-dashboard-tc-ui)
   - [6.6 Đo kiểm tải danh định và sức chịu đựng (QA — TC-PERF)](#66-phan-he-do-kiem-tai-danh-dinh--suc-chiu-dung)
   - [6.7 Phân hệ An toàn Thông tin & Tuân thủ Dữ liệu Viễn thông (TC-SEC)](#67-phan-he-an-toan-thong-tin--tuan-thu-du-lieu-vien-thong)
   - [6.8 Health/diagnostics (TC-HLT)](#68-healthdiagnostics-tc-hlt)
   - [6.9 Phân hệ Kiểm thử Tích hợp End-to-End (Integration Test — TC-INT)](#69-phan-he-kiem-thu-tich-hop-end-to-end-integration-test--tc-int)
   - [6.10 Phân hệ Cơ sở Dữ liệu & Tính toàn vẹn (TC-DB)](#610-phan-he-co-so-du-lieu--tinh-toan-ven-tc-db)
   - [6.11 Phân hệ Bảo mật & Kiểm soát Truy cập Nâng cao (TC-SEC Mở rộng)](#611-phan-he-bao-mat--kiem-soat-truy-cap-nang-cao-tc-sec--mo-rong)
   - [6.12 Phân hệ Đo kiểm Hiệu năng Nâng cao (TC-PERF Mở rộng)](#612-phan-he-do-kiem-hieu-nang-nang-cao-tc-perf--mo-rong)
   - [6.13 Cổng bàn giao và vận hành dự án (TC-OPS)](#613-cong-ban-giao-va-van-hanh-du-an-tc-ops)
7. [Phác thảo harness (chưa phải automated tests)](#7-phac-thao-harness-kiem-thu-chua-phai-automated-tests)
8. [Mô hình Dữ liệu Đối soát Chuẩn (Test Fixtures & Raw Golden Data)](#8-mo-hinh-du-lieu-doi-soat-chuan-test-fixtures--data-dictionary)
9. [Quy trình Quản lý Lỗi & Tiêu chí Nghiệm thu (Defect Management & Sign-off)](#9-quy-trinh-quan-ly-loi--tieu-chi-nghiem-thu-sign-off)
10. [Ma trận Truy vết Yêu cầu đến Ca Kiểm thử (Traceability Matrix)](#10-ma-tran-truy-vet-yeu-cau-den-ca-kiem-thu-traceability-matrix)
11. [Bảng Ghi nhận Kết quả Kiểm thử Thực địa (Test Run Execution Sheet)](#11-bang-ghi-nhan-ket-qua-kiem-thu-thuc-dia-test-run-execution-sheet)
12. [Phê duyệt Bản Đặc tả Kiểm thử (Sign-off & Approval)](#12-phe-duyet-ban-dac-ta-kiem-thu-sign-off--approval)

---

## 1. TỔNG QUAN PHƯƠNG PHÁP LUẬN THIẾT KẾ KIỂM THỬ

Các kỹ thuật dưới đây được chọn theo loại yêu cầu; chúng không tự chứng minh khả năng tải production hoặc vận hành 24/7. Mỗi ca kiểm thử cần liên kết với FR/NFR hoặc AC.

| Bước thiết kế | Cách áp dụng |
|---|---|
| Xác định yêu cầu | Chọn FR/NFR hoặc AC và contract đã được chốt. |
| Chọn test input | Dùng phân vùng tương đương (EP) và giá trị biên (BVA) phù hợp với đầu vào. |
| Xác định tổ hợp | Dùng bảng quyết định cho các luật tương quan BE3. |
| Kiểm tra trạng thái | Dùng state transition cho Link Flap và vòng đời Incident. |
| Ghi expected result | Gắn input/fixture, kết quả mong đợi và evidence vào từng ca. |

### 1.1 Nguyên tắc Phân vùng tương đương (Equivalence Partitioning - EP)
Các đầu vào được phân rã thành miền tương đương khi yêu cầu và contract đã đủ rõ:
- **Lớp tương đương hợp lệ (Valid Equivalence Class - VEC):** Tập hợp các giá trị đầu vào hợp lệ mà hệ thống phải xử lý thành công theo đúng đặc tả yêu cầu chức năng.
- **Lớp tương đương không hợp lệ (Invalid Equivalence Class - IEC):** Tập hợp các giá trị bất thường, vi phạm khuôn mẫu, sai kiểu dữ liệu mà hệ thống phải bắt giữ, cách ly, log cảnh báo và không được phép dừng đột ngột (No Crash / Unhandled Exception).

### 1.2 Nguyên tắc Phân tích giá trị biên (Boundary Value Analysis - BVA)
Áp dụng mô hình **3 giá trị biên (3-point boundary analysis)** cho mọi biên số học, kích thước bộ đệm và ngưỡng thời gian:
- $B - 1$ (Giá trị cận dưới biên - Just below)
- $B$ (Giá trị chính xác tại biên - On boundary)
- $B + 1$ (Giá trị cận trên biên - Just above)

### 1.3 Nguyên tắc Bảng quyết định (Decision Table Testing)
Được áp dụng đặc biệt cho **Correlation (BE3)**. Bảng quyết định chọn các tổ hợp điều kiện quan trọng theo rule đã chốt; không khẳng định liệt kê mọi tổ hợp của toàn hệ thống.

### 1.4 Nguyên tắc Kiểm thử Chuyển trạng thái (State Transition Testing)
Áp dụng cho các thành phần có lưu trạng thái nội tại (Stateful components):
- Bộ máy FSM lọc dao động giao diện (Link Flap FSM)
- Vòng đời xử lý sự cố viễn thông (Incident Lifecycle FSM)

---

## 2. MA TRẬN PHÂN VÙNG TƯƠNG ĐƯƠNG ĐẦU VÀO (EP)

Dưới đây là ma trận phân rã đầu vào cho các tham số đã được xác định hoặc đang cần xác nhận. Các miền ghi mục tiêu/đề xuất là đầu vào thiết kế, không phải yêu cầu nghiệm thu cho đến khi owner xác nhận:

| Nhóm tham số | Tên biến / Tham số | Lớp tương đương hợp lệ (VEC) | Lớp tương đương không hợp lệ (IEC) | Mã xử lý ngoại lệ |
| :--- | :--- | :--- | :--- | :--- |
| **Ingestion UDP** | `payload_bytes` | **VEC-ING-01 (đề xuất):** $1 \le \text{len} \le 8192$ bytes; giới hạn phải do BE1 xác nhận trong receiver contract | **IEC-ING-01:** $\text{len} == 0$ (Rỗng)<br>**IEC-ING-02 (đề xuất):** payload vượt giới hạn; policy xử lý chưa được chốt | Mã counter/error chờ contract; không giả định sẵn DROP |
| **Ingestion UDP** | `udp_port` | **VEC-ING-02:** Cổng `5514` (Port chuẩn SOC) | **IEC-ING-03:** Cổng sai lệch hoặc cổng bị khóa quyền | `SOCKET_BIND_ERR` |
| **Syslog Header** | `PRI_value` | **VEC-HDR-01:** Số nguyên trong ngoặc `<0>` đến `<191>` | **IEC-HDR-01:** Thiếu dấu `<>` (Ví dụ: `134 Nov 06`)<br>**IEC-HDR-02:** $\text{PRI} < 0$<br>**IEC-HDR-03:** $\text{PRI} > 191$<br>**IEC-HDR-04:** Chứa chữ cái `<13a>` | `FALLBACK_RAW`<br>`INVALID_PRI`<br>`OUT_OF_BOUND_PRI`<br>`MALFORMED_HEADER` |
| **Syslog Header** | `timestamp_format` | **VEC-HDR-02:** RFC 3164 (`Mmm dd hh:mm:ss`)<br>**VEC-HDR-03:** RFC 5424 ISO-8601 (`YYYY-MM-DDThh:mm:ss.sTZD`) | **IEC-HDR-05:** Chuỗi thời gian không nhận dạng được<br>**IEC-HDR-06:** Thời gian trong tương lai (> Giờ hiện tại + 1 ngày) | `INFERRED_NOW_TIME`<br>`TIMESTAMP_SKEWED` |
| **Rules YAML** | `yaml_syntax` | **VEC-RUL-01:** Chuẩn YAML 1.2 (Indent bằng Space, UTF-8) | **IEC-RUL-01:** Chứa ký tự Tab (`\t`)<br>**IEC-RUL-02:** Đóng mở ngoặc nhọn JSON lỗi trong YAML<br>**IEC-RUL-03:** Tệp tin rỗng (0 byte) hoặc tệp nhị phân | `YAML_TAB_ERROR`<br>`YAML_SCANNER_ERR`<br>`EMPTY_RULE_FILE` |
| **Rule Schema** | `threshold` | **VEC-RUL-02:** Số nguyên dương $\text{threshold} \ge 1$ | **IEC-RUL-04:** $\text{threshold} == 0$<br>**IEC-RUL-05:** $\text{threshold} < 0$<br>**IEC-RUL-06:** Kiểu số thực `5.5`<br>**IEC-RUL-07:** Kiểu chuỗi `"năm"` | `PYDANTIC_INT_GT_0`<br>`PYDANTIC_TYPE_ERR` |
| **Rule Schema** | `window_seconds` | **VEC-RUL-03 (đề xuất):** Số nguyên $1 \le \text{window} \le 86400$; range cần BE3 xác nhận | **IEC-RUL-08:** $\text{window} \le 0$<br>**IEC-RUL-09 (đề xuất):** $\text{window} > 86400$ | Mã lỗi/schema chờ contract |
| **Correlation** | `group_by_keys` | **VEC-COR-01:** Mảng các trường: `device_name`, `interface_name`, `src_ip` | **IEC-COR-01:** Mảng rỗng `[]`<br>**IEC-COR-02:** Tên trường không tồn tại trong Event schema | `EMPTY_GROUP_KEY`<br>`UNKNOWN_SCHEMA_FIELD` |
| **Network IP** | `ip_address` | **VEC-SEC-01:** IP hợp lệ trong dải lab RFC 1918; dải TEST-NET chỉ dùng trong fixture/tài liệu | **IEC-SEC-01:** Chuỗi sai định dạng/octets (ví dụ `10.10.999.1`)<br>Địa chỉ production không được dùng trong test lab; đó là data policy, không phải lớp IP không hợp lệ về kỹ thuật | `INVALID_IP_FORMAT` |
| **Event Severity**| `normalized_sev` | **VEC-PAR-01:** `CRITICAL`, `MAJOR`, `WARNING`, `INFO`, `DEBUG`, `UNKNOWN` | **IEC-PAR-01:** Kiểu/giá trị không thể map theo schema đã duyệt | `MAP_TO_UNKNOWN` theo contract; schema validation nếu sai kiểu |

---

## 3. PHÂN TÍCH GIÁ TRỊ BIÊN ĐA CHIỀU (BVA)

Bảng phân tích 3 giá trị biên ($B-1, B, B+1$) được xây dựng cho các biến điều khiển cốt lõi:

| Mã BVA | Biến số kiểm định | Điểm biên quy chuẩn ($B$) | Giá trị cận dưới ($B-1$) | Giá trị tại biên ($B$) | Giá trị cận trên ($B+1$) | Hành vi hệ thống mong đợi |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **BVA-01** | `payload_size` (Syslog) | $B = 0$ byte | N/A | **0 byte** (Rỗng) | **1 byte** (Hợp lệ min) | 0 byte: Drop gói, tăng counter drop.<br>1 byte: Nhận, đưa vào parse raw. |
| **BVA-02** | `payload_size` (giới hạn đề xuất) | $B = 8192$ bytes (chưa được duyệt) | **8191 bytes** | **8192 bytes** | **8193 bytes** | `BLOCKED`: BE1 xác nhận giới hạn và hành vi duy nhất cho payload lớn; không giả định truncate/drop hoặc logging là acceptance. |
| **BVA-03** | `PRI` cận dưới RFC 3164 | $B = 0$ (`<0>`) | **-1** | **0** (`<0>`) | **1** (`<1>`) | PRI 0: Facility code 0, RFC severity code 0. Normalized label chỉ assert theo mapping fixture được BE2 duyệt; -1/invalid syntax cần parser contract xác nhận. |
| **BVA-04** | `PRI` cận trên RFC 3164 | $B = 191$ (`<191>`) | **190** (`<190>`) | **191** (`<191>`) | **192** (`<192>`) | PRI 191: Facility code 23, RFC severity code 7. Normalized label chỉ assert theo mapping fixture được BE2 duyệt; PRI 192 ngoài miền RFC cần parser contract xác nhận. |
| **BVA-05** | Ngưỡng đếm Flap (`threshold`) | $B = 5$ lần | **4 lần** | **5 lần** | **6 lần** | 4 lần: Không tạo Incident.<br>5 lần: **Kích hoạt tạo Incident** tức thì.<br>6 lần: Gom vào Incident đã mở (Deduplicate). |
| **BVA-06** | Cửa sổ trượt Flap (`window`) | $B = 60$ giây | **59 giây** | **60 giây** | **61 giây** | 5 sự kiện trong 59s: **Tạo Incident**.<br>5 sự kiện đúng 60s: **Tạo Incident**.<br>Sự kiện thứ 5 tại giây 61: **Hết hạn cửa sổ**, không tạo Incident. |
| **BVA-07** | Ngưỡng kích hoạt đơn (`threshold`) | $B = 1$ | **0** | **1** | **2** | 0: Pydantic ném `ValidationError`.<br>1: Báo động ngay khi có 1 sự kiện (Single-hit alert). |
| **BVA-08** | Cửa sổ trượt tối thiểu (đề xuất) | $B = 1$ giây (range cần BE3 xác nhận) | **0 giây** | **1 giây** | **2 giây** | `BLOCKED` cho tới khi rule contract xác nhận range và lỗi validation; không dùng như acceptance hiện hành. |
| **BVA-09** | Độ trễ xử lý $P_{99}$ | $B = 200$ ms | **199 ms** | **200 ms** | **201 ms** | $< 200$ ms: Đạt NFR-02.<br>$\ge 200$ ms: Không đạt ngưỡng P99 của NFR-02. |
| **BVA-10** | Tỷ lệ rớt gói UDP Socket | $B = 0.00\%$ | N/A | **0.00%** | **0.01%** | $0.00\%$: Nghiệm thu Đạt.<br>$> 0.00\%$: Nghiệm thu Không đạt. |

---

## 4. BẢNG QUYẾT ĐỊNH MA TRẬN TƯƠNG QUAN SỰ CỐ (DECISION TABLES)

### 4.1 Bảng quyết định cho Luật Link Flap (BE3)
Quy tắc: Một sự cố dao động đường truyền chỉ được công nhận khi và chỉ khi xảy ra tối thiểu 5 lần đổi trạng thái UP/DOWN trên **cùng một thiết bị** và **cùng một cổng giao diện mạng** trong khoảng thời gian **không quá 60 giây**.

| Điều kiện kiểm tra (Conditions) | R01 | R02 | R03 | R04 | R05 | R06 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **C1:** Mã sự kiện là `LINK_UPDOWN` | Y | Y | Y | Y | Y | N |
| **C2:** Trùng thiết bị nguồn (`device_name`) | Y | Y | Y | N | Y | Y |
| **C3:** Trùng cổng mạng (`interface_name`) | Y | Y | Y | N | N | Y |
| **C4:** Số sự kiện tích lũy $N$ | $\ge 5$ | 4 | $\ge 5$ | $\ge 5$ | $\ge 5$ | $\ge 5$ |
| **C5:** Khoảng thời gian từ event đầu $\Delta t$ | $\le 60s$ | $\le 60s$ | $> 60s$ (61s) | $\le 60s$ | $\le 60s$ | $\le 60s$ |
| **Hành động hệ thống (System Actions)** | | | | | | |
| **A1:** Tạo Incident mới (Mức `MAJOR`) | **X** | | | | | |
| **A2:** Gom toàn bộ Event ID làm Evidence Link | **X** | | | | | |
| **A3:** Bắn WebSocket cảnh báo Dashboard | **X** | | | | | |
| **A4:** Không tạo Incident (Giữ Event độc lập) | | **X** | **X** | **X** | **X** | **X** |
| **A5:** Reset bộ đếm trượt của Grouping Key | | | **X** | | | |

---

## 5. KIỂM THỬ CHUYỂN ĐỔI TRẠNG THÁI (STATE TRANSITION TESTING - FSM)

Mô hình dưới đây là phác thảo. Quy tắc ≥5 event/60 giây có trong SRS/AC; ngưỡng suppression >10/phút và auto-resolve 300 giây chưa có quyết định nghiệp vụ được duyệt, nên không dùng làm acceptance test cho đến khi ghi vào `DECISIONS.md`/SRS.

### 5.1 FSM Khử bão dao động cổng mạng (Link Flap Suppression FSM)

```
             +--------------------+
             |     S0: NORMAL     |<-----------------------------+
             +--------------------+                              |
                        | Event count == 1                       |
                        v                                        |
             +--------------------+                              |
             |   S1: MONITORING   |                              |
             +--------------------+                              |
               | (Count < 5 &         | (Window > 60s)           |
               |  Window <= 60s)      v Timeout                  |
               |            +--------------------+               |
               +----------->|   S0: NORMAL       |               |
               |            +--------------------+               |
               | Event count >= 5                                |
               v                                                 |
             +--------------------+                              |
             |   S2: FLAPPING     |                              |
             |  (Incident Open)   |                              |
             +--------------------+                              |
                        | Flap count > 10 / min                  |
                        v                                        |
             +--------------------+                              |
             |   S3: SUPPRESSED   |                              |
             | (Tắt cảnh báo phụ) |                              |
             +--------------------+                              |
                        | Không có flap trong 300s               |
                        +----------------------------------------+
```

| Trạng thái hiện tại | Sự kiện đầu vào | Điều kiện bảo vệ (Guard) | Trạng thái tiếp theo | Hành động thực hiện (Action) |
| :--- | :--- | :--- | :--- | :--- |
| **S0: NORMAL** | Nhận `LINK_UPDOWN` | Cổng đang ổn định | **S1: MONITORING** | Khởi tạo sliding window cho `(device, iface)`, đặt counter = 1 |
| **S1: MONITORING** | Nhận `LINK_UPDOWN` | Counter < 5 và $\Delta t \le 60s$ | **S1: MONITORING** | Tăng counter thêm 1, cập nhật timestamp mới nhất |
| **S1: MONITORING** | Hết thời gian | Không đủ 5 event sau 60s | **S0: NORMAL** | Xóa deque sliding window, giải phóng RAM |
| **S1: MONITORING** | Nhận `LINK_UPDOWN` | Counter đạt đúng 5 và $\Delta t \le 60s$| **S2: FLAPPING** | **Khởi tạo Incident mức MAJOR**, gắn 5 event ID, gửi WebSocket |
| **S2: FLAPPING** | Nhận thêm `LINK_UPDOWN` | Counter $\le 10$ trong cùng incident | **S2: FLAPPING** | Cập nhật `event_count` trong Incident, không bắn spam thông báo |
| **S2: FLAPPING** | Tần suất vượt đỉnh | Counter > 10 event / phút | **S3: SUPPRESSED** | Bật cờ `suppressed=True`, gửi 1 thông báo "Giao diện bị cô lập cảnh báo" |
| **S2 / S3** | Timeout yên lặng | Không còn flap trong 300 giây | **S0: NORMAL** | Tự động chuyển Incident sang `AUTO_RESOLVED`, ghi audit log |

---

## 6. ĐẶC TẢ CHI TIẾT TỪNG CA KIỂM THỬ

**Quy ước trạng thái:** Mỗi ca không ghi trạng thái riêng mặc định là `DRAFT / NEEDS OWNER REVIEW / NOT RUN`, không phải READY. Các ca phụ thuộc receiver/parser/database/rules/API/FE chưa có trong baseline phải để `BLOCKED` cho đến khi implementation và contract tương ứng được xác nhận. Chỉ `TC-HLT-001` phản ánh endpoint health đang có; tình trạng tự động hóa nằm trong `REQUIREMENTS_TRACEABILITY_MATRIX.md`.

**Contract còn mở:** severity trong SRS là nhãn chuẩn hóa; `n42-ai-kit/docs/INTERFACES.md` đề xuất số RFC 0–7 (D-01 chưa chốt). Timestamp field cũng khác tên (`event_time` trong SRS, `event_timestamp` trong interface). Assertions chạm các field này phải chờ schema/decision được duyệt; test raw bytes, facility/PRI RFC và extraction độc lập vẫn có thể thiết kế riêng.

### 6.1 Thu nạp dữ liệu — BE1 (TC-ING)

#### TC-ING-001: Tiếp nhận Syslog UDP RFC 3164 chuẩn xác
- **Mã Jira:** `N42-13` | **Owner:** BE1 (UDP Receiver) | **Ưu tiên:** P1 (CRITICAL)
- **Kỹ thuật:** Phân vùng tương đương (VEC-ING-01, VEC-HDR-01)
- **Tiền điều kiện:** Daemon `receiver` đang chạy trên cổng UDP `5514`.
- **Dữ liệu đầu vào (Raw Datagram):**
  ```text
  <134>Nov 06 15:00:00 sw-core-01 %LINK-3-UPDOWN: Interface GigabitEthernet0/1, changed state to down
  ```
- **Các bước thực hiện:**
  1. Dùng socket UDP gửi chuỗi raw payload trên đến `127.0.0.1:5514`.
  2. Truy vấn API: `GET /api/v1/events?limit=1`.
- **Kết quả mong đợi:**
  - HTTP Status: `200 OK`.
  - `raw_message` trùng khớp nguyên vẹn 100%.
  - Có tối đa một event/raw record cho datagram; source là UDP và payload giữ nguyên byte/UTF-8 theo contract.
  - Không dùng ca ingest để khẳng định parser severity/device mapping; các assertion parse nằm ở TC-PAR.

#### TC-ING-002: Kiểm tra biên dưới - Datagram 0 byte (BVA-01)
- **Mã Jira:** `N42-13` | **Ưu tiên:** P2 (HIGH)
- **Trạng thái:** `NEEDS OWNER REVIEW` — expected behavior với datagram rỗng/counter phải được BE1 xác nhận trong receiver contract.
- **Kỹ thuật:** Phân tích giá trị biên ($B = 0$ byte)
- **Dữ liệu đầu vào:** Chuỗi byte rỗng `b""` (0 byte).
- **Các bước thực hiện:** Gửi datagram rỗng đến UDP 5514.
- **Kết quả mong đợi:**
  - Tiến trình Receiver không crash, không sinh lỗi ngoại lệ chưa bắt.
  - Không insert bản ghi nào vào DB.
  - Bộ đếm `udp_dropped_empty` tăng đúng 1.

#### TC-ING-003: Kiểm tra biên 1 byte - Ký tự cực tiểu (BVA-01 Just Above)
- **Mã Jira:** `N42-13` | **Ưu tiên:** P3 (MEDIUM)
- **Trạng thái:** `NEEDS OWNER REVIEW` — việc lưu raw/fallback cần BE1/BE2 xác nhận theo contract.
- **Kỹ thuật:** Phân tích giá trị biên ($B+1 = 1$ byte)
- **Dữ liệu đầu vào:** `b"X"` (1 byte).
- **Kết quả mong đợi:**
  - Hệ thống nhận bản tin, đánh dấu format `RAW_UNKNOWN`.
  - Giữ nguyên raw byte `X`; parse status fallback/unknown theo enum đã chốt. Chưa khẳng định giá trị `severity` cho tới khi D-01/schema được duyệt.

#### TC-ING-004: Kiểm tra biên tối đa bộ đệm 8192 bytes (BVA-02)
- **Mã Jira:** `N42-32` | **Ưu tiên:** P2 (HIGH)
- **Trạng thái:** `BLOCKED` — 8.192 byte là giới hạn đề xuất, chưa thấy trong AC/contract được duyệt.
- **Kỹ thuật:** Phân tích giá trị biên ($B = 8192$ bytes)
- **Dữ liệu đầu vào:** Bản tin Syslog hợp lệ nối đuôi padding ký tự `'A'` đạt tổng chiều dài đúng 8.192 bytes.
- **Kết quả mong đợi:**
  - Lưu trọn vẹn 8.192 ký tự vào trường `raw_message`.
  - Không xảy ra lỗi cắt xén bộ đệm (No truncation).

#### TC-ING-005: Kiểm tra vượt quá kích thước bộ đệm 8193 bytes (BVA-02 Just Above)
- **Mã Jira:** `N42-32` | **Ưu tiên:** P3 (MEDIUM)
- **Trạng thái:** `BLOCKED` — giới hạn 8192 byte là đề xuất; policy drop/reject/truncate và metadata cần được chốt trước khi coi là acceptance.
- **Dữ liệu đầu vào:** Chuỗi 8.193 bytes.
- **Kết quả mong đợi:**
  - Sau khi BE1 chốt contract, xác nhận hành vi duy nhất (drop/reject/truncate), counter/status và cách lưu kích thước gốc. Trước thời điểm đó chỉ ghi nhận yêu cầu an toàn tối thiểu là receiver không crash; không dùng làm acceptance.

#### TC-ING-006: Tiếp nhận Syslog định dạng RFC 5424 (Structured Syslog)
- **Mã Jira:** `N42-13` | **Ưu tiên:** P2 (HIGH)
- **Dữ liệu đầu vào:**
  ```text
  <165>1 2026-11-06T15:05:00.123Z router-edge-01 rsyslogd 1234 ID47 [exampleSDID@32473 iut="3" eventSource="Application"] BOMAn application event
  ```
- **Kết quả mong đợi:**
  - Nhận diện đúng chuẩn RFC 5424 version `1`.
  - Bóc tách đúng timestamp ISO: `2026-11-06T15:05:00.123Z`.
  - `device_name`: `"router-edge-01"`, `app_name`: `"rsyslogd"`.

#### TC-ING-007: REST Ingest API hợp lệ (FR-02)
- **Mã Jira:** `N42-14` | **Ưu tiên:** P1 (CRITICAL)
- **Phạm vi:** Kiểm nhánh RAM với queue còn chỗ. Ca queue đầy kiểm HTTP `503` và nội dung queue giữ nguyên. ACK sau commit được kiểm riêng khi N42-62 chốt hợp đồng và có persistence.
- **Dữ liệu đầu vào:** `POST /api/v1/events/ingest`
  ```json
  {"raw_message": "<134>Nov 06 15:10:00 fw-01 %SYS-5-CONFIG: Configured from console", "source": "REST_CLIENT"}
  ```
- **Kết quả mong đợi:**
  - HTTP Status: `201 Created`.
  - Body: `{"status": "SUCCESS", "event_id": "<UUID>", "received_at": "<TIMESTAMP>"}`.

#### TC-ING-016: REST ingest từ chối bản tin khi queue đầy

- **Mã Jira:** [N42-14](https://nhutp2945-1793259952237.atlassian.net/browse/N42-14) · **Yêu cầu:** FR-02, NFR-08 · **Tiêu chí:** AC-01.
- **Thiết lập:** Dùng queue cô lập, dung lượng nhỏ, nạp trước các RawEvent giả lập có nội dung và thứ tự xác định.
- **Thực hiện:** Gửi một `raw_message` hợp lệ tới `POST /api/v1/events/ingest` khi queue đã đầy.
- **Kết quả mong đợi:** HTTP `503` với `{"detail":"Ingest queue is full"}`. Phản hồi không chứa `SUCCESS` hoặc `event_id`. Các RawEvent đã có giữ nguyên số lượng, thứ tự và nội dung.
- **Bằng chứng:** Gắn commit, kết quả `tests/test_api_ingest.py` và đối chiếu queue trước/sau. Trạng thái ca kiểm thử cập nhật theo kết quả chạy trên commit đã sửa.

#### TC-ING-008: REST Ingest API - Thiếu trường bắt buộc (Negative)
- **Mã Jira:** `N42-14` | **Ưu tiên:** P2 (HIGH)
- **Dữ liệu đầu vào:** `POST /api/v1/events/ingest` với body `{"source": "REST_CLIENT"}`.
- **Kết quả mong đợi:**
  - HTTP Status: `422 Unprocessable Entity`.
  - Báo lỗi rõ ràng trường `raw_message` bị thiếu.

#### TC-ING-009: REST Ingest API - Payload rỗng JSON `{}`
- **Mã Jira:** `N42-14` | **Ưu tiên:** P2 (HIGH)
- **Dữ liệu đầu vào:** `POST /api/v1/events/ingest` với body `{}`.
- **Kết quả mong đợi:**
  - HTTP Status: `422 Unprocessable Entity`.

#### TC-ING-010: REST Ingest API - Sai Content-Type
- **Mã Jira:** `N42-14` | **Ưu tiên:** P3 (MEDIUM)
- **Trạng thái:** `BLOCKED` — không dùng expected result có nhiều lựa chọn; status/error body phải theo REST contract được BE1 xác nhận.
- **Dữ liệu đầu vào:** Gửi request với `Content-Type: text/plain`.
- **Kết quả mong đợi:**
  - BE1 xác nhận một status code và error schema duy nhất trong REST contract. Khi chưa có contract, không thực thi acceptance cho case này.

#### TC-ING-011: File Log Batch Import - 100 dòng hợp lệ (FR-03)
- **Mã Jira:** `N42-22` | **Ưu tiên:** P2 (HIGH)
- **Phạm vi:** Đối soát kết quả cuối của import run theo pipeline được duyệt. Với API bất đồng bộ, lấy các bộ đếm sau khi run hoàn tất.
- **Dữ liệu đầu vào:** File `batch_100.log` chứa đúng 100 dòng Syslog chuẩn.
- **Kết quả mong đợi:**
  - Tạo thành công 100 bản ghi trong CSDL.
  - Phản hồi: `{"total": 100, "success": 100, "failed": 0}`.

#### TC-ING-012: File Log Batch Import - Trộn lẫn dòng lỗi định dạng
- **Mã Jira:** `N42-22` | **Ưu tiên:** P2 (HIGH)
- **Dữ liệu đầu vào:** File 10 dòng: 8 dòng hợp lệ, 2 dòng nhị phân hỏng ở dòng 3 và 7.
- **Kết quả mong đợi:**
  - 8 dòng hợp lệ được nạp thành công.
  - 2 dòng lỗi được ghi log riêng, báo cáo: `{"total": 10, "success": 8, "failed": 2, "error_lines": [3, 7]}`. Tiến trình không bị gián đoạn.

#### TC-ING-013: File Log Batch Import - File kích thước 0 byte
- **Mã Jira:** `N42-22` | **Ưu tiên:** P3 (MEDIUM)
- **Trạng thái:** `BLOCKED` — response cho file rỗng (400 hay successful empty import) chưa được thống nhất trong file-import contract.
- **Dữ liệu đầu vào:** Tệp tin `empty.log` rỗng 0 byte.
- **Kết quả mong đợi:**
  - File-import owner xác nhận một hành vi và response schema duy nhất. Khi contract chưa chốt, không thực thi acceptance cho case này.

#### TC-ING-014: Kiểm tra Socket UDP Buffer khi gửi dồn dập 500 gói
- **Mã Jira:** `N42-32` | **Ưu tiên:** P1 (CRITICAL)
- **Loại đo:** Stress characterization; kết quả phụ thuộc OS/socket cap, generator và receiver host.
- **Dữ liệu đầu vào:** Bắn 500 gói tin UDP trong 100ms.
- **Kết quả mong đợi:**
  - Ghi số sent/received/persisted, socket effective buffer và OS counters. Không suy ra zero loss từ sender send success; tiêu chí final theo NFR-03 chỉ đánh giá ở bài 1.000 msg/s/1h.

#### TC-ING-015: Tiếp nhận ký tự Unicode Tiếng Việt trong Syslog message
- **Mã Jira:** `N42-13` | **Ưu tiên:** P3 (MEDIUM)
- **Dữ liệu đầu vào:** `<134>Nov 06 15:15:00 thiet-bi-hcm %USER-5-LOGIN: Nguoi dung QuanTri dang nhap thanh cong`
- **Kết quả mong đợi:**
  - Lưu trữ đúng UTF-8 trong PostgreSQL, không bị lỗi font hoặc lỗi byte escape.

---

### 6.2 Parser và chuẩn hóa — BE2 (TC-PAR)

Giá trị field mapping (đặc biệt normalized severity label/number và tên event timestamp) phụ thuộc contract còn mở nêu tại đầu mục 6; ghi assertion theo schema được duyệt trước khi chạy.

#### TC-PAR-001: Bóc tách mẫu Cisco Catalyst LINK-3-UPDOWN
- **Mã Jira:** `N42-23` | **Owner:** BE2 (Parser) | **Ưu tiên:** P1 (CRITICAL)
- **Dữ liệu đầu vào:**
  ```text
  <133>Nov 06 15:20:00 sw-core-uth %LINK-3-UPDOWN: Interface GigabitEthernet0/1, changed state to down
  ```
- **Kết quả mong đợi:**
  - `vendor`: `"Cisco"`, `device_name`: `"sw-core-uth"`, `severity`: `"WARNING"`.
  - `event_type`: `"LINK_UPDOWN"`, `interface_name`: `"GigabitEthernet0/1"`, `link_state`: `"down"`.

#### TC-PAR-002: Bóc tách mẫu Cisco LINEPROTO-5-UPDOWN
- **Mã Jira:** `N42-23` | **Ưu tiên:** P1 (CRITICAL)
- **Dữ liệu đầu vào:**
  ```text
  <133>Nov 06 15:20:01 sw-core-uth %LINEPROTO-5-UPDOWN: Line protocol on Interface GigabitEthernet0/1, changed state to up
  ```
- **Kết quả mong đợi:**
  - `event_type`: `"LINEPROTO_UPDOWN"`, `interface_name`: `"GigabitEthernet0/1"`, `link_state`: `"up"`.

#### TC-PAR-003: Bóc tách mẫu Cisco Nexus %IP-4-DUPADDR (Xung đột IP)
- **Mã Jira:** `N42-23` | **Ưu tiên:** P2 (HIGH)
- **Dữ liệu đầu vào:**
  ```text
  <132>Nov 06 15:21:00 nexus-dc-01 %IP-4-DUPADDR: Duplicate address 10.10.5.100 on Vlan100, sourced by aabb.ccdd.1234
  ```
- **Kết quả mong đợi:**
  - `vendor`: `"Cisco"`, `severity`: `"MAJOR"`, `event_type`: `"IP_DUPLICATE"`.
  - `duplicate_ip`: `"10.10.5.100"`, `interface_name`: `"Vlan100"`, `mac_address`: `"aabb.ccdd.1234"`.

#### TC-PAR-004: Bóc tách mẫu Huawei NE40E POWER_SUPPLY_FAILED
- **Mã Jira:** `N42-24` | **Ưu tiên:** P1 (CRITICAL)
- **Dữ liệu đầu vào:**
  ```text
  <131>Nov 06 15:22:00 ne40e-bras-01 %%01DEVM/2/POWER_SUPPLY_FAILED: Power supply module 2 failed
  ```
- **Kết quả mong đợi:**
  - `vendor`: `"Huawei"`, `severity`: `"CRITICAL"`, `event_type`: `"POWER_SUPPLY_FAILED"`.
  - `component`: `"Power supply module 2"`.

#### TC-PAR-005: Bóc tách mẫu Huawei S5700 CPU_TEMP_ALARM
- **Mã Jira:** `N42-24` | **Ưu tiên:** P2 (HIGH)
- **Dữ liệu đầu vào:**
  ```text
  <131>Nov 06 15:23:00 s5700-01 %%01DEVM/2/CPU_TEMP_ALARM: CPU temperature reached 85 C, threshold 80 C
  ```
- **Kết quả mong đợi:**
  - `vendor`: `"Huawei"`, `severity`: `"MAJOR"`, `temperature`: 85, `threshold`: 80.

#### TC-PAR-006: Bóc tách mẫu Fortinet FortiGate Firewall Traffic Deny
- **Mã Jira:** `N42-25` | **Ưu tiên:** P1 (CRITICAL)
- **Dữ liệu đầu vào:**
  ```text
  date=2026-11-06 time=15:24:00 devname="fg-edge-01" type="traffic" subtype="forward" action="deny" srcip=10.10.1.50 dstip=203.0.113.10 dstport=443 proto=6
  ```
- **Kết quả mong đợi:**
  - `vendor`: `"Fortinet"`, `severity`: `"WARNING"`, `action`: `"deny"`.
  - `src_ip`: `"10.10.1.50"`, `dst_ip`: `"203.0.113.10"`, `dst_port`: 443, `protocol`: `"TCP"`.

#### TC-PAR-007: Bóc tách mẫu Juniper MX960 BGP_PEER_DOWN
- **Mã Jira:** Pending scope decision in `N42-62`; no Juniper parser implementation ticket is approved | **Ưu tiên:** P1 (CRITICAL)
- **Dữ liệu đầu vào:**
  ```text
  <133>Nov 06 15:25:00 mx960-pe-01 rpd[1234]: BGP_PEER_DOWN: peer 10.10.0.2 (AS 65002) state changed from Established to Idle
  ```
- **Kết quả mong đợi:**
  - `vendor`: `"Juniper"`, `severity`: `"MAJOR"`, `peer_ip`: `"10.10.0.2"`, `peer_as`: 65002, `old_state`: `"Established"`, `new_state`: `"Idle"`.

#### TC-PAR-008: Bóc tách PRI = 0 (Biên dưới Emergency - BVA-03)
- **Mã Jira:** `N42-15` | **Ưu tiên:** P2 (HIGH)
- **Trạng thái:** `NEEDS OWNER REVIEW` — xác nhận tên field facility/severity RFC trong parser contract; không suy normalized label từ số PRI.
- **Dữ liệu đầu vào:** `<0>Nov 06 15:26:00 core-router kernel: KERNEL PANIC OCCURRED`
- **Kết quả mong đợi:**
  - PRI=0 được bóc tách theo RFC thành facility code 0 và severity code 0. Tên facility và normalized label chờ contract/fixture được BE2 xác nhận.

#### TC-PAR-009: Bóc tách PRI = 191 (Biên trên Debug - BVA-04)
- **Mã Jira:** `N42-15` | **Ưu tiên:** P3 (MEDIUM)
- **Trạng thái:** `NEEDS OWNER REVIEW` — xác nhận tên field facility/severity RFC trong parser contract; không suy normalized label từ số PRI.
- **Dữ liệu đầu vào:** `<191>Nov 06 15:27:00 core-router test: detailed trace logging message`
- **Kết quả mong đợi:**
  - PRI=191 được bóc tách theo RFC thành facility code 23 và severity code 7. Tên facility và normalized label chờ contract/fixture được BE2 xác nhận.

#### TC-PAR-010: Xử lý chuỗi nhị phân hỏng (Negative Malformed)
- **Mã Jira:** `N42-15` | **Ưu tiên:** P2 (HIGH)
- **Dữ liệu đầu vào:** `\x00\x01\xfe\xff GARBAGE BYTES DATA NO SYSLOG`
- **Kết quả mong đợi:**
  - Không văng Exception. Lưu trữ với `format_status: "RAW_FALLBACK"`, `vendor: "UNKNOWN"`.

#### TC-PAR-011: Thiếu mã PRI header hoàn toàn
- **Mã Jira:** `N42-15` | **Ưu tiên:** P2 (HIGH)
- **Dữ liệu đầu vào:** `Nov 06 15:28:00 host-no-pri simple log line`
- **Kết quả mong đợi:**
  - `format_status: "MISSING_PRI"`, `raw_message` được lưu nguyên vẹn.

#### TC-PAR-012: Chuẩn hóa Timezone Offset +07:00 về UTC
- **Mã Jira:** `N42-15` | **Ưu tiên:** P2 (HIGH)
- **Dữ liệu đầu vào:** `<134>2026-11-06T15:30:00+07:00 sw-01 %SYS-5-CONFIG: Configured`
- **Kết quả mong đợi:**
  - `event_time` lưu trữ trong CSDL đúng chuẩn UTC: `2026-11-06T08:30:00Z`.

---

### 6.3 Tương quan và gom nhóm — BE3 (TC-COR — Nguyễn Duy Minh)

#### TC-COR-001: Kích hoạt Link Flap Incident đúng điểm biên 5 lần trong 60 giây (BVA-05, BVA-06)
- **Mã Jira:** `N42-44` | **Owner:** BE3 (Correlation) | **Ưu tiên:** P1 (CRITICAL)
- **Kỹ thuật:** Phân tích giá trị biên kết hợp Bảng quyết định R01
- **Tiền điều kiện:** Luật `RULE-NET-01-LINK-FLAP` (`window: 60s`, `threshold: 5`, `group_by: [device, interface]`) đang kích hoạt.
- **Dữ liệu kiểm thử (Bơm chuỗi 5 sự kiện):**
  - $t = 0s$: `<134>Nov 06 15:40:00 sw-01 %LINK-3-UPDOWN: Interface Gi0/1, changed state to down`
  - $t = 12s$: `<134>Nov 06 15:40:12 sw-01 %LINK-3-UPDOWN: Interface Gi0/1, changed state to up`
  - $t = 25s$: `<134>Nov 06 15:40:25 sw-01 %LINK-3-UPDOWN: Interface Gi0/1, changed state to down`
  - $t = 38s$: `<134>Nov 06 15:40:38 sw-01 %LINK-3-UPDOWN: Interface Gi0/1, changed state to up`
  - $t = 52s$: `<134>Nov 06 15:40:52 sw-01 %LINK-3-UPDOWN: Interface Gi0/1, changed state to down`
- **Kết quả mong đợi:**
  - Đúng thời điểm $t = 52s$, hệ thống sinh **1 Incident mới**.
  - Tiêu đề Incident: `Interface Gi0/1 on sw-01 is flapping`. Severity đối chiếu rule version được duyệt tại DEC-03.
  - Danh sách `evidence_event_ids` chứa chính xác 5 UUID của 5 event trên.
  - Đối soát incident và event IDs. Kênh WebSocket được kiểm riêng ở TC-UI-005 khi có hợp đồng transport và build.

#### TC-COR-002: Kiểm tra biên dưới - 4 lần trong 60 giây (Không tạo Incident)
- **Mã Jira:** `N42-44` | **Ưu tiên:** P1 (CRITICAL)
- **Kỹ thuật:** BVA ($Threshold - 1 = 4$)
- **Dữ liệu kiểm thử:** Bơm 4 sự kiện flap trên `sw-01`, `Gi0/1` tại các mốc $t = 0s, 10s, 20s, 30s$. Chờ tiếp 40 giây (tổng 70s).
- **Kết quả mong đợi:**
  - **Tuyệt đối không tạo Incident nào** trong bảng `incidents`.
  - 4 event vẫn lưu bình thường trong bảng `events`.

#### TC-COR-003: Kiểm tra vượt quá cửa sổ thời gian - Giây thứ 61 (BVA-06 Just Above)
- **Mã Jira:** `N42-44` | **Ưu tiên:** P1 (CRITICAL)
- **Kỹ thuật:** BVA ($Window + 1 = 61s$)
- **Dữ liệu kiểm thử:**
  - Event 1: $t = 0s$
  - Event 2: $t = 15s$
  - Event 3: $t = 30s$
  - Event 4: $t = 45s$
  - **Event 5: $t = 61s$**
- **Kết quả mong đợi:**
  - **Không tạo Incident**.
  - Giải thích: Tại mốc $t = 61s$, cửa sổ trượt $[1s \to 61s]$ chỉ còn chứa 4 sự kiện (Event 1 tại $t=0s$ đã bị loại bỏ vì quá hạn 60s).

#### TC-COR-004: Đúng biên 60 giây (BVA-06 On Boundary)
- **Mã Jira:** `N42-44` | **Ưu tiên:** P1 (CRITICAL)
- **Dữ liệu kiểm thử:** Bơm 5 event tại các mốc $t = 0s, 15s, 30s, 45s, 60s$ (Event 5 đúng mốc 60.000s).
- **Kết quả mong đợi:**
  - **Tạo Incident thành công** (Quy ước biên thời gian inclusive $\le 60s$).

#### TC-COR-005: Khác cổng mạng (Interface) trên cùng một thiết bị
- **Mã Jira:** `N42-44` | **Ưu tiên:** P1 (CRITICAL)
- **Dữ liệu kiểm thử:**
  - Bơm 3 event trên `sw-01`, cổng `Gi0/1`.
  - Bơm 3 event trên `sw-01`, cổng `Gi0/2`.
- **Kết quả mong đợi:**
  - **Không tạo Incident nào**. Grouping key phân biệt độc lập `(sw-01, Gi0/1)` và `(sw-01, Gi0/2)`.

#### TC-COR-006: Khác thiết bị (Device) trên cùng một tên cổng
- **Mã Jira:** `N42-44` | **Ưu tiên:** P1 (CRITICAL)
- **Dữ liệu kiểm thử:**
  - Bơm 3 event trên `sw-01`, cổng `Gi0/1`.
  - Bơm 3 event trên `sw-02`, cổng `Gi0/1`.
- **Kết quả mong đợi:**
  - **Không tạo Incident nào**.

#### TC-COR-007: Khử trùng lặp (Deduplication) khi bão sự kiện tiếp diễn
- **Mã Jira:** `N42-44` | **Ưu tiên:** P1 (CRITICAL)
- **Dữ liệu kiểm thử:** Bơm liên tục 20 event flap trên `sw-01`, `Gi0/1` trong vòng 40 giây.
- **Kết quả mong đợi:**
  - Chỉ duy nhất **1 bản ghi Incident** được tạo ra (không sinh 4 incident trùng).
  - Trường `event_count` trong Incident cập nhật tăng dần từ 5 lên 20.

#### TC-COR-008: Phát hiện bão cảnh báo SYN Flood từ Firewall (KB-03)
- **Mã Jira:** `N42-45` | **Ưu tiên:** P1 (CRITICAL)
- **Trạng thái:** `BLOCKED` — threshold 50, window 30s, severity và incident text là ví dụ chưa được BE3/owner nghiệp vụ xác nhận.
- **Tiền điều kiện:** Nạp luật `RULE-SEC-01-SYN-FLOOD` (`threshold: 50`, `window: 30s`, `group_by: [src_ip]`).
- **Dữ liệu kiểm thử:** Bơm 50 bản tin Firewall Deny từ IP `10.10.1.50` trong 10 giây.
- **Kết quả mong đợi:**
  - Sinh 1 Incident mức `CRITICAL`: `SYN Flood Attack suspected from 10.10.1.50`.

#### TC-COR-009: BGP Session Loss sau 3 lần retry (KB-05)
- **Mã Jira:** `N42-65` | **Ưu tiên:** P1 (CRITICAL)
- **Trạng thái:** `BLOCKED` — retry threshold/window/severity cần xác nhận bằng BE3 và owner nghiệp vụ; ví dụ hiện tại không phải acceptance.
- **Dữ liệu kiểm thử:** Bơm 3 bản tin `BGP_PEER_DOWN` cho IP `10.10.0.2` trong 5 phút.
- **Kết quả mong đợi:**
  - Sinh Incident mức `CRITICAL`: `BGP Neighbor 10.10.0.2 Down (Retries: 3)`.

#### TC-COR-010: Cảnh báo nguồn nguồn hỏng lập tức (Single-hit threshold = 1)
- **Mã Jira:** `N42-45` | **Ưu tiên:** P1 (CRITICAL)
- **Trạng thái:** `BLOCKED` — chỉ áp dụng khi rule single-hit được xác nhận trong baseline; severity/incident mapping cần owner xác nhận.
- **Dữ liệu kiểm thử:** 1 bản tin duy nhất `POWER_SUPPLY_FAILED` từ `ne40e-bras-01`.
- **Kết quả mong đợi:**
  - Sinh ngay 1 Incident `CRITICAL` mà không cần đợi cửa sổ hay tích lũy số lượng.

#### TC-COR-011: Hai luật khác nhau cùng kích hoạt trên một thiết bị
- **Mã Jira:** `N42-44`, `N42-66` | **Ưu tiên:** P2 (HIGH)
- **Dữ liệu kiểm thử:** Thiết bị `sw-01` phát sinh: 5 flap trên Gi0/1 VÀ 1 cảnh báo quá nhiệt `CPU_TEMP_ALARM`.
- **Kết quả mong đợi:**
  - Sinh **2 Incident độc lập**: 1 về Link Flap (MAJOR) và 1 về CPU Temperature (MAJOR). Không bị ghi đè.

#### TC-COR-012: Tự động phục hồi Incident (Auto-resolve sau 300s)
- **Mã Jira:** `N42-44` | **Ưu tiên:** P2 (HIGH)
- **Trạng thái:** `BLOCKED` — timeout 300 giây chưa được xác nhận trong yêu cầu/AC; chỉ đưa vào nghiệm thu sau khi có quyết định.
- **Dữ liệu kiểm thử:** Sau khi tạo Incident Link Flap, hệ thống không nhận thêm bất kỳ event nào trong 300 giây.
- **Kết quả mong đợi:**
  - Trạng thái Incident tự động chuyển từ `NEW` sang `AUTO_RESOLVED`.

---

### 6.4 Cấu hình luật — BE3 (TC-RUL)

**Local review revision 12/11/2026:** validator N42-17 hiện có trên nhánh
`feature/N42-17-rules-yaml-design`; QA/TL sign-off vẫn pending. Đây là đối chiếu code và
expected tại boundary loader; không phải nghiệm thu reload/detector hoặc sửa Confluence.
Contract đang được kiểm bằng `app/models/rule_config.py`, `app/services/rule_config_loader.py`
và `tests/test_rules_config.py`; các quyết định nghiệp vụ cần QA/TL xác nhận trên Jira N42-17.

| Test case | Jira / priority | Input | Expected |
|---|---|---|---|
| TC-RUL-001 | N42-17 / P1 | app/services/rules.yaml; YAML1.2/UTF-8 hợp lệ, biên1 | RuleConfiguration version0.1.1 có đúng3 mẫu tắt; default enabled=false |
| TC-RUL-002 | N42-17 / P1 | tab indentation, duplicate YAML key | YAMLError, vị trí dòng/cột nếu thư viện cung cấp; không partial success |
| TC-RUL-003 | N42-17 / P1 | threshold0 | ValidationError loc=(rules,0,threshold); yêu cầu integer>0 |
| TC-RUL-004 | N42-17 / P1 | window_seconds0 | ValidationError loc=(rules,0,window_seconds); yêu cầu integer>0 |
| TC-RUL-005 | N42-17 / P2 | threshold="five"/"1"/true/1.5; window sai kiểu tương tự | ValidationError đúng loc; không coercion string/bool/float thành int |
| TC-RUL-006 | N42-38 / P2 | bộ luật mới hợp lệ | BLOCKED/NOT RUN: atomic reload/version/hash; route và response target chờ contract N38 |
| TC-RUL-007 | N42-38 / P1 | reload YAML không hợp lệ | BLOCKED/NOT RUN: giữ bộ active cũ và rollback/audit theo contract N38 |

Không kiểm nguyên văn exception của một library version. Unit test thực thi:
`python -m pytest tests/test_rules_config.py -q --junitxml=scratch/n42-17-config-junit.xml`.
File thiếu/encoding hỏng, root sai, field thừa, empty match/catalog/group, identifier sai,
ID/group trùng và YAML object tag không an toàn được kiểm bổ sung trong cùng module.
Các nhóm lỗi có loc/file phù hợp trong contract; không tạo CLI/API mới chỉ để chạy test.

Fixture review `tests/fixtures/rules/review-cases.json` dùng synthetic fields proposed:
LF-01–07, PSU-01–07, BGP-01/02. Expected này chưa được engine thực thi, QA review pending.
Catalog ứng viên0.1.1/MAJOR nằm riêng tại `tests/fixtures/rules/candidate-0.1.1.yaml`;
catalog ứng dụng đã0.1.1/MAJOR theo ủy quyền user, QA/TL xác nhận sau. Nguồn kép cần QA chốt distinct slots,
không dùng single-hit KB02 thay cho dual-PSU. Mọi execution record cần HEAD + working-tree
hash, phiên bản config/fixture/dependencies, timestamp và JUnit thực tế.

---

### N42-17: ca bổ sung TC-RUL-008–011 (triển khai trước approval theo ủy quyền user)

| TC | Input | Expected |
|---|---|---|
| TC-RUL-008 | window86400/86401; threshold10000/10001; text tại/vượt caps | tại caps hợp lệ; vượt caps ValidationError đúng field |
| TC-RUL-009 | severity CRITICAL/MAJOR/MINOR/WARNING/INFO và MAJRO | enum hợp lệ được nạp; typo bị ValidationError ở action.incident_severity |
| TC-RUL-010 | enabled thiếu contract/thiếu field/có đủ field match,group,count | thiếu contract hoặc field bị ValidationError; đủ field nạp được; disabled nhận proposed field |
| TC-RUL-011 | expected_sha256 đúng/sai/sai format; thêm comment giữ version | digest đúng nạp; mismatch/malformed ValueError; thay exactbytes bị phát hiện khi pin |

Owner BE3; trace local FR15/AC05, spec amendment ngày12/11. Expected do trợ lý quyết định
theo ủy quyền người dùng, QA/TL phê duyệt sau. Không có claim activation/detector PASS.

### 6.5 Query và Dashboard (TC-UI)

#### TC-UI-001: Hiển thị đầy đủ 4 thẻ KPI tổng quan hệ thống
- **Mã Jira:** `N42-20` | **Ưu tiên:** P1 (CRITICAL)
- **Kết quả mong đợi:** Hiển thị chính xác số liệu: Tổng sự kiện, Sự cố đang mở, Tốc độ bản tin hiện tại (msg/s), Trạng thái hệ thống (Healthy).

#### TC-UI-002: Lọc danh sách sự kiện theo Mức độ nghiêm trọng (Severity)
- **Mã Jira:** `N42-28`, `N42-34` | **Ưu tiên:** P2 (HIGH)
- **Thực hiện:** Chọn filter `severity=CRITICAL`.
- **Kết quả mong đợi:** Bảng chỉ hiển thị các sự kiện có severity là CRITICAL.

#### TC-UI-003: Phân trang dữ liệu (Pagination) ổn định
- **Mã Jira:** `N42-28`, `N42-34` | **Ưu tiên:** P2 (HIGH)
- **Thực hiện:** DB có 500 event, chọn `page_size = 50`. Chuyển sang trang 2.
- **Kết quả mong đợi:** Hiển thị đúng từ bản ghi 51 đến 100, không bị trùng lặp hoặc mất bản ghi.

#### TC-UI-004: Chống tấn công SQL Injection trong ô tìm kiếm
- **Mã Jira:** `N42-34`, `N42-39` | **Ưu tiên:** P1 (CRITICAL)
- **Dữ liệu đầu vào:** Nhập ô tìm kiếm: `' OR '1'='1'; DROP TABLE events; --`
- **Kết quả mong đợi:**
  - Truy vấn tham số hóa (Parameterized Query) an toàn, trả về danh sách rỗng, bảng CSDL nguyên vẹn.

#### TC-UI-005: Cập nhật Incident thời gian thực qua WebSocket
- **Điều kiện chạy:** N42-51/N42-53 có phạm vi được duyệt và build hỗ trợ transport. Khi thiếu điều kiện, ghi BLOCKED và nêu dependency.
- **Mã Jira:** `N42-51`, `N42-53` | **Ưu tiên:** P1 (CRITICAL)
- **Thực hiện:** Đang mở màn hình Dashboard, Correlation Engine kích hoạt 1 Incident mới.
- **Kết quả mong đợi:**
  - Hàng sự cố mới xuất hiện lập tức trên UI và nhấp nháy đỏ mà không cần người dùng nhấn F5.

#### TC-UI-006: Trạng thái tải, rỗng, lỗi và điều hướng bàn phím
- **Mã Jira:** `N42-20`, `N42-28`, `N42-47`, `N42-53`
- **Nguồn:** Yêu cầu UX trong `ARCHITECTURE_DESIGN.md`; ngoài AC hiện tại, cần FE/TL chốt test scope.
- **Trạng thái:** `BLOCKED` — frontend chưa có trong repo.
- **Các bước:** kiểm tra màn hình khi đang tải, không có kết quả, API lỗi/timeout và dùng bàn phím điều hướng các filter/bảng.
- **Kết quả mong đợi:** mỗi trạng thái có thông báo rõ; bảng/filter có focus và thao tác bàn phím; severity không chỉ phân biệt bằng màu; timezone hiển thị rõ. Lưu ảnh/video và browser/viewport.

#### TC-EXP-001: Export tuân theo filter, escaping và giới hạn
- **Mã Jira:** `N42-63`
- **Requirement:** FR-14 / AC-04, AC-08.
- **Trạng thái:** `BLOCKED` — format (CSV/PDF), endpoint/UI contract và maximum rows chưa được chốt.
- **Tiền điều kiện:** có fixture chứa dấu phẩy, dấu nháy, newline, Unicode và một giá trị rỗng; filter/query contract đã duyệt.
- **Các bước:** export với cùng filter đang áp dụng ở event list; thử kết quả rỗng, ký tự cần quote/escape và giới hạn bản ghi; so sánh nội dung export với query canonical.
- **Kết quả mong đợi:** export không thêm/bỏ record ngoài filter; file parse được theo format đã chốt; cell/record không bị tách do dữ liệu chứa delimiter/newline; hành vi vượt limit được thông báo theo contract. Ghi hash và số dòng/file.

---

### 6.6 Đo kiểm tải danh định và sức chịu đựng (QA — TC-PERF)

#### TC-PERF-001: Đo checkpoint tải 1.000 msg/s trong 10 phút (checkpoint, không phải nghiệm thu cuối)
- **Mã Jira:** `N42-57` | **Ưu tiên:** P1 (CRITICAL)
- **Cấu hình phát tải:** Máy phát tải bơm đều đặn 1.000 datagram/giây liên tục trong 600 giây.
- **Kết quả mong đợi:**
  - Tổng số gói gửi: `600,000`.
  - Tổng số gói ghi nhận tại CSDL: `600,000`.
  - **Tỷ lệ rớt gói:** Đúng **$0.00\%$**.
  - Áp dụng ngưỡng theo `ACCEPTANCE_CRITERIA.md`: CPU $\le 60\%$ trên 4 core và RAM $\le 1.5$ GB; ghi đây là checkpoint 10 phút, không phải final acceptance.

#### TC-PERF-002: Bài kiểm tra Nghiệm thu Tải 1.000 msg/s trong 1 giờ (W13 Final Acceptance)
- **Mã Jira:** `N42-57` | **Ưu tiên:** P1 (CRITICAL)
- **Cấu hình:** Bơm 1.000 msg/s liên tục trong 3.600 giây (3,6 triệu bản tin).
- **Kết quả mong đợi:**
  - Đối soát sent/received/persisted theo ID; observed drop là 0.00% trong giới hạn đo.
  - Cùng run phải ghi P50 <50ms, P99 <200ms, CPU ≤60% trên 4 core và RAM ≤1.5GB theo `ACCEPTANCE_CRITERIA.md`.
  - Lưu môi trường, commit, config, generator/receiver version, counters và raw report; thiếu bất kỳ số liệu nào thì kết luận chưa đủ evidence.

#### TC-PERF-003: Đo kiểm độ trễ xử lý $P_{50}$ và $P_{99}$
- **Mã Jira:** `N42-52`, `N42-57` | **Ưu tiên:** P1 (CRITICAL)
- **Kết quả mong đợi:**
  - Độ trễ trung vị $P_{50} < 50$ ms.
  - Phân vị $P_{99} < 200$ ms.

#### TC-PERF-004: Kiểm tra đột biến tải (Spike Test) 1.500 msg/s trong 2 phút
- **Mã Jira:** `N42-11`, `N42-57` | **Ưu tiên:** P2 (HIGH)
- **Cấu hình:** Đẩy vọt từ 1.000 lên 1.500 msg/s trong 120 giây.
- **Kết quả mong đợi:**
  - Ghi observed throughput, drops, queue/resource và thời gian hồi phục; hệ thống không crash/treo.
  - Đây là stress characterization; chưa có ngưỡng tỷ lệ drop nghiệm thu được AC phê duyệt cho spike nên không gán pass rate 0.05%.

---

### 6.7 Phân hệ An toàn Thông tin & Tuân thủ Dữ liệu Viễn thông (TC-SEC)

#### TC-SEC-001: Rà quét không Hardcode Secret/Password trong Source Code
- **Mã Jira:** `N42-60` | **Ưu tiên:** P1 (CRITICAL)
- **Lệnh thực hiện:** `python tools/check_sensitive.py`
- **Kết quả mong đợi:** Output báo không phát hiện finding trên phạm vi quét đã ghi. Script hiện không trả exit code khác 0 khi có finding, vì vậy exit code đơn lẻ không đủ làm tiêu chí pass; lỗi này cần được sửa trước khi dùng scanner làm CI gate.

#### TC-SEC-002: Tuân thủ policy địa chỉ IP dữ liệu giả lập trong lab (AC-08)
- **Mã Jira:** `N42-60` | **Ưu tiên:** P1 (CRITICAL)
- **Kết quả mong đợi:** IP fixture thuộc RFC1918; TEST-NET (`203.0.113.0/24`, `198.51.100.0/24`, `192.0.2.0/24`) chỉ dùng minh họa; loopback `127.0.0.1` chỉ dùng cho test local. Không đưa IP/host production vào fixture. Lưu ý đây là rà soát dữ liệu test; regex scanner hiện tại chưa tự chứng minh toàn bộ policy này.

### 6.8 Health/diagnostics (TC-HLT)

#### TC-HLT-001: Liveness endpoint `/api/health` của ứng dụng
- **Mã Jira:** `N42-13` | **Ưu tiên:** P1 (CRITICAL)
- **Trạng thái:** Có thể kiểm tra trên baseline hiện tại; đây chỉ là liveness của app, không phải health của các dependency.
- **Các bước thực hiện:**
  1. Gửi `GET /api/health`.
- **Kết quả mong đợi:**
  - HTTP Status: `200 OK`.
  - Body đúng với baseline: `{"status":"UP","service":"n42-api","version":"0.1.0"}`.
  - Không suy diễn từ response này rằng DB, receiver hoặc correlation engine đang khỏe.

#### TC-HLT-002: Health endpoint khi Database bị tắt (Negative — Graceful Degradation)
- **Mã Jira:** `N42-13` (BLOCKED: readiness/DB health contract) | **Ưu tiên:** P1 (CRITICAL)
- **Trạng thái:** `BLOCKED` — readiness/dependency health và database runtime chưa được triển khai. `/api/health` hiện là liveness và không kiểm tra DB; không kỳ vọng endpoint này trả 503 khi DB dừng.
- **Tiền điều kiện:** Tắt dịch vụ PostgreSQL bằng `docker stop n42-postgres`.
- **Các bước thực hiện sau khi readiness contract được duyệt:**
  1. Dừng dependency DB trong môi trường test cô lập.
  2. Gọi readiness endpoint theo OpenAPI đã duyệt (path chưa được chốt).
- **Kết quả mong đợi:**
  - Readiness báo không sẵn sàng theo status/schema đã chốt; liveness `/api/health` tiếp tục xác nhận process còn sống.
  - Body/schema và error code theo readiness contract được duyệt; thông báo lỗi không chứa connection string, mật khẩu hoặc chi tiết nhạy cảm.
  - Tiến trình App server vẫn hoạt động (không crash theo DB).

#### TC-HLT-003: Health endpoint không lộ thông tin bảo mật (Security Hardening)
- **Mã Jira:** `N42-13`, `N42-60` | **Ưu tiên:** P1 (CRITICAL)
- **Kỹ thuật:** Kiểm thử bảo mật (Security Testing)
- **Các bước thực hiện:**
  1. Gửi `GET /api/health`.
  2. Tìm kiếm trong response body các từ khóa nhạy cảm.
- **Kết quả mong đợi:**
  - Không xuất hiện bất kỳ chuỗi nhạy cảm nào (chi dung lab kiểm thử): password, secret, token, api_key, priv-key, connection_string, jdbc, postgresql.
  - Không chứa IP Public thật (regex từ `tools/check_sensitive.py`).
  - Không chứa raw event data hoặc nội dung bản tin syslog.

#### TC-HLT-004: Kiểm tra bộ đếm Metrics tăng chính xác sau mỗi event
- **Mã Jira:** `N42-13` (BLOCKED: metrics contract) | **Ưu tiên:** P2 (HIGH)
- **Trạng thái:** `BLOCKED` — counters và ingest pipeline chưa tồn tại trong baseline.
- **Các bước thực hiện:**
  1. Gọi `GET /api/health` → ghi nhận `events_received = N`.
  2. Gửi 10 datagram UDP hợp lệ.
  3. Gọi `GET /api/health` → ghi nhận `events_received = N'`.
- **Kết quả mong đợi:**
  - $N' = N + 10$.
  - `events_persisted` cũng tăng đúng 10 (nếu DB hoạt động bình thường).
  - `events_dropped` không thay đổi (vì 10 gói đều hợp lệ).

---

### 6.9 Phân hệ Kiểm thử Tích hợp End-to-End (Integration Test — TC-INT)

#### TC-INT-001: Luồng xử lý hoàn chỉnh từ UDP → Parser → DB → Dashboard
- **Mã Jira:** `N42-13` → `N42-15` → `N42-30`/`N42-31` → `N42-34` → `N42-20` | **Ưu tiên:** P1 (CRITICAL)
- **Mục tiêu:** Kiểm chứng toàn bộ pipeline hoạt động liên tục không gián đoạn ở mức tích hợp hệ thống.
- **Tiền điều kiện:** Docker Compose đã dựng đầy đủ tất cả container (App, PostgreSQL, Frontend).
- **Dữ liệu đầu vào:**
  ```text
  <134>Nov 07 14:00:00 sw-integration-test %LINK-3-UPDOWN: Interface GigabitEthernet0/1, changed state to down
  ```
- **Các bước thực hiện:**
  1. Gửi 1 datagram UDP tới `127.0.0.1:5514`.
  2. Chờ 2 giây cho pipeline xử lý hoàn tất.
  3. Gọi API: `GET /api/v1/events?device_name=sw-integration-test`.
  4. Kiểm tra bảng `events` trong PostgreSQL qua DBeaver hoặc `psql`.
  5. Mở Dashboard FE, xác nhận event hiển thị trên giao diện.
- **Kết quả mong đợi:**
  - API trả về đúng 1 event với `device_name = "sw-integration-test"`.
  - PostgreSQL có 1 row tương ứng, `raw_message` nguyên vẹn.
  - Dashboard FE hiển thị dòng event mới với icon severity màu vàng (WARNING).
  - Latency tổng (từ lúc gửi UDP đến lúc hiển thị trên FE) < 3 giây.

#### TC-INT-002: Luồng tích hợp hoàn chỉnh: Link Flap → Incident → WebSocket → Dashboard Alert
- **Điều kiện chạy:** Ghi phiên bản luật DEC-03 và build. Phần WebSocket chỉ chạy khi transport đã được duyệt; ghi riêng kết quả tạo incident và kết quả truyền tới Dashboard.
- **Mã Jira:** `N42-44` → `N42-46` → `N42-51` → `N42-53` | **Ưu tiên:** P1 (CRITICAL)
- **Mục tiêu:** Kiểm chứng chuỗi xử lý từ sự kiện thô → tương quan → tạo sự cố → giao diện.
- **Các bước thực hiện:**
  1. Mở Dashboard FE trên trình duyệt, kết nối WebSocket.
  2. Bơm 5 event Link Flap lên UDP 5514 trong khoảng 30 giây.
  3. Quan sát Dashboard FE.
- **Kết quả mong đợi:**
  - Sau event thứ 5, Dashboard tự động hiển thị 1 Incident mới nhấp nháy đỏ.
  - Incident chứa đúng 5 event evidence.
  - Không cần người dùng nhấn F5.

#### TC-INT-003: Kiểm tra tính toàn vẹn khi Restart Server
- **Mã Jira:** `N42-30`, `N42-31`, `N42-55` | **Ưu tiên:** P2 (HIGH)
- **Các bước thực hiện:**
  1. Gửi 1.000 event hợp lệ qua UDP.
  2. Ghi nhận `events_persisted` từ Health endpoint.
  3. Restart container App: `docker restart n42-app`.
  4. Chờ 10 giây cho App khởi động lại.
  5. Gọi `GET /api/v1/events?limit=1000`.
- **Kết quả mong đợi:**
  - Toàn bộ 1.000 event vẫn truy vấn được sau restart (Dữ liệu đã persist trong PostgreSQL).
  - Health endpoint báo `status: "healthy"` sau khi restart thành công.

#### TC-INT-004: Kiểm tra xử lý đồng thời UDP + REST API
- **Mã Jira:** `N42-13`, `N42-14` | **Ưu tiên:** P2 (HIGH)
- **Các bước thực hiện:**
  1. Đồng thời: Bơm 100 event qua UDP VÀ 50 event qua REST API.
  2. Chờ 5 giây.
  3. Đếm tổng event trong DB.
- **Kết quả mong đợi:**
  - Tổng số bản ghi trong DB: đúng **150** event.
  - Không trùng lặp, không mất dữ liệu, không xung đột khóa (lock contention).

---

### 6.10 Phân hệ Cơ sở Dữ liệu & Tính toàn vẹn (TC-DB)

#### TC-DB-001: Ràng buộc Unique trên `event_id` (Primary Key Integrity)
- **Mã Jira:** `N42-15`, `N42-16`, `N42-30` | **Ưu tiên:** P1 (CRITICAL)
- **Các bước thực hiện:**
  1. Thử insert 2 bản ghi có cùng `event_id` vào bảng `events`.
- **Kết quả mong đợi:**
  - PostgreSQL ném `IntegrityError: duplicate key value violates unique constraint`.
  - Chỉ 1 bản ghi tồn tại trong DB.

#### TC-DB-002: Ràng buộc NOT NULL trên các trường bắt buộc
- **Mã Jira:** `N42-15`, `N42-16`, `N42-30` | **Ưu tiên:** P2 (HIGH)
- **Các bước thực hiện:**
  1. Thử insert bản ghi thiếu `raw_message` (giá trị NULL).
- **Kết quả mong đợi:**
  - PostgreSQL ném `IntegrityError: null value in column "raw_message"`.

#### TC-DB-003: Index hiệu năng trên trường `received_at` và `device_name`
- **Mã Jira:** `N42-30`, `N42-39` | **Ưu tiên:** P2 (HIGH)
- **Các bước thực hiện:**
  1. Insert 100.000 event vào DB.
  2. Chạy query: `SELECT * FROM events WHERE received_at >= '2026-11-06' AND device_name = 'sw-core-01' LIMIT 50`.
  3. Đo thời gian thực thi bằng `EXPLAIN ANALYZE`.
- **Kết quả mong đợi:**
  - Query plan sử dụng Index Scan (không phải Seq Scan).
  - Thời gian thực thi < 100ms trên bộ dữ liệu 100K rows.

#### TC-DB-004: Kiểm tra cascade khi xóa Incident (Referential Integrity)
- **Mã Jira:** `N42-33`, `N42-55` | **Ưu tiên:** P3 (MEDIUM)
- **Các bước thực hiện:**
  1. Tạo 1 Incident có 5 evidence event link.
  2. Xóa Incident đó khỏi bảng `incidents`.
- **Kết quả mong đợi:**
  - Các bản ghi trong bảng `incident_evidence` bị xóa theo (ON DELETE CASCADE).
  - 5 event gốc trong bảng `events` vẫn tồn tại (không bị xóa theo).

---

### 6.11 Phân hệ Bảo mật & Kiểm soát Truy cập Nâng cao (TC-SEC — Mở rộng)

#### TC-SEC-003: Rà quét mã nguồn bằng script `check_sensitive.py` (Automated Secret Scan)
- **Mã Jira:** `N42-10`, `N42-50`, `N42-60` | **Ưu tiên:** P1 (CRITICAL)
- **Công cụ:** Script `tools/check_sensitive.py` với 4 mẫu regex nhạy cảm:
  1. `(?i)(password|passwd|pwd)\s*[:=]\s*["']...["']` → Bắt lộ mật khẩu hardcode.
  2. `(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*["']...["']` → Bắt lộ API Key/Token.
  3. `(?i)private[_-]?key` → Bắt file hoặc chuỗi Private Key.
  4. `\b(?!0\.0\.0\.0)(?!10\.)(?!192\.168\.)(?!172\.(1[6-9]|2[0-9]|3[0-1])\.)(?!203\.0\.113\.)(?!198\.51\.100\.)(?!192\.0\.2\.)(?!127\.)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b` → Bắt IP Public thật (loại trừ dải Private RFC 1918 và TEST-NET RFC 5737).
- **Các bước thực hiện:**
  ```bash
  cd /path/to/n42
  python tools/check_sensitive.py .
  ```
- **Kết quả mong đợi:**
  - Exit code: `0`.
  - Output: `[✔] AN TOÀN: Không phát hiện từ khóa nhạy cảm hay thông tin rò rỉ.`
  - Nếu phát hiện lỗi: Output chỉ rõ file, dòng, loại cảnh báo.

#### TC-SEC-004: Kiểm tra chống SQL Injection trên API Query Events
- **Mã Jira:** `N42-34`, `N42-39` | **Ưu tiên:** P1 (CRITICAL)
- **Dữ liệu đầu vào:**
  - `GET /api/v1/events?device_name='; DROP TABLE events; --`
  - `GET /api/v1/events?severity=' UNION SELECT * FROM pg_shadow --`
  - `GET /api/v1/events?device_name=1 OR 1=1`
- **Kết quả mong đợi (cho mỗi request):**
  - HTTP Status: `422 Unprocessable Entity` hoặc `200 OK` với kết quả rỗng.
  - Bảng `events` và `pg_shadow` hoàn toàn nguyên vẹn.
  - Query log cho thấy Parameterized Query (`$1`, `$2`) được sử dụng thay vì string concatenation.

#### TC-SEC-005: Kiểm tra chống XSS (Cross-Site Scripting) trên Dashboard
- **Mã Jira:** `N42-20`, `N42-47`, `N42-53` | **Ưu tiên:** P2 (HIGH)
- **Dữ liệu đầu vào:** Gửi syslog có nội dung chứa mã HTML/JS:
  ```text
  <134>Nov 07 14:00:00 attacker-host %ALERT: <script>alert('XSS')</script>
  ```
- **Kết quả mong đợi:**
  - Dashboard hiển thị chuỗi `<script>alert('XSS')</script>` dưới dạng **văn bản thuần** (text), không thực thi JavaScript.
  - Kiểm tra DOM: Nội dung được mã hóa HTML entities (`&lt;script&gt;`).

#### TC-SEC-006: Kiểm tra chống Path Traversal trên File Import
- **Mã Jira:** `N42-22` | **Ưu tiên:** P2 (HIGH)
- **Dữ liệu đầu vào:** Upload file với tên `../../../etc/passwd`.
- **Kết quả mong đợi:**
  - HTTP Status: `400 Bad Request`.
  - Hệ thống từ chối, không đọc file ngoài thư mục upload.

#### TC-SEC-007: Kiểm tra giới hạn tốc độ API (Rate Limiting)
- **Mã Jira:** `N42-40` | **Ưu tiên:** P3 (MEDIUM)
- **Các bước thực hiện:** Gửi 1.000 request `POST /api/v1/events/ingest` trong 10 giây từ cùng IP.
- **Kết quả mong đợi:**
  - Sau ngưỡng cấu hình (ví dụ 100 req/s), trả HTTP `429 Too Many Requests`.
  - Các request hợp lệ trước ngưỡng vẫn được xử lý bình thường.

---

### 6.12 Phân hệ Đo kiểm Hiệu năng Nâng cao (TC-PERF — Mở rộng)

#### TC-PERF-005: Đo kiểm rò rỉ bộ nhớ (Memory Leak Test) trong 30 phút
- **Mã Jira:** `N42-58` | **Ưu tiên:** P1 (CRITICAL)
- **Cấu hình:** Bơm 500 msg/s liên tục trong 30 phút (900.000 bản tin tổng).
- **Các bước thực hiện:**
  1. Ghi nhận RSS (Resident Set Size) bộ nhớ tại $t = 0$ phút.
  2. Ghi nhận RSS tại $t = 10, 20, 30$ phút.
  3. Vẽ đồ thị tăng trưởng bộ nhớ theo thời gian.
- **Kết quả mong đợi:**
  - Bộ nhớ tăng ban đầu (warm-up) rồi **ổn định** (plateau), không tăng tuyến tính.
  - Mức tăng tối đa cho phép: $\le 50$ MB sau 30 phút ở tải 500 msg/s.
  - Nếu tăng > 100 MB/giờ → nghi ngờ memory leak, cần kiểm tra với `tracemalloc`.

#### TC-PERF-006: Đo kiểm Connection Pool PostgreSQL dưới tải cao
- **Mã Jira:** `N42-31`, `N42-58` | **Ưu tiên:** P2 (HIGH)
- **Cấu hình:** Pool size = 10 connections, bơm 1.000 msg/s.
- **Các bước thực hiện:**
  1. Chạy bài test 10 phút ở tải 1.000 msg/s.
  2. Theo dõi `pg_stat_activity` để đếm số kết nối đang hoạt động.
- **Kết quả mong đợi:**
  - Số connection PostgreSQL không vượt quá pool size (10).
  - Không có connection rò rỉ (idle connections tăng dần).
  - Không xuất hiện lỗi `too many connections` trong log.

#### TC-PERF-007: Đo kiểm thời gian khởi động Cold Start
- **Mã Jira:** `N42-59` | **Ưu tiên:** P3 (MEDIUM)
- **Các bước thực hiện:**
  1. `docker-compose down` toàn bộ.
  2. `docker-compose up -d` và đo thời gian từ lúc start đến khi Health endpoint trả `200 OK`.
- **Kết quả mong đợi:**
  - Cold start toàn bộ hệ thống (App + PostgreSQL) $\le 30$ giây.

#### TC-PERF-008: Benchmark hiệu năng Query với 1 triệu bản ghi
- **Mã Jira:** `N42-39`, `N42-30` | **Ưu tiên:** P2 (HIGH)
- **Tiền điều kiện:** Đã seed 1.000.000 event vào PostgreSQL.
- **Các bước thực hiện:**
  1. `GET /api/v1/events?severity=CRITICAL&limit=50` → đo thời gian.
  2. `GET /api/v1/events?device_name=sw-core-01&start_time=2026-11-06T00:00:00Z&end_time=2026-11-06T23:59:59Z` → đo thời gian.
- **Kết quả mong đợi:**
  - Cả 2 query trả kết quả trong < 2 giây (NFR-05).
  - Query plan sử dụng Index Scan.

---

### 6.13 Cổng bàn giao và vận hành dự án (TC-OPS)

#### TC-REP-001: Replay cùng scenario/seed cho kết quả tái lập
- **Mã Jira:** `N42-11`, `N42-54`
- **Requirement:** FR-13.
- **Trạng thái:** `BLOCKED` — replay harness, ID strategy và schema report chưa được triển khai/chốt.
- **Tiền điều kiện:** scenario version, seed, fixture hash, rule version và expected labels đã đóng băng.
- **Các bước:** chạy cùng scenario/seed hai lần trên cùng commit/config; lưu input/output IDs, thứ tự phát, expected labels và correlation result.
- **Kết quả mong đợi:** payload/order và outcome theo deterministic contract giống nhau; mọi sai khác được ghi nhận. Không so sánh timestamp wall-clock hoặc UUID random trừ khi contract quy định chúng deterministic.

#### TC-OPS-001: Dựng và demo trên máy sạch trong thời hạn bàn giao
- **Mã Jira:** `N42-59`
- **Requirement:** AC-07; handover checklist #2.
- **Trạng thái:** `BLOCKED` — gói bàn giao và pipeline hoàn chỉnh chưa có.
- **Các bước:** dùng đúng release artifact và runbook trên máy sạch/isolated lab; bắt đầu tính giờ khi bắt đầu cài; dựng services, kiểm tra `/api/health`, chạy các luồng demo đã chọn và lưu log/video.
- **Kết quả mong đợi:** hoàn tất ≤1 giờ theo AC-07; ghi OS, phiên bản, commit/tag, config, bước xử lý lỗi và bằng chứng. Không coi app health đơn lẻ là demo toàn hệ thống.

#### TC-OPS-002: CI kiểm tra chất lượng và ngăn merge khi lỗi
- **Mã Jira:** `N42-10`, `N42-50`
- **Nguồn:** QA role, kickoff minutes và quy trình PR.
- **Owner:** QA Lead; phối hợp DevOps/code owners.
- **Trạng thái (12/11/2026):** `PARTIAL / PENDING VERIFICATION` — đã có workflow; bản nâng cấp local và test failure probes chưa thay thế run PR mới hoặc kiểm chứng enforcement. API main trả protected nhưng required checks trống; chi tiết protection chưa đọc được do quyền kết nối. Xem [hồ sơ N42-10](N42-10_HANDOVER.md) cho MG-01–06 và evidence cần thu.
- **Các bước sau khi QA bổ sung workflow:** rà triggers/jobs/checks; chạy PR pass và fail có kiểm soát; nếu policy yêu cầu merge gate, xác minh required check và branch protection trực tiếp trên GitHub.
- **Kết quả mong đợi:** workflow chạy checks được nhóm duyệt và kết quả gắn commit; chỉ khẳng định merge bị chặn nếu required check/branch protection đã cấu hình. Lưu YAML, run pass/fail và bằng chứng cấu hình.

#### TC-OPS-003: Dựng Compose theo từng profile và xác minh trạng thái service
- **Mã Jira:** `N42-59`, `N42-13`
- **Nguồn:** `docker-compose.yml`, `ARCHITECTURE_DESIGN.md`, handover checklist.
- **Trạng thái:** Chỉ DB/profile scaffold hiện có thể xác minh; full pipeline `BLOCKED`.
- **Các bước:** ghi profile/command chính xác; kiểm tra host port binding/credential trước khi chạy; dựng và dừng từng service; kiểm tra health/dependency, volume và log.
- **Kết quả mong đợi:** service/port đúng với runbook; chỉ bind loopback hoặc lab interface đã được phê duyệt; không hardcode credential theo AC-08; không ghi “full stack healthy” khi app chưa nối DB hoặc thành phần chưa triển khai. Lưu compose config, container status và logs.
- **Finding khi rà tĩnh:** compose hiện map DB `5432:5432`, app `8080:8080` (không chỉ định loopback) và có `POSTGRES_PASSWORD` literal mang nhãn local-dev. Cần xử lý/đánh giá phạm vi cô lập trước khi dùng ngoài máy lab riêng.

#### TC-OPS-004: Rà soát bộ hồ sơ trước phát hành/bàn giao
- **Mã Jira:** `N42-56`, `N42-61`
- **Nguồn:** `DOCUMENT_CONTROL.md` và `HANDOVER_CHECKLIST.md`.
- **Owner:** QA Lead (nội dung kiểm thử/evidence) + Team Leader (phê duyệt hồ sơ).
- **Trạng thái:** Review checklist; hiện có gap tài liệu chưa giải quyết.
- **Các bước:** đối chiếu version/date/owner/status giữa Charter, Decision Log, weekly report, minutes, SRS, AC, TDD, test plan, RTM và package phát hành.
- **Kết quả mong đợi:** hồ sơ không khẳng định approval/test/pass khi thiếu evidence; xung đột lịch/role/TCP/module mapping được giải quyết bằng quyết định/đính chính có owner trước khi phát hành. Lưu checklist ký xác nhận.

## 7. PHÁC THẢO HARNESS KIỂM THỬ (CHƯA PHẢI AUTOMATED TESTS)

Các đoạn dưới đây là phác thảo định hướng, **không chạy được như hiện trạng và không nên copy nguyên trạng vào CI**: một số assertion/API/DB chưa tồn tại, còn TODO hoặc phụ thuộc contract tương lai. Chỉ chuyển thành automated test sau khi có implementation, fixture cô lập và assertion hoàn chỉnh. Automated tests hiện có được liệt kê trong `REQUIREMENTS_TRACEABILITY_MATRIX.md`.

### 7.1 Script kiểm thử UDP Ingestion (Dành cho BE1 — Phạm Hoàng Long)

```python
# tests/test_udp_ingestion.py
"""
Test cases cho BE1 — UDP Syslog Receiver.
Chạy: pytest tests/test_udp_ingestion.py -v
"""
import socket
import time
import pytest

UDP_HOST = "127.0.0.1"
UDP_PORT = 5514

def send_udp(payload: bytes) -> None:
    """Gửi 1 datagram UDP tới Receiver."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(payload, (UDP_HOST, UDP_PORT))
    sock.close()

class TestUDPIngestion:
    """TC-ING-001 → TC-ING-006: Kiểm thử tiếp nhận Syslog UDP."""

    def test_ing_001_valid_rfc3164(self):
        """TC-ING-001: Nhận syslog RFC 3164 hợp lệ tạo đúng 1 event."""
        payload = b"<134>Nov 06 15:00:00 sw-core-01 %LINK-3-UPDOWN: Interface GigabitEthernet0/1, changed state to down"
        send_udp(payload)
        time.sleep(0.5)
        # TODO: Query API kiểm tra event mới nhất
        # response = requests.get(f"http://localhost:8000/api/v1/events?limit=1")
        # assert response.status_code == 200
        # event = response.json()["data"][0]
        # assert event["raw_message"] == payload.decode()
        # assert event["device_name"] == "sw-core-01"

    def test_ing_002_empty_payload_dropped(self):
        """TC-ING-002: Datagram 0 byte bị drop, không crash."""
        send_udp(b"")
        time.sleep(0.5)
        # Receiver phải vẫn sống sau khi nhận payload rỗng
        # Kiểm tra bằng health endpoint
        # response = requests.get("http://localhost:8000/api/health")
        # assert response.status_code == 200

    def test_ing_003_single_byte_raw(self):
        """TC-ING-003: Payload 1 byte được lưu dạng RAW_UNKNOWN."""
        send_udp(b"X")
        time.sleep(0.5)
        # event lưu với format_status = RAW_UNKNOWN

    def test_ing_004_max_buffer_8192(self):
        """TC-ING-004: Payload 8192 bytes được lưu trọn vẹn."""
        header = b"<134>Nov 06 15:00:00 sw-test %SYS-5-CONFIG: "
        padding = b"A" * (8192 - len(header))
        payload = header + padding
        assert len(payload) == 8192
        send_udp(payload)
        time.sleep(0.5)
        # Kiểm tra raw_message có đúng 8192 ký tự

    def test_ing_014_burst_500_packets(self):
        """TC-ING-014: Bắn 500 gói trong 100ms, không mất gói."""
        for i in range(500):
            payload = f"<134>Nov 06 15:00:00 sw-burst-{i:03d} %SYS-5-CONFIG: Burst test".encode()
            send_udp(payload)
        time.sleep(3)
        # Kiểm tra 500 event trong DB
```

### 7.2 Script kiểm thử Correlation Engine (Dành cho BE3 — Nguyễn Duy Minh)

```python
# tests/test_correlation.py
"""
Test cases cho BE3 — Correlation Engine & Sliding Window.
Tập trung BVA-05 (threshold=5), BVA-06 (window=60s).
Chạy: pytest tests/test_correlation.py -v
"""
import time
import socket
import pytest

UDP_HOST = "127.0.0.1"
UDP_PORT = 5514

def send_flap_event(device: str, interface: str, state: str, timestamp_offset: int = 0):
    """Gửi 1 event Link Flap qua UDP."""
    ts = f"Nov 07 14:{timestamp_offset // 60:02d}:{timestamp_offset % 60:02d}"
    msg = f"<134>{ts} {device} %LINK-3-UPDOWN: Interface {interface}, changed state to {state}"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(msg.encode(), (UDP_HOST, UDP_PORT))
    sock.close()

class TestLinkFlapCorrelation:
    """TC-COR-001 → TC-COR-007: Kiểm thử Sliding Window & Link Flap Detection."""

    def test_cor_001_exact_threshold_5_events(self):
        """TC-COR-001: Đúng 5 lần flap trong 52s → Tạo Incident."""
        states = ["down", "up", "down", "up", "down"]
        offsets = [0, 12, 25, 38, 52]  # Tất cả trong 52s < 60s
        for state, offset in zip(states, offsets):
            send_flap_event("sw-test-01", "Gi0/1", state, offset)
            time.sleep(0.1)
        time.sleep(2)
        # TODO: Kiểm tra bảng incidents có đúng 1 row mới
        # response = requests.get("http://localhost:8000/api/v1/incidents?device=sw-test-01")
        # assert len(response.json()["data"]) == 1
        # incident = response.json()["data"][0]
        # assert incident["severity"] == "MAJOR"
        # assert incident["event_count"] == 5

    def test_cor_002_below_threshold_4_events(self):
        """TC-COR-002: Chỉ 4 lần flap → KHÔNG tạo Incident."""
        states = ["down", "up", "down", "up"]
        offsets = [0, 10, 20, 30]
        for state, offset in zip(states, offsets):
            send_flap_event("sw-test-02", "Gi0/2", state, offset)
            time.sleep(0.1)
        time.sleep(2)
        # Không có incident cho sw-test-02

    def test_cor_003_window_expired_61s(self):
        """TC-COR-003: 5 lần nhưng event thứ 5 ở giây 61 → KHÔNG tạo Incident."""
        offsets = [0, 15, 30, 45, 61]
        states = ["down", "up", "down", "up", "down"]
        for state, offset in zip(states, offsets):
            send_flap_event("sw-test-03", "Gi0/3", state, offset)
            time.sleep(0.1)
        time.sleep(2)
        # Cửa sổ trượt: tại t=61, event t=0 đã bị loại → chỉ còn 4 event

    def test_cor_005_different_interfaces_no_incident(self):
        """TC-COR-005: 3 flap trên Gi0/1 + 3 flap trên Gi0/2 → KHÔNG Incident."""
        for i in range(3):
            send_flap_event("sw-test-05", "Gi0/1", "down", i * 10)
        for i in range(3):
            send_flap_event("sw-test-05", "Gi0/2", "down", i * 10)
        time.sleep(2)
        # Grouping key (device, interface) phân biệt → mỗi nhóm chỉ có 3 < 5

    def test_cor_007_deduplication_20_events(self):
        """TC-COR-007: 20 flap liên tục → chỉ 1 Incident duy nhất."""
        for i in range(20):
            state = "down" if i % 2 == 0 else "up"
            send_flap_event("sw-test-07", "Gi0/7", state, i * 2)
            time.sleep(0.05)
        time.sleep(2)
        # Chỉ có 1 incident, event_count = 20
```

### 7.3 Kiểm thử Rule Validation — N42-17

Mã thực thi chuẩn nằm tại [tests/test_rules_config.py](../tests/test_rules_config.py).
Dùng loader thật và Pydantic thật, không dùng phác thảo `yaml.safe_load` hoặc assertion
trên dữ liệu sai để thay cho validation. Lệnh và mapping TC-RUL-001–005 ở §6.4.
TC-RUL-006/007 vẫn thuộc N42-38 và chưa chạy. Kết quả cụ thể nằm trong evidence theo
snapshot, không ghi số PASS cố định vào đặc tả này.

### 7.4 Script kiểm thử Security Scan (Dành cho QA — Ngô Châu Kiệt)

```python
# tests/test_security.py
"""
Test cases cho nhóm TC-SEC — An toàn Thông tin.
Chạy: pytest tests/test_security.py -v
"""
import subprocess
import re
import os
import pytest

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")

class TestSecurityScan:
    """TC-SEC-001 → TC-SEC-003: Kiểm thử An toàn Thông tin."""

    def test_sec_001_no_hardcoded_secrets(self):
        """TC-SEC-001: Không hardcode password/token trong source code."""
        result = subprocess.run(
            ["python", "tools/check_sensitive.py", "."],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        assert "AN TOÀN" in result.stdout, f"Phát hiện secret: {result.stdout}"

    def test_sec_002_only_rfc_ip_addresses(self):
        """TC-SEC-002: Tất cả IP là RFC 1918 hoặc RFC 5737."""
        public_ip_pattern = re.compile(
            r'\b(?!0\.0\.0\.0)(?!10\.)(?!192\.168\.)'
            r'(?!172\.(1[6-9]|2[0-9]|3[0-1])\.)'
            r'(?!203\.0\.113\.)(?!198\.51\.100\.)'
            r'(?!192\.0\.2\.)(?!127\.)'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        )
        violations = []
        for root, dirs, files in os.walk(PROJECT_ROOT):
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', 'venv'}]
            for f in files:
                if f.endswith(('.py', '.yaml', '.yml', '.json', '.md')):
                    path = os.path.join(root, f)
                    if 'check_sensitive' in f:
                        continue
                    with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
                        for i, line in enumerate(fh, 1):
                            if public_ip_pattern.search(line):
                                violations.append(f"{os.path.relpath(path)}:{i}: {line.strip()[:80]}")
        assert len(violations) == 0, f"IP Public thật phát hiện:\n" + "\n".join(violations)
```

### 7.5 Phác thảo kiểm thử tải danh định (chưa chạy; QA sở hữu test tooling)

```python
# tools/load_runner.py
"""
Script phát tải kiểm định hiệu năng và đo rớt gói UDP Socket.
Chạy: python tools/load_runner.py --rate 1000 --duration 600
"""
import socket
import time
import argparse
import sys
from datetime import datetime

def run_load_test(target_ip: str, target_port: int, target_rate: int, duration_sec: int):
    """
    Phát tải UDP đều đặn theo tốc độ chỉ định (msg/s) trong duration_sec giây.
    Gắn microsecond timestamp để đo đạc độ trễ P50, P99.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Nới rộng sender socket buffer tránh nghẽn tại máy phát
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4 * 1024 * 1024)

    total_sent = 0
    start_time = time.time()
    next_second = start_time + 1.0
    sent_in_current_second = 0

    print("=" * 65)
    print(f"N42 HIGH THROUGHPUT BENCHMARK RUNNER")
    print(f"Mục tiêu: {target_rate:,} msg/s | Thời lượng: {duration_sec}s | Tổng phát: {target_rate * duration_sec:,} pkts")
    print(f"Đích gửi: udp://{target_ip}:{target_port}")
    print("=" * 65)

    sample_templates = [
        "<134>{ts} sw-core-{idx:02d} %LINK-3-UPDOWN: Interface Gi0/{p}, changed state to down",
        "<134>{ts} sw-core-{idx:02d} %LINK-3-UPDOWN: Interface Gi0/{p}, changed state to up",
        "<189>{ts} fw-edge-{idx:02d} %%01FW/2/DENY: src=10.10.{idx}.{p} dst=203.0.113.10 proto=TCP action=deny",
        "<133>{ts} r-pe-{idx:02d} rpd[100]: BGP_PEER_DOWN: peer 10.10.0.{p} state changed to Idle",
    ]

    try:
        while time.time() - start_time < duration_sec:
            now = time.time()
            if now >= next_second:
                # Báo cáo tốc độ thực tế từng giây
                elapsed = int(now - start_time)
                print(f"[{elapsed:03d}s/{duration_sec}s] Đã gửi: {total_sent:,} gói | Tốc độ giây vừa qua: {sent_in_current_second:,} msg/s")
                sent_in_current_second = 0
                next_second += 1.0

            if sent_in_current_second < target_rate:
                # Sinh payload có timestamp microsecond
                ts_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                tmpl = sample_templates[total_sent % len(sample_templates)]
                msg = tmpl.format(ts=ts_str, idx=(total_sent % 20) + 1, p=(total_sent % 24) + 1)
                
                sock.sendto(msg.encode("utf-8"), (target_ip, target_port))
                total_sent += 1
                sent_in_current_second += 1
            else:
                # Nghỉ ngắn vi mô để giữ nhịp đều đặn không bị dồn cục
                sleep_rem = next_second - time.time()
                if sleep_rem > 0.001:
                    time.sleep(min(sleep_rem, 0.005))

    except KeyboardInterrupt:
        print("\n[!] Dừng khẩn cấp do người dùng ngắt tín hiệu.")
    finally:
        sock.close()

    total_duration = time.time() - start_time
    actual_rate = total_sent / total_duration if total_duration > 0 else 0
    print("-" * 65)
    print(f"KẾT QUẢ ĐO KIỂM PHÁT TẢI:")
    print(f"• Tổng thời gian: {total_duration:.2f} giây")
    print(f"• Tổng bản tin đã phát: {total_sent:,} gói")
    print(f"• Tốc độ phát trung bình: {actual_rate:,.2f} msg/s")
    print(f"• Đối soát: Hãy kiểm tra Health endpoint (/api/health) để xác nhận tỷ lệ rớt gói 0.00%.")
    print("=" * 65)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="N42 Benchmark Load Runner")
    parser.add_argument("--host", default="127.0.0.1", help="Target UDP host")
    parser.add_argument("--port", type=int, default=5514, help="Target UDP port")
    parser.add_argument("--rate", type=int, default=1000, help="Target rate (msg/s)")
    parser.add_argument("--duration", type=int, default=600, help="Duration in seconds (default 600s = 10m)")
    args = parser.parse_args()
    run_load_test(args.host, args.port, args.rate, args.duration)
```

### 7.6 Script kiểm thử Tự động Bộ Parser Đa Vendor (Dành cho BE2 — Phạm Tấn Thành)

```python
# tests/test_parsers.py
"""
Kiểm thử Unit Test bộ bóc tách và chuẩn hóa dữ liệu đa vendor.
Bao phủ: Cisco IOS, Cisco NX-OS, Huawei NE40E/S5700, Juniper Junos, Fortinet FortiOS.
Chạy: pytest tests/test_parsers.py -v
"""
import pytest

class TestMultiVendorParsers:
    """TC-PAR-001 → TC-PAR-012: Thẩm định chuẩn hóa Event Entity."""

    def test_par_001_cisco_catalyst_link_down(self):
        """TC-PAR-001: Bóc tách chính xác Cisco Catalyst LINK-3-UPDOWN."""
        raw = "<133>Nov 06 15:20:00 sw-core-uth %LINK-3-UPDOWN: Interface GigabitEthernet0/1, changed state to down"
        # Giả lập hàm parse_syslog(raw)
        # parsed = parse_syslog(raw)
        # assert parsed["vendor"] == "Cisco"
        # assert parsed["device_name"] == "sw-core-uth"
        # assert parsed["severity"] == "WARNING"
        # assert parsed["interface_name"] == "GigabitEthernet0/1"
        # assert parsed["link_state"] == "down"

    def test_par_004_huawei_power_supply_fail(self):
        """TC-PAR-004: Bóc tách Huawei NE40E Power Supply Failure."""
        raw = "<131>Nov 06 15:22:00 ne40e-bras-01 %%01DEVM/2/POWER_SUPPLY_FAILED: Power supply module 2 failed"
        # parsed = parse_syslog(raw)
        # assert parsed["vendor"] == "Huawei"
        # assert parsed["severity"] == "CRITICAL"
        # assert parsed["component"] == "Power supply module 2"

    def test_par_006_fortinet_traffic_deny(self):
        """TC-PAR-006: Bóc tách Key-Value format của Fortinet FortiGate."""
        raw = 'date=2026-11-06 time=15:24:00 devname="fg-edge-01" type="traffic" subtype="forward" action="deny" srcip=10.10.1.50 dstip=203.0.113.10 dstport=443 proto=6'
        # parsed = parse_syslog(raw)
        # assert parsed["vendor"] == "Fortinet"
        # assert parsed["src_ip"] == "10.10.1.50"
        # assert parsed["dst_ip"] == "203.0.113.10"
        # assert parsed["dst_port"] == 443
        # assert parsed["protocol"] == "TCP"

    def test_par_007_juniper_bgp_peer_down(self):
        """TC-PAR-007: Bóc tách Juniper MX960 BGP Session Drop."""
        raw = "<133>Nov 06 15:25:00 mx960-pe-01 rpd[1234]: BGP_PEER_DOWN: peer 10.10.0.2 (AS 65002) state changed from Established to Idle"
        # parsed = parse_syslog(raw)
        # assert parsed["vendor"] == "Juniper"
        # assert parsed["peer_ip"] == "10.10.0.2"
        # assert parsed["peer_as"] == 65002
        # assert parsed["new_state"] == "Idle"

    def test_par_010_garbage_bytes_fallback_raw(self):
        """TC-PAR-010: Chuỗi byte nhị phân không làm sập parser, lưu RAW."""
        raw = "\x00\x01\xfe\xff RANDOM_CORRUPTED_BYTES"
        # parsed = parse_syslog(raw)
        # assert parsed["format_status"] == "RAW_FALLBACK"
        # assert parsed["vendor"] == "UNKNOWN"
        # assert parsed["raw_message"] == raw
```

---

## 8. MÔ HÌNH DỮ LIỆU ĐỐI SOÁT CHUẨN (TEST FIXTURES & DATA DICTIONARY)

Các fixture bên dưới là dữ liệu tổng hợp minh họa để khởi tạo thiết kế test. Chỉ gọi là golden fixture sau khi QA quản lý version/hash và code owner xác nhận format cùng expected fields; không dùng như dữ liệu vendor-certified:

```text
================================================================================
BỘ DỮ LIỆU ĐỐI SOÁT CHUẨN (GOLDEN TEST FIXTURES) — DỰ ÁN N4.2
================================================================================

[FIXTURE-01: CISCO CATALYST LINK FLAPPING]
<134>2026-11-06T15:00:01+07:00 sw-core-uth-01 %LINK-3-UPDOWN: Interface GigabitEthernet0/1, changed state to down
<134>2026-11-06T15:00:11+07:00 sw-core-uth-01 %LINK-3-UPDOWN: Interface GigabitEthernet0/1, changed state to up
<134>2026-11-06T15:00:21+07:00 sw-core-uth-01 %LINK-3-UPDOWN: Interface GigabitEthernet0/1, changed state to down
<134>2026-11-06T15:00:31+07:00 sw-core-uth-01 %LINK-3-UPDOWN: Interface GigabitEthernet0/1, changed state to up
<134>2026-11-06T15:00:41+07:00 sw-core-uth-01 %LINK-3-UPDOWN: Interface GigabitEthernet0/1, changed state to down

[FIXTURE-02: HUAWEI NE40E POWER REDUNDANCY FAILURE]
<131>2026-11-06T15:01:00+07:00 ne40e-bras-01 %%01DEVM/2/POWER_SUPPLY_FAILED(l): Power supply module 2 was failed.

[FIXTURE-03: FORTINET FORTIGATE SYN FLOOD ATTACK STREAM]
date=2026-11-06 time=15:02:00 devname="fg-edge-01" devid="FG100F123456" type="traffic" subtype="forward" level="warning" action="deny" srcip=10.10.1.50 dstip=203.0.113.10 srcport=49152 dstport=80 proto=6

[FIXTURE-04: JUNIPER MX960 BGP PEER SESSION TEARDOWN]
<133>2026-11-06T15:03:00+07:00 mx960-pe-01 rpd[2841]: BGP_PEER_DOWN: peer 10.10.0.2 (AS 65002) state changed from Established to Idle

[FIXTURE-05: CISCO NEXUS DUPLICATE ARP DETECTION]
<132>2026-11-06T15:04:00+07:00 nexus-dc-01 %IP-4-DUPADDR: Duplicate address 10.10.5.100 on Vlan100, sourced by aabb.ccdd.1234
```

---

## 9. QUY TRÌNH QUẢN LÝ LỖI & TIÊU CHÍ NGHIỆM THU (SIGN-OFF)

### 9.1 Phân loại Mức độ Nghiêm trọng của Lỗi (Defect Severity)
- **Blocker / S1:** Hệ thống bị crash, rớt gói UDP ở tải < 1.000 msg/s, rò rỉ secret hoặc sai lệch dữ liệu CSDL.
- **Critical / S2:** Không kích hoạt Incident khi đủ 5 lần flap, hoặc tạo nhầm Incident khi chỉ có 4 lần flap.
- **Major / S3:** Parse sai một trường phụ trong Syslog, độ trễ $P_{99}$ vượt 200ms trong điều kiện thường.
- **Minor / S4:** Sai lỗi chính tả trên UI Dashboard, hiển thị lệch vài pixel.

### 9.2 Tiêu chí Đóng bản Kiểm thử (Exit & Sign-off Criteria)
- 100% các Test Case mức **P1 (CRITICAL)** và **P2 (HIGH)** phải đạt kết quả **PASS**.
- Không còn bất kỳ lỗi nào ở mức **S1** và **S2** còn mở (Zero Open Blockers).
- Tỷ lệ rớt gói UDP ở bài test danh định 1.000 msg/s đạt chính xác **$0.00\%$**.
- Toàn bộ code test tự động phải được đẩy lên GitHub và chạy thành công trên CI/CD GitHub Actions.

---

## 10. MA TRẬN TRUY VẾT YÊU CẦU ĐẾN CA KIỂM THỬ (TRACEABILITY MATRIX)

Ma trận dưới đây là ánh xạ kế hoạch giữa FR/NFR, Jira và ca kiểm thử. Đây chưa phải bằng chứng bao phủ tự động 100%; xem `REQUIREMENTS_TRACEABILITY_MATRIX.md` để biết evidence cần thu và các gap backend.

| Mã Yêu cầu | Tên Yêu cầu Nghiệp vụ / Kỹ thuật | Thẻ Jira | Các Ca Kiểm thử Đại diện (Test Cases) | Phụ trách Chính |
| :---: | :--- | :---: | :--- | :---: |
| **FR-01** | Nhận diện Syslog UDP Socket 5514 | [N42-13](https://nhutp2945-1793259952237.atlassian.net/browse/N42-13), [N42-32](https://nhutp2945-1793259952237.atlassian.net/browse/N42-32) | TC-ING-001, 002, 003, 004, 005, 006, 014, 015 | Long (BE1) |
| **FR-02** | REST API Ingest tiếp nhận bản tin | [N42-14](https://nhutp2945-1793259952237.atlassian.net/browse/N42-14) | TC-ING-007, 008, 009, 010 | Long (BE1) |
| **FR-03** | Batch Log File Import từ ổ đĩa | [N42-22](https://nhutp2945-1793259952237.atlassian.net/browse/N42-22) | TC-ING-011, 012, 013, TC-SEC-006 | Long (BE1) |
| **FR-04** | Parser chuẩn hóa đa vendor Cisco/Huawei/Juniper/Fortinet | [N42-15](https://nhutp2945-1793259952237.atlassian.net/browse/N42-15), [N42-23](https://nhutp2945-1793259952237.atlassian.net/browse/N42-23), [N42-24](https://nhutp2945-1793259952237.atlassian.net/browse/N42-24), [N42-25](https://nhutp2945-1793259952237.atlassian.net/browse/N42-25) | TC-PAR-001, 002, 003, 004, 005, 006, 007, 008, 009, 012 | Thành (BE2) |
| **FR-05** | Fallback RAW cho bản tin dị dạng/hỏng | [N42-15](https://nhutp2945-1793259952237.atlassian.net/browse/N42-15) | TC-PAR-010, 011, TC-ING-003 | Thành (BE2) |
| **FR-06** | Lưu trữ sự kiện bền vững vào PostgreSQL | [N42-16](https://nhutp2945-1793259952237.atlassian.net/browse/N42-16), [N42-30](https://nhutp2945-1793259952237.atlassian.net/browse/N42-30), [N42-31](https://nhutp2945-1793259952237.atlassian.net/browse/N42-31), [N42-55](https://nhutp2945-1793259952237.atlassian.net/browse/N42-55) | TC-DB-001, 002, 003, TC-INT-001, 003 | Thành (BE2) |
| **FR-07** | Tìm kiếm, lọc và phân trang sự kiện | [N42-28](https://nhutp2945-1793259952237.atlassian.net/browse/N42-28), [N42-34](https://nhutp2945-1793259952237.atlassian.net/browse/N42-34), [N42-67](https://nhutp2945-1793259952237.atlassian.net/browse/N42-67) | TC-UI-002, 003, TC-SEC-004, TC-PERF-008 | Thành / Huy |
| **FR-08** | Thống kê số lượng sự kiện theo khung giờ/thiết bị | [N42-39](https://nhutp2945-1793259952237.atlassian.net/browse/N42-39), [N42-41](https://nhutp2945-1793259952237.atlassian.net/browse/N42-41) | TC-UI-001, TC-DB-003 | Thành / Huy |
| **FR-09** | Tương quan sự cố đa cảnh báo (Correlation Engine) | [N42-18](https://nhutp2945-1793259952237.atlassian.net/browse/N42-18), [N42-37](https://nhutp2945-1793259952237.atlassian.net/browse/N42-37), [N42-44](https://nhutp2945-1793259952237.atlassian.net/browse/N42-44), [N42-45](https://nhutp2945-1793259952237.atlassian.net/browse/N42-45), [N42-48](https://nhutp2945-1793259952237.atlassian.net/browse/N42-48), [N42-64](https://nhutp2945-1793259952237.atlassian.net/browse/N42-64), [N42-65](https://nhutp2945-1793259952237.atlassian.net/browse/N42-65), [N42-66](https://nhutp2945-1793259952237.atlassian.net/browse/N42-66) | TC-COR-001, 002, 003, 004, 005, 006, 007, 008, 009, 010, 011 | Minh (BE3) |
| **FR-10** | Quản lý vòng đời sự cố (Incident Lifecycle & FSM) | [N42-33](https://nhutp2945-1793259952237.atlassian.net/browse/N42-33), [N42-44](https://nhutp2945-1793259952237.atlassian.net/browse/N42-44), [N42-46](https://nhutp2945-1793259952237.atlassian.net/browse/N42-46), [N42-47](https://nhutp2945-1793259952237.atlassian.net/browse/N42-47) | TC-COR-007, 012, TC-INT-002, TC-DB-004 | Minh (BE3) |
| **FR-11** | Dashboard hiển thị cảnh báo thời gian thực | [N42-20](https://nhutp2945-1793259952237.atlassian.net/browse/N42-20), [N42-28](https://nhutp2945-1793259952237.atlassian.net/browse/N42-28), [N42-34](https://nhutp2945-1793259952237.atlassian.net/browse/N42-34), [N42-41](https://nhutp2945-1793259952237.atlassian.net/browse/N42-41), [N42-47](https://nhutp2945-1793259952237.atlassian.net/browse/N42-47), [N42-53](https://nhutp2945-1793259952237.atlassian.net/browse/N42-53) | TC-UI-001–006, TC-INT-002, TC-SEC-005 | Huy (FE) |
| **FR-12** | Health check & giám sát metrics hệ thống | [N42-13](https://nhutp2945-1793259952237.atlassian.net/browse/N42-13) | TC-HLT-001, 002, 003, 004 | BE1 / QA theo ticket |
| **FR-13** | Replay deterministic theo scenario/seed | [N42-11](https://nhutp2945-1793259952237.atlassian.net/browse/N42-11), [N42-54](https://nhutp2945-1793259952237.atlassian.net/browse/N42-54) | TC-REP-001 | Kiệt (QA) |
| **FR-14** | Export theo filter, escaping và giới hạn | [N42-63](https://nhutp2945-1793259952237.atlassian.net/browse/N42-63) | TC-EXP-001 | FE / BE liên quan |
| **FR-15** | Thẩm định/startup N17; Hot-reload N38 (chờ QA/TL nghiệm thu) | [N42-17](https://nhutp2945-1793259952237.atlassian.net/browse/N42-17), [N42-38](https://nhutp2945-1793259952237.atlassian.net/browse/N42-38) | TC-RUL-001–005, 008–012 (N17); TC-RUL-006/007 (N38) | Minh (BE3) |
| **NFR-01** | Tải danh định $\ge 1.000$ msg/s liên tục | [N42-57](https://nhutp2945-1793259952237.atlassian.net/browse/N42-57) | TC-PERF-001 (10p), TC-PERF-002 (1h), TC-PERF-004 (1.500 msg/s) | Kiệt (QA) |
| **NFR-02** | Độ trễ xử lý $P_{50} < 50$ms, $P_{99} < 200$ms | [N42-52](https://nhutp2945-1793259952237.atlassian.net/browse/N42-52), [N42-57](https://nhutp2945-1793259952237.atlassian.net/browse/N42-57) | TC-PERF-003 | Kiệt (QA) |
| **NFR-03** | Tỷ lệ rớt gói UDP Socket đạt tuyệt đối $0.00\%$ | [N42-32](https://nhutp2945-1793259952237.atlassian.net/browse/N42-32), [N42-57](https://nhutp2945-1793259952237.atlassian.net/browse/N42-57) | TC-ING-014, TC-PERF-001, 002 | Long / Kiệt |
| **NFR-04** | Tiêu thụ tài nguyên CPU $\le 60\%$, RAM $\le 1.5$ GB | [N42-57](https://nhutp2945-1793259952237.atlassian.net/browse/N42-57), [N42-58](https://nhutp2945-1793259952237.atlassian.net/browse/N42-58) | TC-PERF-001, 002, 005 (Memory Leak) | QA + BE owner theo metric |
| **NFR-05** | Truy vấn 1 triệu bản ghi dưới 2 giây | [N42-23](https://nhutp2945-1793259952237.atlassian.net/browse/N42-23), [N42-24](https://nhutp2945-1793259952237.atlassian.net/browse/N42-24), [N42-25](https://nhutp2945-1793259952237.atlassian.net/browse/N42-25), [N42-30](https://nhutp2945-1793259952237.atlassian.net/browse/N42-30), [N42-67](https://nhutp2945-1793259952237.atlassian.net/browse/N42-67) | TC-PERF-008, TC-DB-003 | Thành / Kiệt |
| **NFR-06** | 100% dữ liệu giả lập, không lộ Secret / IP thật | [N42-10](https://nhutp2945-1793259952237.atlassian.net/browse/N42-10), [N42-50](https://nhutp2945-1793259952237.atlassian.net/browse/N42-50), [N42-60](https://nhutp2945-1793259952237.atlassian.net/browse/N42-60) | TC-SEC-001, 002, 003, TC-HLT-003 | QA + code owners; TL điều phối hồ sơ |
| **NFR-07** | Cài đặt và phục hồi theo handover target | [N42-55](https://nhutp2945-1793259952237.atlassian.net/browse/N42-55), [N42-59](https://nhutp2945-1793259952237.atlassian.net/browse/N42-59), [N42-61](https://nhutp2945-1793259952237.atlassian.net/browse/N42-61) | TC-INT-003, TC-PERF-007, TC-OPS-001, 003 | QA / BE1 / BE2 |
| **NFR-08** | Bounded memory và policy khi saturation | [N42-13](https://nhutp2945-1793259952237.atlassian.net/browse/N42-13), [N42-14](https://nhutp2945-1793259952237.atlassian.net/browse/N42-14), [N42-31](https://nhutp2945-1793259952237.atlassian.net/browse/N42-31), [N42-32](https://nhutp2945-1793259952237.atlassian.net/browse/N42-32), [N42-57](https://nhutp2945-1793259952237.atlassian.net/browse/N42-57) | TC-ING-014, TC-PERF-004, 006, TC-OPS-003 | BE1 / BE2 / QA |

---

## 11. BẢNG GHI NHẬN KẾT QUẢ KIỂM THỬ THỰC ĐỊA (TEST RUN EXECUTION SHEET)

Đây là mẫu ghi nhận; không điền sẵn kết quả khi chưa có log/artifact kiểm chứng. Các test case trong mục 6 là **đặc tả/kế hoạch**, không tự động đồng nghĩa đã chạy. Trạng thái mặc định là `NOT RUN`.

| Mã ca | Commit SHA | Thời gian | Môi trường/phiên bản | Fixture/version | Expected | Actual + link artifact | Status | Defect | Người chạy |
|---|---|---|---|---|---|---|---|---|---|
| TC-________ | __________ | __________ | __________ | __________ | __________ | __________ | NOT RUN | — | __________ |

**Trạng thái hợp lệ:** `NOT RUN`, `BLOCKED` (nêu lý do/hợp đồng còn thiếu), `PASS` (có evidence), `FAIL` (có evidence và defect ID). Không dùng `PASS` cho kết quả dự kiến hay ví dụ minh họa.

---

## 12. PHÊ DUYỆT BẢN ĐẶC TẢ KIỂM THỬ (SIGN-OFF & APPROVAL)

Tài liệu này là bản đặc tả làm việc. Chỉ ghi chữ ký và ngày sau khi người có thẩm quyền thực sự rà soát/phê duyệt; bảng dưới không khẳng định đã được ký.

| Vai trò phê duyệt | Họ và tên | Chữ ký điện tử | Ngày ký |
| :--- | :--- | :---: | :---: |
| Project Manager / Team Lead | __________ | Chờ phê duyệt | __________ |
| QA Lead | __________ | Chờ phê duyệt | __________ |
| Đại diện BE1 | __________ | Chờ rà soát | __________ |
| Đại diện BE2 | __________ | Chờ rà soát | __________ |
| Đại diện BE3 | __________ | Chờ rà soát | __________ |


## Startup integration — 12/11/2026

FastAPI lifespan nạp rules.yaml bằng loader thật trước khi nhận request; lưu tại
app.state.rule_configuration. Invalid config làm startup thất bại; không có API mới,
engine hoặc reload. TC-RUL-012: startup hợp lệ nạp3mẫu tắt/version0.1.1, startup invalid
catalog bị ValidationError. Test thực tế tests/test_rule_startup.py. Code owner BE3.
Đây là tích hợp M5 theo ủy quyền triển khai, không suy field producer đã được phê duyệt.


B? sung N42-10 (13/11/2026), TC-OPS-002 / AC-07/08: CI-09?10, JK-01?03, OPS-04?05 v? input/expected t?i [k? ho?ch n?ng c?p](N42-10_UPGRADE_PLAN.md). Tr?ng th?i th?c thi ghi ri?ng theo revision; ??c t? kh?ng ph?i PASS.
