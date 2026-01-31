import React, { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

declare global {
  namespace JSX {
    interface IntrinsicElements {
      'tableau-viz': any;
    }
  }
}

interface TableauTileProps {
  biSystemId: string;
  userId: string;
  onDelete?: () => void;
}

const TableauTile: React.FC<TableauTileProps> = ({ biSystemId, userId, onDelete }) => {
  const [config, setConfig] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Load Tableau Script
    const scriptUrl = "https://public.tableau.com/javascripts/api/tableau.embedding.3.latest.min.js";
    if (!document.querySelector(`script[src="${scriptUrl}"]`)) {
      const script = document.createElement("script");
      script.src = scriptUrl;
      script.type = "module";
      document.head.appendChild(script);
    }
  }, []);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const res = await fetch(`${API_URL}/api/bi-systems/${biSystemId}/url`, {
          headers: { 'X-User-ID': userId }
        });
        if (!res.ok) throw new Error("Failed to load Tableau config");
        const data = await res.json();
        setConfig(data);
      } catch (e: any) {
        console.error(e);
        setError(e.message);
      }
    };
    fetchConfig();
  }, [biSystemId, userId]);

  if (error) return <div className="p-4 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>;
  if (!config) return <div className="p-4 bg-gray-50 text-gray-400 rounded-lg animate-pulse">Loading Tableau...</div>;

  return (
    <div className="relative w-full h-full group">
       {onDelete && (
        <button 
          onClick={(e) => { e.stopPropagation(); onDelete(); }}
          className="absolute top-2 right-2 z-10 p-1.5 bg-white text-gray-400 hover:text-red-500 rounded-md shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      )}

      {/* @ts-ignore */}
      <tableau-viz 
        src={config.embedUrl}
        token={config.accessToken}
        toolbar="hidden"
        hide-tabs
        width="100%" 
        height="100%"
      />
    </div>
  );
};

export default TableauTile;