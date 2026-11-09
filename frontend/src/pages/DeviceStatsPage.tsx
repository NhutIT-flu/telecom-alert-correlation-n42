import React from 'react';
import { BarChart3, PieChart, Activity } from 'lucide-react';

export const DeviceStatsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <BarChart3 className="w-5 h-5 text-cyan-400" />
          <span>Thống kê theo thiết bị & Phân loại viễn thông</span>
        </h2>
        <p className="text-sm text-slate-400">
          Phân tích mật độ sự kiện cảnh báo theo Router, Switch và Firewall
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center space-x-2 text-white font-semibold text-sm">
            <PieChart className="w-4 h-4 text-cyan-400" />
            <span>Phân bổ theo loại thiết bị</span>
          </div>
          <div className="space-y-3 pt-2 text-sm">
            <div>
              <div className="flex justify-between text-xs text-slate-400 mb-1">
                <span>Router (Cisco / Juniper)</span>
                <span className="font-mono text-cyan-400">45%</span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div className="bg-cyan-500 h-full w-[45%]" />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs text-slate-400 mb-1">
                <span>Switch (Huawei / Cisco)</span>
                <span className="font-mono text-cyan-400">35%</span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div className="bg-cyan-500 h-full w-[35%]" />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs text-slate-400 mb-1">
                <span>Firewall (Fortinet / Checkpoint)</span>
                <span className="font-mono text-cyan-400">20%</span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div className="bg-cyan-500 h-full w-[20%]" />
              </div>
            </div>
          </div>
        </div>

        <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 flex flex-col justify-center items-center text-center text-slate-400">
          <Activity className="w-10 h-10 text-slate-600 mb-3" />
          <p className="text-sm">Biểu đồ thống kê chuyên sâu (Recharts / Chart.js)</p>
          <p className="text-xs text-slate-500 mt-1">Sẽ hoàn thiện tại mốc W10–W13</p>
        </div>
      </div>
    </div>
  );
};

export default DeviceStatsPage;
