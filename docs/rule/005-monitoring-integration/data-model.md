# Data model: Tích hợp giám sát

Schema DB nguồn ở [001](../001-alert-data-model/data-model.md). Tài liệu này ánh xạ dữ liệu đi qua biên ingest/normalizer/API/health, không thêm bảng tài khoản, job import hay bảng frontend.

| Entity | Trường liên quan | Quy tắc |
|---|---|---|
| events | id, ingest_source, sender_ip, source_metadata, raw_message/raw_bytes, received_at, scope | Raw commit trước parse; file có import_id/line; normalized JSON giữ nguyên text và raw_kind, không giả raw thiết bị |
| events normalized | event_time/time_status, vendor/os/type, event_type, attributes, vendor_fields, parse_status/error/at | Canonical interface fields theo 005 và [006](../006-correlation-input-contract/contracts/normalized-event.md); unknown không tự điền |
| events correlation | correlation_status/error/at/details | Worker 003 sở hữu; frontend đọc kết quả đã commit |
| pipeline_runtime_status | component, scope, instance_id, status, heartbeat_at, coverage_started_at, details, updated_at | PK(component,scope); health/coverage/receipt riêng syslog; heartbeat update không xóa inflight |
| alerts/evidence/history | signal/workflow/version, event refs | API đọc snapshot; ACK/CLOSE theo 002, không nhận actor/status do client tự khai |
| lab principals | Token/capability trong protected server config | Không bảng account prototype; viewer/operator/ingest/maintenance phân quyền |

## Input và status transitions

UDP một datagram một event, API một text/JSON, file text/JSONL theo batch. Accepted chỉ sau raw commit; parse pending→success/partial/failed; search-only history được gán replay scope ngay khi nhận và mặc định không tương quan. Partial file giữ batch đã commit, báo phần lỗi. Oversize bị từ chối/đếm, không giả là accepted. Storage lỗi trả lỗi API hoặc ghi UDP drop/health lỗi.

## Health/coverage

starting/healthy/degraded/error/stopped. Chỉ healthy có căn cứ mới có coverage_started_at; heartbeat stale coi unsafe dù row chưa đổi status. Gap chưa dựng lại làm coverage mới bắt đầu từ đoạn chứng minh được, không từ sự im lặng. Correlator restart không tự xóa coverage upstream liên tục; API/file một lần và UDP health không chứng minh không mất gói. Replay/maintenance có scope và quyền riêng.

## Giao diện

Frontend lấy snapshot có phân trang và history; refresh đề xuất 1 giây, reconnect reload, hiển thị stale/last success. API 409 khi stale version; 401/403 theo quyền; không optimistic CLOSE. I01–I15 ở [integration-design.md](integration-design.md) là ca nghiệm thu nguồn.
