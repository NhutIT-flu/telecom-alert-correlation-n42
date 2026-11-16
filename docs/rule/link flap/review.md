# Rà soát N4.2 — Link Flap Detection

**Ngày**: 16/11/2026. Đọc tài liệu 972 dòng, đối chiếu định nghĩa, giả mã, ví dụ và nghiệm thu. Đây là rà soát tài liệu, chưa xác minh một triển khai.

## Nhận định

Chưa thấy mâu thuẫn giữa định nghĩa đếm và fixture U01–U26 khi đọc thủ công: UP↔DOWN là một transition, INITIAL không đếm, cửa sổ bao gồm hai đầu. Tài liệu phân biệt tốt repetition/duplicate, số đếm cửa sổ/tổng đợt, workflow/technical status và hết dao động/vẫn DOWN. Chưa có căn cứ cần đổi thuật toán lõi.

## Các quyết định vừa xác nhận

| Nội dung | Kết luận |
| --- | --- |
| Phạm vi | Toàn bộ luật Link Flap và thiết lập module dùng chung cho rule sau |
| Thời gian | RECEIVED_TIME; chấp nhận khác biệt do log dồn/trễ |
| Recovery | 120s, pipeline khỏe và tiến độ đủ; LAST_OBSERVED, không yêu cầu probe/SNMP |

Đã ghi trong [spec.md](spec.md); giữ nguyên tài liệu gốc.

## Các điểm cần chỉnh hoặc cụ thể hóa

1. **Cập nhật phạm vi** — Mục 1.3 chỉ giao phần luật; câu trả lời mới mở rộng sang module rule chung. Kế hoạch cần gồm registry, state namespace, timer, ordering, persistence và giao quyết định. Chưa cần DSL hoặc rule production tiếp theo.

2. **Gán chủ sở hữu test** — Mục 14.1 đưa U01–U26 vào Gói A, nhưng U01/U25 liên quan State Manager/RuleInput; duplicate/restart thuộc engine, phối hợp Link Down thuộc tích hợp. Giữ test nhưng phân nhóm trách nhiệm, tránh hiểu rule pass là hệ thống đã nghiệm thu.

3. **Bổ sung nhánh ID collision vào giả mã** — Mục 5.4 và T02 yêu cầu cùng ID khác payload phải quarantine. Mục 6.4 chỉ viết “if event_id already committed: return DUPLICATE”, chưa thể hiện nhánh so nội dung. Trước khi trả DUPLICATE cần đối chiếu nội dung nghiệp vụ ổn định đã lưu; khác thì trả collision và giữ state đã commit. Cần định nghĩa những trường nào được so để metadata xử lý lại không gây collision giả. Đây là thiếu sót biểu diễn giả mã, chưa phải lỗi mã nguồn đã xác minh.

4. **Chính sách bảo trì còn mở** — Mục 2.1/15.3 chưa chốt admin shutdown/bảo trì. Bản nháp tính mọi OPER_STATUS hợp lệ, chưa suppress. Nếu muốn loại bảo trì, cần chốt nhận diện đầu vào, xử lý đợt ACTIVE, baseline và khi hết bảo trì; không tự bỏ DOWN vì phỏng đoán thao tác quản trị.

5. **Cụ thể hóa bên cung cấp progress/fence** — Thiết kế recovery đã bao phủ cả raw chưa parse. Khi tích hợp cần chốt bên phát barrier, phạm vi nguồn/partition, lỗi/gap và điều kiện resume. “Rule queue rỗng” không thay cho hợp đồng này. Thiếu bên cung cấp thì chưa chứng minh được auto-recovery hoàn chỉnh.

6. **Giữ event-time ngoài bản đầu** — Theo lựa chọn người dùng, chưa triển khai reorder/watermark. Nếu làm sau, schema 4.1 có device_sequence/quality nhưng cần biểu diễn rõ epoch/phạm vi sequence thiết bị được nhắc ở 5.3; source_epoch hiện là epoch Collector. Không dùng sequence Collector để suy ra thứ tự vật lý.

7. **Không biến lab thành cam kết production** — Tick 5s, budget 2s, tải 1.000 interface/100 events/s và retention 7 ngày còn chưa duyệt hoặc đo. Đưa vào thảo luận kế hoạch, chưa đánh dấu đạt hiệu năng.

## Phạm vi kiểm chứng tiếp theo

- Luật: baseline, cửa sổ 60s, tổng đợt, cập nhật và biên 120s, theo U01–U26 và module sở hữu.
- Module chung: rule thứ hai có cùng snapshot, state riêng; lỗi giữa chừng, timer cũ, retry/restart không thêm hiệu lực.
- Tích hợp: progress bao phủ raw, áp dụng quyết định chống trùng/đúng thứ tự, Link Down không dùng snapshot DOWN cũ.

Chưa chạy test hoặc đối chiếu DB/API/mẫu log vì chưa có source/dữ liệu dự án. Constitution còn là template; chưa suy ra framework hoặc hạ tầng.

## Cập nhật khi lập kế hoạch, 16/11/2026

Người dùng đã cung cấp source tại `C:/Projects/vnpt` và yêu cầu lấy công nghệ hiện có, hành vi theo chat. Đã đọc repository `telecom-alert-correlation-n42`: có parser/config/dedup RAM; store và pipeline/progress bền vững chưa được triển khai trong source đã khảo sát. Nhận định “chưa có source” ở phần rà soát phía trên mô tả thời điểm trước thông tin này.

Fixture `tests/fixtures/rules/review-cases.json` tính first transition notice bằng một, còn `docs/scenarios/KB-01-link-flap.md` kỳ vọng năm observations kích hoạt mà chưa định nghĩa baseline. Cần fixture version mới với baseline rõ: có baseline UP thì năm quan sát xen kẽ bắt đầu DOWN tạo năm transitions; không baseline thì cần sáu observations. [plan.md](plan.md) và [research.md](research.md) ghi các thay đổi cần thực hiện. Chưa sửa source hoặc chạy test/DB trong lượt lập kế hoạch.

