"use client";
import React, { useState, useMemo, useEffect, useRef } from "react";
import { Sidebar } from "../sidebar";
import { MainDashboard } from "../MainDashboard";
import { KogniiAssistant } from "../kognii/KogniiAssistant";
import { NotificationCenter } from "../NotificationCenter";
import { useUser } from "../auth/UserContext";
import { useRouter } from "next/navigation";
import "gridstack/dist/gridstack.css";
import {
  GridStackNode,
  GridStack,
  GridStackElement,
  GridStackWidget,
} from 'gridstack';
import "gridstack/dist/gridstack.css";
import "path/to/demo.css";

interface DashboardLayoutProps {
  activeView: string;
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

export function DashboardLayout({ activeView }: DashboardLayoutProps) {
  const { isAuthenticated, loading } = useUser();
  const router = useRouter();

  const [isKogniiOpen, setIsKogniiOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [strategySessionMode, setStrategySessionMode] = useState(false);
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

  const [kogniiControlState, setKogniiControlState] = useState({
    shouldOpenObjectiveCreation: false,
    shouldNavigateToView: null as string | null,
    objectiveFormData: null as any,
    shouldHighlightElement: null as string | null,
    guidedTourActive: false,
    currentGuidanceStep: 0,
  });

  // init gridstack
  useEffect(()=>{
    if (whiteboardMode && gridRef.current && !gridInstanceRef.current){
      gridInstanceRef.current = GridStack.init({
        cellHeight: 70,
        margin: 10,
        float: true,
        animate: true,
        draggable:{
          handle:'.grid-stack-item-content'
        },
        resizable:{
            handles: 'e, se, s, sw, w'
        }
      }, gridRef.current);

      gridInstanceRef.current.on('change', (event, items)=>{
        if (items){
          setWidgets(prevWidgets =>{
            const updatedWidgets = [...prevWidgets];
            items.forEach((item:any)=>{
              const widgetIndex  = updatedWidgets.findIndex(w=>w.id === item.id);
              if(widgetIndex!==-1){
                updatedWidgets[widgetIndex]={
                  ...updatedWidgets[widgetIndex],
                  x: item.x || 0,
                  y: item.y || 0,
                  w: item.w || 0,
                  h: item.h || 0,
                };
              }
            });
            return updatedWidgets;
          });
        }
      });
    }
    return () => {
      if (gridInstanceRef.current) {
        gridInstanceRef.current.destroy(false);
        gridInstanceRef.current = null;
      }
    };
  }, [whiteboardMode]
  );

  // Redirect if not authenticated
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
  const addWidget = (type: GridWidget['type'])=>{
    const newWidget : GridWidget = {
      id:`widget${Date.now()}`,
      x: 0,
      y:0,
      w:4,
      h:3,
      content: `New ${type}`,
      type,
      title: `New ${type.charAt(0).toUpperCase()+ type.slice(1)}`
    };
    setWidgets(prev => [...prev, newWidget]);

    if(gridInstanceRef.current){
      gridInstanceRef.current.addWidget({
        id: newWidget.id,
        x: newWidget.x,
        y: newWidget.y,
        w: newWidget.w,
        h: newWidget.h,
      });
    }
  };

  const removeWidget = (id:string)=>{
    setWidgets(prev => prev.filter(w=>w.id !== id));
    if (gridInstanceRef.current){
      const element = document.getElementById(id);
      if(element){
        gridInstanceRef.current.removeWidget(element);
      }
    }
  };

  const saveLayout = ()=>{
    localStorage.setItem('dashboardLayout', JSON.stringify(widgets));
    alert('Layout Saved'); // for debugging 
  };

  const loadLayout = () => {
    const saved = localStorage.getItem('dashboardLayout');
    if(saved){
      setWidgets(JSON.parse(saved));
    }
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
