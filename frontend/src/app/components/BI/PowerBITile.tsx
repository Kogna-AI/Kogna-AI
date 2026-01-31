import React, { useEffect, useState } from 'react';
import { PowerBIEmbed } from 'powerbi-client-react';
import { models } from 'powerbi-client';

// Point this to your FastAPI backend
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface PowerBITileProps {
  biSystemId: string;
  userId: string;
  onDelete?: () => void;
}

const PowerBITile: React.FC<PowerBITileProps> = ({ biSystemId, userId, onDelete }) => {
  const [embedConfig, setEmbedConfig] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        // Fetch the specific token/url for this report
        const response = await fetch(`${API_URL}/api/bi-systems/${biSystemId}/url`, {
          headers: { 'X-User-ID': userId }
        });
        
        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || "Failed to load report");
        }

        const data = await response.json();
        setEmbedConfig(data);
      } catch (err: any) {
        console.error("Power BI Load Error:", err);
        setError(err.message);
      }
    };

    fetchConfig();
  }, [biSystemId, userId]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-red-50 text-red-600 p-4 rounded-lg">
        <p className="font-semibold mb-2">Unable to load chart</p>
        <p className="text-sm text-center">{error}</p>
        {error.includes("Connectors") && (
          <a href="/connectors" className="mt-4 px-4 py-2 bg-red-100 hover:bg-red-200 rounded text-sm font-medium">
            Go to Connectors
          </a>
        )}
      </div>
    );
  }

  if (!embedConfig) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50 rounded-lg animate-pulse">
        <span className="text-gray-400 font-medium">Loading Power BI...</span>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full group">
      {/* Delete Button */}
      {onDelete && (
        <button 
          onClick={(e) => { e.stopPropagation(); onDelete(); }}
          className="absolute top-2 right-2 z-10 p-1.5 bg-white text-gray-400 hover:text-red-500 rounded-md shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      )}

      <PowerBIEmbed
        embedConfig={{
          type: 'report',
          id: embedConfig.reportId,
          embedUrl: embedConfig.embedUrl,
          accessToken: embedConfig.accessToken,
          tokenType: models.TokenType.Aad, // User Owns Data uses 'Aad'
          settings: {
            panes: {
              filters: { visible: false },
              pageNavigation: { visible: false }
            },
            background: models.BackgroundType.Transparent,
          }
        }}
        cssClassName={"w-full h-full rounded-lg"}
      />
    </div>
  );
};

export default PowerBITile;