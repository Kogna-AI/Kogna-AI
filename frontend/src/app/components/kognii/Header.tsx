import { KogniiThinkingIcon } from "../../../../public/KogniiThinkingIcon"
import { Button } from "@/app/ui/button"
import { X } from "lucide-react"
import { KogniiAssistantProps } from "./types/KogniiTypes"

export default function Header ({onClose, activeView}:KogniiAssistantProps){
  return (
    <div className="p-4 border-b border-white/10 bg-white/5 backdrop-blur-md">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-400 to-purple-600 flex items-center justify-center shadow-lg ring-1 ring-white/20">
            <KogniiThinkingIcon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Kogna Assistant</h3>
            <p className="text-xs text-blue-200/80">Strategic AI companion</p>
          </div>
        </div>
        <Button 
          variant="ghost" 
          size="sm" 
          onClick={onClose}
          className="text-white/60 hover:text-white hover:bg-white/10"
        >
          <X className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}