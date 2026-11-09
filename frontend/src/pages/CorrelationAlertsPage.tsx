import React from 'react';
import { Layers, GitMerge } from 'lucide-react';

export const CorrelationAlertsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <Layers className="w-5 h-5 text-cyan-400" />
          <span>Sự kiện gom nhóm & Cảnh báo từ luật tương quan</span>
        </h2>
        <p className="text-sm text-slate-400">
          Kết quả phân tích gom nhóm: (Root-cause analysis)
        </p>
      </div>

      <div className="p-8 rounded-xl bg-slate-900 border border-slate-800 text-center text-slate-400 space-y-3">
        <GitMerge className="w-10 h-10 text-cyan-500/60 mx-auto" />
        <h3 className="font-semibold text-white">Đang chờ tích hợp Engine(BE3)</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          Màn hình sẽ hiển thị các cụm cảnh báo (Incident Cluster) được suy luận từ chuỗi sự kiện Syslog
          theo thời gian và topo mạng.
        </p>
      </div>
    </div>
  );
};

export default CorrelationAlertsPage;
