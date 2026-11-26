# Quickstart: Kiểm chứng hợp đồng đầu vào tương quan

Đây là guide xác thực **tài liệu hiện có** và bộ kịch bản chạy sau khi có implementation. Hiện tại chưa có lệnh chạy worker/test app được xác nhận, chưa có benchmark; không diễn giải phần kịch bản là test đã chạy. Đầu vào và expected results nằm trong [spec](spec.md) và [contracts](contracts/normalized-event.md), [disposition](contracts/input-disposition.md).

## 1. Kiểm tra tài liệu ngay

Từ `C:\Projects\vnpt` trong PowerShell:

```powershell
$feature = 'specs/006-correlation-input-contract'
Get-ChildItem $feature -Recurse -File | Select-Object -ExpandProperty FullName
Select-String -Path "$feature/spec.md" -Pattern '\*\*FR-\d{3}\*\*','\*\*SC-\d{3}\*\*'
Get-Content '.specify/feature.json'
```

Kỳ vọng: có `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, hai contract và feature pointer `specs/006-correlation-input-contract`. Lệnh trên chỉ kiểm tra sự tồn tại/nội dung; không chứng minh behavior.

## 2. Điều kiện trước khi chạy test ứng dụng

- Leader duyệt phạm vi LinkFlap, cách lưu guard và giới hạn đo; ticket N42 thực được gắn trước triển khai.
- Repository ứng dụng là `C:/Projects/vnpt/telecom-alert-correlation-n42`, Python 3.12 và pytest hiện có. Chưa có worker hoặc lệnh test contract 006; không dùng tên branch feature như bằng chứng đã tạo branch Git. Xem [bản đồ code](../003-rule-dispatch-correlation/codebase-mapping.md).
- Có mẫu Cisco XRv đã gán nhãn, gồm raw hợp lệ, partial, sai enum/lớp, thiếu device/interface, thời gian không rõ và log đến muộn.
- Có môi trường lab tách biệt, không đưa credential hoặc log production vào fixture.

## 3. Kịch bản nghiệm thu sau triển khai

| ID | Thiết lập/hành động | Kết quả mong đợi |
|---|---|---|
| Q1 | 40 mẫu log Cisco XRv đã gán nhãn, gồm tín hiệu vật lý và mẫu sai lớp/thiếu trường | 100% mapping đúng schema hoặc diagnostic. Raw giữ nguyên. |
| Q2 | Một event thiếu field LinkFlap, rule thử khác đủ field | LinkFlap INVALID_FOR_RULE, rule kia APPLY, event processed sau commit; guard cần thiết còn bền vững |
| Q3 | 1.000 interface tên trùng ở thiết bị khác | 100% group đúng device+interface, không có NULL group |
| Q4 | Event trước deadline vẫn pending/chưa chốt | Timer không recover nhóm ảnh hưởng; sau xét, event cùng thời điểm được ưu tiên trước timer |
| Q5 | Log thiếu interface nhưng biết thiết bị A. Cho event thành `processed`, sau đó đến hạn kết thúc | Guard thiết bị A vẫn có hiệu lực, cảnh báo LinkFlap liên quan vẫn `active` và tra được lý do. Thiết bị khác vẫn được xét theo căn cứ của nó. |
| Q6 | Log không xác định device/source | Báo phạm vi không chứng minh được; không tự kết luận quiet liên quan |
| Q7 | Pipeline mất quan sát từ giây 30 đến 100, lần chuyển cuối ở giây 20, khoảng yên 60 giây | Không recover ở 80. Mốc hiệu lực sớm nhất là 160 nếu quan sát đủ căn cứ từ 100, watermark an toàn và không còn guard bản tin liên quan. |
| Q8 | Event đến muộn >3 giây chen giữa hai observation | Tính bù LinkFlap trong vùng có đủ history; ngoài vùng ghi incomplete/diagnostic, không sửa closed |
| Q9 | Kill trước receipt, sau receipt và sau result commit | Đúng pending/processed và revision snapshot; không nhân đôi alert/evidence/history |
| Q10 | Lỗi handler hoặc checkpoint schema không đọc được | Fail-stop, health error, event chưa hoàn tất/failed có barrier; không coi là không khớp |
| Q11 | Replay history cùng loại log live | State/evidence replay không trộn live |
| Q12 | 1.000 interface/900.000 transition trong một giờ, tải đều và burst | Đối chiếu đủ ID/kết quả; đo p95/p99 từng chặng, backlog, CPU/RAM, WAL và latency truy vấn guard |
| Q13 | Log vật lý có giờ nguồn thiếu múi giờ, cấu hình thiết bị đã xác minh, kết quả UTC duy nhất và qua kiểm tra thời gian | Lưu `inferred` cùng căn cứ. LinkFlap nhận `APPLY` khi đủ chốt và đủ các field còn lại, kể cả khi thiếu `target_ip`. |
| Q14 | Sự kiện khớp bộ lọc LinkFlap, chỉ biết giờ nhận hoặc giờ suy ra có căn cứ thiếu/mâu thuẫn | Bản tin tra cứu được. Dispatcher ghi `INVALID_FOR_RULE` / `UNKNOWN_EVENT_TIME` cho LinkFlap và đánh giá guard nếu bản tin có thể che một lần chuyển trạng thái. |
| Q15 | Bản tin lớp `protocol` đã xác minh, thiếu một field riêng của LinkFlap | `NOT_APPLICABLE` với LinkFlap, kể cả khi thiếu field. |
| Q16 | Nạp hai log cùng nội dung có ID khác nhau, sau đó thử xử lý lại cùng ID | Hai ID được lưu và xét riêng. Log cùng trạng thái không tăng số lần chuyển. Xử lý lại cùng ID không nhân kết quả hay bằng chứng. |

## 4. Điều kiện kết luận

Không tuyên bố feature đạt khi chỉ có fixture mapping đúng. Cần chứng minh result/guard sau restart, event/rule fan-out, timer an toàn, correction có giới hạn và dữ liệu đã commit thống nhất. Báo cáo kết quả phải phân biệt test đã chạy, kịch bản chưa chạy và mục tiêu lab chưa đo. Nếu query guard dựa trên event không đạt tải, trình leader phương án bảng guard riêng thay vì tắt guard.
