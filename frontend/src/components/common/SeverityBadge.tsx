import React from 'react';
import { SEVERITY_LABEL, SEVERITY_COLOR_GROUP } from '../../types';

interface SeverityBadgeProps {
  severity: number;
  className?: string;
}

/**
 * Hiển thị badge mức độ cảnh báo theo RFC 5424 (D-01)
 * severity là số nguyên 0–7; FE tự ánh xạ sang nhãn và màu
 */
export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity, className = '' }) => {
  const group = SEVERITY_COLOR_GROUP(severity);
  const label = SEVERITY_LABEL[severity] ?? `SEV-${severity}`;

  const colorClass = {
    critical: 'bg-red-500/20 text-red-400 border-red-500/40',
    major:    'bg-orange-500/20 text-orange-400 border-orange-500/40',
    warning:  'bg-amber-500/20 text-amber-400 border-amber-500/40',
    info:     'bg-cyan-500/20 text-cyan-400 border-cyan-500/40',
    debug:    'bg-slate-500/20 text-slate-400 border-slate-500/40',
  }[group];

  const dotClass = {
    critical: 'bg-red-400',
    major:    'bg-orange-400',
    warning:  'bg-amber-400',
    info:     'bg-cyan-400',
    debug:    'bg-slate-400',
  }[group];

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide border ${colorClass} ${className}`}
    >
      <span className={`w-1.5 h-1.5 mr-1.5 rounded-full ${dotClass} animate-pulse`} />
      {label}
    </span>
  );
};

export default SeverityBadge;
