"use client";

import {
  Check,
  ChevronRight,
  FileText,
  FolderOpen,
  HardDrive,
  Loader2,
  ScanSearch,
  Shield,
  Sparkles,
  Upload,
} from "lucide-react";
import Image from "next/image";
import { useEffect, useState } from "react";
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

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface ConnectionInfo {
  status: string;
  connected_at?: string;
}

interface DriveFile {
  id: string;
  name: string;
  type: string;
  size: string;
  modified: string;
  selected: boolean;
}

/* ------------------------------------------------------------------ */
/*  Mock files (placeholder until backend file-list endpoints exist)   */
/* ------------------------------------------------------------------ */

const mockGoogleFiles: DriveFile[] = [
  { id: "g1", name: "Q4 Business Plan 2025.docx", type: "Document", size: "2.4 MB", modified: "Jan 28, 2026", selected: false },
  { id: "g2", name: "Market Research — APAC.pdf", type: "PDF", size: "8.1 MB", modified: "Jan 15, 2026", selected: false },
  { id: "g3", name: "Operations Playbook.docx", type: "Document", size: "1.7 MB", modified: "Dec 20, 2025", selected: false },
  { id: "g4", name: "Competitive Analysis 2026.xlsx", type: "Spreadsheet", size: "540 KB", modified: "Feb 1, 2026", selected: false },
  { id: "g5", name: "Marketing Campaign ROI.pdf", type: "PDF", size: "3.2 MB", modified: "Jan 10, 2026", selected: false },
];

const mockOneDriveFiles: DriveFile[] = [
  { id: "o1", name: "Strategic Roadmap H1 2026.pptx", type: "Presentation", size: "5.6 MB", modified: "Feb 2, 2026", selected: false },
  { id: "o2", name: "Annual Financial Report.xlsx", type: "Spreadsheet", size: "4.3 MB", modified: "Jan 30, 2026", selected: false },
  { id: "o3", name: "Customer Feedback Summary.docx", type: "Document", size: "980 KB", modified: "Jan 22, 2026", selected: false },
  { id: "o4", name: "Risk Assessment Matrix.xlsx", type: "Spreadsheet", size: "1.1 MB", modified: "Jan 18, 2026", selected: false },
];

/* ------------------------------------------------------------------ */
/*  File type icon helper                                              */
/* ------------------------------------------------------------------ */

function FileIcon({ type }: { type: string }) {
  const colors: Record<string, string> = {
    Document: "text-blue-500",
    PDF: "text-red-500",
    Spreadsheet: "text-green-600",
    Presentation: "text-orange-500",
  };
  return <FileText className={`h-4 w-4 ${colors[type] ?? "text-muted-foreground"}`} />;
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

interface DriveHubProps {
  onOpenAssistant?: () => void;
}

export function DriveHub({ onOpenAssistant }: DriveHubProps) {
  const [connectionStatuses, setConnectionStatuses] = useState<Record<string, ConnectionInfo>>({});
  const [googleFiles, setGoogleFiles] = useState<DriveFile[]>(mockGoogleFiles);
  const [oneDriveFiles, setOneDriveFiles] = useState<DriveFile[]>(mockOneDriveFiles);
  const [scanning, setScanning] = useState(false);
  const [scanComplete, setScanComplete] = useState(false);

  /* ---------- Fetch connection statuses ---------- */
  useEffect(() => {
    let cancelled = false;
    const fetch_ = async () => {
      try {
        const s = await api.getConnectionStatus();
        if (!cancelled) setConnectionStatuses(s);
      } catch { /* ignore */ }
    };
    const t = setTimeout(fetch_, 500);
    const i = setInterval(fetch_, 30_000);
    return () => { cancelled = true; clearTimeout(t); clearInterval(i); };
  }, []);

  const isGoogleConnected =
    connectionStatuses["google"]?.status === "connected" ||
    (connectionStatuses["google"]?.status === "available" && !!connectionStatuses["google"]?.connected_at);

  const isOneDriveConnected =
    connectionStatuses["microsoft"]?.status === "connected" ||
    (connectionStatuses["microsoft"]?.status === "available" && !!connectionStatuses["microsoft"]?.connected_at);

  /* ---------- Connect ---------- */
  const handleConnect = async (provider: string) => {
    try {
      const data = await api.getConnectUrl(provider);
      if (data.url) window.location.href = data.url;
    } catch (err) {
      console.error(`Failed to connect ${provider}:`, err);
    }
  };

  /* ---------- File selection ---------- */
  const toggleFile = (provider: "google" | "onedrive", fileId: string) => {
    const setter = provider === "google" ? setGoogleFiles : setOneDriveFiles;
    setter((prev) =>
      prev.map((f) => (f.id === fileId ? { ...f, selected: !f.selected } : f)),
    );
  };

  const selectedCount =
    googleFiles.filter((f) => f.selected).length +
    oneDriveFiles.filter((f) => f.selected).length;

  /* ---------- Mock scan ---------- */
  const handleScan = () => {
    setScanning(true);
    setScanComplete(false);
    // Simulate a 3-second scan
    setTimeout(() => {
      setScanning(false);
      setScanComplete(true);
    }, 3000);
  };

  /* ---------- Render ---------- */
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold text-foreground flex items-center gap-2">
          <HardDrive className="h-5 w-5 text-purple-600" />
          Data Drive
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Connect OneDrive or Google Drive to scan documents for Kogna&apos;s
          SWOT analysis — business plans, marketing research, operations docs
          and more.
        </p>
      </div>

      {/* Drive Connectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Google Drive */}
        <DriveConnectorCard
          name="Google Drive"
          icon={<FolderOpen className="h-5 w-5 text-green-500" />}
          isConnected={isGoogleConnected}
          onConnect={() => handleConnect("google")}
          files={googleFiles}
          onToggleFile={(id) => toggleFile("google", id)}
        />

        {/* OneDrive */}
        <DriveConnectorCard
          name="OneDrive"
          icon={<HardDrive className="h-5 w-5 text-blue-500" />}
          isConnected={isOneDriveConnected}
          onConnect={() => handleConnect("microsoft")}
          files={oneDriveFiles}
          onToggleFile={(id) => toggleFile("onedrive", id)}
        />
      </div>

      {/* Scan Action */}
      {(isGoogleConnected || isOneDriveConnected) && (
        <Card className="border-purple-200/60 bg-gradient-to-br from-purple-50/40 via-white to-blue-50/40">
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="rounded-lg bg-gradient-to-br from-purple-500/20 to-blue-500/20 p-2.5">
                  <ScanSearch className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground">
                    Kogna SWOT Analysis
                  </h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {selectedCount > 0
                      ? `${selectedCount} document${selectedCount > 1 ? "s" : ""} selected — Kogna will scan for Strengths, Weaknesses, Opportunities & Threats.`
                      : "Select documents above, then scan to generate a comprehensive SWOT analysis."}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {scanComplete && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5 text-purple-600 border-purple-200"
                    onClick={onOpenAssistant}
                  >
                    <Sparkles className="h-3.5 w-3.5" />
                    View in Kogna
                  </Button>
                )}

                <Button
                  size="sm"
                  className="gap-1.5 bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white"
                  disabled={selectedCount === 0 || scanning}
                  onClick={handleScan}
                >
                  {scanning ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      Scanning…
                    </>
                  ) : scanComplete ? (
                    <>
                      <Check className="h-3.5 w-3.5" />
                      Scan Complete
                    </>
                  ) : (
                    <>
                      <ScanSearch className="h-3.5 w-3.5" />
                      Run SWOT Scan
                    </>
                  )}
                </Button>
              </div>
            </div>

            {/* SWOT Preview */}
            {scanComplete && (
              <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { label: "Strengths", count: 4, color: "bg-emerald-100 text-emerald-700" },
                  { label: "Weaknesses", count: 2, color: "bg-red-100 text-red-700" },
                  { label: "Opportunities", count: 5, color: "bg-blue-100 text-blue-700" },
                  { label: "Threats", count: 3, color: "bg-amber-100 text-amber-700" },
                ].map((s) => (
                  <div
                    key={s.label}
                    className="rounded-lg border border-border bg-background p-3 text-center space-y-1"
                  >
                    <span className={`inline-block rounded-full px-2 py-0.5 text-[11px] font-semibold ${s.color}`}>
                      {s.label}
                    </span>
                    <p className="text-lg font-bold text-foreground">{s.count}</p>
                    <p className="text-[11px] text-muted-foreground">items found</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Info Banner */}
      <div className="flex items-start gap-3 rounded-lg border border-border bg-muted/30 p-4">
        <Shield className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
        <p className="text-xs text-muted-foreground leading-relaxed">
          Kogna only reads documents you explicitly select. Files are processed
          securely and never stored — only the generated analysis is saved to
          your workspace.
        </p>
      </div>
    </div>
  );
}

/* ================================================================== */
/*  DriveConnectorCard — sub-component                                 */
/* ================================================================== */

interface DriveConnectorCardProps {
  name: string;
  icon: React.ReactNode;
  isConnected: boolean;
  onConnect: () => void;
  files: DriveFile[];
  onToggleFile: (id: string) => void;
}

function DriveConnectorCard({
  name,
  icon,
  isConnected,
  onConnect,
  files,
  onToggleFile,
}: DriveConnectorCardProps) {
  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            {icon}
            <CardTitle className="text-sm">{name}</CardTitle>
          </div>
          {isConnected ? (
            <Badge
              variant="secondary"
              className="gap-1 text-[10px] bg-emerald-100 text-emerald-700 border-0"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Connected
            </Badge>
          ) : (
            <Button size="sm" variant="outline" onClick={onConnect} className="h-7 text-xs">
              Connect
            </Button>
          )}
        </div>
        <CardDescription className="text-xs">
          {isConnected
            ? "Select documents for Kogna to scan and analyse."
            : `Connect your ${name} account to import documents.`}
        </CardDescription>
      </CardHeader>

      {isConnected && (
        <CardContent className="flex-1 pt-0">
          <div className="rounded-lg border border-border divide-y divide-border">
            {files.map((file) => (
              <button
                key={file.id}
                type="button"
                onClick={() => onToggleFile(file.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 text-left transition-colors hover:bg-accent/40 ${
                  file.selected ? "bg-purple-50/60 dark:bg-purple-900/10" : ""
                }`}
              >
                {/* Checkbox */}
                <div
                  className={`flex h-4 w-4 shrink-0 items-center justify-center rounded border transition-colors ${
                    file.selected
                      ? "border-purple-500 bg-purple-500 text-white"
                      : "border-border"
                  }`}
                >
                  {file.selected && <Check className="h-3 w-3" />}
                </div>

                <FileIcon type={file.type} />

                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-foreground truncate">
                    {file.name}
                  </p>
                  <p className="text-[10px] text-muted-foreground">
                    {file.type} · {file.size} · {file.modified}
                  </p>
                </div>
              </button>
            ))}
          </div>

          <p className="text-[10px] text-muted-foreground mt-2 text-center">
            {files.filter((f) => f.selected).length} of {files.length} selected
          </p>
        </CardContent>
      )}

      {!isConnected && (
        <CardContent className="flex-1 flex items-center justify-center py-10">
          <div className="text-center space-y-3">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border-2 border-dashed border-border">
              <Upload className="h-5 w-5 text-muted-foreground" />
            </div>
            <p className="text-xs text-muted-foreground">
              Click <strong>Connect</strong> to link your {name}
            </p>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
