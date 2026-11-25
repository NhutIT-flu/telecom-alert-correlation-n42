# Quickstart: Kiểm chứng 001-alert-data-model

Guide này phân biệt kiểm tra tài liệu chạy được **ngay** với kiểm thử ứng dụng **sau khi triển khai**. Repository ứng dụng đã xác minh ở C:/Projects/vnpt/telecom-alert-correlation-n42; pytest hiện có nhưng chưa có worker/lifecycle/DB end-to-end theo đặc tả. Không coi tình huống dự kiến là test đã chạy.

## 1. Kiểm tra tài liệu từ C:\Projects\vnpt

```powershell
$feature = 'specs/001-alert-data-model'
Get-ChildItem $feature -Recurse -File | Select-Object -ExpandProperty FullName
Select-String -Path "$feature/spec.md" -Pattern '\*\*FR-\d{3}\*\*','\*\*SC-\d{3}\*\*'
Get-Content "$feature/plan.md" -TotalCount 20
```

Kỳ vọng thấy spec/plan/research/data-model/quickstart, thiết kế [data-model.md](data-model.md) và [contract](contracts/persistence.md). Kiểm tra này chỉ xác nhận artifact, không chứng minh runtime.

## 2. Điều kiện trước kiểm thử ứng dụng

- Leader duyệt phạm vi prototype và các quyết định/rủi ro trong plan; ticket N42 có mã thực trước code/commit.
- Dùng repo ứng dụng C:/Projects/vnpt/telecom-alert-correlation-n42 (Python 3.12, pytest, Docker Compose lab); xác nhận fixture, DB, ticket và quyền truy cập trước test.
- Không dùng credential/log production. Ghi rõ môi trường, phiên bản, số lượng event và tải khi đo.
- Chạy test contract/integration theo 001 SC-001–SC-011 ở [thiết kế nguồn](data-model.md); lệnh thực tế được điền ở tasks sau khi xác minh repo.

## 3. Kịch bản cần chạy sau triển khai

1. raw commit→parse lỗi/partial→đọc lại đúng bytes/text.
2. 100.000 event/40 query.
3. crash sau raw/before parse/giữa correlation.
4. replay search-only.
5. FK RESTRICT.
6. cùng ID retry không nhân alert, khác ID chưa suy trùng.

## 4. Kết quả cần báo

Đối chiếu event/alert/state/bằng chứng theo ID và expected results ở 001 SC-001–SC-011; ghi số ca pass/fail, latency từng chặng nếu liên quan, CPU/RAM/WAL/backlog và lỗi. Mục tiêu thử lab không phải kết quả đo hoặc SLA. Nếu chưa có app/test command, ghi rõ chưa chạy; không thay bằng kiểm tra Markdown.

