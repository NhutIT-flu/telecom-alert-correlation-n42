# KẾ HOẠCH KIỂM THỬ TỔNG THỂ & ĐO KIỂM TẢI 1.000 MSG/S (QA MASTER TEST PLAN)

> **Mã tài liệu:** `VNPT-NET-N42-QATP-2026-V1.2`  
> **Chủ nhiệm kiểm thử:** **Ngô Châu Kiệt — QA Lead**
> **Người phê duyệt & Điều phối chung:** **Phạm Minh Nhựt — Project Manager / Team Leader**  
> **Cơ quan bảo trợ:** Trung tâm Điều hành Khai thác Mạng VNPT NET  
> **Cơ sở đào tạo:** Trường ĐH Giao thông Vận tải TP.HCM (UTH) — Học kỳ Doanh nghiệp  
> **Trạng thái:** BẢN KẾ HOẠCH KIỂM THỬ NỘI BỘ — chờ Cố vấn VNPT NET xác nhận

---

## 1. MỤC TIÊU & PHẠM VI KIỂM THỬ

1. **Kiểm thử chức năng:** Lập và thực thi test theo `TEST_CASE_SPECIFICATION.md`, bao phủ các nguồn UDP, REST và file theo SRS; parser, persistence/query, correlation/rules, health và dashboard theo contract đã được duyệt. Tài liệu hiện là kế hoạch; code baseline mới có health endpoint, nên chưa tuyên bố coverage hoặc pass chức năng 100%.
2. **Kiểm thử hiệu năng & chịu tải:** Các lần kiểm tra trung gian duy trì tải danh định **&ge; 1.000 msg/s trong ít nhất 10 phút**. Bài nghiệm thu cuối ở W13 phải duy trì **&ge; 1.000 msg/s liên tục trong 1 giờ** và đạt **0.00% UDP drops observed** theo phương pháp đo trong AC; đồng thời CPU/RAM phải trong giới hạn đã duyệt.
3. **Kiểm thử bảo mật:** Quét mã nguồn định kỳ, đảm bảo không lưu mật khẩu hoặc token hardcode. Dữ liệu chỉ dùng IP giả lập; mạng lab `10.10.0.0/16` là dải riêng RFC 1918, còn `203.0.113.0/24` là dải ví dụ tài liệu RFC 5737.

---

## 2. CHỈ TIÊU ĐO KIỂM (KPI CỦA ĐỀ TÀI, KHÔNG PHẢI SLA PRODUCTION)

| Chỉ số KPI/AC | Mục tiêu nghiệm thu | Ghi chú đánh giá |
| :--- | :--- | :--- |
| **Thông lượng tiếp nhận** | **&ge; 1.000 msg/s** | Dưới mục tiêu AC là không đạt; vùng 950–999 chỉ dùng theo dõi, không phải Pass. |
| **Thời lượng bài nghiệm thu cuối** | **1 giờ liên tục ở mức danh định** | Checkpoint 10 phút không thay thế bài final. |
| **Tỷ lệ rớt gói UDP Socket (final theo AC)** | **0.00% observed** | Mọi tỷ lệ quan sát được lớn hơn 0.00% đều không đạt AC; nêu giới hạn phép đo. |
| **Độ trễ xử lý P50** | **&lt; 50 ms** | Từ 50 ms trở lên không đạt AC. |
| **Độ trễ xử lý P99** | **&lt; 200 ms** | Từ 200 ms trở lên không đạt AC. |
| **Mức chiếm dụng CPU (4 Cores)** | **&le; 60%** | Trên 60% không đạt AC; ghi rõ quota và cách lấy mẫu. |
| **Mức chiếm dụng RAM** | **&le; 1.5 GB** | Trên 1.5 GB không đạt AC; ghi rõ process/container scope. |

Các ngưỡng trên lấy từ `ACCEPTANCE_CRITERIA.md`; đây là KPI nghiệm thu của đề tài, không phải SLA production. Khi có thay đổi, cập nhật AC, kế hoạch, test case và RTM cùng một decision record.

---

## 3. KỊCH BẢN PHÁT TẢI 4 GIAI ĐOẠN (RAMP-UP PROFILE)

```
Lưu lượng (msg/s)
   ^
   |                                 [Giai đoạn 4: Spike Test 1.500 msg/s]
   |                                    +------+
1500|                                    |      |
   |               [Giai đoạn 3: Peak]  |      |
1000|            +----------------------+      +------+
   |            /                                     \
500|      +----+ [Giai đoạn 2: Nominal]               \
   |     /                                             \
200|  +-+ [Giai đoạn 1: Warm-up]                       \
   |  |                                                 \
 0 +--+----+----+-----------------------+------+-------+---> Thời gian (Phút)
   0  2    5    8                      18     20      22
```

1. **Giai đoạn 1 (Warm-up - 2 phút):** Phát 200 msg/s để khởi tạo pool kết nối DB và làm nóng socket buffer.
2. **Giai đoạn 2 (Nominal - 3 phút):** Nâng tải lên 500 msg/s, kiểm tra tính toàn vẹn của parser.
3. **Giai đoạn 3 (Peak Load - 10 phút):** Duy trì đều đặn **1.000 msg/s** bằng load runner có đối soát; runner chưa có trong baseline. Đây là checkpoint, không thay bài final 1 giờ.
4. **Giai đoạn 4 (Spike Stress - 2 phút):** Đẩy đột biến lên 1.500 msg/s để quan sát queue/resource/error và recovery. Ghi throughput và drops thực tế; không tự đặt tiêu chí 0% drop cho spike nếu chưa có AC được duyệt.
5. **Giai đoạn hạ tải (Cool-down - 2 phút):** Giảm dần về 0, kiểm tra giải phóng tài nguyên.

Các 4 giai đoạn trên là bài kiểm tra ramp-up/checkpoint. Chúng không thay bài nghiệm thu cuối: ở W13 chạy riêng 60 phút liên tục tại ít nhất 1.000 msg/s theo `ACCEPTANCE_CRITERIA.md` và lưu số gửi/nhận, latency, CPU, RAM.

---

## 4. MA TRẬN 8 KỊCH BẢN KIỂM THỬ CHUẨN (TEST MATRIX KB-01..08)

| Mã KB | Tên kịch bản | Thiết bị nguồn | Dạng cảnh báo mô phỏng | Kết quả kỳ vọng (tiêu chí đặc tả) | Code owner theo module | QA tích hợp |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **KB-01** | Bão cảnh báo Interface Flapping | Cisco Catalyst | `LINK-3-UPDOWN` & `LINEPROTO-5-UPDOWN` | 5 event/60 giây thành 1 incident; 4 event hoặc event thứ 5 ở T+61 không tạo incident theo rule | BE1 Phạm Hoàng Long (Cisco parser N42-23); BE2 Phạm Tấn Thành (schema N42-15); BE3 Nguyễn Duy Minh (dedup N42-18) | QA Ngô Châu Kiệt |
| **KB-02** | Nguồn cấp điện dự phòng lỗi | Huawei NE40E | `POWER_SUPPLY_FAILED` | Giữ raw, parse vendor/message, severity theo mapping đã duyệt; incident single-hit chỉ khi rule nằm trong release | BE2 Phạm Tấn Thành (Huawei parser N42-24); BE3 Nguyễn Duy Minh (mapping N42-26, rules N42-17) | QA Ngô Châu Kiệt |
| **KB-03** | Tấn công SYN Flood dồn dập | Fortinet FortiGate | `type="traffic" action="deny"` | So sánh N-1/N/N+1 theo threshold/window/grouping đã duyệt, giữ trace event→incident | BE1 Phạm Hoàng Long (ingest N42-13/14); BE2 Phạm Tấn Thành (Fortinet parser N42-25); BE3 Nguyễn Duy Minh (rules/dedup/mapping N42-17/18/26) | QA Ngô Châu Kiệt |
| **KB-04** | Xung đột địa chỉ IP mạng nội bộ | Cisco Nexus | `IP-4-DUPADDR` | Parse IP/MAC/VLAN/interface; không gộp chéo VLAN khi contract yêu cầu phân biệt | BE1 Phạm Hoàng Long (Cisco parser N42-23); BE3 Nguyễn Duy Minh (grouping dependency N42-18) | QA Ngô Châu Kiệt |
| **KB-05** | BGP Neighbor Session Drop | Theo fixture được duyệt | `BGP_PEER_DOWN` | Đối chiếu retry/window đã chốt; hiện blocked nếu semantics chưa được duyệt | BE2 Phạm Tấn Thành (parser); BE3 Nguyễn Duy Minh (correlation) | QA Ngô Châu Kiệt |
| **KB-06** | Quá nhiệt CPU thiết bị Core | Huawei S5700 | `CPU_TEMP_ALARM` | Parse nhiệt độ/ngưỡng/severity; UI/WebSocket chỉ nghiệm thu sau khi API/UI có | BE2 Phạm Tấn Thành (parser); FE Lê Khắc Huy (UI nếu có) | QA Ngô Châu Kiệt |
| **KB-07** | Bản tin Syslog dị dạng (Malformed) | Vô danh (Unknown) | Chuỗi bytes hỏng, thiếu header | Boundary payload/PRI/encoding theo contract; giữ raw hoặc drop/error theo semantics được duyệt, không crash | BE1 Phạm Hoàng Long (receiver); BE2 Phạm Tấn Thành (parser/fallback) | QA Ngô Châu Kiệt |
| **KB-08** | Bắn tải và kiểm tra recovery | Máy tạo tải nội bộ | Đa thiết bị kết hợp từ fixture có seed | Đo sent/accepted/persisted/dropped, latency/resource/recovery; checkpoint 10 phút tách final 1 giờ | QA Ngô Châu Kiệt (generator N42-11); BE1 Phạm Hoàng Long (UDP/load N42-32); BE2 Phạm Tấn Thành (DB N42-16/31); BE3 nếu correlation trong profile | QA Ngô Châu Kiệt |

---

## 5. ĐỐI CHIẾU TIẾN ĐỘ JIRA (ẢNH CHỤP 09/11/2026)

Đối chiếu Jira sau khi xếp lịch các ticket còn thiếu: `N42-62` (BE2, hợp đồng API/Event) ở Sprint 1 vì đang chặn `N42-14`; Sprint 1 có 14 work items, 48 SP đã ước lượng và 1 ticket chưa estimate. `N42-64/65/66` (BE3, rule KB-04/05/06) ở Sprint 4; Sprint 4 có 10 work items, 33 SP đã ước lượng và 3 ticket chưa estimate. `N42-63` (FE, export) ở Sprint 6 sau `N42-34` (Sprint 3) và `N42-46` (Sprint 5); Sprint 6 có 7 work items, 28 SP đã ước lượng và 1 ticket chưa estimate. Cả 5 ticket mới vẫn `To Do`; không suy ra đã triển khai hoặc kiểm thử. Sprint assignment là kế hoạch tạm thời cho tới khi team refinement xác nhận estimate và capacity.

**Ngày và quan hệ phụ thuộc Jira (đối chiếu 09/11/2026):** 58/58 Task đã có `Start date` và `Due date`; ngày là cửa sổ kế hoạch theo sprint, không quy đổi Story Point thành ngày công. Các cửa sổ ngày làm việc là S1 09–20/11, S2 23/11–04/12, S3 07–18/12, S4 21–31/12, S5 04–15/01, S6 18–22/01 và S7 25–30/01/2027. Mốc riêng giữ theo lịch chương trình: kickoff `N42-21` ngày 09/11; báo cáo tháng `N42-29` ngày 28/11, `N42-43` ngày 26/12, `N42-56` ngày 23/01; release gate `N42-61` ngày 30/01. Jira hiện có **91 quan hệ `Blocks`**: 33 phụ thuộc kỹ thuật ban đầu, 44 liên kết xếp thứ tự công việc theo assignee và 14 blocker chéo thành viên được bổ sung sau khi rà phạm vi tích hợp/kiểm thử/release. Đã đọc lại cả 58 task; các luồng assignee liền mạch, các link chéo mới được xác nhận đúng hướng và đồ thị không có chu trình. Ví dụ các phụ thuộc chéo: ingest/parser `N42-14/23` chặn test E2E `N42-35`; API thống kê `N42-39` chặn biểu đồ FE `N42-41`; API incident `N42-46` chặn bảng FE `N42-47`; parser Fortinet `N42-25` chặn rule `N42-45`; kết quả tương quan và DB `N42-52/55` chặn tối ưu tích hợp `N42-58`, sau đó `N42-58` chặn QA tải `N42-57`, và `N42-57` chặn release gate `N42-61`. `N42-50` hiện được giao cho Ngô Châu Kiệt — QA Lead, khớp nhãn `[QA - Kiệt]`; chuỗi QA là `N42-48 → N42-50 → N42-54`, còn chuỗi TL nối `N42-49 → N42-56`. Các luật tương quan vẫn theo chuỗi `N42-64 → N42-65 → N42-66`. Đây là rà soát theo phạm vi/tiêu đề và quan hệ issue hiện có; phụ thuộc nghiệp vụ cần xác nhận lại khi refinement. Quan hệ `Blocks` hiển thị thứ tự trên Jira nhưng **không tự cấm** chuyển trạng thái khi blocker còn mở; muốn cưỡng chế cứng phải cấu hình và kiểm thử workflow validator/condition riêng. Start/due date vẫn là cửa sổ sprint, không phải lịch ngày cho từng ticket nối tiếp. `N42-49` ghi “W9” nhưng đang ở Sprint 5 (04–17/01); không tự đổi sprint/ngày khi chưa xác nhận lịch đánh giá chéo.

**Chuẩn mã KB đã thống nhất:** KB-02 = Power Supply Failure; KB-03 = SYN Flood; KB-04 = IP Conflict. Jira API đọc lại ngày 09/11/2026: summary và Description của `N42-27` đều khớp KB-03/KB-04 và trỏ đến đúng scenario/TC/RTM; trạng thái vẫn `To Do`. `N42-12` cũng vẫn `To Do`, nhưng Description đã ghi đúng KB-01 Link Flap và KB-02 Power Supply Failure. `To Do` không chứng minh đặc tả đã chạy hay QA đã nghiệm thu.

## 6. PHÂN CÔNG THEO VAI TRÒ
- **Implementation và unit/component test:** BE1/BE2/BE3/FE theo cột Code owner ở trên; người viết code tự chịu trách nhiệm kiểm thử module của mình và cung cấp build/commit, log, kết quả.
- **Khung và hồ sơ dự án:** **Phạm Minh Nhựt — TL/PM** quản lý baseline tài liệu, điều phối yêu cầu/quyết định, gán và theo dõi ticket, tổng hợp review/sign-off. TL không tự xác định contract, ngưỡng nghiệp vụ hay expected result kỹ thuật.
- **Test specification, fixture, coverage, kiểm thử tích hợp/replay và evidence:** **Ngô Châu Kiệt — QA Lead**, theo ticket Jira được giao, sau khi dependencies được merge và môi trường sẵn sàng. QA chủ trì test design và kết quả kiểm thử tích hợp; không thay implementation nghiệp vụ của BE/FE.
- **Contract và expected result kỹ thuật/nghiệp vụ:** code owner BE/FE liên quan xác nhận; yêu cầu hoặc ngưỡng thuộc sản phẩm cần người có thẩm quyền nghiệp vụ phê duyệt. TL ghi nhận quyết định đã được các owner thống nhất vào tài liệu/Jira, rồi cập nhật baseline.
- **Tình trạng hiện tại:** cả KB-01..08 là đặc tả chưa chạy; các pipeline nghiệp vụ tương ứng chưa đủ trong baseline. Không coi tiêu chí dự kiến là Pass; ghi `BLOCKED` nếu dependency/contract thiếu và `NOT RUN` cho đến khi có execution record.
- **Giao việc:** đây là owner theo module trong hồ sơ dự án, không chứng minh Jira đã assign. TL đối chiếu ticket/assignee trước khi bắt đầu; owner cập nhật Jira và evidence của phần mình.
