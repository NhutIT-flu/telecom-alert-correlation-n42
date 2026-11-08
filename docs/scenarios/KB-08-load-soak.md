# KB-08 Load and Recovery

**Phiên bản:** 1.1 · **QA đặc tả/chạy tích hợp:** Ngô Châu Kiệt — QA Lead · **Code owner theo module (dự kiến):** Ngô Châu Kiệt — QA Lead (generator N42-11; To Do); Phạm Hoàng Long — BE1 (UDP/load N42-32; To Do trong sprint sau); Phạm Tấn Thành — BE2 (DB dependency N42-16/31; To Do). BE3 Nguyễn Duy Minh chỉ khi correlation nằm trong profile đo. · **Trạng thái:** Đặc tả; chưa chạy; BLOCKED chờ implementation/contract · **Liên kết:** TC-PERF-001/002/004; AC-01/AC-07; NFR-01/03/04/08

## Phân công theo vai trò

- **Code implementation:** Ngô Châu Kiệt — QA Lead (generator N42-11; To Do); Phạm Hoàng Long — BE1 (UDP/load N42-32; To Do trong sprint sau); Phạm Tấn Thành — BE2 (DB dependency N42-16/31; To Do). BE3 Nguyễn Duy Minh chỉ khi correlation nằm trong profile đo. Mỗi BE/FE tự viết và chạy unit/component test cho phần code mình phụ trách, ghi commit và evidence trên Jira.
- **Chuẩn bị fixture, test case, chạy tích hợp/replay và lưu evidence:** Ngô Châu Kiệt — QA Lead; QA xác nhận kết quả sau khi dependencies sẵn sàng, không thay BE/FE viết logic nghiệp vụ.
- **Điều phối tài liệu và quyết định:** Phạm Minh Nhựt — TL/PM ghi nhận scope/acceptance đã được chủ yêu cầu và code owner xác nhận; không tự chốt contract, ngưỡng hoặc semantics kỹ thuật.
- **Lưu ý giao việc:** đây là owner theo phân công module trong tài liệu dự án, không khẳng định Jira đã gán ticket; TL cần đối chiếu Jira trước khi bắt đầu. Không tự ghi PASS khi chưa chạy và có evidence.


> **Hiện trạng baseline:** repo hiện chưa có pipeline nghiệp vụ tương ứng với kịch bản này; đây là đặc tả, không phải báo cáo chạy. Trạng thái thực thi hiện tại: `BLOCKED / NOT RUN`. Chỉ bỏ Blocked khi code/dependency và contract nêu trong case đã sẵn sàng.

> **Đối chiếu Jira (09/11/2026):** xem ticket được nêu tại phần phân công; trạng thái Jira là ảnh chụp tại ngày này, không tự đồng bộ khi ticket đổi trạng thái. Ticket đang `To Do`/`In Progress` không có nghĩa code đã xong.

## Mục tiêu
Đo tải danh định, stress và khả năng phục hồi của hệ thống lab bằng generator có thể tái lập; tách kết quả checkpoint khỏi nghiệm thu W13.

## Tiền điều kiện và reset
Ghi máy/OS, commit, config, DB state, generator version, seed, socket/queue limits và clock sync. Generator phải được đo riêng để loại nghẽn nguồn phát. Chỉ dùng dữ liệu giả lập và loopback/lab.

## Dữ liệu đầu vào và profile
Seed `KB-08-v1`. Checkpoint: 200→500→1.000 msg/s, ít nhất 10 phút tại tải danh định theo Test Plan. Stress riêng: 1.500 msg/s trong 2 phút. Final W13: ≥1.000 msg/s liên tục 1 giờ, không gộp với checkpoint/stress.

## Kết quả mong đợi
Báo cáo sent/accepted/persisted/dropped IDs, throughput, P50/P99, CPU/RAM, queue depth, DB outcome và recovery sau hạ tải. Chỉ kết luận theo AC sau khi đối soát đầy đủ; UDP loss là observed measurement, không khẳng định bảo đảm mạng tuyệt đối.

## Thực hiện và evidence
Lưu script/config/seed hash, raw logs, thời điểm bắt đầu-kết thúc, artifact và commit. Nếu bất kỳ phần đối soát/generator measurement nào thiếu, ghi Inconclusive/Blocked, không PASS.


