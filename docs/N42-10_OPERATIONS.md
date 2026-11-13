# Vận hành CI/CD đã khôi phục — N42-10

Ngày 13/11/2026. Compose chuẩn nằm ở gốc repo, project `telecom-alert-correlation-n42`.
`N42-CICD/docker-compose.yml` ngoài repo là điểm vào tương thích dùng `include`, không định nghĩa lại service.
Không dùng hai Compose khác cấu hình để recreate cùng container.

## Dữ liệu hiện có

| Container | Volume bền vững |
|---|---|
| n42-jenkins | n42-cicd_jenkins_data |
| n42-sonarqube | n42-cicd_sonar_data, n42-cicd_sonar_extensions, n42-cicd_sonar_logs |
| n42-db | telecom-alert-correlation-n42_n42-db-data |

Sonar dùng PostgreSQL database `sonarqube`; DB ứng dụng là `n42`. Không chỉ sao lưu Elasticsearch/sonar_data.
Các volume trên dùng `external: true` và tên chính xác: thiếu volume phải dừng và restore, không tạo volume rỗng để vượt lỗi.
Image Sonar/PostgreSQL và base Jenkins/Python được ghim digest; nâng phiên bản cần backup và kiểm compatibility riêng.

## Lệnh từ PowerShell

```powershell
./tools/cicd.ps1 status
./tools/cicd.ps1 start
# Chỉ khi không còn build cần giữ:
./tools/cicd.ps1 backup
./tools/cicd.ps1 stop
```

`start` có thể recreate Jenkins khi image/config đổi; không dùng thay cho kiểm tra trước nâng cấp.
Backup dừng Jenkins/Sonar, dump DB, dừng PostgreSQL để tar volume nhất quán rồi khởi động lại những service ban đầu đang chạy.
Lưu ngoài repo tại `../N42-CICD/backups/<timestamp>`, có manifest/checksum. File Jenkins chứa credential/khóa khôi phục: giữ riêng, không đính kèm PR.
Nếu backup lỗi, xem log và trạng thái dịch vụ; manifest không tự chứng minh backup hoàn chỉnh.
Không dùng Docker Desktop Reset/Clean dữ liệu hoặc xóa volume dữ liệu. Docker Desktop cần hoạt động sau đăng nhập; restart policy không tự mở Docker Desktop.

## Kết quả restore cách ly ngày 13/11

Backup `20261113_163418`: checksum PASS; giải nén Jenkins vào volume mới thấy hai job `N42-CI-Pipeline`, `N42-CI-Test-Feature`, config và master key.
Restore PostgreSQL bằng pg_restore --exit-on-error trên container không network/port: database Sonar có 185 bảng public; database n42 có 0 bảng public.
Đây là kiểm chứng archive/dump, chưa phải đăng nhập vào một Jenkins phục hồi hoàn chỉnh hoặc reboot máy Windows.
Xem `restore-verification.json` trong thư mục backup. Không ghi đè volume chính để thử restore.

## Cấu hình job review khi có quyền quản trị

1. Tạo project Sonar `n42-telecom-alert-ci-validation`; giữ project chính `n42-telecom-alert`.
2. Tạo job Pipeline from SCM `N42-CI-N42-10-Review`, branch `*/feature/N42-10-ci-pipeline`, Script Path `Jenkinsfile`.
3. Dùng Sonar server `SonarQube-N42`, scanner `SonarScanner` và credential hiện có qua Jenkins Credentials; không dán token vào SCM/log.
4. Build lần đầu để đăng ký parameter, sau đó Build with Parameters: `SONAR_REVIEW=true`. Đối chiếu checkout SHA với revision đã push.
5. Cấu hình webhook Sonar -> `http://jenkins:8080/sonarqube-webhook/`, kiểm Last Delivery và task ID.
6. Gate OK phải SUCCESS. Trên project thử riêng gắn Gate có điều kiện cố ý không đạt để thu FAILURE; trả lại cấu hình thử sau bài kiểm tra.
7. Timeout cần tác vụ thật chưa có kết quả trước deadline; không lấy sleep/error giả làm bằng chứng waitForQualityGate. Ghi riêng cách trì hoãn xử lý trong lab, đảm bảo không ảnh hưởng project chính.
8. Hủy thủ công phải ABORTED; timeout chờ Gate là FAILURE/TIMEOUT artifact. Chưa có runtime evidence thì không đánh dấu PASS.

Job chính `N42-CI-Pipeline` giữ `*/main`, Sonar/Gate theo main; feature thông thường bỏ qua Sonar nếu không bật SONAR_REVIEW.
Required check GitHub phải do tài khoản có quyền repo thiết lập; quyền quản trị Docker không cấp quyền quản trị GitHub.

## Phiên quản trị được cho phép

Người dùng cho phép token Jenkins tạm và sử dụng credential Sonar chỉ trong bộ nhớ, không xuất Sonar token ra file/log; thu hồi token quản trị tạm khi xong.
Đã tạo N42-CI-N42-10-Review và project n42-telecom-alert-ci-validation. Global Analysis Token hiện có chạy analysis được nhưng API quản trị Quality Gate/webhook trả 403. User Token tạm có quyền phù hợp đã được dùng để kiểm chứng Gate ERROR/FAILURE và khôi phục OK/SUCCESS trên project validation, sau đó thu hồi và gỡ credential tạm; giữ token pipeline cũ.
Jenkinsfile có SONAR_REVIEW_TIMEOUT_SECONDS 10..600 giây cho review; main luôn 600. Không hạ timeout main để thử lỗi.

Jenkins sandbox chỉ phê duyệt chữ ký `method org.jenkinsci.plugins.workflow.steps.FlowInterruptedException isActualInterruption` để phân biệt hủy thủ công/timeout. Đây là getter boolean; không tắt sandbox hoặc approve script rộng. Review #1 phát hiện thiếu approval, không tính PASS; sau approval, review #2 ghi TIMEOUT/FAILURE đúng yêu cầu trên task thật đang xử lý.
