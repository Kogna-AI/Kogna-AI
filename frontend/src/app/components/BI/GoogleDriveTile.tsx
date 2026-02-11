import React, { useEffect, useState } from 'react';
import { FileText, Calendar, Database } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface GoogleDriveFile {
  id: string;
  file_name: string;
  file_path: string;
  file_size: number;
  source_id: string;
  source_metadata: any;
  last_ingested_at: string;
  chunk_count: number;
}

interface GoogleDriveTileProps {
  userId: string;
  onDelete?: () => void;
}

const GoogleDriveTile: React.FC<GoogleDriveTileProps> = ({ userId, onDelete }) => {
  const [files, setFiles] = useState<GoogleDriveFile[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFiles = async () => {
      try {
        const res = await fetch(`${API_URL}/api/bi-systems/google-drive/files`, {
          headers: { 'X-User-ID': userId }
        });

        if (!res.ok) {
          throw new Error("Failed to load Google Drive files");
        }

        const data = await res.json();
        setFiles(data);
      } catch (e: any) {
        console.error(e);
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };

    fetchFiles();
  }, [userId]);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return 'Unknown';
    }
  };

  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-600 rounded-lg text-sm h-full flex items-center justify-center">
        <div className="text-center">
          <p className="font-semibold mb-2">Unable to load files</p>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-4 bg-gray-50 text-gray-400 rounded-lg animate-pulse h-full flex items-center justify-center">
        Loading Google Drive files...
      </div>
    );
  }

  if (files.length === 0) {
    return (
      <div className="p-6 bg-gray-50 rounded-lg h-full flex items-center justify-center">
        <div className="text-center text-gray-500">
          <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="font-medium text-base">No files selected for analysis</p>
          <p className="text-sm mt-1">Select files from Google Drive to power AI insights</p>
          <a
            href="/connectors"
            className="inline-block mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700"
          >
            Select Files
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full group bg-white rounded-lg overflow-hidden">
      {onDelete && (
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(); }}
          className="absolute top-2 right-2 z-10 p-1.5 bg-white text-gray-400 hover:text-red-500 rounded-md shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}

      <div className="p-6 h-full flex flex-col">
        {/* Header */}
        <div className="mb-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-gray-700">
              Selected Files for Analysis
            </h3>
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-blue-50 rounded-full">
              <Database className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-700">{files.length}</span>
            </div>
          </div>
        </div>

        {/* All Files List */}
        <div className="flex-1 overflow-y-auto space-y-2.5">
          {files.map((file) => (
            <div
              key={file.id}
              className="flex items-start gap-3 p-3 hover:bg-gray-50 rounded-lg border border-gray-100 transition-colors"
            >
              <div className="p-2 bg-blue-50 rounded-lg shrink-0">
                <FileText className="w-5 h-5 text-blue-600" />
              </div>

              <div className="flex-1 min-w-0">
                <h4 className="font-semibold text-gray-900 truncate text-sm mb-1" title={file.file_name}>
                  {file.file_name}
                </h4>

                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-gray-600">
                  <span className="flex items-center gap-1">
                    <Database className="w-3.5 h-3.5 text-gray-400" />
                    {formatFileSize(file.file_size)}
                  </span>
                  <span className="text-gray-400">•</span>
                  <span>{file.chunk_count} chunks</span>
                  <span className="text-gray-400">•</span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-gray-400" />
                    {formatDate(file.last_ingested_at)}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default GoogleDriveTile;
