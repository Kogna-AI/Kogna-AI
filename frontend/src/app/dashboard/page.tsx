"use client";

import { DashboardLayout } from "../components/layouts/DashboardLayout";
import { UnifiedDashboard } from "../components/UnifiedDashboard";

export default function DashboardPage() {
  return (
    <DashboardLayout activeView="dashboard">
      <UnifiedDashboard />
    </DashboardLayout>
  );
}