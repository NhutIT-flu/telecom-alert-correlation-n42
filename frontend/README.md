# NOC VNPT NET — Frontend Dashboard (Module M7)

> **Dự án N4.2** — Hệ thống Thu thập & Phân tích Cảnh báo Viễn thông  
> **Chương trình** Học kỳ Doanh nghiệp UTH × VNPT NET (2026–2027)  
> **Người phụ trách**: Lê Khắc Huy (Frontend Engineer — FE)  
> **Thẻ Jira**: [N42-19](https://nhutp2945-1793259952237.atlassian.net/browse/N42-19) · **Epic cha**: N42-6 (Module M7)  
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
8. [Tích hợp API Backend (Baseline W1)](#tích-hợp-api-backend-baseline-w1)
9. [Mock Data & Quy chuẩn IP (Baseline 03/11/2026)](#mock-data--quy-chuẩn-ip-baseline-03112026)
10. [Quy chuẩn an toàn thông tin](#quy-chuẩn-an-toàn-thông-tin)
11. [Lịch trình tích hợp](#lịch-trình-tích-hợp)
12. [Khắc phục sự cố thường gặp](#khắc-phục-sự-cố-thường-gặp)

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

### Bước 1: Di chuyển vào thư mục frontend

```bash
cd frontend
```

### Bước 2: Cài đặt toàn bộ gói phụ thuộc

```bash
npm install
```

### Bước 3: Khởi động Dev server

```bash
npm run dev
```

Sau khi khởi động thành công, truy cập giao diện tại:

```
http://localhost:5173
```

> **Lưu ý:** Giai đoạn W2–W4 sử dụng `VITE_USE_MOCK=true` trong `.env.development`. Giao diện hoạt động trơn tru với dữ liệu giả lập chuẩn, console browser sạch 100% không báo lỗi đỏ 404. Thanh Header hiển thị trạng thái `DEV MOCK (W2–W4)` màu cyan.

### Bước 4: Chạy kiểm tra lint

```bash
npm run lint
```

Phải cho kết quả: `0 errors, 0 warnings`.

---

## Build production

Tạo gói đóng gói tối ưu cho môi trường sản xuất:

```bash
npm run build
```

Sau khi build xong:
- Gói tĩnh được tạo tại thư mục `frontend/dist/`
- Kiểm tra TypeScript: `tsc -b` không có lỗi
- Bundle JavaScript đã minify và tối ưu gzip

Xem trước bản build production:

```bash
npm run preview
```

---

## Cấu trúc thư mục

```text
frontend/
├── dist/                          # Gói build production (tự động tạo, không commit)
├── public/                        # Tài nguyên tĩnh công khai
├── src/
│   ├── types/                     # Hợp đồng kiểu dữ liệu TypeScript
│   │   ├── alert.ts               # Schema AlertEvent v0.9 & Severity RFC 5424 (D-01)
│   │   └── index.ts
│   ├── services/                  # Tầng fetch — tách biệt hoàn toàn khỏi UI
│   │   ├── api.ts                 # Axios client tập trung + interceptors chuẩn hóa lỗi
│   │   ├── alertService.ts        # Gọi API: /health (thật), query/simulate (mock W2-W4)
│   │   ├── mockData.ts            # Dữ liệu giả lập chuẩn RFC 1918 10.10.x & TEST-NET-3
│   │   └── index.ts
│   ├── components/
│   │   └── common/                # UI component dùng chung
│   │       ├── Header.tsx         # Thanh tiêu đề NOC + đồng hồ ICT/UTC + API status
│   │       ├── Sidebar.tsx        # Điều hướng 6 màn hình + mốc dự án
│   │       ├── SeverityBadge.tsx  # Huy hiệu màu severity (Icon + Text + Số RFC 5424)
│   │       └── index.ts
│   ├── pages/                     # 6 màn hình chính Module M7
│   │   ├── DashboardOverviewPage.tsx   # Màn hình (1): 4 thẻ KPI + Live Table + Detail Panel
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

Giao diện sử dụng bảng màu chuyên dụng cho Trung tâm Giám sát Điều hành Mạng (NOC), định nghĩa trong [`tailwind.config.js`](./tailwind.config.js):

| Token Tailwind | Mã màu HEX | Vai trò |
|---|---|---|
| `noc-bg` | `#0a0e17` | Nền màn hình chính |
| `noc-surface` | `#121826` | Nền card, panel, bảng |
| `noc-border` | `#1e293b` | Đường viền phân cách |
| `noc-critical` | `#ef4444` | Cảnh báo CRITICAL (Severity 0–2: Emergency, Alert, Critical) |
| `noc-major` | `#f97316` | Cảnh báo MAJOR (Severity 3: Error) |
| `noc-minor` | `#f59e0b` | Cảnh báo WARNING (Severity 4: Warning) |
| `noc-info` | `#06b6d4` | Thông tin INFO (Severity 5–6: Notice, Info) |

**Quy tắc hiển thị mức độ cảnh báo (RFC 5424 D-01 & ARCHITECTURE_DESIGN Mục 5):**
Mọi badge cảnh báo bắt buộc phải có cả **Icon + Nhãn văn bản + Mã số (0–7)**, không chỉ phân biệt bằng màu sắc đơn thuần.

---

## Hợp đồng dữ liệu AlertEvent (v0.9)

Schema `AlertEvent` bám sát `n42-ai-kit/docs/INTERFACES.md` và `docs/DATA_AND_API_DESIGN.md` (Baseline 03/11/2026):

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

## Tích hợp API Backend (Baseline W1)

Theo `docs/DATA_AND_API_DESIGN.md` Mục 4 (Baseline 03/11/2026):
- **Hiện hành (Baseline W1):** Chỉ có duy nhất `GET /api/health` (`status: "UP"`, `service: "n42-api"`, `version: "0.1.0"`).
- **Target (W7–W8):** Các endpoint ingest (`POST /api/v1/events`), query (`GET /api/v1/events?from=&to=&hostname=&severity=...`) do BE2 bàn giao qua tài liệu OpenAPI.
- **Frontend Layer:** Tuyệt đối không gọi API ngoài hợp đồng OpenAPI. Trong giai đoạn W2–W4, toàn bộ query được fallback an toàn bằng mock service nội bộ.

---

## Mock Data & Quy chuẩn IP (Baseline 03/11/2026)

Tuân thủ nghiêm ngặt theo `docs/ACCEPTANCE_CRITERIA.md` Mục 3 và `docs/TECHNICAL_DESIGN_DOCUMENT.md` Mục 6:
- **Dải IP lab riêng (RFC 1918):** `10.10.0.0/16` (ví dụ `10.10.1.1`, `10.10.2.10`, `10.10.10.1`).
- **Dải IP tài liệu minh họa (RFC 5737):** `203.0.113.0/24` (TEST-NET-3).
- **Tuyệt đối không dùng:** IP thật của thiết bị hạ tầng viễn thông VNPT NET.

---

## Quy chuẩn an toàn thông tin

- Không commit tệp `.env`, `.env.local`, `.env.development`, token bí mật hoặc credential vào Git.
- Kiểm tra mã nguồn với công cụ quét bảo mật: `python tools/check_sensitive.py`.
- Tuân thủ quy trình Git Flow: Nhánh `feature/N42-19-react-vite-setup`, commit theo chuẩn `feat: khoi tao du an react vite tailwind css (N42-19)`, PR có ít nhất 1 reviewer phê duyệt.
