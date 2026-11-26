# N42-23 — Thiết kế bộ phân tích cảnh báo Cisco IOS XR và IOS/Nexus

- **Ticket Jira:** [N42-23](https://nhutp2945-1793259952237.atlassian.net/browse/N42-23)
- **Branch:** `feature/N42-23-cisco-ios-parser`
- **Owner triển khai:** Phạm Hoàng Long (BE1) | **Kiểm chứng:** Ngô Châu Kiệt (QA)
- **Phụ thuộc hợp đồng:** [N42-62](https://nhutp2945-1793259952237.atlassian.net/browse/N42-62) (Event/API Contract), [N42-26](https://nhutp2945-1793259952237.atlassian.net/browse/N42-26) (Mapping mức độ nghiêm trọng)
- **Truy vết:** `KB-01/02/04 · FR-04 · FR-05 · AC-02 · TC-PAR-001..003, 010..012`
- **Căn cứ kỹ thuật:** Confluence [Thu thập và chuẩn hóa Syslog lên/xuống cổng Cisco IOS XR và Juniper (v7)](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/7602179), `docs/N42-15_DESIGN.md`, `docs/TEST_CASE_SPECIFICATION.md`.

---

## 1. Phạm vi và nguyên tắc tách profile

1. Giữ nguyên `parse_syslog_rfc3164` trong `app/services/parser.py` cho bộ hồi quy cơ sở `N42-15` (không sửa regex RFC 3164 cũ để gộp định dạng không có PRI).
2. Triển khai bộ phân tích chuyên biệt Cisco (`app/services/cisco_parser.py`) gồm:
   - `parse_cisco_syslog(raw, source_ip, *, received_at=None, source_timezone=None) -> AlertEvent`
   - `CiscoNormalizer` (hỗ trợ `can_parse(RawEvent)` và `parse(RawEvent) -> AlertEvent`)
3. Dispatcher phân loại rõ trước khi bóc tách:
   - **Profile 1 (`cisco_ios_xr` — ưu tiên trước):** Bản tin Cisco IOS XR có vị trí card dạng `LC/<r>/<s>/CPU<n>:` hoặc `RP/<r>/<slot>/CPU<n>:` (có hoặc không có `<PRI>`).
   - **Profile 2 (`cisco_ios` / `cisco_nexus`):** Bản tin có `<PRI>` (hoặc chữ ký Cisco hợp lệ kèm header thời gian RFC 3164 / ISO-8601) chứa thông báo `%FACILITY-N-MNEMONIC:`.

---

## 2. Mở rộng tương thích ngược trên `AlertEvent`

Để phục vụ `N42-23` và đồng bộ hướng DTO `N42-62` mà không phá vỡ code/test `N42-15`, `app/models/alert_event.py` bổ sung các trường tùy chọn (có giá trị mặc định) và cho phép `facility`/`severity` là `None` khi bản tin nguồn không có `<PRI>`:

| Trường | Kiểu | Ý nghĩa |
|---|---|---|
| `interface` | `Optional[str]` | Tên cổng đã trích xuất (`TenGigE0/1/0/4`, `GigabitEthernet0/1`, `Vlan100`, `Ethernet1/1`, ...) |
| `state` | `Optional[Literal["UP", "DOWN"]]` | Trạng thái vận hành của cổng (`UP` hoặc `DOWN`) |
| `card_location` | `Optional[str]` | Vị trí card/module phần cứng (`LC/0/1/CPU0`), **không** ghi đè vào `hostname` |
| `vendor_severity` | `Optional[int]` (`0..7`) | Mức độ gốc trong mã hãng (ví dụ `3` trong `%PKT_INFRA-LINK-3-UPDOWN`) |
| `normalized_severity` | `Optional[NormalizedSeverityType]` | Mức nghiệp vụ `CRITICAL / MAJOR / WARNING / INFO / DEBUG / UNKNOWN` |
| `severity_conflict` | `bool` | `True` khi `PRI severity != vendor_severity` |
| `timestamp_origin` | `Optional[TimestampOriginType]` | `PARSED`, `INFERRED`, hoặc `RECEIVED_FALLBACK` |
| `duplicate_ip` | `Optional[str]` | IP bị trùng trong mẫu `%IP-4-DUPADDR` (`TC-PAR-003`) |
| `mac_address` | `Optional[str]` | MAC nguồn xung đột trong mẫu `%IP-4-DUPADDR` (`TC-PAR-003`) |
| `parse_status` | `Literal["parsed", "partial", "fallback"]` | Thêm `partial` khi nhận diện được Cisco mnemonic trạng thái cổng nhưng thiếu `interface` hoặc `state` |

---

## 3. Quy tắc bóc tách từng định dạng

### 3.1 Cisco IOS XR (`%PKT_INFRA-LINK-3-UPDOWN`, `%PKT_INFRA-LINEPROTO-5-UPDOWN`)
- **Mẫu mentor:**
  `LC/0/1/CPU0:Nov 13 09:06:45.781 +07: ifmgr[193]: %PKT_INFRA-LINK-3-UPDOWN : Interface TenGigE0/1/0/4, changed state to Down`
- **Quy tắc:**
  - `card_location = "LC/0/1/CPU0"`.
  - `hostname`: dùng hostname trong header nếu có; khi mẫu IOS XR không có hostname thì **dùng `source_ip`** (không bao giờ lấy `LC/0/1/CPU0` làm `hostname`).
  - `facility`, `severity`: `None` nếu bản tin không có `<PRI>` (không tự sinh/bịa PRI).
  - `event_timestamp`: bóc tách `Mmm dd HH:MM:SS[.mmm]` và offset (`+07` / `+07:00` / `UTC`). Nếu thiếu năm → suy ra năm gần `received_at` nhất (3 ứng viên năm `y-1, y, y+1`) và đặt `timestamp_inferred = True`, `timestamp_origin = "INFERRED"`. Nếu thiếu offset → dùng `source_timezone`. Nếu đủ năm + offset → `timestamp_inferred = False`, `timestamp_origin = "PARSED"`. Giữ `received_at` riêng và đổi `event_timestamp` về UTC.
  - `program = "ifmgr"`, `mnemonic = "PKT_INFRA-LINK-3-UPDOWN"`, `vendor_severity = 3`.
  - `interface = "TenGigE0/1/0/4"`, `state = "DOWN"` / `"UP"`, `category = "link_status"`.

### 3.2 Cisco IOS & Cisco Nexus
- **`%LINK-3-UPDOWN` (`TC-PAR-001`):** `Interface <iface>, changed state to <up|down|administratively down>` (hoặc dạng rút gọn `<iface> <up|down>`) → `interface`, `state` (`"UP"`/`"DOWN"`), `category = "link_status"`.
- **`%LINEPROTO-5-UPDOWN` (`TC-PAR-002`):** `Line protocol on Interface <iface>, changed state to <up|down>` → `interface`, `state`, `category = "link_status"`.
- **`%ETHPORT-5-IF_UP` / `%ETHPORT-5-IF_DOWN_*` (Nexus NX-OS):** `Interface <iface> is <up|down>...` → `interface`, `state`, `category = "link_status"`.
- **`%IP-4-DUPADDR` (`TC-PAR-003`):** `Duplicate address <ip> on <iface>, sourced by <mac>` → `duplicate_ip`, `interface`, `mac_address`, `category = "ip_conflict"`.

---

## 4. Ánh xạ mức độ nghiêm trọng (phiên bản đề xuất `cisco-map-v0.9`, chờ N42-26 chốt v1.0)

| Mức số (`0..7`) | Tên RFC 5424 / Cisco | `normalized_severity` |
|---|---|---|
| `0, 1, 2` | Emergency, Alert, Critical | `CRITICAL` |
| `3` | Error | `MAJOR` |
| `4` | Warning | `WARNING` |
| `5, 6` | Notice, Informational | `INFO` |
| `7` | Debug | `DEBUG` |

- Khi bản tin có cả `<PRI>` và `vendor_severity`:
  - Giữ cả hai trường (`severity = PRI % 8`, `vendor_severity = N`).
  - Nếu `severity != vendor_severity` → đặt `severity_conflict = True`.
  - Ưu tiên dùng `vendor_severity` để suy `normalized_severity` vì mã hãng phản ánh trực tiếp mức độ của sự kiện trên thiết bị Cisco.

---

## 5. Xử lý lỗi, `partial` và cô lập trạng thái

- Thứ tự kiểm tra lỗi tương đồng `N42-15` (`empty_input` → `payload_too_large` > 2048 bytes → ký tự điều khiển / newline bên trong `malformed_header` → `invalid_pri` → `malformed_header` → `invalid_timestamp` → `unsupported_format`).
- Với bản tin Cisco port-status hoặc `IP-4-DUPADDR` đã nhận diện được chữ ký hãng nhưng thiếu `interface` hoặc `state` (hoặc thiếu `duplicate_ip`/`mac_address`):
  - Trả `parse_status = "partial"`, `parse_error = "missing_interface_or_state"` (hoặc `"missing_conflict_fields"`), `interface = None`, `state = None` (không sinh khóa rỗng cho correlation).
- Mọi hàm parse đều stateless, regex compile một lần ở cấp module và neo chặt chẽ chống ReDoS: lỗi ở bản tin trước tuyệt đối không ảnh hưởng sang bản tin hợp lệ tiếp theo.
