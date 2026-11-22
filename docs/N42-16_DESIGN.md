# N42-16 - Thiết kế Schema TimescaleDB, Index và Đề xuất Chính sách Retention / Compression

- **Phiên bản:** 1.0, Ngày 12/11/2026.
- **Trạng thái:** DRAFT / PROPOSED FOR REVIEW (Chờ Team Leader và QA Lead phê duyệt).
- **Kỹ sư phụ trách:** Phạm Tấn Thành (Backend Engineer 2 - BE2).
- **Thẻ Jira:** [N42-16](https://nhutp2945-1793259952237.atlassian.net/browse/N42-16).
- **Truy vết yêu cầu:** FR-06 (Lưu trữ và lập chỉ mục chuỗi thời gian), AC-07 (Khởi tạo database tự động qua Docker Compose), TC-DB-001..004 (Đặc tả kiểm thử CSDL).
- **Tài liệu căn cứ:** [TDD](TECHNICAL_DESIGN_DOCUMENT.md), [Thiết kế dữ liệu và API](DATA_AND_API_DESIGN.md), [Kiến trúc hệ thống](ARCHITECTURE_DESIGN.md), [Quyết định kỹ thuật](DECISIONS.md) (D-02, D-05).

---

## 1. Phạm vi kỹ thuật

Thiết kế kiến trúc cơ sở dữ liệu chuỗi thời gian (Time-Series Database) cho Hệ thống thu thập và phân tích cảnh báo mạng viễn thông N4.2:
1. Định nghĩa lược đồ bảng dữ liệu sự kiện chuẩn hóa `alert_events` tương thích 100% với model Pydantic v2 `AlertEvent` (đã hoàn thành ở N42-15).
2. Thiết lập Hypertable TimescaleDB với khóa phân vùng thời gian `event_timestamp` và chu kỳ phân đoạn chunk 1 ngày (`INTERVAL '1 day'`) theo Quyết định D-02.
3. Thiết kế hệ thống chỉ mục B-tree đa chiều tối ưu hóa cho các truy vấn thời gian thực và tổng hợp thống kê.
4. Thiết kế lược đồ bảng sự cố gốc `incidents` và bảng quan hệ liên kết `incident_events` phục vụ Module tương quan M6.
5. Soạn thảo đề xuất định lượng về chính sách Nén dữ liệu (Native Compression) và chính sách Lưu trữ (Retention Policy) phù hợp với tải trọng 1.000 msg/s.

---

## 2. Chi tiết Lược đồ CSDL (DDL Specification)

Toàn bộ kịch bản DDL được đóng gói trong tệp [`docker/init-db.sql`](../docker/init-db.sql):

### 2.1. Bảng `alert_events` (Hypertable)
- Lưu trữ toàn bộ các bản tin cảnh báo viễn thông sau khi chuẩn hóa bởi Module M2.
- **Quy tắc TimescaleDB:** Khóa chính bắt buộc phải là khóa composite chứa cột phân vùng thời gian `(id, event_timestamp)`.

| Cột | Kiểu dữ liệu | Ràng buộc | Ý nghĩa nghiệp vụ |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `NOT NULL` | Định danh sự kiện duy nhất |
| `event_timestamp` | `TIMESTAMPTZ` | `NOT NULL` | Thời điểm xảy ra sự kiện (Khóa phân vùng TimescaleDB, chuẩn UTC) |
| `received_at` | `TIMESTAMPTZ` | `NOT NULL` | Thời điểm hệ thống tiếp nhận bản tin |
| `timestamp_inferred` | `BOOLEAN` | `DEFAULT TRUE` | Đánh dấu thời gian có được suy diễn (RFC 3164) hay không |
| `source_ip` | `VARCHAR(45)` | `NOT NULL` | Địa chỉ IP nguồn (hỗ trợ cả IPv4 và IPv6) |
| `hostname` | `VARCHAR(255)` | `NOT NULL` | Tên thiết bị mạng phát sinh cảnh báo |
| `facility` | `SMALLINT` | `CHECK (0..23)` | Phân loại dịch vụ theo chuẩn RFC 5424 |
| `severity` | `SMALLINT` | `CHECK (0..7)` | Mức độ nghiêm trọng theo chuẩn RFC 5424 (0=Emergency..7=Debug) |
| `vendor` | `VARCHAR(30)` | `NOT NULL` | Hãng thiết bị (cisco, huawei, fortinet, linux, unknown) |
| `program` | `VARCHAR(100)` | `NULL` | Tên tiến trình/tiện ích phát sinh log |
| `mnemonic` | `VARCHAR(100)` | `NULL` | Mã định danh cảnh báo của hãng |
| `category` | `VARCHAR(50)` | `DEFAULT 'unknown'` | Phân loại nghiệp vụ (chờ mapping M5) |
| `message` | `TEXT` | `NOT NULL` | Nội dung thông điệp cảnh báo đã bóc tách |
| `raw_payload` | `TEXT` | `NOT NULL` | Bản tin syslog thô ban đầu |
| `parse_status` | `VARCHAR(20)` | `DEFAULT 'parsed'` | Trạng thái bóc tách (`parsed` hoặc `fallback`) |
| `parse_error` | `VARCHAR(50)` | `NULL` | Mã lỗi nếu rơi vào trường hợp fallback |
| `schema_version` | `VARCHAR(10)` | `DEFAULT '1.0'` | Phiên bản cấu trúc schema |

#### 2.1.1. Luận chứng Kỹ thuật về Khóa chính và Bộ định vị bản ghi (Record Locator Strategy)
Để giải quyết dứt điểm phản biện review về việc sử dụng `(id, event_timestamp)` thay vì `id + received_at`:

1. **Ràng buộc bất biến của kiến trúc TimescaleDB (Invariance Rule):**
   - Theo Quyết định **D-02**, bảng `alert_events` bắt buộc phải là một Hypertable phân vùng theo thời gian thực của sự kiện (`event_timestamp`) với chu kỳ chunk 1 ngày (`INTERVAL '1 day'`).
   - Theo đặc tả động cơ TimescaleDB / PostgreSQL: Mọi ràng buộc `PRIMARY KEY` hoặc `UNIQUE` trên một Hypertable **bắt buộc phải bao gồm cột phân vùng thời gian** (`partitioning column`).
   - Nếu áp dụng khóa chính `(id, received_at)` trong khi phân vùng theo `event_timestamp`, TimescaleDB sẽ từ chối tạo Hypertable với lỗi: `ERROR: cannot create a unique index without the column "event_timestamp" (used in partitioning)`. Do đó, `PRIMARY KEY (id, event_timestamp)` là phương án kỹ thuật hợp lệ duy nhất.

2. **Ý nghĩa nghiệp vụ viễn thông & Phân tích nguyên nhân gốc (RCA M6):**
   - Cảnh báo mạng viễn thông gắn liền với thời điểm vật lý xuất hiện sự cố trên phần cứng (`event_timestamp`). Đây là mốc thời gian khách quan để xác định chuỗi nhân quả (causality) giữa các cảnh báo (ví dụ Router báo Link Down lúc $T_0$, kéo theo hàng loạt BGP Neighbor Down tại $T_0 + 50ms$).
   - `received_at` chỉ là mốc nhận tin tại cổng Ingest, bị phụ thuộc vào độ trễ đường truyền mạng và độ sâu hàng đợi, có thể bị đến muộn hoặc xáo trộn (out-of-order), không thể đại diện cho danh tính vật lý của sự kiện.

3. **Chiến lược Định vị bản ghi (Locator) & Hiệu năng EXPLAIN:**
   - **Tuple Locator `(id, event_timestamp)`:**
     - Kịch bản API tối ưu: `GET /api/v1/events/{id}?event_timestamp={ts}`.
     - TimescaleDB thực thi cơ chế **Chunk Pruning**: Bỏ qua toàn bộ các chunk không liên quan, định tuyến thẳng tới duy nhất 1 chunk chứa `event_timestamp`, sau đó thực hiện B-tree lookup trên `pk_alert_events`.
     - Kế hoạch truy vấn: `Index Scan using pk_alert_events on _hyper_1_chunk (cost=0.15..8.17 rows=1)`.
   - **Single ID Locator `id`:**
     - Kịch bản API RESTful chuẩn: `GET /api/v1/events/{id}`.
     - Vì `id` là **cột dẫn đầu (leading column)** trong chỉ mục B-tree tổ hợp `pk_alert_events (id, event_timestamp)`, hệ thống PostgreSQL thực hiện quét trực tiếp trên chỉ mục khóa chính tại các chunk mà **hoàn toàn không cần quét toàn bảng (Full Table Scan / Seq Scan)**.
   - **Đồng bộ với hợp đồng N42-62:**
     - Ticket N42-62 thiết kế cursor phân trang ổn định dựa trên cặp `(event_timestamp, id)`.
     - Lược đồ DDL và cấu trúc khóa chính `(id, event_timestamp)` đồng bộ 100% với định dạng con trỏ cursor của API N42-62.

### 2.2. Bảng `incidents` (Module M6)
- Lưu vết các sự cố mạng sau khi chạy thuật toán tương quan gom nhóm và phân tích nguyên nhân gốc (RCA).
- Bao gồm các trường: `id`, `incident_name`, `rule_key`, `hostname`, `root_cause_type`, `root_cause_alert_id`, `severity` (0-7), `status` (`OPEN`, `INVESTIGATING`, `RESOLVED`, `CLOSED`), `first_seen`, `last_seen`, `event_count`, `summary`, `evidence` (JSONB).

### 2.3. Bảng `incident_events` (Liên kết Sự cố - Cảnh báo)
- Quan hệ nhiều-nhiều liên kết các cảnh báo thành phần cấu thành một sự cố gốc:
  - `incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE`
  - `alert_id UUID NOT NULL`
  - `event_timestamp TIMESTAMPTZ NOT NULL`
  - Khóa chính composite: `PRIMARY KEY (incident_id, alert_id, event_timestamp)`.

---

## 3. Chiến lược Chỉ mục B-tree Tối ưu hóa Truy vấn

Để đáp ứng tiêu chí truy vấn dưới 2 giây trên tập dữ liệu 1.000.000 bản tin (theo TDD v2 Mục 2.2):

1. **`idx_alerts_ts_sev` `(event_timestamp DESC, severity)`**:
   - Tối ưu cho API truy vấn danh sách cảnh báo thời gian thực có lọc theo mức độ nghiêm trọng (ví dụ: lấy các cảnh báo Critical/Error trong 1 giờ qua).
2. **`idx_alerts_host_ts` `(hostname, event_timestamp DESC)`**:
   - Tối ưu cho trang chi tiết thiết bị, hỗ trợ tra cứu nhanh lịch sử cảnh báo của một Router/Switch cụ thể.
3. **`idx_alerts_ts_host_sev` `(event_timestamp DESC, hostname, severity)`**:
   - Chỉ mục tổ hợp theo **Quyết định D-02** phục vụ truy vấn lọc đa chiều trên Dashboard.
4. **`idx_alerts_vendor_ts` `(vendor, event_timestamp DESC)`**:
   - Phục vụ báo cáo phân tích tỷ trọng cảnh báo theo nhà sản xuất (Cisco, Huawei, Fortinet).
5. **Chỉ mục sự cố M6**:
   - `idx_incidents_status_last_seen ON incidents (status, last_seen DESC)`: Phục vụ hiển thị bảng sự cố đang hoạt động (Active Incidents).
   - `idx_incidents_host_last_seen ON incidents (hostname, last_seen DESC)`: Phục vụ tra cứu sự cố theo thiết bị mạng.

---

## 4. Đề xuất Chính sách Chunk, Nén (Compression) & Lưu trữ (Retention)

### 4.1. Phân tích Tải trọng & Dung lượng Lưu trữ
- **Tải trọng mục tiêu:** $\ge 1.000\text{ msg/s}$ (theo AC-01/AC-08).
- **Số lượng bản tin phát sinh:**
  - Trong 1 giờ: $1.000 \times 3.600 = 3.600.000\text{ bản tin}$.
  - Trong 1 ngày (24 giờ): $3.600.000 \times 24 = 86.400.000\text{ bản tin/ngày}$.
- **Ước tính dung lượng đĩa:**
  - Kích thước trung bình mỗi dòng bản tin trong PostgreSQL: $\approx 300 - 350\text{ bytes}$ (bao gồm cả index).
  - Dung lượng thô (Uncompressed) mỗi ngày: $86.400.000 \times 300\text{ bytes} \approx 25,92\text{ GB/ngày}$.
  - Trong 30 ngày: $\approx 777\text{ GB}$.

### 4.2. Khuyến nghị Cấu hình Chunk Interval
- **Khuyến nghị:** `chunk_time_interval => INTERVAL '1 day'`.
- **Cơ sở kỹ thuật:** Mỗi chunk chứa dữ liệu của 1 ngày ($\approx 25\text{ GB}$), hoàn toàn nằm gọn trong bộ nhớ đệm (RAM) của server, giúp tối ưu hóa bộ nhớ đệm index B-tree và tránh hiện tượng thrashing đĩa cứng.

### 4.3. Đề xuất Chính sách Nén (TimescaleDB Native Compression - Chờ duyệt)
- **Trạng thái:** ĐỀ XUẤT CHỜ DUYỆT (Đã gỡ khỏi bootstrap DDL theo review ngày 22/11/2026).
- **Cấu hình mẫu tham chiếu:**
  ```sql
  -- Lệnh áp dụng thủ công khi đưa vào vận hành:
  -- ALTER TABLE alert_events SET (
  --     timescaledb.compress,
  --     timescaledb.compress_segmentby = 'hostname, vendor',
  --     timescaledb.compress_orderby = 'event_timestamp DESC'
  -- );
  -- SELECT add_compression_policy('alert_events', INTERVAL '7 days', if_not_exists => TRUE);
  ```
- **Lợi ích dự kiến:**
  - Dữ liệu trong vòng 7 ngày gần nhất (**Hot Data**) được giữ nguyên ở dạng không nén, đảm bảo hiệu năng ghi $\ge 1.000\text{ msg/s}$ và truy vấn thời gian thực có độ trễ thấp nhất.
  - Các chunk cũ hơn 7 ngày (**Warm Data**) tự động được nén cột (columnar compression), đạt tỷ lệ nén từ **70% đến 85%**.
  - Dung lượng 1 ngày sau nén chỉ còn $\approx 3,8 - 6,5\text{ GB}$ (tiết kiệm hơn $20\text{ GB/ngày}$).

### 4.4. Đề xuất Chính sách Lưu trữ (Data Retention Policy - Chờ duyệt)
- **Trạng thái:** ĐỀ XUẤT CHỜ DUYỆT (Đã gỡ khỏi bootstrap DDL theo review ngày 22/11/2026).
- **Cấu hình mẫu tham chiếu:**
  ```sql
  -- Lệnh áp dụng thủ công khi đưa vào vận hành:
  -- SELECT add_retention_policy('alert_events', INTERVAL '30 days', if_not_exists => TRUE);
  ```
- **Lưu ý an toàn:**
  - Tuyệt đối không tự động kích hoạt `add_retention_policy` khi bootstrap container để tránh việc background worker tự động drop chunk dữ liệu lab/test.
  - Việc kích hoạt sẽ do DBA thực hiện qua migration riêng sau khi có văn bản phê duyệt chính thức (30 ngày cho Lab / 90 ngày cho Production kèm quy trình backup).

---

## 5. Kết quả Kiểm thử & Nghiệm thu (TC-DB-001..005)

Toàn bộ các tiêu chí kiểm thử đã được tự động hóa tại [`tests/test_database_schema.py`](../tests/test_database_schema.py) (12 tests pass 100%):

1. **TC-DB-001 (Primary Key Integrity):** Xác thực khóa chính composite `(id, event_timestamp)` ngăn chặn trùng lặp dữ liệu theo đúng yêu cầu phân vùng của TimescaleDB Hypertable.
2. **TC-DB-002 (NOT NULL Constraints):** Xác thực bắt buộc đối với các trường trọng yếu (`event_timestamp`, `received_at`, `source_ip`, `hostname`, `facility`, `severity`, `vendor`, `message`, `raw_payload`).
3. **TC-DB-003 (CHECK Constraints & Index Query Plan):** Kiểm chứng giá trị biên của `facility` (0–23), `severity` (0–7), `incidents.status` ('OPEN', 'INVESTIGATING', 'RESOLVED', 'CLOSED'); EXPLAIN QUERY PLAN chứng minh query engine sử dụng B-tree index `idx_alerts_host_ts`.
4. **TC-DB-004 (Referential Integrity & Cascade):** Kiểm chứng xóa Incident sẽ kích hoạt `ON DELETE CASCADE` dọn dẹp quan hệ trong `incident_events` mà vẫn bảo toàn 100% các bản ghi sự kiện gốc trong `alert_events`.
5. **TC-DB-005 (Record Locator & EXPLAIN Query Plan):** Kiểm chứng toàn diện chiến lược định vị bản ghi:
   - Truy vấn locator đầy đủ `(id, event_timestamp)` tối ưu hóa chunk pruning và sử dụng `pk_alert_events`.
   - Truy vấn single ID `id` (API `GET /api/v1/events/{id}`) tận dụng leading column của B-tree index `pk_alert_events` mà không cần Full Table Scan.
   - Đối soát dữ liệu (reconciliation) đảm bảo trả về chính xác 1 bản ghi duy nhất, truy vấn sai timestamp trả về rỗng.
6. **Không kích hoạt Retention/Compression tại Bootstrap:** Khẳng định 100% không có lệnh `add_retention_policy` hoặc `add_compression_policy` nào chạy chủ động trong DDL khởi tạo.
7. **Model Parity:** Kiểm chứng 100% khớp trường giữa Pydantic model `AlertEvent` và cấu trúc DDL PostgreSQL.
8. **Bảo mật & Chất lượng mã nguồn:** Quét `tools/check_sensitive.py` không rò rỉ credential hay IP thật; Flake8 & Black đạt chuẩn PEP 8.


