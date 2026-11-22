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
  AlertTriangle,
  FolderOpen,
  Keyboard,
} from 'lucide-react';
import type { AlertEvent } from '../types';
import { SEVERITY_COLOR_GROUP } from '../types';
import { fixtureAdapter } from '../services';
import type { FixtureMode } from '../services';
import { SeverityBadge } from '../components/common';

export const DashboardOverviewPage: React.FC = () => {
  const [events, setEvents] = useState<AlertEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [fixtureMode, setFixtureMode] = useState<FixtureMode>('success');

  // Tải lại / Thử lại: luôn thay toàn bộ danh sách bằng snapshot mới (AC 2).
  // Không merge với dữ liệu cũ — đảm bảo khi retry trả rỗng, bảng hiển thị đúng trạng thái rỗng.
  const handleReload = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await fixtureAdapter.getEvents({ mode: fixtureMode, delayMs: 400 });
      setEvents(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Lỗi không xác định khi nạp dữ liệu.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    fixtureAdapter
      .getEvents({ mode: fixtureMode, delayMs: 400 })
      .then((data) => {
        if (!ignore) {
          setEvents(data);
          setError(null);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!ignore) {
          const msg = err instanceof Error ? err.message : 'Lỗi không xác định khi nạp dữ liệu.';
          setError(msg);
          setLoading(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, [fixtureMode]);

  // Xử lý phím tắt mở rộng dòng bằng bàn phím (TC-UI-006: A11y Enter / Space)
  const handleKeyDown = (e: React.KeyboardEvent, id: string) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      setExpandedId((prev) => (prev === id ? null : id));
    }
  };

  // Tính toán 4 thẻ KPI theo chuẩn TC-UI-001
  const kpi = fixtureAdapter.calculateKpis(events, !error);

  // Thống kê phân bố mức độ RFC 5424 (D-01)
  const criticalCount = events.filter((e) => SEVERITY_COLOR_GROUP(e.severity) === 'critical').length;
  const majorCount    = events.filter((e) => SEVERITY_COLOR_GROUP(e.severity) === 'major').length;
  const warningCount  = events.filter((e) => SEVERITY_COLOR_GROUP(e.severity) === 'warning').length;
  const infoCount     = events.filter((e) => SEVERITY_COLOR_GROUP(e.severity) === 'info').length;

  return (
    <div className="space-y-6">
      {/* Thanh tiêu đề & Bộ chuyển đổi Fixture Mode */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <span>Dòng thời gian cảnh báo mạng viễn thông</span>
            <span className="inline-flex items-center text-xs font-normal px-2 py-0.5 rounded bg-slate-700/50 text-slate-400 border border-slate-600/40">
              <Radio className="w-3 h-3 mr-1" /> Dữ liệu mẫu
            </span>
          </h2>
          <p className="text-sm text-slate-400">
            Giám sát thời gian thực theo hợp đồng Fixture AlertEvent v0.9 (Thẻ N42-20)
          </p>
        </div>

        {/* Thanh công cụ kiểm thử AC 1 & AC 2 */}
        <div className="flex items-center space-x-2 bg-slate-900 p-1.5 rounded-lg border border-slate-800 text-xs">
          <span className="text-slate-400 px-2 font-medium">Chế độ Fixture:</span>
          <button
            onClick={() => setFixtureMode('success')}
            className={`px-2.5 py-1 rounded font-medium transition ${
              fixtureMode === 'success'
                ? 'bg-cyan-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Hợp lệ v1.0
          </button>
          <button
            onClick={() => setFixtureMode('empty')}
            className={`px-2.5 py-1 rounded font-medium transition ${
              fixtureMode === 'empty'
                ? 'bg-cyan-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Dữ liệu rỗng
          </button>
          <button
            onClick={() => setFixtureMode('error')}
            className={`px-2.5 py-1 rounded font-medium transition ${
              fixtureMode === 'error'
                ? 'bg-red-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Giả lập lỗi
          </button>
          <button
            onClick={() => handleReload()}
            disabled={loading}
            className="flex items-center space-x-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 ml-2 transition"
            title="Tải lại / Thử lại (Thay toàn bộ bằng snapshot mới)"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Tải lại</span>
          </button>
        </div>
      </div>

      {/* 4 THẺ KPI TỔNG QUAN THEO CHUẨN TC-UI-001 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* KPI 1: Tổng sự kiện */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-cyan-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Tổng sự kiện</span>
            <Activity className="w-5 h-5" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">{kpi.totalEvents}</div>
          <div className="text-xs text-slate-400 mt-1">Số bản tin đã chuẩn hóa trong buffer</div>
        </div>

        {/* KPI 2: Sự cố đang mở */}
        <div
          className={`p-4 rounded-xl bg-slate-900 border ${
            kpi.openIncidents !== null && kpi.openIncidents > 0
              ? 'border-red-500/30'
              : 'border-slate-800'
          }`}
        >
          <div
            className={`flex items-center justify-between ${
              kpi.openIncidents !== null && kpi.openIncidents > 0
                ? 'text-red-400'
                : 'text-slate-400'
            } mb-2`}
          >
            <span className="text-xs font-semibold uppercase tracking-wider">Sự cố đang mở</span>
            <Layers className="w-5 h-5" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">
            {kpi.openIncidents !== null ? kpi.openIncidents : '—'}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            {kpi.openIncidents !== null
              ? 'Cụm tương quan gom nhóm mức cao'
              : 'Cần kết nối API tương quan (N42-34)'}
          </div>
        </div>

        {/* KPI 3: Tốc độ bản tin */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between text-indigo-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Tốc độ bản tin</span>
            <Gauge className="w-5 h-5" />
          </div>
          <div className="text-2xl font-bold font-mono text-white">
            {kpi.ingestRate !== null ? (
              <>
                <span>{kpi.ingestRate}</span>
                <span className="text-xs font-normal text-slate-400 ml-1">msg/s</span>
              </>
            ) : (
              '—'
            )}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            {kpi.ingestRate !== null
              ? 'Tải danh định W13: 1.000 msg/s'
              : 'Cần luồng dữ liệu thời gian thực (N42-34)'}
          </div>
        </div>

        {/* KPI 4: Trạng thái hệ thống */}
        <div className="p-4 rounded-xl bg-slate-900 border border-emerald-500/30">
          <div className="flex items-center justify-between text-emerald-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Trạng thái hệ thống</span>
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div className="text-base font-bold text-emerald-400 mt-1">{kpi.systemStatus}</div>
          <div className="text-xs text-slate-400 mt-1">Giám sát Liveness & Fixture State</div>
        </div>
      </div>

      {/* Thanh phân bố Mức độ nghiêm trọng (RFC 5424 D-01) */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
        <span className="font-semibold text-slate-400 uppercase tracking-wide">
          Phân bố mức độ cảnh báo:
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

      {/* Bảng sự kiện (Event Explorer) & Các trạng thái UX theo AC 2 & TC-UI-006 */}
      <div className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <h3 className="font-semibold text-white text-sm">Bảng sự kiện tiếp nhận (Event Explorer)</h3>
            <span className="text-[11px] text-slate-400 flex items-center font-normal">
              <Keyboard className="w-3.5 h-3.5 mr-1 text-cyan-400" /> Hỗ trợ phím Tab + Enter/Space
            </span>
          </div>
          <span className="text-xs text-slate-400 font-mono">Hiển thị {events.length} sự kiện</span>
        </div>

        {/* 1. TRẠNG THÁI ĐANG TẢI (LOADING SKELETON) */}
        {loading ? (
          <div className="p-6 space-y-3 animate-pulse">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-10 bg-slate-800/60 rounded-lg w-full" />
            ))}
            <p className="text-center text-xs text-slate-500 pt-2">Đang nạp dữ liệu cảnh báo...</p>
          </div>
        ) : error ? (
          /* 2. TRẠNG THÁI LỖI (ERROR STATE CÓ NÚT RETRY) */
          <div className="p-12 text-center space-y-4">
            <div className="w-12 h-12 bg-red-500/10 text-red-400 rounded-full flex items-center justify-center mx-auto border border-red-500/20">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <h4 className="text-white font-semibold text-sm">Không thể nạp dữ liệu sự kiện</h4>
              <p className="text-xs text-red-400/90 mt-1 max-w-md mx-auto">{error}</p>
            </div>
            <button
              onClick={() => handleReload()}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-red-600/20 text-red-300 border border-red-500/30 hover:bg-red-600/30 text-xs font-medium transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Thử lại kết nối (Retry)</span>
            </button>
          </div>
        ) : events.length === 0 ? (
          /* 3. TRẠNG THÁI RỖNG (EMPTY STATE) */
          <div className="p-12 text-center space-y-3">
            <div className="w-12 h-12 bg-slate-800 text-slate-500 rounded-full flex items-center justify-center mx-auto">
              <FolderOpen className="w-6 h-6" />
            </div>
            <h4 className="text-white font-semibold text-sm">Không có sự kiện cảnh báo nào</h4>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Tệp dữ liệu fixture hiện tại đang rỗng hoặc không có bản ghi phù hợp.
            </p>
            <button
              onClick={() => setFixtureMode('success')}
              className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium transition"
            >
              <span>Nạp lại Fixture v1.0</span>
            </button>
          </div>
        ) : (
          /* 4. BẢNG DỮ LIỆU ĐẦY ĐỦ VÀ DETAIL PANEL */
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
                        tabIndex={0}
                        role="button"
                        aria-expanded={isExpanded}
                        onClick={() => setExpandedId(isExpanded ? null : evt.id)}
                        onKeyDown={(e) => handleKeyDown(e, evt.id)}
                        className={`cursor-pointer transition hover:bg-slate-800/50 focus:outline-none focus:ring-1 focus:ring-cyan-500 ${
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

                      {/* Detail Panel tách Normalized Fields từ Raw Payload */}
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

                            {/* Raw Payload nguyên bản */}
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
