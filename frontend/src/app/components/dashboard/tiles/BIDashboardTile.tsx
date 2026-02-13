"use client";

import {
  BarChart3,
  FileSpreadsheet,
  LayoutDashboard,
  Table2,
} from "lucide-react";
import { useState } from "react";
import { DashboardTile } from "./DashboardTile";
import { TileExpandModal } from "./TileExpandModal";

const biConnectors = [
  {
    id: "microsoft-excel",
    name: "Excel",
    icon: <FileSpreadsheet className="h-8 w-8 text-green-700" />,
  },
  {
    id: "google",
    name: "Google Sheets",
    icon: <Table2 className="h-8 w-8 text-green-500" />,
  },
  {
    id: "tableau",
    name: "Tableau",
    icon: <BarChart3 className="h-8 w-8 text-blue-600" />,
  },
  {
    id: "power-bi",
    name: "Power BI",
    icon: <LayoutDashboard className="h-8 w-8 text-yellow-600" />,
  },
];

interface BIDashboardTileProps {
  connectedTool?: string | null;
  iframeUrl?: string;
  onConnect: (connectorId: string) => void;
}

export function BIDashboardTile({
  connectedTool,
  iframeUrl,
  onConnect,
}: BIDashboardTileProps) {
  const [expanded, setExpanded] = useState(false);

  const isConnected = !!connectedTool;

  const connectedContent = (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg bg-muted/50 p-3 space-y-1">
          <p className="text-[11px] text-muted-foreground">Revenue</p>
          <p className="text-lg font-semibold text-foreground">$1.2M</p>
        </div>
        <div className="rounded-lg bg-muted/50 p-3 space-y-1">
          <p className="text-[11px] text-muted-foreground">Growth</p>
          <p className="text-lg font-semibold text-emerald-600">+12.5%</p>
        </div>
      </div>
      <div className="h-24 rounded-lg bg-muted/30 flex items-center justify-center">
        <BarChart3 className="h-8 w-8 text-muted-foreground/40" />
      </div>
    </div>
  );

  return (
    <>
      <DashboardTile
        title="Executive Dashboard"
        subtitle="Connect your BI tool to view dashboards"
        isConnected={isConnected}
        connectedToolName={connectedTool ?? undefined}
        connectedContent={connectedContent}
        connectorOptions={biConnectors}
        onConnect={onConnect}
        onExpand={() => setExpanded(true)}
      />

      <TileExpandModal
        isOpen={expanded}
        onClose={() => setExpanded(false)}
        title="Executive Dashboard"
        toolName={connectedTool ?? undefined}
        iframeUrl={iframeUrl}
      />
    </>
  );
}
