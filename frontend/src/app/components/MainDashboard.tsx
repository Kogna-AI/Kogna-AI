import { DashboardOverview } from "./dashboard/dashboardoverview";
import { DriveHub } from "./dashboard/DriveHub";
import { TeamOverview } from "./dashboard/TeamOverview";
import { StrategyHub } from "./dashboard/StrategyHub";
import { DataConnectorHub } from "./dashboard/DataConnectorHub";
import { SettingsView } from "./dashboard/SettingsView";
import { useUser } from "./auth/UserContext";

interface MainDashboardProps {
  activeView: string;
  setActiveView: (view: string) => void;
  onStrategySession: () => void;
  onOpenAssistant?: () => void;
  kogniiControlState?: any;
  onKogniiActionComplete?: () => void;
}

export function MainDashboard({
  activeView,
  setActiveView,
  onStrategySession,
  onOpenAssistant,
  kogniiControlState,
  onKogniiActionComplete,
}: MainDashboardProps) {
  const { user } = useUser();
  const renderView = () => {
    switch (activeView) {
      case "dashboard":
        return (
          <DashboardOverview user={user} onOpenAssistant={onOpenAssistant} />
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
      case "drive":
        return <DriveHub onOpenAssistant={onOpenAssistant} />;
      case "settings":
        return <SettingsView />;
      default:
        return (
          <DashboardOverview user={user} onOpenAssistant={onOpenAssistant} />
        );
    }
  };

  return <div className="flex-1 overflow-auto">{renderView()}</div>;
}
