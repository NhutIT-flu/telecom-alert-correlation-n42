# Research: Dữ liệu sự kiện và cảnh báo

## R1. Mô hình đa hãng
- **Decision**: Một bảng events chung, cột có kiểu cho metadata thường dùng, attributes JSONB cho field nghiệp vụ chuẩn và vendor_fields JSONB cho phần riêng hãng.
- **Rationale**: Rule/tìm kiếm có ngữ nghĩa chung trong khi parser hãng có thể mở rộng.
- **Alternatives considered**: Bảng theo hãng, JSONB cho toàn bộ, EAV; tăng schema/join hoặc mất kiểm soát kiểu và truy vấn chung.
- **Source**: [data-model.md](data-model.md) mục 1–4.

## R2. Bảo toàn raw và tiến độ
- **Decision**: Commit raw trước parse; một event ID xuyên suốt; parse/correlation status phân biệt pending, success/partial/failed và pending/processed/failed/skipped.
- **Rationale**: Lỗi parser/worker không làm mất đầu vào hoặc giả xử lý hoàn tất.
- **Alternatives considered**: Chỉ lưu parsed hoặc chỉ raw; không đủ bằng chứng hoặc không đủ field tìm kiếm.
- **Source**: 001 mục 4/9 và 006 contract.

## R3. Bảng/khóa/retention
- **Decision**: 8 bảng chung, UUID managed/alert, BIGINT event, FK RESTRICT; lab không tự xóa; replay scope riêng.
- **Rationale**: Bằng chứng, checkpoint, history và health tồn tại độc lập, có thể khôi phục.
- **Alternatives considered**: Xóa dây chuyền, lưu history chung alerts, bảng sự cố riêng; không phù hợp phạm vi/khả năng audit hiện tại.
- **Limit**: Chống trùng giữa ID nhận khác nhau chưa chốt; không UNIQUE raw/hash. Index interface/text và partition cần số đo/thiết kế retention riêng.

## R4. Hiệu năng và rủi ro
- **Decision**: Index tối thiểu theo truy vấn thường gặp, đo 100k events/40 query và chi phí JSONB/WAL; không GIN mọi JSONB.
- **Rationale**: Cân bằng chi phí ghi/đọc của syslog.
- **Alternatives considered**: Index mọi field hoặc partition từ đầu; tăng ghi/migration mà chưa có tải thật.
- **Gate**: 95/100 trang đầu ≤2 giây là mục tiêu lab, không phải benchmark đã chạy.
