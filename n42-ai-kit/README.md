# Bộ AI Kit — Nhóm N4.2 (HKDN UTH × VNPT NET)

Một nguồn sự thật duy nhất, dùng được cho nhiều công cụ AI. Sửa một chỗ, mọi người cùng nhận.

```text
AGENTS.md                  Bối cảnh + quy định chung (Codex, Antigravity, Cursor đọc trực tiếp)
CLAUDE.md                  Trỏ tới AGENTS.md (cho Claude Code)
docs/
├── roles/                 TL, BE1, BE2, BE3, FE, QA: chỉ phần riêng của từng vai
├── INTERFACES.md          Hợp đồng AlertEvent, RawEvent, EventStore, API, DDL
├── DECISIONS.md           Quyết định và đề xuất chờ TL chốt
├── templates/             Chỗ dán mẫu Daily, Mẫu 2, Mẫu 3, hồ sơ bàn giao
└── scenarios/             Kịch bản kiểm thử (QA)
.agents/skills/            10 skill dùng khi cần (xem bảng dưới)
scripts/                   validate.py, build_chat_prompts.py
dist/chat/                 File dán cho ChatGPT/Gemini/Claude Project (tự sinh)
```

## Cách dùng theo công cụ

**Codex, Antigravity, Cursor, Claude Code** (đọc thẳng từ repo)
1. Chép toàn bộ kit vào **gốc repo** của dự án (giữ nguyên cấu trúc, nhớ cả thư mục ẩn `.agents`).
2. Mở dự án bằng công cụ. `AGENTS.md` được nạp tự động. Claude Code đọc `CLAUDE.md` (đã trỏ tới `AGENTS.md`).
3. Mở chat và nói vai trò của bạn, ví dụ: *"Tôi là BE2, hôm nay làm parser Cisco."* AI sẽ đọc `docs/roles/BE2.md`.
4. Skill nằm ở `.agents/skills/`: Codex và Antigravity quét thư mục này. Claude Code dùng `.claude/skills/`, nên chạy một trong hai: `cp -r .agents/skills .claude/skills` hoặc tạo symlink.

**ChatGPT, Gemini, Claude (chat thường)**
1. Chạy `python scripts/build_chat_prompts.py` để sinh `dist/chat/skill-<VAI>.md`.
2. Dán nội dung file của **đúng vai của bạn** vào:
   - ChatGPT: **Project → Instructions** (khuyên dùng, chỉ áp dụng trong Project) hoặc Custom Instructions. Gói trả phí tối đa 5.000 ký tự, gói Free/Go chỉ 1.500 nên không dán vừa. Mỗi file hiện dài khoảng 4.000–4.400 ký tự.
   - Gemini: Gem → Instructions.
   - Claude: Project → Project Knowledge, hoặc dán đầu cuộc chat.
3. Tải kèm `docs/INTERFACES.md` làm file của Project/Gem để AI biết hợp đồng dữ liệu.

## 10 skill

| Skill | Dùng khi | Ai hay dùng |
|---|---|---|
| `git-workflow` | Đặt nhánh, commit, chuẩn bị PR | Mọi người |
| `review-pr` | Review PR theo chuẩn nghiệm thu | TL, reviewer |
| `daily-report` | Viết Daily trước 18:00 | Mọi người |
| `pm-report` | Weekly, Monthly, email PM, hồ sơ bàn giao | TL |
| `change-alertevent-schema` | Đổi `AlertEvent`/DDL/API | Mọi người |
| `write-parser-tests` | Test parser ≥200 mẫu/hãng | BE2 |
| `write-correlation-rule` | Luật tương quan không hardcode | BE3 |
| `make-test-scenario` | Kịch bản + bộ sinh dữ liệu | QA, BE3 |
| `debug-network-ingest` | Mất gói, queue đầy, loop bị chặn | BE1, QA |
| `fe-api-contract-mock` | API service, mock khớp schema | FE |

## Kiểm tra

```bash
python scripts/validate.py          # skill hợp lệ? vai trò đủ? mẫu đã dán chưa?
python scripts/build_chat_prompts.py
```

## Việc TL cần làm trước (rất quan trọng)

1. **Dán nội dung mẫu chính thức** vào `docs/templates/` (Daily 6 mục, Mẫu 2 và Mẫu 3 mỗi mẫu 7 mục, hồ sơ 8 hạng mục). Chưa có thì AI từ chối soạn báo cáo chứ không tự bịa.
2. **Chốt các mục trong `docs/DECISIONS.md`** và `docs/INTERFACES.md` trước W4 (28/11), nhất là: thang severity 0–7 (D-01) và tên cột `event_timestamp`/`hostname` (D-02). Hiện tất cả đang ở trạng thái ĐỀ XUẤT; khi chốt, đổi trạng thái rồi chạy lại `build_chat_prompts.py`.
3. Soát lại nội dung `AGENTS.md` một lượt: đây là bản tổng hợp từ 6 file cũ, có chỉnh các chỗ lệch (xem mục dưới).

## Khác gì so với bộ 6 file cũ

- Bối cảnh và quy định chung tách ra một chỗ (`AGENTS.md`), file vai trò chỉ còn phần riêng.
- Thống nhất: 2 reviewer cho parser, luật và `receiver/`; khuôn commit dùng khoảng trắng; thang severity 0–7; tên cột `event_timestamp`/`hostname`; ghi đúng dải IP (10.x, 192.168.x là private, chỉ 203.0.113.x là TEST-NET).
- Bổ sung hợp đồng giao diện (`INTERFACES.md`) mà các file cũ chỉ nhắc "đừng phá vỡ".
- Các điều AI không thể tự biết (trễ mấy ngày, CI xanh chưa, mấy giờ) giờ được viết thành "dựa vào điều người dùng cho biết".
- Thêm gợi ý ghi DB theo lô để chịu 1.000 sự kiện/giây.
- Bỏ câu "xác nhận đã hiểu rồi hỏi tôi" khỏi bản cho agent (chỉ còn trong bản dán chat).
- Việc lặp lại chuyển thành skill nạp khi cần.

## Giới hạn cần biết

- Chưa thử trên Codex/Antigravity thật; đường dẫn quét skill có thể đổi theo phiên bản, nếu không thấy skill thì đối chiếu tài liệu của công cụ.
- Mọi mục ở `docs/DECISIONS.md` là đề xuất của người soạn bộ kit, không phải quyết định đã được nhóm thông qua.
