"use client";

import { useEffect, useState } from "react";
import api from "@/services/api";
import { BIDashboardTile } from "./tiles/BIDashboardTile";
import { CRMTile } from "./tiles/CRMTile";
import { KognaInsightsTile } from "./tiles/KognaInsightsTile";
import { ProjectManagementTile } from "./tiles/ProjectManagementTile";

// Map connector IDs used in tiles back to service names the API understands
const connectorToServiceMap: Record<string, string> = {
  jira: "jira",
  asana: "asana",
  "microsoft-excel": "microsoft-excel",
  google: "google",
  monday: "monday",
  smartsheet: "smartsheet",
  tableau: "tableau",
  "power-bi": "power-bi",
};

interface ConnectionInfo {
  status: string;
  connected_at?: string;
}

interface DashboardOverviewProps {
  user?: any;
  onOpenAssistant?: () => void;
}

const getUserDisplayName = (user: any) => {
  if (!user) return "there";
  const fullName = [user.first_name, user.second_name]
    .filter(Boolean)
    .join(" ");
  return fullName || user.email || "there";
};

export function DashboardOverview({
  user,
  onOpenAssistant,
}: DashboardOverviewProps) {
  const [connectionStatuses, setConnectionStatuses] = useState<
    Record<string, ConnectionInfo>
  >({});

  // Fetch connection statuses on mount
  useEffect(() => {
    const fetchStatuses = async () => {
      try {
        const statuses = await api.getConnectionStatus();
        setConnectionStatuses(statuses);
      } catch (err) {
        console.error("Failed to fetch connection statuses:", err);
      }
    };

    const timeoutId = setTimeout(fetchStatuses, 500);
    const interval = setInterval(fetchStatuses, 30000);
    return () => {
      clearTimeout(timeoutId);
      clearInterval(interval);
    };
  }, []);

  // Determine connected tool per category
  const biConnectorIds = [
    "microsoft-excel",
    "google",
    "tableau",
    "power-bi",
  ];
  const pmConnectorIds = ["jira", "asana", "monday", "smartsheet"];

  const findConnectedTool = (ids: string[]) => {
    for (const id of ids) {
      const svc = connectorToServiceMap[id] ?? id;
      if (connectionStatuses[svc]?.status === "connected") {
        return id;
      }
    }
    return null;
  };

  const connectedBI = findConnectedTool(biConnectorIds);
  const connectedPM = findConnectedTool(pmConnectorIds);

  // Handle connect
  const handleConnect = async (connectorId: string) => {
    try {
      const data = await api.getConnectUrl(connectorId);
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      console.error(`Failed to connect ${connectorId}:`, err);
    }
  };

  // Friendly names for display
  const toolNames: Record<string, string> = {
    jira: "Jira",
    asana: "Asana",
    monday: "Monday.com",
    smartsheet: "Smartsheet",
    "microsoft-excel": "Microsoft Excel",
    google: "Google Sheets",
    tableau: "Tableau",
    "power-bi": "Power BI",
  };

  return (
    <div className="p-6 space-y-6 h-full flex flex-col">
      {/* Greeting */}
      <div className="shrink-0">
        <h1 className="text-xl font-semibold text-foreground">
          Good morning, {getUserDisplayName(user)}
        </h1>
        <p className="text-sm text-muted-foreground">
          Here&apos;s your strategic overview and AI-powered insights
        </p>
      </div>

      {/* Main layout: Kogna Insights LEFT, 3 tiles RIGHT */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-6">
        {/* Left — Kogna Insights hero (full height) */}
        <KognaInsightsTile onOpenAssistant={onOpenAssistant} />

        {/* Right — 3 stacked tiles */}
        <div className="flex flex-col gap-5">
          <BIDashboardTile
            connectedTool={connectedBI ? toolNames[connectedBI] : null}
            onConnect={handleConnect}
          />
          <ProjectManagementTile
            connectedTool={connectedPM ? toolNames[connectedPM] : null}
            onConnect={handleConnect}
          />
          <CRMTile />
        </div>
      </div>
    </div>
  );
}
