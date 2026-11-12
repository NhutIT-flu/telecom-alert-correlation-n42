# N42-17 — Code đã triển khai theo ủy quyền người dùng

## Đối chiếu sau merge main — 12/11/2026

Đã lưu code N42-17 tại commit507b4eb và hợp nhất origin/main1a12b22 vào nhánh feature.
Giữ mapping Jira mới của main trong TCS/RTM cùng TC-RUL008–012 của N17;
requirements chỉ giữ một dòng pydantic>=2.9.0,<3 và giữ ruamel.yaml.
Toàn suite sau merge:130tests và10subtests PASS trên Python3.12.16.
Flake8 toàn app/tests/tools:0finding; Black22file Python:PASS. Các14finding lint của
baseline N17 bên dưới đã được main sửa và không còn sau merge. Chưa xác nhận CI remote.
Parser/frontend/generator từ main được giữ; node_modules/reports cục bộ không vào commit.
Các thông tin HEAD/patch chưa commit và kết quả68tests bên dưới là lịch sử trước merge.

Nhánh feature/N42-17-rules-yaml-design, HEAD baseline883d048; patch chưa commit.
Người dùng cho phép tự quyết thiết kế và code trước, báo lại để xin QA/TL phê duyệt sau.

## Code chạy chính

- app/models/rule_config.py: window1..86400s, threshold1..10000; text caps
  version64/rule_id128/name120/description1000/title200; incident severity enum
  CRITICAL/MAJOR/MINOR/WARNING/INFO. Giữ strict types, extra forbid, uniqueness.
- Model validator kiểm rule bật có supported_event_fields từ context; mọi field
  match/group_by/count.field phải được contract cung cấp. Rule tắt nhận field proposed.
- app/services/rule_config_loader.py: giữ hàm trả RuleConfiguration; thêm keyword
  supported_event_fields và expected_sha256. Đọc bytes1lần, pinSHA256 trước decode/YAML/schema.
  Mismatch/malformed pin ValueError; lỗi I/O/UTF8/YAML/Pydantic vẫn nguyên loại.
- app/services/rules.yaml: version0.1.1, LinkFlap MAJOR;3rule vẫn disabled.
  LF5/60; PSU2distinctslots/60; BGP3statechanges/120, hai mẫu sau là lựa chọn lab.

## Kiểm chứng

68/68 tests PASS trên Python3.12.16 và3.14.2 (64 config + 2 health + 2 startup).
Coverage Python3.14:81/81 statements,16/16 branches=100% code hiện có.
Flake8/Black phần N17 PASS. Repo Flake8 còn14finding baseline ngoài phạm vi.
AIkit0error/5warning. Security pattern scan riêng phần thay đổi, xem checks.json/log.
Không có CI run hoặc engine/reload execution. Coverage/lint3.12 bị policy DLLWindows
chặn; kiểm các phần này trên3.14, không đổi policy. Warning pytest-asyncio giữ trong log.

## Cần phê duyệt sau triển khai

QA/TL xác nhận caps, severity enum/MAJOR, field capability contract, digest pin và fixture
nguồn kép; chốt field/taxonomy producer N23/24/26/62/65. QA/TL ký thật vẫn pending,
không ngăn local implementation theo ủy quyền user. Cần CI đúng patch, reviewer và merge.
Không triển khai detector/dedup/reload/parser/DB trong N17. No production activity.

Evidence local: specs/001-n42-rule-config/evidence/manifest.json,checks.json,JUnit,
coverage-py314.json,decision-record.md. specs/ bị localGitexclude; code/test/docs ở
working tree và file mới untracked, chưa commit/push. Khi tạo PR phải đính kèm evidence.


## Startup integration — 12/11/2026

FastAPI lifespan nạp rules.yaml bằng loader thật trước khi nhận request; lưu tại
app.state.rule_configuration. Invalid config làm startup thất bại; không có API mới,
engine hoặc reload. TC-RUL-012: startup hợp lệ nạp3mẫu tắt/version0.1.1, startup invalid
catalog bị ValidationError. Test thực tế tests/test_rule_startup.py. Code owner BE3.
Đây là tích hợp M5 theo ủy quyền triển khai, không suy field producer đã được phê duyệt.
