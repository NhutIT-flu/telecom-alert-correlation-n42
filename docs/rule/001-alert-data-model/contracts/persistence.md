# Contract: Lưu sự kiện và kết quả tương quan

## Raw → normalized
- Input: một lần tiếp nhận qua UDP/API/file có raw text hoặc bytes, nguồn/scope và giờ hệ thống nhận.
- Commit raw `events` với ID ổn định, parse pending trước khi trả accepted cho kênh có phản hồi. UDP không có ACK ứng dụng.
- Normalizer giữ raw/ID, ghi field chuẩn + parse success/partial/failed, parser/time diagnostics. Unknown không tự điền.
- File history là replay scope riêng và search-only mặc định; không gán live.

## Normalized → correlator
- Chỉ event parse success/partial và correlation pending được chọn; projection canonical theo [006](../../006-correlation-input-contract/contracts/normalized-event.md).
- Worker ghi exact event IDs, registry snapshot và kết quả vào receipt/transaction theo 003. Processed có thể không có alert. Failed không tự skip.

## Result transaction
Trong cùng commit: checkpoint nhóm, alert snapshot, alert_events, alert_state_history, diagnostic/guard cần giữ, đúng event progress và xóa receipt. Crash trước commit giữ pending; sau commit reload DB. Không sửa raw/event_time để tạo lại thứ tự. Các FK RESTRICT, PK evidence/history và schema JSONB theo [data-model.md](../data-model.md).

## Query
Tra theo received_at/event_time cần phân biệt thời gian và dùng cặp thời gian+ID cho phân trang ổn định. Tìm event đã lưu được dù parse failed. Index theo [data-model.md](../data-model.md) mục 8; index interface/text thêm sau đo. Không tuyên bố hai raw giống nhau với ID khác nhau là một event.
