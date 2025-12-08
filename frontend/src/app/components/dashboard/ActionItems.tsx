import { CheckCircle, Clock } from "lucide-react";
import { Badge } from "../../ui/badge";
import { Card, CardContent, CardHeader } from "../../ui/card";

export default function ActionItems({ actions }: { actions: any[] }) {
  return (
    <Card className="lg:col-span-2">
      <CardHeader>
        <div>Action Items</div>
        <p className="text-sm text-muted-foreground">
          Critical tasks and decisions pending
        </p>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {actions.map((action, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 border rounded-lg"
            >
              <div className="flex items-center gap-3">
                {action.status === "completed" ? (
                  <CheckCircle className="w-4 h-4 text-green-600" />
                ) : (
                  <Clock className="w-4 h-4 text-orange-600" />
                )}
                <div>
                  <h4 className="font-medium">{action.task}</h4>
                  <p className="text-sm text-muted-foreground">
                    Due {action.due}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge>{action.priority}</Badge>
                <Badge>{action.status}</Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
