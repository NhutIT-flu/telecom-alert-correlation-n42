import React from 'react';
import { Server, CheckCircle2, ShieldAlert } from 'lucide-react';

export const DeviceDetailPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <Server className="w-5 h-5 text-cyan-400" />
          <span>Chi tiết & Tra cứu theo thiết bị</span>
        </h2>
        <p className="text-sm text-slate-400">
          Tra cứu thông tin router, switch, firewall và lịch sử cảnh báo theo thiết bị
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {['R1-CORE-HN (Router)', 'SW-DIST-01 (Switch)', 'FW-PERIMETER-01 (Firewall)'].map((device, idx) => (
          <div key={idx} className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-white">{device}</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            </div>
            <p className="text-xs text-slate-400">Trạng thái: Đang hoạt động bình thường</p>
            <div className="pt-2 border-t border-slate-800 flex justify-between text-xs text-slate-500">
              <span>Đang giám sát</span>
              <span className="text-cyan-400">RFC 5737 IP</span>
            </div>
          </div>
        ))}
      </div>

      <div className="p-8 rounded-xl bg-slate-900 border border-slate-800 text-center text-slate-400 text-sm">
        <ShieldAlert className="w-8 h-8 text-slate-600 mx-auto mb-2" />
        Chức năng tra cứu chi tiết lịch sử đang được phát triển.
      </div>
    </div>
  );
};

export default DeviceDetailPage;
