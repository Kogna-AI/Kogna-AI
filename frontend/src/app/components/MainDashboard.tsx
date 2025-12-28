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
import { previousWednesday } from "date-fns";


interface MainDashboardProps {
  activeView: string;
  setActiveView: (view: string) => void;
  onStrategySession: () => void;
  kogniiControlState?: any;
  onKogniiActionComplete?: () => void;
}


export function MainDashboard({
  activeView,
  setActiveView,
  onStrategySession,
  kogniiControlState,
  onKogniiActionComplete,
}: MainDashboardProps) {
  const { user } = useUser();
 

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
