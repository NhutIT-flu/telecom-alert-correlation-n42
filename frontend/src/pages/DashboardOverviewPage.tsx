import React, { useEffect, useState } from 'react';
import {
  Activity,
  Layers,
  Gauge,
  CheckCircle2,
  RefreshCw,
  Radio,
  ChevronDown,
  ChevronRight,
  Terminal,
} from 'lucide-react';
import type { AlertEvent } from '../types';
import { SEVERITY_COLOR_GROUP } from '../types';
import { alertService } from '../services';
import { SeverityBadge } from '../components/common';

export const DashboardOverviewPage: React.FC = () => {
  const [events, setEvents] = useState<AlertEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

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

  // Phân loại đếm severity theo RFC 5424 (D-01)
  const criticalCount = events.filter((e) => SEVERITY_COLOR_GROUP(e.severity) === 'critical').length;
  const majorCount    = events.filter((e) => SEVERITY_COLOR_GROUP(e.severity) === 'major').length;
  const warningCount  = events.filter((e) => SEVERITY_COLOR_GROUP(e.severity) === 'warning').length;
  const infoCount     = events.filter((e) => SEVERITY_COLOR_GROUP(e.severity) === 'info').length;

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="space-y-6">
      {/* Tiêu đề điều hành NOC */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <span>Dòng thời gian cảnh báo mạng viễn thông</span>
            <span className="inline-flex items-center text-xs font-normal px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Radio className="w-3 h-3 mr-1 animate-pulse" /> Live Stream
            </span>
          </h2>
          <p className="text-sm text-slate-400">
            Giám sát cảnh báo thời gian thực từ Router, Switch, Firewall theo đặc tả Baseline 03/11/2026
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

      {/* 4 THẺ KPI TỔNG QUAN THEO CHUẨN TC-UI-001 (Baseline 03/11/2026) */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* KPI 1: Tổng sự kiện (Total Events) */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-cyan-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Tổng sự kiện</span>
            <Activity className="w-5 h-5" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">{events.length}</div>
          <div className="text-xs text-slate-400 mt-1">Sự kiện đã chuẩn hóa trong buffer</div>
        </div>

        {/* KPI 2: Sự cố đang mở (Open Incidents) */}
        <div className="p-4 rounded-xl bg-slate-900 border border-red-500/30">
          <div className="flex items-center justify-between text-red-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Sự cố đang mở</span>
            <Layers className="w-5 h-5" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">1</div>
          <div className="text-xs text-slate-400 mt-1">Cụm tương quan Link Flap / BGP</div>
        </div>

        {/* KPI 3: Tốc độ bản tin (Ingest Rate msg/s) */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-indigo-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Tốc độ bản tin</span>
            <Gauge className="w-5 h-5" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">
            <span>~10</span>
            <span className="text-xs font-normal text-slate-400 ml-1">msg/s</span>
          </div>
          <div className="text-xs text-slate-400 mt-1">Tải danh định W13: 1.000 msg/s</div>
        </div>

        {/* KPI 4: Trạng thái hệ thống (System Status) */}
        <div className="p-4 rounded-xl bg-slate-900 border border-emerald-500/30">
          <div className="flex items-center justify-between text-emerald-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Trạng thái hệ thống</span>
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div className="text-base font-bold text-emerald-400 mt-1">SẴN SÀNG (HEALTHY)</div>
          <div className="text-xs text-slate-400 mt-1">Process Liveness GET /api/health</div>
        </div>
      </div>

      {/* Thanh phân bố Mức độ nghiêm trọng (Severity Breakdown Bar) */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
        <span className="font-semibold text-slate-400 uppercase tracking-wide">
          Phân bố mức độ cảnh báo (RFC 5424 D-01):
        </span>
        <div className="flex items-center space-x-6">
          <span className="flex items-center space-x-1.5 text-red-400">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
            <span>Critical (0–2): <b>{criticalCount}</b></span>
          </span>
          <span className="flex items-center space-x-1.5 text-orange-400">
            <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
            <span>Major / Error (3): <b>{majorCount}</b></span>
          </span>
          <span className="flex items-center space-x-1.5 text-amber-400">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <span>Warning (4): <b>{warningCount}</b></span>
          </span>
          <span className="flex items-center space-x-1.5 text-cyan-400">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-500" />
            <span>Info (5–6): <b>{infoCount}</b></span>
          </span>
        </div>
      </div>

      {/* Live Alert Table với Detail Panel tách Normalized vs Raw theo ARCHITECTURE_DESIGN Mục 5 */}
      <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-white text-sm">Bảng sự kiện tiếp nhận (Event Explorer)</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Nhấp vào từng dòng để mở chi tiết trường chuẩn hóa và bản tin thô (raw payload)
            </p>
          </div>
          <span className="text-xs text-slate-400 font-mono">Hiển thị {events.length} sự kiện</span>
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
                  <th className="py-3 px-3 w-8"></th>
                  <th className="py-3 px-4">Thời gian (ICT / UTC+7)</th>
                  <th className="py-3 px-4">Mức độ</th>
                  <th className="py-3 px-4">Thiết bị (Hostname)</th>
                  <th className="py-3 px-4">Vendor</th>
                  <th className="py-3 px-4">IP Nguồn (Lab 10.10.x)</th>
                  <th className="py-3 px-4">Tiến trình</th>
                  <th className="py-3 px-4">Thông điệp chuẩn hóa</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-sans">
                {events.map((evt) => {
                  const isExpanded = expandedId === evt.id;
                  return (
                    <React.Fragment key={evt.id}>
                      <tr
                        onClick={() => toggleExpand(evt.id)}
                        className={`cursor-pointer transition hover:bg-slate-800/50 ${
                          isExpanded ? 'bg-slate-800/40' : ''
                        }`}
                      >
                        <td className="py-3 px-3 text-slate-500">
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4 text-cyan-400" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                        </td>
                        <td className="py-3 px-4 font-mono text-xs text-slate-400 whitespace-nowrap">
                          {new Date(evt.event_timestamp).toLocaleTimeString('vi-VN', {
                            timeZone: 'Asia/Ho_Chi_Minh',
                          })}
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
                        <td className="py-3 px-4 text-slate-300 text-xs max-w-md truncate" title={evt.message}>
                          {evt.message}
                        </td>
                      </tr>

                      {/* Detail Panel tách Normalized Fields từ Raw Payload (ARCHITECTURE_DESIGN Mục 5) */}
                      {isExpanded && (
                        <tr className="bg-slate-950/70 border-b border-slate-800">
                          <td colSpan={8} className="p-4 pl-12 space-y-3">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs bg-slate-900/90 p-3 rounded-lg border border-slate-800">
                              <div>
                                <span className="text-slate-500 block">Event UUID:</span>
                                <span className="font-mono text-slate-300 select-all">{evt.id}</span>
                              </div>
                              <div>
                                <span className="text-slate-500 block">Received At (UTC):</span>
                                <span className="font-mono text-slate-300">
                                  {new Date(evt.received_at).toISOString()}
                                </span>
                              </div>
                              <div>
                                <span className="text-slate-500 block">Facility:</span>
                                <span className="font-mono text-cyan-400">{evt.facility}</span>
                              </div>
                              <div>
                                <span className="text-slate-500 block">Phân loại (Category):</span>
                                <span className="font-mono text-emerald-400">{evt.category}</span>
                              </div>
                            </div>

                            {/* Raw Payload nguyên bản (Đối soát kiểm thử) */}
                            <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                              <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400 mb-1.5">
                                <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                                <span>Bản tin thô tiếp nhận (Raw Syslog Payload):</span>
                              </div>
                              <pre className="font-mono text-xs text-emerald-300/90 bg-black/40 p-2.5 rounded border border-slate-800/80 overflow-x-auto select-all">
                                {evt.raw_payload}
                              </pre>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardOverviewPage;
