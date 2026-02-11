import {
  File,
  FileText,
  FileSpreadsheet,
  Presentation,
  Image,
  Video,
  Music,
} from "lucide-react";
import { Checkbox } from "../../../ui/checkbox";
import {
  formatFileSize,
  formatRelativeDate,
  getFileType,
} from "@/utils/fileHelpers";
import type { ConnectorFile } from "./types";

interface FileListItemProps {
  file: ConnectorFile;
  isSelected: boolean;
  onToggle: (fileId: string) => void;
}

const FILE_TYPE_ICONS: Record<string, React.ComponentType<any>> = {
  document: FileText,
  spreadsheet: FileSpreadsheet,
  presentation: Presentation,
  image: Image,
  video: Video,
  audio: Music,
  pdf: FileText,
  file: File,
};

export function FileListItem({
  file,
  isSelected,
  onToggle,
}: FileListItemProps) {
  const fileType = getFileType(file.mime_type);
  const IconComponent = FILE_TYPE_ICONS[fileType] || File;

  return (
    <div
      className="flex items-center gap-3 p-3 rounded-md hover:bg-gray-50 transition-colors cursor-pointer group"
      onClick={() => onToggle(file.id)}
    >
      {/* Checkbox */}
      <Checkbox
        checked={isSelected}
        onCheckedChange={() => onToggle(file.id)}
        onClick={(e) => e.stopPropagation()}
      />

      {/* File Icon */}
      <div className="flex-shrink-0">
        <IconComponent className="w-5 h-5 text-gray-600" />
      </div>

      {/* File Info */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">
          {file.name}
        </p>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span>{formatFileSize(file.size)}</span>
          {file.last_modified && (
            <>
              <span>•</span>
              <span>{formatRelativeDate(file.last_modified)}</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
