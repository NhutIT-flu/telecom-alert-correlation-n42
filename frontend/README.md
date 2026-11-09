# NOC VNPT NET — Frontend Dashboard

> **Dự án N4.2** — Hệ thống Thu thập & Phân tích Cảnh báo Viễn thông  
> **Chương trình** Học kỳ Doanh nghiệp UTH × VNPT NET (2026–2027)  
> **Người phụ trách**: Lê Khắc Huy (Frontend Engineer — FE)  
> **Thẻ Jira**: [N42-19](https://nhutp2945-1793259952237.atlassian.net/browse/N42-19) · **Epic cha**: N42-6 (Module M7)

---

## Mục lục

1. [Tổng quan](#tổng-quan)
2. [Yêu cầu môi trường](#yêu-cầu-môi-trường)
3. [Khởi chạy môi trường phát triển](#khởi-chạy-môi-trường-phát-triển)
4. [Build production](#build-production)
5. [Cấu trúc thư mục](#cấu-trúc-thư-mục)
6. [Bảng màu NOC Dark Theme](#bảng-màu-noc-dark-theme)
7. [Hợp đồng dữ liệu AlertEvent](#hợp-đồng-dữ-liệu-alertevent)
8. [Tích hợp API Backend](#tích-hợp-api-backend)
9. [Mock Data (W2–W4)](#mock-data-w2w4)
10. [Quy chuẩn an toàn thông tin](#quy-chuẩn-an-toàn-thông-tin)
11. [Khắc phục sự cố thường gặp](#khắc-phục-sự-cố-thường-gặp)

---

## Tổng quan

Module M7 cung cấp giao diện điều hành (NOC Dashboard) cho hệ thống giám sát cảnh báo mạng viễn thông thời gian thực, bao gồm 6 màn hình chính:

| # | Màn hình | Mô tả |
|---|---|---|
| 1 | **Dòng thời gian** | KPI + Bảng sự kiện cảnh báo tổng quan theo thời gian thực |
| 2 | **Chi tiết thiết bị** | Tra cứu lịch sử cảnh báo theo Router / Switch / Firewall |
| 3 | **Bộ lọc & Tra cứu** | Lọc đa chiều theo thời gian, thiết bị, IP nguồn, mức độ |
| 4 | **Thống kê viễn thông** | Phân bổ cảnh báo theo loại thiết bị và nhà sản xuất |
| 5 | **Gom nhóm tương quan** | Sự cố gom nhóm từ luật tương quan (Module BE3) |
| 6 | **Xuất báo cáo** | Xuất CSV/PDF phục vụ báo cáo vận hành NOC VNPT NET |

**Stack công nghệ:**

| Thành phần | Phiên bản | Vai trò |
|---|---|---|
| React | 19.3.1 | Framework giao diện |
| TypeScript | 6.0.x | Kiểm tra kiểu tĩnh |
| Vite | 8.3.x | Build tool & Dev server HMR |
| Tailwind CSS | 3.4.x | Utility-first CSS — NOC Dark Theme |
| Lucide React | 1.70.x | Icon hệ thống mạng |
| Axios | 1.21.x | HTTP Client tích hợp Backend API |

---

## Yêu cầu môi trường

| Yêu cầu | Phiên bản tối thiểu | Ghi chú |
|---|---|---|
| Node.js | **20 LTS trở lên** | Yêu cầu bắt buộc theo CONTRIBUTING.md |
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

> **Lưu ý:** Nếu Backend API (`/api`) chưa khởi động, giao diện vẫn hoạt động bình thường với dữ liệu giả lập (Mock Data). Thanh Header sẽ hiển thị trạng thái **MOCK / STANDBY** thay vì **ONLINE**.

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

Truy cập tại `http://localhost:4173`.

---

## Cấu trúc thư mục

```text
frontend/
├── dist/                          # Gói build production (tự động tạo, không commit)
├── public/                        # Tài nguyên tĩnh công khai
├── src/
│   ├── types/                     # Hợp đồng kiểu dữ liệu TypeScript
│   │   ├── alert.ts               # Schema AlertEvent 10 trường (hợp đồng N42-19)
│   │   └── index.ts
│   ├── services/                  # Tầng fetch — tách biệt hoàn toàn khỏi UI
│   │   ├── api.ts                 # Axios client tập trung + interceptors
│   │   ├── alertService.ts        # Gọi API: /health, /events, /events/count, /ingest, /simulate
│   │   ├── mockData.ts            # Dữ liệu giả lập chuẩn RFC 5737 (W2–W4)
│   │   └── index.ts
│   ├── components/
│   │   └── common/                # UI component dùng chung
│   │       ├── Header.tsx         # Thanh tiêu đề NOC + đồng hồ + API status
│   │       ├── Sidebar.tsx        # Điều hướng 6 màn hình
│   │       ├── SeverityBadge.tsx  # Huy hiệu màu severity chuẩn NOC
│   │       └── index.ts
│   ├── pages/                     # 6 màn hình chính Module M7
│   │   ├── DashboardOverviewPage.tsx   # Màn hình (1)
│   │   ├── DeviceDetailPage.tsx        # Màn hình (2)
│   │   ├── AlertSearchPage.tsx         # Màn hình (3)
│   │   ├── DeviceStatsPage.tsx         # Màn hình (4)
│   │   ├── CorrelationAlertsPage.tsx   # Màn hình (5)
│   │   ├── ReportsPage.tsx             # Màn hình (6)
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

Giao diện sử dụng bảng màu chuyên dụng cho Trung tâm Giám sát Điều hành Mạng (NOC), được định nghĩa trong [`tailwind.config.js`](./tailwind.config.js):

| Token Tailwind | Mã màu HEX | Vai trò |
|---|---|---|
| `noc-bg` | `#0a0e17` | Nền màn hình chính |
| `noc-surface` | `#121826` | Nền card, panel, bảng |
| `noc-border` | `#1e293b` | Đường viền phân cách |
| `noc-critical` | `#ef4444` | Cảnh báo CRITICAL (Severity 0–2) |
| `noc-major` | `#f97316` | Cảnh báo MAJOR (Severity 3) |
| `noc-minor` | `#f59e0b` | Cảnh báo WARNING (Severity 4) |
| `noc-info` | `#06b6d4` | Thông tin INFO (Severity 5–6) |

**Quy tắc hiển thị mức độ cảnh báo:**

| Severity | Tên hiển thị | Màu sắc |
|---|---|---|
| `CRITICAL` | 🔴 Critical | Đỏ — `noc-critical` |
| `MAJOR` | 🟠 Major | Cam — `noc-major` |
| `WARNING` | 🟡 Warning | Vàng — `noc-minor` |
| `INFO` | 🔵 Info | Cyan — `noc-info` |

---

## Hợp đồng dữ liệu AlertEvent

Schema `AlertEvent` tuân thủ **đề xuất v0.9** tại `n42-ai-kit/docs/INTERFACES.md` (chờ TL chốt v1.0 trước W4), được khai báo tại [`src/types/alert.ts`](./src/types/alert.ts).  
Mọi component, mock data và API call đều bám sát theo schema chuẩn này:

```typescript
interface AlertEvent {
  id: string;               // UUID định danh duy nhất
  received_at: string;      // ISO 8601 UTC — thời điểm hệ thống tiếp nhận
  event_timestamp: string;  // ISO 8601 UTC — thời điểm sự kiện ghi nhận từ thiết bị
  source_ip: string;        // IP nguồn — RFC 1918 hoặc TEST-NET-3 (RFC 5737)
  hostname: string;         // Tên thiết bị viễn thông (Router, Switch, Firewall)
  facility: number;         // Syslog facility (0–23)
  severity: number;         // RFC 5424 (0–7): 0 Emergency → 7 Debug (Quyết định D-01)
  program: string;          // Tiến trình ghi log (BGP, IFPDT, ddos-guard...)
  message: string;          // Nội dung sự kiện đã chuẩn hóa
  raw_payload: string;      // Nội dung gói tin log thô từ Syslog
  vendor: string;           // CISCO | HUAWEI | LINUX | RFC3164 | RFC5424 | UNKNOWN
  category: string;         // Phân loại sự kiện chuẩn hóa
}
```

> **Lưu ý quan trọng (D-01, D-02):** Thang `severity` trong DB là số nguyên `0–7` (RFC 5424). Tên CRITICAL/MAJOR/WARNING... được FE ánh xạ bằng helper function `SEVERITY_LABEL` và `SEVERITY_COLOR_GROUP` để hiển thị trực quan. Sau khi TL chốt v1.0, mọi thay đổi trường sẽ cập nhật đồng bộ qua skill `change-alertevent-schema`.

---

## Tích hợp API Backend

Mọi request HTTP đi qua tầng service tại [`src/services/alertService.ts`](./src/services/alertService.ts).  
**Tuyệt đối không gọi API trực tiếp từ component.**

| Endpoint | Phương thức | Hàm Service | Màn hình dùng |
|---|---|---|---|
| `/api/health` | `GET` | `alertService.getHealth()` | Header (kiểm tra kết nối) |
| `/api/events?limit=N` | `GET` | `alertService.getEvents(limit)` | Màn hình (1) Dòng thời gian |
| `/api/events/count` | `GET` | `alertService.getEventsCount()` | KPI tổng số sự kiện |
| `/api/ingest` | `POST` | `alertService.ingestEvent(payload)` | Nhận sự kiện thủ công |
| `/api/simulate?count=N` | `POST` | `alertService.simulateEvents(count)` | Giả lập dữ liệu kiểm thử |

> API tìm kiếm/lọc đầy đủ (theo thời gian, thiết bị, severity, phân trang) dự kiến mở tại **W7–W8** (BE2). Không tự bổ sung endpoint ngoài danh sách trên — mọi đề xuất bổ sung phải qua họp kỹ thuật với TL và BE2.

**Chế độ Mock Development (W2–W4):**
- Dự án sử dụng cấu hình `.env.development` với biến `VITE_USE_MOCK=true`.
- Khi bật chế độ mock, `alertService` trả trực tiếp dữ liệu giả lập từ `mockData.ts` mà không thực hiện request HTTP thật, triệt tiêu 100% các lỗi 404/ERR_CONNECTION_REFUSED trên Browser Console (đáp ứng đúng DoD của N42-19).
- Khi Backend chạy thật (W5+), chỉ cần đổi `VITE_USE_MOCK=false` và trỏ `VITE_API_BASE_URL`.

---

## Mock Data (W2–W4)

Trong giai đoạn W2–W4, khi Backend chưa cung cấp đầy đủ API, `alertService` hoạt động với dữ liệu giả lập tại [`src/services/mockData.ts`](./src/services/mockData.ts).

**Quy tắc bắt buộc khi chỉnh sửa mock data (D-09):**
- Phân biệt rõ dải IP: `10.x.x.x` và `192.168.x.x` là dải private **RFC 1918**; `203.0.113.0/24` là **TEST-NET-3 (RFC 5737)** dùng trong tài liệu/log minh họa.
- Phải khớp đầy đủ trường của `AlertEvent` v0.9 — không được thiếu hoặc thêm trường ngoài hợp đồng.
- Không dùng IP, hostname, thiết bị thật của hạ tầng VNPT NET.
- Không hardcode credential, API key hoặc token vào bất kỳ file nào trong `src/`.

---

## Quy chuẩn an toàn thông tin

Tuân thủ 100% theo `CONTRIBUTING.md` và chính sách bảo mật dự án N4.2:

- **Không commit** file `.env`, `.env.local`, token, secret key, mật khẩu vào Git.
- **Không nhúng** thông tin thiết bị sản xuất, log thật, địa chỉ IP thật của VNPT NET vào source code.
- **Không push thẳng** lên nhánh `main` — mọi thay đổi phải qua Pull Request với ít nhất **1 phê duyệt** từ Team Leader.
- Toàn bộ dữ liệu hiển thị trong giai đoạn phát triển phải là **giả lập**.

---

## Khắc phục sự cố thường gặp

**`npm run dev` báo lỗi port đã bị chiếm:**
```bash
npm run dev -- --port 5174
```

**Tailwind classes không áp dụng (UI trắng bóc):**  
Kiểm tra lại 2 điểm:
1. File `src/index.css` có 3 dòng `@tailwind base/components/utilities` ở **đầu file**.
2. `tailwind.config.js` có đúng đường dẫn `content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}']`.

**Backend không kết nối được (Header hiển thị MOCK/STANDBY):**  
Đây là trạng thái bình thường trong giai đoạn W2–W4. Giao diện tự dùng mock data, không cần can thiệp.

**`npm run build` báo lỗi TypeScript:**  
Chạy riêng để xem chi tiết:
```bash
cd frontend
npx tsc -b --noEmit
```

**Lỗi `import type` khi build:**  
Dự án dùng `verbatimModuleSyntax`. Mọi import chỉ dùng kiểu TypeScript phải dùng `import type { ... }`.
