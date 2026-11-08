# Checklist nghiệm thu và bàn giao N4.2

**Mốc:** W16–W18 · **Điều phối:** Phạm Minh Nhựt · **Chốt bằng chứng:** Ngô Châu Kiệt

| # | Hạng mục bàn giao | Điều kiện hoàn tất | Owner | Bằng chứng/đường dẫn |
|---:|---|---|---|---|
| 1 | Mã nguồn và phiên bản | Mã trên GitHub, tag release, lịch sử PR/review; không còn secret | TL + toàn nhóm | Link repo/tag, secret scan |
| 2 | Hướng dẫn cài đặt | Máy sạch dựng được trong ≤1 giờ theo tài liệu | QA | Video + checklist |
| 3 | Tài liệu kiến trúc, yêu cầu và kiểm thử | Charter, SADD, SRS, TDD, AC, Test Plan, Test Case Specification và RTM cùng baseline; Word/PDF/ZIP khớp nguồn | TL + BE2 + QA | `docs/` + manifest phân phối |
| 4 | Lược đồ sự kiện và API | Schema có version; OpenAPI khớp build bàn giao; ví dụ request/response | BE2 + BE1 | OpenAPI/schema + examples |
| 5 | Bộ dữ liệu và kịch bản | Fixture giả lập có nhãn; KB-01..08 chạy lại được; có expected result | QA + BE3 | Generator, fixtures, test report |
| 6 | Báo cáo kiểm thử | Kết quả chức năng, benchmark W13 một giờ, sent/received, latency và tài nguyên | QA | Báo cáo + dữ liệu gốc |
| 7 | Hướng dẫn vận hành | Health check, port, cấu hình môi trường, reset lab, xử lý lỗi thường gặp | BE1 + BE2 | Runbook |
| 8 | Hồ sơ học kỳ doanh nghiệp | Weekly/Monthly, minutes, đánh giá chéo, đóng góp cá nhân và báo cáo tổng kết | TL | Hồ sơ chương trình |

## Cổng bàn giao

- **W16:** TL rà danh mục hạng mục, owner, đường dẫn và thiếu hụt.
- **W17:** demo trên bộ dữ liệu chuẩn; nhóm ghi lại lỗi, giới hạn đã biết và hướng dẫn chạy demo.
- **W18:** người nhận cài lại từ máy sạch, xác nhận phiên bản và ghi nhận hoàn tất; mọi mục chưa đạt có owner và ngày xử lý.
