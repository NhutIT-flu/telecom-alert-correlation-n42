import type { AlertEvent } from '../types';
import { FIXTURE_EVENTS_V1, FIXTURE_EVENTS_EMPTY } from '../fixtures';

export type FixtureMode = 'success' | 'empty' | 'error';

export interface FixtureAdapterOptions {
  mode?: FixtureMode;
  delayMs?: number;
}

export interface KpiSummary {
  totalEvents: number;
  /** null = không có nguồn dữ liệu thực, hiển thị "—" trên UI */
  openIncidents: number | null;
  /** null = không có nguồn dữ liệu thực, hiển thị "—" trên UI */
  ingestRate: number | null;
  systemStatus: 'HEALTHY' | 'DEGRADED' | 'STANDBY';
}

export const fixtureAdapter = {
  /**
   * Tải sự kiện từ Fixture với độ trễ và chế độ mô phỏng
   */
  async getEvents(options: FixtureAdapterOptions = {}): Promise<AlertEvent[]> {
    const { mode = 'success', delayMs = 400 } = options;

    if (delayMs > 0) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }

    if (mode === 'error') {
      throw new Error('Mô phỏng lỗi kết nối: Không thể nạp tệp dữ liệu fixture.');
    }

    if (mode === 'empty') {
      return [...FIXTURE_EVENTS_EMPTY];
    }

    return [...FIXTURE_EVENTS_V1];
  },

  /**
   * Tính toán 4 thẻ KPI theo chuẩn TC-UI-001.
   *
   * - openIncidents: null vì fixture không cung cấp trạng thái tương quan thực — hiển thị "—".
   * - ingestRate:    null vì fixture không đo tốc độ ghi theo thời gian thực — hiển thị "—".
   * - Chỉ totalEvents và systemStatus có nguồn dữ liệu xác định từ fixture.
   */
  calculateKpis(events: AlertEvent[], isHealthy: boolean = true): KpiSummary {
    return {
      totalEvents: events.length,
      openIncidents: null,
      ingestRate: null,
      systemStatus: isHealthy ? 'HEALTHY' : 'DEGRADED',
    };
  },
};

export default fixtureAdapter;
