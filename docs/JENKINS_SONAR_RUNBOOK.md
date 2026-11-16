# Jenkins và SonarQube — Python 3.12, tự chạy main và Quality Gate

N42-10 · 12/11/2026 · yêu cầu do Ngô Châu Kiệt xác nhận, chờ review và triển khai.

## Cấu hình nguồn và giới hạn

- Job chính: Pipeline script from SCM, Git repo của nhóm, branch specifier `*/main`, Script Path `Jenkinsfile`.
- Job thử nghiệm `N42-CI-Test-Feature`: `*/feature/N42-10-ci-pipeline`. Dùng để kiểm checkout, môi trường, test và smoke; hai stage Sonar/Gate sẽ SKIPPED theo chủ đích.
- Pipeline nhận branch từ kết quả `checkout scm`; nếu không xác định được thì fail. Checkout chỉ một lần, không tự checkout lại main giữa các stage.
- SonarQube Community hiện dùng chung project `n42-telecom-alert`. Không dùng analysis feature để ghi đè project chính. Nếu cần thử scanner/Gate trước merge, tạo project và credential thử nghiệm riêng, cùng một bản Jenkinsfile dành cho thử nghiệm; không đổi job chính để build feature vào project chính.
- Python 3.12 là minor version được chốt; patch có thể cập nhật theo image `python:3.12-slim-trixie`. Dockerfile dựng cùng Debian 13 với Jenkins và kiểm import SSL/SQLite/bz2/lzma/ctypes/venv khi build.

## Pipeline mới

Checkout → Python 3.12/dependencies → UDP preflight → lint/AI kit → scan → unittest/pytest/coverage → health smoke → Sonar analysis main → Quality Gate main.

`requirements.txt` là file dependency duy nhất. Pipeline không tự upgrade pip hoặc đổi phiên bản package ngoài file này. `.venv` được tạo lại bằng `python3.12 -m venv --clear` trong workspace riêng của job; virtualenv Python 3.13 cũ được thay thế, không xóa volume Jenkins.
Build tối đa 30 phút, cài dependency tối đa 10 phút, smoke tối đa 2 phút, analysis và Gate mỗi bước tối đa 10 phút (còn chịu timeout tổng). Build đồng thời của cùng job được xếp hàng. Giữ tối đa 20 build.
Artifact được lưu từ `reports/**` và `.scannerwork/report-task.txt`; JUnit được publish nếu report có tồn tại. JUnit lỗi vẫn cố archive artifact. Không có report khi bước trước test đã lỗi là tình huống có thể xảy ra, không tự báo test PASS.
`reports/environment.json` ghi Python/package/SHA/job/build; `reports/quality-gate.txt` ghi Gate đã nhận. Sonar đọc `reports/coverage.xml`, chỉ phân tích Python 3.12. Giữ exclusion coverage của tools theo profile hiện tại, không coi coverage app là coverage toàn repo.

## Cập nhật image Jenkins sau khi thay đổi được review

Build và recreate **chỉ service Jenkins** khi không có build quan trọng đang chạy:

```powershell
docker compose build jenkins
docker compose up -d --no-deps jenkins
docker exec n42-jenkins python3.12 --version
```

Recreate gây gián đoạn giao diện/build Jenkins trong thời gian ngắn. Không dùng `docker compose down -v`; giữ volume `jenkins_data` cùng dữ liệu DB/Sonar. Pipeline chưa push thì Jenkins SCM vẫn đọc bản cũ; build image không tự đưa diff local lên GitHub.

## Tự động khi main có cập nhật

Môi trường đã chốt là Docker trên localhost. Pipeline chỉ dùng SCM polling `H/5 * * * *`, không cần public Jenkins hoặc tạo webhook GitHub. Polling kiểm tra thay đổi Git, không chạy build định kỳ nếu nhánh không đổi. Máy, Docker Desktop và Jenkins cần hoạt động, có kết nối GitHub.
Job chính dùng đúng repo và `*/main`. Sau khi Jenkinsfile mới đã ở `main`, chạy Build Now **một lần** để Jenkins đăng ký trigger và checkout baseline. Tương tự, job feature cần Build Now sau khi bản mới được push lên nhánh feature. Sau đó thay đổi được phát hiện ở các lượt polling cách nhau khoảng 5 phút; thời gian build còn phụ thuộc hàng đợi.
Trong Configure → Build Triggers, kiểm Poll SCM có lịch trên; bỏ chọn GitHub hook trigger nếu còn cấu hình tay từ lần thử trước. Dùng SCM Polling Log để đối chiếu lần phát hiện thay đổi. Không đặt token/secret trong Jenkinsfile.
Push feature không nên kích hoạt build main nếu main không đổi; merge PR cập nhật main sẽ được job chính phát hiện. Cấu hình này không tự tạo required status check hoặc chặn merge GitHub; ruleset được kiểm tra riêng.

## SonarQube và webhook Quality Gate

Giữ Jenkins server config `SonarQube-N42`, URL `http://sonarqube:9000`, credential hiện có `sonarqube-token` và scanner tool `SonarScanner` (ảnh hiện tại 8.3.1.16491). Đây là tên/ID, không phải nội dung token.
`withSonarQubeEnv` dùng cấu hình này; log cũ đã xác nhận inject thành công dù checkbox Environment variables trên System chưa bật.

SonarQube project → Project Settings → Webhooks → Create:

- Name: `Jenkins N42 Quality Gate`.
- URL: `http://jenkins:8080/sonarqube-webhook/` khi cả hai container ở network Compose hiện tại. Dấu `/` cuối cần giữ.
- Có thể cấu hình webhook secret ở Sonar và credential Secret text tương ứng trong Jenkins → System → SonarQube-N42 → Advanced → Webhook Secret. Không dùng lại analysis token làm webhook secret.

URL nội bộ trên dành cho **Sonar → Jenkins** và vẫn cần dù Jenkins lấy code bằng polling. Không dùng localhost: localhost trong container Sonar là chính container Sonar. Xem Last Delivery của webhook có 2xx, task ID phải thuộc analysis cùng build.
Với Community Build v26.11.0.134175 trong lab này, validation chặn URL nội bộ. Người dùng đã tắt **Enable local webhooks validation** (`sonar.validateWebhooks`) trong Administration → Configuration → General Settings → Security và tạo webhook thành công. Thiết lập này áp dụng toàn instance và cho phép webhook tới mạng nội bộ; chỉ giữ trong lab do nhóm quản trị. Chưa có bằng chứng Last Delivery hoặc Quality Gate của pipeline mới. Xem [giải thích của SonarSource](https://community.sonarsource.com/t/validating-webhooks-breaks-our-ci/189245).
Jenkins gọi `waitForQualityGate()`, chỉ `OK` mới tiếp tục; status khác gọi `error()` nên build FAILURE. Webhook thiếu/hỏng có thể khiến chờ đến timeout; pipeline lưu TIMEOUT và kết thúc FAILURE. Hủy thủ công giữ ABORTED. Không thêm `sonar.qualitygate.wait=true` đồng thời vì pipeline đã có bước chờ riêng.
Không tự hạ Quality Gate để làm xanh build. Ảnh cũ Passed nhưng Security D/2 issues cần đọc Issues và điều kiện gate/new code; Passed không có nghĩa không có issue bảo mật.

## Checklist kiểm chứng sau triển khai

1. Xem console Python 3.12.x, SHA checkout và tên branch main; lint/test/scan/smoke đạt, coverage file của chính build.
2. Sonar analysis trả task ID, Gate nhận `OK`, Jenkins SUCCESS; Dashboard hiện đúng lần phân tích/revision.
3. Trên môi trường/project thử nghiệm riêng, kiểm gate không OK làm FAILURE; webhook lỗi làm build dừng theo timeout. Không cố ý làm lỗi gate của project chính để thử.
4. Merge một thay đổi đã review vào main; không bấm Build Now; lưu SCM Polling Log, build cause và build SHA để chứng minh tự động. Push feature mà main không đổi không được tạo build main mới.
5. Job feature không có stage analysis chạy, không làm thay đổi Last analysis của project Sonar chính.

Log người dùng gửi ngày 12/11 là build commit 8f8b7a6, Python 3.13.5, 6 test; scanner upload thành công. Không dùng kết quả đó để xác nhận Jenkinsfile/image mới.

## Nguồn kỹ thuật

- [Pipeline syntax](https://www.jenkins.io/doc/book/pipeline/syntax/): trigger/options/timeout/checkout/concurrency.
- [SonarQube Community pipeline pause](https://docs.sonarsource.com/sonarqube-community-build/analyzing-source-code/ci-integration/jenkins-integration/pipeline-pause): withSonarQubeEnv, webhook bắt buộc và waitForQualityGate.

## Cập nhật triển khai 13/11/2026

Xem [vận hành và backup](N42-10_OPERATIONS.md), [kế hoạch/ca nghiệm thu](N42-10_UPGRADE_PLAN.md) và [nhật ký thực thi theo revision](N42-10_EXECUTION_2026-11-13.md).
Jenkinsfile có SONAR_REVIEW (mặc định false); feature review chỉ dùng project n42-telecom-alert-ci-validation, main dùng project chính. Build feature bỏ qua Sonar không được dùng làm minh chứng Gate.
Gate timeout được bắt và lưu TIMEOUT/FAILURE; hủy thủ công giữ ABORTED. Review #2/#4 trên b349700 đã kiểm chứng timeout/hủy; review #10/#11 trên d249e57 kiểm chứng ERROR/FAILURE và OK/SUCCESS, có webhook HTTP 200 đúng task ID.
Backup đã restore cách ly thành công. Snapshot local mới nhất chạy đầy đủ pipeline với 64 unittest, 162 pytest và 644 subtest đạt, Gate OK; kết quả snapshot không thay thế run của commit sắp push.
Job chính vẫn lấy Jenkinsfile từ main và cần xác minh bản nâng cấp sau merge. Required checks còn cần chủ repo; không tự merge PR hoặc dùng evidence cũ như kết quả revision mới.
