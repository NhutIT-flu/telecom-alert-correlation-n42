import type { AlertEvent } from '../types';
import { FIXTURE_EVENTS_V1, FIXTURE_EVENTS_EMPTY } from '../fixtures';

export type FixtureMode = 'success' | 'empty' | 'error';

export interface FixtureAdapterOptions {
  mode?: FixtureMode;
  delayMs?: number;
}

export interface KpiSummary {
  totalEvents: number;
  openIncidents: number;
  ingestRate: number;
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
   * Chống nhân bản dòng (Deduplication theo id) khi retry - Tiêu chuẩn AC 2
   */
  mergeEvents(existing: AlertEvent[], incoming: AlertEvent[]): AlertEvent[] {
    const map = new Map<string, AlertEvent>();
    existing.forEach((e) => map.set(e.id, e));
    incoming.forEach((e) => map.set(e.id, e));

    return Array.from(map.values()).sort(
      (a, b) => new Date(b.event_timestamp).getTime() - new Date(a.event_timestamp).getTime()
    );
  },

  /**
   * Tính toán 4 thẻ KPI theo chuẩn TC-UI-001
   */
  calculateKpis(events: AlertEvent[], isHealthy: boolean = true): KpiSummary {
    const totalEvents = events.length;
    const hasCritical = events.some((e) => e.severity <= 2);
    const openIncidents = hasCritical ? 1 : 0;

    return {
      totalEvents,
      openIncidents,
      ingestRate: totalEvents > 0 ? 10 : 0,
      systemStatus: isHealthy ? 'HEALTHY' : 'DEGRADED',
    };
  },
};

export default fixtureAdapter;
