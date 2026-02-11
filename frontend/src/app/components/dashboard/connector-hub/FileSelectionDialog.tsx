"use client";

import { useState, useMemo, useEffect } from "react";
import { Search, Loader2, AlertCircle, FolderOpen } from "lucide-react";
import { Button } from "../../../ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../../../ui/dialog";
import { Input } from "../../../ui/input";
import { ScrollArea } from "../../../ui/scroll-area";
import { useConnectorFiles, useSyncConnector, useSelectedFiles } from "@/app/hooks/useDashboard";
import { FileListItem } from "./FileListItem";
import type { Connector } from "./types";

interface FileSelectionDialogProps {
  connector: Connector | null;
  isOpen: boolean;
  onClose: () => void;
  onSyncComplete?: () => void;
}

export function FileSelectionDialog({
  connector,
  isOpen,
  onClose,
  onSyncComplete,
}: FileSelectionDialogProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFileIds, setSelectedFileIds] = useState<Set<string>>(new Set());

  // Fetch files only when dialog is open
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useConnectorFiles(connector?.id || "", { enabled: isOpen && !!connector });

  // Fetch previously selected files
  const {
    data: selectedFilesData,
    isLoading: isLoadingSelection
  } = useSelectedFiles(connector?.id, { enabled: isOpen && !!connector });

  // Sync mutation
  const { mutate: syncFiles, isPending: isSyncing } = useSyncConnector();

  // Pre-populate with existing selection when dialog opens
  useEffect(() => {
    if (isOpen && selectedFilesData && selectedFilesData.file_ids) {
      setSelectedFileIds(new Set(selectedFilesData.file_ids));
    }
  }, [isOpen, selectedFilesData]);

  // Filter files based on search query
  const filteredFiles = useMemo(() => {
    if (!data?.files) return [];

    const query = searchQuery.toLowerCase();
    if (!query) return data.files;

    return data.files.filter((file) =>
      file.name.toLowerCase().includes(query)
    );
  }, [data?.files, searchQuery]);

  // Handle file selection toggle
  const handleToggle = (fileId: string) => {
    setSelectedFileIds((prev) => {
      const next = new Set(prev);
      if (next.has(fileId)) {
        next.delete(fileId);
      } else {
        next.add(fileId);
      }
      return next;
    });
  };

  // Handle select all / deselect all
  const handleSelectAll = () => {
    if (selectedFileIds.size === filteredFiles.length) {
      setSelectedFileIds(new Set());
    } else {
      setSelectedFileIds(new Set(filteredFiles.map((f) => f.id)));
    }
  };

  // Handle sync selected files
  const handleSyncSelected = () => {
    if (!connector) return;

    const fileIdsArray = Array.from(selectedFileIds);
    syncFiles(
      { provider: connector.id, fileIds: fileIdsArray },
      {
        onSuccess: () => {
          onSyncComplete?.();
          onClose();
          // Reset state
          setSelectedFileIds(new Set());
          setSearchQuery("");
        },
      }
    );
  };

  // Handle sync all files
  const handleSyncAll = () => {
    if (!connector) return;

    syncFiles(
      { provider: connector.id, fileIds: undefined }, // undefined = sync all
      {
        onSuccess: () => {
          onSyncComplete?.();
          onClose();
          // Reset state
          setSelectedFileIds(new Set());
          setSearchQuery("");
        },
      }
    );
  };

  // Reset state when dialog closes
  const handleClose = () => {
    setSelectedFileIds(new Set());
    setSearchQuery("");
    onClose();
  };

  if (!connector) return null;

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FolderOpen className="w-5 h-5" />
            Select Files from {connector.name}
          </DialogTitle>
          <DialogDescription>
            Choose specific files to sync, or sync all files from your {connector.name}
          </DialogDescription>

          {/* Current Selection Status */}
          {selectedFilesData && !isLoadingSelection && (
            <div className="text-sm text-muted-foreground mt-2 p-2 bg-blue-50 rounded-md">
              {selectedFilesData.selection_mode === 'all' && (
                <p>💡 Currently syncing <strong>all files</strong>. Select specific files below to limit the scope.</p>
              )}
              {selectedFilesData.selection_mode === 'specific' && (
                <p>✅ Currently syncing <strong>{selectedFilesData.file_ids?.length} selected file(s)</strong>.</p>
              )}
              {selectedFilesData.selection_mode === 'none' && (
                <p className="text-yellow-700">⚠️ No files selected. Select files to enable analysis.</p>
              )}
            </div>
          )}
        </DialogHeader>

        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            placeholder="Search files..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* File List */}
        <div className="flex-1 min-h-0">
          {(isLoading || isLoadingSelection) && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
            </div>
          )}

          {error && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <AlertCircle className="w-12 h-12 text-red-500 mb-3" />
              <p className="text-sm text-gray-600 mb-4">
                Failed to load files. Please try again.
              </p>
              <Button variant="outline" onClick={() => refetch()}>
                Retry
              </Button>
            </div>
          )}

          {!isLoading && !isLoadingSelection && !error && filteredFiles.length === 0 && searchQuery && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Search className="w-12 h-12 text-gray-300 mb-3" />
              <p className="text-sm text-gray-600">
                No files match your search
              </p>
            </div>
          )}

          {!isLoading && !isLoadingSelection && !error && filteredFiles.length === 0 && !searchQuery && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FolderOpen className="w-12 h-12 text-gray-300 mb-3" />
              <p className="text-sm text-gray-600">
                No files found in {connector.name}
              </p>
            </div>
          )}

          {!isLoading && !isLoadingSelection && !error && filteredFiles.length > 0 && (
            <div className="space-y-2">
              {/* Selection Header */}
              <div className="flex items-center justify-between pb-2 border-b">
                <button
                  onClick={handleSelectAll}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  {selectedFileIds.size === filteredFiles.length
                    ? "Deselect All"
                    : "Select All"}
                </button>
                <span className="text-sm text-gray-600">
                  {selectedFileIds.size} of {filteredFiles.length} selected
                </span>
              </div>

              {/* File List */}
              <ScrollArea className="h-[400px]">
                <div className="space-y-1">
                  {filteredFiles.map((file) => (
                    <FileListItem
                      key={file.id}
                      file={file}
                      isSelected={selectedFileIds.has(file.id)}
                      onToggle={handleToggle}
                    />
                  ))}
                </div>
              </ScrollArea>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isSyncing}
          >
            Cancel
          </Button>
          <Button
            variant="secondary"
            onClick={handleSyncAll}
            disabled={isSyncing || isLoading}
          >
            {isSyncing ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Syncing...
              </>
            ) : (
              "Sync All Files"
            )}
          </Button>
          <Button
            onClick={handleSyncSelected}
            disabled={selectedFileIds.size === 0 || isSyncing || isLoading}
          >
            {isSyncing ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Syncing...
              </>
            ) : (
              `Sync Selected (${selectedFileIds.size})`
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
