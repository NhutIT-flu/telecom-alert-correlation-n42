# KẾ HOẠCH KIỂM THỬ TỔNG THỂ & ĐO KIỂM TẢI 1.000 MSG/S (QA MASTER TEST PLAN)

> **Mã tài liệu:** `VNPT-NET-N42-QATP-2026-V1.2`  
> **Chủ nhiệm kiểm thử:** **Ngô Châu Kiệt — QA Lead (Module M8)**  
> **Người phê duyệt & Điều phối chung:** **Phạm Minh Nhựt — Project Manager / Team Leader**  
> **Cơ quan bảo trợ:** Trung tâm Điều hành Khai thác Mạng VNPT NET  
> **Cơ sở đào tạo:** Trường ĐH Giao thông Vận tải TP.HCM (UTH) — Học kỳ Doanh nghiệp  
> **Trạng thái:** BẢN KẾ HOẠCH KIỂM THỬ NỘI BỘ — chờ Cố vấn VNPT NET xác nhận

---

## 1. MỤC TIÊU & PHẠM VI KIỂM THỬ

1. **Kiểm thử chức năng:** Đảm bảo 100% các chức năng tiếp nhận Syslog UDP (`5514`), parser đa vendor, đệm hàng đợi, gom nhóm tương quan và dashboard real-time hoạt động đúng thiết kế kỹ thuật.
2. **Kiểm thử hiệu năng & chịu tải:** Các lần kiểm tra trung gian duy trì tải danh định **&ge; 1.000 msg/s trong ít nhất 10 phút**. Bài nghiệm thu cuối ở W13 phải duy trì **&ge; 1.000 msg/s liên tục trong 1 giờ**, không rớt gói UDP và không tràn bộ nhớ.
3. **Kiểm thử bảo mật:** Quét mã nguồn định kỳ, đảm bảo không lưu mật khẩu hoặc token hardcode. Dữ liệu chỉ dùng IP giả lập; mạng lab `10.10.0.0/16` là dải riêng RFC 1918, còn `203.0.113.0/24` là dải ví dụ tài liệu RFC 5737.

---

## 2. CHỈ TIÊU KỸ THUẬT & TIÊU CHUẨN ĐO ĐẠC TẢI 1.000 MSG/S (SLA & KPIS)

| Chỉ số (KPI) | Mục tiêu SLA | Ngưỡng cảnh báo | Đánh giá Thất bại (Fail) |
| :--- | :--- | :--- | :--- |
| **Thông lượng tiếp nhận** | **&ge; 1.000 msg/s** | 950 &ndash; 999 msg/s | &lt; 950 msg/s |
| **Thời lượng bài nghiệm thu cuối** | **1 giờ liên tục ở mức danh định** | Chỉ hoàn thành bài trung gian 10 phút | Dưới 10 phút hoặc bị gián đoạn |
| **Tỷ lệ rớt gói UDP Socket** | **0.00%** | &gt; 0.00% và &le; 0.05% | &gt; 0.05% |
| **Độ trễ xử lý P50** | **&lt; 50 ms** | 50 &ndash; 100 ms | &gt; 100 ms |
| **Độ trễ xử lý P99** | **&lt; 200 ms** | 200 &ndash; 500 ms | &gt; 500 ms |
| **Mức chiếm dụng CPU (4 Cores)** | **&le; 60%** | 60% &ndash; 75% | &gt; 75% liên tục 2 phút |
| **Mức chiếm dụng RAM** | **&le; 1.5 GB** | 1.5 &ndash; 2.0 GB | &gt; 2.0 GB (nguy cơ OOM) |

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
3. **Giai đoạn 3 (Peak Load - 10 phút):** Duy trì đều đặn **1.000 msg/s** bằng load runner do QA triển khai theo Jira; hiện chưa có runner trong baseline W1.
4. **Giai đoạn 4 (Spike Stress - 2 phút):** Đẩy đột biến lên 1.500 msg/s kiểm tra khả năng chịu lỗi và tính cơ động của bộ đệm hàng đợi (In-memory Queue).
5. **Giai đoạn hạ tải (Cool-down - 2 phút):** Giảm dần về 0, kiểm tra giải phóng tài nguyên.

Các 4 giai đoạn trên là bài kiểm tra ramp-up/checkpoint. Chúng không thay bài nghiệm thu cuối: ở W13 chạy riêng 60 phút liên tục tại ít nhất 1.000 msg/s theo `ACCEPTANCE_CRITERIA.md` và lưu số gửi/nhận, latency, CPU, RAM.

---

## 4. MA TRẬN 8 KỊCH BẢN KIỂM THỬ CHUẨN (TEST MATRIX KB-01..08)

| Mã KB | Tên kịch bản | Thiết bị nguồn | Dạng cảnh báo mô phỏng | Kết quả kỳ vọng (Pass Criteria) | Phụ trách |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **KB-01** | Bão cảnh báo Interface Flapping | Cisco Catalyst | `LINK-3-UPDOWN` & `LINEPROTO-5-UPDOWN` | Gom ít nhất 5 sự kiện cùng thiết bị/giao diện trong cửa sổ 60 giây thành 1 sự cố gốc | Kiệt (QA) |
| **KB-02** | Nguồn cấp điện dự phòng lỗi | Huawei NE40E | `POWER_SUPPLY_FAILED` | Bắn cảnh báo mức CRITICAL lên Dashboard lập tức | Kiệt (QA) |
| **KB-03** | Tấn công SYN Flood dồn dập | Fortinet FortiGate | `type="traffic" action="deny"` | Lọc khử trùng, tổng hợp tần suất theo IP nguồn | Kiệt (QA) |
| **KB-04** | Xung đột địa chỉ IP mạng nội bộ | Cisco Nexus | `IP-4-DUPADDR` | Trích xuất chính xác MAC và Interface gây xung đột | Kiệt (QA) |
| **KB-05** | BGP Neighbor Session Drop | Juniper MX | `BGP_PEER_DOWN` | Nhận diện đứt kết nối ngang hàng sau 3 lần retry | Kiệt (QA) |
| **KB-06** | Quá nhiệt CPU thiết bị Core | Huawei S5700 | `CPU_TEMP_ALARM` | Kích hoạt cảnh báo mức MAJOR, gửi WebSocket | Kiệt (QA) |
| **KB-07** | Bản tin Syslog dị dạng (Malformed) | Vô danh (Unknown) | Chuỗi bytes hỏng, thiếu header | Ghi log `unknown_format`, không làm sập tiến trình | Kiệt (QA) |
| **KB-08** | Bắn tải đột biến 1.500 msg/s | Máy tạo tải nội bộ | Đa thiết bị kết hợp ngẫu nhiên | Socket buffer 4MB hấp thụ 100%, tỷ lệ rớt 0% | Kiệt (QA) |

---

## 5. PHÂN CÔNG THỰC HIỆN KIỂM THỬ
- **Chủ nhiệm QA & Test Execution:** **Ngô Châu Kiệt** (Soạn kịch bản, chạy benchmark, tổng hợp log, kiểm tra lỗi).
- **Phê duyệt & Hạ tầng CI/CD:** **Phạm Minh Nhựt** (Team Leader / PM, thiết lập GitHub Actions, phân phối nhiệm vụ Jira).
