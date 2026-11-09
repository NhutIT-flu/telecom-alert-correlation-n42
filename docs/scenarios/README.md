# Scenario Catalog — KB-01..08

Bộ này là **đặc tả scenario**, không phải bằng chứng kiểm thử đã chạy. Repo baseline hiện chỉ có API health; các pipeline ingest, parser, persistence, correlation/rules và dashboard chưa hoàn chỉnh để thực thi end-to-end các KB. Vì vậy trạng thái hiện tại của 8 case là `BLOCKED / NOT RUN`. Không ghi PASS nếu chưa có run record gắn commit, môi trường và evidence.

## Cách hiểu phân công

- **TL/PM — Phạm Minh Nhựt:** xây dựng/duy trì khung và hồ sơ dự án (charter, kế hoạch, mẫu, RTM), điều phối xác nhận scope/acceptance với người có thẩm quyền, quản lý Jira và baseline, tổng hợp review/sign-off. TL không tự chốt contract hay threshold kỹ thuật/nghiệp vụ.
- **QA Lead — Ngô Châu Kiệt:** viết đặc tả test case chi tiết, coverage, fixture và điều kiện biên; chạy kiểm thử tích hợp khi dependency sẵn sàng, lưu evidence và báo defect. QA không thay BE/FE viết logic nghiệp vụ. Ticket QA cụ thể cần có trên Jira; trạng thái hiện tại ghi trong snapshot bên dưới.
- **BE/FE code owner:** xác nhận contract kỹ thuật và expected result, viết/chạy unit/component test cho phần code mình triển khai, hỗ trợ QA điều tra defect. Owner ghi trong bảng là theo module/ticket đã thấy; phần chưa có ticket cần TL tạo/gán trước khi kéo việc.
- **Quy ước mã đã thống nhất:** KB-02 = Power Supply Failure; KB-03 = SYN Flood; KB-04 = IP Conflict. Đây là chuẩn mã trong bộ tài liệu và tiêu đề Jira N42-27 đã được sửa cho khớp ngày 09/11/2026.

| KB | Code owner theo module | QA chạy tích hợp | Gate chính trước khi chạy |
|---|---|---|---|
| KB-01 Link Flap | Phạm Hoàng Long (BE1, N42-23 Cisco parser); Phạm Tấn Thành (BE2, N42-15 schema); Nguyễn Duy Minh (BE3, N42-18 dedup) | Ngô Châu Kiệt | Parser/schema và rule threshold/window theo AC đã merge |
| KB-02 Power Failure | Phạm Tấn Thành (BE2, N42-24 Huawei parser); Nguyễn Duy Minh (BE3, N42-26 severity mapping, N42-17 rules) | Ngô Châu Kiệt | Parser/mapping có; single-hit rule được BE3 và owner nghiệp vụ xác nhận |
| KB-03 SYN Flood | Phạm Hoàng Long (BE1, N42-13/14 ingest); Phạm Tấn Thành (BE2, N42-25 parser); Nguyễn Duy Minh (BE3, N42-17/18/26) | Ngô Châu Kiệt | Ingest/parser có; threshold/window/grouping được BE3 và owner nghiệp vụ xác nhận |
| KB-04 IP Conflict | Phạm Hoàng Long (BE1, N42-23 Cisco parser); Nguyễn Duy Minh (BE3, rule N42-64 — Sprint 4, To Do, chưa estimate; N42-18 grouping dependency) | Ngô Châu Kiệt | Parser fields và grouping contract có; ngưỡng/grouping semantics cần owner xác nhận |
| KB-05 BGP Neighbor Down | Phạm Tấn Thành (BE2, parser scope chờ N42-62 contract decision); Nguyễn Duy Minh (BE3, rule N42-65 — Sprint 4, To Do, chưa estimate) | Ngô Châu Kiệt | Parser/vendor scope được duyệt; retry semantics/window được BE3 xác nhận và owner nghiệp vụ duyệt nếu cần |
| KB-06 CPU High Temperature | Phạm Tấn Thành (BE2, Huawei parser N42-24); Nguyễn Duy Minh (BE3, rule N42-66 — Sprint 4, To Do, chưa estimate) | Ngô Châu Kiệt | Parser/severity mapping và comparator được BE2 xác nhận; dashboard/API chỉ chạy khi đã triển khai |
| KB-07 Malformed Syslog | Phạm Hoàng Long (BE1), Phạm Tấn Thành (BE2) | Ngô Châu Kiệt | Receiver/parser contract và payload policy được BE1/BE2 xác nhận |
| KB-08 Load and Recovery | Ngô Châu Kiệt (QA, N42-11 generator); Phạm Hoàng Long (BE1, N42-32); Phạm Tấn Thành (BE2, N42-16/31); Nguyễn Duy Minh (BE3, nếu nằm trong scope) | Ngô Châu Kiệt | Pipeline end-to-end, generator và môi trường đo được owner liên quan xác nhận |

## Jira snapshot 09/11/2026 (sau cập nhật sprint)

`N42-62` (BE2, contract API/Event) ở Sprint 1 để xử lý blocker của `N42-14`. `N42-64/65/66` (BE3, ba rule KB-04/05/06) ở Sprint 4; `N42-63` (FE, export) ở Sprint 6 sau các dependency `N42-34` (Sprint 3) và `N42-46` (Sprint 5). Cả năm ticket đã được Jira API đọc lại: trạng thái `To Do`, assignee giữ nguyên, story point chưa estimate. Các vị trí sprint là tạm thời cho đến khi refinement và rà capacity; đây không phải bằng chứng code/test đã hoàn thành. Các trạng thái ticket khác trong phần này là snapshot theo thời điểm, cần đọc lại Jira trước khi phân công thực thi.

**Đối chiếu Jira API (09/11/2026):** summary và Description của `N42-27` đã khớp KB-03 (SYN Flood) và KB-04 (IP Conflict), liên kết đúng scenario/TC/RTM; `N42-12` khớp KB-01 Link Flap và KB-02 Power Supply Failure. Cả hai vẫn `To Do`; đây là trạng thái công việc, không phải kết quả test. Các ticket mới N42-62–66 có lịch như snapshot trên, nhưng chưa estimate.

Ticket QA `N42-12` và các ticket triển khai vẫn cần được đối chiếu trực tiếp trên Jira trước khi bắt đầu; tài liệu đặc tả trong repo không chứng minh trạng thái thực thi hay kết quả kiểm thử.

Xem từng KB để biết input, expected result, biên, reset, ticket/dependency và evidence cần lưu. Mọi threshold/contract còn mở phải do code owner và người có thẩm quyền xác nhận; TL ghi nhận decision vào tài liệu/Jira trước khi QA chuyển ca sang READY.

