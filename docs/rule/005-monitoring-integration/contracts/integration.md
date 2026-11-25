# Contract: Đầu vào, API giám sát và health

## Ingest/normalization
UDP: mỗi datagram một event, không ACK. API: một text hoặc normalized JSON; file text/JSONL stream theo batch, có import_id+line. Server sở hữu ID/received_at/scope/status, commit raw trước accepted. Giới hạn thử lab: event 16,384 bytes; request 1 MiB; file 50 MiB; batch 500. Oversize reject/count; lỗi parse giữ raw đã accepted. Historical search-only có replay scope ngay lúc nhận, không trộn live. Canonical output theo [006](../../006-correlation-input-contract/contracts/normalized-event.md).

## API surface dự kiến
POST /ingest/events, /ingest/files; GET /events, /alerts, /alerts/{id}, /alerts/{id}/history, /alerts/{id}/events, /health; POST /alerts/{id}/ack, /close; maintenance POST /events/{id}/retry, /replays/{scope}/evaluate, /correlations/rebuild. ACK/CLOSE dùng expected_state_version theo 002. Replay/rebuild cần request_id/reason, quyền riêng và scope rõ. Lỗi 400/401/403/404/409/413/503 theo trường hợp; không báo accepted khi chưa commit.

## Auth/UI
Viewer đọc; operator ACK/CLOSE; ingest:live/history và maintenance:retry/replay/rebuild tách quyền. Principal/token lab ở protected server config, không bảng account hoặc credential trong repo. UI đọc snapshot đã commit, polling thử 1 giây; reconnect reload, stale/last-success rõ; 409 reload, không optimistic CLOSE.

## Health/coverage
Mỗi component/scope ghi instance/status/heartbeat/coverage_started_at; trial heartbeat 1s/stale 3s. Healthy không đồng nghĩa backlog drained hoặc UDP giao đủ. Gap không chứng minh được reset đầu đoạn safe mới; correlator restart không tự xóa chứng cứ coverage upstream. Health update không ghi đè receipt/rebuild_request trong details. Bản đầy đủ và I01–I15: [integration-design.md](../integration-design.md).
