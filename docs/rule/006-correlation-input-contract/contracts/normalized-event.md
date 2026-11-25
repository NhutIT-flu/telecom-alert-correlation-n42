# Contract v1: Sự kiện chuẩn hóa đưa vào engine

**Producer:** module chuẩn hóa theo 005. **Consumer:** worker/dispatcher/handler theo 003. **Transport:** sự kiện đã commit trong kho bền vững, không phải lời gọi trực tiếp bắt buộc. **Source of truth:** [001](../../001-alert-data-model/data-model.md).

## Eligibility

- `parse_status ∈ {success,partial}`, `correlation_status=pending`; scope live hoặc replay được phép. Search-only lịch sử không tự được chọn.
- Event có thời gian chưa đủ chốt vẫn pending. Event thiếu thời gian dùng được được phân loại diagnostic/guard, không treo mãi trong heap và không giả giờ nhận là giờ nguồn.
- Producer không đặt hộ ID, received_at, correlation_status, scope quyền hoặc actor. Raw/ID đã commit trước chuẩn hóa.

## Projection có kiểu

| Field | Kiểu | Nguồn/ý nghĩa |
|---|---|---|
| event_id | BIGINT dương | events.id; định danh, không thứ tự nguồn |
| event_type | string hoặc NULL | loại nghiệp vụ được parser xác nhận |
| event_time | UTC timestamp hoặc NULL | thời điểm phát sinh có căn cứ |
| time_status | parsed/inferred/unknown | căn cứ parse/inference; unknown đi với event_time NULL |
| received_at | UTC timestamp | thời gian hệ thống nhận |
| device_id | UUID hoặc NULL | thiết bị xác định được |
| correlation_scope | live hoặc replay:<UUID> | tách live/history |
| fields | object có schema theo event_type | projection từ events.attributes, không là bản lưu thứ hai |
| normalization_schema_version | integer dương | source_metadata, kiểm tra phiên bản |
| parser_revision | string | source_metadata, truy vết adapter |

## Schema interface_state_change v1

| Field trong fields | Giá trị hợp lệ | Ý nghĩa |
|---|---|---|
| interface_name | string không rỗng | Tên trong phạm vi thiết bị; không tự đổi alias |
| interface_state | UP/DOWN | Trạng thái được quan sát |
| interface_layer | physical/protocol | Lớp được parser chứng minh; không mặc định physical |

Thiếu field có thể được biểu diễn bằng vắng mặt và diagnostic, không điền NULL string, `UNKNOWN` hoặc giá trị hợp lệ giả. Cùng field từ dạng cũ và chuẩn mà mâu thuẫn không được tùy chọn một bên. Normalizer ánh xạ Cisco/Juniper về cùng nghĩa; `vendor_fields` không được handler dùng làm nguồn ngầm thay field chuẩn. Một quan sát lặp UP→UP vẫn được bàn giao nếu rule đăng ký loại này.

`target_ip` được biên bản họp đề xuất bổ sung cho sự kiện có địa chỉ đích. Nó **không bắt buộc với LinkFlap** và không được điền bằng `source_ip`/`sender_ip`. Khi event_type/rule cần nó, giá trị phải là IP hợp lệ có căn cứ; vắng mặt tạo diagnostic riêng. Quyết định lưu nó ở cột INET chung hay trong `attributes` cần TL/BE2/BE3 chốt theo [đối chiếu schema](../../001-alert-data-model/meeting-schema-alignment.md) trước migration.

## Ownership và versioning

Normalizer bảo đảm mapping/diagnostic; worker kiểm tra lại shape trước dispatcher; handler khai báo `required_fields`/group/time và chỉ nhận projection phù hợp. Schema thay nghĩa phải tạo phiên bản/migration có kiểm chứng, không ghi cùng tên field với nghĩa khác. Không chỉnh raw hoặc event_time sau khi evidence/correlation đã có hiệu lực.

## Ví dụ hợp lệ

```json
{
  "event_id": 42,
  "event_type": "interface_state_change",
  "event_time": "2026-11-25T00:00:05Z",
  "time_status": "parsed",
  "received_at": "2026-11-25T00:00:06Z",
  "device_id": "00000000-0000-4000-8000-000000000001",
  "correlation_scope": "live",
  "fields": {"interface_name": "GigabitEthernet0/0", "interface_state": "DOWN", "interface_layer": "physical"},
  "normalization_schema_version": 1,
  "parser_revision": "lab-cisco-v1"
}
```

Đây là ví dụ contract nội bộ, không là JSON gốc do thiết bị gửi.
