import type { AlertEvent, FilterCriteria, FilterValidationResult, TimePreset } from '../types';

/**
 * Filter Engine Core cho Module M7 (Dashboard)
 * Thực thi các yêu cầu nghiệp vụ theo Thẻ N42-28:
 * - AC 1: Lọc kết hợp đa tiêu chí (Thời gian, Hostname, Vendor, Severity, Từ khóa)
 * - AC 2: Bắt lỗi thời gian đảo (startTime > endTime)
 * - AC 4: Hỗ trợ cấu trúc tham số chuẩn để reset con trỏ phân trang
 * - TC-UI-002: Lọc theo Mức độ nghiêm trọng (Severity)
 */
export const filterService = {
  /**
   * Kiểm tra tính hợp lệ của tiêu chí lọc (Validation)
   * Bắt lỗi thời gian đảo theo tiêu chuẩn AC 2
   */
  validateCriteria(criteria: FilterCriteria): FilterValidationResult {
    const { startTime, endTime } = criteria;

    if (startTime && endTime) {
      const start = new Date(startTime).getTime();
      const end = new Date(endTime).getTime();

      if (isNaN(start) || isNaN(end)) {
        return {
          isValid: false,
          errorMessage: 'Định dạng mốc thời gian không hợp lệ.',
        };
      }

      if (start > end) {
        return {
          isValid: false,
          errorMessage: 'Khoảng thời gian không hợp lệ: Thời gian bắt đầu không được lớn hơn thời gian kết thúc (thời gian đảo).',
        };
      }
    }

    return { isValid: true };
  },

  /**
   * Thuật toán lọc sự kiện thuần khiết (Pure function)
   * Không làm thay đổi mảng gốc, kết quả được sắp xếp theo event_timestamp mới nhất lên đầu
   */
  applyFilters(events: AlertEvent[], criteria: FilterCriteria): AlertEvent[] {
    // Nếu tiêu chí thời gian không hợp lệ, trả về mảng rỗng
    const validation = this.validateCriteria(criteria);
    if (!validation.isValid) {
      return [];
    }

    return events
      .filter((evt) => {
        const evtTime = new Date(evt.event_timestamp).getTime();

        // 1. Lọc theo thời gian bắt đầu (startTime)
        if (criteria.startTime) {
          const start = new Date(criteria.startTime).getTime();
          if (evtTime < start) return false;
        }

        // 2. Lọc theo thời gian kết thúc (endTime)
        if (criteria.endTime) {
          const end = new Date(criteria.endTime).getTime();
          if (evtTime > end) return false;
        }

        // 3. Lọc theo Hostname / Thiết bị (Không phân biệt hoa thường)
        if (criteria.hostname && criteria.hostname.trim() !== '') {
          const query = criteria.hostname.trim().toLowerCase();
          if (!evt.hostname.toLowerCase().includes(query)) {
            return false;
          }
        }

        // 4. Lọc theo Hãng / Vendor (So sánh chính xác)
        if (criteria.vendor && criteria.vendor.trim() !== '' && criteria.vendor !== 'ALL') {
          if (evt.vendor.toUpperCase() !== criteria.vendor.trim().toUpperCase()) {
            return false;
          }
        }

        // 5. Lọc theo Mức độ nghiêm trọng / Severity (TC-UI-002, RFC 5424)
        if (criteria.severity && criteria.severity.length > 0) {
          if (!criteria.severity.includes(evt.severity)) {
            return false;
          }
        }

        // 6. Lọc theo từ khóa tìm kiếm (Full-text trong message, program, source_ip)
        if (criteria.searchQuery && criteria.searchQuery.trim() !== '') {
          const keyword = criteria.searchQuery.trim().toLowerCase();
          const matchMessage = evt.message.toLowerCase().includes(keyword);
          const matchProgram = evt.program.toLowerCase().includes(keyword);
          const matchSource = evt.source_ip.toLowerCase().includes(keyword);
          const matchRaw = evt.raw_payload.toLowerCase().includes(keyword);

          if (!matchMessage && !matchProgram && !matchSource && !matchRaw) {
            return false;
          }
        }

        return true;
      })
      .sort(
        (a, b) => new Date(b.event_timestamp).getTime() - new Date(a.event_timestamp).getTime()
      );
  },

  /**
   * Tính toán dải thời gian theo các Preset chọn nhanh (15m, 1h, 6h, 24h, 7d)
   */
  getTimePresetRange(preset: TimePreset, referenceDate: Date = new Date()): { startTime: string; endTime: string } {
    if (preset === 'all') {
      return { startTime: '', endTime: '' };
    }

    const end = new Date(referenceDate);
    const start = new Date(referenceDate);

    switch (preset) {
      case '15m':
        start.setMinutes(start.getMinutes() - 15);
        break;
      case '1h':
        start.setHours(start.getHours() - 1);
        break;
      case '6h':
        start.setHours(start.getHours() - 6);
        break;
      case '24h':
        start.setHours(start.getHours() - 24);
        break;
      case '7d':
        start.setDate(start.getDate() - 7);
        break;
    }

    return {
      startTime: start.toISOString(),
      endTime: end.toISOString(),
    };
  },
};

export default filterService;
