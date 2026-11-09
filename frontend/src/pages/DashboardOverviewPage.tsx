import React, { useEffect, useState } from 'react';
import { AlertCircle, AlertTriangle, Info, Bell, RefreshCw, Radio } from 'lucide-react';
import type { AlertEvent } from '../types';
import { SEVERITY_COLOR_GROUP } from '../types';
import { alertService } from '../services';
import { SeverityBadge } from '../components/common';

export const DashboardOverviewPage: React.FC = () => {
  const [events, setEvents] = useState<AlertEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await alertService.getEvents(50);
      setEvents(data);
    } catch (err) {
      setError('Không thể tải danh sách cảnh báo từ máy chủ.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    alertService
      .getEvents(50)
      .then((data) => {
        if (!ignore) {
          setEvents(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!ignore) {
          setError('Không thể tải danh sách cảnh báo từ máy chủ.');
          setLoading(false);
          console.error(err);
        }
      });

    return () => {
      ignore = true;
    };
  }, []);

  // Đếm KPI theo số severity RFC 5424 (D-01): 0-2 = critical, 3 = major, 4 = warning, 5-6 = info
  const criticalCount = events.filter((e) => SEVERITY_COLOR_GROUP(e.severity) === 'critical').length;
  const majorCount    = events.filter((e) => SEVERITY_COLOR_GROUP(e.severity) === 'major').length;
  const warningCount  = events.filter((e) => SEVERITY_COLOR_GROUP(e.severity) === 'warning').length;
  const infoCount     = events.filter((e) => SEVERITY_COLOR_GROUP(e.severity) === 'info').length;

  return (
    <div className="space-y-6">
      {/* Thanh tiêu đề & nút tải lại */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <span>Dòng thời gian cảnh báo mạng viễn thông</span>
            <span className="inline-flex items-center text-xs font-normal px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Radio className="w-3 h-3 mr-1 animate-pulse" /> Live Feed
            </span>
          </h2>
          <p className="text-sm text-slate-400">
            Giám sát cảnh báo thời gian thực từ Router, Switch, Firewall
          </p>
        </div>

        <button
          onClick={loadAlerts}
          disabled={loading}
          className="flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium border border-slate-700 transition"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Làm mới</span>
        </button>
      </div>

      {/* KPI Cards — severity 0-2 đỏ, 3 cam, 4 vàng, 5-6 cyan */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900 border border-red-500/30">
          <div className="flex items-center justify-between text-red-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Critical (0–2)</span>
            <AlertCircle className="w-5 h-5" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">{criticalCount}</div>
          <div className="text-xs text-slate-400 mt-1">Emergency / Alert / Critical</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-orange-500/30">
          <div className="flex items-center justify-between text-orange-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Error (3)</span>
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">{majorCount}</div>
          <div className="text-xs text-slate-400 mt-1">Error — lỗi diện rộng</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-amber-500/30">
          <div className="flex items-center justify-between text-amber-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Warning (4)</span>
            <Bell className="w-5 h-5" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">{warningCount}</div>
          <div className="text-xs text-slate-400 mt-1">Warning — tiềm ẩn rủi ro</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900 border border-cyan-500/30">
          <div className="flex items-center justify-between text-cyan-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Info (5–6)</span>
            <Info className="w-5 h-5" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">{infoCount}</div>
          <div className="text-xs text-slate-400 mt-1">Notice / Info — vận hành bình thường</div>
        </div>
      </div>

      {/* Live Alert Table */}
      <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="font-semibold text-white text-sm">Danh sách sự kiện cảnh báo tiếp nhận</h3>
          <span className="text-xs text-slate-400">Hiển thị {events.length} sự kiện mới nhất</span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-400 text-sm">Đang tải dữ liệu cảnh báo...</div>
        ) : error ? (
          <div className="p-8 text-center text-red-400 text-sm">{error}</div>
        ) : events.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">Không có sự kiện nào.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-800/60 text-slate-400 text-xs uppercase font-mono tracking-wider">
                <tr>
                  <th className="py-3 px-4">Thời gian</th>
                  <th className="py-3 px-4">Mức độ</th>
                  <th className="py-3 px-4">Hostname</th>
                  <th className="py-3 px-4">Vendor</th>
                  <th className="py-3 px-4">IP Nguồn</th>
                  <th className="py-3 px-4">Program</th>
                  <th className="py-3 px-4">Nội dung</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-sans">
                {events.map((evt) => (
                  <tr key={evt.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-mono text-xs text-slate-400 whitespace-nowrap">
                      {new Date(evt.event_timestamp).toLocaleTimeString('vi-VN')}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <SeverityBadge severity={evt.severity} />
                    </td>
                    <td className="py-3 px-4 font-semibold text-white whitespace-nowrap">
                      {evt.hostname}
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-cyan-400 whitespace-nowrap">
                      {evt.vendor}
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-slate-400 whitespace-nowrap">
                      {evt.source_ip}
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-slate-500 whitespace-nowrap">
                      {evt.program}
                    </td>
                    <td className="py-3 px-4 text-slate-300 text-xs max-w-md truncate" title={evt.raw_payload}>
                      {evt.message}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardOverviewPage;
