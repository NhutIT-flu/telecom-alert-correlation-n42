# Contract: Rule và operator tác động vòng đời cảnh báo

## Đề nghị từ rule
Handler trả ACTIVATE/RECOVER với rule revision, scope, group, evidence IDs, outcome, effective_at, reason và decision_source. Lifecycle kiểm tra DB hiện hành, state version, bằng chứng/coverage; handler không ghi DB hoặc ACK/CLOSE. Timer RECOVER có causal_event_id NULL nhưng phải tham chiếu bằng chứng thật.

## Thao tác operator
ACK và CLOSE nhận alert ID + expected_state_version; actor lấy từ danh tính xác thực của 005. Nếu đích đã đạt, trả snapshot no-op không thêm history; nếu version cũ hoặc state không hợp lệ, từ chối và yêu cầu đọc lại. CLOSE chỉ khi recovered; RN có thể ACK+CLOSE trong cùng transaction với hai history version.

## Output
alerts là snapshot hai trục; alert_state_history append-only với from/to, actor, source, effective_at và recorded_at; alert_events giữ bằng chứng trigger/recovery/correction. Tạo, cập nhật snapshot, history/evidence và checkpoint của engine cùng commit. Closed bất biến; correction về sau ghi diagnostic riêng. Quy tắc chi tiết và T01–T39: [lifecycle-design.md](../lifecycle-design.md).

Khi tạo alert, Lifecycle lấy mức độ từ revision đã đánh giá. Các cập nhật trên cùng alert giữ nguyên mức đã gán theo [chính sách 001](../../001-alert-data-model/spec.md#quy-ước-gán-mức-độ-nghiêm-trọng).
