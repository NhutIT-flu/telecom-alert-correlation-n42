import type { AlertEvent } from '../types';

/**
 * Dữ liệu giả lập (Mock Data) chuẩn theo schema AlertEvent v0.9
 * Nguồn tham chiếu: n42-ai-kit/docs/INTERFACES.md
 *
 * Quy tắc IP (D-09):
 *  - 10.x.x.x / 192.168.x.x  → dải private RFC 1918 (mạng nội bộ lab)
 *  - 203.0.113.x              → TEST-NET-3 (RFC 5737) dùng trong tài liệu minh họa
 * Không dùng IP public thật của VNPT NET.
 */
export const MOCK_ALERT_EVENTS: AlertEvent[] = [
  {
    id: 'a1b2c3d4-0001-0000-0000-000000000001',
    received_at: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
    event_timestamp: new Date(Date.now() - 1000 * 60 * 2 - 200).toISOString(),
    source_ip: '10.100.1.1',          // RFC 1918 — core router lab
    hostname: 'R1-CORE-HN',
    facility: 23,
    severity: 2,                      // Critical (đỏ)
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
    source_ip: '192.168.10.1',        // RFC 1918 — firewall quản trị lab
    hostname: 'FW-PERIMETER-01',
    facility: 4,
    severity: 3,                      // Error → Major (cam)
    program: 'ddos-guard',
    message: 'Phát hiện SYN Flood lưu lượng lớn vào cổng 443 từ 203.0.113.99 (TEST-NET-3)',
    raw_payload: '<11>1 2026-11-08T12:40:00Z FW-PERIMETER-01 ddos-guard - - SYN Flood detected from 203.0.113.99',
    vendor: 'RFC5424',
    category: 'security',
  },
  {
    id: 'a1b2c3d4-0003-0000-0000-000000000003',
    received_at: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
    event_timestamp: new Date(Date.now() - 1000 * 60 * 12 - 500).toISOString(),
    source_ip: '10.200.2.10',         // RFC 1918 — distribution switch lab
    hostname: 'SW-DIST-01',
    facility: 23,
    severity: 4,                      // Warning (vàng)
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
    source_ip: '10.100.2.1',          // RFC 1918 — PE router lab HCM
    hostname: 'R2-PE-HCM',
    facility: 23,
    severity: 5,                      // Notice → Info (cyan)
    program: 'SYS',
    message: 'Quản trị viên vnp_admin cập nhật cấu hình thiết bị qua console',
    raw_payload: '%SYS-5-CONFIG_I: Configured from console by vnp_admin on vty0 (192.168.1.50)',
    vendor: 'CISCO',
    category: 'config-change',
  },
  {
    id: 'a1b2c3d4-0005-0000-0000-000000000005',
    received_at: new Date(Date.now() - 1000 * 60 * 40).toISOString(),
    event_timestamp: new Date(Date.now() - 1000 * 60 * 40 - 100).toISOString(),
    source_ip: '10.200.5.8',          // RFC 1918 — access switch lab
    hostname: 'SW-ACCESS-08',
    facility: 23,
    severity: 1,                      // Alert → Critical (đỏ)
    program: 'STP',
    message: 'Root Bridge thay đổi đột ngột trên VLAN 100 — nguy cơ loop mạng',
    raw_payload: '<2>Nov  8 12:05:00 SW-ACCESS-08 STP: Root bridge changed on VLAN 100',
    vendor: 'RFC3164',
    category: 'stp',
  },
];
