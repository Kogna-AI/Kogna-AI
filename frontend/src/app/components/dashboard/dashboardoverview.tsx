"use client";

import { useState, useEffect, useRef } from "react";
import { StarIcon } from "../../../../public/StarIcon";
import { Button } from "../../ui/button";
import ActionItems from "./ActionItems";
import {
  aiInsights,
  performanceData,
  strategicMetrics,
  upcomingActions,
} from "./dashboardData";
import InsightDetailsModal from "./InsightDetailsModal";
import InsightsList from "./InsightsList";
import MetricCard from "./MetricCard";
import PerformanceTrend from "./PerformanceTrend";
import StrategicGoals from "./StrategicGoals";
import { GridStack } from "gridstack";

interface DashboardOverviewProps {
  onStrategySession: () => void;
  user?: any;
}
interface GridWidget {
  id: string;
  x: number;
  y: number;
  w: number;
  h: number;
  componentType: 'metrics' | 'performance' | 'insights' | 'actions' | 'goals';
  title: string;
}



export function DashboardOverview({
  onStrategySession,
  user,
}: DashboardOverviewProps) {
  const [selectedInsight, setSelectedInsight] = useState<any>(null);
  const [isInsightModalOpen, setIsInsightModalOpen] = useState(false);

  const handleViewDetails = (insight: any) => {
    setSelectedInsight(insight);
    setIsInsightModalOpen(true);
  };

  const handleCloseInsightModal = () => {
    setIsInsightModalOpen(false);
    setSelectedInsight(null);
  };
  
 const [whiteboardMode, setWhiteBoardMode] = useState(false);  
  
  // Gridstack refrences
  const gridRef = useRef<HTMLDivElement>(null);
  const gridInstanceRef = useRef<GridStack | null> (null);
  const [widgets, setWidgets] = useState<GridWidget[]>([
    {
      id: 'widget-metrics',
      x: 0,
      y: 0,
      w: 12,
      h: 2,
      componentType: 'metrics',
      title: 'Strategic Metrics'
    },
    {
      id: 'widget-performance',
      x: 0,
      y: 2,
      w: 6,
      h: 4,
      componentType: 'performance',
      title: 'Performance Trend'
    },
    {
      id: 'widget-insights',
      x: 6,
      y: 2,
      w: 6,
      h: 4,
      componentType: 'insights',
      title: 'AI Insights'
    },
    {
      id: 'widget-actions',
      x: 0,
      y: 6,
      w: 4,
      h: 3,
      componentType: 'actions',
      title: 'Action Items'
    },
    {
      id: 'widget-goals',
      x: 4,
      y: 6,
      w: 8,
      h: 3,
      componentType: 'goals',
      title: 'Strategic Goals'
    }
  ]);


  useEffect(()=>{
    if (whiteboardMode && gridRef.current && !gridInstanceRef.current){
      gridInstanceRef.current = GridStack.init({
        cellHeight: 80,
        margin: 12,
        float: true,
        animate: true,
        column: 12,
        draggable:{
          handle: '.widget-drag-handle'
        },
        resizable:{
          handles:'e,se,s,sw,w'
        }
      }, gridRef.current);

      gridInstanceRef.current.on('change',(event,items)=>{
        if (items){
          setWidgets(prevWidgets => { 
            const updatedWidgets = [...prevWidgets];
            items.forEach((item:any)=> {
              const widgetIndex = updatedWidgets.findIndex(w=> w.id === item.id);
              if (widgetIndex!== -1) {
                updatedWidgets[widgetIndex]= {
                  ...updatedWidgets[widgetIndex],
                  x:item.x || 0,
                  y: item.y || 0,
                  w: item.w || 6,
                  h: item.h || 4,
                };
              }
            });
            return updatedWidgets;
          });
        }
      });
    }
    return ()=> {
      if (gridInstanceRef.current){
        gridInstanceRef.current.destroy(false);
        gridInstanceRef.current = null;
      }
    };
  }, [whiteboardMode]);

  const addWidget = (componentType: GridWidget['componentType']) =>{
    const titles = {
      metrics: 'Strategic Metrics',
      performance: 'Performance Trend',
      insights: 'AI Insights',
      actions: 'Action Items',
      goals: 'Strategic Goals'
    };
    const newWidget: GridWidget = {
      id: `widget-${Date.now}`,
      x: 0,
      y: 0,
      w: 6,
      h: 4, 
      componentType,
      title: titles[componentType]
    };
    setWidgets(prev => [...prev, newWidget]);

    if (gridInstanceRef.current){
      gridInstanceRef.current.addWidget({
        id: newWidget.id,
        x: newWidget.x,
        y: newWidget.y,
        w: newWidget.w,
        h: newWidget.h
      });
    }
  };

  const removeWidget = (id: string) =>{
    setWidgets(prev => prev.filter(w=> w.id !== id));
    if (gridInstanceRef.current){
      const element = document.getElementById(id);
      if (element){
        gridInstanceRef.current.removeWidget(element);
      }
    }
  };

  const saveLayout = () => {
    localStorage.setItem('whiteboardLayout', JSON.stringify(widgets));
    alert('Layout saved!');
  };

  const loadLayout = () => {
    const saved = localStorage.getItem('whiteboardLayout');
    if(saved){
      setWidgets(JSON.parse(saved));
    }
  }

  const renderComponents = (componentType: GridWidget['componentType']) =>{
    switch (componentType){
      case 'metrics': 
      return(
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 p-4">
          {strategicMetrics.map((metric, idx) => (
              <MetricCard key={idx} metric={metric} />
            ))}
        </div>
      );
      case 'performance':
        return <PerformanceTrend data={performanceData} />;
      case 'insights':
        return <InsightsList insights={aiInsights} onView={handleViewDetails}/>
      case 'actions':
        return <ActionItems actions={upcomingActions}/>
      case 'goals':
        return <StrategicGoals/>
      default:
        return null;
    }
  };

  if (whiteboardMode){
    return (
      <div className = "h-full flex flex-col">
        {/* whitebord toolbar*/}
        <div className="border-b p-3 flex items-center gap-3 bg-white shadow-sm shrink-0">
          <button
          onClick={()=> setWhiteBoardMode(false)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium text-sm">
            Exit Whiteboard
          </button>

          <div className="h-6 w-px bg-gray-300"/>
          <div className="flex gap-2 flex-wrap">
            <button
            onClick={()=> addWidget('metrics')}
            className="px-3 py-1.5 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700 transition"
            >
              + Metrics
            </button>
          <button
          onClick={()=> addWidget('actions')}
          className="px-3 py-1.5 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700 transition">
            + Actions
          </button>
          <button
          onClick={()=> addWidget('goals')}
          className="px-3 py-1.5 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700 transition">
            + Goals
          </button>
          <button
          onClick={()=> addWidget('insights')}
           className="px-3 py-1.5 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700 transition">
            + Insights
          </button>
          <button
          onClick={()=> addWidget('performance')}
           className="px-3 py-1.5 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700 transition">
            + Performance
          </button>
          </div>
          <div
          className="ml-auto flex gap-2">
            <button
            onClick={saveLayout}
            className="px-3 py-1.5 bg-gray-700 text-white rounded text-sm hover:bg-gray-800 transition">
              Save 
            </button>
          <button
          onClick={loadLayout}
          className="px-3 py-1.5 bg-gray-700 text-white rounded text-sm hover:bg-gray-800 transition">
            Load
          </button>
          </div>
          </div>
        {/* GridStack Whiteboard */}

        <div className="flex-1 overflow-auto bg-gradient-to-br from-gray-50 to-gray-100 p-4">
          <div ref={gridRef} className="grid-stack min-h-full">
            {widgets.map((widgets)=>(<div
                key={widgets.id}
                id={widgets.id}
                className="grid-stack-item"
                gs-x={widgets.x}
                gs-y={widgets.y}
                gs-w={widgets.w}
                gs-h={widgets.h}
              >
                <div className="grid-stack-item-content bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden flex flex-col h-full">
                  {/* Widget Header - Drag Handle */}
                  <div className="widget-drag-handle p-3 border-b bg-gradient-to-r from-gray-50 to-white flex justify-between items-center cursor-move hover:bg-gray-100 transition shrink-0">
                    <div className="flex items-center gap-2">
                      <div className="flex flex-col gap-0.5">
                        <div className="w-3 h-0.5 bg-gray-400 rounded" />
                        <div className="w-3 h-0.5 bg-gray-400 rounded" />
                      </div>
                      <h3 className="font-semibold text-sm text-gray-700">{widgets.title}</h3>
                    </div>
                    <button
                      onClick={() => removeWidget(widgets.id)}
                      className="text-gray-400 hover:text-red-600 text-lg font-bold transition"
                    >
                      ×
                    </button>
                  </div>

                  {/* Widget Content */}
                  <div className="flex-1 overflow-auto">
                    {renderComponents(widgets.componentType)}
                  </div>
                </div>
              </div>
            ))}     
          </div>
        </div>
        <InsightDetailsModal
        insight={selectedInsight}
        isOpen={isInsightModalOpen}
        onClose={handleCloseInsightModal}/>
        </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1>Good morning, {user?.name}</h1>
          <p className="text-muted-foreground">
            Here's your strategic overview and AI-powered insights
          </p>
        </div>
        <Button className="gap-2" onClick={onStrategySession}>
          <StarIcon className="w-4 h-4" />
          AI Strategy Session
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {strategicMetrics.map((metric, idx) => (
          <MetricCard key={idx} metric={metric} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PerformanceTrend data={performanceData} />
        <InsightsList insights={aiInsights} onView={handleViewDetails} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ActionItems actions={upcomingActions} />
        <StrategicGoals />
      </div>

      <InsightDetailsModal
        insight={selectedInsight}
        isOpen={isInsightModalOpen}
        onClose={handleCloseInsightModal}
      />
    </div>
  );
}
