import React, { useEffect, useState } from 'react';
import { Activity, ShieldCheck, Wifi, Globe } from 'lucide-react';
import { alertService } from '../../services';

export const Header: React.FC = () => {
  const [timeIct, setTimeIct] = useState<string>('');
  const [timeUtc, setTimeUtc] = useState<string>('');
  const [backendStatus, setBackendStatus] = useState<'UP' | 'DOWN' | 'MOCK' | 'CHECKING'>('CHECKING');

  useEffect(() => {
    const updateClocks = () => {
      const now = new Date();
      setTimeIct(now.toLocaleTimeString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' }));
      setTimeUtc(now.toLocaleTimeString('en-GB', { timeZone: 'UTC' }));
    };

    updateClocks();
    const timer = setInterval(updateClocks, 1000);

    let ignore = false;
    alertService
      .getHealth()
      .then((res) => {
        if (!ignore) {
          if (res.status === 'UP') setBackendStatus('UP');
          else if (res.status === 'MOCK') setBackendStatus('MOCK');
          else setBackendStatus('DOWN');
        }
      })
      .catch(() => {
        if (!ignore) setBackendStatus('DOWN');
      });

    return () => {
      ignore = true;
      clearInterval(timer);
    };
  }, []);

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/90 backdrop-blur px-6 flex items-center justify-between text-slate-100">
      <div className="flex items-center space-x-3">
        <div className="p-2 bg-cyan-500/10 rounded-lg text-cyan-400">
          <Activity className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="font-bold text-sm tracking-wide text-white uppercase">
              N4.2 — NOC VNPT NET × UTH
            </h1>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
              Baseline 03/11/2026
            </span>
          </div>
          <p className="text-xs text-slate-400">Hệ thống Thu thập & Phân tích Cảnh báo Viễn thông (Module M7)</p>
        </div>
      </div>

      <div className="flex items-center space-x-6 text-xs">
        {/* Kết nối Backend API theo Baseline */}
        <div className="flex items-center space-x-2">
          <Wifi className="w-4 h-4 text-slate-400" />
          <span className="text-slate-400">Backend Liveness:</span>
          <span
            className={`font-mono font-medium px-2 py-0.5 rounded text-[11px] ${
              backendStatus === 'UP'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : backendStatus === 'MOCK'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
            }`}
          >
            {backendStatus === 'UP' ? 'ONLINE (GET /api/health)' : backendStatus === 'MOCK' ? 'DEV MOCK (W2–W4)' : 'STANDBY'}
          </span>
        </div>

        {/* Khung múi giờ hiển thị minh bạch theo ARCHITECTURE_DESIGN Mục 5 */}
        <div className="flex items-center space-x-4 border-l border-slate-800 pl-6">
          <div className="flex items-center space-x-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span className="text-slate-400">ICT (UTC+7):</span>
            <span className="font-mono text-cyan-300">{timeIct || '--:--:--'}</span>
          </div>
          <div className="flex items-center space-x-1.5 text-slate-500">
            <Globe className="w-3.5 h-3.5" />
            <span>UTC:</span>
            <span className="font-mono text-slate-400">{timeUtc || '--:--:--'}</span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
