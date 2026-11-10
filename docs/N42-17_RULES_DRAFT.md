# N42-17 — Bản nháp cấu hình luật v0.1.0

Phần có thể review độc lập với database gồm `app/services/rules.yaml`, `RuleConfiguration` và hàm `load_rule_configuration(Path(...))`. Hàm nạp một tệp UTF-8 bằng YAML 1.2, rồi kiểm tra cấu trúc với Pydantic. Bản nháp lấy `threshold`, `match` và `action` theo ví dụ trong [N42-17](https://nhutp2945-1793259952237.atlassian.net/browse/N42-17). `version` định danh bộ luật để đối chiếu khi review, còn `enabled` mặc định là `false`. Hai chế độ đếm đề xuất là `distinct` (đếm giá trị khác nhau) và `state_changes` (đếm sự kiện chuyển trạng thái theo trường đã chỉ định). Nếu không có `count`, đề xuất đếm các sự kiện thỏa `match`.

| Luật mẫu | Hành vi dự kiến khi tích hợp | Điều kiện cần chốt |
|---|---|---|
| Link Flap | Năm sự kiện chuyển trạng thái trong 60 giây trên cùng thiết bị và interface. Bốn sự kiện, cảnh báo lặp cùng trạng thái hoặc hai interface riêng không đủ ngưỡng. | Đối chiếu `interface`/`link_state` với schema parser. Ví dụ N42-17 dùng `CRITICAL`, còn TC-COR-001 ghi `MAJOR`. Xem KB-01 và N42-44. |
| Dual Power Supply Failure | Hai slot nguồn khác nhau trên cùng thiết bị. Hai bản tin từ cùng slot vẫn chỉ tính một slot. Cửa sổ 60 giây là giá trị minh họa. | Field `psu_slot`, taxonomy Huawei và cửa sổ. KB-02 hiện chỉ có fixture một nguồn hỏng; incident single-hit cần duyệt riêng. QA cần fixture hai slot cho N42-45. |
| BGP Flapping | Nhóm theo thiết bị và peer, đếm chuyển trạng thái phiên. Ngưỡng 3, cửa sổ 120 giây và mnemonic là ví dụ cấu hình. | Field peer/state, nguồn parser, ngưỡng, cửa sổ và severity. KB-05/N42-65 đặc tả BGP Neighbor Down theo retry nên cần xác nhận phạm vi riêng trước khi dùng làm tiêu chí cho BGP Flapping. |

## Readiness và evidence

- Đối chiếu [TCS mục 6.4](TEST_CASE_SPECIFICATION.md#64-cấu-hình-luật--be3-tc-rul) và [RTM](REQUIREMENTS_TRACEABILITY_MATRIX.md) theo FR-15/AC-05. Unit test bản nháp kiểm tra TC-RUL-001–005 ở mức nạp tệp và validation, gồm YAML lỗi, giá trị biên `0`/`1`, kiểu dữ liệu sai, khóa YAML và mã luật trùng.
- Evidence cục bộ có thể xuất bằng `python -m pytest tests/test_rules_config.py --junitxml=scratch/n42-17-junit.xml`. Khi bàn giao ghi kèm commit SHA, phiên bản YAML, Python/dependencies và lệnh chạy. QA Lead cần xác nhận cấu hình với KB-02 theo DoD của N42-17. Fixture KB-02 có một slot hỏng; cần fixture riêng hai slot để nghiệm thu luật nguồn kép.
- Trước khi bật luật, BE2/BE3 xác nhận field và taxonomy theo N42-15/N42-62, QA xác nhận expected result và liên kết case với RTM, TL ghi nhận quyết định. Engine, hot reload và lưu trữ đi theo ticket triển khai tương ứng.
