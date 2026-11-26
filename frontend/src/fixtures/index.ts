import type { AlertEvent } from '../types';
import eventsV1Data from './events-v1.json';
import eventsEmptyData from './events-empty.json';

/**
 * Danh mục Fixtures chuẩn hóa cho Module M7 (Dashboard)
 * Tuân thủ tiêu chuẩn AC 1 & AC 2 của thẻ N42-20
 */
export const FIXTURE_EVENTS_V1: AlertEvent[] = eventsV1Data as AlertEvent[];
export const FIXTURE_EVENTS_EMPTY: AlertEvent[] = eventsEmptyData as AlertEvent[];

export const FIXTURE_METADATA = {
  version: '1.0.0',
  schema: 'AlertEvent-v0.9',
  baselineDate: '03/11/2026',
  totalV1Records: FIXTURE_EVENTS_V1.length,
};
