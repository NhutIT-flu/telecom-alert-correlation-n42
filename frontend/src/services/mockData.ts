import type { AlertEvent } from '../types';

/**
 * Dữ liệu giả lập (Mock Data) chuẩn theo Baseline 03/11/2026:
 * - Tham chiếu: docs/ACCEPTANCE_CRITERIA.md (Mục 3), docs/TECHNICAL_DESIGN_DOCUMENT.md (Mục 6)
 * - Dải IP mạng lab riêng (RFC 1918): 10.10.0.0/16 (ví dụ: 10.10.1.x, 10.10.2.x)
 * - Dải IP tài liệu minh họa TEST-NET-3 (RFC 5737): 203.0.113.0/24
 * - Tuyệt đối không dùng IP thiết bị thật hoặc cấu hình sản xuất của VNPT NET.
 * - Schema bám sát mô hình AlertEvent v0.9 (n42-ai-kit/docs/INTERFACES.md).
 */
export const MOCK_ALERT_EVENTS: AlertEvent[] = [
  {
    id: 'a1b2c3d4-0001-0000-0000-000000000001',
    received_at: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
    event_timestamp: new Date(Date.now() - 1000 * 60 * 2 - 200).toISOString(),
    source_ip: '10.10.1.1',           // Baseline: Mạng lab riêng 10.10.0.0/16 (Core Router)
    hostname: 'R1-CORE-HN',
    facility: 23,
    severity: 2,                      // Critical (RFC 5424 D-01)
    program: 'BGP',
    message: 'BGP session ngắt kết nối với láng giềng 203.0.113.5 (TEST-NET-3)',
    raw_payload: '%BGP-3-BGP_NEIGHBOR_DOWN: Neighbor 203.0.113.5 Down: Peer closed session',
    vendor: 'CISCO',
    category: 'routing',
  },
  {
    id: 'a1b2c3d4-0002-0000-0000-000000000002',
    received_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    event_timestamp: new Date(Date.now() - 1000 * 60 * 5 - 150).toISOString(),
    source_ip: '10.10.10.1',          // Baseline: Mạng lab riêng 10.10.0.0/16 (Firewall)
    hostname: 'FW-PERIMETER-01',
    facility: 4,
    severity: 3,                      // Error (RFC 5424)
    program: 'ddos-guard',
    message: 'Phát hiện SYN Flood lưu lượng lớn vào cổng 443 từ 203.0.113.99 (TEST-NET-3)',
    raw_payload: '<11>1 2026-11-09T03:40:00Z FW-PERIMETER-01 ddos-guard - - SYN Flood detected from 203.0.113.99',
    vendor: 'RFC5424',
    category: 'security',
  },
  {
    id: 'a1b2c3d4-0003-0000-0000-000000000003',
    received_at: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
    event_timestamp: new Date(Date.now() - 1000 * 60 * 12 - 500).toISOString(),
    source_ip: '10.10.2.10',          // Baseline: Mạng lab riêng 10.10.0.0/16 (Distribution Switch)
    hostname: 'SW-DIST-01',
    facility: 23,
    severity: 4,                      // Warning (RFC 5424)
    program: 'IFPDT',
    message: 'Cổng GigabitEthernet0/0/12 tự phục hồi từ trạng thái error-down',
    raw_payload: '%%01IFPDT/4/IF_ERR_RECOVERY(l): The interface GigabitEthernet0/0/12 recovered from error-down state.',
    vendor: 'HUAWEI',
    category: 'interface',
  },
  {
    id: 'a1b2c3d4-0004-0000-0000-000000000004',
    received_at: new Date(Date.now() - 1000 * 60 * 25).toISOString(),
    event_timestamp: new Date(Date.now() - 1000 * 60 * 25 - 300).toISOString(),
    source_ip: '10.10.1.2',           // Baseline: Mạng lab riêng 10.10.0.0/16 (PE Router)
    hostname: 'R2-PE-HCM',
    facility: 23,
    severity: 5,                      // Notice (RFC 5424)
    program: 'SYS',
    message: 'Quản trị viên vnp_admin cập nhật cấu hình thiết bị qua console',
    raw_payload: '%SYS-5-CONFIG_I: Configured from console by vnp_admin on vty0 (10.10.99.50)',
    vendor: 'CISCO',
    category: 'config-change',
  },
  {
    id: 'a1b2c3d4-0005-0000-0000-000000000005',
    received_at: new Date(Date.now() - 1000 * 60 * 40).toISOString(),
    event_timestamp: new Date(Date.now() - 1000 * 60 * 40 - 100).toISOString(),
    source_ip: '10.10.5.8',           // Baseline: Mạng lab riêng 10.10.0.0/16 (Access Switch)
    hostname: 'SW-ACCESS-08',
    facility: 23,
    severity: 1,                      // Alert (RFC 5424)
    program: 'STP',
    message: 'Root Bridge thay đổi đột ngột trên VLAN 100 — nguy cơ loop mạng',
    raw_payload: '<2>Nov  9 03:05:00 SW-ACCESS-08 STP: Root bridge changed on VLAN 100',
    vendor: 'RFC3164',
    category: 'stp',
  },
];
