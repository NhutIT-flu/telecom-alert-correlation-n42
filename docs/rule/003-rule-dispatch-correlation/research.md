# Research: Engine điều phối và tương quan

## R1. Topology worker
- **Decision**: Một worker riêng FastAPI, một Dispatcher/Registry/Scheduler/CleanupManager logic; event pending PostgreSQL là nguồn việc.
- **Rationale**: Ít hạ tầng cho prototype, state theo group trong RAM + checkpoint bền vững.
- **Alternatives considered**: Quét DB từng rule, broker/nhiều worker; chi phí truy vấn hoặc vận hành cao hơn trước khi đo.
- **Source**: [engine-design.md](engine-design.md) mục 1–2/13.

## R2. Contract và cấu hình rule
- **Decision**: Logic Python handler, file cấu hình có version công bố snapshot rules; 5 thao tác initial_state/evaluate/on_time/prune_state/can_evict_state, context chỉ đọc, result có READY/NEEDS_HISTORY/INCOMPLETE.
- **Rationale**: Thêm rule không thêm bảng/interface process, riêng thuật toán nhưng dùng chung vận hành.
- **Alternatives considered**: Logic rule trong DB hoặc một handler/instance cho từng interface; khó kiểm thử và tốn tài nguyên.
- **Source**: 003 mục 3/11; 004 LinkFlap.

## R3. Chính xác qua restart
- **Decision**: Session advisory lock, receipt event_ids + registry snapshot trước đánh giá; result/checkpoint/evidence/progress commit atomically; fail-stop lỗi nghiêm trọng.
- **Rationale**: Không bỏ event hoặc nhân kết quả sau crash; một owner state.
- **Alternatives considered**: Max event ID cursor, bỏ qua rule lỗi; có thể làm mất việc/kết quả sai.
- **Source**: 003 mục 7/13.

## R4. Thời gian, guard, cleanup
- **Decision**: Đệm 3 giây một lần, timer theo nguồn và coverage; tính bù có giới hạn/horizon handler. Prune khác evict; active giữ nóng, recovered chưa closed có thể cold-load đủ guard.
- **Rationale**: Không phục hồi sai từ im lặng hoặc xóa state còn cần.
- **Alternatives considered**: Timer mỗi interface, chỉ giữ N mốc, reset rỗng sau restart.
- **Tích hợp 006**: Event processed vẫn có thể để lại guard chưa release; query guard bền vững trước timer. Cách lưu/query guard theo event cần đo; phương án bảng riêng nếu không đạt tải, không bỏ guard.

## R5. Phạm vi prototype
- LinkFlap là rule nghiệp vụ đầu; kiểm thử 5 rule dùng handler thử. Poll 200ms/batch500/retry/shutdown/memory budgets là giá trị thử, không cam kết SLA. Đường dẫn code hiện có và khung đề xuất ở [codebase-mapping.md](codebase-mapping.md); chưa gắn ticket implementation cụ thể hoặc chốt contract liên nhóm.
