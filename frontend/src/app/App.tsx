import { useMemo, useState } from "react";
import { LoginScreen } from "./components/auth/LoginScreen";
import { UserProvider, useUser } from "./components/auth/UserContext";
import { KogniiAssistant } from "./components/KogniiAssistant";
import { MainDashboard } from "./components/Maindashboard";
import { NotificationCenter } from "./components/NotificationCenter";
import { Sidebar } from "./components/sidebar";

type ObjectiveFormData = {
  title?: string;
  description?: string;
  deadline?: string;
  priority?: string;
  team_responsible?: string;
  [key: string]: unknown;
};

function AppContent() {
  const { isAuthenticated, loading } = useUser(); // ✅ take loading
  const [activeView, setActiveView] = useState("dashboard");
  const [isKogniiOpen, setIsKogniiOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [strategySessionMode, setStrategySessionMode] = useState(false);

  const [kogniiControlState, setKogniiControlState] = useState({
    shouldOpenObjectiveCreation: false,
    shouldNavigateToView: null as string | null,
    objectiveFormData: null as ObjectiveFormData | null,
    shouldHighlightElement: null as string | null,
    guidedTourActive: false,
    currentGuidanceStep: 0,
  });

  const handleStrategySession = () => {
    setStrategySessionMode(true);
    setIsKogniiOpen(true);
  };

  const handleCloseKognii = () => {
    setIsKogniiOpen(false);
    setStrategySessionMode(false);
    kogniiActions.clearKogniiControl();
  };

  const kogniiActions = useMemo(
    () => ({
      navigateToView: (view: string) => {
        setActiveView(view);
        setKogniiControlState((prev) => ({
          ...prev,
          shouldNavigateToView: view,
        }));
      },

      openObjectiveCreation: (prefillData?: ObjectiveFormData) => {
        setActiveView("strategy");
        setKogniiControlState((prev) => ({
          ...prev,
          shouldOpenObjectiveCreation: true,
          objectiveFormData: prefillData || null,
        }));
      },

      updateObjectiveForm: (formData: ObjectiveFormData) => {
        setKogniiControlState((prev) => ({
          ...prev,
          objectiveFormData: { ...prev.objectiveFormData, ...formData },
        }));
      },

      highlightElement: (elementId: string) => {
        setKogniiControlState((prev) => ({
          ...prev,
          shouldHighlightElement: elementId,
        }));
      },

      startGuidedTour: (_tourType: string) => {
        setKogniiControlState((prev) => ({
          ...prev,
          guidedTourActive: true,
          currentGuidanceStep: 0,
        }));
      },

      clearKogniiControl: () => {
        setKogniiControlState({
          shouldOpenObjectiveCreation: false,
          shouldNavigateToView: null,
          objectiveFormData: null,
          shouldHighlightElement: null,
          guidedTourActive: false,
          currentGuidanceStep: 0,
        });
      },
    }),
    []
  );

  // ✅ 1. While auth state is being determined, render nothing (or a loader)
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center text-sm text-muted-foreground">
        Checking authentication…
      </div>
    );
  }

  // ✅ 2. Only AFTER loading finishes, decide to show login
  if (!isAuthenticated) {
    return <LoginScreen />;
  }

  // ✅ 3. Authenticated app
  return (
    <div className="size-full flex bg-background">
      <Sidebar
        activeView={activeView}
        setActiveView={setActiveView}
        onKogniiToggle={() => setIsKogniiOpen(!isKogniiOpen)}
        onNotificationsToggle={() => setNotificationsOpen(!notificationsOpen)}
      />

      <div className="flex-1 flex">
        <MainDashboard
          activeView={activeView}
          setActiveView={setActiveView}
          onStrategySession={handleStrategySession}
          kogniiControlState={kogniiControlState}
          onKogniiActionComplete={kogniiActions.clearKogniiControl}
        />

        {isKogniiOpen && (
          <div
            className="fixed inset-0 pointer-events-none"
            style={{ zIndex: "var(--z-kognii-assistant)" }}
          >
            <div className="absolute right-0 top-0 h-full pointer-events-auto">
              <KogniiAssistant
                onClose={handleCloseKognii}
                strategySessionMode={strategySessionMode}
                activeView={activeView}
                kogniiActions={kogniiActions}
              />
            </div>
          </div>
        )}
      </div>

      {notificationsOpen && (
        <NotificationCenter onClose={() => setNotificationsOpen(false)} />
      )}
    </div>
  );
}

export default function App() {
  return (
    <UserProvider>
      <AppContent />
    </UserProvider>
  );
}
