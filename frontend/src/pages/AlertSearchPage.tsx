import React from 'react';
import { Filter, Search } from 'lucide-react';

export const AlertSearchPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <Filter className="w-5 h-5 text-cyan-400" />
          <span>Bộ lọc & Tra cứu cảnh báo đa chiều (Event Explorer)</span>
        </h2>
        <p className="text-sm text-slate-400">
          Màn hình số (3) — Tham số lọc theo Baseline 03/11/2026 (DATA_AND_API_DESIGN Mục 5.2)
        </p>
      </div>

      <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Thiết bị (Hostname)</label>
            <input
              type="text"
              placeholder="VD: R1-CORE, SW-01..."
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Vendor</label>
            <select className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500">
              <option value="">Tất cả Vendor</option>
              <option value="CISCO">CISCO</option>
              <option value="HUAWEI">HUAWEI</option>
              <option value="LINUX">LINUX</option>
              <option value="RFC5424">RFC5424</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Mức độ (RFC 5424)</label>
            <select className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500">
              <option value="">Tất cả (0–7)</option>
              <option value="0,1,2">0–2: Emergency / Alert / Critical</option>
              <option value="3">3: Error</option>
              <option value="4">4: Warning</option>
              <option value="5,6">5–6: Notice / Info</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">IP Nguồn (Lab 10.10.x)</label>
            <input
              type="text"
              placeholder="10.10.x.x"
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
