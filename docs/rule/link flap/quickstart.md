# Quickstart validation — Link Flap module

**Tình trạng hiện tại**: Hướng dẫn chạy **sau implementation**; file source/test/migration mới được liệt kê là dự kiến. Lượt plan chưa chạy các lệnh ứng dụng, cài dependency hoặc khởi động DB.
**Implementation root**: `C:/Projects/vnpt/telecom-alert-correlation-n42`.
**Contracts**: [module](contracts/rule-module.md), [ingress](contracts/ingress-and-progress.md), [delivery](contracts/decision-delivery.md).

## 1. Prerequisites

- Python3.12 và môi trường dự án có requirements, gồm driver psycopg[binary] mới sau implement.
- PostgreSQL16/TimescaleDB lab từ Compose; không dùng database production. Synthetic fixtures, mỗi integration run dùng schema riêng do test tạo và dọn đúng schema đó.
- Producer/consumer test adapter cho unit/component. Bài tích hợp production cần provider progress và consumer thật; fixture fake không thay được.
- N42_CORRELATION_TEST_DSN cung cấp qua môi trường local, không commit/log credential. Runtime dùng N42_CORRELATION_DSN. Không hardcode DSN trong module.
- README-local ghi nhận .venv từng thiếu ruamel.yaml; kiểm tra lại import, không lấy báo cáo test lịch sử làm kết quả lần này.

```powershell
Set-Location C:/Projects/vnpt/telecom-alert-correlation-n42
.\.venv\Scripts\python.exe -c "import sys, pydantic, ruamel.yaml, psycopg; print(sys.version); print(pydantic.__version__)"
```

Nếu import thiếu, dùng quy trình dependency của repo để cập nhật môi trường trước khi chạy; lượt plan không thay .venv.

## 2. Database setup (lab, sau khi migration được viết)

```powershell
docker compose up -d db
docker compose exec -T db pg_isready -U n42 -d n42
Get-Content -LiteralPath docker/migrations/001_correlation_state.sql | docker compose exec -T db psql -U n42 -d n42 -v ON_ERROR_STOP=1
```

Expected: DB sẵn sàng, versioned migration thành công, năm bảng metadata xuất hiện. Migration phải có kiểm tra phiên bản; chạy lại không làm mất state. Bootstrap init-db.sql không được dùng như migration cho volume đã tồn tại. Không chạy down migration/drop volume để reset.

Integration tests tự tạo schema riêng và apply cùng migration trong schema đó, chỉ cleanup schema do run tạo; không dùng bảng lab đang chạy để assert data rỗng.

## 3. Unit/config/module validation

```powershell
.\.venv\Scripts\python.exe -m pytest tests/correlation/test_contracts.py tests/correlation/test_link_flap.py tests/correlation/test_engine.py tests/correlation/test_runtime.py tests/test_rules_config.py tests/test_rule_startup.py -q -p no:cacheprovider
```

Expected:

- Baseline UP tại −1s, transitions 0D/10U/20D/30U/40D → đúng một trigger tại 40, total=5, episode_start=0, due=160.
- Không baseline, cùng năm observations → bốn transitions, không trigger; thêm UP tại 50 → trigger, total=5.
- 0/15/30/45/60 có baseline → trigger; đổi event cuối thành 60.001 → không trigger.
- DOWN lặp tại 45/100/159 không đổi due160; transition 50/100 → total7, Q100=3, due220.
- Due−1ms kéo dài đợt; đúng due tách đợt trước event; worker trễ cho cùng kết quả.
- Timer thiếu progress hoặc health suy giảm giữ mở có lý do; LAST_OBSERVED không khẳng định link đã UP.
- Thêm rule kiểm chứng không đổi kết quả Link Flap, không sửa shared snapshot; rule lỗi rollback.
- Config LF typed, enabled thiếu capability fail-fast; hai rule khác disabled, disabled startup không đòi DB.

Không dùng sleep 60/120s: fake clock và input timestamps chính xác.

## 4. PostgreSQL/integration validation

Sau khi đặt N42_CORRELATION_TEST_DSN qua môi trường:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/correlation/test_postgres.py -q -p no:cacheprovider
```

Nhóm test DB phải **fail rõ nếu DSN vắng hoặc DB unavailable** khi gọi trực tiếp, không skip rồi báo pass. Unit suite tách độc lập. CI hiện đã có service DB; khi implement phải cung cấp DSN và chạy nhóm này rõ ràng.

Expected: receipt retry/collision đổi entity; rule thứ hai lỗi không lưu nửa event; state+timer+outbox commit atomically; stale owner/timer không ghi được; repetition tăng version không vô hiệu timer generation; restore cùng episode và total.

Test cancellation sau thread commit phải retry cùng ID mà không thêm effect. Outbox consumer test nhận duplicate/gap/xuyên đợt và chỉ áp dụng một lần hiệu lực. Link Down command trễ sau UP không tạo DOWN cũ.

## 5. Fence và adapter acceptance

Component test dùng durable state + producer test adapter để tái hiện raw nhận trước due còn chưa normalize: worker phải block tới khi proof đầy đủ. Stage event đúng due, timer kết thúc trước observe event đó.

Khi tích hợp producer thật, chạy lại cùng tình huống qua raw journal thật, heartbeat khi im lặng, health đổi giữa proof và commit, source gap, restart/backlog. Consumer thật phải chứng minh receipt/open slot và stream ordering. Chưa có adapters này thì chỉ ghi PASS cho module/component, luồng production ghi NOT RUN hoặc dependency chưa sẵn sàng.

## 6. Regression / evidence

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
.\.venv\Scripts\python.exe tools/check_sensitive.py .
```

Full suite chỉ chạy sau khi DSN test đã chuẩn bị; marker/CI selection phải rõ. Run record ghi commit nguồn, Python/dependency versions, fixture/catalog hash, DB version, kết quả theo test group và dependency nào dùng fake. Không sửa actual_engine=not_run thành passed trong fixture dựa trên expected.

Chạy startup mặc định với các rule disabled và xác nhận /api/health giữ hành vi. Bật LF trong cấu hình test với capability đầy đủ để kiểm chứng runtime; missing provider phải startup fail có reason. Không sửa catalog production thành enabled chỉ để demo.

Load profile là bước đo riêng sau tính đúng; báo throughput, latency, backlog, timer delay và lỗi thực đo, chưa nhận các số lab của tài liệu thành năng lực hệ thống.

Riêng outbox kiểm tra recovery cuối DOWN tạo DECISION và COMMAND ở hai stream: trigger đợt tiếp theo phải có DECISION sequence liền trước, không bị gap do command. Phía nhận command lưu receipt và effect cùng transaction; crash sau apply trước ACK không tạo Link Down trùng.

## 7. Rollout / rollback

Trước code: liên kết ticket/owner, test/expected và RTM theo AGENTS; không dùng tên nhánh N42-18 hiện tại như ticket Link Flap. Tạo branch đúng ticket khi tới implement.

Rollout với LF disabled, apply additive migration, chạy acceptance, cấu hình đúng producer/consumer rồi mới enable. Nếu cần rollback code/config, ngừng admission, drain/checkpoint và giữ snapshot/timer/outbox cùng config pin; không xóa dữ liệu hoặc gọi đợt ACTIVE là recovered do rollback.

