import { Button } from "@/app/ui/button";
import { KogniiThinkingIcon } from "../../../../public/KogniiThinkingIcon";


export function LandingNavigation({ onGetStarted }: { onGetStarted: () => void }) {

return(
    <>
    <nav className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <KogniiThinkingIcon size={32} />
            <span className="text-xl font-semibold">KognaDash</span>
          </div>
          <Button onClick={onGetStarted}>
            Get Started
          </Button>
        </div>
      </nav>
      </>
    )
}
