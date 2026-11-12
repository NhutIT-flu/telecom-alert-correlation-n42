# N42-10 — cổng merge và bàn giao

Ngày rà soát: 12/11/2026. Nhánh: `feature/N42-10-ci-pipeline`.
Đây là hồ sơ chuẩn bị triển khai; các ô chưa đánh dấu cần evidence chạy thật. Chính sách Flake8/Black được xử lý sau cùng, trước vòng kiểm chứng cuối và đề nghị merge.

## Hiện trạng GitHub đã đọc

- API `branches/main`: `protected=true`, nhưng phần `required_status_checks` trả `enforcement_level=off`, `contexts=[]`, `checks=[]`.
- API `rulesets?includes_parents=true`: danh sách trống.
- API chi tiết `branches/main/protection`: 403 `Resource not accessible by integration`. Kết nối hiện tại không đủ quyền Administration để xác minh yêu cầu review, bypass hoặc sửa protection.
- Vì vậy chưa có bằng chứng check CI đang bắt buộc; không kết luận rằng main hoàn toàn không được bảo vệ. Cần chủ repo kiểm tra rule hiện có trong Settings → Branches trước khi bổ sung.

## Cấu hình cổng merge đề nghị

Chủ repo áp dụng vào rule hiện có cho `main`, tránh tạo nhiều cơ chế trùng nhau. Cấu hình dưới đây cần đối chiếu quyền và policy nhóm, chưa được áp dụng từ phiên làm việc này.

| Mục | Giá trị đề nghị | Lý do |
|---|---|---|
| Require a pull request before merging | Bật | Làm việc qua PR |
| Require approvals | Ít nhất 1, TL review PR N42-10 của QA | Không tự duyệt PR của mình |
| Dismiss stale pull request approvals when new commits are pushed | Bật | Approval phải theo thay đổi mới |
| Require status checks to pass before merging | Bật | CI lỗi phải chặn merge |
| Required check | `Code Quality & Automated Tests`, nguồn GitHub Actions | Tổng hợp cả quality/security/tests/smoke |
| Require branches to be up to date before merging | Bật | Kiểm tra cùng main mới nhất |
| Require conversation resolution before merging | Bật | Giải quyết feedback review |
| Do not allow bypassing the above settings | Bật nếu phù hợp quyền quản trị nhóm | Không dùng admin bypass để làm evidence PASS |
| Allow force pushes / Allow deletions | Tắt | Giữ main ổn định |

Chạy workflow mới trên PR trước khi chọn check để tên check được GitHub ghi nhận. Không xóa required checks đang phục vụ nhóm mà chưa đối chiếu. Không chọn Jenkins localhost làm required check: job chính chỉ chạy sau khi main thay đổi và hiện chưa phát status PR. Không bật merge queue trong phạm vi này; nếu dùng sau này cần workflow hỗ trợ `merge_group`.

## Kiểm chứng cổng merge trên GitHub

Các thử nghiệm lỗi thực hiện trên PR thử nghiệm riêng, không merge fixture lỗi vào main. Dữ liệu scanner phải là giả lập và xóa trước khi kết thúc. Khi thao tác bằng tài khoản có quyền bypass, quan sát trạng thái bị chặn của rule, không dùng bypass để thử merge.

| Case | Thao tác | Expected và evidence cần lưu |
|---|---|---|
| MG-01 | PR sạch chưa có approval | Checks có thể xanh nhưng merge chờ reviewer |
| MG-02 | Thêm test thất bại trên nhánh thử | Job tests và check tổng hợp đỏ; merge bị chặn |
| MG-03 | Bỏ fixture lỗi và push commit sửa | Check chạy lại đúng revision; không dùng kết quả commit cũ |
| MG-04 | Có approval rồi push thay đổi mới | Approval cũ bị dismiss; cần review lại |
| MG-05 | Main thay đổi sau lần CI xanh | GitHub yêu cầu cập nhật branch/chạy lại theo rule |
| MG-06 | Đủ checks, review và resolve feedback | Đủ điều kiện merge theo rule; không cần merge PR thử |

Local đã kiểm tra gate từ chối failure/skipped/cancelled/missing. Điều đó không thay thế MG-01–06 trên GitHub hoặc xác minh workflow runtime. Giữ ảnh cấu hình rule, URL PR/run, head SHA và merge-ref SHA; không đưa token hoặc nội dung credential vào ảnh.

## Thứ tự triển khai và nghiệm thu

1. Hoàn tất review diff local, sau đó xử lý Flake8/Black theo phần riêng đã thống nhất.
2. Chạy lại kiểm tra cuối trên đúng diff, commit trên feature theo khuôn `chore: hoan thien pipeline va ho so CI (N42-10)`; push feature khi sẵn sàng. Không push trực tiếp main.
3. Thu run PR mới: đủ bốn job, check tổng hợp, JUnit/coverage/smoke và metadata. Đối chiếu checkout SHA với run; PR có thể kiểm tra merge ref.
4. Chủ repo cấu hình rule và thực hiện MG-01–06. TL Phạm Minh Nhựt review; squash merge sau khi đủ điều kiện.
5. Áp dụng image Python 3.12 cho Jenkins theo [runbook](JENKINS_SONAR_RUNBOOK.md). Build Now một lần trên job `*/main` để đăng ký polling; lần cập nhật main tiếp theo được build tự động. Giữ volume hiện có.
6. Kiểm checkout main đúng SHA, Python 3.12, Sonar task/revision, Last Delivery 2xx, Quality Gate OK. Kiểm non-OK/timeout trên project thử nghiệm riêng. Thu log polling/build cause cho lần tự chạy, không lấy lần Build Now làm bằng chứng tự động.
7. Cập nhật execution record và PR; demo 5 phút; chỉ xác nhận Done sau khi đủ DoD.

## Phiếu evidence theo revision

| Hạng mục | Nội dung phải ghi | Trạng thái trước push |
|---|---|---|
| Revision | Commit SHA, diff đã commit, ngày chạy, người chạy | Diff local, chưa có SHA cuối |
| Local Windows | Python/packages, unittest, pytest, scan, health | Đã kiểm bản local; xem reports |
| Linux image thử | Image ID, Python 3.12, cài sạch, pytest, health | Đã kiểm image review, chưa thay service |
| GitHub Actions | Run URL, attempt, checkout/merge SHA, từng job, artifact | Chưa chạy workflow mới |
| Merge gate | Rule, nguồn check, reviewer, MG-01–06 | Chưa xác minh enforcement |
| Jenkins | Build URL/number, branch/SHA, Python, poll log, artifacts | Chưa chạy pipeline mới trên service |
| SonarQube | Task ID, revision, Gate, webhook delivery | Webhook đã tạo; chưa xác minh delivery mới |
| Bàn giao | TL approval, merge SHA, Docker/demo | Chờ thực hiện |

Log local trong `reports/` bị Git ignore theo thiết kế. Đính kèm log/ảnh đã rà soát vào PR hoặc kho evidence được nhóm cho phép; link local không phải bằng chứng truy cập được cho reviewer. Sau thay đổi Flake8/Black phải thu evidence mới cho revision cuối, không tái sử dụng ảnh cũ như kết quả mới.

## Tham chiếu

- [GitHub branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule).
- [Required status checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks).
- [GitHub Actions của dự án](GITHUB_ACTIONS_GUIDE.md).
- [Runbook Jenkins/Sonar](JENKINS_SONAR_RUNBOOK.md).
