import React, { useState } from 'react';
import {
  Filter,
  RotateCcw,
  Calendar,
  Clock,
  Server,
  Layers,
  Search,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Check,
} from 'lucide-react';
import type { FilterCriteria, TimePreset } from '../../types';
import { filterService } from '../../services/filterService';
import { SEVERITY_LABEL, SEVERITY_COLOR_GROUP } from '../../types';

export interface AlertFilterPanelProps {
  criteria: FilterCriteria;
  onChange: (criteria: FilterCriteria) => void;
  onApply: () => void;
  onReset: () => void;
  totalFilteredCount?: number;
  totalCount?: number;
  className?: string;
}

const VENDOR_OPTIONS = [
  { value: '', label: 'Tất cả hãng (All)' },
  { value: 'CISCO', label: 'Cisco IOS-XE' },
  { value: 'HUAWEI', label: 'Huawei VRP' },
  { value: 'LINUX', label: 'Linux OS' },
  { value: 'RFC5424', label: 'RFC 5424 Generic' },
  { value: 'RFC3164', label: 'RFC 3164 Legacy' },
];

const PRESET_OPTIONS: { id: TimePreset; label: string }[] = [
  { id: 'all', label: 'Tất cả' },
  { id: '15m', label: '15 phút' },
  { id: '1h', label: '1 giờ' },
  { id: '6h', label: '6 giờ' },
  { id: '24h', label: '24 giờ' },
  { id: '7d', label: '7 ngày' },
];

const ALL_SEVERITIES = [0, 1, 2, 3, 4, 5, 6, 7];

/**
 * Component Giao diện Bộ lọc Cảnh báo Đa tiêu chí (Module M7)
 * Đáp ứng các yêu cầu thẻ N42-28 & Đặc tả Sprint 2:
 * - AC 1: Lọc kết hợp đa tiêu chí (Thời gian, Thiết bị, Hãng, Mức độ, Từ khóa)
 * - AC 2: Báo lỗi inline khi thời gian đảo chiều (startTime > endTime)
 * - Chuẩn hóa màu sắc NOC Dark Theme và tương thích A11y
 */
export const AlertFilterPanel: React.FC<AlertFilterPanelProps> = ({
  criteria,
  onChange,
  onApply,
  onReset,
  totalFilteredCount,
  totalCount,
  className = '',
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);
  const [activePreset, setActivePreset] = useState<TimePreset>('all');

  // Kiểm tra tính hợp lệ của bộ lọc hiện tại (bắt lỗi thời gian đảo theo AC 2)
  const validation = filterService.validateCriteria(criteria);

  // Xử lý khi chọn nhanh Preset thời gian
  const handlePresetSelect = (preset: TimePreset) => {
    setActivePreset(preset);
    const range = filterService.getTimePresetRange(preset);
    onChange({
      ...criteria,
      startTime: range.startTime,
      endTime: range.endTime,
    });
  };

  // Xử lý bật/tắt chọn Severity (đa chọn RFC 5424)
  const handleSeverityToggle = (sev: number) => {
    const current = criteria.severity || [];
    const next = current.includes(sev)
      ? current.filter((s) => s !== sev)
      : [...current, sev].sort((a, b) => a - b);
    onChange({ ...criteria, severity: next });
  };

  // Chọn toàn bộ hoặc bỏ chọn toàn bộ Severity
  const handleSelectAllSeverities = () => {
    const current = criteria.severity || [];
    if (current.length === ALL_SEVERITIES.length) {
      onChange({ ...criteria, severity: [] });
    } else {
      onChange({ ...criteria, severity: [...ALL_SEVERITIES] });
    }
  };

  return (
    <div
      className={`rounded-xl border border-slate-800 bg-slate-900/80 backdrop-blur-sm shadow-xl transition-all ${className}`}
    >
      {/* Tiêu đề & Thanh trạng thái thu gọn */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-800/80">
        <div className="flex items-center space-x-3">
          <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Filter className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
              Bộ lọc cảnh báo đa chiều
              <span className="text-[11px] font-normal text-slate-400 font-mono">
                (N42-28)
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Lọc theo thời gian UTC, thiết bị, hãng, mức độ RFC 5424 và nội dung
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {totalCount !== undefined && totalFilteredCount !== undefined && (
            <div className="text-xs font-mono text-slate-400 bg-slate-800/60 px-2.5 py-1 rounded-md border border-slate-700/50">
              Khớp:{' '}
              <span className="text-cyan-400 font-bold">
                {totalFilteredCount}
              </span>
              /{totalCount}
            </div>
          )}

          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            title={isExpanded ? 'Thu gọn bộ lọc' : 'Mở rộng bộ lọc'}
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Nội dung chi tiết bộ lọc */}
      {isExpanded && (
        <div className="p-5 space-y-4">
          {/* Cảnh báo lỗi inline khi thời gian đảo chiều (AC 2) */}
          {!validation.isValid && (
            <div className="flex items-center space-x-2 p-3 rounded-lg bg-red-950/40 border border-red-500/40 text-red-300 text-xs animate-shake">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              <span>{validation.errorMessage}</span>
            </div>
          )}

          {/* Hàng 1: Khoảng thời gian & Preset */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-1.5">
                <Clock className="w-3.5 h-3.5 text-cyan-400" />
                <span>Khoảng thời gian (UTC)</span>
              </label>

              {/* Các nút chọn nhanh Preset */}
              <div className="flex items-center space-x-1 bg-slate-950/60 p-0.5 rounded-lg border border-slate-800 text-[11px]">
                {PRESET_OPTIONS.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => handlePresetSelect(p.id)}
                    className={`px-2 py-0.5 rounded transition font-medium ${
                      activePreset === p.id
                        ? 'bg-cyan-500 text-slate-950 shadow'
                        : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                    }`}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] text-slate-400 mb-1 flex items-center gap-1">
                  <Calendar className="w-3 h-3" /> Từ thời điểm (Start UTC)
                </label>
                <input
                  type="text"
                  placeholder="YYYY-MM-DDTHH:mm:ssZ"
                  value={criteria.startTime || ''}
                  onChange={(e) => {
                    setActivePreset('all');
                    onChange({ ...criteria, startTime: e.target.value });
                  }}
                  className={`w-full px-3 py-1.5 text-xs rounded-lg bg-slate-950 border font-mono text-slate-200 placeholder-slate-600 focus:outline-none transition ${
                    !validation.isValid
                      ? 'border-red-500/60 focus:border-red-500'
                      : 'border-slate-800 focus:border-cyan-500'
                  }`}
                />
              </div>

              <div>
                <label className="block text-[11px] text-slate-400 mb-1 flex items-center gap-1">
                  <Calendar className="w-3 h-3" /> Đến thời điểm (End UTC)
                </label>
                <input
                  type="text"
                  placeholder="YYYY-MM-DDTHH:mm:ssZ"
                  value={criteria.endTime || ''}
                  onChange={(e) => {
                    setActivePreset('all');
                    onChange({ ...criteria, endTime: e.target.value });
                  }}
                  className={`w-full px-3 py-1.5 text-xs rounded-lg bg-slate-950 border font-mono text-slate-200 placeholder-slate-600 focus:outline-none transition ${
                    !validation.isValid
                      ? 'border-red-500/60 focus:border-red-500'
                      : 'border-slate-800 focus:border-cyan-500'
                  }`}
                />
              </div>
            </div>
          </div>

          {/* Hàng 2: Thiết bị, Hãng & Từ khóa */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Hostname */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1 flex items-center space-x-1.5">
                <Server className="w-3.5 h-3.5 text-cyan-400" />
                <span>Thiết bị (Hostname)</span>
              </label>
              <input
                type="text"
                placeholder="Ví dụ: R1-CORE, SW-DIST..."
                value={criteria.hostname || ''}
                onChange={(e) =>
                  onChange({ ...criteria, hostname: e.target.value })
                }
                className="w-full px-3 py-1.5 text-xs rounded-lg bg-slate-950 border border-slate-800 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500 transition"
              />
            </div>

            {/* Vendor */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1 flex items-center space-x-1.5">
                <Layers className="w-3.5 h-3.5 text-cyan-400" />
                <span>Nhà sản xuất (Vendor)</span>
              </label>
              <select
                value={criteria.vendor || ''}
                onChange={(e) =>
                  onChange({ ...criteria, vendor: e.target.value })
                }
                className="w-full px-3 py-1.5 text-xs rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500 transition"
              >
                {VENDOR_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Query */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1 flex items-center space-x-1.5">
                <Search className="w-3.5 h-3.5 text-cyan-400" />
                <span>Tìm kiếm nội dung (Query)</span>
              </label>
              <input
                type="text"
                placeholder="Từ khóa thông báo, IP, program..."
                value={criteria.searchQuery || ''}
                onChange={(e) =>
                  onChange({ ...criteria, searchQuery: e.target.value })
                }
                className="w-full px-3 py-1.5 text-xs rounded-lg bg-slate-950 border border-slate-800 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500 transition"
              />
            </div>
          </div>

          {/* Hàng 3: Dải chip chọn Severity (RFC 5424) */}
          <div className="space-y-1.5 pt-1">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-slate-300 flex items-center space-x-1.5">
                <AlertCircle className="w-3.5 h-3.5 text-cyan-400" />
                <span>Mức độ nghiêm trọng (RFC 5424 Severity)</span>
              </label>
              <button
                type="button"
                onClick={handleSelectAllSeverities}
                className="text-[11px] text-cyan-400 hover:text-cyan-300 transition"
              >
                {criteria.severity?.length === ALL_SEVERITIES.length
                  ? 'Bỏ chọn tất cả'
                  : 'Chọn tất cả (0-7)'}
              </button>
            </div>

            <div className="flex flex-wrap gap-1.5">
              {ALL_SEVERITIES.map((sev) => {
                const isSelected = criteria.severity?.includes(sev);
                const group = SEVERITY_COLOR_GROUP(sev);
                const label = SEVERITY_LABEL[sev] ?? `SEV-${sev}`;

                const activeColor = {
                  critical:
                    'bg-red-500/20 text-red-300 border-red-500/60 shadow-red-950/50',
                  major:
                    'bg-orange-500/20 text-orange-300 border-orange-500/60 shadow-orange-950/50',
                  warning:
                    'bg-amber-500/20 text-amber-300 border-amber-500/60 shadow-amber-950/50',
                  info:
                    'bg-cyan-500/20 text-cyan-300 border-cyan-500/60 shadow-cyan-950/50',
                  debug:
                    'bg-slate-700/30 text-slate-300 border-slate-600/60',
                }[group];

                return (
                  <button
                    key={sev}
                    type="button"
                    onClick={() => handleSeverityToggle(sev)}
                    className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-md text-xs font-medium border transition ${
                      isSelected
                        ? `${activeColor} shadow-sm font-semibold`
                        : 'bg-slate-950 text-slate-500 border-slate-800 hover:border-slate-700 hover:text-slate-300'
                    }`}
                  >
                    {isSelected && <Check className="w-3 h-3 mr-0.5" />}
                    <span>{label}</span>
                    <span className="text-[10px] font-mono opacity-60">
                      ({sev})
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Thanh nút hành động (Actions) */}
          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800/80">
            <button
              type="button"
              onClick={() => {
                setActivePreset('all');
                onReset();
              }}
              className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white bg-slate-800/60 hover:bg-slate-800 border border-slate-700/50 transition"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Đặt lại bộ lọc</span>
            </button>

            <button
              type="button"
              onClick={onApply}
              disabled={!validation.isValid}
              className={`inline-flex items-center space-x-1.5 px-4 py-1.5 rounded-lg text-xs font-medium transition ${
                validation.isValid
                  ? 'bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold shadow-lg shadow-cyan-950/50 cursor-pointer'
                  : 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed opacity-60'
              }`}
            >
              <Filter className="w-3.5 h-3.5" />
              <span>Áp dụng bộ lọc</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertFilterPanel;
