"use client";

import { Contact, HeadsetIcon, Users } from "lucide-react";
import { DashboardTile } from "./DashboardTile";

const crmConnectors = [
  {
    id: "salesforce",
    name: "Salesforce",
    icon: <Contact className="h-8 w-8 text-blue-500" />,
  },
  {
    id: "hubspot",
    name: "HubSpot",
    icon: <Users className="h-8 w-8 text-orange-500" />,
  },
  {
    id: "zendesk",
    name: "Zendesk",
    icon: <HeadsetIcon className="h-8 w-8 text-emerald-600" />,
  },
];

export function CRMTile() {
  return (
    <DashboardTile
      title="CRM"
      subtitle="Salesforce, HubSpot, Zendesk and more"
      isConnected={false}
      connectorOptions={crmConnectors}
      isPlaceholder={true}
    />
  );
}
