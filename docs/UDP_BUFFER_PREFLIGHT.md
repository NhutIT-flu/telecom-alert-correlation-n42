# UDP socket buffer preflight (QA, N42-10 / TC-OPS-002)

## Phạm vi và tiêu chí trước triển khai

Theo yêu cầu người dùng: chỉ sửa tooling/CI của QA. Giữ nguyên receiver và test backend N42-13.
Code owner của receiver vẫn là BE1; QA kiểm chứng cấu hình và khả năng môi trường trước unittest/pytest/smoke.
Không biến socket buffer thành KPI mới hoặc tự đổi hành vi startup của sản phẩm.

| Case | Input / điều kiện | Expected |
|---|---|---|
| UB-01 | Checkout chưa có app/receiver/server.py | NOT_APPLICABLE, checked=false; không tuyên bố UDP PASS |
| UB-02 | Backend có mặt, default 4 MiB, OS đáp ứng | Đọc request từ instance; probe và receiver thật đạt; đóng receiver; READY |
| UB-03 | Default/constructor request 8 hoặc 16 MiB | Dùng cùng thuật toán, không sửa số trong script |
| UB-04 | Linux readback thấp hơn request đã nhân đôi | Thử chuẩn bị nếu được bật; đọc lại; vẫn thiếu thì exit 1 và report môi trường |
| UB-05 | Không có quyền hoặc sysctl không có tác dụng | Không hạ request/assertion, không skip test; report nguyên nhân và exit khác 0 |
| UB-06 | Backend có mặt nhưng import/constructor lỗi | ERROR, exit 2; không coi là chưa có backend |
| UB-07 | Request âm/0/không nguyên/vượt kiểu int socket | INVALID_REQUEST, exit 2 |
| UB-08 | Probe đủ nhưng receiver thật cấp thiếu / start lỗi | FAIL/ERROR, cleanup receiver; report không READY |
| UB-09 | Nền tảng chưa có quy tắc readback xác minh | UNVERIFIED_PLATFORM, exit 2 |
| UB-10 | Chuẩn bị thành công / thất bại / chạy lại | Kiểm lại socket thật; ghi OS limit trước/sau, SHA, source hash và trạng thái |

## Thiết kế

Mặc định đọc SyslogReceiverServer(host=127.0.0.1, port=0).so_rcvbuf trong chính checkout đang kiểm tra.
Nhánh chưa có receiver được ghi NOT_APPLICABLE; có receiver thì không bỏ qua lỗi import hoặc lỗi tài nguyên.
Request riêng chỉ phục vụ probe QA qua constructor hiện có, không cấu hình lại FastAPI trong sản phẩm.
Linux trả SO_RCVBUF đã nhân đôi cho bookkeeping: kiểm reported >= 2 * requested; Windows kiểm reported >= requested.
Đây là kiểm chứng yêu cầu socket được chấp nhận, không phải đo payload hữu dụng hoặc chứng minh không mất gói.

GitHub tests/smoke có thể gọi sudo -n cho duy nhất sysctl net.core.rmem_max; không sửa rmem_default hoặc cấu hình reboot.
Jenkins không tự dùng sudo hoặc privileged container. Nếu giới hạn nằm ở Docker host, fail rõ và yêu cầu đầu mối lab chuẩn bị agent.
Chỉ nâng, không hạ trần. Ngân sách tự chuẩn bị mặc định 64 MiB, thay được bằng --max-prepare-bytes do chủ lab chốt; vượt ngân sách là lỗi policy QA, không kết luận Linux không hỗ trợ.
Sau chuẩn bị vẫn phải đọc lại socket thật. Không coi exit code sysctl bằng 0 là đủ.

Nguồn: PROJECT_CHARTER.md mục 2, TEST_PLAN.md mục 6, TDD mục 7; https://man7.org/linux/man-pages/man7/socket.7.html.

## Cách chạy và đọc kết quả

```bash
# Chỉ đo, không sửa OS.
python tools/udp_buffer_preflight.py
# Runner dùng một lần, sudo không cần mật khẩu.
python tools/udp_buffer_preflight.py --prepare --allow-sudo
# Jenkins: chỉ thử với quyền agent hiện có.
python tools/udp_buffer_preflight.py --prepare
# Probe 8 MiB bằng constructor đã có, không đổi cấu hình sản phẩm.
python tools/udp_buffer_preflight.py --require-backend --requested-bytes 8388608
```

Report `reports/udp-buffer.json` ghi request/probe/receiver bytes, rmem_max trước/sau, platform, source hash, SHA và exit code.
READY (0) là đáp ứng; NOT_APPLICABLE (0, checked=false) là checkout chưa có backend; INSUFFICIENT_BUFFER (1) là môi trường chưa đáp ứng; ERROR/INVALID_REQUEST/UNVERIFIED_PLATFORM (2) là lỗi cần xử lý.
Source snapshot trong reports/ không lấy nhầm SHA của repo cha: ghi unknown, đối chiếu revision/hash qua manifest riêng.

Preflight dùng loopback/cổng động và đóng receiver sau kiểm tra. CI/smoke đặt N42_UDP_HOST=127.0.0.1, N42_UDP_PORT=0 để không tranh cổng 5514.
Preflight thất bại thì không chạy tiếp bộ test/smoke; report vẫn được upload/archive. Không dùng continue-on-error, không hạ assertion hoặc skip bài lỗi.
Nếu Jenkins không nâng được rmem_max, chủ lab chuẩn bị host/agent phù hợp rồi chạy lại. Không tự thêm privileged, mount Docker socket hoặc sửa persistent sysctl.
Không đưa buffer vào env giả nếu backend chưa đọc biến đó; nguồn chuẩn là constructor của checkout.
Nếu owner đổi default 4 thành 8 nhưng test backend vẫn assert bằng 4, owner cần cập nhật expected; preflight không che lỗi này.

## Phát hành

Thay đổi ở N42-10, không push vào nhánh BE1. Checkout QA chưa có receiver sẽ ghi NOT_APPLICABLE.
Kiểm chứng trên source snapshot N42-13 phải kèm backend revision/hash, không gán kết quả cho commit QA.
Sau merge QA PR, đồng bộ các nhánh feature và chạy lại để sử dụng workflow mới.
