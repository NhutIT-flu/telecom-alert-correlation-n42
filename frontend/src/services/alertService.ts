import { apiClient } from './api';
import type { AlertEvent, ApiHealthResponse, AlertCountResponse } from '../types';
import { MOCK_ALERT_EVENTS } from './mockData';

/**
 * Điều khiển chế độ dữ liệu Frontend:
 * - Khi VITE_USE_MOCK=true (W2–W4): Hoạt động trên dữ liệu giả lập chuẩn, không gửi HTTP thừa
 * - Khi VITE_USE_MOCK=false (W5+): Kết nối trực tiếp Backend FastAPI (Base URL: /api)
 *
 * Tham chiếu Baseline 03/11/2026 (docs/DATA_AND_API_DESIGN.md Mục 4):
 *  - Hiện tại nhánh W1 chỉ có duy nhất: GET /api/health
 *  - Các endpoint ingest/query/simulate là target đề xuất cho các ticket tiếp theo.
 */
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

export const alertService = {
  /**
   * Kiểm tra tình trạng liveness của Backend (GET /api/health)
   * Endpoint thực tế duy nhất có trên Baseline W1
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
   * Lấy danh sách sự kiện cảnh báo
   * W2–W4 (VITE_USE_MOCK=true): Trả về mock data bám sát AlertEvent v0.9
   * W5+ (VITE_USE_MOCK=false): Đấu nối API truy vấn sau khi BE2 bàn giao OpenAPI
   */
  async getEvents(limit: number = 50): Promise<AlertEvent[]> {
    if (USE_MOCK) {
      return MOCK_ALERT_EVENTS.slice(0, limit);
    }
    try {
      const response = await apiClient.get<AlertEvent[]>(`/events?limit=${limit}`);
      return response.data;
    } catch {
      return MOCK_ALERT_EVENTS.slice(0, limit);
    }
  },

  /**
   * Đếm tổng số sự kiện trong buffer/CSDL
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
   * Đẩy sự kiện cảnh báo (target API)
   */
  async ingestEvent(payload: Partial<AlertEvent>): Promise<void> {
    if (USE_MOCK) return;
    await apiClient.post('/ingest', payload);
  },

  /**
   * Kích hoạt giả lập dữ liệu kiểm thử (target API)
   */
  async simulateEvents(count: number = 10): Promise<{ message: string; count: number }> {
    if (USE_MOCK) {
      return { message: 'Mock simulate OK (W2–W4)', count };
    }
    const response = await apiClient.post<{ message: string; count: number }>(`/simulate?count=${count}`);
    return response.data;
  },
};

export default alertService;
