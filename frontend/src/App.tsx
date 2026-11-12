import React, { useState } from 'react';
import { Header, Sidebar } from './components/common';
import type { ScreenTab } from './components/common';
import {
  DashboardOverviewPage,
  DeviceDetailPage,
  AlertSearchPage,
  DeviceStatsPage,
  CorrelationAlertsPage,
  ReportsPage,
} from './pages';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<ScreenTab>('timeline');

  const renderActiveScreen = () => {
    switch (currentTab) {
      case 'timeline':
        return <DashboardOverviewPage />;
      case 'devices':
        return <DeviceDetailPage />;
      case 'filter':
        return <AlertSearchPage />;
      case 'stats':
        return <DeviceStatsPage />;
      case 'correlation':
        return <CorrelationAlertsPage />;
      case 'reports':
        return <ReportsPage />;
      default:
        return <DashboardOverviewPage />;
    }
  };

  return (
    <div className="min-h-screen bg-noc-bg text-slate-100 flex flex-col font-sans">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar currentTab={currentTab} onSelectTab={setCurrentTab} />
        <main className="flex-1 overflow-y-auto p-6 bg-slate-950/40">
          {renderActiveScreen()}
        </main>
      </div>
    </div>
  );
};

export default App;
