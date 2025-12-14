import { useState, useEffect, useRef } from "react";
import { DashboardOverview } from "./dashboard/dashboardoverview";
import { TeamOverview } from "./dashboard/TeamOverview";
import { StrategyHub } from "./dashboard/StrategyHub";
import { DataConnectorHub } from "./dashboard/DataConnectorHub";
import { MeetingsView } from "./dashboard/MeetingsView";
import { AnalyticsView } from "./dashboard/AnalyticsView";
import { FeedbackView } from "./dashboard/FeedbackView";
import { SettingsView } from "./dashboard/SettingsView";
import { useUser } from "./auth/UserContext";
import { GridStack } from 'gridstack';
import "gridstack/dist/gridstack.css";
import "gridstack/dist/gridstack-extra.css";


interface MainDashboardProps {
  activeView: string;
  setActiveView: (view: string) => void;
  onStrategySession: () => void;
  kogniiControlState?: any;
  onKogniiActionComplete?: () => void;
}

interface GridWidget {
  id: string;
  x: number;
  y: number;
  w: number;
  h: number;
  content: string;
  type: 'chart' | 'metric' | 'table' | 'note' | 'custom';
  title: string;
}

export function MainDashboard({
  activeView,
  setActiveView,
  onStrategySession,
  kogniiControlState,
  onKogniiActionComplete,
}: MainDashboardProps) {
  const { user } = useUser();
  const [whiteboardMode, setWhiteBoardMode] = useState(false);  
  
    // Gridstack refrences
    const gridRef = useRef<HTMLDivElement>(null);
    const gridInstanceRef = useRef<GridStack | null> (null);
    const [widgets, setWidgets] = useState<GridWidget[]>([
      {
        id: 'widget-1',
        x: 0,
        y: 0,
        w: 4,
        h: 3,
        content: 'Revenue Chart',
        type: 'chart',
        title: 'Revenue Overview'
      },
      {
        id: 'widget-2',
        x: 4,
        y: 0,
        w: 4,
        h: 3,
        content: 'Key Metrics',
        type: 'metric',
        title: 'KPIs'
      },
      {
        id: 'widget-3',
        x: 8,
        y: 0,
        w: 4,
        h: 3,
        content: 'Tasks Table',
        type: 'table',
        title: 'Recent Tasks'
      }
    ]);


  const renderView = () => {
    switch (activeView) {
      case "dashboard":
        return (
          <DashboardOverview
            onStrategySession={onStrategySession}
            user={user}
          />
        );
      case "team":
        return <TeamOverview />;
      case "strategy":
        return (
          <StrategyHub
            kogniiControlState={kogniiControlState}
            onKogniiActionComplete={onKogniiActionComplete}
          />
        );

      case "connectors":
        return <DataConnectorHub />;
      case "meetings":
        return <MeetingsView />;
      case "analytics":
        return <AnalyticsView />;
      case "feedback":
        return <FeedbackView />;
      case "settings":
        return <SettingsView />;
      default:
        return (
          <DashboardOverview
            onStrategySession={onStrategySession}
            user={user}
          />
        );
    }
  };

  return <div className="flex-1 overflow-auto">{renderView()}</div>;
}
