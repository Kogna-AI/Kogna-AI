export interface Organization {
  id: string;
  name: string;
  industry?: string;
  team_due?: number;
  team?: string;
  project_number?: number;
}

export interface Team {
  id: string;
  name: string;
  organization_id: string;
}

export interface TeamMember {
  id: string;
  role: string;
  performance: number;
  capacity: number;
  project_count: number;
  status: string;
  user_id: string;
  team_id: string;
}
