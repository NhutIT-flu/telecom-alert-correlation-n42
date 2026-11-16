# N42-62 - Đặc tả Thiết kế Hợp đồng API và Sự kiện v1.0 (API & Event Contract v1)

- **Phiên bản:** 1.0, Ngày 16/11/2026.
- **Trạng thái:** PROPOSED FOR CROSS-MODULE REVIEW (Đề xuất thẩm định liên module).
- **Kỹ sư phụ trách:** Phạm Tấn Thành (Backend Engineer 2 - BE2).
- **Thẻ Jira:** [N42-62](https://nhutp2945-1793259952237.atlassian.net/browse/N42-62).
- **Khối công việc:** Epic CHUANHOA (M3, M4).
- **Các thẻ liên quan:**
  - **Blocks (Chặn):** [N42-14](https://nhutp2945-1793259952237.atlassian.net/browse/N42-14) (BE1 Ingest REST API), [N42-67](https://nhutp2945-1793259952237.atlassian.net/browse/N42-67) (BE2 Query API).
  - **Downstream consumers:** [N42-34](https://nhutp2945-1793259952237.atlassian.net/browse/N42-34) (FE Dashboard Events Table), [N42-22](https://nhutp2945-1793259952237.atlassian.net/browse/N42-22) (BE1 File Import), [N42-18](https://nhutp2945-1793259952237.atlassian.net/browse/N42-18) (BE3 Correlation Engine).
- **Căn cứ tài liệu:** [`docs/DATA_AND_API_DESIGN.md`](DATA_AND_API_DESIGN.md), [`n42-ai-kit/docs/INTERFACES.md`](../n42-ai-kit/docs/INTERFACES.md), [`docs/DECISIONS.md`](DECISIONS.md) (D-01, D-02), [`docs/ACCEPTANCE_CRITERIA.md`](ACCEPTANCE_CRITERIA.md).

---

## 1. Bối cảnh & Mục tiêu kỹ thuật

Hiện tại, hệ thống N4.2 đang bước vào giai đoạn tích hợp giữa các phân hệ:
1. **Module M1 (Ingest):** Tiếp nhận bản tin thô qua REST API ([N42-14](https://nhutp2945-1793259952237.atlassian.net/browse/N42-14)).
2. **Module M2/M4 (Parser & Storage):** Bóc tách chuẩn hóa thành `AlertEvent` và lưu vào TimescaleDB ([N42-15](https://nhutp2945-1793259952237.atlassian.net/browse/N42-15), [N42-16](https://nhutp2945-1793259952237.atlassian.net/browse/N42-16), [N42-30](https://nhutp2945-1793259952237.atlassian.net/browse/N42-30)).
3. **Module M7 (Dashboard / Frontend):** Hiển thị danh sách sự kiện và bộ lọc thời gian thực ([N42-34](https://nhutp2945-1793259952237.atlassian.net/browse/N42-34)).

Để tránh hiện tượng lệch pha về tên trường, kiểu dữ liệu, ngữ nghĩa mã lỗi HTTP và cơ chế phân trang, tài liệu này **đóng băng bộ hợp đồng kỹ thuật v1.0 (Frozen Contract Gate)** làm căn cứ triển khai cho toàn bộ nhóm.

---

## 2. Quyết định Kỹ thuật 01: Chuẩn hóa Thực thể & DTO (DEC-01)

### 2.1. Thống nhất trường dữ liệu `AlertEvent` v1.0 (Internal Domain Model)
- **Chuẩn thời gian:** Bắt buộc định dạng ISO-8601 kèm múi giờ UTC (`timezone-aware`). Ví dụ: `2026-11-16T07:15:30.123Z`.
- **Tên thiết bị mạng:** Thống nhất chính thức sử dụng tên trường **`hostname`** (VARCHAR 255), loại bỏ hoàn toàn việc dùng xen kẽ `device_id` gây nhầm lẫn giữa BE và FE.
- **Địa chỉ IP nguồn:** `source_ip` bắt buộc hợp lệ theo chuẩn IPv4/IPv6 (RFC 5737 / RFC 1918 trong môi trường thử nghiệm).
- **Phân định Severity:**
  - `severity`: Kiểu số nguyên chuẩn RFC 5424 (0 = Emergency .. 7 = Debug).
  - Khuyến nghị bổ sung nhãn đọc được: `severity_label` (string tương ứng).

### 2.2. Định nghĩa DTO `EventView` (External Response Model cho Dashboard)
Để tối ưu hóa băng thông mạng khi truy vấn hàng ngàn sự kiện lên Dashboard, `EventView` là bản thu gọn của `AlertEvent`:
- **Loại bỏ:** Trường `raw_payload` (dung lượng lớn, chỉ tải khi người dùng bấm xem chi tiết modal log).
- **Bổ sung:** Thuộc tính tính toán `severity_label` để UI render màu sắc ngay lập tức mà không cần tự mapping.

| Tên trường | Kiểu dữ liệu | Bắt buộc | Ghi chú cho Frontend (FE) |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` (string) | Có | Định danh duy nhất của sự kiện cảnh báo |
| `event_timestamp` | `TIMESTAMPTZ` (string ISO-8601) | Có | Thời gian xảy ra sự kiện (UTC) |
| `received_at` | `TIMESTAMPTZ` (string ISO-8601) | Có | Thời gian hệ thống tiếp nhận (UTC) |
| `source_ip` | `string` | Có | IP thiết bị phát sinh cảnh báo |
| `hostname` | `string` | Có | Tên thiết bị (Router, Switch, Firewall) |
| `facility` | `int (0..23)` | Có | Mã phân loại dịch vụ RFC 5424 |
| `severity` | `int (0..7)` | Có | Mức độ nghiêm trọng (0 = Emergency, 7 = Debug) |
| `severity_label` | `string` | Có | Nhãn mức độ: CRITICAL, ERROR, WARNING, INFO... |
| `vendor` | `string` | Có | Hãng thiết bị: `cisco`, `huawei`, `fortinet`, `linux` |
| `program` | `string | null` | Không | Tiến trình phát sinh (ví dụ: `BGP`, `LINK`, `sshd`) |
| `mnemonic` | `string | null` | Không | Mã định danh cảnh báo của hãng (ví dụ: `UPDOWN`) |
| `category` | `string` | Có | Phân loại nghiệp vụ (mặc định `unknown`) |
| `message` | `string` | Có | Nội dung cảnh báo đã bóc tách |
| `parse_status` | `string` | Có | Trạng thái bóc tách (`parsed` hoặc `fallback`) |

---

## 3. Quyết định Kỹ thuật 02: Hợp đồng Tiếp nhận REST API (DEC-02 - N42-14)

### 3.1. Đặc tả Endpoint Tiếp nhận
- **Đường dẫn chuẩn:** `POST /api/v1/events` (Hỗ trợ alias tương thích ngược: `POST /api/v1/events/ingest`).
- **Headers:**
  - `Content-Type: application/json` (Bắt buộc).
  - `Idempotency-Key: <UUIDv4>` (Khuyến nghị): Mã định danh idempotency để chống gửi trùng lặp bản tin khi client retry mạng.

### 3.2. Cấu trúc Request Body (`EventIngestRequest`)
Hỗ trợ cả gửi bản tin thô (Syslog Raw String) và gửi bản tin có metadata:
```json
{
  "raw_message": "<189>Nov 16 07:15:30 r-core-01 %LINK-3-UPDOWN: Interface GigabitEthernet0/0/1, changed state to down",
  "source_ip": "192.0.2.1"
}
```
Hoặc dạng nhận theo lô (Batch Ingest):
```json
{
  "items": [
    { "raw_message": "<189>Nov 16 ...", "source_ip": "192.0.2.1" },
    { "raw_message": "<190>Nov 16 ...", "source_ip": "192.0.2.2" }
  ]
}
```

### 3.3. Phân định Ngữ nghĩa Trả về (ACK Semantics) & Mã lỗi HTTP
- **`201 Created` (Durable Commit):**
  - Trả về khi sự kiện đã được parse và ghi thành công xuống CSDL bền vững TimescaleDB (M4).
  - Body:
    ```json
    {
      "status": "persisted",
      "event_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "received_at": "2026-11-16T07:15:30.123Z"
    }
    ```
- **`202 Accepted` (RAM Queue Ingest - Phục vụ PoC N42-14):**
  - Trả về khi hệ thống tiếp nhận bản tin thô vào hàng đợi bộ nhớ (RAM/Queue) và chờ worker nền bóc tách bất đồng bộ.
  - Body:
    ```json
    {
      "status": "queued",
      "receipt_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "received_at": "2026-11-16T07:15:30.123Z"
    }
    ```
- **Các mã lỗi chuẩn hóa:**
  - **`400 Bad Request`:** Định dạng JSON bị hỏng hoặc thiếu trường `raw_message`.
  - **`409 Conflict`:** Gửi lại cùng một `Idempotency-Key` nhưng nội dung `raw_message` khác với lần gửi trước đó.
  - **`422 Unprocessable Entity`:** Dữ liệu vi phạm schema Pydantic (ví dụ: `source_ip` không đúng chuẩn IP).
  - **`503 Service Unavailable`:** Hàng đợi RAM bị đầy (vượt ngưỡng saturation theo quy định AC-01/NFR-08) hoặc CSDL TimescaleDB tạm thời ngắt kết nối.

---

## 4. Quyết định Kỹ thuật 03: Hợp đồng Tra cứu & Phân trang (DEC-03 - N42-67 / N42-34)

### 4.1. Đặc tả Endpoint Tra cứu Danh sách Sự kiện
- **Đường dẫn chuẩn:** `GET /api/v1/events`
- **Phương thức:** `GET`
- **Mục đích:** Cung cấp dữ liệu danh sách cảnh báo thời gian thực cho Dashboard Frontend ([N42-34](https://nhutp2945-1793259952237.atlassian.net/browse/N42-34)).

### 4.2. Tham số Truy vấn (Query Parameters)
| Tham số | Kiểu | Bắt buộc | Mặc định | Ý nghĩa |
| :--- | :--- | :--- | :--- | :--- |
| `from` | `string (ISO-8601)` | **Bắt buộc** | - | Mốc thời gian bắt đầu (UTC) |
| `to` | `string (ISO-8601)` | **Bắt buộc** | - | Mốc thời gian kết thúc (UTC) |
| `hostname` | `string` | Không | `null` | Lọc chính xác theo tên thiết bị mạng |
| `severity` | `int (0..7)` | Không | `null` | Lọc theo mức độ nghiêm trọng |
| `vendor` | `string` | Không | `null` | Lọc theo nhà sản xuất (`cisco`, `huawei`...) |
| `limit` | `int` | Không | `50` | Số lượng bản ghi tối đa trên một trang (Max: 500) |
| `cursor` | `string (base64)` | Không | `null` | Con trỏ phân trang của trang kế tiếp |

### 4.3. Cơ chế Phân trang bằng Cursor (Cursor-based Pagination)
Nhằm đảm bảo thời gian truy vấn **dưới 2 giây trên tập dữ liệu $\ge 1.000.000$ bản tin** (theo tiêu chí NFR-05):
- **Không dùng `OFFSET`:** Phân trang dạng `OFFSET n LIMIT m` sẽ quét toàn bộ dữ liệu phía trước, gây suy giảm hiệu năng nghiêm trọng khi người dùng lật đến trang sau.
- **Sử dụng Cursor:** Cursor là chuỗi mã hóa Base64 chứa cặp khóa phân vùng: `(event_timestamp, id)`.
  - Cấu trúc giải mã của cursor: `{"ts": "2026-11-16T07:00:00Z", "id": "uuid-cua-ban-ghi-cuoi"}`.
  - Câu truy vấn tối ưu trên TimescaleDB:
    ```sql
    SELECT * FROM alert_events
    WHERE event_timestamp >= :from AND event_timestamp <= :to
      AND (event_timestamp, id) < (:cursor_ts, :cursor_id)
    ORDER BY event_timestamp DESC, id DESC
    LIMIT :limit + 1;
    ```

### 4.4. Cấu trúc Response Body (`EventListResponse`)
```json
{
  "items": [
    {
      "id": "e0b0e5d4-4f0f-4886-b47a-c71c4c92b23a",
      "event_timestamp": "2026-11-16T07:15:30Z",
      "received_at": "2026-11-16T07:15:30.123Z",
      "source_ip": "192.0.2.1",
      "hostname": "r-core-01",
      "facility": 23,
      "severity": 3,
      "severity_label": "ERROR",
      "vendor": "cisco",
      "program": "LINK",
      "mnemonic": "UPDOWN",
      "category": "interface_status",
      "message": "Interface GigabitEthernet0/0/1, changed state to down",
      "parse_status": "parsed"
    }
  ],
  "next_cursor": "eyJ0cyI6ICIyMDI2LTExLTE2VDA3OjE1OjMwWiIsICJpZCI6ICJlMGIwZTVkNC00ZjBmLTQ4ODYtYjQ3YS1jNzFjNGM5MmIyM2EifQ==",
  "has_more": true
}
```

---

## 5. Quyết định Kỹ thuật 04: Hợp đồng Nhập tệp Lịch sử (DEC-04 - N42-22)

- **Đường dẫn:** `POST /api/v1/imports`
- **Định dạng tải lên:** `multipart/form-data` chứa tệp log đuôi `.log`, `.txt` (tối đa 50MB trong môi trường Lab).
- **Phản hồi:** Trả về mã `202 Accepted` kèm theo `job_id`, mã băm `sha256` của tệp để theo dõi tiến độ xử lý đối soát số dòng theo yêu cầu AC-01/AC-07.

---

## 6. Ma trận Trách nhiệm Tích hợp (Integration Matrix)

| Module / Ticket | Phụ trách | Phạm vi hợp đồng phụ thuộc |
| :--- | :--- | :--- |
| **N42-62 (Hiện tại)** | **Phạm Tấn Thành (BE2)** | **Chủ trì: Đóng băng tài liệu contract v1, xây dựng DTO Pydantic và fixture mẫu.** |
| **N42-14 (REST Ingest)** | Phạm Hoàng Long (BE1) | Triển khai endpoint `POST /api/v1/events` tuân thủ DTO Ingest và mã ACK. |
| **N42-30 (DB Repository)** | Phạm Tấn Thành (BE2) | Hiện thực hóa lưu trữ `AlertEvent` và batch insert vào TimescaleDB. |
| **N42-67 (Query API)** | Phạm Tấn Thành (BE2) | Triển khai endpoint `GET /api/v1/events` hỗ trợ cursor pagination. |
| **N42-34 (Dashboard FE)** | Lê Khắc Huy (FE) | Dựng giao diện bảng danh sách sự kiện và bộ lọc theo đúng DTO `EventView`. |
| **M8 (Test & CI)** | Ngô Châu Kiệt (QA Lead) | Sử dụng bộ fixture mẫu v1 để thiết lập kịch bản kiểm thử tự động E2E. |

