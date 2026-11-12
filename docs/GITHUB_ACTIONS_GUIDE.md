# GitHub Actions — N42-10

Ngày cập nhật 12/11/2026 · QA: Ngô Châu Kiệt · Nhánh `feature/N42-10-ci-pipeline`.
Nguồn: ticket N42-10, TC-OPS-002, TC-SEC-001–003, AC-08 và CONTRIBUTING.md.
Đây là thay đổi hạ tầng CI để review; không xác nhận đã bật branch protection hoặc đã chạy workflow mới trên GitHub.

## Phạm vi thay đổi

Giữ workflow `N42 CI Pipeline`, push trên `main`/`feature/**`, PR có nhánh đích `main`; thêm `workflow_dispatch` để chạy thủ công sau khi workflow được GitHub nhận trên nhánh mặc định.
PR từ fork vẫn dùng `pull_request`, không chạy mã PR qua `pull_request_target` và không cần repository secrets.
Quyền token chỉ `contents: read`; checkout không lưu credential. Không deploy hoặc sửa nội dung repository.

Job dùng Ubuntu 24.04 và Python 3.12. Pin nhãn Ubuntu đang dùng trong run cũ, thay vì tự chuyển theo `ubuntu-latest`; image Ubuntu vẫn nhận bản vá từ GitHub.
Concurrency tách theo workflow/event/ref, hủy lượt cũ cùng loại khi có lượt mới; push và PR có thể cùng chạy vì bảo đảm cả ref nhánh và merge ref được kiểm tra.

## Các nhóm kiểm tra

| Job | Nội dung | Evidence | Timeout |
|---|---|---|---|
| quality | Flake8, Black, validate AI kit; tiếp tục các bước độc lập khi bước kiểm tra trước lỗi và setup vẫn thành công | environment.json, flake8.txt, black.txt, ai-kit.txt | 10 phút |
| security | Scanner trên checkout; pipeline Bash giữ exit code khi dùng tee | environment.json, security-scan.txt | 10 phút |
| tests | unittest đúng lệnh trong ticket, rồi pytest gồm cả test hàm parser và coverage | environment.json, unittest.txt, pytest.txt, JUnit, XML/HTML coverage | 15 phút |
| smoke | Khởi động Uvicorn trên loopback/cổng ngẫu nhiên, kiểm nội dung JSON `/api/health`, đóng và thu hồi process | environment.json, uvicorn.log, health-check.json nếu đạt | 10 phút; bước smoke 2 phút |
| quality-and-security | Python tổng hợp bốn job; chỉ xanh nếu tất cả success. Failure/skipped/cancelled không được coi là success | Job Summary | 5 phút |

Giữ tên check cuối **Code Quality & Automated Tests** để thuận tiện kiểm tra required checks sau này. Đây chưa phải bằng chứng GitHub đã bắt buộc check đó trước merge. Khi review ruleset, chọn đúng check và nguồn phát, xác minh bằng PR thử nghiệm riêng.

Artifact có tên riêng theo job/run/attempt, giữ 14 ngày và được upload khi job lỗi nếu workflow chưa bị hủy. Job timeout/cancellation có thể không kịp upload; log GitHub vẫn là nguồn đối chiếu. Không giả định luôn có artifact khi install/setup thất bại.

Hiện tests và ứng dụng không kết nối DB. Bỏ service TimescaleDB và cấu hình mật khẩu tạm không được sử dụng khỏi workflow, không thay đổi Compose hoặc kế hoạch persistence. Smoke chỉ kiểm liveness/API health, không phải DB readiness. Khi có test DB thực, thêm job integration với version image cố định và evidence ghi/đọc/reset riêng.

## Dependency và định dạng

`.github/actions/setup-python-ci/action.yml` dùng chung Python, cache, cài `requirements.txt`, chạy `pip check`, ghi môi trường. Cache key theo file requirements duy nhất này.
`requirements.txt` gồm dependency ứng dụng, kiểm thử, coverage và kiểm tra chất lượng; dùng chung cho local, Docker, Jenkins và GitHub Actions. Do dùng một file, Docker cũng cài các công cụ QA/CI. Các dependency trực tiếp được ghim theo bộ đã chạy trên Python 3.12; **chưa phải lock toàn bộ dependency bắc cầu**. `environment.json` ghi các phiên bản thực tế để điều tra sai khác; không thu env tùy ý hoặc secret. Muốn tái lập đầy đủ sau này cần lock Linux/Windows có quy trình cập nhật riêng.

Đợt này không đổi `.flake8`, không đổi quy tắc Black và không tự đặt coverage threshold. Pin phiên bản công cụ giúp thống nhất môi trường; xử lý chính sách Flake8/Black được để sau cùng. Phần đồng bộ Jenkins/SonarQube được mô tả riêng trong [runbook](JENKINS_SONAR_RUNBOOK.md).
Giữ cả unittest và pytest vì ticket ghi rõ lệnh unittest. Có chạy lặp một số case; có thể bỏ lượt unittest riêng sau khi TL đồng ý vì pytest cũng thu thập unittest.

## Kiểm chứng trước khi push

```powershell
python -m pip install -r requirements.txt
python -m pip check
python -X utf8 tools/ci_checks.py metadata --reports reports/n42-10
python -X utf8 tools/ci_checks.py health --reports reports/n42-10
python -X utf8 -m unittest discover -s tests -p "test_*.py" -v
python -X utf8 -m pytest tests -q -p no:cacheprovider --junitxml=reports/n42-10/junit.xml --cov=app --cov-report=xml:reports/n42-10/coverage.xml
python tools/check_sensitive.py .
```

Health đợi startup log của chính process con để lấy cổng, mỗi request có timeout; luôn terminate/wait, kill nếu process không dừng sau 5 giây. Startup exit, JSON khác expected hoặc hết deadline phải trả mã khác 0. Không kết nối nhầm Jenkins/API khác đang dùng cổng 8000.

## Ma trận hồi quy CI

| Case cục bộ (TC-OPS-002/TC-SEC-003) | Input/điều kiện | Expected |
|---|---|---|
| CI-01 | API đúng build, health status UP/service/version đã biết | File health-check.json hợp lệ, process được đóng |
| CI-02 | API lỗi startup | Smoke đỏ, có log, không có health success |
| CI-03 | API chưa sẵn sàng hết deadline hoặc không dừng | Smoke đỏ, terminate rồi kill/wait có giới hạn |
| CI-04 | Health JSON DOWN/sai service/version | Smoke đỏ, cleanup process |
| CI-05 | Scanner gặp credential giả trong thư mục temp | Process scanner trả 1; fixture sạch trả 0; không để fixture giả trong repo |
| CI-06 | Pytest chạy test assert False trong thư mục temp | Process pytest trả 1 |
| CI-07 | Gate nhận bốn success | Gate trả 0 |
| CI-08 | Gate nhận failure/skipped/cancelled hoặc giá trị thiếu | Gate trả khác 0 |

Các ID CI-* là nhãn hồi quy cục bộ, không thay mã TC chính thức. Case lỗi có chủ đích là test xác minh bộ kiểm tra, không phải lỗi sản phẩm; chúng không tạo secret thật.

Sau push cần thu run URL/SHA, xem đủ bốn nhóm và check tổng hợp, tải artifact, kiểm tra metadata SHA thực tế. PR runs thường kiểm merge commit; metadata lưu checkout SHA và GITHUB_SHA. Kết quả Windows local không thay validation YAML/runtime trên Ubuntu GitHub. Chưa dùng kết quả cũ của PR #17 để tuyên bố diff mới đã xanh.

## Tham chiếu kỹ thuật

- [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax): permissions, timeout, needs, status expressions và explicit Bash có pipefail.
- [Concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency).
- [Runbook Jenkins/SonarQube](JENKINS_SONAR_RUNBOOK.md): Python 3.12, polling localhost và main-only Quality Gate.
- [Cổng merge và bàn giao N42-10](N42-10_HANDOVER.md): cấu hình đề nghị, checklist kiểm chứng và evidence.
