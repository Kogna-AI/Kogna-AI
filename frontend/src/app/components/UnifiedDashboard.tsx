"use client";

import React, { useState, useEffect } from "react";
import { Plus, ExternalLink, X, Trash2, BarChart3, LayoutGrid } from "lucide-react";
import { Button } from "../ui/button";
import { useUser } from "./auth/UserContext";
import { DashboardOverview } from "./dashboard/dashboardoverview";
import PowerBITile from "./BI/PowerBITile";
import TableauTile from "./BI/TableauTile";
import GoogleDriveTile from "./BI/GoogleDriveTile";

// --- Types ---
interface BISystem {
  id: string;
  organization_id: string;
  bi_tool: string;
  base_url: string | null;
  report_id: string | null;
  workspace_id: string | null;
  embed_code: string | null;
  thumbnail_url: string | null;
  display_name: string;
  icon_emoji: string;
  is_active: boolean;
  last_accessed_at: string | null;
}

interface DashboardTile {
  id: string;
  name: string;
  icon: string;
  type: "kogna" | "external";
  url?: string;
  embedCode?: string;
  thumbnailUrl?: string;
  description: string;
  biTool?: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// --- Constants ---
const DEFAULT_THUMBNAILS: Record<string, string> = {
  kogna: "/KognaDashboardPreview.png",
  powerbi: "https://placehold.co/600x400/F2C811/black?text=Power+BI+Report",
  tableau: "https://placehold.co/600x400/E97627/white?text=Tableau+Viz",
  looker: "https://placehold.co/600x400/4285F4/white?text=Looker",
  metabase: "https://placehold.co/600x400/509EE3/white?text=Metabase",
  grafana: "https://placehold.co/600x400/F46800/white?text=Grafana",
  "google-drive": "https://placehold.co/600x400/4285F4/white?text=Google+Drive+Files",
};

export function UnifiedDashboard() {
  const { user } = useUser();
  const [biSystems, setBiSystems] = useState<BISystem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDashboard, setSelectedDashboard] = useState<DashboardTile | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  // 1. Kogna Native Dashboard
  const kognaDashboard: DashboardTile = {
    id: "kogna-dashboard",
    name: "Kogna Strategic Overview",
    icon: "📊",
    type: "kogna",
    thumbnailUrl: DEFAULT_THUMBNAILS.kogna,
    description: "AI-driven insights and strategy",
    biTool: "kogna"
  };

  useEffect(() => {
    if (user?.id) {
      loadBISystems();
    }
  }, [user]);

  const loadBISystems = async () => {
    try {
      const response = await fetch(`${API_URL}/api/bi-systems/`, {
        headers: { "X-User-ID": user?.id || "" }
      });

      if (response.ok) {
        const data = await response.json();
        setBiSystems(data);
      }
    } catch (error) {
      console.error("Failed to load BI systems:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteBISystem = async (biTool: string, e: React.MouseEvent) => {
    e.stopPropagation(); 
    if (!confirm(`Remove this BI system?`)) return;

    try {
      const response = await fetch(`${API_URL}/api/bi-systems/${biTool}`, {
        method: "DELETE",
        headers: { "X-User-ID": user?.id || "" }
      });

      if (response.ok) {
        loadBISystems(); 
      } else {
        alert("Failed to remove system.");
      }
    } catch (error) {
      console.error("Error removing BI system:", error);
    }
  };

  // 2. Map API Data to Tiles
  const externalDashboards: DashboardTile[] = biSystems.map((bi) => ({
    id: bi.id,
    name: bi.display_name,
    icon: bi.icon_emoji,
    type: "external",
    url: bi.base_url || undefined,
    embedCode: bi.embed_code || undefined,
    thumbnailUrl: bi.thumbnail_url || DEFAULT_THUMBNAILS[bi.bi_tool] || DEFAULT_THUMBNAILS['powerbi'],
    description: `External ${bi.bi_tool} Analytics`,
    biTool: bi.bi_tool
  }));

  const allDashboards = [kognaDashboard, ...externalDashboards];

  // ===============================================
  // VIEW MODE: The "Open" Dashboard State
  // ===============================================
  if (selectedDashboard) {
    return (
      <div className="fixed inset-0 z-50 bg-white flex flex-col">
        {/* Header */}
        <div className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm flex-shrink-0">
          <div className="flex items-center space-x-4">
            <div className="p-2 bg-gray-100 rounded-lg">
              <span className="text-xl">{selectedDashboard.icon}</span>
            </div>
            <div>
              <h2 className="font-bold text-gray-800 text-lg">{selectedDashboard.name}</h2>
              <p className="text-xs text-gray-500">Live Connection</p>
            </div>
          </div>
          <Button
            onClick={() => setSelectedDashboard(null)}
            variant="ghost"
            className="text-gray-500 hover:bg-gray-100 hover:text-gray-900"
          >
            <X className="w-5 h-5 mr-2" />
            Close Dashboard
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden bg-gray-50 relative">
          {selectedDashboard.type === "kogna" ? (
            <div className="h-full overflow-auto p-6">
              <DashboardOverview onStrategySession={() => {}} user={user} />
            </div>
          ) : selectedDashboard.biTool === "powerbi" ? (
            <div className="w-full h-full p-4">
               <PowerBITile 
                biSystemId={selectedDashboard.id} 
                userId={user?.id || ""} 
              />
            </div>
          ) : selectedDashboard.biTool === "tableau" ? (
            <div className="w-full h-full p-4">
              <TableauTile
                biSystemId={selectedDashboard.id}
                userId={user?.id || ""}
              />
            </div>
          ) : selectedDashboard.biTool === "google-drive" ? (
            <div className="w-full h-full p-4">
              <GoogleDriveTile
                userId={user?.id || ""}
              />
            </div>
          ) : selectedDashboard.embedCode ? (
            <div 
              className="w-full h-full"
              dangerouslySetInnerHTML={{ __html: selectedDashboard.embedCode }}
            />
          ) : (
            <iframe
              src={selectedDashboard.url}
              className="w-full h-full border-none"
              title={selectedDashboard.name}
            />
          )}
        </div>
      </div>
    );
  }

  // ===============================================
  // GRID MODE: The "Selection" Screen
  // ===============================================
  return (
    <div className="p-8 min-h-screen bg-gray-50/50">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <LayoutGrid className="w-6 h-6 text-purple-600" />
              Unified Analytics
            </h1>
            <p className="text-gray-500 mt-1">Manage your Kogna insights and external BI reports</p>
          </div>
          <Button
            onClick={() => setShowAddModal(true)}
            className="bg-purple-600 hover:bg-purple-700 text-white shadow-sm"
          >
            <Plus className="w-4 h-4 mr-2" />
            Connect Report
          </Button>
        </div>

        {/* Grid */}
        {loading ? (
          <div className="flex justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {allDashboards.map((dashboard) => (
              <div
                key={dashboard.id}
                onClick={() => setSelectedDashboard(dashboard)}
                className="group bg-white rounded-xl border border-gray-200 hover:border-purple-300 hover:shadow-lg transition-all duration-200 cursor-pointer overflow-hidden flex flex-col"
              >
                {/* Thumbnail */}
                <div className="relative h-48 bg-gray-100 overflow-hidden border-b border-gray-100">
                  <img
                    src={dashboard.thumbnailUrl}
                    alt={dashboard.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  <div className="absolute top-3 left-3 px-2 py-1 bg-white/90 backdrop-blur rounded-md text-xs font-medium shadow-sm flex items-center gap-1">
                    <span>{dashboard.icon}</span>
                    <span className="capitalize">{dashboard.biTool}</span>
                  </div>
                  {dashboard.type === "external" && (
                    <button
                      onClick={(e) => handleDeleteBISystem(dashboard.biTool || "", e)}
                      className="absolute top-3 right-3 p-2 bg-white/90 text-red-500 rounded-md opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>

                {/* Info */}
                <div className="p-5 flex-1 flex flex-col justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1 group-hover:text-purple-600 transition-colors">
                      {dashboard.name}
                    </h3>
                    <p className="text-sm text-gray-500 line-clamp-2">{dashboard.description}</p>
                  </div>
                  <div className="mt-4 flex items-center text-sm font-medium text-purple-600 opacity-0 group-hover:opacity-100 transition-opacity transform translate-y-2 group-hover:translate-y-0">
                    View Report <ExternalLink className="w-3 h-3 ml-1" />
                  </div>
                </div>
              </div>
            ))}

            {/* Add New Button */}
            <button
              onClick={() => setShowAddModal(true)}
              className="border-2 border-dashed border-gray-200 rounded-xl flex flex-col items-center justify-center p-8 hover:border-purple-300 hover:bg-purple-50/50 transition-all group min-h-[300px]"
            >
              <div className="w-12 h-12 bg-gray-50 rounded-full flex items-center justify-center mb-3 group-hover:bg-purple-100 transition-colors">
                <Plus className="w-6 h-6 text-gray-400 group-hover:text-purple-600" />
              </div>
              <span className="font-medium text-gray-600 group-hover:text-purple-700">Add New Connection</span>
            </button>
          </div>
        )}

        {showAddModal && (
          <AddBISystemModal
            onClose={() => setShowAddModal(false)}
            onSuccess={() => {
              setShowAddModal(false);
              loadBISystems();
            }}
            userId={user?.id || ""}
          />
        )}
      </div>
    </div>
  );
}

// ===============================================
// ADD BI SYSTEM MODAL (THE MAGIC DROPDOWN)
// ===============================================

interface AddBISystemModalProps {
  onClose: () => void;
  onSuccess: () => void;
  userId: string;
}

function AddBISystemModal({ onClose, onSuccess, userId }: AddBISystemModalProps) {
  const [availableTools, setAvailableTools] = useState<any[]>([]);
  const [selectedTool, setSelectedTool] = useState("");
  
  // Power BI State
  const [pbiReports, setPbiReports] = useState<any[]>([]);
  const [isLoadingReports, setIsLoadingReports] = useState(false);
  
  // Form Fields
  const [reportId, setReportId] = useState("");
  const [workspaceId, setWorkspaceId] = useState("");
  const [embedCode, setEmbedCode] = useState("");
  const [customUrl, setCustomUrl] = useState("");
  const [thumbnailUrl, setThumbnailUrl] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAvailableTools();
  }, []);

  // Fetch Reports when Power BI is selected
  useEffect(() => {
    if (selectedTool === 'powerbi') {
      fetchPowerBIReports();
    }
  }, [selectedTool]);

  const loadAvailableTools = async () => {
    try {
      const response = await fetch(`${API_URL}/api/bi-systems/available`);
      if (response.ok) {
        const data = await response.json();
        setAvailableTools(data);
      }
    } catch (error) {
      console.error("Failed to load BI tools:", error);
    }
  };

  const fetchPowerBIReports = async () => {
    setIsLoadingReports(true);
    setPbiReports([]); // Clear previous
    try {
      const response = await fetch(`${API_URL}/api/bi-systems/powerbi/reports`, {
        headers: { "X-User-ID": userId }
      });
      if (response.ok) {
        const data = await response.json();
        setPbiReports(data);
      } else {
        console.error("Failed to fetch reports");
      }
    } catch (error) {
      console.error("Failed to fetch PBI reports", error);
    } finally {
      setIsLoadingReports(false);
    }
  };

  const handleReportSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedId = e.target.value;
    setReportId(selectedId);
    
    // Auto-fill Workspace ID
    const report = pbiReports.find(r => r.id === selectedId);
    if (report) {
      setWorkspaceId(report.workspaceId || "");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        bi_tool: selectedTool,
        thumbnail_url: thumbnailUrl || null,
        // Send IDs only for Power BI
        report_id: selectedTool === 'powerbi' ? reportId : null,
        workspace_id: selectedTool === 'powerbi' ? workspaceId : null,
        custom_url: selectedTool === 'tableau' ? customUrl : null,
        embed_code: !['powerbi', 'tableau'].includes(selectedTool) ? embedCode : null,
      };

      const response = await fetch(`${API_URL}/api/bi-systems/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-ID": userId
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        onSuccess();
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail}`);
      }
    } catch (error) {
      console.error(error);
      alert("Failed to add BI system.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100] p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full overflow-hidden flex flex-col max-h-[90vh]">
        <div className="p-5 border-b border-gray-100 flex justify-between items-center bg-gray-50">
          <h2 className="text-lg font-bold text-gray-800">Add Data Connection</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Platform</label>
            <select
              value={selectedTool}
              onChange={(e) => setSelectedTool(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
              required
            >
              <option value="">Select Platform...</option>
              {availableTools.map((tool) => (
                <option key={tool.id} value={tool.id}>
                  {tool.icon} {tool.name}
                </option>
              ))}
            </select>
          </div>

          {/* === DYNAMIC POWER BI DROPDOWN === */}
          {selectedTool === 'powerbi' && (
            <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-100 space-y-3">
              <div className="flex items-center justify-between text-yellow-800 font-medium text-sm">
                <span className="flex items-center gap-2"><BarChart3 className="w-4 h-4" /> Select Report</span>
                {isLoadingReports && <span className="text-xs animate-pulse">Loading reports...</span>}
              </div>

              {pbiReports.length > 0 ? (
                <div>
                  <label className="block text-sm text-gray-700 mb-1">Available Reports</label>
                  <select
                    value={reportId}
                    onChange={handleReportSelect}
                    className="w-full px-3 py-2 bg-white border border-gray-200 rounded text-sm focus:border-yellow-500 outline-none"
                    required
                  >
                    <option value="">-- Choose a Report --</option>
                    {pbiReports.map((report) => (
                      <option key={report.id} value={report.id}>
                        {report.name}
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div className="text-sm text-gray-500 bg-white p-3 rounded border border-gray-200">
                  {isLoadingReports ? "Fetching..." : (
                    <span>
                      No reports found. Please ensure you are <a href="/connectors" className="text-purple-600 underline">connected to Microsoft</a> and have permissions.
                    </span>
                  )}
                </div>
              )}
              
              {/* Read-Only inputs for debug/confirmation */}
              <div className="grid grid-cols-2 gap-2 opacity-60">
                 <div>
                    <label className="block text-[10px] uppercase font-bold text-gray-400">Report ID</label>
                    <input 
                      value={reportId} 
                      readOnly 
                      className="w-full px-2 py-1 bg-gray-50 text-xs border border-gray-200 rounded text-gray-500" 
                    />
                 </div>
                 <div>
                    <label className="block text-[10px] uppercase font-bold text-gray-400">Workspace ID</label>
                    <input 
                      value={workspaceId} 
                      readOnly 
                      className="w-full px-2 py-1 bg-gray-50 text-xs border border-gray-200 rounded text-gray-500" 
                    />
                 </div>
              </div>
            </div>
          )}

          {/* Tableau Section */}
          {selectedTool === 'tableau' && (
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 space-y-3">
              <h3 className="text-blue-900 font-medium text-sm">Tableau Cloud</h3>
               <div>
                <label className="block text-sm text-gray-700 mb-1">Embed URL</label>
                <input
                  required
                  value={customUrl}
                  onChange={(e) => setCustomUrl(e.target.value)}
                  placeholder="https://prod-useast-b.online.tableau.com/..."
                  className="w-full px-3 py-2 bg-white border border-gray-200 rounded text-sm"
                />
              </div>
            </div>
          )}

          {/* Google Drive Section */}
          {selectedTool === 'google-drive' && (
            <div className="bg-green-50 p-4 rounded-lg border border-green-100 space-y-3">
              <h3 className="text-green-900 font-medium text-sm">📁 Google Drive Data Source</h3>
              <p className="text-sm text-gray-700">
                This tile will display files from your Google Drive that have been ingested for data analysis.
                Make sure you have connected your Google Drive account in the{' '}
                <a href="/connectors" className="text-purple-600 underline font-medium">
                  Connectors
                </a>{' '}
                page.
              </p>
              <div className="bg-white p-3 rounded border border-green-200">
                <p className="text-xs text-gray-600">
                  <strong>Note:</strong> The tile will show the most recently analyzed file and a list of other files from Google Drive.
                </p>
              </div>
            </div>
          )}

          {/* Generic Embed Code */}
          {selectedTool && !['powerbi', 'tableau', 'google-drive'].includes(selectedTool) && (
             <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Embed Code</label>
              <textarea
                required
                value={embedCode}
                onChange={(e) => setEmbedCode(e.target.value)}
                placeholder='<iframe src="..." ...></iframe>'
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Thumbnail URL (Optional)</label>
            <input
              type="url"
              value={thumbnailUrl}
              onChange={(e) => setThumbnailUrl(e.target.value)}
              placeholder="https://..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>

          <div className="pt-4 flex gap-3">
            <Button type="button" onClick={onClose} variant="ghost" className="flex-1">
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!selectedTool || loading || (selectedTool === 'powerbi' && !reportId) || (selectedTool === 'tableau' && !customUrl)}
              className="flex-1 bg-purple-600 hover:bg-purple-700 text-white"
            >
              {loading ? "Saving..." : "Add Connection"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}