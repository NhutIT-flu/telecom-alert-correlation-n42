# Mẫu báo cáo tiến độ dự án N4.2 W1

**Kỳ báo cáo:** W1, 01–07/11/2026 · **Người lập:** Team Leader · **Trạng thái:** DỰ THẢO CHƯA PHÁT HÀNH

Bản này là mẫu ghi nhận, không xác nhận Jira Done, cuộc họp đã diễn ra, test đã chạy hoặc KPI đã đạt. TL hoàn tất sau khi đối chiếu Jira, PR/commit và artifact; nếu chưa có bằng chứng ghi `Chưa xác minh` hoặc `Chưa thực hiện`, không tự điền kết quả. Kickoff dự kiến ngày 09/11 thuộc W2.

## 1. Tóm tắt kỳ báo cáo

- Trạng thái chung: `[Cập nhật sau đối chiếu]`
- Mốc dự kiến: `[Mốc trong W1]`
- Việc bị trễ / forecast: `[Nêu tác động và owner]`
- Quyết định cần PM hỗ trợ: `[Nội dung hoặc Không có]`

## 2. Kết quả theo công việc

| Jira | Owner | Kế hoạch | Kết quả thực tế | Trạng thái | Evidence |
|---|---|---|---|---|---|
| `[N42-xx]` | `[Tên]` | `[Mô tả]` | `[Chưa cập nhật]` | `[To Do/In Progress/Done/Blocked]` | `[PR/log/link hoặc chưa có]` |

## 3. Chất lượng và kiểm thử

| Hạng mục | Kết quả | Evidence / ghi chú |
|---|---|---|
| Test case/coverage | Chưa xác minh | Liên kết `TEST_CASE_SPECIFICATION` và RTM |
| Unit/integration tests | Chưa xác minh | Không ghi PASS nếu thiếu run log/commit |
| CI/workflow | Chưa có workflow trong repo hiện tại; QA Lead là owner dự kiến triển khai | Ghi Jira/task, link workflow và run/evidence sau khi hoàn thành; hiện không ghi PASS |
| Load/performance | Chưa xác minh | Ghi config, duration, sent/received, latency và tài nguyên |

## 4. Rủi ro, blocker và hỗ trợ

| Mô tả | Mức độ | Tác động | Owner | Hạn / hỗ trợ cần |
|---|---|---|---|---|
| `[Cập nhật từ Jira/Risk Register]` | `[H/M/L]` | `[Mốc/đầu việc]` | `[Tên]` | `[Yêu cầu]` |

## 5. Kế hoạch kỳ tiếp theo

| Ưu tiên | Jira | Owner | Kết quả dự kiến | Phụ thuộc |
|---|---|---|---|---|
| `[Điền sau khi thống nhất]` | `[N42-xx]` | `[Tên]` | `[Acceptance/evidence]` | `[Nếu có]` |

## 6. Rà soát và gửi

- TL đối chiếu với Jira và bằng chứng: `[Tên / ngày]`
- Gửi PM trong hạn quy trình chương trình: `[Ngày / trạng thái]`
- Link báo cáo / email: `[Chưa ghi nhận]`
