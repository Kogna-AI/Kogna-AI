import { KogniiThinkingIcon } from "../../../../public/KogniiThinkingIcon"
import { Button } from "@/app/ui/button"
import { X } from "lucide-react"
import { KogniiAssistantProps } from "./types/KogniiTypes"

export default function Header ({onClose}:KogniiAssistantProps){
<div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
              <KogniiThinkingIcon className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold">Kognii Assistant</h3>
              <p className="text-xs text-muted-foreground">Strategic AI companion</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>
}