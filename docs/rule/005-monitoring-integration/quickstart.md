# Quickstart: Kiểm chứng 005-monitoring-integration

Guide này phân biệt kiểm tra tài liệu chạy được **ngay** với kiểm thử ứng dụng **sau khi triển khai**. Repository ứng dụng đã xác minh ở C:/Projects/vnpt/telecom-alert-correlation-n42; pytest hiện có nhưng chưa có worker/lifecycle/DB end-to-end theo đặc tả. Không coi tình huống dự kiến là test đã chạy.

## 1. Kiểm tra tài liệu từ C:\Projects\vnpt

```powershell
$feature = 'specs/005-monitoring-integration'
Get-ChildItem $feature -Recurse -File | Select-Object -ExpandProperty FullName
Select-String -Path "$feature/spec.md" -Pattern '\*\*FR-\d{3}\*\*','\*\*SC-\d{3}\*\*'
Get-Content "$feature/plan.md" -TotalCount 20
```

Kỳ vọng thấy spec/plan/research/data-model/quickstart, thiết kế [integration-design.md](integration-design.md) và [contract](contracts/integration.md). Kiểm tra này chỉ xác nhận artifact, không chứng minh runtime.

## 2. Điều kiện trước kiểm thử ứng dụng

- Leader duyệt phạm vi prototype và các quyết định/rủi ro trong plan; ticket N42 có mã thực trước code/commit.
- Dùng repo ứng dụng C:/Projects/vnpt/telecom-alert-correlation-n42 (Python 3.12, pytest, Docker Compose lab); xác nhận fixture, DB, ticket và quyền truy cập trước test.
- Không dùng credential/log production. Ghi rõ môi trường, phiên bản, số lượng event và tải khi đo.
- Chạy test contract/integration theo I01–I15 ở [thiết kế nguồn](integration-design.md); lệnh thực tế được điền ở tasks sau khi xác minh repo.

## 3. Kịch bản cần chạy sau triển khai

1. UDP/API/file accepted chỉ sau raw commit.
2. file nhập dở giữ batch đã commit.
3. Cisco XRv canonical/diagnostic trong prototype. Kiểm chứng thêm hãng thứ hai khi có mẫu và adapter tương ứng.
4. viewer/operator/ingest/maintenance phân quyền.
5. API 409 version cũ.
6. UI stale/reconnect.
7. health stale/gap và receipt không mất.

## 4. Kết quả cần báo

Đối chiếu event/alert/state/bằng chứng theo ID và expected results ở I01–I15; ghi số ca pass/fail, latency từng chặng nếu liên quan, CPU/RAM/WAL/backlog và lỗi. Mục tiêu thử lab không phải kết quả đo hoặc SLA. Nếu chưa có app/test command, ghi rõ chưa chạy; không thay bằng kiểm tra Markdown.

