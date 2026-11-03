# PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG — N4.2

**Mã:** VNPT-NET-UTH-N42-SADD · **Baseline:** 03/11/2026  
**Trạng thái:** Tài liệu phân tích/thiết kế cho dự án doanh nghiệp UTH × VNPT NET; các nội dung target cần được nhóm và đầu mối VNPT xác nhận trước khi đưa vào triển khai. Môi trường phát triển/kiểm chứng hiện tại là lab; phần mô tả nghiệp vụ định hướng hỗ trợ vận hành NOC không đại diện cho kết quả khảo sát nội bộ hoặc số liệu vận hành VNPT.

## 1. Mục tiêu và phạm vi

N4.2 là dự án doanh nghiệp phối hợp UTH × VNPT NET, xây dựng giải pháp thu thập và phân tích cảnh báo mạng nhằm hỗ trợ quy trình giám sát NOC. Phiên bản đang phát triển được kiểm chứng trong lab bằng dữ liệu giả lập; việc tích hợp production cần VNPT thẩm định và phê duyệt riêng. Phạm vi, giả định và quy tắc nghiệp vụ được đặc tả tại [SYSTEM_REQUIREMENTS_AND_USE_CASES.md](SYSTEM_REQUIREMENTS_AND_USE_CASES.md).

## 2. Tóm tắt bài toán và giải pháp

Log đa định dạng làm việc lọc, tra cứu và nhận biết cảnh báo liên đới khó hơn. N4.2 tạo một schema event chung, giữ bản tin thô, chạy quy tắc có thể tái lập, liên kết event với incident, rồi cung cấp API/dashboard để tra cứu. Mức giảm nhiễu và detection được tính theo tiêu chí nghiệm thu; không mặc định các event cùng từ khóa là cùng sự cố.

## 3. Bộ tài liệu phân tích–thiết kế

| Mảng | Tài liệu | Nội dung |
|---|---|---|
| Yêu cầu/nghiệp vụ | [SYSTEM_REQUIREMENTS_AND_USE_CASES.md](SYSTEM_REQUIREMENTS_AND_USE_CASES.md) | Scope, actor, FR/NFR, quy tắc, ca sử dụng, ngoại lệ |
| Kiến trúc | [ARCHITECTURE_DESIGN.md](ARCHITECTURE_DESIGN.md) | C4, thành phần, luồng, failure path, security, deployment, hiện trạng vs target |
| Dữ liệu/API | [DATA_AND_API_DESIGN.md](DATA_AND_API_DESIGN.md) | ERD, schema, hiện trạng mismatch, API thực tế và hợp đồng đề xuất |
| Kỹ thuật | [TECHNICAL_DESIGN_DOCUMENT.md](TECHNICAL_DESIGN_DOCUMENT.md) | Module, triển khai, hiệu năng và các cấu hình còn cần quyết định |
| Nghiệm thu | [ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md), [TEST_PLAN.md](TEST_PLAN.md) | Pass/fail, dữ liệu thử, phép đo |
| Truy vết | [REQUIREMENTS_TRACEABILITY_MATRIX.md](REQUIREMENTS_TRACEABILITY_MATRIX.md) | Requirement → module → acceptance → test/evidence |

## 4. Kết luận phân tích hiện trạng

Nhánh baseline W1 hiện chỉ có khung FastAPI và `GET /api/health`. UDP/TCP, ingest, parser, event store, correlation, dashboard và repository TimescaleDB là phần việc chưa triển khai theo Jira. SQL bootstrap chỉ bật extension, không tạo bảng nghiệp vụ hay nạp dữ liệu. Không ghi capability tương lai như thể đã triển khai.

## 5. Từ điển và ràng buộc

- `AlertEvent`: một bản tin đã chuẩn hóa; raw message được bảo toàn.
- `GroupedIncident`: nhóm event được rule kết luận liên quan, có references và evidence.
- `CorrelationRule`: cấu hình có version, điều kiện, ngưỡng và cửa sổ.
- Lab `10.10.0.0/16` là RFC1918 private; `203.0.113.0/24` chỉ dùng làm TEST-NET-3 trong tài liệu.
- Vai trò: Phạm Minh Nhựt (TL/PM), Nguyễn Duy Minh (BE3), Ngô Châu Kiệt (QA), Phạm Hoàng Long (BE1), Phạm Tấn Thành (BE2), Lê Khắc Huy (FE).

## 6. Câu hỏi thiết kế còn mở

1. File import: format/encoding/rotation, dung lượng tối đa, duplicate và archive.
2. TCP syslog có thuộc nghiệm thu W13 hay chỉ UDP/API/file.
3. Timestamp fallback, timezone không ghi trong log, late-arrival policy.
4. Cửa sổ event-time hay processing-time, rule overlap, merge/resolve incident.
5. DB retention/backup/restore và cấu hình benchmark.
6. Phạm vi dashboard/export; React app có repo riêng hay nằm trong repo này.
7. Authentication/TLS nếu demo qua mạng nhóm.

Mọi câu trả lời ảnh hưởng kiến trúc/AC cần được ghi trong `DECISIONS.md` trước khi xem là chốt.
