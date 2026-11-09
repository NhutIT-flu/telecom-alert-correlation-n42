import React, { useEffect, useState } from 'react';
import { Activity, ShieldCheck, Wifi } from 'lucide-react';
import { alertService } from '../../services';

export const Header: React.FC = () => {
  const [time, setTime] = useState<string>(new Date().toLocaleTimeString('vi-VN'));
  const [backendStatus, setBackendStatus] = useState<'UP' | 'DOWN' | 'MOCK' | 'CHECKING'>('CHECKING');

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString('vi-VN'));
    }, 1000);

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
          <h1 className="font-bold text-sm tracking-wide text-white uppercase">
            NOC VNPT NET
          </h1>
          <p className="text-xs text-slate-400">Hệ thống Thu thập & Phân tích Cảnh báo Viễn thông</p>
        </div>
      </div>

      <div className="flex items-center space-x-6 text-xs">
        <div className="flex items-center space-x-2">
          <Wifi className="w-4 h-4 text-slate-400" />
          <span className="text-slate-400">Backend API:</span>
          <span
            className={`font-mono font-medium px-2 py-0.5 rounded text-[11px] ${
              backendStatus === 'UP'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : backendStatus === 'MOCK'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
            }`}
          >
            {backendStatus === 'UP' ? 'ONLINE' : backendStatus === 'MOCK' ? 'MOCK' : 'STANDBY'}
          </span>
        </div>

        <div className="flex items-center space-x-2 border-l border-slate-800 pl-6">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span className="text-slate-400">Thời gian NOC:</span>
          <span className="font-mono text-cyan-300">{time}</span>
        </div>
      </div>
    </header>
  );
};

export default Header;
