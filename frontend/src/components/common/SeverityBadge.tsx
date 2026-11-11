import React from 'react';
import {
  AlertOctagon,
  AlertTriangle,
  AlertCircle,
  Info,
  HelpCircle,
} from 'lucide-react';
import { SEVERITY_LABEL, SEVERITY_COLOR_GROUP } from '../../types';

interface SeverityBadgeProps {
  severity: number;
  className?: string;
  showIcon?: boolean;
}

/**
 * Hiển thị huy hiệu mức độ cảnh báo theo RFC 5424 (D-01 & Baseline 03/11/2026)
 * Tuân thủ mục 5 ARCHITECTURE_DESIGN:
 * "Severity must have text/icon in addition to color" (kết hợp màu sắc + icon + text)
 */
export const SeverityBadge: React.FC<SeverityBadgeProps> = ({
  severity,
  className = '',
  showIcon = true,
}) => {
  const group = SEVERITY_COLOR_GROUP(severity);
  const label = SEVERITY_LABEL[severity] ?? `SEV-${severity}`;

  const renderIcon = () => {
    switch (group) {
      case 'critical':
        return <AlertOctagon className="w-3.5 h-3.5 mr-1 text-red-400" />;
      case 'major':
        return <AlertTriangle className="w-3.5 h-3.5 mr-1 text-orange-400" />;
      case 'warning':
        return <AlertCircle className="w-3.5 h-3.5 mr-1 text-amber-400" />;
      case 'info':
        return <Info className="w-3.5 h-3.5 mr-1 text-cyan-400" />;
      case 'debug':
      default:
        return <HelpCircle className="w-3.5 h-3.5 mr-1 text-slate-400" />;
    }
  };

  const colorClass = {
    critical: 'bg-red-500/15 text-red-300 border-red-500/40',
    major:    'bg-orange-500/15 text-orange-300 border-orange-500/40',
    warning:  'bg-amber-500/15 text-amber-300 border-amber-500/40',
    info:     'bg-cyan-500/15 text-cyan-300 border-cyan-500/40',
    debug:    'bg-slate-500/15 text-slate-300 border-slate-500/40',
  }[group];

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold tracking-wide border ${colorClass} ${className}`}
      title={`Severity ${severity}: ${label}`}
    >
      {showIcon && renderIcon()}
      <span>{label}</span>
      <span className="ml-1 text-[10px] opacity-60 font-mono">({severity})</span>
    </span>
  );
};

export default SeverityBadge;
