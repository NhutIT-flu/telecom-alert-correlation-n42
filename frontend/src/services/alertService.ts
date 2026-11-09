import { apiClient } from './api';
import type { AlertEvent, ApiHealthResponse, AlertCountResponse } from '../types';
import { MOCK_ALERT_EVENTS } from './mockData';

/**
 * Chế độ Mock W2-W4: đọc từ biến môi trường VITE_USE_MOCK
 * - true  → trả dữ liệu giả lập trực tiếp, KHÔNG gọi HTTP (không có lỗi 404 Console)
 * - false → gọi API thật, fallback mock nếu lỗi (W5+ khi Backend khả dụng)
 */
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

/**
 * Service quản lý toàn bộ API tương tác với Backend cho Module M7
 * Tuân thủ đúng hợp đồng endpoint:
 *  - GET /api/health
 *  - GET /api/events?limit=
 *  - GET /api/events/count
 *  - POST /api/ingest
 *  - POST /api/simulate?count=
 */
export const alertService = {
  /**
   * Kiểm tra tình trạng kết nối của Backend
   */
  async getHealth(): Promise<ApiHealthResponse> {
    if (USE_MOCK) {
      return { status: 'MOCK', service: 'n42-api (dev mock W2-W4)', version: '0.1.0' };
    }
    try {
      const response = await apiClient.get<ApiHealthResponse>('/health');
      return response.data;
    } catch {
      return { status: 'DOWN', service: 'n42-api', version: '0.1.0' };
    }
  },

  /**
   * Lấy danh sách sự kiện cảnh báo mới nhất
   * W2-W4 (VITE_USE_MOCK=true): trả mock ngay, không gọi HTTP
   * W5+   (VITE_USE_MOCK=false): gọi API thật, fallback mock nếu lỗi mạng
   */
  async getEvents(limit: number = 50): Promise<AlertEvent[]> {
    if (USE_MOCK) {
      return MOCK_ALERT_EVENTS.slice(0, limit);
    }
    try {
      const response = await apiClient.get<AlertEvent[]>(`/events?limit=${limit}`);
      return response.data;
    } catch {
      console.warn('[alertService] Backend offline, fallback sang Mock Data');
      return MOCK_ALERT_EVENTS.slice(0, limit);
    }
  },

  /**
   * Đếm tổng số lượng sự kiện hiện có trong cơ sở dữ liệu
   */
  async getEventsCount(): Promise<number> {
    if (USE_MOCK) {
      return MOCK_ALERT_EVENTS.length;
    }
    try {
      const response = await apiClient.get<AlertCountResponse>('/events/count');
      return response.data.count;
    } catch {
      return MOCK_ALERT_EVENTS.length;
    }
  },

  /**
   * Đẩy sự kiện cảnh báo mới vào hệ thống (POST /api/ingest)
   */
  async ingestEvent(payload: Partial<AlertEvent>): Promise<void> {
    if (USE_MOCK) return;
    await apiClient.post('/ingest', payload);
  },

  /**
   * Yêu cầu Backend giả lập luồng log viễn thông (POST /api/simulate?count=)
   */
  async simulateEvents(count: number = 10): Promise<{ message: string; count: number }> {
    if (USE_MOCK) {
      return { message: 'Mock simulate OK', count };
    }
    const response = await apiClient.post<{ message: string; count: number }>(`/simulate?count=${count}`);
    return response.data;
  },
};

export default alertService;
