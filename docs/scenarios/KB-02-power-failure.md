# KB-02 Power Supply Failure

**Phiên bản:** 1.1 · **QA đặc tả/chạy tích hợp:** Ngô Châu Kiệt — QA Lead · **Code owner theo module (dự kiến):** Phạm Tấn Thành — BE2 (Huawei parser, Jira N42-24; To Do); Nguyễn Duy Minh — BE3 (severity/mnemonic mapping N42-26 and rule format N42-17; both To Do; incident single-hit only if approved) · **Trạng thái:** Đặc tả; chưa chạy; BLOCKED chờ implementation/contract · **Liên kết:** TC-COR-010; TC-PAR-004; AC-02/AC-05; FR-04/FR-09

## Phân công theo vai trò

- **Code implementation:** Phạm Tấn Thành — BE2 (Huawei parser, Jira N42-24; To Do); Nguyễn Duy Minh — BE3 (severity/mnemonic mapping N42-26 and rule format N42-17; both To Do; incident single-hit only if approved). Mỗi BE/FE tự viết và chạy unit/component test cho phần code mình phụ trách, ghi commit và evidence trên Jira.
- **Chuẩn bị fixture, test case, chạy tích hợp/replay và lưu evidence:** Ngô Châu Kiệt — QA Lead; QA xác nhận kết quả sau khi dependencies sẵn sàng, không thay BE/FE viết logic nghiệp vụ.
- **Điều phối tài liệu và quyết định:** Phạm Minh Nhựt — TL/PM ghi nhận scope/acceptance đã được chủ yêu cầu và code owner xác nhận; không tự chốt contract, ngưỡng hoặc semantics kỹ thuật.
- **Lưu ý giao việc:** đây là owner theo phân công module trong tài liệu dự án, không khẳng định Jira đã gán ticket; TL cần đối chiếu Jira trước khi bắt đầu. Không tự ghi PASS khi chưa chạy và có evidence.


> **Hiện trạng baseline:** repo hiện chưa có pipeline nghiệp vụ tương ứng với kịch bản này; đây là đặc tả, không phải báo cáo chạy. Trạng thái thực thi hiện tại: `BLOCKED / NOT RUN`. Chỉ bỏ Blocked khi code/dependency và contract nêu trong case đã sẵn sàng.

> **Đối chiếu Jira (09/11/2026):** xem ticket được nêu tại phần phân công; trạng thái Jira là ảnh chụp tại ngày này, không tự đồng bộ khi ticket đổi trạng thái. Ticket đang `To Do`/`In Progress` không có nghĩa code đã xong.

## Mục tiêu
Kiểm tra cảnh báo lỗi nguồn nghiêm trọng được parse, giữ nguyên raw và đưa vào xử lý đúng severity.

## Tiền điều kiện và reset
Dùng fixture Huawei NE40E giả lập; cấu hình rule single-hit nếu rule này được phê duyệt. Dùng `run_id` riêng và không gửi tới thiết bị thật.

## Dữ liệu đầu vào
Seed `KB-02-v1`; một bản tin: `<131>2026-11-06T15:01:00+07:00 ne40e-bras-01 %%01DEVM/2/POWER_SUPPLY_FAILED(l): Power supply module 2 was failed.`

## Kết quả mong đợi
Parser giữ raw, xác định vendor/message theo fixture và severity `CRITICAL` theo mapping đã duyệt. Nếu single-hit rule nằm trong release, tạo một incident có source event ID và evidence; nếu chưa có rule/config, đánh dấu case blocked bởi dependency, không thay bằng PASS.

## Thực hiện và evidence
Lưu parser version, expected/actual từng trường, rule version, event/incident IDs và log.


