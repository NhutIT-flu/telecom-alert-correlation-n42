# NOC VNPT NET — Frontend Dashboard (Module M7)

> **Dự án N4.2** — Hệ thống Thu thập & Phân tích Cảnh báo Viễn thông  
> **Chương trình** Học kỳ Doanh nghiệp UTH × VNPT NET (2026–2027)  
> **Người phụ trách**: Lê Khắc Huy (Frontend Engineer — FE)  
> **Thẻ Jira**: [N42-20](https://nhutp2945-1793259952237.atlassian.net/browse/N42-20) · **Epic cha**: N42-6 (Module M7)  
> **Baseline đối chiếu**: 03/11/2026 (`docs/DATA_AND_API_DESIGN.md`, `docs/ARCHITECTURE_DESIGN.md`, `docs/TECHNICAL_DESIGN_DOCUMENT.md`)

---

## Mục lục

1. [Tổng quan](#tổng-quan)
2. [Yêu cầu môi trường](#yêu-cầu-môi-trường)
3. [Khởi chạy môi trường phát triển](#khởi-chạy-môi-trường-phát-triển)
4. [Build production](#build-production)
5. [Cấu trúc thư mục](#cấu-trúc-thư-mục)
6. [Bảng màu NOC Dark Theme](#bảng-màu-noc-dark-theme)
7. [Hợp đồng dữ liệu AlertEvent (v0.9)](#hợp-đồng-dữ-liệu-alertevent-v09)
8. [Bộ dữ liệu mẫu & Fixture Adapter (N42-20)](#bộ-dữ-liệu-mẫu--fixture-adapter-n42-20)
9. [Hướng dẫn kiểm thử nghiệm thu (AC 1, AC 2, TC-UI-001/006)](#hướng-dẫn-kiểm-thử-nghiệm-thu-ac-1-ac-2-tc-ui-001006)
10. [Tích hợp API Backend (Baseline W1)](#tích-hợp-api-backend-baseline-w1)
11. [Quy chuẩn an toàn thông tin & IP Lab](#quy-chuẩn-an-toàn-thông-tin--ip-lab)

---

## Tổng quan

Module M7 cung cấp giao diện điều hành (NOC Dashboard) cho hệ thống giám sát cảnh báo mạng viễn thông thời gian thực, bao gồm 6 màn hình chính:

| # | Màn hình | Mô tả |
|---|---|---|
| 1 | **Dòng thời gian (Event Explorer)** | 4 thẻ KPI (TC-UI-001) + Bảng sự kiện thời gian thực kèm Detail Panel tách trường chuẩn hóa khỏi bản tin thô |
| 2 | **Chi tiết thiết bị** | Tra cứu lịch sử cảnh báo theo Router / Switch / Firewall trong dải lab `10.10.0.0/16` |
| 3 | **Bộ lọc & Tra cứu** | Lọc đa chiều theo thời gian, hostname, IP nguồn, vendor, mức độ (RFC 5424) |
| 4 | **Thống kê viễn thông** | Phân bổ cảnh báo theo Vendor (CISCO, HUAWEI, LINUX) phục vụ AC-02 (Corpus 200 mẫu) |
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
│   ├── fixtures/                  # Bộ dữ liệu mẫu có version theo N42-20
│   │   ├── events-v1.json         # Fixture v1.0 hợp lệ (5 sự kiện đa vendor, RFC 1918)
│   │   ├── events-empty.json      # Fixture rỗng [] kiểm thử AC 2
│   │   └── index.ts
│   ├── types/                     # Hợp đồng kiểu dữ liệu TypeScript
│   │   ├── alert.ts               # Schema AlertEvent v0.9 & Severity RFC 5424 (D-01)
│   │   └── index.ts
│   ├── services/                  # Tầng fetch & Fixture Adapter
│   │   ├── fixtureAdapter.ts      # Adapter nạp fixture, deduplication và KPI (N42-20)
│   │   ├── api.ts                 # Axios client tập trung + interceptors chuẩn hóa lỗi
│   │   ├── alertService.ts        # Service gọi API Backend (/health)
│   │   ├── mockData.ts            # Mock data chuẩn
│   │   └── index.ts
│   ├── components/
│   │   └── common/                # UI component dùng chung
│   │       ├── Header.tsx         # Thanh tiêu đề NOC + đồng hồ ICT/UTC + API status
│   │       ├── Sidebar.tsx        # Điều hướng 6 màn hình + mốc dự án
│   │       ├── SeverityBadge.tsx  # Huy hiệu mức độ cảnh báo (Icon + Text + Số RFC 5424)
│   │       └── index.ts
│   ├── pages/                     # 6 màn hình chính Module M7
│   │   ├── DashboardOverviewPage.tsx   # Màn hình (1): 4 thẻ KPI + Live Table + Detail Panel + Fixture Switcher
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
  id: string;               // UUID
  received_at: string;      // ISO 8601 UTC — thời điểm hệ thống tiếp nhận
  event_timestamp: string;  // ISO 8601 UTC — thời điểm sự kiện từ thiết bị
  source_ip: string;        // IP nguồn: dải lab 10.10.0.0/16 hoặc TEST-NET 203.0.113.0/24
  hostname: string;         // Tên thiết bị (router/switch/firewall)
  facility: number;         // Syslog facility (0–23)
  severity: number;         // RFC 5424 (0: Emergency → 7: Debug)
  program: string;          // Tiến trình/process ghi log
  message: string;          // Nội dung thông điệp đã chuẩn hóa
  raw_payload: string;      // Bản tin thô nhận từ Syslog
  vendor: string;           // CISCO | HUAWEI | LINUX | RFC3164 | RFC5424 | UNKNOWN
  category: string;         // Phân loại do BE2 gán khi chuẩn hóa
}
```

---

## Bộ dữ liệu mẫu & Fixture Adapter (N42-20)

Tệp `src/services/fixtureAdapter.ts` cung cấp tầng truy xuất dữ liệu mẫu phục vụ kiểm thử giao diện:
1. **Nạp đa kịch bản:** Hỗ trợ 3 chế độ (`success`, `empty`, `error`) kèm độ trễ mạng giả lập `delayMs` để quan sát hiệu ứng tải.
2. **Khử trùng lặp (`mergeEvents`):** Đảm bảo tính toán toàn vẹn khi retry, không sinh ra dòng trùng lặp dựa trên Event UUID.
3. **Tính toán KPI (`calculateKpis`):** Tự động tính 4 thẻ KPI dựa trên dữ liệu sự kiện thực tế trong fixture, không suy diễn số liệu ảo.

---

## Hướng dẫn kiểm thử nghiệm thu (AC 1, AC 2, TC-UI-001/006)

Mở trình duyệt tại `http://localhost:5173` và kiểm tra theo các bước sau:

| Mã kiểm thử | Thao tác trên giao diện | Kết quả mong đợi | Trạng thái |
|:---|:---|:---|:---:|
| **AC 1 / TC-UI-001** | Chọn chế độ **Hợp lệ v1.0** | 4 thẻ KPI hiển thị chính xác (Tổng sự kiện: 5, Sự cố mở: 1, Tốc độ: 10 msg/s, Trạng thái: HEALTHY). Bảng hiển thị 5 sự kiện với đầy đủ nhãn chữ và icon mức độ nghiêm trọng (RFC 5424). | ✅ PASS |
| **AC 2 (Empty)** | Bấm nút **Dữ liệu rỗng** | Giao diện hiển thị Empty State chuyên biệt với biểu tượng thư mục rỗng và nút nạp lại. | ✅ PASS |
| **AC 2 (Error)** | Bấm nút **Giả lập lỗi** | Giao diện hiển thị Error State màu đỏ với thông báo lỗi rõ ràng và nút **Thử lại kết nối (Retry)**. | ✅ PASS |
| **AC 2 (Retry deduplication)** | Bấm nút **Tải lại** nhiều lần | Dữ liệu được nạp lại mượt mà, tổng số dòng vẫn giữ nguyên là 5, **hoàn toàn không bị nhân bản dòng trùng lặp**. | ✅ PASS |
| **TC-UI-006 (A11y)** | Dùng phím `Tab` di chuyển vào dòng bảng, bấm `Enter` hoặc `Space` | Dòng mở rộng (Detail Panel) hiển thị chi tiết các trường chuẩn hóa và hộp bản tin thô `raw_payload`. Bấm lại `Enter`/`Space` để đóng. | ✅ PASS |

---

## Tích hợp API Backend (Baseline W1)

- **Hiện hành (Baseline W1):** Chỉ có duy nhất `GET /api/health`.
- **Target (W7–W8 - Thẻ N42-34):** Các endpoint ingest (`POST /api/v1/events`), query (`GET /api/v1/events`) sẽ được kết nối sau khi BE2 bàn giao OpenAPI.

---

## Quy chuẩn an toàn thông tin & IP Lab

- **Dải IP lab riêng (RFC 1918):** `10.10.0.0/16` (ví dụ `10.10.1.1`, `10.10.2.10`, `10.10.10.1`).
- **Dải IP tài liệu minh họa (RFC 5737):** `203.0.113.0/24` (TEST-NET-3).
- Không commit tệp `.env`, `.env.development`, credential hay token vào Git. Quét công cụ `python tools/check_sensitive.py` phải đạt 100% xanh an toàn.
