/**
 * DỰ ÁN N4.2 — HỆ THỐNG PHÂN TÍCH CẢNH BÁO VIỄN THÔNG
 *
 * Schema AlertEvent theo INTERFACES.md v0.9 (đề xuất, chờ TL chốt v1.0 trước W4)
 * Nguồn tham chiếu: n42-ai-kit/docs/INTERFACES.md
 * Quyết định liên quan: D-01, D-02, D-09 trong n42-ai-kit/docs/DECISIONS.md
 *
 * ⚠️  KHÔNG tự sửa trường nào ở đây mà không có TL phê duyệt.
 *     Mọi thay đổi schema: dùng skill change-alertevent-schema + cập nhật DDL cùng lúc.
 */

/**
 * Mức severity theo RFC 5424 (D-01)
 * FE tự ánh xạ số → nhãn hiển thị, không lưu chuỗi "CRITICAL"/"MAJOR" vào DB
 */
export type SeverityLevel = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7;

/** Ánh xạ số severity → nhãn hiển thị cho NOC Dashboard */
export const SEVERITY_LABEL: Record<number, string> = {
  0: 'Emergency',
  1: 'Alert',
  2: 'Critical',
  3: 'Error',
  4: 'Warning',
  5: 'Notice',
  6: 'Info',
  7: 'Debug',
};

/** Ánh xạ số severity → nhóm màu NOC */
export const SEVERITY_COLOR_GROUP = (severity: number): 'critical' | 'major' | 'warning' | 'info' | 'debug' => {
  if (severity <= 2) return 'critical'; // Emergency, Alert, Critical → đỏ
  if (severity === 3) return 'major';   // Error → cam
  if (severity === 4) return 'warning'; // Warning → vàng
  if (severity <= 6) return 'info';     // Notice, Info → cyan
  return 'debug';                       // Debug → xám
};

/**
 * AlertEvent — hợp đồng dữ liệu chuẩn v0.9
 * Khớp 1-1 với Pydantic model trong INTERFACES.md và DDL TimescaleDB
 */
export interface AlertEvent {
  id: string;               // UUID
  received_at: string;      // ISO 8601 UTC — thời điểm hệ thống tiếp nhận
  event_timestamp: string;  // ISO 8601 UTC — thời điểm sự kiện ghi nhận từ thiết bị
  source_ip: string;        // IP nguồn — dải private RFC1918 hoặc TEST-NET 203.0.113.0/24
  hostname: string;         // Tên thiết bị (router/switch/firewall)
  facility: number;         // Syslog facility 0–23
  severity: number;         // RFC 5424: 0 (Emergency) → 7 (Debug)
  program: string;          // Tiến trình/process ghi log
  message: string;          // Nội dung đã chuẩn hóa
  raw_payload: string;      // Nội dung log thô nhận từ Syslog
  vendor: string;           // CISCO | HUAWEI | LINUX | RFC3164 | RFC5424 | UNKNOWN
  category: string;         // Phân loại do BE2 gán khi chuẩn hóa
}

/** Trạng thái sức khỏe Backend (GET /api/health) */
export interface ApiHealthResponse {
  status: 'UP' | 'DOWN' | 'MOCK' | string;
  service: string;
  version: string;
}

/** Phản hồi đếm sự kiện (GET /api/events/count) */
export interface AlertCountResponse {
  count: number;
}
