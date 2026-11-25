# Research: Rule LinkFlap

## R1. Đếm chuyển
- **Decision**: Chỉ lớp physical đã chọn; quan sát đầu làm baseline; mỗi UP↔DOWN là một transition, log lặp không đếm nhưng được giữ/xét; N=5 trong (T−60,T].
- **Rationale**: Đúng định nghĩa đã chốt, phân biệt router/interface và tránh đếm đôi physical/protocol.
- **Alternatives considered**: Đếm DOWN→UP là một chu kỳ, đếm mọi log trạng thái; lệch ngưỡng.
- **Source**: [link-flap-design.md](link-flap-design.md) mục 2–3.

## R2. Kết thúc
- **Decision**: Sau 60 giây không chuyển trong đoạn quan sát an toàn, trả flap_stopped_up/down và đề nghị RECOVER; LinkDown là rule khác.
- **Rationale**: Flap có thể hết ở DOWN; không giữ alert active vô hạn hoặc tự suy thiết bị tốt.
- **Alternatives considered**: Chỉ recover khi UP; giữ cảnh báo flap mở mãi ở DOWN.
- **Source**: 004 mục 3/8 và 002 lifecycle.

## R3. Log trễ và state
- **Decision**: 3 giây reorder do engine; log trễ trong vùng ảnh hưởng phải dựng lại baseline, observations cả log lặp và endpoint sau đó; history thiếu thì INCOMPLETE, không commit suy đoán.
- **Rationale**: Chèn log có thể đổi hai cạnh và làm thay cửa sổ/episode.
- **Alternatives considered**: Chỉ lưu tối đa 5 transition hoặc bỏ log trễ; không đủ tính bù.
- **Source**: 004 mục 4/8, 003 history policy.

## R4. Tài nguyên và điều kiện thực thi
- **Decision**: State theo device+interface+revision+scope khi có event, scheduler/cleanup chung; recovered chỉ evict nếu nạp lại đủ. Ví dụ cấu hình disabled vì chưa có triển khai.
- **Rationale**: Không cấp trước 1.000 instance/window.
- **Gate**: 900.000 transition/giờ là kịch bản kiểm thử, không là benchmark đã đạt; LF01–LF26 là expected results.
