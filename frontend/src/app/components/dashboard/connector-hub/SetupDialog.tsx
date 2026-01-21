import { ExternalLink, Sparkles } from "lucide-react";
import { useState } from "react";
import api from "@/services/api";
import { Badge } from "../../../ui/badge";
import { Button } from "../../../ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../../../ui/dialog";
import type { Connector } from "./types";

interface SetupDialogProps {
  connector: Connector | null;
  onClose: () => void;
}

export function SetupDialog({ connector, onClose }: SetupDialogProps) {
  const [isConnecting, setIsConnecting] = useState(false);

  if (!connector) return null;

  const handleConnect = async () => {
    setIsConnecting(true);
    try {
      console.log(` Getting connect URL for ${connector.id}...`);
      const data = await api.getConnectUrl(connector.id);

      if (!data.url) {
        throw new Error("No authorization URL received from server");
      }

      console.log(` Redirecting to: ${data.url}`);
      window.location.href = data.url;
    } catch (err) {
      console.error(`Failed to connect ${connector.id}:`, err);
      alert(
        `Failed to connect ${connector.name}: ${err instanceof Error ? err.message : "Unknown error"}`,
      );
      setIsConnecting(false);
    }
  };

  return (
    <Dialog open={!!connector} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            {connector.icon}
            Connect {connector.name}
            {connector.isRecommended && (
              <Badge className="bg-gradient-to-r from-amber-400 to-orange-500 text-white">
                <Sparkles className="w-3 h-3 mr-1" />
                Recommended
              </Badge>
            )}
          </DialogTitle>
          <DialogDescription>{connector.description}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <p className="text-sm text-muted-foreground">
            Connect {connector.name} to integrate your data and unlock powerful
            insights. This integration allows you to sync your existing tools
            and data sources for comprehensive project management.
          </p>

          <Button
            className="w-full"
            onClick={handleConnect}
            disabled={isConnecting}
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            {isConnecting ? "Connecting..." : `Connect ${connector.name}`}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
