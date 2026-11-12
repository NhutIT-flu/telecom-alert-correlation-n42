import React from 'react';
import { Layers, GitMerge, AlertOctagon } from 'lucide-react';

export const CorrelationAlertsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <Layers className="w-5 h-5 text-cyan-400" />
          <span>Sự kiện gom nhóm & Cảnh báo từ luật tương quan (Incident Explorer)</span>
        </h2>
        <p className="text-sm text-slate-400">
          Màn hình số (5) — Kết quả phân tích gom nhóm từ Module M5/M6 theo Baseline 03/11/2026 (AC-05, AC-06)
        </p>
      </div>

      {/* Minh họa 1 sự cố tương quan gom nhóm (Mock Grouped Incident theo Baseline DATA_AND_API_DESIGN) */}
      <div className="p-5 rounded-xl bg-slate-900 border border-red-500/40 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-red-500/20 text-red-400 rounded-lg">
              <AlertOctagon className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-white text-base">INC-20261109-001: Link Flap Bão cảnh báo cổng</span>
                <span className="px-2 py-0.5 rounded text-xs font-semibold bg-red-500/20 text-red-300 border border-red-500/40">
                  CRITICAL
                </span>
                <span className="px-2 py-0.5 rounded text-xs font-mono bg-slate-800 text-cyan-300 border border-slate-700">
                  Luật: RULE_LINK_FLAP_01 (v1.0)
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Thiết bị: <b className="text-slate-200">SW-ACCESS-08</b> (10.10.5.8) | Cổng: GigabitEthernet0/0/24
              </p>
            </div>
          </div>
          <div className="text-right">
            <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-300 border border-amber-500/30">
              Trạng thái: OPEN
            </span>
            <div className="text-[11px] text-slate-500 mt-1">Cửa sổ trượt 60s (≥5 sự kiện)</div>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
          <div>
            <span className="text-slate-500 block">Sự kiện con đã gom (Noise reduction):</span>
            <span className="font-mono text-cyan-400 font-bold text-sm">7 sự kiện → 1 Incident</span>
          </div>
          <div>
            <span className="text-slate-500 block">Tỷ lệ giảm nhiễu (AC-06 target ≥70%):</span>
            <span className="font-mono text-emerald-400 font-bold text-sm">85.7%</span>
          </div>
          <div>
            <span className="text-slate-500 block">Xuất hiện lần đầu (First seen):</span>
            <span className="font-mono text-slate-300">03:04:12 UTC</span>
          </div>
          <div>
            <span className="text-slate-500 block">Gần nhất (Last seen):</span>
            <span className="font-mono text-slate-300">03:05:00 UTC</span>
          </div>
        </div>
      </div>

      <div className="p-8 rounded-xl bg-slate-900 border border-slate-800 text-center text-slate-400 space-y-2">
        <GitMerge className="w-8 h-8 text-cyan-500/60 mx-auto" />
        <h3 className="font-semibold text-white">Động cơ Tương quan (Module M6) do BE3 Nguyễn Duy Minh phụ trách</h3>
        <p className="text-xs text-slate-400 max-w-lg mx-auto">
          Tại mốc W9–W12, hệ thống sẽ mở WebSocket Stream để đẩy Incident mới trực tiếp lên UI (TC-UI-005).
        </p>
      </div>
    </div>
  );
};

export default CorrelationAlertsPage;
