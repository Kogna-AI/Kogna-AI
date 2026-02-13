import { KogniiThinkingIcon } from "../../../../public/KogniiThinkingIcon"
import { Button } from "@/app/ui/button"
import { X, Maximize2, Minimize2 } from "lucide-react"

interface HeaderProps {
  onClose: () => void;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
}

export default function Header({ onClose, isExpanded, onToggleExpand }: HeaderProps) {
  return (
    <div className="p-4 border-b border-border">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
            <KogniiThinkingIcon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold">Kogna Assistant</h3>
            <p className="text-xs text-muted-foreground">Strategic AI companion</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {onToggleExpand && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggleExpand}
              title={isExpanded ? "Exit full screen" : "Full screen"}
            >
              {isExpanded ? (
                <Minimize2 className="w-4 h-4" />
              ) : (
                <Maximize2 className="w-4 h-4" />
              )}
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}