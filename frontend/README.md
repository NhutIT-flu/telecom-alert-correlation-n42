# NOC VNPT NET — Frontend Dashboard (Module M7)

> **Dự án N4.2** — Hệ thống Thu thập & Phân tích Cảnh báo Viễn thông  
> **Chương trình** Học kỳ Doanh nghiệp UTH × VNPT NET (2026–2027)  
> **Người phụ trách**: Lê Khắc Huy (Frontend Engineer — FE)  
> **Thẻ Jira**: [N42-20](https://nhutp2945-1793259952237.atlassian.net/browse/N42-20) (Dựng bảng cảnh báo) · [N42-28](https://nhutp2945-1793259952237.atlassian.net/browse/N42-28) (Bộ lọc cảnh báo đa tiêu chí)  
> **Epic cha**: N42-6 (Module M7)  
> **Baseline đối chiếu**: 03/11/2026 (`docs/DATA_AND_API_DESIGN.md`, `docs/ARCHITECTURE_DESIGN.md`, `docs/REQUIREMENTS_TRACEABILITY_MATRIX.md`)

---

## Mục lục

1. [Tổng quan](#tổng-quan)
2. [Yêu cầu môi trường](#yêu-cầu-môi-trường)
3. [Khởi chạy môi trường phát triển](#khởi-chạy-môi-trường-phát-triển)
4. [Build production](#build-production)
5. [Cấu trúc thư mục](#cấu-trúc-thư-mục)
6. [Bảng màu NOC Dark Theme](#bảng-màu-noc-dark-theme)
7. [Hợp đồng dữ liệu AlertEvent (v0.9)](#hợp-đồng-dữ-liệu-alertevent-v09)
8. [Bộ lọc cảnh báo đa tiêu chí & Engine (N42-28)](#bộ-lọc-cảnh-báo-đa-tiêu-chí--engine-n42-28)
9. [Bộ dữ liệu mẫu Fixture v1.1.0 (N42-20 & N42-28)](#bộ-dữ-liệu-mẫu-fixture-v110-n42-20--n42-28)
10. [Ma trận kiểm thử nghiệm thu RTM (AC 1–4, TC-UI-002/003/006)](#ma-trận-kiểm-thử-nghiệm-thu-rtm-ac-14-tc-ui-002003006)
11. [Tích hợp API Backend (Baseline W1 & Target W7–W8)](#tích-hợp-api-backend-baseline-w1--target-w7w8)
12. [Quy chuẩn an toàn thông tin & IP Lab](#quy-chuẩn-an-toàn-thông-tin--ip-lab)

---

## Tổng quan

Module M7 cung cấp giao diện điều hành (NOC Dashboard) cho hệ thống giám sát cảnh báo mạng viễn thông thời gian thực, bao gồm 6 màn hình chính:

| # | Màn hình | Mô tả |
|---|---|---|
| 1 | **Dòng thời gian (Event Explorer)** | 4 thẻ KPI (TC-UI-001) + Bộ lọc đa tiêu chí (N42-28) + Bảng sự kiện thời gian thực kèm Detail Panel tách trường chuẩn hóa khỏi bản tin thô |
| 2 | **Chi tiết thiết bị** | Tra cứu lịch sử cảnh báo theo Router / Switch / Firewall trong dải lab `10.10.0.0/16` |
| 3 | **Bộ lọc & Tra cứu** | Lọc đa chiều theo thời gian UTC, hostname, IP nguồn, vendor, mức độ (RFC 5424) |
| 4 | **Thống kê viễn thông** | Phân bổ cảnh báo theo Vendor (CISCO, HUAWEI, LINUX) phục vụ AC-02 |
| 5 | **Gom nhóm tương quan (Incident Explorer)** | Sự cố gom nhóm từ luật tương quan (M5/M6), đo tỷ lệ giảm nhiễu (mục tiêu ≥70% theo AC-06) |
| 6 | **Xuất báo cáo** | Xuất CSV/PDF canonical tuân thủ bộ lọc và escaping (TC-EXP-001) |

**Stack công nghệ:**

| Thành phần | Phiên bản | Vai trò |
|---|---|---|
| React | 19.3.1 | Framework giao diện (Function components + Hooks) |
| TypeScript | 6.0.x | Kiểm tra kiểu tĩnh strict (`verbatimModuleSyntax`) |
| Vite | 8.3.x | Build tool & Dev server HMR |
| Tailwind CSS | 3.4.x | Utility-first CSS — NOC Dark Theme Palette |
| Lucide React | 1.70.x | Icon hệ thống mạng & chỉ báo Severity |
| Axios | 1.21.x | HTTP Client tích hợp Backend API (fetch layer tách biệt) |

---

## Yêu cầu môi trường

| Yêu cầu | Phiên bản tối thiểu | Ghi chú |
|---|---|---|
| Node.js | **20 LTS trở lên** | Yêu cầu bắt buộc theo `CONTRIBUTING.md` |
| npm | 10+ | Đi kèm Node.js 20 LTS |

Kiểm tra phiên bản hiện tại:

```bash
node --version   # Phải >= v20.0.0
npm --version    # Phải >= 10.0.0
```

---

## Khởi chạy môi trường phát triển

```bash
cd frontend
npm install
npm run dev
```

Truy cập giao diện tại: `http://localhost:5173`.

Kiểm tra chất lượng code:
```bash
npm run lint     # Phải 0 errors, 0 warnings
npm run build    # Build production dist/ sạch sẽ
```

---

## Cấu trúc thư mục

```text
frontend/
├── dist/                          # Gói build production (tự động tạo, không commit)
├── public/                        # Tài nguyên tĩnh công khai (favicon)
├── src/
│   ├── fixtures/                  # Bộ dữ liệu mẫu có version theo N42-20 & N42-28
│   │   ├── events-v1.json         # Fixture v1.1.0 hợp lệ (12 sự kiện đa vendor, RFC 1918)
│   │   ├── events-empty.json      # Fixture rỗng [] kiểm thử kịch bản rỗng
│   │   └── index.ts
│   ├── types/                     # Hợp đồng kiểu dữ liệu TypeScript
│   │   ├── alert.ts               # Schema AlertEvent v0.9 & Severity RFC 5424 (D-01)
│   │   ├── filter.ts              # FilterCriteria, TimePreset, FilterValidationResult (N42-28)
│   │   └── index.ts
│   ├── services/                  # Tầng fetch, Fixture Adapter & Filter Engine
│   │   ├── filterService.ts       # Thuật toán lọc đa tiêu chí thuần khiết & validation UTC (N42-28)
│   │   ├── fixtureAdapter.ts      # Adapter nạp fixture, snapshot update và KPI chuẩn hóa (N42-20)
│   │   ├── api.ts                 # Axios client tập trung + interceptors chuẩn hóa lỗi
│   │   ├── alertService.ts        # Service gọi API Backend (/health)
│   │   ├── mockData.ts            # Mock data chuẩn
│   │   └── index.ts
│   ├── components/
│   │   ├── common/                # UI component dùng chung
│   │   │   ├── Header.tsx         # Thanh tiêu đề NOC + đồng hồ ICT/UTC + API status
│   │   │   ├── Sidebar.tsx        # Điều hướng 6 màn hình + mốc dự án
│   │   │   ├── SeverityBadge.tsx  # Huy hiệu mức độ cảnh báo (Icon + Text + Số RFC 5424)
│   │   │   └── index.ts
│   │   └── filter/                # UI component bộ lọc đa tiêu chí (N42-28)
│   │       ├── AlertFilterPanel.tsx # Panel lọc thời gian, vendor, severity, hostname, search
│   │       └── index.ts
│   ├── pages/                     # 6 màn hình chính Module M7
│   │   ├── DashboardOverviewPage.tsx   # Màn hình (1): KPI + Filter Panel + Bảng sự kiện + Phân trang
│   │   ├── DeviceDetailPage.tsx        # Màn hình (2): Tra cứu thiết bị mạng lab
│   │   ├── AlertSearchPage.tsx         # Màn hình (3): Bộ lọc đa chiều
│   │   ├── DeviceStatsPage.tsx         # Màn hình (4): Thống kê Vendor
│   │   ├── CorrelationAlertsPage.tsx   # Màn hình (5): Gom nhóm Incident & Noise reduction
│   │   ├── ReportsPage.tsx             # Màn hình (6): Xuất CSV/PDF escaping
│   │   └── index.ts
│   ├── App.tsx                    # Shell điều phối Header + Sidebar + Router màn hình
│   ├── index.css                  # Tailwind directives + cấu hình nền tối NOC
│   └── main.tsx                   # Điểm vào ứng dụng React
├── tailwind.config.js             # Bảng màu NOC Dark Palette
├── postcss.config.js              # Cấu hình PostCSS + Autoprefixer
├── vite.config.ts                 # Cấu hình Vite
├── tsconfig.app.json              # Cấu hình TypeScript
├── package.json                   # Danh sách gói phụ thuộc
└── README.md                      # Tài liệu này
```

---

## Bảng màu NOC Dark Theme

Định nghĩa trong [`tailwind.config.js`](./tailwind.config.js):

| Token Tailwind | Mã màu HEX | Vai trò |
|---|---|---|
| `noc-bg` | `#0a0e17` | Nền màn hình chính |
| `noc-surface` | `#121826` | Nền card, panel, bảng |
| `noc-border` | `#1e293b` | Đường viền phân cách |
| `noc-critical` | `#ef4444` | Cảnh báo CRITICAL (Severity 0–2: Emergency, Alert, Critical) |
| `noc-major` | `#f97316` | Cảnh báo MAJOR (Severity 3: Error) |
| `noc-minor` | `#f59e0b` | Cảnh báo WARNING (Severity 4: Warning) |
| `noc-info` | `#06b6d4` | Thông tin INFO (Severity 5–6: Notice, Info) |

---

## Hợp đồng dữ liệu AlertEvent (v0.9)

Schema `AlertEvent` bám sát `n42-ai-kit/docs/INTERFACES.md` và `docs/DATA_AND_API_DESIGN.md`:

```typescript
export interface AlertEvent {
  id: string;               // UUID định danh sự kiện
  received_at: string;      // ISO 8601 UTC — thời điểm hệ thống tiếp nhận
  event_timestamp: string;  // ISO 8601 UTC — thời điểm sự kiện từ thiết bị
  source_ip: string;        // IP nguồn: dải lab 10.10.0.0/16 hoặc TEST-NET 203.0.113.0/24
  hostname: string;         // Tên thiết bị (router/switch/firewall)
  facility: number;         // Syslog facility (0–23)
  severity: number;         // RFC 5424 (0: Emergency → 7: Debug)
  program: string;          // Tiến trình/process ghi log
  message: string;          // Nội dung thông điệp đã chuẩn hóa
  raw_payload: string;      // Bản tin thô nhận từ Syslog
  vendor: string;           // CISCO | HUAWEI | LINUX | RFC3164 | RFC5424
  category: string;         // Phân loại cảnh báo
}
```

---

## Bộ lọc cảnh báo đa tiêu chí & Engine (N42-28)

Triển khai tại `src/components/filter/AlertFilterPanel.tsx` và `src/services/filterService.ts`:
1. **Lọc đa chiều kết hợp (AC 1):** Hỗ trợ lọc đồng thời theo khoảng thời gian UTC (`startTime` – `endTime`), tên thiết bị (`hostname`), nhà sản xuất (`vendor`), danh sách mức độ (`severity` 0–7 RFC 5424) và từ khóa toàn văn (`searchQuery`).
2. **Kiểm tra thời gian đảo chiều (AC 2):** Hàm `validateCriteria` phát hiện `startTime > endTime`, hiển thị cảnh báo lỗi inline màu đỏ trên giao diện và vô hiệu hóa nút Áp dụng bộ lọc.
3. **Trạng thái rỗng chuyên biệt (AC 3):** Khi kết quả lọc không có bản ghi nào (`filteredEvents.length === 0`), giao diện hiển thị Empty Filter State kèm nút **Đặt lại bộ lọc (Reset Filter)**.
4. **Tự động đặt lại phân trang (AC 4):** Mỗi khi điều kiện lọc thay đổi hoặc đặt lại, con trỏ phân trang tự động quay về trang 1 (`setCurrentPage(1)`).
5. **Cơ chế chống Race Condition (Sprint 2):** Sử dụng `requestIdRef` bảo đảm các phản hồi cũ hoặc thao tác reload nhanh không bao giờ ghi đè lên kết quả của bộ lọc mới nhất.

---

## Bộ dữ liệu mẫu Fixture v1.1.0 (N42-20 & N42-28)

Tệp `src/fixtures/events-v1.json` được nâng cấp lên **version 1.1.0** với 12 bản ghi chuẩn hóa:
- **5 nhà sản xuất:** `CISCO`, `HUAWEI`, `LINUX`, `RFC5424`, `RFC3164`.
- **Mức độ phong phú:** Phủ đầy đủ severity từ 0 (Emergency) đến 6 (Informational).
- **Mạng IP lab:** Tuân thủ chuẩn RFC 1918 `10.10.x.x` (10.10.1.1, 10.10.2.1, 10.10.3.1, 10.10.10.1...).

---

## Ma trận kiểm thử nghiệm thu RTM (AC 1–4, TC-UI-002/003/006)

Mở trình duyệt tại `http://localhost:5173` và đối chiếu theo ma trận sau:

| Mã kiểm thử | Thao tác trên giao diện | Kết quả mong đợi (Expected Results) | Trạng thái |
|:---|:---|:---|:---:|
| **AC 1 / TC-UI-002 (Cisco Sev 0–2)** | Chọn Vendor = `Cisco IOS-XE`, Severity = `0` và `2`, bấm Áp dụng | Bảng trả về đúng **2 sự kiện ID**: `a1b2c3d4-0001-...` (Sev 2) và `a1b2c3d4-0006-...` (Sev 0). | ✅ PASS |
| **AC 1 / TC-UI-002 (Huawei Sev 3–4)** | Chọn Vendor = `Huawei VRP`, Severity = `3` và `4`, bấm Áp dụng | Bảng trả về đúng **2 sự kiện ID**: `a1b2c3d4-0003-...` (Sev 4) và `a1b2c3d4-0007-...` (Sev 3). | ✅ PASS |
| **AC 2 (Thời gian đảo chiều)** | Nhập `startTime` lớn hơn `endTime` (ví dụ: `2026-11-20` đến `2026-11-18`) | Xuất hiện khung lỗi màu đỏ inline: *"Khoảng thời gian không hợp lệ: Thời gian bắt đầu không được lớn hơn thời gian kết thúc"*, nút Áp dụng bị disabled. | ✅ PASS |
| **AC 2 (Kiểm tra biên UTC)** | Nhập mốc thời gian đúng bằng thời điểm của sự kiện (so sánh `>=` và `<=`) | Bản tin tại đúng mốc biên thời gian vẫn được giữ lại trong danh sách kết quả, không bị lệch múi giờ. | ✅ PASS |
| **AC 3 (Empty Filter State)** | Nhập từ khóa tìm kiếm không tồn tại (ví dụ: `firewall-xyz`) | Hiển thị giao diện Empty Filter State chuyên biệt kèm nút **Đặt lại bộ lọc (Reset Filter)**. Bấm nút Reset ➔ khôi phục 12 sự kiện. | ✅ PASS |
| **AC 4 / TC-UI-003 (Reset cursor)** | Chuyển sang Trang 2 hoặc Trang 3, thay đổi Vendor rồi bấm Áp dụng | Danh sách được lọc và phân trang tự động **quay trở về Trang 1**. | ✅ PASS |
| **TC-UI-006 (A11y)** | Dùng phím `Tab` duyệt qua các ô nhập, phím `Space`/`Enter` để chọn chip Severity và mở xem `raw_payload` | Tiêu điểm focus rõ ràng theo palette NOC, mở rộng dòng chi tiết mượt mà, hỗ trợ screen-reader với đầy đủ nhãn ARIA. | ✅ PASS |
| **Sprint 2 (Chống Race Condition)** | Bấm chuyển đổi nhanh giữa các chế độ fixture và nút Tải lại liên tục | Không xảy ra hiện tượng dữ liệu cũ ghi đè dữ liệu mới, kết quả hiển thị khớp 100% với lựa chọn cuối cùng. | ✅ PASS |

---

## Tích hợp API Backend (Baseline W1 & Target W7–W8)

- **Hiện hành (Baseline W1):** Chỉ có duy nhất `GET /api/health`.
- **Target (W7–W8 - Thẻ N42-34 & N42-67):** Các endpoint ingest (`POST /api/v1/events`), query (`GET /api/v1/events`) sẽ được kết nối sau khi BE2 bàn giao OpenAPI.

---

## Quy chuẩn an toàn thông tin & IP Lab

- **Dải IP lab riêng (RFC 1918):** `10.10.0.0/16` (ví dụ `10.10.1.1`, `10.10.2.10`, `10.10.10.1`).
- **Dải IP tài liệu minh họa (RFC 5737):** `203.0.113.0/24` (TEST-NET-3).
- Tuyệt đối không đưa credential, IP thật hoặc cấu hình production vào kho mã nguồn.
- Quét định kỳ bằng công cụ: `python tools/check_sensitive.py` bảo đảm 100% xanh an toàn.
