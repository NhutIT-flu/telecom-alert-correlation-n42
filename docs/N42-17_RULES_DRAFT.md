# N42-17 — Bản nháp cấu hình luật v0.1.1

Phần có thể review độc lập với database gồm `app/services/rules.yaml`, `RuleConfiguration` và hàm `load_rule_configuration(Path(...))`. Hàm nạp một tệp UTF-8 bằng YAML 1.2, rồi kiểm tra cấu trúc với Pydantic. Bản nháp lấy `threshold`, `match` và `action` theo ví dụ trong [N42-17](https://nhutp2945-1793259952237.atlassian.net/browse/N42-17). `version` định danh bộ luật để đối chiếu khi review, còn `enabled` mặc định là `false`. Hai chế độ đếm đề xuất là `distinct` (đếm giá trị khác nhau) và `state_changes` (đếm sự kiện chuyển trạng thái theo trường đã chỉ định). Nếu không có `count`, đề xuất đếm các sự kiện thỏa `match`.

| Luật mẫu | Hành vi dự kiến khi tích hợp | Điều kiện cần chốt |
|---|---|---|
| Link Flap | Năm sự kiện chuyển trạng thái trong 60 giây trên cùng thiết bị và interface. Bốn sự kiện, cảnh báo lặp cùng trạng thái hoặc hai interface riêng không đủ ngưỡng. | Đối chiếu `interface`/`link_state` với schema parser. Ví dụ N42-17 dùng `CRITICAL`, còn TC-COR-001 ghi `MAJOR`. Xem KB-01 và N42-44. |
| Dual Power Supply Failure | Hai slot nguồn khác nhau trên cùng thiết bị. Hai bản tin từ cùng slot vẫn chỉ tính một slot. Cửa sổ 60 giây là giá trị minh họa. | Field `psu_slot`, taxonomy Huawei và cửa sổ. KB-02 hiện chỉ có fixture một nguồn hỏng; incident single-hit cần duyệt riêng. QA cần fixture hai slot cho N42-45. |
| BGP Flapping | Nhóm theo thiết bị và peer, đếm chuyển trạng thái phiên. Ngưỡng 3, cửa sổ 120 giây và mnemonic là ví dụ cấu hình. | Field peer/state, nguồn parser, ngưỡng, cửa sổ và severity. KB-05/N42-65 đặc tả BGP Neighbor Down theo retry nên cần xác nhận phạm vi riêng trước khi dùng làm tiêu chí cho BGP Flapping. |

## Contract canonical và tham số tham khảo (review 12/11/2026)

Public boundary: `load_rule_configuration(path: Path, *, supported_event_fields=None, expected_sha256=None) -> RuleConfiguration`.
Loader đọc UTF-8/YAML 1.2 safe, cấm khóa YAML trùng, thẩm định toàn bộ rồi trả model;
không có API/CLI, engine, reload hoặc partial success trong N42-17.

| Field | Kiểu / ràng buộc | Bắt buộc / mặc định | Tham khảo |
|---|---|---|---|
| version | string trim, không rỗng | bắt buộc | catalog ứng dụng và ứng viên 0.1.1 |
| rules | list không rỗng, rule_id duy nhất | bắt buộc | đúng 3 mẫu tắt |
| rule_id | string trim, không rỗng | bắt buộc | giữ ID trong YAML |
| name | string trim, không rỗng | bắt buộc | tên hiển thị |
| description | string trim không rỗng hoặc null | null | diễn giải điều kiện và giới hạn |
| enabled | boolean strict | false | cả 3 mẫu false |
| window_seconds | integer strict 1..86400 | bắt buộc | LF60, PSU60 ví dụ, BGP120 ví dụ |
| threshold | integer strict 1..10000 | bắt buộc | LF5, PSU2, BGP3 ví dụ |
| group_by | list identifier không rỗng, không trùng | bắt buộc | LF hostname/interface; PSU hostname; BGP hostname/peer |
| match | map identifier→string trim không rỗng, ít nhất 1 cặp | bắt buộc | equality AND; không regex/comparator |
| count | object hoặc null | null | null: đề xuất đếm event khớp, chưa có consumer runtime |
| count.mode | literal distinct hoặc state_changes | bắt buộc khi có count | PSU distinct; LF/BGP state_changes |
| count.field | identifier | bắt buộc khi có count | psu_slot/link_state/session_state |
| action | object | bắt buộc | không nhận key thừa |
| action.create_incident | boolean strict | bắt buộc | true trong mẫu |
| action.incident_severity | string trim không rỗng | bắt buộc | LF MAJOR; enum lab CRITICAL/MAJOR/MINOR/WARNING/INFO |
| action.title | string trim không rỗng | bắt buộc | tiêu đề incident dự kiến |

Mọi model strict=True/extra=forbid. Identifier khớp `^[a-zA-Z_][a-zA-Z0-9_]*$`,
không tự trim; kiểm cú pháp không chứng minh field có ở producer. Enum/caps và kiểm field của enabled rule đã triển khai theo ủy quyền mới của người dùng;
chưa có phê duyệt tổ chức. Disabled rule vẫn nhận field proposed.
`threshold_count`→`threshold`, `match_pattern`/`match_conditions`→`match`,
`severity_trigger`→`action.incident_severity` chỉ là đối chiếu thuật ngữ nguồn,
không phải alias đầu vào. Threshold là số đếm, không dùng trực tiếp cho nhiệt độ.

Link Flap dùng transition notice: bản đầu tính 1, lặp cùng trạng thái cộng 0;
snapshot không thuộc corpus này. Năm notice trong rolling60s; đúng biên60s tính trong
expected TCS. Time source/late-event/idempotency chờ N42-18/44/62.
Người dùng ủy quyền triển khai MAJOR vào YAML ứng dụng trước QA/TL sign-off; vẫn tắt luật.
Ứng viên để review tại `tests/fixtures/rules/candidate-0.1.1.yaml`, không được loader tự nạp.

### Field và producer

| Rule | Field | Type/nullability dự kiến | Producer/ticket | Trạng thái / fixture |
|---|---|---|---|---|
| cả ba | hostname | string không rỗng khi nhóm | BE2 N42-15/62 | observed trên snapshot parser; contract chờ N62 |
| LF/PSU | vendor, mnemonic | string canonical không rỗng khi match | BE2 N42-23/24/26/62 | observed; mapping/casing cần chốt |
| LF | interface | string không rỗng khi nhóm | BE2 N42-23/62 | missing trên aa6dc2f; LF-01–07 proposed |
| LF | link_state | UP/DOWN khi đếm | BE2 N42-23/26/62 | missing; LF-01–07 proposed |
| PSU | psu_slot | slot ID string không rỗng khi đếm distinct | BE2 N42-24/62 | missing; PSU-01–07 proposed |
| BGP | peer | string không rỗng khi nhóm | BE2/BE3 N42-62/65 | missing; BGP-01/02 proposed |
| BGP | session_state | string theo mapping chưa chốt | BE2/BE3 N42-26/62/65 | missing; BGP-01/02 proposed |
| BGP | mnemonic | string canonical không rỗng | BE2 N42-26/62 | BGP_SESSION_STATE_CHANGE khác Cisco BGP-5-ADJCHANGE |

Snapshot parser aa6dc2f chưa cung cấp các field missing. Các field proposed trong JSON
là dữ liệu review, không phải AlertEvent runtime. Thiếu slot không tự mặc định một slot.
KB02 raw ISO giữ nguyên và đã quan sát unsupported_format; không sửa raw để lấy PASS.
KB05 Neighbor Down theo retry thuộc N42-65, không nghiệm thu BGP Flapping.

### Nhóm lỗi và truy vết test

| TC / tình huống | Expected ở boundary loader | Test thực tế |
|---|---|---|
| TC-RUL-001 hợp lệ | model, YAML1.2, UTF-8, 3 mẫu tắt | loads_three_disabled_sample_rules; loads_yaml_1_2_and_accepts_lower_bound; loads_vietnamese_text_from_utf8_file |
| TC-RUL-002 YAML lỗi | YAMLError, vị trí nếu thư viện cung cấp | rejects_yaml_with_tab_indentation; rejects_duplicate_yaml_keys; rejects_unsafe_yaml_object_tag |
| TC-RUL-003 threshold0 | ValidationError, loc rules/0/threshold | rejects_invalid_rule_fields |
| TC-RUL-004 window0 | ValidationError, loc rules/0/window_seconds | rejects_invalid_rule_fields |
| TC-RUL-005 sai kiểu | ValidationError, loc đúng field, không ép string/bool/float thành int | rejects_invalid_rule_fields; rejects_unusable_or_unknown_configuration |
| file/encoding | FileNotFoundError (filename), UnicodeDecodeError | reports_missing_yaml_file; rejects_yaml_file_with_invalid_utf8 |
| cấu trúc/uniqueness | ValidationError, loc root/rules/field tương ứng | rejects_invalid_rule_file_structure; rejects_duplicate_rule_ids; rejects_duplicate_ids_after_whitespace_normalization |
| TC-RUL-006/007 | NOT RUN: reload/rollback N42-38 | không thuộc unit test N17 |

Tên test trên có prefix `test_`, nằm trong `tests/test_rules_config.py`.
Không assert toàn bộ chuỗi exception theo một library version. Thất bại không trả catalog
hợp lệ một phần. Fixture `review-cases.json` có expected thiết kế; test chỉ xác nhận metadata/
tham chiếu catalog, không đo detection hoặc ký thay QA.

### Bằng chứng và nhận diện bản bàn giao

Hash SHA-256 exact-file bytes và version nằm trong manifest evidence, không thêm key vào
grammar YAML. Cùng version khác bytes vẫn là artifact khác; không suy immutable store hoặc
active ruleset. Đổi MAJOR sau sign-off cần đồng bộ version0.1.1/YAML/expected rồi chạy lại.
N42-18 nhận dedup, N42-38 reload, N42-44/45/65/66 engine; không áp KPI pipeline cho loader.

## Readiness và evidence (quy trình)

- Đối chiếu [TCS mục 6.4](TEST_CASE_SPECIFICATION.md#64-cấu-hình-luật--be3-tc-rul) và [RTM](REQUIREMENTS_TRACEABILITY_MATRIX.md) theo FR-15/AC-05. Unit test bản nháp kiểm tra TC-RUL-001–005 ở mức nạp tệp và validation, gồm YAML lỗi, giá trị biên `0`/`1`, kiểu dữ liệu sai, khóa YAML và mã luật trùng.
- Evidence cục bộ có thể xuất bằng `python -m pytest tests/test_rules_config.py --junitxml=scratch/n42-17-junit.xml`. Khi bàn giao ghi kèm commit SHA, phiên bản YAML, Python/dependencies và lệnh chạy. QA Lead cần xác nhận cấu hình với KB-02 theo DoD của N42-17. Fixture KB-02 có một slot hỏng; cần fixture riêng hai slot để nghiệm thu luật nguồn kép.
- Trước khi bật luật, BE2/BE3 xác nhận field và taxonomy theo N42-15/N42-62, QA xác nhận expected result và liên kết case với RTM, TL ghi nhận quyết định. Engine, hot reload và lưu trữ đi theo ticket triển khai tương ứng.


## Quyết định triển khai theo ủy quyền người dùng — 12/11/2026

Người dùng yêu cầu triển khai code, tự quyết định các điểm mở và báo lại để xin người
có quyền phê duyệt sau. Điều này thay gate chờ approval trước code trong bản kế hoạch cũ;
không thay QA/TL sign-off, CI hoặc merge. Các dòng pending trước đó được giữ làm lịch sử.

Đã triển khai window1..86400s; threshold1..10000; name120/description1000/rule_id128/
version64/title200 ký tự tối đa. Severity incident: CRITICAL/MAJOR/MINOR/WARNING/INFO,
uppercase chính xác; không đồng nhất với severity event. Enabled rule bắt buộc có field
contract supplied ở boundary loader hoặc model validation context; kiểm tất cả field của
match/group_by/count. Disabled rule vẫn cho field proposed. Không tự suy parser đã có field.
Loader optional expected_sha256: đúng64hex, so exactbytes trước decode/YAML, đọc file1lần;
pin sai/malformed raise ValueError. Nếu không pin vẫn dùng API cũ; không có version store.
Catalog ứng dụng0.1.1, LinkFlap MAJOR,3rule disabled. Candidate fixture giữ để đối chiếu.
PSU60s/2slot và BGP120s/3 là tham số lab được tự chọn, cần business review sau;
không tạo detector/dedup/reload/parser/DB hoặc tự bật luật.
TC-RUL008–011 và local FR15 mở rộng có expected trước code; tests chứng minh từ fail→pass.
