/**
 * File utility functions for formatting and processing file metadata
 */

/**
 * Format file size from bytes to human-readable format
 * @param bytes - File size in bytes
 * @returns Formatted string (e.g., "2.5 MB")
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';

  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${Math.round(bytes / Math.pow(k, i) * 10) / 10} ${sizes[i]}`;
}

/**
 * Format date to relative time (e.g., "2 days ago")
 * @param dateString - ISO date string
 * @returns Relative time string
 */
export function formatRelativeDate(dateString?: string): string {
  if (!dateString) return 'Unknown';

  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;

  return date.toLocaleDateString();
}

/**
 * Get file type category from MIME type
 * @param mimeType - MIME type string
 * @returns File type category
 */
export function getFileType(mimeType?: string): string {
  if (!mimeType) return 'file';

  if (mimeType.includes('spreadsheet') || mimeType.includes('excel')) return 'spreadsheet';
  if (mimeType.includes('document') || mimeType.includes('word')) return 'document';
  if (mimeType.includes('presentation') || mimeType.includes('powerpoint')) return 'presentation';
  if (mimeType.includes('image')) return 'image';
  if (mimeType.includes('pdf')) return 'pdf';
  if (mimeType.includes('video')) return 'video';
  if (mimeType.includes('audio')) return 'audio';

  return 'file';
}

/**
 * Get icon name for file type (maps to lucide-react icon names)
 * @param mimeType - MIME type string
 * @returns Icon name for lucide-react
 */
export function getFileIcon(mimeType?: string): string {
  const fileType = getFileType(mimeType);

  switch (fileType) {
    case 'spreadsheet':
      return 'sheet';
    case 'document':
      return 'file-text';
    case 'presentation':
      return 'presentation';
    case 'image':
      return 'image';
    case 'pdf':
      return 'file-text';
    case 'video':
      return 'video';
    case 'audio':
      return 'music';
    default:
      return 'file';
  }
}
