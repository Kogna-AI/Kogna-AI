"use client";

import { useMemo, useState } from "react";
import { UserProvider } from "./components/auth/UserContext";
import { KogniiAssistant } from "./components/kognii/KogniiAssistant";
import { MainDashboard } from "./components/MainDashboard";
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

      startGuidedTour: () => {
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
