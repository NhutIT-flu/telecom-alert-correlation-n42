/**
 * DỰ ÁN N4.2 — HỆ THỐNG PHÂN TÍCH CẢNH BÁO VIỄN THÔNG (MODULE M7)
 * Khai báo kiểu dữ liệu bộ lọc cảnh báo đa tiêu chí theo Thẻ N42-28
 *
 * Truy vết: FR-07/11 · AC-03/04 · TC-UI-002/003 · DATA_AND_API_DESIGN Mục 5.2
 */

/**
 * Các khoảng thời gian chọn nhanh (Time Presets)
 */
export type TimePreset = 'all' | '15m' | '1h' | '6h' | '24h' | '7d';

/**
 * Tiêu chí lọc đa chiều trên giao diện Dashboard
 */
export interface FilterCriteria {
  startTime?: string;      // ISO 8601 UTC - Thời điểm bắt đầu
  endTime?: string;        // ISO 8601 UTC - Thời điểm kết thúc
  hostname?: string;       // Lọc theo tên thiết bị (ví dụ: R1-CORE, SW-DIST)
  vendor?: string;         // Lọc theo Vendor: CISCO | HUAWEI | LINUX | RFC5424 | RFC3164 | ALL
  severity?: number[];     // Lọc theo mảng Severity RFC 5424 (0: Emergency ... 7: Debug)
  searchQuery?: string;    // Từ khóa tìm kiếm trong thông điệp cảnh báo (message / program)
}

/**
 * Kết quả kiểm tra hợp lệ của bộ lọc (Validation Result)
 */
export interface FilterValidationResult {
  isValid: boolean;
  errorMessage?: string;
}

/**
 * Giá trị bộ lọc mặc định ban đầu
 */
export const DEFAULT_FILTER_CRITERIA: FilterCriteria = {
  startTime: '',
  endTime: '',
  hostname: '',
  vendor: '',
  severity: [],
  searchQuery: '',
};
