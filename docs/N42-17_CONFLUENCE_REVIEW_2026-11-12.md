# Đối chiếu N42-17: Confluence, mã triển khai và đề xuất N42-18

**Ngày rà:** 2026-11-12 · **Múi giờ:** Asia/Saigon
**Trạng thái:** báo cáo review nội bộ; không phải quyết định thiết kế hoặc nghiệm thu.
**Mục đích:** xác định phần cần bổ sung để hoàn thiện N42-17, không tự mở rộng ticket thành engine.

## 1. Kết luận và phạm vi bằng chứng

N42-17 đã hiện thực bộ cấu hình mẫu, schema và loader YAML độc lập tại commit
`883d048ea1b3a0f39ef4e608cda6fe2721571477`. Bộ test cục bộ có 25 ca cấu hình
và 2 ca health PASS. Chưa có bằng chứng trong nguồn đã đọc để kết luận N42-17
đã được QA nghiệm thu hoặc đã merge; Jira hiện ghi **Code Review**.

Phần còn thiếu đáng ưu tiên là contract cấu hình thống nhất, field/taxonomy giữa parser và
rule, fixture nguồn kép, semantics Link Flap, truy vết FR/TC/Jira và sign-off.
Không lấy việc chưa có engine, hot reload hoặc cache dedup làm lý do tự động mở rộng N42-17.

Đã truy xuất toàn bộ **61 trang current** được CQL trả về cho tài khoản trong lần rà:
**46 trang liên quan N4.2** (36 trong space OTHER, 10 bản sao/trang dự án ở space cá nhân)
và 15 trang hệ thống, mẫu hoặc trống không dùng làm căn cứ nghiệp vụ.
Không còn trang phân trang tiếp theo. Đã tìm đối chiếu trên toàn bộ nội dung Markdown
thu được, không chỉ tiêu đề/snippet tìm kiếm. Danh mục phiên bản nằm ở phụ lục A.

Đã kiểm kê **19 attachment metadata**; có ảnh sơ đồ và ảnh trang trí, không thấy
schema/OpenAPI YAML/JSON trong kết quả attachment đã được index. Không kết luận rằng
artifact Git hoặc attachment chưa được index không tồn tại. Ảnh nhị phân không được
download/rà trực quan trong đợt này; kết luận dựa vào phần văn bản và mã Mermaid của trang.

Đã đọc cả footer/inline comments trên 6 trang quan trọng: Decision Log, Tech Spec,
KB-01, KB-02, TCS và Blueprint; các kết quả đều rỗng. Jira N42-17 có một bình luận
Automation liên kết PR #5, không phải xác nhận của QA/TL.
Link báo cáo lịch sử page `5046496` được chat cũ nhắc đến trả **404**, không sử dụng
làm evidence. Phạm vi này không bao gồm lịch sử mọi revision, trang archived/draft,
nguồn bị giới hạn quyền hoặc trao đổi ngoài hệ thống.

Bản trả lời trước đã được lưu nguyên văn ở
[N42-17_N42-18_PROPOSAL_2026-11-12.md](N42-17_N42-18_PROPOSAL_2026-11-12.md).
Nội dung đó là bản lưu lịch sử; các hiệu chỉnh khuyến nghị mới nằm trong báo cáo này.

## 2. Nguồn ưu tiên và baseline mã

Theo [Document Control v6](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3408058):
quy trình HKDN chính thức → quyết định đã được chốt → Charter/AC → thiết kế và RTM.
Jira quyết định owner, scope, hạn và trạng thái thực tế. Ghi DRAFT, mẫu tham khảo hoặc
“đã xác minh mô tả Jira” không đồng nghĩa đã phê duyệt nội dung kỹ thuật.

| Nguồn mã | Commit được đọc | Phạm vi |
|---|---|---|
| N42-17 | `883d048ea1b3a0f39ef4e608cda6fe2721571477` | Schema, YAML, loader, tests, bản nháp |
| Parser N42-15 | `aa6dc2feaafcbcd274064a270ca48004b81aab4b` | AlertEvent, parser RFC3164 |
| QA N42-12 | `a6bb50eb86cfc36726bd1752df757f497d548d55` | KB-01/02 và các hồ sơ liên quan |
| main/ref cục bộ | `1a12b225f407bf022aed00bcce6315eefbba57d4` | CI, parser và dependency hiện có |

File parser/model tại ref N42-15 và ref main nêu trên không có diff.
Không fetch remote trong đợt rà, vì vậy đây là ref có sẵn trên máy, không phải cam kết
rằng nó là trạng thái GitHub mới nhất.

Workspace bắt đầu ở nhánh N42-17 và đã được chuyển sang main trong lúc rà bởi thao tác
ngoài lượt công việc này. Trợ lý không thực hiện checkout/merge; các kết luận về N42-17
được ghim vào commit bất biến. Các đường dẫn mã trong báo cáo là đường dẫn **tại ref**,
không khẳng định file hiện có trên checkout main.

## 3. Ma trận hiện thực N42-17

| Thành phần tại 883d048 | Đã có | Giới hạn phải ghi khi bàn giao |
|---|---|---|
| `app/models/rule_config.py` | Strict types; extra forbid; số nguyên >0; group/rule ID duy nhất; match/action/count | Tên event field mới được kiểm tra cú pháp, chưa kiểm theo schema event; severity/version chỉ là chuỗi không rỗng |
| `app/services/rule_config_loader.py` | UTF-8, YAML 1.2 safe loader, cấm duplicate key, Pydantic validation | Hàm thư viện; không có reload, active ruleset, HTTP route hay transaction runtime |
| `app/services/rules.yaml` | 3 mẫu, catalog version 0.1.0, tất cả disabled | Tham số và field còn chờ xác nhận; chưa phải 3 luật đã phát hiện đúng nghiệp vụ |
| `tests/test_rules_config.py` | 25 ca parametrized/test; valid/invalid structure, types, duplicates, UTF-8, file missing | Không thực thi điều kiện rule hoặc timeline correlation |
| `docs/N42-17_RULES_DRAFT.md` | Ghi rõ draft, các điểm còn mở và tách engine/reload | Chưa thay thế sign-off QA/BE2/TL |
| `requirements.txt` | Thêm Pydantic >=2,<3 và ruamel.yaml >=0.18.16,<0.19 | Cần reconcile với main đang yêu cầu Pydantic >=2.9.0 |
| Replay cũ | Có trong commit ed5f7bf | Đã bị xóa tại 883d048; log cũ không chứng minh engine hiện hành |

Tìm caller trong snapshot N42-17: loader/model được gọi từ test; `app/main.py`
chỉ đăng ký health. Việc chưa wire loader vào runtime phù hợp phần cấu hình độc lập,
không chứng minh ticket đã triển khai hot reload.

## 4. Các phát hiện cần hành động

### F01 — Mã FR không còn thống nhất giữa SRS và RTM

**Bằng chứng:** SRS v13 dùng FR-21/22/23 cho YAML/schema/hot reload, nhưng RTM v7,
TCS v11 và Jira dùng FR-15 cho rule configuration. FR-15 ở chính SRS lại là
single-hit power failure. Đây là lệch ý nghĩa, không chỉ khác cách viết.

**Tác động:** một dòng “FR-15 đã covered” có thể trỏ sang hai yêu cầu khác nhau.

**Cần bổ sung:** TL/QA lập bảng ánh xạ theo hành vi + phiên bản nguồn, gắn N42-17 với
YAML/schema và N42-38 với hot reload; giữ lịch sử, không âm thầm đổi mã yêu cầu đã dùng.
Chưa có bảng này thì không tuyên bố coverage FR hoàn chỉnh.

Nguồn: [SRS v13](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3375211),
[RTM v7](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3440729).

### F02 — Kiến trúc gán chức năng vào sai Jira

Kiến trúc v11 ghi rule reload ở N42-46, nhưng Jira N42-46 là incident query API;
reload thực tế thuộc N42-38. Cùng bảng còn ghi RAW fallback ở N42-18, queue ở N42-28
và API ở N42-19; chúng không khớp scope Jira hiện hành.

**Cần bổ sung:** chỉnh bảng liên kết kiến trúc theo ticket hiện hành, phân biệt
schema/loader N42-17, dedup N42-18, reload N42-38, Link Flap N42-44 và incident API N42-46.
Không kéo các chức năng gán nhầm đó vào N42-17.

Nguồn: [Kiến trúc v11](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3375232),
[N42-38](https://nhutp2945-1793259952237.atlassian.net/browse/N42-38),
[N42-46](https://nhutp2945-1793259952237.atlassian.net/browse/N42-46).

### F03 — Rule–event contract chưa đủ để bật ba mẫu

Probe từ parser ref aa6dc2f với cấu hình 883d048 cho kết quả:

| Mẫu | Parser/match quan sát được | Field cần nhưng thiếu |
|---|---|---|
| Cisco LINK-3-UPDOWN RFC3164 | parsed; vendor/mnemonic khớp rule nếu bỏ qua enabled | interface, link_state |
| KB-02 nguyên văn trên Confluence | fallback / unsupported_format; không khớp rule Huawei | psu_slot |
| Huawei POWER_SUPPLY_FAILED bọc RFC3164 | parsed; vendor/mnemonic khớp | psu_slot |
| Cisco BGP-5-ADJCHANGE minh họa | parsed; mnemonic khác BGP_SESSION_STATE_CHANGE | peer, session_state |

AlertEvent hiện extra forbid, nên không thể coi việc gắn tùy ý các field bổ sung lên model
là contract hợp lệ. N42-23/24 và N42-62 cần chốt nơi/tên/kiểu/nullability của enrichment.

**Cần bổ sung ở N42-17:** bảng field mà mỗi mẫu yêu cầu, trạng thái hỗ trợ và fixture
normalized đề xuất; tiếp tục disabled cho tới khi dependency được xác nhận.
Không tự sửa model/parser của owner khác, và không dựng allowlist chỉ từ schema N42-15
rồi kết luận toàn bộ rule tương lai vĩnh viễn không hợp lệ.

Nguồn: [N42-23](https://nhutp2945-1793259952237.atlassian.net/browse/N42-23),
[N42-24](https://nhutp2945-1793259952237.atlassian.net/browse/N42-24),
[N42-62](https://nhutp2945-1793259952237.atlassian.net/browse/N42-62).

### F04 — Tên cấu hình và ngôn ngữ điều kiện đang có nhiều biến thể

| Hiện thực N42-17 | Tài liệu/mẫu khác | Hướng xử lý |
|---|---|---|
| threshold | threshold_count | Chọn tên canonical; ghi mapping tài liệu, không nhận đồng thời hai tên ngầm |
| match: field→string | match_conditions / match_pattern | Equality AND và regex không cùng semantics; không chỉ đổi tên |
| action.incident_severity | severity_trigger | Là severity đầu ra incident, không mặc định cùng nghĩa severity đầu vào event |
| hostname, interface | device_name, interface_name / device, iface | Chốt alias/field ở contract N42-62, không tự đổi key ở riêng rule |
| RuleConfiguration / CorrelationRule | RuleSchema | TCS mô tả lớp thực tế hoặc giao diện ổn định, không bắt đổi tên code chỉ để giống ví dụ |
| RULE_LINK_FLAP_01 | RULE-NET-01-LINK-FLAP | Chốt ID fixture; expected phải nêu ID/version thực tế |

**Khuyến nghị:** giữ cấu trúc code hiện tại làm ứng viên canonical vì đã có loader/tests,
nhưng cần owner xác nhận trước khi downstream phụ thuộc. Không thêm cả hai DSL để chiều
mọi ví dụ. Model hiện tại chủ động extra forbid: đó là hành vi hữu ích, cần giữ.

### F05 — Link Flap: trạng thái đầu, severity và biên vẫn mở

KB-01 v6 ghi rõ DEC-03 cần chốt severity, trạng thái ban đầu, cách đếm, biên,
duplicate và late event. Fixture 5 giá trị UP/DOWN không tự chứng minh 5 chuyển trạng thái:
5 snapshot chỉ có 4 lần đổi quan sát được nếu không có baseline trước đó.

Cần chọn rõ một trong hai hợp đồng:
- Log là **thông báo chuyển trạng thái** đã xảy ra: bản tin đầu có thể tính 1 theo bảo đảm
  của nguồn/parser, loại lặp cùng trạng thái theo định nghĩa đã duyệt.
- Log là **snapshot trạng thái**: bản đầu tạo baseline, tính 0; cần 6 quan sát để xác nhận
  5 chuyển trạng thái, trừ khi đã có trạng thái trước cửa sổ.

Không chọn thay owner bằng một default. Cấu hình Link Flap đang CRITICAL, TCS ghi MAJOR;
đề xuất trước dùng MAJOR chỉ là ứng viên, chưa có phê duyệt.
Biên detector đúng 60s có expected trong TCS; nó không chốt nguồn thời gian/late-event policy
và không áp được nguyên xi cho cửa sổ dedup N42-18.

Nguồn: [KB-01 v6](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3440805),
[Decision Log v11](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/983071),
[N42-44](https://nhutp2945-1793259952237.atlassian.net/browse/N42-44).

### F06 — KB-02: có yêu cầu nguồn kép nhưng fixture thân bài vẫn một nguồn

Phần RC3 đầu KB-02 v6 yêu cầu phân biệt hai slot; thân trang vẫn chỉ một log module 2
và single-hit có điều kiện. Rule hiện tại distinct(psu_slot)>=2 không thể được nghiệm thu
bằng một log đó. Log ISO-prefixed trong KB-02 còn không nằm trong parser RFC3164 đang có.

Cần QA và BE2/BE3 thống nhất:
- Slot 1 lặp hai lần: distinct=1, không đạt nguồn kép.
- Slot 1 và slot 2 cùng thiết bị: distinct=2, đạt nếu cùng cửa sổ đã duyệt.
- Hai thiết bị mỗi thiết bị một slot: không gộp chéo.
- Thiếu slot / ngoài cửa sổ: expected rõ và giữ raw.
- Single-hit và dual-PSU là hai hành vi riêng; giữ ca single-hit nếu được release duyệt.

N42-17 cần fixture/expected để xác nhận **cấu hình**; thực thi rule/timeline thuộc N42-45.
Giữ mẫu 60s là minh họa cho tới khi owner xác nhận.
Không thay âm thầm format log của KB-02 để làm test xanh.

Nguồn: [KB-02 v6](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3408107),
[N42-12](https://nhutp2945-1793259952237.atlassian.net/browse/N42-12),
[N42-45](https://nhutp2945-1793259952237.atlassian.net/browse/N42-45).

### F07 — BGP Flapping không thay BGP Neighbor Down

N42-17 yêu cầu mẫu BGP Flapping; KB-05/N42-65 yêu cầu các cảnh báo peer down theo retry.
Một chuỗi DOWN, DOWN, DOWN có thể đạt ngưỡng retry nhưng không có ba chuyển trạng thái.
Mnemonic BGP_SESSION_STATE_CHANGE cũng không phải BGP_PEER_DOWN hay BGP-5-ADJCHANGE.

Giữ mẫu Flapping disabled theo phạm vi gốc; mô tả đây là mẫu schema chưa được KB-05
nghiệm thu. Không đổi nó thành Neighbor Down nếu chưa có quyết định đổi scope.
N42-65 chốt vendor, retry/window và fixture riêng.

Nguồn: [KB-05 v6](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3408127),
[N42-65](https://nhutp2945-1793259952237.atlassian.net/browse/N42-65).

### F08 — TCS đã tách reload nhưng vẫn có expected phụ thuộc implementation cũ

TC-RUL-001–005 gắn N42-17 design/N42-38 implementation; TC-RUL-006/007 gắn N42-38.
N42-17 có coverage loader/validation cục bộ, chưa có reload.
Phần mở đầu TCS yêu cầu không bám chuỗi exception phiên bản cụ thể, nhưng các case bên dưới
vẫn ghi chuỗi kiểu PyYAML/Pydantic cũ; code hiện dùng ruamel.yaml/Pydantic v2.

Cập nhật mapping case→test và expected theo:
- YAML error: phân loại lỗi, vị trí nguồn nếu có; không ép namespace PyYAML.
- Validation error: field location và loại vi phạm; không assert nguyên câu exception.
- Count số rule thực tế là 3 mẫu disabled của fixture đang review.
- Giữ API/CLI/reload case blocked theo contract tương ứng, không viết route để làm TCS hết blocked.
- Link “Test Case Specification” trong Jira đang trỏ Test Plan 983091; sửa sang TCS 3375173.

Nguồn: [TCS v11 §6.4](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3375173),
[N42-38](https://nhutp2945-1793259952237.atlassian.net/browse/N42-38).

### F09 — Version/hash, giới hạn trên và enum: cần policy trước khi siết code

Probe trước cho thấy model nhận window/threshold=1.000.000.000, event field không có
trong contract và incident severity tùy ý; thêm dedup_window_seconds bị từ chối.
Đây là giới hạn hiện thực, không phải bằng chứng mọi giá trị đó vi phạm AC đã duyệt.

Nên chốt:
- version hiện là nhãn catalog, chưa phải per-rule version bất biến trong DB.
- SHA-256 file UTF-8 có thể dùng làm artifact checksum để truy vết; nó khác semantic hash
  và đổi khi format file đổi. Chọn loại hash trước khi dùng làm identity của engine.
- Miền upper bound, độ dài text, danh mục severity chỉ thêm khi policy được xác nhận.
- Engine/activation validation kiểm field được hỗ trợ khi dependency sẵn sàng.

Không đưa 86.400s, threshold 10.000, max title 200 hoặc SemVer chặt thành gate bắt buộc
chỉ vì chúng xuất hiện trong đề xuất trước. Không xây immutable version store trong N42-17.

### F10 — Các rule phụ thuộc sau này vượt khả năng equality-only hiện có

N42-64 cần IP/VLAN/MAC và grouping được duyệt; các field đó chưa có trong AlertEvent đã đọc.
N42-66 cần so sánh nhiệt độ với ngưỡng, comparator > hoặc >= còn mở.
match: dict[field,string] hiện chỉ mô tả equality AND; threshold là ngưỡng **đếm**,
không mặc định là nhiệt độ. Không giả vờ schema hiện đã biểu diễn đầy đủ rule nhiệt độ.

N42-17 nên ghi capability/giới hạn và mở rộng contract đúng ticket sau khi owner quyết định.
Không thêm một DSL toán tử tổng quát để giải quyết trước mọi rule tương lai.

Nguồn: [N42-64](https://nhutp2945-1793259952237.atlassian.net/browse/N42-64),
[N42-66](https://nhutp2945-1793259952237.atlassian.net/browse/N42-66).

### F11 — Idempotency của N42-18 cần event ID ổn định từ upstream

Probe parse lại cùng raw tạo hai UUID khác nhau. Điều này phù hợp parser tạo event mới,
nhưng cache theo event ID không tự khử được retry nếu upstream cấp ID mới mỗi lần.
Không suy raw giống nhau là duplicate vì cảnh báo lặp hợp lệ cũng có thể giống raw.

Giữ yêu cầu ID ổn định tại ranh giới retry trong N42-62/N42-18; không quy lỗi cho loader N42-17.
Profile nhớ ID 300s trong câu trả lời trước chỉ có nghĩa khi producer/ingest giữ cùng ID.

### F12 — CI và nhánh thực tế cần phân biệt với tài liệu cũ

Ref main đã có .github/workflows/ci.yml dùng Python 3.12, flake8, black và pytest tests/.
Một số trang/CONTRIBUTING vẫn có câu “chưa có workflow”; chúng là mô tả cũ.
Điều này không chứng minh run CI xanh hoặc branch protection đang bật.

N42-17 và main đều thay requirements.txt. Cần reconcile dependency khi đồng bộ:
giữ ruamel.yaml của N42-17 và xem xét ràng buộc kết hợp Pydantic >=2.9.0,<3;
đây là đề xuất hợp nhất ràng buộc, chưa thực hiện merge hay xác nhận conflict thực tế.
Các bộ test N42-17 là pytest functions; unittest discover riêng không chứng minh đã chạy 25 ca.
Black/flake8 không có trong dependencies cục bộ dùng cho đợt rà nên chưa chạy lint.
Không cài thêm hoặc thay dependency của người dùng trong lượt này.

## 5. So sánh với đề xuất trước: giữ, sửa, chuyển ticket

| Đề xuất trước | Kết quả đối chiếu | Hành động phù hợp |
|---|---|---|
| Strict YAML/schema, disabled mặc định | Đã có và phù hợp | Giữ, bổ sung evidence và mapping TC |
| Field allowlist | Chưa có contract field đầy đủ | Chốt bảng field; activation gate khi dữ liệu sẵn sàng, không chặn mẫu disabled bằng schema cũ |
| Link Flap dùng MAJOR | Nguồn vẫn xung đột MAJOR/CRITICAL | Rút khỏi default bắt buộc; để DEC-03 xác nhận |
| Bản tin đầu của state_changes tính 1 | Chỉ đúng nếu log là transition notice | Chốt với parser/QA, không áp cho snapshot |
| Hash và version chặt | Có nhu cầu truy vết, chưa có policy đầy đủ | Chọn artifact/semantic hash; metadata trước, runtime swap ở N42-38 |
| Upper bounds / giới hạn text | Thông số tham khảo, chưa phê duyệt | Không gọi là bug hoặc bắt buộc thêm ngay |
| dedup_window_seconds=30, version 0.2.0 | Chưa có trong schema, loader cũ reject | Thiết kế/migration theo N42-18 và contract được duyệt |
| Processing-time, fixed [start,end), TTL=300s | Không tìm thấy quyết định đã chốt | Giữ proposal N42-18; không biến thành AC N42-17 |
| Capacity 50.000/400.000/100.000/10.000 | Chưa benchmark; AC có RAM <=1.5GB | Đo memory/fan-out trước khi áp; không chứng nhận đủ tải |
| Replay engine | Đã bị gỡ khỏi scope code hiện tại | N42-44/45/65 và QA replay, không khôi phục chỉ để đóng N42-17 |
| Hot reload, rollback, reload API | Jira/TCS xác nhận N42-38 | Không đưa vào phần phải code của N42-17 |
| Bảo toàn raw/evidence | Phù hợp nguồn chuẩn | Giữ như contract liên module; không thêm DB migration trong N42-17 |

## 6. Gói bổ sung nhỏ nhất để hoàn thiện N42-17

### 6.1. Nội dung độc lập có thể chuẩn bị ngay

1. Bổ sung docs/N42-17_RULES_DRAFT.md thành contract cấu hình ứng viên:
   field/type/required/default/semantics, tên canonical và tên cũ ở tài liệu, phạm vi 3 mẫu,
   giới hạn equality/count, source version và dependency. Không coi đây là quyết định thay owner.
2. Lập bảng rule→field→parser/taxonomy ticket→fixture→TC, giữ 3 mẫu disabled.
3. QA chuẩn bị fixture normalized một-slot/lặp-slot/hai-slot/khác-device cho review nguồn kép;
   mỗi fixture ghi expected và trạng thái phần nào chỉ là đặc tả, phần nào đã chạy.
4. Đối chiếu 25 tests với TC-RUL-001–005; bổ sung test theo **hành vi mới được duyệt** nếu có.
   Không tạo test engine giả hoặc test lặp lại implementation để làm tăng số ca.
5. Gắn evidence gắn commit, Python/dependency versions, lệnh chạy và JUnit; xin QA review đúng
   tiêu chí nguồn kép, không chỉ gửi ảnh “pytest pass”.

### 6.2. Các quyết định phải chốt cùng owner

| Quyết định | Owner liên quan | Điều kiện đầu ra |
|---|---|---|
| Canonical rule/event field, vendor casing, severity đầu vào/đầu ra | BE3 + BE2, QA; N42-26/62 | Bảng field/mapping và fixture expected cùng version |
| Link Flap initial state/count/severity/time boundary | BE3 + QA; DEC-03/N42-44 | Timeline có input/expected, người xác nhận |
| Single-hit và dual-PSU | BE3 + BE2 + QA; N42-12/24/45 | Hai mục tiêu tách rõ; fixture slot đủ |
| BGP Flapping so với Neighbor Down | BE3 + QA + owner parser; N42-65/62 | Scope/vendor/field/threshold được duyệt |
| FR/UC/Jira/TC aliases | TL + QA + owner kỹ thuật | RTM không còn trỏ cùng FR sang hai hành vi |
| Version/hash và giới hạn cấu hình nếu áp dụng | BE3 + QA; N42-17/38 | Policy và test tương ứng, không dựa vào số tham khảo chưa duyệt |

### 6.3. Danh sách nơi phải cập nhật nếu quyết định làm đổi hành vi

- Schema: app/models/rule_config.py.
- Loader: app/services/rule_config_loader.py **chỉ khi** contract nạp/lỗi thay đổi.
- Ba fixture cấu hình: app/services/rules.yaml và fixture test.
- Tests: tests/test_rules_config.py.
- Dependency: requirements.txt nếu đồng bộ với main.
- Contract/migration: docs/N42-17_RULES_DRAFT.md.
- Hồ sơ ngoài repo: Tech Spec/DEC-03, TCS, RTM, KB-01/02/05 và links Jira.
- Caller hiện tại: test. Runtime activation/reload callers đi theo N42-38; parser và model
  event đi theo owner tương ứng. Không tự viết thêm endpoint hoặc wrapper.

### 6.4. Điều kiện kết luận N42-17 hoàn thiện

- YAML/schema/loader đáp ứng scope Jira đã thống nhất và có unit evidence gắn commit.
- Ba mẫu có nội dung review rõ, phần chưa được duyệt không bị bật hoặc ghi là đã chạy.
- QA xác nhận cấu hình với fixture nguồn kép phù hợp DoD; dependency chưa xong được ghi đúng.
- Contract/expected/TC/RTM và links Jira không mâu thuẫn về phạm vi N42-17/N42-38.
- PR được review/merge theo policy; gắn CI run đúng commit khi có và đủ approvals theo quy trình.
- Jira chỉ cập nhật Done sau khi các cổng áp dụng thực sự đạt; báo cáo này không chuyển trạng thái.

## 7. Nội dung đề nghị bổ sung vào N42-17 để người dùng review

> Phạm vi hiện tại: bộ schema/loader YAML và ba cấu hình mẫu disabled tại 883d048.
> Unit test cục bộ 25 ca cấu hình PASS; chưa có bằng chứng engine/reload hoặc QA sign-off.
>
> Phần cần hoàn thiện:
> 1. BE3/BE2/QA thống nhất tên field cấu hình và event, semantics count và severity.
> 2. QA bổ sung fixture nguồn kép, phân biệt một slot lặp và hai slot khác nhau.
> 3. Ghi rõ BGP Flapping là mẫu cấu hình; không dùng KB-05 Neighbor Down làm evidence thay thế.
> 4. Đồng bộ TCS TC-RUL-001–005, RTM/FR aliases và liên kết Test Case Specification.
> 5. Gắn fixture/version, commit, dependency versions, JUnit và xác nhận review của QA.
>
> Hot reload/rollback thuộc N42-38; dedup time/ID/cache thuộc N42-18;
> rule execution thuộc N42-44/45/65/66. Các thông số tham khảo chưa có quyết định không tự
> trở thành acceptance mới của N42-17.

Đoạn trên là nháp cho người dùng; **chưa đăng bình luận hoặc sửa ticket**.

## 8. Kiểm chứng đã thực hiện và giới hạn

- Unit suite N42-17 snapshot 883d048: **27 PASS**, gồm 25 cấu hình và 2 health.
  JUnit: ../scratch/n42-17-confluence-review-2026-11-12/junit.xml.
  Timestamp trong JUnit: 2026-11-12T19:40:09+07:00.
- Python 3.14.2; Pydantic 2.14.3; ruamel.yaml 0.18.17; pytest 9.2.0.
- Lệnh dùng dependency đã có:
  `python -B -c 'import sys; sys.path.insert(0,"scratch/n42-17-deps"); import pytest; raise SystemExit(pytest.main(["tests","-q","-p","no:cacheprovider","--junitxml=scratch/n42-17-confluence-review-2026-11-12/junit.xml"]))'`.
- Parser compatibility probe chạy code từ Git ref trong bộ nhớ, không ghép nhánh:
  Cisco match được nhưng thiếu interface/state; KB-02 ISO fallback; RFC3164 Huawei thiếu slot;
  Cisco BGP mnemonic khác; cùng raw parse lại được cấp UUID mới.
  Bốn mẫu có assert expected và một assert ID mới; lưu parser-rule-probe.json.
  Tái lập: `python -B scratch/n42-17-confluence-review-2026-11-12/check_parser_rule_contract.py`.
- Đã so các file thay đổi hai phía N42-17/main từ merge base 35eb2fc:
  overlap là requirements.txt; chưa thực hiện merge.
- Các bằng chứng này không phải load test, replay engine, CI run, approval hoặc branch protection.
  Chưa chạy lại Python 3.12/CI, lint và chưa rà trực quan PNG attachment.
- Không sửa mã ứng dụng, test nghiệp vụ, Jira hoặc Confluence. Chỉ ghi hai tài liệu review
  trong docs và evidence/snapshot trong scratch (đang được .gitignore loại).

## Phụ lục A — Danh mục toàn bộ trang đã truy xuất

Số trang là phạm vi CQL trả về, không phải tuyên bố đã truy cập nội dung ngoài quyền.
Các bản sao cá nhân được giữ để phát hiện drift; không tự chọn trang có số version lớn hơn
làm nguồn chuẩn vì version chỉ so sánh được trong cùng một page ID.

| Page ID | Tiêu đề | Version | Phân loại | Link |
|---|---|---|---|---|
| 65962 | Teamwork Collection Home | 1 | Hệ thống/mẫu/trống | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/TWC/overview) |
| 65977 | Product Requirements Template | 1 | Hệ thống/mẫu/trống | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/TWC/pages/65977/Product+Requirements+Template) |
| 65997 | Nhật ký quyết định dự án N4.2 — Baseline 09/11/2026 | 10 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~71202083ddbb5ba878423a897212137f84b4f3/pages/65997/Nh+t+k+quy+t+nh+d+n+N4.2+Baseline+09+11+2026) |
| 98305 | [Example] Embed docs directly for easy access | 1 | Hệ thống/mẫu/trống | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/TWC/pages/98305/Example+Embed+docs+directly+for+easy+access) |
| 98446 | N4.2 — Cổng thông tin dự án | 14 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/overview) |
| 98511 | Biên bản dự kiến cuộc họp khởi động N4.2 — W2 | 16 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/98511/Bi+n+b+n+d+ki+n+cu+c+h+p+kh+i+ng+N4.2+W2) |
| 98524 | N4.2 — Báo cáo trạng thái và kế hoạch tuần (snapshot 09/11/2026) | 11 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/98524/N4.2+B+o+c+o+tr+ng+th+i+v+k+ho+ch+tu+n+snapshot+09+11+2026) |
| 98543 | Danh mục kịch bản kiểm thử N4.2 — KB-01 đến KB-08 | 4 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~71202083ddbb5ba878423a897212137f84b4f3/pages/98543/Danh+m+c+k+ch+b+n+ki+m+th+N4.2+KB-01+n+KB-08) |
| 196708 | Overview | 1 | Hệ thống/mẫu/trống | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~71202083ddbb5ba878423a897212137f84b4f3/overview) |
| 229377 | Điều lệ dự án N4.2 — Baseline 09/11/2026 | 9 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~71202083ddbb5ba878423a897212137f84b4f3/pages/229377/i+u+l+d+n+N4.2+Baseline+09+11+2026) |
| 229413 | Quy định vận hành nhóm dự án N4.2 — Bản rà soát 09/11/2026 | 6 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~71202083ddbb5ba878423a897212137f84b4f3/pages/229413/Quy+nh+v+n+h+nh+nh+m+d+n+N4.2+B+n+r+so+t+09+11+2026) |
| 229430 | Thiết kế kỹ thuật hệ thống N4.2 (TDD) | 10 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~71202083ddbb5ba878423a897212137f84b4f3/pages/229430/Thi+t+k+k+thu+t+h+th+ng+N4.2+TDD) |
| 229446 | Kế hoạch kiểm thử tổng thể N4.2 — Baseline 09/11/2026 | 17 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~71202083ddbb5ba878423a897212137f84b4f3/pages/229446/K+ho+ch+ki+m+th+t+ng+th+N4.2+Baseline+09+11+2026) |
| 851987 | Quy định vận hành nhóm dự án N4.2 — Bản rà soát 09/11/2026 | 6 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/851987/Quy+nh+v+n+h+nh+nh+m+d+n+N4.2+B+n+r+so+t+09+11+2026) |
| 917524 | Danh mục kịch bản kiểm thử N4.2 — KB-01 đến KB-08 | 5 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/917524/Danh+m+c+k+ch+b+n+ki+m+th+N4.2+KB-01+n+KB-08) |
| 917544 | N4.2 — Báo cáo trạng thái và kế hoạch tuần (snapshot 09/11/2026) | 7 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~71202083ddbb5ba878423a897212137f84b4f3/pages/917544/N4.2+B+o+c+o+tr+ng+th+i+v+k+ho+ch+tu+n+snapshot+09+11+2026) |
| 983041 | Bộ biểu mẫu quản lý HKDN — Nhóm N4.2 | 15 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~71202083ddbb5ba878423a897212137f84b4f3/pages/983041/B+bi+u+m+u+qu+n+l+HKDN+Nh+m+N4.2) |
| 983071 | Nhật ký quyết định dự án N4.2 — Baseline 09/11/2026 | 11 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/983071/Nh+t+k+quy+t+nh+d+n+N4.2+Baseline+09+11+2026) |
| 983091 | Kế hoạch kiểm thử tổng thể N4.2 — Baseline 09/11/2026 | 21 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/983091/K+ho+ch+ki+m+th+t+ng+th+N4.2+Baseline+09+11+2026) |
| 983112 | Biên bản dự kiến cuộc họp khởi động N4.2 — W2 | 10 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~71202083ddbb5ba878423a897212137f84b4f3/pages/983112/Bi+n+b+n+d+ki+n+cu+c+h+p+kh+i+ng+N4.2+W2) |
| 1015837 | Thiết kế kỹ thuật hệ thống N4.2 (TDD) | 9 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/1015837/Thi+t+k+k+thu+t+h+th+ng+N4.2+TDD) |
| 1015858 | Bộ biểu mẫu quản lý HKDN — Nhóm N4.2 | 16 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/1015858/B+bi+u+m+u+qu+n+l+HKDN+Nh+m+N4.2) |
| 1048584 | Điều lệ dự án N4.2 — Baseline 09/11/2026 | 9 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/1048584/i+u+l+d+n+N4.2+Baseline+09+11+2026) |
| 1048604 | Phân tích và thiết kế hệ thống N4.2 (SADD) | 4 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~71202083ddbb5ba878423a897212137f84b4f3/pages/1048604/Ph+n+t+ch+v+thi+t+k+h+th+ng+N4.2+SADD) |
| 2556022 | Overview | 1 | Hệ thống/mẫu/trống | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~7120204efad3ae6442420a99178797d2da4d0b/overview) |
| 2556091 | Untitled live doc 2026-11-06 | 1 | Hệ thống/mẫu/trống | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~7120204efad3ae6442420a99178797d2da4d0b/pages/2556091/Untitled+live+doc+2026-11-06) |
| 2556209 | Overview | 1 | Hệ thống/mẫu/trống | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~7120203a2a3120b5bb480dbcab1d79d1d2f91c/overview) |
| 2687069 | Overview | 1 | Hệ thống/mẫu/trống | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~71202067da66791c074fa5b0c91c679559a00b/overview) |
| 2850979 | Overview | 1 | Hệ thống/mẫu/trống | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~712020783f5d76b2b34f68ba51b9d7da87009a/overview) |
| 2883585 | Untitled live doc 2026-11-06 | 1 | Hệ thống/mẫu/trống | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~712020783f5d76b2b34f68ba51b9d7da87009a/pages/2883585/Untitled+live+doc+2026-11-06) |
| 2883605 | Untitled live doc 2026-11-06 | 1 | Hệ thống/mẫu/trống | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~7120203a2a3120b5bb480dbcab1d79d1d2f91c/pages/2883605/Untitled+live+doc+2026-11-06) |
| 2916354 | Untitled live doc 2026-11-06 (2) | 1 | Hệ thống/mẫu/trống | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~7120204efad3ae6442420a99178797d2da4d0b/pages/2916354/Untitled+live+doc+2026-11-06+2) |
| 2949150 | Untitled live doc 2026-11-06 | 1 | Hệ thống/mẫu/trống | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~7120200ad5e210883e44498daa2d3b51029e4d/pages/2949150/Untitled+live+doc+2026-11-06) |
| 2982054 | Overview | 1 | Hệ thống/mẫu/trống | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~7120200ad5e210883e44498daa2d3b51029e4d/overview) |
| 2982060 | Untitled live doc 2026-11-06 (2) | 1 | Hệ thống/mẫu/trống | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/~7120203a2a3120b5bb480dbcab1d79d1d2f91c/pages/2982060/Untitled+live+doc+2026-11-06+2) |
| 3375173 | Đặc tả ca kiểm thử N4.2 — Bản chi tiết 09/11/2026 | 11 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3375173/c+t+ca+ki+m+th+N4.2+B+n+chi+ti+t+09+11+2026) |
| 3375211 | Đặc tả yêu cầu hệ thống và ca sử dụng N4.2 | 13 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3375211/c+t+y+u+c+u+h+th+ng+v+ca+s+d+ng+N4.2) |
| 3375232 | Thiết kế kiến trúc hệ thống N4.2 | 11 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3375232/Thi+t+k+ki+n+tr+c+h+th+ng+N4.2) |
| 3375253 | Tiêu chí nghiệm thu dự án N4.2 | 5 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3375253/Ti+u+ch+nghi+m+thu+d+n+N4.2) |
| 3375289 | KB-07 Malformed Syslog | 6 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3375289/KB-07+Malformed+Syslog) |
| 3408022 | Thiết kế dữ liệu và API N4.2 | 13 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3408022/Thi+t+k+d+li+u+v+API+N4.2) |
| 3408058 | Quản lý và kiểm soát tài liệu dự án N4.2 | 6 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3408058/Qu+n+l+v+ki+m+so+t+t+i+li+u+d+n+N4.2) |
| 3408087 | Mẫu báo cáo trạng thái W1 — Bản dự thảo | 6 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3408087/M+u+b+o+c+o+tr+ng+th+i+W1+B+n+d+th+o) |
| 3408107 | KB-02 Power Supply Failure | 6 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3408107/KB-02+Power+Supply+Failure) |
| 3408127 | KB-05 BGP Neighbor Down | 6 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3408127/KB-05+BGP+Neighbor+Down) |
| 3440729 | Ma trận truy vết yêu cầu N4.2 — FR/NFR đến AC/TC/Evidence | 7 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3440729/Ma+tr+n+truy+v+t+y+u+c+u+N4.2+FR+NFR+n+AC+TC+Evidence) |
| 3440765 | Danh mục nghiệm thu và bàn giao N4.2 | 4 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3440765/Danh+m+c+nghi+m+thu+v+b+n+giao+N4.2) |
| 3440785 | [Tech Spec] Phân Tích & Thiết Kế Kiến Trúc Hệ Thống: N4.2 — Thu thập và phân tích cảnh báo mạng | 10 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3440785/Tech+Spec+Ph+n+T+ch+Thi+t+K+Ki+n+Tr+c+H+Th+ng+N4.2+Thu+th+p+v+ph+n+t+ch+c+nh+b+o+m+ng) |
| 3440805 | KB-01 Link Flap | 6 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3440805/KB-01+Link+Flap) |
| 3440825 | KB-08 Load and Recovery | 6 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3440825/KB-08+Load+and+Recovery) |
| 3702807 | Sổ đăng ký rủi ro dự án N4.2 | 4 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3702807/S+ng+k+r+i+ro+d+n+N4.2) |
| 3702827 | KB-03 SYN Flood | 6 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3702827/KB-03+SYN+Flood) |
| 3702847 | KB-04 IP Conflict | 6 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3702847/KB-04+IP+Conflict) |
| 3833906 | KB-06 CPU High Temperature | 6 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/3833906/KB-06+CPU+High+Temperature) |
| 5013638 | N4.2 — Overview | 1 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/5013638/N4.2+Overview) |
| 5046309 | N4.2 — ADRs | 1 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/5046309/N4.2+ADRs) |
| 5046331 | N4.2 — QA & Testing | 1 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/5046331/N4.2+QA+Testing) |
| 5144653 | N4.2 — Operations & Runbooks | 1 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/5144653/N4.2+Operations+Runbooks) |
| 5210229 | N4.2 — Enterprise Confluence Blueprint & Master Tech Spec | 5 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/5210229/N4.2+Enterprise+Confluence+Blueprint+Master+Tech+Spec) |
| 5308529 | N4.2 — Architecture & Specs | 1 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/5308529/N4.2+Architecture+Specs) |
| 5308557 | N4.2 — Database & APIs | 1 | N4.2 | [Nguồn](https://nhutp2945-1793259952237.atlassian.net/wiki/spaces/OTHER/pages/5308557/N4.2+Database+APIs) |

## Phụ lục B — Nguồn lưu cục bộ

- Bản trả lời trước: N42-17_N42-18_PROPOSAL_2026-11-12.md, giữ nguyên nội dung.
- Báo cáo này: N42-17_CONFLUENCE_REVIEW_2026-11-12.md.
- Snapshot phần văn bản: ../scratch/n42-17-confluence-review-2026-11-12/corpus.md.
- Manifest page/version và attachment metadata: ../scratch/n42-17-confluence-review-2026-11-12/sources.json.
- JUnit: ../scratch/n42-17-confluence-review-2026-11-12/junit.xml.
- Probe và self-check: ../scratch/n42-17-confluence-review-2026-11-12/parser-rule-probe.json
  và check_parser_rule_contract.py trong cùng thư mục.

Scratch không được Git theo dõi theo cấu hình repo hiện tại. Các tài liệu docs mới chưa commit;
không có thao tác push hoặc đăng nội dung ra hệ thống bên ngoài.
