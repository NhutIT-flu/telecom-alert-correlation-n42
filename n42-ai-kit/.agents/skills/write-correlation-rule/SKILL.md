---
name: write-correlation-rule
description: Thiết kế và viết luật tương quan, gom nhóm cảnh báo (Port Flapping, brute-force/port scan, Alert Spike, lan truyền đa thiết bị, BGP neighbor down) với tham số đọc từ cấu hình, kèm test dòng thời gian. Hãy dùng skill này khi BE3 thêm luật mới, chỉnh ngưỡng, viết engine cửa sổ trượt, hoặc đo tỷ lệ phát hiện của luật.
---

# Luật tương quan

## Nguyên tắc
- **Không hardcode** `window_seconds`, `threshold_count`, `group_by`, `match_pattern`, `severity_trigger` trong mã. Thêm luật mới chỉ là thêm cấu hình (JSON hoặc dòng `correlation_rules`), không sửa/build lại mã.
- Đầu vào là `AlertEvent` nhận qua `Pipeline.subscribe`. Không sửa `AlertEvent` nếu chưa qua `change-alertevent-schema`.

## Cấu hình luật (ví dụ)
```json
{
  "rule_id": "port-flapping",
  "enabled": true,
  "window_seconds": 300,
  "threshold_count": 5,
  "group_by": ["hostname"],
  "match_pattern": "link (up|down)",
  "severity_trigger": 4
}
```

## Quy trình
1. Xác định hành vi cần phát hiện và kịch bản chuẩn tương ứng của QA (`docs/scenarios/`).
2. Chọn cách tính: cửa sổ trượt in-memory bằng `collections.deque`, hoặc aggregate theo time bucket của TimescaleDB. Giải thích lý do trong PR.
3. Cài luật như một lớp đọc cấu hình, xử lý theo nhóm `group_by`, sinh/ cập nhật `GroupedIncident`, tránh sinh cảnh báo lặp cho cùng một sự cố.
4. Viết test `pytest` mô phỏng chuỗi sự kiện theo dòng thời gian (dùng timestamp giả, không `sleep`): ca phát hiện đúng (TP), ca không đủ ngưỡng, ca ngoài cửa sổ, ca nhiều thiết bị, ca nhiễu (FP).
5. Tính tỷ lệ TP/FP trên các kịch bản; mục tiêu ≥90%, **mốc W12 ≥70%**. Báo số liệu thật, không ước chừng.
6. Gom nhóm cảnh báo lặp: mục tiêu giảm ≥70% cảnh báo trùng thừa.

## PR
`feat: them luat <ten-luat> (N42-x)`. Luật cần **2 reviewer**.
