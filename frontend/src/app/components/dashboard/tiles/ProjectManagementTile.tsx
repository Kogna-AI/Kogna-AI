"use client";

import {
  BarChart3,
  CheckCircle,
  FolderKanban,
  Target,
} from "lucide-react";
import { useState } from "react";
import { DashboardTile } from "./DashboardTile";
import { TileExpandModal } from "./TileExpandModal";

const pmConnectors = [
  {
    id: "jira",
    name: "Jira",
    icon: <Target className="h-8 w-8 text-blue-600" />,
  },
  {
    id: "asana",
    name: "Asana",
    icon: <CheckCircle className="h-8 w-8 text-red-500" />,
  },
  {
    id: "monday",
    name: "Monday",
    icon: <FolderKanban className="h-8 w-8 text-yellow-500" />,
  },
  {
    id: "smartsheet",
    name: "Smartsheet",
    icon: <BarChart3 className="h-8 w-8 text-blue-700" />,
  },
];

interface ProjectManagementTileProps {
  connectedTool?: string | null;
  iframeUrl?: string;
  onConnect: (connectorId: string) => void;
}

export function ProjectManagementTile({
  connectedTool,
  iframeUrl,
  onConnect,
}: ProjectManagementTileProps) {
  const [expanded, setExpanded] = useState(false);

  const isConnected = !!connectedTool;

  const connectedContent = (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-2">
        <div className="rounded-lg bg-muted/50 p-2.5 text-center space-y-0.5">
          <p className="text-[11px] text-muted-foreground">Open</p>
          <p className="text-lg font-semibold text-foreground">24</p>
        </div>
        <div className="rounded-lg bg-muted/50 p-2.5 text-center space-y-0.5">
          <p className="text-[11px] text-muted-foreground">In Progress</p>
          <p className="text-lg font-semibold text-blue-600">12</p>
        </div>
        <div className="rounded-lg bg-muted/50 p-2.5 text-center space-y-0.5">
          <p className="text-[11px] text-muted-foreground">Done</p>
          <p className="text-lg font-semibold text-emerald-600">38</p>
        </div>
      </div>
      <div className="h-20 rounded-lg bg-muted/30 flex items-center justify-center">
        <FolderKanban className="h-8 w-8 text-muted-foreground/40" />
      </div>
    </div>
  );

  return (
    <>
      <DashboardTile
        title="Project Management"
        subtitle="Connect Jira, Asana, or other PM tools"
        isConnected={isConnected}
        connectedToolName={connectedTool ?? undefined}
        connectedContent={connectedContent}
        connectorOptions={pmConnectors}
        onConnect={onConnect}
        onExpand={() => setExpanded(true)}
      />

      <TileExpandModal
        isOpen={expanded}
        onClose={() => setExpanded(false)}
        title="Project Management"
        toolName={connectedTool ?? undefined}
        iframeUrl={iframeUrl}
      />
    </>
  );
}
