import { useUser } from "./auth/UserContext";
import { AnalyticsView } from "./dashboard/AnalyticsView";
import { DataConnectorHub } from "./dashboard/DataConnectorHub";
import { DashboardOverview } from "./dashboard/dashboardoverview";
import { FeedbackView } from "./dashboard/FeedbackView";
import { MeetingsView } from "./dashboard/MeetingsView";
import { SettingsView } from "./dashboard/SettingsView";
import { StrategyHub } from "./dashboard/StrategyHub";
import { TeamOverview } from "./dashboard/TeamOverview";

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

  return (
    <div className="flex-1 overflow-auto">
      {renderView()}
    </div>
  );
}
