---
name: review-pr
description: Review pull request hoặc diff theo tiêu chuẩn nghiệm thu của dự án N4.2 (schema AlertEvent, test parser/luật, bảo mật dữ liệu giả lập, mốc W4–W13). Hãy dùng skill này khi người dùng nhờ review PR, xem giúp thay đổi, kiểm tra trước khi merge, hoặc dán diff.
---

# Review PR theo chuẩn nhóm

Chỉ đọc và nhận xét, không tự sửa trừ khi được yêu cầu. Lấy diff bằng `git diff main...HEAD` hoặc theo PR được đưa.

## Checklist
1. **Phạm vi**: PR làm đúng một thẻ `N42-x`? Commit/nhánh đúng khuôn (xem `git-workflow`)?
2. **Số reviewer**: parser, luật tương quan, code `receiver/` cần 2 reviewer.
3. **Schema**: có đụng `AlertEvent` hoặc DDL? Nếu có phải có TL duyệt, DDL + `docs/INTERFACES.md` cập nhật cùng PR (xem `change-alertevent-schema`).
4. **Test**: parser có ≥200 sự kiện mẫu? Luật có test dòng thời gian tái lập được? Test thật sự fail khi code sai?
5. **Đúng đắn và lỗi**: trường hợp biên, exception không làm sập luồng, log lỗi đi vào quarantine; chặn event loop (I/O đồng bộ trong `async`).
6. **Hiệu năng**: ghi DB theo lô; không đọc cả file lớn vào RAM; regex chống ReDoS.
7. **Bảo mật dữ liệu**: không credential/API key; IP mẫu chỉ 10.x, 192.168.x, 203.0.113.x; không kết nối thiết bị thật.
8. **Luật không hardcode**: threshold/window/scope đọc từ cấu hình.
9. **Hợp đồng FE**: không thêm endpoint ngoài OpenAPI; mock FE khớp 100% `AlertEvent`.
10. **Docs và Docker**: docs cập nhật; chạy được bằng `docker compose up -d`.

## Báo cáo
```
Tóm tắt: (1–2 câu) · Đề xuất: Duyệt / Sửa rồi duyệt / Chưa duyệt
Nghiêm trọng (phải sửa): file:dòng — vấn đề — gợi ý
Nên sửa:
Gợi ý nhỏ:
Rủi ro cho mốc: (W4/W6/W8/W12/W13 nếu có)
Điểm tốt:
```
Nếu không thấy vấn đề, nói rõ đã kiểm tra những mục nào, không bịa lỗi.
