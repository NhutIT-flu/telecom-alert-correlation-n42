# Thiết kế chi tiết rule LinkFlap

Ngày: 2026-11-20. Trạng thái: đề xuất; bổ sung coverage, history context, owner revision và eviction recovered theo constitution 2.0.0. [Đặc tả nghiệp vụ](spec.md).

## 1. Phạm vi và ranh giới sở hữu

| Nguồn chuẩn | Nội dung |
|---|---|
| Feature 004 — tài liệu này | Đếm chuyển UP↔DOWN, ngưỡng/cửa sổ, state riêng, horizon tính bù, kết thúc UP/DOWN, chính sách prune/evict và mô hình tải LinkFlap |
| [Dữ liệu 001](../001-alert-data-model/data-model.md) | events/raw, rules snapshot, alerts, bằng chứng, history và checkpoint dùng chung; không thêm bảng LinkFlap |
| [Vòng đời 002](../002-alert-lifecycle/lifecycle-design.md) | signal/workflow, ACK/CLOSE, tái phát và audit/correction |
| [Engine 003](../003-rule-dispatch-correlation/engine-design.md) | Registry/Dispatcher, hợp đồng 5 thao tác, sắp thứ tự/watermark, lịch chung, giao dịch/checkpoint và CleanupManager |

Một evaluator cho mỗi revision cấu hình trong worker, nhiều group state. Không tạo instance rule, tiến trình, thread hoặc timer hệ điều hành riêng cho mỗi interface. Lịch chỉ là deadline trong scheduler chung. Không gửi frontend trực tiếp; công bố sau commit qua phần API/thông báo của hệ thống. LinkDown độc lập.

## 2. Đăng ký và cấu hình

Ví dụ file JSON đã bổ sung điều kiện link flap hiện tại; vẫn tắt vì đây là tài liệu, chưa có code/test được nghiệm thu:

```json
{
  "rule_key": "interface_link_flap",
  "version": 1,
  "name": "Interface link flap",
  "handler_key": "link_flap",
  "handler_revision": "1",
  "enabled": false,
  "alert_severity": 4,
  "definition": {
    "subscribed_event_types": [
      "interface_state_change"
    ],
    "group_by": [
      "device_id",
      "interface_name"
    ],
    "parameters": {
      "window_seconds": 60,
      "min_transitions": 5,
      "interface_layer": "physical"
    },
    "recovery": {
      "mode": "quiet_period",
      "quiet_seconds": 60
    }
  }
}
```

Cấu hình này kết thúc điều kiện flap khi 60 giây không ghi nhận chuyển mới, trả outcome theo trạng thái cuối: flap_stopped_up hoặc flap_stopped_down. Không chờ UP để kết thúc flap ở DOWN. Đây là suy luận theo dữ liệu đã nhận và mốc chốt an toàn, không phải kiểm tra trực tiếp thiết bị; không tự ACK/CLOSE và không tạo LinkDown.

Rule không đủ schema/điều kiện vẫn bị chặn bật. Ví dụ này không còn recovery=null; enabled=false chỉ ngăn hiểu nhầm tài liệu đã triển khai. Bản nháp chưa công bố có thể hoàn thiện; snapshot đã công bố chỉ thay bằng revision mới.

Khóa nhóm đầy đủ là (rule_key, config_version, handler_revision, correlation_scope, device_id, interface_name); lớp tín hiệu cố định trong revision cấu hình. Nếu một cấu hình thực sự xử lý nhiều lớp thì phải đưa lớp vào identity trước công bố, không trộn state. rules.id đại diện revision khi lưu; group_values chứa đúng group_by. Không thay device_id bằng hostname hoặc sender_ip.

Trường cần: event_id, event_type=interface_state_change, event_time/time_status đáng tin cậy, received_at, device_id, correlation_scope, interface_name, interface_state UP/DOWN, interface_layer. Chỉ lớp đã chọn góp vào chuỗi; thiếu trường thì skip có lý do, không tạo nhóm NULL hoặc tự parse raw.

Schema LinkFlap kiểm tra window_seconds/min_transitions/quiet_seconds là số nguyên dương (không nhận boolean như số), interface_layer thuộc tập hỗ trợ, recovery.mode=quiet_period và đúng kiểu/field được phép. group_by phải gồm device_id và interface_name; subscription phải tương thích handler. Bộ thông số hiện tại là 60/5/physical/quiet 60; thay thông số tạo revision mới theo 003. Đệm 3 giây thuộc engine, không thêm vào quiet_seconds.

## 3. Điều kiện, state và thuật toán

### 3.1. Điều kiện đã chọn

- Cùng thiết bị–interface–lớp tín hiệu: mỗi UP↔DOWN có căn cứ là một lần, không phải một chu kỳ hoàn chỉnh.
- Phát sinh khi có ít nhất 5 lần chuyển trong (T-60 giây,T]. Quan sát đầu chưa biết trạng thái trước chỉ làm baseline.
- UP→UP/DOWN→DOWN không tăng count nhưng vẫn được giữ/xét như quan sát cần thiết. Không kết thúc evaluate sớm chỉ vì interface hoặc alert chưa đổi.
- Phục hồi điều kiện flap khi 60 giây không ghi nhận chuyển mới, đã chốt được dữ liệu và pipeline/đồng hồ đủ an toàn. Outcome cố định của handler: flap_stopped_up hoặc flap_stopped_down. Cả hai đề nghị RECOVER, giữ workflow của người giám sát.
- Đứng yên ở DOWN không giữ flap active mãi. LinkDown là rule độc lập; LinkFlap không tạo/chỉ đạo LinkDown.
- Một log UP, số mốc giảm dưới 5 hoặc hành động dọn cache không tự đủ điều kiện RECOVER.

### 3.2. Cập nhật khi có quan sát đã sắp thứ tự

1. Tra/nạp state đúng revision/group/scope. Thiếu field/thời gian có căn cứ thì skip có lý do, giữ raw.
2. Cập nhật quan sát. Chưa có baseline thì khởi tạo; khác trạng thái trước thì tạo một transition, giống thì không tăng count.
3. Loại mốc ngoài (T-60,T] và ngoài chu kỳ hợp lệ. Mỗi transition giữ time và event_id.
4. Xét ngưỡng và điều kiện kết thúc có liên quan, kể cả khi không tăng count; trả state/kết luận, không tự ghi DB.
5. Lifecycle tạo/cập nhật alert chưa đóng cùng khóa; không sinh alert mới cho mỗi lần ngưỡng còn đúng.

| Thời gian nguồn | Trạng thái | Mốc chuyển còn trong khoảng xét | Kết quả ngưỡng |
|---|---|---|---|
| 0 | UP | Rỗng | Baseline |
| 5 | DOWN | 5 | Chưa đủ |
| 6 | DOWN | 5 | Lặp, vẫn cập nhật quan sát |
| 8 | UP | 5,8 | Chưa đủ |
| 13 | DOWN | 5,8,13 | Chưa đủ |
| 16 | UP | 5,8,13,16 | Chưa đủ |
| 21 | DOWN | 5,8,13,16,21 | Đủ 5, đề nghị ACTIVATE |

Chọn một lớp tín hiệu, ví dụ physical; không cộng LINEPROTO và LINK thành hai lần của cùng một thay đổi. Nếu định nghĩa nhiều lớp phải phân biệt khóa hoặc phiên bản cấu hình, không tự gộp alias.

### 3.3. State phải đủ cho tính bù

| Phần | Vai trò |
|---|---|
| Baseline trước khoảng cần dựng lại | Trạng thái/time/event_id ngay trước đoạn; không thay bằng last_state mới nhất |
| Quan sát đã chốt trong vùng sống | UP/DOWN và thời gian/ID, gồm cả quan sát không thêm transition |
| Bộ đệm ngưỡng tối đa 5 mốc | Đường tính nhanh trên chuỗi đã chốt, không phải toàn bộ checkpoint |
| Mốc chuyển gần nhất và giai đoạn nội bộ | Đặt lịch kết thúc, phân biệt tích lũy/flap/đã kết thúc |
| Ranh giới chu kỳ hợp lệ | Không dùng lại bằng chứng trước lần kết thúc còn hợp lệ |
| Phiên bản state/checkpoint | Khôi phục đúng logic và chống áp dụng lại |
| Pending trước chốt | Engine quản lý; event vẫn pending trong DB cho đến xử lý hoàn tất |

Quan sát vùng RAM khoảng 60+3 giây cộng baseline là vùng làm việc, không phải cam kết đủ mọi lịch sử để tính lại. Khi cần, engine đọc thêm DB theo mục 4 của tài liệu này. Bộ đệm 5 mốc không cho số tổng chính xác và không đủ phát hiện hai transition bị che bởi một log trễ chèn giữa hai UP.

### 3.4. Kết thúc theo thời gian

Khi coverage liên tục đủ, nếu last_transition_at=20, rule đặt next_check_at=80 theo thời gian nguồn. Engine gọi on_time khi watermark>=80; trong ví dụ đồng hồ đồng bộ, không backlog, khoảng xử lý sớm là giây 83. Rule không cộng thêm 3 giây lần nữa.

Engine áp dụng mọi event đã đủ chốt tại mốc đó trước timer. Một chuyển mới đúng giây 80 làm dời hạn, không tạo RECOVER thoáng qua rồi ACTIVATE. Công việc hẹn state cũ bị bỏ bằng kiểm tra checkpoint/cache generation.

Không có log mới không đồng nghĩa thiết bị bình thường. RECOVER quiet_period chỉ có nghĩa điều kiện flap đã kết thúc theo quan sát. Khi pipeline lỗi/tồn đọng ảnh hưởng nhóm hoặc căn cứ thời gian không an toàn, không tiến mốc để kết luận khoảng yên. Không có một timer/thread riêng cho mỗi interface; chỉ có dữ liệu deadline do bộ lập lịch chung quản lý.

### 3.5. Chu kỳ và hiệu chỉnh

Một RECOVER hợp lệ mở ranh giới chu kỳ mới; tái phát bình thường phải đủ lại 5 transition mới. Nếu log trễ chứng minh RECOVER trước đó không hợp lệ thì đó là hiệu chỉnh episode cũ, không được dùng ranh giới sai để bỏ bằng chứng hoặc đòi thêm 5 transition. Alert chưa đóng được phục hồi nhận định active theo bản tính lại có chứng cứ; giữ audit và ACK. Alert đã closed vẫn bất biến theo mục 4 và vòng đời 002.

## 4. Thời gian nguồn và tính bù của LinkFlap

### 4.1. Đệm và mốc chốt

event_time dùng để xác định UP/DOWN và cửa sổ; received_at đo tiếp nhận/độ trễ. Sắp trong cùng nhóm theo thời gian nguồn; timestamp bằng nhau chỉ dùng thứ tự nguồn nếu nguồn thực sự cung cấp căn cứ, không dùng event_id/arrival order để đoán.

Engine giữ log chưa chốt khoảng 3 giây. Khi có clock UTC/ngữ cảnh nguồn đủ tin cậy và không backlog chưa xử lý ảnh hưởng, mốc tham chiếu là now_UTC-3 giây; engine phải xử lý các event đủ điều kiện trước khi chạy timer đến mốc đó. Mốc vẫn tiến khi im lặng, không phụ thuộc việc có một log tiếp theo. Watermark không là lời hứa rằng không còn log cũ nào đến nữa.

Thời gian nguồn unknown, quá tương lai hoặc clock mâu thuẫn phải có diagnostic/điều kiện chặn; không giữ vô hạn trong heap rồi coi đó là dữ liệu trễ bình thường. Pipeline/thời gian chưa an toàn không dùng khoảng im lặng để RECOVER. Không cộng 3 giây ở cả rule lẫn scheduler.

### 4.2. Phạm vi hiệu chỉnh

Vùng sống tại watermark F là (F-60,F], cộng các quan sát chưa chốt và baseline gần nhất trước đầu vùng. Log quá 3 giây được kiểm tra:
- Nếu nằm trong vùng sống hoặc thay baseline/transition có thể ảnh hưởng vùng, tính bù đúng nhóm.
- Nếu không còn ảnh hưởng, giữ raw và đánh dấu late_out_of_horizon; không phát lại mọi incident lịch sử.
- Nếu dữ liệu/clock không đủ, đánh dấu correction_incomplete hoặc ordering_ambiguous; không suy ra count=0 hay phục hồi.

Cache khoảng 63 giây + baseline không đủ để xét mọi cửa sổ kết thúc ở một thời điểm quá khứ: cửa sổ đó cần thêm 60 giây trước chính nó. Engine đọc thêm DB từ trước transition bị ảnh hưởng sớm nhất một W và một baseline, cùng lịch sử/ràng buộc episode đang theo dõi. Với endpoint trong vùng sống, phần lookback thường tới khoảng hai W trước F; không cố định mọi truy vấn ở 63 giây và không quét toàn DB cho mọi log.

### 4.3. Quy trình tính bù

1. Chốt snapshot đang có và vùng ảnh hưởng; chọn đúng rule revision/scope/group/lớp. Chỉ dùng dữ liệu đã áp dụng hoặc batch đang đánh giá; pending khác chưa chốt không tự trở thành bằng chứng đã xử lý.
2. Nạp baseline và quan sát cần thiết, chèn theo event_time. Quan sát không thêm count vẫn quan trọng: 50 UP,60 UP có thể thành 50 UP,55 DOWN,60 UP, lộ hai transition.
3. Dựng lại từ baseline, không cộng chuỗi DB vào buffer checkpoint đã chứa nó. Xét mọi endpoint bị ảnh hưởng, không chỉ cửa sổ kết thúc tại timestamp log đến trễ.
4. Dùng mode=rebuild; phát lại event và deadline trong thứ tự nguồn trên state tạm. Deadline d<t được xét trước event tại t; mọi event đúng d được xét trước timer d. Handler trả đề nghị nhưng không có IO; không ghi thông báo/lịch sử trung gian một cách máy móc.
5. So với kết quả đã công bố. Kết luận mới có chứng cứ có thể tạo alert phát hiện muộn, bổ sung bằng chứng, đổi outcome hoặc sửa nhận định của alert chưa đóng. effective_at có thể cũ hơn created_at, không ghi lùi thời gian hệ thống.
6. Ghi correction source, before/after, reason, bằng chứng và phiên bản trong cùng giao dịch state/progress. Nếu facts không đổi thì không thêm audit có ý nghĩa hoặc version.
7. Nếu RECOVER cũ bị vô hiệu, lấy ranh giới chu kỳ hợp lệ trước đó và giữ episode chưa đóng, không đòi mới 5 lần sau ranh giới sai. Nếu ACTIVATE cũ không còn chứng minh được mà chưa có kết luận kết thúc hợp lệ, đánh dấu evidence_review_required, không tự xóa/hủy/đóng chỉ vì count<5.
8. Không sửa alert đã closed; ghi late_conflict_closed ở diagnostic sự kiện và giữ bằng chứng để xem riêng. Mô hình chưa có trạng thái hủy hoặc tái dựng toàn lịch sử.

Chỉ 5 transition timestamp không thể làm bước 2/3. Chi phí tăng theo số quan sát vùng liên quan và số log trễ, nên cần đo lại RAM/CPU; các microbenchmark N=3 ở mục 6 không đại diện phương án hoàn chỉnh.

### 4.4. Ví dụ kiểm chứng

Baseline 0 UP; đã biết 10 DOWN,20 UP,40 DOWN,50 UP,60 UP: có 4 transition. Nhận trễ 55 DOWN làm chuỗi có transition 10,20,40,50,55,60; ngưỡng 5 đạt lần đầu tại 55. Cửa sổ kết thúc tại 60 cũng bị ảnh hưởng.

Trường hợp chỉ minh họa các transition đã xác định: 10,30,40,50 mới có 4; chèn 15 làm 5 tại endpoint 50. Chỉ đánh giá tại 15 sẽ bỏ sót. Với raw UP/DOWN phải dựng lại trạng thái, không tự coi mỗi log là một transition.

### 4.5. Baseline ngoài vùng sống và lookback

- Tại F=100, vùng sống là (40,100]. Đã biết 20 UP,50 UP,60 DOWN,70 UP,80 DOWN,90 UP: có 4 chuyển trong vùng. Log trễ 35 DOWN thay baseline trước vùng, làm lộ chuyển 50 UP và đủ 5 tại 90. Không được bỏ chỉ vì 35 nằm trước 40.
- Đã biết 0 UP,10 DOWN,20 UP,30 DOWN,40 UP,50 UP,70 DOWN: chưa đủ 5 trong các cửa sổ liên quan. Chèn 45 DOWN làm ngưỡng đạt lần đầu ở 45. Dù tại F=100 cửa sổ hiện tại có ít hơn 5, vẫn cần xét endpoint quá khứ bị ảnh hưởng; lấy thêm các quan sát trước cache và baseline, không giới hạn truy vấn ở 63 giây.
- Cùng timestamp có trạng thái khác nhau mà không có sequence nguồn đáng tin cậy: ordering_ambiguous, không tự dùng event_id/thứ tự nhận quyết định cạnh.

## 5. Tích hợp hợp đồng và chính sách dọn

Hợp đồng và cơ chế gọi chỉ được định nghĩa tại 003 mục 11; bảng này là cách LinkFlap đáp ứng hợp đồng đó.

| Thao tác | Chính sách LinkFlap |
|---|---|
| initial_state | Unknown khi thật sự không có checkpoint/baseline; lỗi restore không được biến thành cửa sổ rỗng |
| evaluate | Xử lý mục 3; log lặp vẫn cập nhật/xét; log trễ dựng lại vùng mục 4 qua engine |
| on_time | Khi watermark đủ deadline, quiet 60 giây và dữ liệu an toàn: RECOVER với outcome UP/DOWN nếu có episode active |
| prune_state | Bỏ mốc hết hạn khi không còn cần cho ngưỡng/tính bù; giữ baseline/đường nạp lại, ranh giới và chứng cứ |
| can_evict_state | Chỉ đề nghị khi không còn dữ liệu cần giữ nóng; recovered chưa closed có thể cold-load, active giữ nóng; engine áp mọi guard |

Còn 4 transition hợp lệ thì giữ; count<5 không là lý do xóa. Chỉ tích lũy dưới ngưỡng rồi hết hạn thì không sinh RECOVER. Entry có cảnh báo active giữ nóng. Recovered chưa closed được evict nếu next_check_at=NULL và đầy đủ guard/cold-load theo 003 mục 18. Prune không đổi tín hiệu.

Điều kiện cuối do CleanupManager 003 kiểm tra: không pending/in-flight/cảnh báo active, đủ idle, checkpoint sạch/an toàn và generation còn đúng. Lỗi lưu hoặc cập nhật mới hủy thu hồi. Chỉ bỏ RAM, không xóa events/checkpoint/history; khôi phục không cộng lại observations đã có.

Chu kỳ dọn 5 giây và idle 60 giây lấy từ mặc định đề xuất của engine, không phải tham số đếm/kết thúc LinkFlap. Hết hạn transition dùng watermark nguồn; idle dùng clock đơn điệu. Log lặp không kéo dài tuổi transition nhưng có thể giữ cache nóng. Timer phục hồi không chờ đến lượt dọn.

### 5.1. Timeline dọn nhóm chưa đạt ngưỡng

Giả sử thời gian sinh/nhận trùng nhau, không backlog, đã có baseline UP. Các transition ở giây 5,10,20 (mới 3 lần).

| Thời gian engine | Mốc/việc | Kết quả |
|---|---|---|
| 80 | watermark=77 | Transition 20 còn trong (17,77], không evict |
| 83 | watermark=80 | 20 ra khỏi (20,80], cửa sổ ngưỡng rỗng |
| 85 | Lượt dọn, idle đủ, checkpoint sạch, không alert | Bỏ cache, giữ dữ liệu bền vững |
| 90 | Nhận UP mới | Vào reorder; không tự coi là quan sát đầu |
| 93 | Chốt UP 90 | Nạp baseline DOWN 20, ghi nhận một transition tại 90 |

Nếu có log trễ sau evict, nạp checkpoint và quan sát/baseline liên quan, dựng lại một lần; không cộng vào cả checkpoint cũ lẫn bản rebuild. Trạng thái mới nhất không thay thế baseline đầu khoảng.

Checkpoint dùng rule_group_states chung với payload đủ các phần mục 3.3 và next_check_at nguồn. Không lưu ACK/CLOSE trong payload như nguồn chuẩn. Sau eviction, khôi phục baseline gần đoạn cần dựng lại, không chỉ last_state mới nhất; pending chưa chốt không được coi là đã áp dụng.

## 6. Mô hình tải và tài nguyên

Giả định mỗi interface UP đúng 5 giây, DOWN đúng 3 giây, mỗi lần chuyển một log liên quan:

| Chỉ số | Giá trị |
|---|---|
| Chu kỳ | 8 giây, 2 lần chuyển |
| 1 interface trong 1 giờ | 450 chu kỳ, 900 lần chuyển |
| 1.000 interface | 900.000 lần chuyển/giờ, trung bình 250/giây |
| Đồng bộ thời điểm | Đợt 1.000 log sau mỗi quãng 3 hoặc 5 giây |
| Raw giả định 500 byte/log | 450.000.000 byte, khoảng 450 MB/giờ, chưa có chuẩn hóa/index/WAL/evidence/checkpoint |

Nếu thời gian UP/DOWN dài hơn thì trung bình giảm; nếu nhiều raw log/lần chuyển thì lưu lượng collector tăng theo hệ số đó, còn rule phải tránh đếm lặp cùng tín hiệu. Cần baseline UP trước giờ thử, không tính là một lần chuyển trong giờ.

Số tham khảo lịch sử từ phép mô phỏng bộ đếm ngưỡng cũ N=3, không phải state đầy đủ N=5 + tính bù hiện tại, CPython 3.14.2 64-bit: 1.000 state với deque 3 tuple(timestamp,event_id), dict state và tham chiếu alert dạng số giữ khoảng 1,81 MiB; chưa gồm group keys dựng sẵn và toàn bộ process. Có thể dùng khoảng 2 MiB như ước lượng phần state tối giản, không phải ngân sách worker.

Mô phỏng 900.000 cập nhật trên các state này có median khoảng 0,3125 giây CPU cộng dồn trong ba lượt; KHÔNG gồm parser, dispatcher đầy đủ, phục hồi, DB, checkpoint, bằng chứng, HTTP hay thông báo. Không dùng kết quả đó để cam kết %CPU hoặc cấu hình máy production. Nhiều rule/state phức tạp có chi phí khác; không có tiền vận hành ước tính khi chưa biết host và thời hạn lưu.

RAM không nhân với 3.600 giây khi state có giới hạn. CPU/tổng ghi tăng theo E×k (E là sự kiện, k là số rule ứng viên trung bình), cửa sổ phức tạp có thêm chi phí riêng. Số nhóm trong cache, kích thước state, checkpoint, evidence và batch quyết định chi phí thực. Một alert chưa đóng mỗi group không có nghĩa chỉ có 1.000 dòng ghi trong cả giờ.

## 7. Ca kiểm chứng và đối chiếu engine

| Mã | Tình huống | Expected result |
|---|---|---|
| LF01 | Quan sát đầu và trạng thái lặp | Baseline đầu không tính; lặp không tăng count. |
| LF02 | LINK/LINEPROTO cùng thay đổi | Chọn đúng lớp, không cộng đôi. |
| LF03 | Các mốc 10,20,30,40,50,85; N5/W60 | Đạt tại 50; tại 85 còn 30,40,50,85, không tự recovery chỉ vì count<5. |
| LF04 | Mốc đúng T-W | Loại khỏi cửa sổ; đủ đúng N thì đạt. |
| LF05 | 1.000 nhóm chạy 1 giờ | Bộ đệm ngưỡng N5 <=5.000 mốc; đo thêm quan sát/baseline/reorder, raw đủ 900.000 lần chuyển. |
| LF06 | Dừng sau bốn lần chuyển rồi lần thứ năm | Đạt một lần đúng bằng chứng. |
| LF07 | Log không thêm transition | Cập nhật quan sát, vẫn xét điều kiện có liên quan, không early-return toàn rule. |
| LF08 | Chèn 55 DOWN giữa 50 UP,60 UP | Hai transition mới; xét cửa sổ mới hơn log đến trễ. |
| LF09 | Log trước đầu cửa sổ đổi baseline | Tính lại transition đầu đúng, không chỉ kiểm tra timestamp bên trong. |
| LF10 | Cần cửa sổ kết thúc quá khứ bị ảnh hưởng | Đọc thêm lookback và baseline; không coi cache 63 giây là đủ mọi trường hợp. |
| LF11 | Quiet 60 giây, cuối UP hoặc DOWN | Hai outcome RECOVER riêng, không tạo LinkDown, không ACK/CLOSE. |
| LF12 | Chỉ tích lũy dưới ngưỡng rồi cửa sổ rỗng | Không sinh RECOVER nếu chưa có episode; có thể prune/evict an toàn. |
| LF13 | Correction hủy tính hợp lệ recovery cũ | Bỏ ranh giới sai, phục hồi nhận định episode chưa đóng và audit, không đòi 5 mốc sau ranh giới sai. |
| LF14 | Còn 4 transition hợp lệ | Không xóa chỉ vì chưa đạt 5. |
| LF15 | Dọn ở mốc 83/85 rồi UP 90 chốt 93 | Nạp DOWN trước đó, đếm một transition, không mất baseline. |
| LF16 | Log trễ trước vùng sống làm đổi baseline | Dựng lại cạnh đầu và xét endpoint liên quan; ví dụ ở mục 4.5 phải đủ ngưỡng tại endpoint 90. |
| LF17 | Đạt ngưỡng quá khứ cần lookback trước cache | Tìm lần đạt 5 tại 45, không kết luận không flap chỉ vì cửa sổ hiện tại dưới ngưỡng. |
| LF18 | Transition đúng deadline và backlog có event mới hơn deadline | Dùng lịch chung 003: tại cùng mốc event trước timer; timer cũ hơn event chạy trước, giữ đủ lịch sử. |
| LF19 | Pipeline/time không an toàn, timestamp trùng mâu thuẫn | Diagnostic, không suy thứ tự nhận hoặc quiet recovery. |
| LF20 | Cùng ID thử lại, restore, timer lặp, correction bản closed | Không nhân đôi; bản closed bất biến; diagnostic theo 002/003. |
| LF21 | Field cũ state và interface_layer thiếu/sai | Theo adapter 005; đủ căn cứ mới đếm, không đoán physical |
| LF22 | Gap 30–100, last transition20, quiet60 | Không recover80; safe_since100 thì effective sớm nhất160 |
| LF23 | Chỉ worker restart, dữ liệu/coverage liên tục đủ | Dựng lại đúng thứ tự, không tự tạo gap hoặc đếm đôi |
| LF24 | Recovered evict rồi tái phát/CLOSE | Giữ id/ACK nếu chưa đóng; bản closed bất biến |
| LF25 | Revision mới bật khi state cũ cold | Resolver tìm owner cũ từ DB, không mở alert revision mới song song |
| LF26 | Yêu cầu lịch sử thiếu/lặp/vượt hạn mức | NEEDS_HISTORY hữu hạn; INCOMPLETE giữ kết quả trước, không count=0 |


Các ca này được chuyển/tách từ bộ C của 003; kiểm chứng chung về giao dịch, handler, fan-out, lịch và quyền sở hữu vẫn ở 003. Đây là yêu cầu cho test triển khai, chưa chạy trên ứng dụng.

SC-001 ↔ LF01–04; SC-002 ↔ khóa/field mục 2 và ca nhóm C của 003; SC-003 ↔ LF07–10, LF16–17, LF19–20; SC-004 ↔ LF11–13, LF18–19; SC-005 ↔ LF06, LF13–15, LF20; SC-006–008 ↔ LF05, mục 6 và phép đo đầy đủ của 003. Các mục SC-007 là mục tiêu đề xuất, không phải số đo.

## 8. Binding vận hành của LinkFlap

### 8.1. Projection và state payload v1

Đầu vào theo [005 mục 2](../005-monitoring-integration/integration-design.md):
interface_name là string chuẩn, interface_state là UP/DOWN, interface_layer là physical/protocol.
Bản mẫu chỉ đếm physical. Không tự đổi alias hoặc cộng LINEPROTO vào LINK.

State handler v1 gồm:

- phase: unknown/tracking/flapping/recovered, là giai đoạn thuật toán, không phải workflow.
- baseline: NULL hoặc observation có event_id, event_time, interface_state và lớp.
- observations: chuỗi đã chốt cần cho dựng lại, gồm log lặp; mỗi phần tử cùng shape baseline.
- threshold_transitions: tối đa min_transitions phần tử (event_id,event_time,from_state,to_state);
  các quan sát trước/sau chứng minh cạnh phải còn hoặc nạp lại được.
- last_observation và last_transition (nullable khi chưa có); giữ tham chiếu log thật.
- episode_boundary: mốc phục hồi còn hợp lệ và history version tham chiếu nếu có.
- last_outcome: NULL/flap_stopped_up/flap_stopped_down; không chứa ACK/CLOSE như nguồn chuẩn.

Envelope engine/coverage và cột next_check_at theo 003 mục 14; schema kiểm tra thứ tự,
ID, lớp, UTC và size. Bộ đệm N không là tổng transition count chính xác.

### 8.2. History policy

Horizon hiện tại W=60 giây, lookback thêm W trước điểm kết luận bị ảnh hưởng và một
baseline trước đoạn; phải có episode boundaries và coverage của đoạn dựng lại.
Log trước vùng sống có thể thay baseline nên không loại chỉ dựa timestamp.
Engine nhận history_request, nạp observations theo group/lớp/scope và trả HistoryContext.
Tối đa vòng/số quan sát/query timeout theo 003; không đủ thì INCOMPLETE, giữ kết quả
đã commit, diagnostic correction_incomplete và chặn quiet liên quan cho tới khi giải quyết.

### 8.3. Deadline có coverage

Khi safe_since đã biết, deadline=max(last_transition_at+60, safe_since+60).
Nếu coverage liên tục đủ từ trước last_transition, ví dụ20→80 vẫn giữ nguyên.
Gap30–100 không dựng lại được: safe_since=100, deadline=160; tại160 mọi event đủ chốt
được xét trước timer, khoảng ghi sớm ~163 trong ví dụ chuẩn. safe_since unknown:
không RECOVER, wake theo thay đổi health/input thay vì lặp timer quá hạn liên tục.
Health healthy không chứng minh UDP không mất gói; outcome vẫn là hết flap theo log đã nhận.

### 8.4. Owner và eviction

Nhóm recovered chưa closed có thể evict khi không còn dữ liệu cần giữ nóng, deadline NULL,
không pending/in-flight, checkpoint/baseline/ranh giới đủ và idle/generation đúng.
Nạp lại phải tìm alert owner theo rule_key trong DB trước khi xét; cache cũ không ghi đè CLOSE.
Bật revision mới không tạo buffer mới song song cho nhóm còn alert cũ.
Khi owner chuyển sau closed, chỉ tính transition sau cả mốc kích hoạt revision mới và
ranh giới phục hồi hợp lệ; baseline trước ranh giới không tự tính một lần chuyển.
