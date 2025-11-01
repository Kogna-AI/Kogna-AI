"use client";
import { useState, useMemo, useEffect } from "react";
import { Sidebar } from "../sidebar";
import { MainDashboard } from "../MainDashboard";
import { KogniiAssistant } from "../kognii/KogniiAssistant";
import { NotificationCenter } from "../NotificationCenter";
import { useUser } from "../auth/UserContext";
import { useRouter } from "next/navigation";

interface DashboardLayoutProps {
  activeView: string;
}

export function DashboardLayout({ activeView }: DashboardLayoutProps) {
  const { isAuthenticated } = useUser();
  const router = useRouter();
  const [isKogniiOpen, setIsKogniiOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [strategySessionMode, setStrategySessionMode] = useState(false);

  // Kognii control states
  const [kogniiControlState, setKogniiControlState] = useState({
    shouldOpenObjectiveCreation: false,
    shouldNavigateToView: null as string | null,
    objectiveFormData: null as any,
    shouldHighlightElement: null as string | null,
    guidedTourActive: false,
    currentGuidanceStep: 0,
  });

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  const handleStrategySession = () => {
    setStrategySessionMode(true);
    setIsKogniiOpen(true);
  };

  const handleCloseKognii = () => {
    setIsKogniiOpen(false);
    setStrategySessionMode(false);
    kogniiActions.clearKogniiControl();
  };

  // Memoized Kognii control functions
  const kogniiActions = useMemo(
    () => ({
      navigateToView: (view: string) => {
        // Navigate to the appropriate route
        router.push(`/${view}`);
        setKogniiControlState((prev) => ({
          ...prev,
          shouldNavigateToView: view,
        }));
      },

      openObjectiveCreation: (prefillData?: any) => {
        router.push('/strategy');
        setKogniiControlState((prev) => ({
          ...prev,
          shouldOpenObjectiveCreation: true,
          objectiveFormData: prefillData || null,
        }));
      },

      updateObjectiveForm: (formData: any) => {
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

      startGuidedTour: (tourType: string) => {
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
    [router]
  );

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="size-full flex bg-background">
      <Sidebar
        activeView={activeView}
        setActiveView={(view) => router.push(`/${view}`)}
        onKogniiToggle={() => setIsKogniiOpen(!isKogniiOpen)}
        onNotificationsToggle={() => setNotificationsOpen(!notificationsOpen)}
      />

      <div className="flex-1 flex">
        <MainDashboard
          activeView={activeView}
          setActiveView={(view) => router.push(`/${view}`)}
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
