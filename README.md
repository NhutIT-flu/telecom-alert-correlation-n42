# N4.2 — Khung khởi đầu dự án UTH × VNPT NET

Repo này là baseline W1 để nhóm bắt đầu triển khai theo Jira. Prototype xử lý log trước đây đã được bỏ khỏi nhánh này để tránh hiểu nhầm phần nào đã xong. Lịch sử Git trên `main` vẫn giữ nguyên prototype.

## Trạng thái code

Hiện có khung FastAPI tối thiểu với `GET /api/health`. Receiver, parser, event model, store, correlation engine, dashboard và kết nối TimescaleDB **chưa được triển khai trên nhánh này**. Các tài liệu trong `docs/` mô tả yêu cầu/thiết kế đích; không đồng nghĩa các chức năng đã có trong code.

Database chỉ được khởi tạo extension TimescaleDB; chưa có bảng nghiệp vụ hoặc dữ liệu seed. Dữ liệu thử của dự án phải là giả lập 100%. Bộ sinh dữ liệu và kịch bản kiểm thử sẽ do thành viên QA Lead triển khai theo các ticket tương ứng.

## Chạy API khung

Yêu cầu Python 3.12+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- Health: `GET http://127.0.0.1:8000/api/health`
- OpenAPI: `http://127.0.0.1:8000/docs`
- Chạy test: `python -m unittest discover -s tests -p "test_*.py"`

Chỉ health endpoint hoạt động lúc này. Không gửi log thật hoặc kết nối thiết bị production.

## Bắt đầu theo Jira

- Tạo nhánh `feature/<mo-ta>-<ten>` từ nhánh được nhóm thống nhất; không push thẳng `main`.
- Mỗi ticket cập nhật đúng module, test và tài liệu liên quan; dùng `n42-ai-kit/docs/INTERFACES.md` làm **đề xuất cần chốt** khi ticket đụng schema/API.
- Giới hạn WIP: tối đa hai thẻ mỗi người ở `In Progress`; muốn nhận thẻ thứ ba phải hoàn thành hoặc trả lại một thẻ.
- Kết thúc ticket khi PR được review, CI xanh, hướng dẫn chạy phù hợp và bằng chứng được ghi trong Jira.

## Tài liệu

- [Quy chuẩn đóng góp mã nguồn (Contribution Guidelines)](CONTRIBUTING.md).
- [Điều lệ dự án](docs/PROJECT_CHARTER.md), [quyết định](docs/DECISIONS.md), [kiểm soát tài liệu](docs/DOCUMENT_CONTROL.md).
- [Yêu cầu và ca sử dụng](docs/SYSTEM_REQUIREMENTS_AND_USE_CASES.md), [kiến trúc](docs/ARCHITECTURE_DESIGN.md), [thiết kế dữ liệu/API](docs/DATA_AND_API_DESIGN.md), [thiết kế kỹ thuật](docs/TECHNICAL_DESIGN_DOCUMENT.md).
- [Tiêu chí nghiệm thu](docs/ACCEPTANCE_CRITERIA.md), [kế hoạch kiểm thử](docs/TEST_PLAN.md), [ma trận truy vết](docs/REQUIREMENTS_TRACEABILITY_MATRIX.md).
- [AI Kit và vai trò](n42-ai-kit/README.md).

## Nhóm

| Vai trò | Thành viên | MSSV |
|---|---|---|
| Team Leader / PM | Phạm Minh Nhựt | 082205017237 |
| BE1 | Phạm Hoàng Long | 0822065010353 |
| BE2 | Phạm Tấn Thành | 082205009270 |
| BE3 | Nguyễn Duy Minh | 083205002424 |
| FE | Lê Khắc Huy | 082205014597 |
| QA | Ngô Châu Kiệt | 083205002376 |
