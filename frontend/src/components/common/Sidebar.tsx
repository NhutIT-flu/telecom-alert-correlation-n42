import React from 'react';
import {
  Clock,
  Server,
  Filter,
  BarChart3,
  Layers,
  FileSpreadsheet,
} from 'lucide-react';

export type ScreenTab =
  | 'timeline'
  | 'devices'
  | 'filter'
  | 'stats'
  | 'correlation'
  | 'reports';

interface SidebarProps {
  currentTab: ScreenTab;
  onSelectTab: (tab: ScreenTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
  const menuItems = [
    { id: 'timeline' as ScreenTab, label: 'Dòng thời gian', icon: Clock },
    { id: 'devices' as ScreenTab, label: 'Chi tiết thiết bị', icon: Server },
    { id: 'filter' as ScreenTab, label: 'Bộ lọc & Tra cứu', icon: Filter },
    { id: 'stats' as ScreenTab, label: 'Thống kê viễn thông', icon: BarChart3 },
    { id: 'correlation' as ScreenTab, label: 'Gom nhóm tương quan', icon: Layers },
    { id: 'reports' as ScreenTab, label: 'Xuất báo cáo', icon: FileSpreadsheet },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/50 flex flex-col justify-between p-4">
      <div>
        <div className="px-3 mb-4 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
          Mục điều hành M7
        </div>
        <nav className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </aside>
  );
};

export default Sidebar;
