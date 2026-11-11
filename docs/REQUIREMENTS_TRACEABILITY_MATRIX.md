# MA TRẬN TRUY VẾT YÊU CẦU — N4.2

Ma trận này là kế hoạch bao phủ FR/NFR đến tiêu chí nghiệm thu, mã ca kiểm thử và evidence cần thu. Mã test trong ma trận là mã đặc tả trong `TEST_CASE_SPECIFICATION.md`; không đồng nghĩa đã tự động hóa hoặc đã chạy.

## 1. Quy ước trạng thái

- **Đặc tả:** Có mô tả ca kiểm thử, chưa có bằng chứng chạy.
- **Một phần hiện thực:** Có code cho một phần yêu cầu; cần test đúng contract hiện tại.
- **Gap:** Chưa có ca cụ thể hoặc chưa đủ acceptance/evidence để kết luận.
- Chỉ ghi **PASS/FAIL** trong execution record có commit SHA, thời gian, môi trường, input/version và artifact. Không ghi kết quả dự kiến như kết quả thực tế.

## 2. Truy vết yêu cầu chức năng

| Requirement | AC | Owner | Mã ca kiểm thử đặc tả | Evidence cần thu | Hiện trạng repo |
|---|---|---|---|---|---|
| FR-01 UDP ingest | AC-01 | BE1 | TC-ING-001–006, 014–015; TC-INT-001, 004 | Fixture/IDs gửi nhận, counters, raw/event đã lưu, log | Chỉ health endpoint; receiver chưa có |
| FR-02 REST ingest | AC-01 | BE1/BE2 | TC-ING-007–010; TC-INT-004 | Request/response, status, event ID và persistence result | Chưa có endpoint ingest |
| FR-03 File import | AC-01, AC-07 | BE1/QA | TC-ING-011–013; TC-SEC-006 | File fixture, report theo dòng, encoding/duplicate/path cases | Chưa có importer; quy tắc encoding/idempotency cần chốt |
| FR-04 Parser/normalization | AC-02 | BE2 | TC-PAR-001–009, 012 | Corpus ≥200 mẫu/format đã chốt; expected/actual từng field, error counts | Parser chưa có; các mẫu hiện có chưa đạt corpus AC-02 |
| FR-05 Parse fallback | AC-02 | BE2 | TC-PAR-010–011; TC-ING-003 | Malformed input, raw giữ nguyên, parse status, không crash | Chưa có parser/pipeline |
| FR-06 Durable storage | AC-07 | BE2 | TC-DB-001–004; TC-INT-001, 003 | Migration, write/read/restart/restore, ID reconciliation | Chưa có model/bảng/repository; DB chưa nối runtime |
| FR-07 Query/filter/pagination | AC-03 | BE2/FE | TC-UI-002–003; TC-SEC-004; TC-PERF-008 | Dataset/version, filter correctness, pagination ổn định, latency/config | Chưa có query endpoint |
| FR-08 Statistics | AC-04 | BE2/FE | TC-UI-001; TC-DB-003 | Known dataset, expected aggregates, API actual | Chưa có statistics endpoint |
| FR-09 Correlation | AC-05, AC-06 | BE3 | TC-COR-001–011; TC-INT-002 | Rule/version, event/evidence IDs, TP/FP/FN, raw/incident/standalone counts | Engine chưa có; semantics time-boundary, late event và multi-rule cần chốt |
| FR-10 Incident lifecycle | AC-04 | BE3/FE | TC-COR-007, 012; TC-DB-004; TC-INT-002 | State transition, actor/time/audit, persistence và API result | Lifecycle/audit chưa có; bổ sung mutation tests sau khi contract được duyệt |
| FR-11 Dashboard | AC-04 | FE | TC-UI-001–006; TC-INT-001–002; TC-SEC-005 | Checklist UI, API contract, recording, loading/error/empty, keyboard and XSS evidence | Frontend chưa có; phụ thuộc API chưa triển khai |
| FR-12 Health/diagnostics | AC-08 | BE1/BE2 | TC-HLT-001–004; TC-SEC-003 | Liveness/readiness, dependency failure, field allowlist, metric deltas | Có `GET /api/health` liveness với 2 unit checks; chưa có readiness/dependency/counters |
| FR-13 Deterministic replay | AC-01, AC-05 | QA | TC-REP-001 | Seed, fixture version, deterministic payload/order, expected labels and result | Chưa có replay harness/ID strategy; test blocked |
| FR-14 Export | AC-04, AC-08 | FE/BE | TC-EXP-001 | Filter equivalence, delimiter/quote/newline escaping, size limit, file integrity | Chưa có contract/export endpoint; format/limit cần chốt, test blocked |
| FR-15 Rule configuration | AC-05 | BE3 | TC-RUL-001–007 | Schema/version, invalid cases, active hash trước/sau reload, rollback/audit | Rule service/API chưa có; schema/path/response phải chốt trước automation |

## 3. Truy vết yêu cầu phi chức năng

| Requirement | AC | Mã ca kiểm thử đặc tả | Evidence/định nghĩa đo | Hiện trạng |
|---|---|---|---|---|
| NFR-01 Throughput | AC-01 | TC-PERF-001, 002, 004 | ≥1,000 msg/s trong checkpoint 10 phút và final 1 giờ; generator/receiver IDs, config, commit | Chưa có receiver/load runner; không có kết quả đo |
| NFR-02 Latency | AC-03 | TC-PERF-003 | Xác định rõ start/end timestamp; báo P50/P99, không lấy thời gian generator gửi đơn lẻ | Chưa có pipeline để đo |
| NFR-03 Observed drops | AC-01 | TC-ING-014; TC-PERF-001, 002 | Gửi/nhận/persisted ID reconciliation và OS/socket counters; 0.00% ở final | Chưa đo; UDP loss chỉ có thể báo là observed theo giới hạn đo |
| NFR-04 Resource use | AC-01 | TC-PERF-001, 002, 005 | CPU/RAM, core quota, process/container scope, warm-up và sampling | Chưa đo |
| NFR-05 Parser/query | AC-02, AC-03 | TC-PAR-001–012; TC-PERF-008; TC-DB-003 | ≥200 labeled samples/format; query dataset 1M; expected/actual và cấu hình | Parser/DB/query chưa có |
| NFR-06 Safe synthetic data | AC-08 | TC-SEC-001–003; TC-HLT-003; TC-OPS-002 | Scan report gắn commit; rà fixtures/config; isolated lab evidence | Có script scan nhưng hiện không trả non-zero exit khi tìm thấy finding; cần sửa trước khi dùng làm CI gate. Chưa có report chạy gắn commit |
| NFR-07 Install/recovery | AC-07 | TC-INT-003; TC-PERF-007; TC-OPS-001, 003 | Clean install/restart/restore, thời gian, config/commit, ID reconciliation | Chưa có persistence/runtime stack và gói bàn giao hoàn chỉnh để chạy drill |
| NFR-08 Bounded processing | AC-01, AC-07 | TC-ING-014; TC-PERF-004, 006 | Queue depth, saturation/backpressure/drop policy, recovery, resource samples | Queue chưa có; cần thêm ca rõ cho queue full và recovery |

## 4. Bao phủ bàn giao và chất lượng dự án

Các mục sau không phải FR của sản phẩm, nhưng xuất hiện trong Charter, QA role, architecture và handover checklist nên cần bằng chứng trước khi đóng dự án.

| Cổng dự án | Nguồn | Mã ca/evidence | Tiêu chí kiểm tra | Hiện trạng |
|---|---|---|---|---|
| Build/CI gate | QA role, kickoff minutes, CONTRIBUTING | TC-OPS-002 | Sau khi QA triển khai workflow, đối chiếu checks với policy lint/test/security, xác nhận chúng chạy trên PR và lưu evidence; branch protection/required checks chỉ ghi là bật khi đã kiểm chứng | Owner: QA Lead (phối hợp DevOps/code owners); implementation được lên kế hoạch, chưa hoàn thành. Repo snapshot hiện chưa có `.github/workflows/ci.yml`. QA cần tạo workflow, ghi checks thực tế, chạy pass/fail có kiểm soát; branch protection/required checks chỉ ghi là bật khi đã kiểm chứng. |
| Docker/runtime | Handover, README, compose | TC-OPS-003 | Dựng đúng profile/service, health endpoint, dependency health, cấu hình/port/secret và dừng/khởi động lại | Compose hiện có DB và app profile scaffold; app chỉ health, DB chưa được nối. DB port map `5432:5432` và app `8080:8080` bind mọi interface; `POSTGRES_PASSWORD` có giá trị local hardcode, cần giới hạn loopback/lab và externalize trước khi dùng ngoài máy cô lập |
| Cài đặt sạch | AC-07, handover #2 | TC-OPS-001 | Máy sạch cài từ đúng gói bàn giao ≤1 giờ; demo pass; lưu video, commit, cấu hình và log | Chưa có pipeline nghiệp vụ/gói bàn giao hoàn chỉnh |
| Bộ scenario/replay | Charter, QA role, AC-05 | TC-REP-001; KB-01–08 | 8–10 scenario versioned, deterministic seed, expected labels và replay result | Có đặc tả KB-01..08; replay harness, fixture/generator đầy đủ và nhãn chuẩn chưa có. QA Lead sở hữu chuẩn bị/run tích hợp; code owner là BE theo module của từng KB; các KB hiện BLOCKED/NOT RUN do pipeline nghiệp vụ chưa sẵn sàng |
| Export/report | AC-04, FR-14, FE role | TC-EXP-001 | Export đúng filter đang xem; escaping/limit; nội dung đối chiếu được với query; format phải chốt | Export UI/API chưa có; PDF/CSV scope cần chốt |
| Tài liệu và sign-off | Document control, handover #3–8 | TC-OPS-004 | Tài liệu cùng baseline/version; report không ghi trạng thái chưa có evidence; approvals và package links thực | Có xung đột lịch/role/status liệt kê ở gap phía dưới; kickoff vẫn là draft |
| Bảo vệ dữ liệu | AC-08, architecture security | TC-SEC-001–003; TC-HLT-003 | Synthetic fixtures; loopback chỉ dùng local; không có secret/production data; scanner findings được review | Scanner hiện không trả exit code khác 0 khi có finding; cần remediation trước CI gate |

## 5. Baseline đã làm rõ và gap còn mở

- **Lịch W1/kickoff:** W1 là 01–07/11/2026; W2 là 08–14/11. Kickoff dự kiến 09/11 thuộc W2. Biên bản kickoff giữ trạng thái dự thảo cho đến sau họp; báo cáo tuần chỉ ghi kết quả sau khi đối chiếu Jira và evidence.
- **Phân module:** dùng FR + owner làm khóa truy vết. Mapping M1–M8 đã được đồng bộ giữa Charter, TDD và role files; cập nhật Jira trước khi tạo dependency liên module.
- **Kênh TCP:** SRS/AC baseline hiện gồm UDP, REST và file. TCP không nằm trong test nghiệm thu; chỉ thêm sau khi có decision, cập nhật FR/AC/RTM và Jira.
- **Workflow/release evidence:** `.github/workflows/ci.yml` chưa có trong repo hiện tại; QA Lead sẽ triển khai theo kế hoạch. Sau khi có workflow, đối chiếu checks, kết quả gắn commit, required status và bằng chứng release.
- **Scenario assets:** đã có đặc tả KB-01..08 với version, seed, input, expected outcome, phân công code owner theo module và QA runner. Fixture/generator/replay vẫn là công việc riêng; cả 8 case hiện BLOCKED/NOT RUN theo baseline, đặc tả không chứng minh scenario đã được chạy. Jira assignee phải được TL đối chiếu riêng.

## 6. Gap cần xử lý trước khi gọi đây là baseline kiểm thử hoàn chỉnh

### Đề xuất thiết kế N42-15 (09/11/2026)

[Bản thiết kế N42-15](N42-15_DESIGN.md) liên kết FR-04/FR-05 và AC-02 với các nhóm ca cục bộ N15-01..24, contract parser, corpus và evidence dự kiến. Trạng thái DRAFT / NEEDS OWNER REVIEW / NOT RUN; chưa thay thế TC-PAR chính thức, chưa chốt interface v0.9 và không thay đổi trạng thái Jira hoặc hiện trạng implementation trong các bảng trên. QA Lead review coverage; BE2 xác nhận expected output; TL cùng các owner xác nhận contract trước code hành vi.

1. **Contract-first:** `DATA_AND_API_DESIGN.md` ghi API/model nghiệp vụ là target. TC nào gọi `/api/v1/events`, `/api/v1/incidents`, WebSocket hoặc DB phải chuyển `BLOCKED` cho tới khi contract được duyệt và implementation xuất hiện. Hiện API có `GET /api/health`.
2. **Hoàn tất coverage còn thiếu:** Thực thi TC-REP-001, TC-EXP-001, TC-OPS-001–004 sau khi contract/gói bàn giao được chốt; bổ sung lifecycle audit/mutation, queue saturation/recovery, file import limits/encoding và query pagination edge cases.
3. **Parser corpus:** 5 fixture mẫu trong đặc tả chỉ là smoke examples, không đáp ứng 200 mẫu mỗi format ở AC-02.
4. **Correlation labels:** Đóng băng tập scenario, expected labels và quy tắc đếm TP/FP/FN; tránh coi mỗi event trong một chuỗi là một positive case nếu AC chưa định nghĩa.
5. **Execution:** Repo hiện có `tests/test_health.py` với 2 kiểm tra health route/service. Chưa có automated tests cho ingest, parser, storage/query, correlation hay rules. Tất cả các ca đó đang là đặc tả, chưa chạy/đạt.

## 7. Cách duy trì

Khi FR, API/schema, rule hoặc AC đổi, cập nhật SRS, thiết kế dữ liệu/API, acceptance criteria, test plan, test-case specification và ma trận trong cùng work item. Mỗi test phải truy ngược tới ít nhất một requirement; requirement chưa có test phải được ghi rõ là gap, owner và milestone.
