import React from 'react';
import { Filter, Search } from 'lucide-react';

export const AlertSearchPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <Filter className="w-5 h-5 text-cyan-400" />
          <span>Bộ lọc & Tra cứu cảnh báo đa chiều</span>
        </h2>
        <p className="text-sm text-slate-400">
          Lọc theo khoảng thời gian, thiết bị, IP nguồn và mức độ nghiêm trọng
        </p>
      </div>

      <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Thiết bị</label>
            <input
              type="text"
              placeholder="VD: R1-CORE, SW-01..."
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Mức độ (Severity)</label>
            <select className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500">
              <option value="">Tất cả mức độ</option>
              <option value="CRITICAL">CRITICAL (Đỏ)</option>
              <option value="MAJOR">MAJOR (Cam)</option>
              <option value="WARNING">WARNING (Vàng)</option>
              <option value="INFO">INFO (Xanh)</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Từ ngày</label>
            <input
              type="date"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>
          <div className="flex items-end">
            <button className="w-full flex items-center justify-center space-x-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg px-4 py-2 text-sm font-medium transition">
              <Search className="w-4 h-4" />
              <span>Tìm kiếm</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlertSearchPage;
