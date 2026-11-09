import React from 'react';
import { FileSpreadsheet, Download, FileText } from 'lucide-react';

export const ReportsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <FileSpreadsheet className="w-5 h-5 text-cyan-400" />
          <span>Xuất báo cáo tổng hợp</span>
        </h2>
        <p className="text-sm text-slate-400">
          Xuất dữ liệu thống kê cảnh báo phục vụ báo cáo vận hành NOC VNPT NET
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center space-x-3 text-white font-semibold">
            <FileSpreadsheet className="w-6 h-6 text-emerald-400" />
            <div>
              <div className="text-sm">Báo cáo cảnh báo CSV</div>
              <div className="text-xs text-slate-400 font-normal">Xuất toàn bộ AlertEvents thô và phân tách</div>
            </div>
          </div>
          <button className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 rounded-lg bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-600/30 text-sm font-medium transition">
            <Download className="w-4 h-4" />
            <span>Tải xuống CSV</span>
          </button>
        </div>

        <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center space-x-3 text-white font-semibold">
            <FileText className="w-6 h-6 text-red-400" />
            <div>
              <div className="text-sm">Báo cáo tóm tắt sự cố PDF</div>
              <div className="text-xs text-slate-400 font-normal">Tóm tắt sự kiện gom nhóm và KPI sự cố</div>
            </div>
          </div>
          <button className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 rounded-lg bg-red-600/20 text-red-400 border border-red-500/30 hover:bg-red-600/30 text-sm font-medium transition">
            <Download className="w-4 h-4" />
            <span>Tải xuống PDF</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
