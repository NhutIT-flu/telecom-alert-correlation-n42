# Research: Vòng đời cảnh báo

## R1. Hai trục trạng thái
- **Decision**: signal active/recovered do hệ thống; workflow new/acknowledged/closed do operator. Chỉ 5 tổ hợp hợp lệ AN/AA/RN/RA/RC.
- **Rationale**: Phân biệt rule thấy điều kiện đã hết với người đã xác nhận.
- **Alternatives considered**: Một cột open/in_progress/resolved/closed; trộn nhận định thiết bị và thao tác con người.
- **Source**: [lifecycle-design.md](lifecycle-design.md) mục 1–2.

## R2. Lịch sử và concurrency
- **Decision**: alerts snapshot + state_version, alert_state_history append-only; ACK/CLOSE dùng expected_state_version, no-op không tăng version; RN→RC có thể ghi ACK+CLOSE hai dòng cùng transaction.
- **Rationale**: Audit và tránh ghi đè khi operator/rule cập nhật đồng thời.
- **Alternatives considered**: Chỉ update status; mất chuỗi chuyển và actor. Frontend tự xác định version; không tin cậy.
- **Source**: 002 mục 5–7.

## R3. Tái phát/hiệu chỉnh
- **Decision**: Recovered chưa closed vẫn giữ alert ID và ACK khi tái phát; closed bất biến, lần đủ ngưỡng sau tạo episode mới; correction có audit.
- **Rationale**: Theo dõi cùng sự cố tới khi người giám sát đóng, giữ bằng chứng lịch sử.
- **Alternatives considered**: Tự close khi recovered, tạo ID mới ngay khi tái phát; trái phạm vi.
- **Limit**: Timer recovery cần coverage an toàn từ 003/005/006; không tạo syslog giả.

## R4. Điều chưa chốt
- Cơ chế actor/identity lab theo 005; cách implement row lock/CAS và transaction theo repository thực tế. Không thêm bảng tài khoản hoặc khắc phục thiết bị trong feature này.
