import React from 'react';
import { FileSpreadsheet, Download, FileText, ShieldAlert } from 'lucide-react';

export const ReportsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <FileSpreadsheet className="w-5 h-5 text-cyan-400" />
          <span>Xuất báo cáo tổng hợp (Reporting & Export)</span>
        </h2>
        <p className="text-sm text-slate-400">
          Màn hình số (6) — Tiêu chí AC-04, FR-14 và TC-EXP-001 (Baseline 03/11/2026)
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center space-x-3 text-white font-semibold">
            <FileSpreadsheet className="w-6 h-6 text-emerald-400" />
            <div>
              <div className="text-sm">Báo cáo sự kiện cảnh báo (CSV Canonical)</div>
              <div className="text-xs text-slate-400 font-normal">
                Xuất AlertEvents tuân thủ bộ lọc hiện hành, xử lý escape delimiter và giới hạn bản ghi (TC-EXP-001)
              </div>
            </div>
          </div>
          <button className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 rounded-lg bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-600/30 text-sm font-medium transition">
            <Download className="w-4 h-4" />
            <span>Tải xuống CSV (Mock)</span>
          </button>
        </div>

        <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center space-x-3 text-white font-semibold">
            <FileText className="w-6 h-6 text-red-400" />
            <div>
              <div className="text-sm">Báo cáo tóm tắt sự cố & Tỷ lệ giảm nhiễu (PDF)</div>
              <div className="text-xs text-slate-400 font-normal">
                Báo cáo Incident, tỷ lệ giảm nhiễu (mục tiêu ≥70% theo AC-06) phục vụ nghiệm thu W13
              </div>
            </div>
          </div>
          <button className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 rounded-lg bg-red-600/20 text-red-400 border border-red-500/30 hover:bg-red-600/30 text-sm font-medium transition">
            <Download className="w-4 h-4" />
            <span>Tải xuống PDF (Mock)</span>
          </button>
        </div>
      </div>

      <div className="p-4 rounded-lg bg-slate-900/50 border border-slate-800 flex items-start space-x-3 text-xs text-slate-400">
        <ShieldAlert className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div>
          <span className="text-slate-300 font-semibold">Tuân thủ an toàn xuất dữ liệu (TC-SEC-005 & TC-EXP-001):</span> Toàn bộ trường văn bản khi xuất ra định dạng bảng tính đều được escape ký tự đặc biệt (dấu phẩy, dấu nháy, ký tự điều khiển) và chỉ chứa dữ liệu mạng lab giả lập RFC 1918 (10.10.0.0/16).
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
