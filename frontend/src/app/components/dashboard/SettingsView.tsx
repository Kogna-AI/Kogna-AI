import { Bell, User } from "lucide-react";
import { Button } from "../../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../ui/card";
import { Label } from "../../ui/label";
import { Switch } from "../../ui/switch";
import SubscriptionManager from "../SubscriptionManager";

export function SettingsView() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1>Settings</h1>
        <p className="text-muted-foreground">
          Manage your dashboard preferences and notifications
        </p>
      </div>

      {/* Subscription Section */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Subscription & Billing</h2>
        <SubscriptionManager />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="w-4 h-4" />
              Notifications
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="email-notifications">Email Notifications</Label>
              <Switch id="email-notifications" defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="push-notifications">Push Notifications</Label>
              <Switch id="push-notifications" defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="ai-insights">AI Insights</Label>
              <Switch id="ai-insights" defaultChecked />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="w-4 h-4" />
              Profile
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Display Name</Label>
              <div className="text-sm text-muted-foreground">Admin User</div>
            </div>
            <div className="space-y-2">
              <Label>Role</Label>
              <div className="text-sm text-muted-foreground">
                Strategic Manager
              </div>
            </div>
            <Button variant="outline" className="w-full">
              Edit Profile
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
