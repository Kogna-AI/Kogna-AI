"use client";

import {
  BarChart3,
  CheckCircle2,
  Crown,
  FolderOpen,
  Plug,
  Shield,
  Sparkles,
  Zap,
} from "lucide-react";
import {
  type JSXElementConstructor,
  type Key,
  type ReactElement,
  type ReactNode,
  type ReactPortal,
  useEffect,
  useState,
} from "react";
import api from "@/services/api";
import { Badge } from "../../ui/badge";
import { Button } from "../../ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../ui/card";
import { connectors } from "./connector-hub/constants";
import type { Connector } from "./connector-hub/types";
import { getStatusIcon, getStatusText } from "./connector-hub/utils";
import { FileSelectionDialog } from "./connector-hub/FileSelectionDialog";

// Map connector IDs to service names in the database
const connectorToServiceMap: Record<string, string> = {
  jira: "jira",
  google: "google",
  asana: "asana",
  "microsoft-excel": "microsoft-excel",
  "microsoft-project": "microsoft-project",
  "microsoft-teams": "microsoft-teams",
  microsoft: "microsoft",
  smartsheet: "smartsheet",
  github: "github",
  notion: "notion",
  slack: "slack",
};

interface ConnectionInfo {
  status: string;
  connected_at?: string;
  created_at?: string;
  next_reconnect?: string;
}

export function DataConnectorHub() {
  const [connectingIds, setConnectingIds] = useState<Set<string>>(new Set());
  const [connectionStatuses, setConnectionStatuses] = useState<
    Record<string, ConnectionInfo>
  >({});
  const [fileSelectionConnector, setFileSelectionConnector] = useState<Connector | null>(null);

  const kognaCoreConnector = connectors.find(
    (c: { id: string }) => c.id === "kognacore",
  );

  // Count active connections
  const activeConnectionsCount = Object.values(connectionStatuses).filter(
    (info) => info.status === "connected",
  ).length;

  useEffect(() => {
    const fetchConnectionStatus = async () => {
      try {
        const statuses = await api.getConnectionStatus();
        console.log("Connection statuses received:", statuses);
        setConnectionStatuses(statuses);
      } catch (error) {
        console.error("Failed to fetch connection status:", error);
      }
    };

    // Add a small delay to ensure auth is ready
    const timeoutId = setTimeout(() => {
      fetchConnectionStatus();
    }, 500);

    // Refresh status every 30 seconds
    const interval = setInterval(fetchConnectionStatus, 30000);

    return () => {
      clearTimeout(timeoutId);
      clearInterval(interval);
    };
  }, []);

  const handleConnect = async (connector: Connector) => {
    setConnectingIds((prev) => new Set(prev).add(connector.id));
    try {
      console.log(`Getting connect URL for ${connector.id}...`);
      const data = await api.getConnectUrl(connector.id);

      if (!data.url) {
        throw new Error("No authorization URL received from server");
      }

      console.log(`Redirecting to: ${data.url}`);
      window.location.href = data.url;
    } catch (err) {
      console.error(`Failed to connect ${connector.id}:`, err);
      alert(
        `Failed to connect ${connector.name}: ${err instanceof Error ? err.message : "Unknown error"}`,
      );
      setConnectingIds((prev) => {
        const next = new Set(prev);
        next.delete(connector.id);
        return next;
      });
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1>Data Connectors</h1>
          <p className="text-muted-foreground">
            Connect your existing tools and data sources for comprehensive
            project insights
          </p>
        </div>
      </div>

      {/* KognaCore Highlight */}
      {/* {kognaCoreConnector && (
        <Card className="border-2 border-amber-200 bg-gradient-to-r from-amber-50 via-orange-50 to-amber-50 shadow-lg">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center">
                  <Crown className="w-6 h-6 text-white" />
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-lg font-semibold">
                      {kognaCoreConnector.name}
                    </h3>
                    <Badge className="bg-gradient-to-r from-amber-400 to-orange-500 text-white">
                      <Sparkles className="w-3 h-3 mr-1" />
                      Recommended
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">
                    {kognaCoreConnector.description}
                  </p>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Shield className="w-3 h-3" />
                      Enterprise Security
                    </span>
                    <span className="flex items-center gap-1">
                      <Zap className="w-3 h-3" />
                      Real-time Sync
                    </span>
                    <span className="flex items-center gap-1">
                      <BarChart3 className="w-3 h-3" />
                      Advanced Analytics
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )} */}

      {/* Integration Stats */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Integration Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {activeConnectionsCount}
              </div>
              <div className="text-sm text-muted-foreground">
                Active Connections
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">24/7</div>
              <div className="text-sm text-muted-foreground">
                Real-time Monitoring
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">99.9%</div>
              <div className="text-sm text-muted-foreground">Uptime</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">30min</div>
              <div className="text-sm text-muted-foreground">Refresh Time</div>
            </div>
          </div>
        </CardContent>
      </Card>
      {/* Connectors Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {connectors
          .filter((c: { id: string }) => c.id !== "kognacore")
          .map(
            (connector: {
              id: Key | null | undefined;
              icon:
                | string
                | number
                | bigint
                | boolean
                | ReactElement<unknown, string | JSXElementConstructor<any>>
                | Iterable<ReactNode>
                | ReactPortal
                | Promise<
                    | string
                    | number
                    | bigint
                    | boolean
                    | ReactPortal
                    | ReactElement<unknown, string | JSXElementConstructor<any>>
                    | Iterable<ReactNode>
                    | null
                    | undefined
                  >
                | null
                | undefined;
              name:
                | string
                | number
                | bigint
                | boolean
                | ReactElement<unknown, string | JSXElementConstructor<any>>
                | Iterable<ReactNode>
                | ReactPortal
                | Promise<
                    | string
                    | number
                    | bigint
                    | boolean
                    | ReactPortal
                    | ReactElement<unknown, string | JSXElementConstructor<any>>
                    | Iterable<ReactNode>
                    | null
                    | undefined
                  >
                | null
                | undefined;
              status: string;
              description:
                | string
                | number
                | bigint
                | boolean
                | ReactElement<unknown, string | JSXElementConstructor<any>>
                | Iterable<ReactNode>
                | ReactPortal
                | Promise<
                    | string
                    | number
                    | bigint
                    | boolean
                    | ReactPortal
                    | ReactElement<unknown, string | JSXElementConstructor<any>>
                    | Iterable<ReactNode>
                    | null
                    | undefined
                  >
                | null
                | undefined;
              features: any[];
            }) =>
              (() => {
                const connectorId = String(connector.id);
                const serviceName =
                  connectorToServiceMap[connectorId] || connectorId;
                const connectionInfo = connectionStatuses[serviceName];
                const actualStatus = connectionInfo?.status || connector.status;
                const isConnected = actualStatus === "connected";

                // Format dates - converts UTC to user's local timezone
                const formatDate = (dateStr?: string) => {
                  if (!dateStr) return null;
                  try {
                    console.log(`Formatting date: ${dateStr}`);
                    let utcDate: Date;
                    
                    // Handle different timestamp formats from backend
                    if (dateStr.includes('T')) {
                      // ISO format: "2026-01-15T21:52:13" or "2026-01-15T21:52:13.184097"
                      // Backend might send this for next_reconnect
                      if (!dateStr.endsWith('Z') && !dateStr.includes('+')) {
                        // Add Z to indicate UTC if not present
                        utcDate = new Date(dateStr + 'Z');
                      } else {
                        utcDate = new Date(dateStr);
                      }
                    } else if (dateStr.includes(' ')) {
                      // Database format: "2026-01-15 21:52:13.184097" (stored as UTC)
                      // Replace space with T and add Z to indicate UTC
                      const cleaned = dateStr.split('+')[0]; // Remove +00 if present
                      const withoutMicroseconds = cleaned.split('.')[0]; // Remove microseconds
                      utcDate = new Date(withoutMicroseconds.replace(' ', 'T') + 'Z');
                    } else {
                      utcDate = new Date(dateStr);
                    }
                    
                    // Check if date is valid
                    if (isNaN(utcDate.getTime())) {
                      console.warn(`Invalid date: ${dateStr}`);
                      return null;
                    }
                    
                    console.log(`UTC date object: ${utcDate.toISOString()}`);
                    console.log(`Local timezone offset: ${utcDate.getTimezoneOffset()} minutes`);
                    
                    // Format in user's local timezone
                    const formatted = utcDate.toLocaleString(undefined, {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                      hour12: true,
                    });
                    
                    console.log(`Formatted: ${formatted}`);
                    return formatted;
                  } catch (error) {
                    console.error(`Error formatting date: ${dateStr}`, error);
                    return null;
                  }
                };

                const connectedAt = formatDate(connectionInfo?.connected_at);
                const nextReconnect = formatDate(
                  connectionInfo?.next_reconnect,
                );

                return (
                  <Card
                    key={connector.id}
                    className="hover:shadow-md transition-shadow cursor-pointer group"
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          {connector.icon}
                          <CardTitle className="text-base">
                            {connector.name}
                          </CardTitle>
                        </div>
                        <div className="flex items-center gap-1">
                          {getStatusIcon(actualStatus)}
                          <span className="text-xs text-muted-foreground">
                            {getStatusText(actualStatus)}
                          </span>
                        </div>
                      </div>
                      <CardDescription className="text-sm">
                        {connector.description}
                      </CardDescription>
                    </CardHeader>

                    <CardContent className="pt-0">
                      <div className="flex flex-col h-full space-y-3">
                        {isConnected && connectedAt && (
                          <div className="text-xs space-y-1">
                            <div className="flex items-center gap-1 text-green-600">
                              <span className="font-medium">Connected:</span>
                              <span>{connectedAt}</span>
                            </div>
                            {nextReconnect && (
                              <div className="flex items-center gap-1 text-muted-foreground">
                                <span className="font-medium">
                                  Next refresh:
                                </span>
                                <span>{nextReconnect}</span>
                              </div>
                            )}
                          </div>
                        )}

                        {!isConnected && connectedAt && (
                          <div className="text-xs text-muted-foreground">
                            <span className="font-medium">Last connected:</span>{" "}
                            {connectedAt}
                          </div>
                        )}

                        <div className="flex flex-wrap gap-1 flex-1">
                          {connector.features
                            .slice(0, 2)
                            .map(
                              (
                                feature:
                                  | string
                                  | number
                                  | bigint
                                  | boolean
                                  | ReactElement<
                                      unknown,
                                      string | JSXElementConstructor<any>
                                    >
                                  | Iterable<ReactNode>
                                  | ReactPortal
                                  | Promise<
                                      | string
                                      | number
                                      | bigint
                                      | boolean
                                      | ReactPortal
                                      | ReactElement<
                                          unknown,
                                          string | JSXElementConstructor<any>
                                        >
                                      | Iterable<ReactNode>
                                      | null
                                      | undefined
                                    >
                                  | null
                                  | undefined,
                                index: Key | null | undefined,
                              ) => (
                                <Badge
                                  key={index}
                                  variant="secondary"
                                  className="text-xs"
                                >
                                  {feature}
                                </Badge>
                              ),
                            )}
                          {connector.features.length > 2 && (
                            <Badge variant="outline" className="text-xs">
                              +{connector.features.length - 2} more
                            </Badge>
                          )}
                        </div>

                        <div className="mt-auto pt-2">
                          {isConnected ? (
                            // Google Drive gets special file selection button
                            connectorId === "google" ? (
                              <div className="flex gap-2">
                                <Button
                                  className="flex-1 bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-600 hover:text-white hover:border-blue-600 transition-all duration-200"
                                  variant="outline"
                                  onClick={() => setFileSelectionConnector(connector as Connector)}
                                >
                                  <FolderOpen className="w-4 h-4 mr-2" />
                                  Select Files
                                </Button>
                                <Button
                                  className="flex-1 bg-green-50 text-green-700 border-green-200 hover:bg-green-600 hover:text-white hover:border-green-600 transition-all duration-200"
                                  variant="outline"
                                  onClick={() => handleConnect(connector as Connector)}
                                  disabled={connectingIds.has(connectorId)}
                                >
                                  <CheckCircle2 className="w-4 h-4 mr-2" />
                                  Reconnect
                                </Button>
                              </div>
                            ) : (
                              // Other connectors get standard reconnect button
                              <Button
                                className="w-full bg-green-50 text-green-700 border-green-200 hover:bg-green-600 hover:text-white hover:border-green-600 transition-all duration-200 group/btn shadow-sm hover:shadow-md"
                                variant="outline"
                                onClick={() =>
                                  handleConnect(connector as Connector)
                                }
                                disabled={connectingIds.has(connectorId)}
                              >
                                <CheckCircle2 className="w-4 h-4 mr-2 group-hover/btn:hidden" />
                                <Plug className="w-4 h-4 mr-2 hidden group-hover/btn:block group-hover/btn:animate-pulse" />
                                <span className="font-medium group-hover/btn:hidden">
                                  Connected
                                </span>
                                <span className="font-medium hidden group-hover/btn:inline">
                                  Reconnect
                                </span>
                              </Button>
                            )
                          ) : (
                            <Button
                              className="w-full group-hover:bg-primary group-hover:text-primary-foreground transition-colors"
                              variant="default"
                              onClick={() =>
                                handleConnect(connector as Connector)
                              }
                              disabled={connectingIds.has(connectorId)}
                            >
                              <Plug className="w-4 h-4 mr-2" />
                              {connectingIds.has(connectorId)
                                ? "Connecting..."
                                : "Connect"}
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })(),
          )}
      </div>

      {/* File Selection Dialog */}
      <FileSelectionDialog
        connector={fileSelectionConnector}
        isOpen={!!fileSelectionConnector}
        onClose={() => setFileSelectionConnector(null)}
        onSyncComplete={() => {
          // Optionally refresh connection status or show success message
          setFileSelectionConnector(null);
        }}
      />
    </div>
  );
}
