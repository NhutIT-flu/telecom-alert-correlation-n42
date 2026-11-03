# MA TRẬN TRUY VẾT YÊU CẦU — N4.2

Ma trận nối đặc tả → thành phần → AC → kịch bản/evidence. Đây là baseline cần cập nhật cùng Jira khi scope hoặc hợp đồng thay đổi. Tình trạng code hiện tại phải căn cứ repo/commit, không suy ra từ thiết kế.

| Requirement | Thành phần/owner | AC liên quan | Bằng chứng kiểm thử |
|---|---|---|---|
| FR-01 UDP ingest | M1 / Phạm Hoàng Long | AC-01, AC-08 | KB fixtures, sent/received IDs, UDP counters |
| FR-02 REST ingest | M1 / Phạm Hoàng Long | AC-01, AC-02 | Request/response, status/error tests, event ID |
| FR-03 File import | M1 / Phạm Hoàng Long + QA | AC-01, AC-07 | Fixtures encoding/line error/duplicate, import report |
| FR-04/05 normalization & parse fallback | M2 / BE1 + Phạm Tấn Thành | AC-02, AC-08 | ≥200 labeled samples/format; expected/actual, raw retention |
| FR-06 durable storage | M4 / Phạm Tấn Thành | AC-03, AC-07 | Migration, write/read/restart/restore evidence |
| FR-07 event query | M4 / BE2 + FE | AC-03 | 1M dataset, filters, p95/query latency, pagination consistency |
| FR-08 statistics | M4/M7 / BE2 + FE | AC-04 | Known dataset and expected aggregates |
| FR-09 grouping/correlation | M5/M6 / Nguyễn Duy Minh | AC-05, AC-06 | KB-01..08 labels, TP/FP/FN, raw/incident/standalone counts |
| FR-10 incident lifecycle | M5/M7 / BE3 + FE | AC-04 | state transition, audit/evidence, UI/API response |
| FR-11 dashboard | M7 / Lê Khắc Huy | AC-04 | demo/video and API contract |
| FR-12 health/diagnostics | M1–M4 / BE1 + BE2 | AC-08 | readiness/live, dependency down, no sensitive fields |
| FR-13 deterministic replay | M8 / Ngô Châu Kiệt | AC-01, AC-05 | seed, fixture version, event IDs and expected labels |
| FR-14 export | M7 / FE + backend | AC-04, AC-08 | filter equivalence, escaping and size-bound checks |
| FR-15 rule configuration | M6 / Nguyễn Duy Minh | AC-05 | schema validation, version, dry-run, rollback evidence |
| NFR-01 throughput | M1/M3/M4 / BE1 + BE2 + QA | AC-01 | ≥1,000 msg/s × 1h; commit/config/machine and ID reconciliation |
| NFR-02 latency | M1–M7 / QA | AC-03 | documented endpoints and P50/P99 samples |
| NFR-03 observed drops | M1 / BE1 + QA | AC-01 | generator IDs, accepted/persisted counts, OS/socket counters |
| NFR-04 resources | Runtime / QA | AC-01 | CPU/RAM with core quota and monitoring scope |
| NFR-05 parser/query | M2/M4 / BE2 + QA | AC-02/03 | labeled format corpus; 1M query dataset and machine config |
| NFR-06 safe synthetic data | Whole team / TL + QA | AC-08 | secret scan, data/IP review, isolated network checklist |
| NFR-07 install/recovery | M4/M8 / BE2 + QA | AC-07 | clean install/restart/restore rehearsal and recorded duration |
| NFR-08 bounded processing | M3 / BE2 + QA | AC-01/07 | queue saturation, backpressure/drop policy and counters |

## Mốc kiểm soát

- W4: schema và corpus mẫu được đóng băng; thay đổi qua decision log.
- W6: ingest → normalize → persist chạy đầu-cuối (persistence hiện còn gap).
- W8: query/API và prototype UI theo hợp đồng versioned.
- W12: detection checkpoint ≥70%, TL ghi quyết định giữ/thu hẹp scope.
- W13: nghiệm thu theo AC và code freeze.
- W18: cài lại, demo, bàn giao đủ tài liệu/evidence.

## Cách duy trì

Mỗi Jira item chạm FR/NFR phải dẫn tới test hoặc ghi rõ chưa có test/evidence. Khi FR, schema, API, rule hoặc AC đổi, cập nhật đồng bộ `SYSTEM_REQUIREMENTS_AND_USE_CASES.md`, design specs, `ACCEPTANCE_CRITERIA.md`, `TEST_PLAN.md` và `DECISIONS.md`.
