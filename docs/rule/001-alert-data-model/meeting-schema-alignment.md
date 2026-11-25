# Đối chiếu đề xuất schema từ biên bản họp với repo ứng dụng

**Nguồn:** Trích biên bản do người dùng cung cấp trong chat, chưa có ngày họp, người quyết hoặc mã ticket kèm theo. **Đích áp dụng:** `C:/Projects/vnpt/telecom-alert-correlation-n42`. Đây là đầu vào thiết kế để leader/BE2/BE3 chốt migration, không phải xác nhận SQL đã đổi.

| Nội dung họp | Hiện trạng repo code/tài liệu | Đề xuất ghi vào contract trước implementation |
|---|---|---|
| Đổi `alert_event` thành tên rõ chức năng, ví dụ `event` | Code có model `app/models/alert_event.py` (class AlertEvent); tài liệu v0.9/DATA_AND_API_DESIGN đề xuất bảng `alert_events`; `docker/init-db.sql` chưa tạo bảng ứng dụng | Phân biệt **tên Python model/API** với **tên bảng vật lý**. Chọn tên bảng cụ thể `event` hoặc `events` trong migration được duyệt; không đổi class/route/FK hàng loạt trước mapping. Các spec 001–006 đang dùng tên logic `events`. |
| Đổi `incidents` thành `alert` | Tài liệu repo đề xuất `grouped_incidents`, chưa có bảng ứng dụng hoặc model incident thực chạy | Chọn tên bảng vật lý `alert` hoặc `alerts`; cập nhật FK, query, migration, OpenAPI/FE và tài liệu cùng một version. Spec 001–006 dùng tên logic `alerts`, ID alert là ID sự cố. |
| Bổ sung `target_ip` | `AlertEvent` hiện không có `target_ip`; tài liệu DATA_AND_API_DESIGN mới ghi IP tổng quát, chưa có DDL | Đề xuất field `target_ip` kiểu IP (PostgreSQL INET nếu thành cột), nullable vì không phải mọi syslog có IP đích. Dữ liệu có thể do parser rút từ body có căn cứ; không lấy mặc định từ source_ip/sender_ip. Với loại event cần IP đích, rule/schema đánh dấu thiếu bằng diagnostic. |
| Từ NOT NULL đơn thuần sang đánh giá đầy đủ/thiếu | Model `AlertEvent` dùng nhiều field bắt buộc; fallback đang điền `event_timestamp=received_at`, hostname=source_ip, facility/severity giả định | Chia **bắt buộc để lưu** (ID/nguồn/raw/received_at/status/scope theo schema mới) và **bắt buộc để đánh giá từng event_type/rule**. Field chưa biết là NULL/vắng mặt kèm `parse_status` success/partial/failed và mã lý do; không bịa field hợp lệ để vượt validation. `target_ip` chỉ bắt buộc cho loại/rule thực sự cần nó. |

## Ma trận đầy đủ đề xuất

| Lớp | Field/điều kiện | Khi thiếu |
|---|---|---|
| Tiếp nhận bền vững | ID ổn định, raw text/bytes, received_at, ingest_source, scope | Không báo accepted nếu chưa commit; UDP có metric/drop, không ACK |
| Chuẩn hóa chung | event_type, event_time/time_status, device_id, metadata parser, attributes | Lưu raw và partial/failed/diagnostic, không loại bỏ log |
| LinkFlap | device_id + interface_name + interface_state UP/DOWN + interface_layer physical + event_time tin cậy | Không gọi LinkFlap cho nhóm giả; lưu reason và guard timer nếu có thể ảnh hưởng |
| Rule cần IP đích trong tương lai | target_ip là IP hợp lệ và có căn cứ | Rule đó INVALID_FOR_RULE/MISSING_TARGET_IP; rule khác vẫn có thể xét |

## Quy tắc đánh dấu

- Trạng thái parse mô tả **mức độ chuẩn hóa**, không dùng NOT NULL toàn hàng để biến log thiếu thông tin thành lỗi mất dữ liệu.
- Kết quả theo **event–rule** phân biệt APPLY, NOT_APPLICABLE, INVALID_FOR_RULE, DEFER; diagnostic mã lý do có thể gồm MISSING_TARGET_IP. Một event processed vẫn có thể mang guard chưa release, theo [006](../006-correlation-input-contract/contracts/input-disposition.md).
- Lưu căn cứ parser/schema version và raw bất biến; UI/QA phân biệt “đã lưu nhưng thiếu dữ liệu” với “đã xét đủ và không thỏa rule”.
- Mốc thời gian chưa biết không thay bằng received_at để rule thời gian xét như giờ nguồn. Phải có chính sách migration/adapter cho `AlertEvent.event_timestamp` hiện luôn bắt buộc.

## Cần xác nhận trong cuộc review

1. **Tên vật lý cuối cùng** là singular `event`/`alert` hay plural `events`/`alerts`; trích biên bản dùng “ví dụ”, nên chưa tự khẳng định tên exact đã chốt.
2. `target_ip` là cột chung INET hay field trong `attributes` theo loại event; nếu cần lọc thường xuyên, ưu tiên cột có kiểu và index sau đo. Dù chọn cách nào, chỉ một nguồn chuẩn.
3. Owner/mã ticket, ngày/người quyết, migration/backfill và khả năng tương thích API/FE; repo `AGENTS.md` yêu cầu contract, test case và RTM trước code đổi schema.

**Không sửa repo ứng dụng ở bước lập kế hoạch.** Thay đổi tên bảng/model và chính sách NOT NULL tác động BE2/BE3/FE; cần chốt contract với TL trước migration hoặc handler implementation.
