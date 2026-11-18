# N42-10 — nâng cấp ngày 13/11/2026

Owner: Ngô Châu Kiệt (QA). Người dùng cho phép triển khai 9 hạng mục và dừng lab để sao lưu. Chờ TL review trước merge. Nguồn: Jira N42-10, TC-OPS-002, AC-07/08 và review PR #17.

## Ca nghiệm thu bổ sung (đặc tả trước triển khai)

| ID | Input/điều kiện | Expected |
|---|---|---|
| CI-09 | Push feature hoặc PR main có test mới trong tests/test_*.py | Checkout revision nhánh/merge ref, chạy toàn bộ unittest + pytest; JUnit/coverage gắn SHA |
| CI-10 | Một test backend thất bại | Job tests và check tổng hợp thất bại; merge chỉ bị chặn khi required check đã bật |
| JK-01 | Build main hoặc job review dùng project validation cố định | Scanner và Gate cùng task/revision, không ghi đè project chính từ feature |
| JK-02 | Gate trả OK / ERROR | SUCCESS / FAILURE và artifact Gate |
| JK-03 | Bước wait thực sự hết deadline | FAILURE, artifact TIMEOUT; hủy thủ công vẫn ABORTED |
| OPS-04 | Backup khi Jenkins/Sonar dừng, PostgreSQL dump, archive volume | Kiểm checksum, danh mục archive và restore thử database/Jenkins trên volume cách ly |
| OPS-05 | Restart stack với volume đã xác minh | Job/config/project/database còn; không tự tạo volume trống |

## Phạm vi quyền

Không tự merge PR, đổi policy owner, đóng Jira hoặc tuyên bố required checks hoạt động khi thiếu quyền. Giữ các stash N42-12. Việc job main chạy pipeline mới qua polling cần nghiệm thu sau merge được duyệt. Không thêm tự động gửi Jira/email.

## JK-04 — deadline review (bổ sung sau ủy quyền quản trị)

SONAR_REVIEW_TIMEOUT_SECONDS chỉ áp dụng feature review, mặc định 600, nhận số nguyên 10..600; main luôn 600 giây. Input 9/601/không phải số phải bị từ chối. Kiểm cú pháp bằng declarative linter Jenkins; kiểm runtime timeout dùng deadline 15 giây trên project validation không webhook. Chỉ ghi PASS khi log cho thấy waitForQualityGate đã thực sự đợi và hết hạn.
