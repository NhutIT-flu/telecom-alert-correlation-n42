# AGENTS.md — Đề tài N4.2 (HKDN UTH × VNPT NET)

Trả lời bằng TIẾNG VIỆT, ngắn gọn, đi thẳng vào việc. Code Python 3.12+ (type hints đầy đủ, async) và React (Vite).

## Chủ nhiệm và nhóm`n- TL/PM nội bộ: Phạm Minh Nhựt; BE1: Phạm Hoàng Long; BE2: Phạm Tấn Thành; BE3: Nguyễn Duy Minh; FE: Lê Khắc Huy; QA: Ngô Châu Kiệt.`n- Nguồn chuẩn vai trò và nghiệm thu: `../../docs/DOCUMENT_CONTROL.md`, `../../docs/PROJECT_CHARTER.md`, `../../docs/ACCEPTANCE_CRITERIA.md`.`n`n## Dự án
Hệ thống lab thu thập và phân tích cảnh báo từ router/switch/firewall: 3 nguồn (syslog UDP/TCP, file, API) → chuẩn hóa thành `AlertEvent` → TimescaleDB → tìm kiếm/thống kê → gom nhóm + ≥5 luật tương quan → dashboard React + xuất CSV/PDF. Tải nghiệm thu: 1.000 sự kiện/giây × 1 giờ.
- 18 tuần, 01/11/2026–06/03/2027. Đóng băng tính năng **30/01/2027 (W13)**; W14–15 nghỉ Tết; W16–18 hồ sơ, demo, nghiệm thu.
- Stack chốt: Python 3.12+ (FastAPI, asyncio, Pydantic v2, asyncpg), TimescaleDB, React (Vite, Tailwind), Docker Compose, GitHub Actions. UDP syslog: cổng 5514.
- Luồng: BE1 thu thập → BE2 chuẩn hóa + lưu → BE3 tương quan → FE hiển thị. Hợp đồng dữ liệu và giao diện: `docs/INTERFACES.md`.

## Mốc sống còn
W4 (28/11) lược đồ v1.0 + bộ sinh 3 nguồn · W6 (12/12) pipeline đầu-cuối · W8 (26/12) API truy vấn ổn định + prototype dashboard · W9 đánh giá giữa kỳ · W12 (23/01) checkpoint luật tương quan ≥70% · W13 (30/01) nghiệm thu ≥90% trên 8–10 kịch bản và tải 1.000 msg/s × 1 giờ, sau đó đóng băng. W14–15 nghỉ Tết; W16–18 bàn giao/demo.

<!-- chat-omit-start -->
## Vai trò
Người dùng sẽ nói mình là TL, BE1, BE2, BE3, FE hoặc QA (chưa nói thì hỏi một câu). Đọc `docs/roles/<VAI>.md` tương ứng và bám đúng phạm vi vai đó.
<!-- chat-omit-end -->

## Quy định nhóm (nhắc khi người dùng sắp vi phạm)
- **Git**: không push thẳng `main`; nhánh `feature/<mo-ta>-<ten>` từ main; commit `<type>: mo ta khong dau (N42-x)` với type ∈ feat|fix|test|refactor|perf|docs|chore; squash merge; không tự merge PR của mình.
- **Review**: PR ≥1 reviewer; **2 reviewer** cho parser, luật tương quan và code thu thập mạng lõi (`receiver/`). CI xanh mới merge.
- **WIP (D.2)**: mỗi người giữ tối đa hai thẻ ở cột Đang làm (In Progress); muốn nhận việc thứ ba phải hoàn thành hoặc trả lại một thẻ. Thẻ "Xong" khi: merge sau review + CI xanh + chạy được bằng Docker + docs cập nhật + demo được (5 phút).
- **Daily Report** trước 18:00 mỗi ngày làm việc (mẫu: `docs/templates/daily.md`).
- Đổi schema `AlertEvent` phải được TL duyệt và cập nhật DDL cùng lúc (skill `change-alertevent-schema`).
- Mỗi parser, mỗi luật tương quan bắt buộc có test `pytest` tái lập được.
- **Dữ liệu 100% giả lập**: IP lab dùng dải riêng RFC1918, ví dụ 10.10.0.0/16; 203.0.113.0/24 (TEST-NET-3) chỉ dùng trong tài liệu minh họa. Không credential thật, không kết nối hay quét thiết bị thật, không dán dữ liệu nhạy cảm lên AI công cộng.

## Cách trợ lý làm việc
- Khi đề xuất thay đổi code, kèm: tên nhánh, commit message đúng khuôn, lệnh test cần chạy.
- Chỉ dựa vào thông tin người dùng cho biết về tiến độ, thời gian, kết quả CI; không tự suy ra. Ví dụ: người dùng nói thẻ trễ ≥3 ngày thì gợi ý tách thẻ nhỏ.
- Không bịa nội dung mẫu báo cáo, endpoint hay trường dữ liệu chưa có trong tài liệu repo; thiếu thì hỏi hoặc ghi đề xuất vào `docs/DECISIONS.md`.
- Cảnh báo khi việc đang làm đe dọa các mốc W4/W6/W8/W12/W13.

<!-- chat-omit-start -->
## Bản đồ tài liệu và skill
- `docs/INTERFACES.md` hợp đồng `AlertEvent`, `RawEvent`, `EventStore`, API · `docs/DECISIONS.md` quyết định và đề xuất chờ chốt · `docs/templates/` mẫu báo cáo · `docs/scenarios/` kịch bản test.
- Skill trong `.agents/skills/`: `git-workflow`, `review-pr`, `daily-report`, `pm-report`, `change-alertevent-schema`, `write-parser-tests`, `write-correlation-rule`, `make-test-scenario`, `debug-network-ingest`, `fe-api-contract-mock`.
<!-- chat-omit-end -->



