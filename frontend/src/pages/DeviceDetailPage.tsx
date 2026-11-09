import React from 'react';
import { Server, CheckCircle2, ShieldAlert } from 'lucide-react';

export const DeviceDetailPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <Server className="w-5 h-5 text-cyan-400" />
          <span>Chi tiết & Tra cứu theo thiết bị (Hostname)</span>
        </h2>
        <p className="text-sm text-slate-400">
          Màn hình số (2) — Tra cứu topo router, switch, firewall trong dải lab 10.10.0.0/16 theo Baseline 03/11/2026
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { name: 'R1-CORE-HN', type: 'Router (Cisco)', ip: '10.10.1.1' },
          { name: 'SW-DIST-01', type: 'Switch (Huawei)', ip: '10.10.2.10' },
          { name: 'FW-PERIMETER-01', type: 'Firewall (RFC5424)', ip: '10.10.10.1' },
        ].map((device, idx) => (
          <div key={idx} className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-white">{device.name}</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-xs text-slate-400">Phân loại: {device.type}</p>
            <div className="pt-2 border-t border-slate-800 flex justify-between text-xs text-slate-500">
              <span>IP Quản trị:</span>
              <span className="text-cyan-400 font-mono">{device.ip}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="p-8 rounded-xl bg-slate-900 border border-slate-800 text-center text-slate-400 text-sm">
        <ShieldAlert className="w-8 h-8 text-slate-600 mx-auto mb-2" />
        Chức năng tra cứu chi tiết lịch sử thiết bị sẽ kết nối API truy vấn sau khi BE2 bàn giao OpenAPI tại W7–W8.
      </div>
    </div>
  );
};

export default DeviceDetailPage;
