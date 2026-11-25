# Research: Tích hợp giám sát

## R1. Pipeline và đồng bộ
- **Decision**: UDP/API/file→commit raw→normalize→worker polling→commit results→API snapshot/frontend polling. LISTEN/SSE/broker là bước sau.
- **Rationale**: Nguồn dữ liệu bền vững, ít thành phần cho prototype.
- **Alternatives considered**: Push trực tiếp handler/frontend hoặc broker ngay; tăng vận hành, rủi ro kết quả trước commit.
- **Source**: [integration-design.md](integration-design.md) mục 1/5.

## R2. Chuẩn hóa đa hãng
- **Decision**: Canonical interface_name, interface_state UP/DOWN, interface_layer physical/protocol; adapter field cũ chỉ ở biên; raw preserved, unknown diagnostic.
- **Rationale**: Cùng rule cho Cisco/Juniper khi mapping có căn cứ.
- **Alternatives considered**: Rule tự parse raw/field hãng hoặc mặc định physical; tăng coupling và false alert.
- **Source**: 005 mục 2, 006 contract.

## R3. Đầu vào/quyền
- **Decision**: Giới hạn event/request/file và batch thử lab theo 005; API/file chỉ báo thành công sau commit. Principal lab tách viewer/operator/ingest/maintenance; không bảng tài khoản mới.
- **Rationale**: Không báo lưu giả, quyền thao tác rõ.
- **Alternatives considered**: Nhận dữ liệu không giới hạn hoặc tin actor/status từ client; không an toàn.
- **Limit**: Không tuyên bố UDP exactly-once; API/file không tự chứng minh quan sát liên tục.

## R4. Frontend và health
- **Decision**: API đọc snapshot đã commit; polling giao diện mục tiêu 1 giây, reconnect reload và hiển thị stale. Health/coverage theo component+scope, heartbeat 1 giây/stale 3 giây là giá trị thử; health healthy không đồng nghĩa backlog rỗng.
- **Rationale**: Không hiển thị dữ liệu cũ như trực tiếp hoặc dùng silence làm recovery.
- **Alternatives considered**: Chỉ incremental MAX(ID), gộp health với syslog, coi correlator restart xóa mọi coverage; sai trạng thái.
- **Limit**: TLS/identity/clock policy thực tế phải xác nhận trước deployment; không có đo SLA.
