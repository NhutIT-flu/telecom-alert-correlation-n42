---
name: change-alertevent-schema
description: Quy trình thay đổi lược đồ AlertEvent, DDL TimescaleDB hoặc hợp đồng trong docs/INTERFACES.md của dự án N4.2. Hãy dùng skill này khi ai đó muốn thêm, đổi tên, xóa hoặc đổi kiểu một trường của AlertEvent, đổi cột trong alert_events, hoặc đổi tham số API /api/events, kể cả khi họ gọi đó là "chỉnh nhỏ".
---

# Thay đổi schema `AlertEvent`

Schema ảnh hưởng cả 6 người, nên thay đổi phải có kiểm soát.

1. **Nêu rõ thay đổi**: trường nào, vì sao, ai bị ảnh hưởng (BE1 `RawEvent`, BE2 parser/DDL, BE3 luật, FE mock/UI, QA bộ sinh/kịch bản).
2. **Xin TL duyệt** và ghi vào `docs/DECISIONS.md` (ID mới, trạng thái ĐỀ XUẤT → ĐÃ CHỐT). Chưa có duyệt thì không viết code thay đổi.
3. **Sau W4 (28/11)** lược đồ v1.0 đã đóng băng: ưu tiên thay đổi tương thích ngược (thêm trường tùy chọn có giá trị mặc định). Đổi tên, xóa hoặc đổi kiểu cần TL đồng ý riêng.
4. **Cập nhật cùng một PR**: model Pydantic, DDL (`docker/init-db.sql` + migration nếu có), `docs/INTERFACES.md`, OpenAPI.
5. **Cập nhật phía dùng**: fixtures parser, mock/MSW của FE, bộ sinh dữ liệu của QA, luật của BE3 nếu dùng trường đó.
6. **Test**: parser vẫn pass bộ ≥200 mẫu; truy vấn mẫu chạy được; FE mock khớp 100%.
7. **Thông báo cả nhóm** khi merge. PR cần 2 reviewer nếu đụng parser.

Thang severity là 0–7 (D-01); đừng thêm thang thứ hai vào schema.
