# Quickstart: Kiểm chứng 003-rule-dispatch-correlation

Guide này phân biệt kiểm tra tài liệu chạy được **ngay** với kiểm thử ứng dụng **sau khi triển khai**. Repository ứng dụng đã xác minh ở C:/Projects/vnpt/telecom-alert-correlation-n42; pytest hiện có nhưng chưa có worker/lifecycle/DB end-to-end theo đặc tả. Không coi tình huống dự kiến là test đã chạy.

## 1. Kiểm tra tài liệu từ C:\Projects\vnpt

```powershell
$feature = 'specs/003-rule-dispatch-correlation'
Get-ChildItem $feature -Recurse -File | Select-Object -ExpandProperty FullName
Select-String -Path "$feature/spec.md" -Pattern '\*\*FR-\d{3}\*\*','\*\*SC-\d{3}\*\*'
Get-Content "$feature/plan.md" -TotalCount 20
```

Kỳ vọng thấy spec/plan/research/data-model/quickstart, thiết kế [engine-design.md](engine-design.md) và [contract](contracts/handler-worker.md). Kiểm tra này chỉ xác nhận artifact, không chứng minh runtime.

## 2. Điều kiện trước kiểm thử ứng dụng

- Leader duyệt phạm vi prototype và các quyết định/rủi ro trong plan; ticket N42 có mã thực trước code/commit.
- Dùng repo ứng dụng C:/Projects/vnpt/telecom-alert-correlation-n42 (Python 3.12, pytest, Docker Compose lab); xác nhận fixture, DB, ticket và quyền truy cập trước test.
- Không dùng credential/log production. Ghi rõ môi trường, phiên bản, số lượng event và tải khi đo.
- Chạy test contract/integration theo C01–C48 ở [thiết kế nguồn](engine-design.md); lệnh thực tế được điền ở tasks sau khi xác minh repo.

## 3. Kịch bản cần chạy sau triển khai

1. event→nhiều handler thử, mỗi revision một lượt.
2. restart trước/sau receipt/result commit.
3. lock mất.
4. failed barrier.
5. timer cùng timestamp event trước.
6. NEEDS_HISTORY đủ/thiếu.
7. guard từ 006 còn sau processed.
8. prune/evict/cold-load.
9. tải burst.

## 4. Kết quả cần báo

Đối chiếu event/alert/state/bằng chứng theo ID và expected results ở C01–C48; ghi số ca pass/fail, latency từng chặng nếu liên quan, CPU/RAM/WAL/backlog và lỗi. Mục tiêu thử lab không phải kết quả đo hoặc SLA. Nếu chưa có app/test command, ghi rõ chưa chạy; không thay bằng kiểm tra Markdown.

