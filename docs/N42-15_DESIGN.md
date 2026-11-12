# N42-15 - Đề xuất schema AlertEvent và parser RFC3164

- Phiên bản: 0.1, ngày 09/11/2026.
- Trạng thái: DRAFT / NEEDS OWNER REVIEW. Chưa phải contract được duyệt, code hoặc kết quả test.
- Code owner: Phạm Tấn Thành (BE2). QA Lead chủ trì coverage và đặc tả kiểm thử; BE2 xác nhận expected output và viết unit test.
- Ticket: [N42-15](https://nhutp2945-1793259952237.atlassian.net/browse/N42-15).
- Truy vết: FR-04/FR-05, AC-02; TC-PAR-001..012 chỉ áp dụng phần scope được duyệt; xem [RTM](REQUIREMENTS_TRACEABILITY_MATRIX.md).
- Nguồn: mô tả ticket do người dùng cung cấp; [TDD](TECHNICAL_DESIGN_DOCUMENT.md), [thiết kế dữ liệu/API](DATA_AND_API_DESIGN.md), [AC](ACCEPTANCE_CRITERIA.md), [interface v0.9](../n42-ai-kit/docs/INTERFACES.md), [decision log](DECISIONS.md).

## 1. Phạm vi đề xuất

Thiết kế entity chuẩn và parser đồng bộ, không I/O: chuỗi syslog RFC3164 -> AlertEvent. Bóc PRI, thời gian, hostname, tag/program, nội dung; nhận diện Cisco/Huawei/Linux trên các chữ ký được liệt kê dưới đây. Nhận diện Fortinet key-value và trả fallback unsupported, chưa parse đầy đủ định dạng đó trong N42-15.

Parser thuộc M2 theo TDD hiện tại; M3 là queue. Tham chiếu "TDD v2 mục 2.2 / M3" trong ticket cần cập nhật theo nguồn hiện hành.

Ngoài scope đề xuất: receiver/queue, persistence/migration, API, correlation, phân tích sâu interface/IP/trạng thái link, RFC5424, Juniper và Fortinet key-value đầy đủ. Không loại chức năng khỏi baseline dự án; cần TL xác nhận phân bổ sang ticket liên quan. Test TC-PAR-012 dùng ISO timestamp không phải header RFC3164, đề nghị liên kết parser định dạng tương ứng thay vì ngầm thêm vào N42-15.

## 2. Schema để review

Ưu tiên tên field gần interface v0.9 để giảm thay đổi liên module; bổ sung các field cần phân biệt fallback. Đây là lựa chọn đề xuất, chưa sửa interface nguồn.

| Field | Kiểu / ràng buộc đề xuất | Ý nghĩa |
|---|---|---|
| id | UUID, default UUID4 | ID riêng cho mỗi lần parse; không bảo đảm idempotency |
| schema_version | Literal["1.0"] | Phiên bản đích sau phê duyệt; hiện tài liệu vẫn v0.1 |
| received_at | datetime có timezone, chuẩn UTC | Thời điểm adapter nhận; wrapper dùng clock nếu caller không truyền |
| event_timestamp | datetime có timezone, chuẩn UTC | Thời gian suy từ log; fallback dùng received_at |
| timestamp_inferred | bool | true với RFC3164 vì thiếu năm/timezone; cũng true khi fallback |
| source_ip | str, kiểm tra IPv4/IPv6, xuất dạng chuẩn | IP transport, không lấy từ hostname/body; địa chỉ mặc định loopback chỉ dùng local |
| hostname | str | Host bóc từ header; fallback dùng source_ip |
| facility | int strict, 0..23 | PRI // 8; fallback dùng 1 (giá trị thay thế, cần duyệt) |
| severity | int strict, 0..7 | PRI % 8; fallback dùng 6 theo ticket |
| vendor | cisco / huawei / fortinet / linux / unknown | Enum chữ thường theo ticket; không dùng format làm vendor |
| program | str hoặc null | Tag/process, ví dụ sshd; null nếu không có hoặc không nhận dạng |
| mnemonic | str hoặc null | Ví dụ LINK-3-UPDOWN hoặc POWER_SUPPLY_FAILED |
| category | str, mặc định "unknown" | Chưa phân loại nghiệp vụ trong N42-15; mapping ở ticket riêng |
| message | str | Content sau prefix hãng/tag đã nhận dạng; nếu không nhận dạng giữ nguyên MSG |
| raw_payload | str | Giữ nguyên chuỗi caller truyền, không strip/cắt/chuyển newline |
| parse_status | parsed / fallback | parsed chỉ khi header và ngày giờ hợp lệ; không khẳng định hỗ trợ sâu nội dung |
| parse_error | enum hoặc null | null khi parsed; mã lỗi bên dưới khi fallback |

Đề xuất Pydantic v2: cấm extra fields, kiểm tra datetime aware và chuẩn UTC; facility/severity không nhận bool hoặc chuỗi số. `raw_payload` và `message` cho phép chuỗi rỗng để chứa fallback. Không có alias xuất ra hai bộ field song song.

### Khác biệt cần duyệt so với ticket và v0.9

| Nguồn | Chuyển sang đề xuất này |
|---|---|
| ticket.timestamp | event_timestamp; thêm received_at riêng |
| ticket.raw_log | raw_payload |
| ticket không có tag | program chứa tag; mnemonic vẫn độc lập |
| v0.9 vendor chữ hoa, lẫn RFC3164/RFC5424 | enum chữ thường; format không phải vendor |
| v0.9 không có fallback status | thêm parse_status, parse_error, timestamp_inferred |
| v0.9 program bắt buộc | nullable để không bịa tag |

Fallback AlertEvent là record chẩn đoán, không phải sự kiện nghiệp vụ hợp lệ. Pipeline tương lai phải chặn `parse_status=fallback` khỏi correlation và chuyển quarantine. Việc tạo QuarantineRecord từ record này thuộc contract pipeline; chưa triển khai và chưa thay chữ ký BaseNormalizer. Đây là điểm phải được BE1/BE2/BE3/TL thống nhất vì v0.9 đề xuất ParseError/QuarantineRecord.

## 3. Giao diện hàm đề xuất

```python
def parse_syslog_rfc3164(
    raw: str,
    source_ip: str = "127.0.0.1",
    *,
    received_at: datetime | None = None,
    source_timezone: tzinfo | None = None,
) -> AlertEvent: ...
```

- Giữ tương thích hai tham số positional trong ticket; tham số thêm chỉ keyword.
- Không có timezone nguồn: mặc định UTC, là giả định cần duyệt; không dùng timezone máy chạy. Fixture cố định timezone +07:00 và received_at để tái lập.
- received_at bị bỏ trống: lấy UTC now đúng một lần. Khi được cung cấp phải aware.
- raw không phải str, source_ip không hợp lệ, received_at naive hoặc timezone config không hợp lệ: lỗi lập trình/cấu hình, trả TypeError/ValueError có kiểm soát. Caller/pipeline xử lý ở boundary; không bắt mọi Exception để giả thành lỗi log.
- raw là str dị dạng: luôn trả fallback hợp lệ, không ném lỗi dữ liệu. Decode bytes thuộc adapter, không dùng errors=ignore làm mất bytes. RawEvent adapter tương lai phải giữ bytes gốc nếu decode lỗi.
- UUID/clock được cô lập để test; không assert equality toàn bộ record giữa hai lần parse vì UUID khác nhau.

## 4. Quy tắc phân tích

1. Bảo toàn raw; dùng bản nhìn phục vụ parse, cho phép bỏ đúng một LF cuối hoặc một cặp CRLF cuối. Newline/control character bên trong bị coi malformed. Trần đề xuất 1024 bytes UTF-8 cho bản tin gốc, vượt trần trả fallback; ngưỡng này cần BE1/QA duyệt. Raw không bị cắt, input guard phía adapter chịu giới hạn cấp transport.
2. Regex compile ở cấp module, neo đầu/cuối, nhóm có giới hạn; không dùng nested quantifier. Bóc `<PRI>Mmm dd hh:mm:ss HOST MSG`, tháng tiếng Anh độc lập locale. Chấp nhận ngày một chữ số có khoảng trắng padding và biến thể zero padding như ví dụ ticket; ghi rõ đây là profile dung sai.
3. PRI có 1..3 chữ số ASCII, miền 0..191. Không nhận dấu âm, chữ, leading zero trừ chính `0`. Tính facility/severity từ PRI, không ghi đè bằng số trong body hãng.
4. Host là token ASCII không chứa khoảng trắng/control; không DNS lookup. MSG có thể rỗng. Ngày/giờ phải có thật, không nhận leap second trong profile v0.1; thiếu năm xử lý theo mục 5.
5. Bóc chữ ký Huawei trước, Cisco sau, Linux sau cùng. Nếu không match hãng vẫn parsed với vendor unknown khi header hợp lệ; giữ MSG nguyên vẹn.
6. Prefix hãng chỉ được bóc khi cú pháp đầy đủ match. Không match prefix thì không đánh rơi nội dung; không suy loại thiết bị từ tên hostname.

| Dấu hiệu ở đầu MSG | vendor | program / mnemonic / message |
|---|---|---|
| `%LINK-3-UPDOWN: ...`, `%OSPF-5-ADJCHG: ...`, `%FACILITY-N-MNEMONIC: ...` | cisco | program=FACILITY; mnemonic=toàn token bỏ `%`; message=phần sau `:` và tối đa một space |
| `%%01DEVM/2/POWER_SUPPLY_FAILED: ...` hoặc mnemonic có hậu tố `(l)` | huawei | program=DEVM; mnemonic=POWER_SUPPLY_FAILED (bỏ hậu tố); message=content |
| `sshd[123]: ...`, `kernel: ...`, `rsyslogd: ...`, `systemd[1]: ...`, `sudo: ...`, `cron: ...` | linux | program=tag bỏ PID; mnemonic=null; message=content |
| Tag khác như `customapp[42]: ...` | unknown | bóc program=customapp; mnemonic=null; message=content; tag đơn thuần không chứng minh Linux |
| Raw bắt đầu `date=... time=...` đúng mẫu nhận diện key-value | unknown trong fallback | parse_error=unsupported_format; không tuyên bố đã parse Fortinet |

Allowlist Linux là heuristic đề xuất, không phải định danh hệ điều hành chắc chắn. Fortinet có thể được nhận diện nội bộ để dispatch, nhưng output fallback vẫn vendor unknown theo ticket; parser Fortinet đầy đủ sẽ tạo vendor fortinet khi được triển khai riêng.

## 5. Chính sách thời gian đề xuất

- RFC3164 không có năm/timezone: lấy timezone nguồn từ cấu hình; dùng received_at làm mốc.
- Tạo tối đa ba ứng viên ở năm nhận -1, năm nhận, năm nhận +1 trong timezone nguồn. Bỏ ứng viên ngày không tồn tại; đổi UTC rồi chọn ứng viên gần received_at nhất theo khoảng cách tuyệt đối; nếu hòa chọn thời điểm sớm hơn.
- Không có ứng viên hợp lệ: invalid_timestamp. Mọi log RFC3164 đều có timestamp_inferred=true. Thuật toán không bảo đảm suy đúng năm cho log lịch sử; file replay lịch sử phải truyền mốc nhận phù hợp hoặc dùng parser/metadata riêng sau khi được duyệt.
- v0.1 đề xuất dùng timezone có offset cố định; timezone có DST chưa hỗ trợ để tránh giờ trùng/không tồn tại, phải báo lỗi cấu hình thay vì tự đoán.
- Không tự áp threshold "tương lai >1 ngày" hoặc giới hạn độ cũ chưa được duyệt. Cần thống nhất riêng với QA nếu muốn thêm skew policy.

## 6. Fallback và thứ tự lỗi

Mọi fallback: vendor=unknown, facility=1, severity=6, hostname=source_ip, program/mnemonic=null, category=unknown, event_timestamp=received_at, timestamp_inferred=true, message=raw_payload=raw, parse_status=fallback. Không giữ field parse dở vì dễ tạo record nửa hợp lệ. Không dùng fallback để đạt tỷ lệ parse đúng.

Chọn một mã lỗi theo thứ tự kiểm tra dưới đây; chi tiết nội bộ không chứa secrets hoặc stack trace trong record:

| Thứ tự | Điều kiện | parse_error |
|---|---|---|
| 1 | raw rỗng | empty_input |
| 2 | vượt trần bytes được duyệt | payload_too_large |
| 3 | ký tự control ngoài terminal LF/CRLF hợp lệ | malformed_header |
| 4 | nhận diện ISO/RFC5424 hoặc Fortinet KV ngoài scope | unsupported_format |
| 5 | không bắt đầu bằng `<` | missing_pri |
| 6 | PRI sai cú pháp/ngoài miền | invalid_pri |
| 7 | phần header còn lại sai cấu trúc | malformed_header |
| 8 | ngày/giờ không hợp lệ | invalid_timestamp |

Regex recognition unsupported chỉ là dispatch tối thiểu, không validate đầy đủ format khác. Payload không nhận diện thuộc format khác tiếp tục qua kiểm tra PRI/header.

## 7. Bản nháp ca kiểm thử để QA review

Trạng thái chung: NEEDS OWNER REVIEW / NOT RUN. Đây là input/expected đề xuất, chưa thay đặc tả QA chính thức. Môi trường dự kiến Python 3.12, Pydantic v2; không network/DB. Mỗi ca chạy độc lập, không cần cleanup storage.

Mặc định: source_ip=10.10.0.10; received_at=2026-11-03T15:00:01Z; source_timezone=UTC+07:00; raw không có newline cuối. Với ca parsed lúc Nov 03 22:00:00: event_timestamp=2026-11-03T15:00:00Z, timestamp_inferred=true, parse_error=null; id là UUID4, schema_version=1.0, category=unknown, source/received/raw giữ đúng input. Ký hiệu F là toàn bộ expected fallback ở mục 6. Các field không nêu dùng quy tắc chung, không bỏ assert.

| ID | Input hoặc thay đổi so với mặc định | Expected chính | Truy vết |
|---|---|---|---|
| N15-01 | `<189>Nov 03 22:00:00 rtr-01 %LINK-3-UPDOWN: Gi0/1 down` | parsed; facility=23; severity=5; hostname=rtr-01; cisco; program=LINK; mnemonic=LINK-3-UPDOWN; message=`Gi0/1 down` | FR-04, TC-PAR-001 |
| N15-02 | `<133>Nov 03 22:00:00 rtr-01 %OSPF-5-ADJCHG: Neighbor down` | parsed; 16/5; cisco; program=OSPF; mnemonic=OSPF-5-ADJCHG; message=`Neighbor down` | FR-04 |
| N15-03 | `<131>Nov 03 22:00:00 ne-01 %%01DEVM/2/POWER_SUPPLY_FAILED: Power failed` | parsed; 16/3; huawei; program=DEVM; mnemonic=POWER_SUPPLY_FAILED; message=`Power failed` | FR-04, TC-PAR-004 |
| N15-04 | như N15-03, thêm `(l)` ngay sau FAILED | cùng output N15-03 trừ raw | FR-04 |
| N15-05 | `<34>Nov  3 22:00:00 host-01 sshd[123]: Login failed` | parsed; 4/2; linux; program=sshd; mnemonic=null; message=`Login failed` | FR-04 |
| N15-06 | `<0>Nov 03 22:00:00 host-01 kernel: test` | parsed; 0/0; linux; program=kernel; message=`test` | FR-04, TC-PAR-008 |
| N15-07 | `<191>Nov 03 22:00:00 host-01 customapp[42]: test` | parsed; 23/7; unknown; program=customapp; message=`test` | FR-04, TC-PAR-009 |
| N15-08 | `<134>Nov 03 22:00:00 host-01 plain content` | parsed; 16/6; unknown; program/mnemonic=null; message=`plain content` | FR-04 |
| N15-09 | N15-01 PRI lần lượt `<-1>`, `<192>`, `<abc>`, `<01>`, `<>` | F, invalid_pri cho từng biến thể | FR-05 |
| N15-10 | `Nov 03 22:00:00 host-01 test` | F, missing_pri | FR-05, TC-PAR-011 |
| N15-11 | chuỗi rỗng | F, empty_input | FR-05 |
| N15-12 | `<34>Nov 31 22:00:00 host-01 test`; giờ `25:00:00` trong header hợp lệ | F, invalid_timestamp cho từng biến thể | FR-05 |
| N15-13 | `<34>Bad 03 22:00:00 host-01 test` | F, malformed_header | FR-05 |
| N15-14 | `<34>Dec 31 23:59:59 host-01 kernel: test`; received=2027-01-01T00:00:01Z, timezone=UTC | parsed; event_timestamp=2026-12-31T23:59:59Z; 4/2; linux | FR-04 |
| N15-15 | `<34>Jan  1 00:00:01 host-01 kernel: test`; received=2026-12-31T23:59:59Z, timezone=UTC | parsed; event_timestamp=2027-01-01T00:00:01Z | FR-04 |
| N15-16 | `<34>Feb 29 00:00:00 host-01 kernel: test`; received=2024-03-01T00:00:00Z, timezone=UTC | parsed; event_timestamp=2024-02-29T00:00:00Z | FR-04 |
| N15-17 | như N15-16, received=2026-03-01T00:00:00Z | F, invalid_timestamp (2025/2026/2027 đều không nhuận) | FR-05 |
| N15-18 | N15-05 content=`Cảnh báo: kết nối lỗi` và hậu tố CRLF | parsed; message giữ Unicode/dấu colon, không CRLF; raw giữ cả CRLF | FR-04 |
| N15-19 | raw chứa NUL hoặc newline giữa header/body | F, malformed_header | FR-05, TC-PAR-010 |
| N15-20 | `<134>2026-11-03T22:00:00+07:00 host-01 test` | F, unsupported_format; không gán parsed RFC3164 | FR-05, TC-PAR-012 cần chuyển scope |
| N15-21 | `date=2026-11-03 time=22:00:00 devname="fg-01" action="deny"` | F, unsupported_format; nhận diện dispatch Fortinet chưa phải parse đúng | FR-05, TC-PAR-006 cần scope riêng |
| N15-22 | bản tin RFC3164 valid ASCII dài đúng 1024 rồi 1025 bytes | 1024 parsed, 1025 F/payload_too_large; bổ sung Unicode đo bytes thay vì ký tự | FR-04/05 |
| N15-23 | source_ip=`not-an-ip`; received_at naive; raw=bytes | ValueError / ValueError / TypeError; không sinh AlertEvent | contract boundary |
| N15-24 | `<34>Nov 03 22:00:00 host-01 kernel: ` | parsed; message rỗng; program=kernel; 4/2; linux | FR-04 |

QA mở rộng model validation: facility=-1/24, severity=-1/8, bool/chuỗi số, vendor ngoài enum, extra field, datetime naive; xác nhận ValidationError. UUID random không được coi là lỗi replay. Các mã N15-* là ID cục bộ đề xuất, không tự đổi hay tạo mã TC-PAR chính thức.

### Corpus và evidence

- 24 dòng trên là nhóm ca, chưa phải corpus AC-02. QA/BE2 chuẩn bị tối thiểu 200 mẫu có nhãn cho mỗi format được chấp nhận, có biến thể header/tag/thời gian; không tính sao chép một mẫu thành coverage đủ. Chốt định nghĩa format/vendor để xác định số corpus; Fortinet/RFC5424 chưa tính đã được hỗ trợ bởi N42-15.
- Fixture đề xuất JSONL gồm case_id, raw, source_ip, received_at, timezone offset, expected đầy đủ trừ UUID sinh mới, requirement và fixture version. Gắn SHA-256 cho file.
- Evidence path dự kiến `artifacts/N42-15/<commit-sha>/<run-id>/`: environment.json, fixture-manifest.json, expected-vs-actual.jsonl, pytest.xml, benchmark.json. Chưa tạo artifact hoặc ghi PASS khi chưa chạy.
- Run record có commit, UTC timestamp, Python/Pydantic/OS/CPU, cấu hình, tổng parsed/fallback/failed, IDs ca và status. QA quản lý evidence tích hợp; BE2 lưu unit/benchmark module.

## 8. Phép đo hiệu năng đề xuất

Mục tiêu ticket: >=5.000 log/s trên một nhân CPU. Không thay KPI end-to-end >=1.000 msg/s trong một giờ của AC.

Benchmark toàn hàm trả AlertEvent (regex, datetime, UUID, validation), một process/một thread, CPU affinity một logical CPU; ghi rõ CPU/core/SMT. Đọc fixture trước khi tính giờ, warm-up 10.000 calls, đo 5 lượt x 100.000 calls bằng perf_counter. Giữ nhận dạng/mix corpus cố định, có cả fallback; report từng format và mix, số lỗi, checksum output và throughput từng lượt. Không bỏ validation/Pydantic hoặc UUID để làm đẹp số đo. Đề xuất pass khi cả 5 lượt mix >=5.000 log/s và output đúng; threshold/lượt đo cần QA xác nhận. Không chạy trong pytest mặc định để tránh flaky CI.

## 9. Quyết định cần review và điều kiện bắt đầu code

| ID | Nội dung cần xác nhận | Người review |
|---|---|---|
| OPEN-01 | Schema, tên field, enum, nullable và schema version | BE2 đề xuất; BE1/BE3, TL xác nhận; thông báo FE |
| OPEN-02 | AlertEvent fallback vs ParseError/QuarantineRecord; không đưa fallback vào correlation | BE1/BE2/BE3, TL |
| OPEN-03 | Năm/timezone, profile ngày padding, leap second, giới hạn bytes | BE2/BE1, QA |
| OPEN-04 | Fortinet/RFC5424/vendor parsing sâu nằm ở ticket nào; mapping M2 | TL và code owners |
| OPEN-05 | Expected output, corpus >=200/format, benchmark và evidence | QA chủ trì, BE2 xác nhận |

Hiện tất cả OPEN-* chưa xác nhận. Tài liệu này không tự cập nhật Jira hay decision log thành ĐÃ CHỐT. Trước code hành vi: ticket liên kết bản review được chấp thuận, test input/expected/boundary và RTM; owner/dependency và WIP được đối chiếu trên Jira. Sau khi duyệt, ghi quyết định thực tế và đồng bộ INTERFACES/TDD/data design/test specification/RTM trước khi tạo phụ thuộc liên module.

## 10. Kế hoạch triển khai sau phê duyệt

1. Dùng nhánh ticket `feature/N42-15-alertevent-parser`, kiểm tra nhánh đã tồn tại và thay đổi đang có trước khi tạo/chuyển.
2. Tạo model `app/models/alert_event.py`, parser `app/services/parser.py`; khai báo dependency Pydantic v2 trực tiếp nếu code import, không chỉ dựa vào dependency bắc cầu FastAPI.
3. Tạo fixtures và `tests/test_parser.py` theo bản test được duyệt; chạy pytest riêng parser rồi regression health.
4. Benchmark và lưu evidence thực; sửa lỗi trước khi lập PR.
5. PR về main có trace FR/AC/test, khác biệt contract và evidence; TL review theo policy nhóm, không push thẳng main. Chưa ghi task Done nếu thiếu corpus/KPI/evidence hoặc approval được yêu cầu.

## 11. Review record

| Vai trò | Kết quả / ngày / link evidence |
|---|---|
| BE2 - Phạm Tấn Thành | Chờ review nội dung đề xuất |
| BE1 - Phạm Hoàng Long | Chờ xác nhận đầu vào và boundary |
| BE3 - Nguyễn Duy Minh | Chờ xác nhận schema và fallback |
| QA - Ngô Châu Kiệt | Chờ review coverage/expected/benchmark |
| TL - Phạm Minh Nhựt | Chờ ghi nhận quyết định/phạm vi sau review |
