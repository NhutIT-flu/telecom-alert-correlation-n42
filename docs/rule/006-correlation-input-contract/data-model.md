# Data model: Ranh giới đầu vào tương quan

Không tạo bảng mới cho feature 006 ở prototype. Đây là mapping và validation của các entity đã có; schema DB nguồn chuẩn ở [001](../001-alert-data-model/data-model.md), lifecycle ở [002](../002-alert-lifecycle/lifecycle-design.md), checkpoint/receipt ở [003](../003-rule-dispatch-correlation/engine-design.md).

| Entity | Thuộc tính dùng ở ranh giới | Quan hệ / chủ sở hữu |
|---|---|---|
| `events` | id, parse_status, correlation_status, event_type, device_id, event_time/time_status/received_at, correlation_scope, attributes, source_metadata, correlation_details | Một event ID được xét trong registry snapshot; raw và normalization theo 001/005 |
| `rules` | id, rule_key, version, handler_key/revision, definition, is_enabled, activated_at | Metadata `supported_event_types`, `required_fields`, `required_group_fields` do 003 kiểm tra; chỉ LinkFlap là rule nghiệp vụ đợt đầu |
| `rule_group_states` | rule_id, scope, group_values, state_schema_version, state_payload, checkpoint_version, last_event_id, next_check_at | State theo revision/scope/group; không là kho guard cho device/scope chưa biết group |
| `pipeline_runtime_status` | component, scope, instance_id, heartbeat_at, coverage_started_at, details.inflight | Health và work receipt; không thay diagnostic từng event |
| `alerts`, `alert_events`, `alert_state_history` | Cảnh báo, bằng chứng, audit | 002/003 sở hữu ghi theo kết luận handler; 006 không ghi trực tiếp |

## Bản chiếu sự kiện

`NormalizedEvent` là object có kiểu **trong worker**, không là bảng mới. Nguồn từ `events`: `event_id=id`, `event_type`, `device_id`, `correlation_scope`, `event_time`, `received_at`, `time_status`, cùng `fields` được kiểm tra từ `attributes`. `source_metadata.normalization_schema_version` và `parser_revision` là căn cứ decode. Chi tiết ở [contract projection](contracts/normalized-event.md).

Với `interface_state_change`, `fields` có `interface_name` string không rỗng, `interface_state` UP/DOWN, `interface_layer` physical/protocol khi xác định được. Field vắng mặt có nghĩa là chưa biết, không là một enum thứ ba. Handler LinkFlap đòi device, interface, lớp đã chọn và event_time tin cậy.

## Diagnostic và guard

`events.correlation_details` là JSONB có schema/version, không là kho raw hoặc state thuật toán. Đề xuất shape cấp cao:

```json
{
  "contract_version": 1,
  "registry_rule_ids": ["rule-revision-id"],
  "rule_dispositions": [
    {"rule_id": "rule-revision-id", "kind": "INVALID_FOR_RULE", "reason_code": "MISSING_GROUP_FIELD"}
  ],
  "guards": [
    {"rule_id": "rule-revision-id", "scope_kind": "device", "scope_key": "device-id", "reason_code": "MISSING_GROUP_FIELD", "raised_at": "2026-11-25T00:00:00Z", "released_at": null}
  ]
}
```

Giá trị ID trong ví dụ là nhãn minh họa, không tuyên bố UUID hợp lệ. Thao tác release giữ lý do và mốc audit; không xóa entry cũ. Giới hạn bytes/entry và index cần được đo, không giả rằng JSONB tìm guard nhanh. Nếu một event có nhiều rule ứng viên, disposition phải gắn rule_id cụ thể; rule không đăng ký event_type không cần được ghi thành hàng loạt NOT_APPLICABLE.

**Điều kiện bất biến:** `processed` chỉ khi mọi candidate có disposition cuối, guard cần thiết đã lưu và result/checkpoint/evidence đã commit. Guard còn mở vẫn chặn timer liên quan dù event đã `processed`. Với bản tin thiếu trường, phương án khôi phục căn cứ và gỡ guard theo nhóm thuộc [phạm vi sau prototype](contracts/input-disposition.md#xử-lý-sau-prototype).

## State transitions của event

| Trạng thái hiện tại | Điều kiện | Trạng thái sau |
|---|---|---|
| parse pending | Raw đã lưu, chờ chuẩn hóa | parse success/partial/failed |
| correlation pending | success/partial, live hoặc replay chủ động, chưa đủ chốt | pending; chưa đánh giá |
| correlation pending | candidate xét xong và transaction kết quả commit | processed; diagnostic/guard có thể còn |
| correlation pending | search-only lịch sử hoặc không thể áp dụng theo chính sách | skipped kèm lý do |
| correlation pending | Lỗi handler/schema hoặc retry cạn | failed nếu DB ghi được; dừng worker |
| correlation failed | Khôi phục quản trị có quyền và audit | pending, giữ raw/ID/snapshot retry |

Không có trạng thái `processing` lưu dài hạn. Receipt trong `pipeline_runtime_status.details.inflight` giữ workset chưa commit. `event_time`, raw, ID không đổi để hợp thức lại thứ tự. Closed alert không bị sửa bởi correction.

## Validation cần đo

- Query guard theo group/device/source/scope trước timer, kể cả event processed và parse-pending/failed. Nếu đường JSONB không đạt tải prototype, thiết kế bảng guard riêng ở revision sau và migration rõ.
- Serialize/restore state, schema version và registry snapshot qua restart; không khởi tạo rỗng khi checkpoint lỗi.
- Chỉ số từ `correlation_details`: số disposition theo mã lý do, guard mở, tuổi guard, tuổi pending; cùng health/backlog nhưng không lẫn thành syslog.
