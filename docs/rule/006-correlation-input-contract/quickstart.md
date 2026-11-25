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
- Có fixture đã gán nhãn Cisco/Juniper, gồm raw hợp lệ, partial, sai enum/lớp, thiếu device/interface, thời gian không rõ và log đến muộn.
- Có môi trường lab tách biệt, không đưa credential hoặc log production vào fixture.

## 3. Kịch bản nghiệm thu sau triển khai

| ID | Thiết lập/hành động | Kết quả mong đợi |
|---|---|---|
| Q1 | 40 log Cisco/Juniper cùng nghĩa và sai nghĩa đã gán nhãn | 100% mapping đúng schema hoặc diagnostic; raw giữ nguyên |
| Q2 | Một event thiếu field LinkFlap, rule thử khác đủ field | LinkFlap INVALID_FOR_RULE, rule kia APPLY, event processed sau commit; guard cần thiết còn bền vững |
| Q3 | 1.000 interface tên trùng ở thiết bị khác | 100% group đúng device+interface, không có NULL group |
| Q4 | Event trước deadline vẫn pending/chưa chốt | Timer không recover nhóm ảnh hưởng; sau xét, event cùng thời điểm được ưu tiên trước timer |
| Q5 | Log thiếu interface nhưng biết device A | Guard device A; event processed không tự release; device khác không bị chặn nếu nguồn/căn cứ cho phép |
| Q6 | Log không xác định device/source | Báo phạm vi không chứng minh được; không tự kết luận quiet liên quan |
| Q7 | Gap 30–100 giây, last transition 20, quiet 60 | Không recover ở 80; sớm nhất 160 nếu healthy từ 100 và watermark an toàn |
| Q8 | Event đến muộn >3 giây chen giữa hai observation | Tính bù LinkFlap trong vùng có đủ history; ngoài vùng ghi incomplete/diagnostic, không sửa closed |
| Q9 | Kill trước receipt, sau receipt và sau result commit | Đúng pending/processed và revision snapshot; không nhân đôi alert/evidence/history |
| Q10 | Lỗi handler hoặc checkpoint schema không đọc được | Fail-stop, health error, event chưa hoàn tất/failed có barrier; không coi là không khớp |
| Q11 | Replay history cùng loại log live | State/evidence replay không trộn live |
| Q12 | 1.000 interface/900.000 transition trong một giờ, tải đều và burst | Đối chiếu đủ ID/kết quả; đo p95/p99 từng chặng, backlog, CPU/RAM, WAL và latency truy vấn guard |

## 4. Điều kiện kết luận

Không tuyên bố feature đạt khi chỉ có fixture mapping đúng. Cần chứng minh result/guard sau restart, event/rule fan-out, timer an toàn, correction có giới hạn và dữ liệu đã commit thống nhất. Báo cáo kết quả phải phân biệt test đã chạy, kịch bản chưa chạy và mục tiêu lab chưa đo. Nếu query guard dựa trên event không đạt tải, trình leader phương án bảng guard riêng thay vì tắt guard.
