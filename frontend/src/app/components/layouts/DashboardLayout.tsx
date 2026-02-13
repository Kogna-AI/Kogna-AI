"use client";

import { useState, useMemo, useEffect } from "react";
import { Sidebar } from "../sidebar";
import { MainDashboard } from "../MainDashboard";
import { KogniiAssistant } from "../kognii/KogniiAssistant";
import { NotificationCenter } from "../NotificationCenter";
import { DashboardTopNav } from "./DashboardTopNav";
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
      {/* Left sidebar (priority) — full height from top */}
      <Sidebar
        activeView={activeView}
        setActiveView={(view) => router.push(`/${view}`)}
        onKogniiToggle={() => setIsKogniiOpen(!isKogniiOpen)}
        onNotificationsToggle={() => setNotificationsOpen(!notificationsOpen)}
      />

      {/* Main content area: top bar only above content, not above sidebar */}
      <div className="flex-1 flex flex-col ml-64 min-h-0">
        <DashboardTopNav
          onKogniiToggle={() => setIsKogniiOpen(!isKogniiOpen)}
          onNotificationsToggle={() => setNotificationsOpen(!notificationsOpen)}
        />
        <div className="flex-1 flex min-h-0 relative overflow-hidden">
          <div className="flex-1 min-w-0 flex flex-col overflow-hidden">
            <MainDashboard
              activeView={activeView}
              setActiveView={(view) => router.push(`/${view}`)}
              onStrategySession={handleStrategySession}
              onOpenAssistant={() => setIsKogniiOpen(true)}
              kogniiControlState={kogniiControlState}
              onKogniiActionComplete={kogniiActions.clearKogniiControl}
            />
          </div>

          {/* Notifications — same right-panel position as Kogna Assistant */}
          {notificationsOpen && (
            <div
              className="
                w-[400px] border-l border-border bg-background transition-all duration-300 flex flex-col min-h-0 shrink-0
                fixed top-12 right-0 bottom-0 z-30
                min-[1400px]:relative min-[1400px]:top-auto min-[1400px]:right-auto min-[1400px]:bottom-auto min-[1400px]:z-auto
              "
            >
              <NotificationCenter onClose={() => setNotificationsOpen(false)} />
            </div>
          )}

          {isKogniiOpen && (
            <div
              className="
                w-[400px] border-l border-border bg-background transition-all duration-300 flex flex-col min-h-0 shrink-0
                fixed top-12 right-0 bottom-0 z-30
                min-[1400px]:relative min-[1400px]:top-auto min-[1400px]:right-auto min-[1400px]:bottom-auto min-[1400px]:z-auto
              "
            >
              <KogniiAssistant
                onClose={handleCloseKognii}
                strategySessionMode={strategySessionMode}
                activeView={activeView}
                kogniiActions={kogniiActions}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
