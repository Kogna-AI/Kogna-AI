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
  const { isAuthenticated, loading } = useUser();
  const router = useRouter();

  const [isKogniiOpen, setIsKogniiOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [strategySessionMode, setStrategySessionMode] = useState(false);

  const [kogniiControlState, setKogniiControlState] = useState({
    shouldOpenObjectiveCreation: false,
    shouldNavigateToView: null as string | null,
    objectiveFormData: null as any,
    shouldHighlightElement: null as string | null,
    guidedTourActive: false,
    currentGuidanceStep: 0,
  });

  useEffect(() => {
    if (loading) return;

    if (!isAuthenticated) {
      router.replace("/login");
    }
  }, [loading, isAuthenticated, router]);

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
        router.push(`/${view}`);
        setKogniiControlState((prev) => ({
          ...prev,
          shouldNavigateToView: view,
        }));
      },

      openObjectiveCreation: (prefillData?: any) => {
        router.push("/strategy");
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
    [router]
  );

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center text-sm text-muted-foreground">
        Loading dashboard…
      </div>
    );
  }

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

      <div className="flex-1 flex ml-64">
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
