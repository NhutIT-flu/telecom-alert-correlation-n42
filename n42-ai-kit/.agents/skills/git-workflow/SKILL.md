---
name: git-workflow
description: Đặt tên nhánh, viết commit message và chuẩn bị PR đúng khuôn của nhóm N4.2. Hãy dùng skill này mỗi khi người dùng chuẩn bị commit, tạo nhánh, mở pull request, hỏi "commit thế nào", hoặc nói thẻ N42-x đã làm xong, kể cả khi họ không nhắc đến Git.
---

# Quy trình Git của nhóm

## Nhánh
`feature/<mo-ta>-<ten>`, tạo từ `main`, mô tả không dấu, gạch nối. Ví dụ: `feature/tcp-syslog-receiver-an`. Không bao giờ push thẳng `main`.

## Commit
Khuôn: `<type>: mo ta khong dau (N42-x)`
- type ∈ `feat | fix | test | refactor | perf | docs | chore`
- mô tả không dấu, ngắn, ở thể mệnh lệnh, bắt buộc có mã thẻ `N42-x`.
- Ví dụ: `feat: them tcp syslog receiver (N42-14)` · `fix: sua parser bo qua hostname co khoang trang (N42-23)` · `test: them kich ban bung no canh bao (N42-28)`.

Nếu người dùng chưa nói mã thẻ, **hỏi mã thẻ** thay vì tự đặt.

## Trước khi mở PR
1. Chạy lint (`ruff`) và `pytest`; báo lệnh đã chạy và kết quả (chỉ dựa vào kết quả người dùng cho biết).
2. Thay đổi parser, luật tương quan hoặc `receiver/` → cần **2 reviewer**; còn lại ≥1.
3. Không tự merge PR của mình; merge kiểu squash; CI xanh mới merge.
4. Thẻ chỉ "Xong" khi: merge sau review + CI xanh + chạy được bằng Docker + docs cập nhật + demo được 5 phút.
5. WIP tối đa 2 thẻ/người: nếu người dùng đang mở thẻ thứ 3, nhắc hoàn thành một thẻ trước.

## Đầu ra
Đưa ra: tên nhánh, commit message, mô tả PR ngắn (làm gì, vì sao, cách test), danh sách reviewer cần thiết.

## Tránh
- Commit lẫn nhiều việc không liên quan; commit file `.env`, credential, dữ liệu thật.
- Dùng `git push --force` lên nhánh chung.
