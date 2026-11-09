# KB-03 SYN Flood

**Phiên bản:** 1.1 · **QA đặc tả/chạy tích hợp:** Ngô Châu Kiệt — QA Lead · **Code owner theo module (dự kiến):** Phạm Hoàng Long — BE1 (ingest dependency N42-13/14; To Do); Phạm Tấn Thành — BE2 (Fortinet parser N42-25; To Do); Nguyễn Duy Minh — BE3 (rule format N42-17, dedup N42-18 and mapping N42-26; To Do) · **Trạng thái:** Đặc tả; chưa chạy; BLOCKED chờ implementation/contract · **Liên kết:** TC-COR-008; AC-05/AC-06; FR-09

## Phân công theo vai trò

- **Code implementation:** Phạm Hoàng Long — BE1 (ingest dependency N42-13/14; To Do); Phạm Tấn Thành — BE2 (Fortinet parser N42-25; To Do); Nguyễn Duy Minh — BE3 (rule format N42-17, dedup N42-18 and mapping N42-26; To Do). Mỗi BE/FE tự viết và chạy unit/component test cho phần code mình phụ trách, ghi commit và evidence trên Jira.
- **Chuẩn bị fixture, test case, chạy tích hợp/replay và lưu evidence:** Ngô Châu Kiệt — QA Lead; QA xác nhận kết quả sau khi dependencies sẵn sàng, không thay BE/FE viết logic nghiệp vụ.
- **Điều phối tài liệu và quyết định:** Phạm Minh Nhựt — TL/PM ghi nhận scope/acceptance đã được chủ yêu cầu và code owner xác nhận; không tự chốt contract, ngưỡng hoặc semantics kỹ thuật.
- **Lưu ý giao việc:** đây là owner theo phân công module trong tài liệu dự án, không khẳng định Jira đã gán ticket; TL cần đối chiếu Jira trước khi bắt đầu. Không tự ghi PASS khi chưa chạy và có evidence.


> **Hiện trạng baseline:** repo hiện chưa có pipeline nghiệp vụ tương ứng với kịch bản này; đây là đặc tả, không phải báo cáo chạy. Trạng thái thực thi hiện tại: `BLOCKED / NOT RUN`. Chỉ bỏ Blocked khi code/dependency và contract nêu trong case đã sẵn sàng.

> **Đối chiếu Jira (09/11/2026):** xem ticket được nêu tại phần phân công; trạng thái Jira là ảnh chụp tại ngày này, không tự đồng bộ khi ticket đổi trạng thái. Ticket đang `To Do`/`In Progress` không có nghĩa code đã xong.

## Mục tiêu
Đánh giá phát hiện chuỗi deny bất thường từ firewall mà vẫn giữ trace từ incident về event gốc.

## Tiền điều kiện và reset
Chỉ dùng firewall giả lập và dải địa chỉ TEST-NET cho đích minh họa. Rule phải có `threshold_count`, `window_seconds` và grouping key được duyệt; không hardcode ngưỡng riêng trong fixture.

## Dữ liệu đầu vào
Seed `KB-03-v1`; phát N bản tin Fortinet `action=deny`, `proto=6`, cùng source giả lập `10.10.1.50`, cùng rule key trong cửa sổ cấu hình. Chạy biến thể N-1, N và N+1; ghi N/window thực tế vào execution record.

## Kết quả mong đợi
N-1 không tạo incident nếu rule quy định ngưỡng N; N và N+1 tạo/duy trì incident theo dedup policy, với toàn bộ event IDs và rule version. Tính noise reduction theo AC-06, không suy ra từ số event gửi đơn thuần.

## Thực hiện và evidence
Lưu generator/config hash, counts, TP/FP/FN, raw/incident/standalone counts, resource/latency và log. Nếu rule chưa chốt thì case `BLOCKED`, không PASS.


