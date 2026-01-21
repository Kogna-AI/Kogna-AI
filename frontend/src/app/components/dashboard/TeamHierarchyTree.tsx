"use client";
import { useState } from "react";
import { Card, CardContent } from "../../ui/card";
import { Badge } from "../../ui/badge";
import { Avatar, AvatarFallback } from "../../ui/avatar";
import {
  Users,
  ChevronRight,
  ChevronDown,
  Building2,
  Briefcase,
  User,
  Shield,
} from "lucide-react";

interface TeamLeader {
  id: string;
  first_name: string | null;
  second_name: string | null;
  title: string | null;
  rbac_role_name: string | null;
  rbac_role_level: number;
}

interface TeamMember {
  id: string;
  first_name: string | null;
  second_name: string | null;
  title: string | null;
  rbac_role_name: string | null;
  rbac_role_level: number;
  performance?: number | null;
  capacity?: number | null;
  project_count?: number | null;
  status?: string | null;
}

interface Team {
  id: string;
  name: string;
  leaders: TeamLeader[];
  members: TeamMember[];
  metrics: {
    member_count: number;
    avg_performance: number | null;
    avg_capacity: number | null;
  };
}

interface Director {
  id: string;
  first_name: string | null;
  second_name: string | null;
  title: string | null;
  rbac_role_name: string | null;
  rbac_role_level: number;
  teams: Team[];
}

interface TeamHierarchyTreeProps {
  mode: string;
  directors?: Director[];
  teams?: Team[];
}

export function TeamHierarchyTree({
  mode,
  directors = [],
  teams = [],
}: TeamHierarchyTreeProps) {
  const [expandedDirectors, setExpandedDirectors] = useState<Set<string>>(
    new Set()
  );
  const [expandedTeams, setExpandedTeams] = useState<Set<string>>(new Set());
  const [hoveredTeamId, setHoveredTeamId] = useState<string | null>(null);

  const toggleDirector = (directorId: string) => {
    const newExpanded = new Set(expandedDirectors);
    if (newExpanded.has(directorId)) {
      newExpanded.delete(directorId);
    } else {
      newExpanded.add(directorId);
    }
    setExpandedDirectors(newExpanded);
  };

  const toggleTeam = (teamId: string) => {
    const newExpanded = new Set(expandedTeams);
    if (newExpanded.has(teamId)) {
      newExpanded.delete(teamId);
    } else {
      newExpanded.add(teamId);
    }
    setExpandedTeams(newExpanded);
  };

  const getInitials = (firstName: string | null, secondName: string | null) => {
    const first = firstName?.[0] || "";
    const second = secondName?.[0] || "";
    return (first + second).toUpperCase() || "?";
  };

  const getName = (firstName: string | null, secondName: string | null) => {
    return `${firstName || ""} ${secondName || ""}`.trim() || "Unknown";
  };

  const getRoleBadgeColor = (roleLevel: number) => {
    if (roleLevel >= 5) return "bg-purple-100 text-purple-700 border-purple-200";
    if (roleLevel >= 4) return "bg-indigo-100 text-indigo-700 border-indigo-200";
    if (roleLevel >= 3) return "bg-blue-100 text-blue-700 border-blue-200";
    if (roleLevel >= 2) return "bg-green-100 text-green-700 border-green-200";
    return "bg-gray-100 text-gray-700 border-gray-200";
  };

  const getAvatarColor = (roleLevel: number) => {
    if (roleLevel >= 5) return "bg-gradient-to-br from-purple-500 to-purple-600 text-white";
    if (roleLevel >= 4) return "bg-gradient-to-br from-indigo-500 to-indigo-600 text-white";
    if (roleLevel >= 3) return "bg-gradient-to-br from-blue-500 to-blue-600 text-white";
    if (roleLevel >= 2) return "bg-gradient-to-br from-green-500 to-green-600 text-white";
    return "bg-gradient-to-br from-gray-400 to-gray-500 text-white";
  };

  const getRoleIcon = (roleLevel: number) => {
    if (roleLevel >= 4) return <Shield className="w-3 h-3" />;
    if (roleLevel >= 3) return <Briefcase className="w-3 h-3" />;
    if (roleLevel >= 2) return <Users className="w-3 h-3" />;
    return <User className="w-3 h-3" />;
  };

  // CEO Mode: Show Directors with their teams
  if (mode === "ceo") {
    if (directors.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center py-12 px-4">
          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
            <Building2 className="w-8 h-8 text-muted-foreground" />
          </div>
          <p className="text-sm font-medium text-muted-foreground">
            No Directors Found
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Invite directors to build your organizational structure
          </p>
        </div>
      );
    }

    return (
      <div className="space-y-3">
        {directors.map((director) => {
          const isExpanded = expandedDirectors.has(director.id);
          const directorName = getName(
            director.first_name,
            director.second_name
          );

          return (
            <Card
              key={director.id}
              className="overflow-hidden border-2 hover:border-primary/20 transition-all duration-200"
            >
              {/* Director Header */}
              <div
                className="flex items-center justify-between p-4 cursor-pointer hover:bg-muted/50 transition-colors bg-gradient-to-r from-blue-50/50 to-transparent dark:from-blue-950/20"
                onClick={() => toggleDirector(director.id)}
              >
                <div className="flex items-center gap-3">
                  {director.teams.length > 0 ? (
                    isExpanded ? (
                      <ChevronDown className="w-5 h-5 text-primary" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-muted-foreground" />
                    )
                  ) : (
                    <div className="w-5" />
                  )}
                  <Avatar className="w-10 h-10 ring-2 ring-blue-200 dark:ring-blue-800">
                    <AvatarFallback className={getAvatarColor(director.rbac_role_level)}>
                      {getInitials(director.first_name, director.second_name)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="font-semibold text-base">{directorName}</div>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge
                        variant="outline"
                        className={`text-xs ${getRoleBadgeColor(director.rbac_role_level)}`}
                      >
                        <span className="flex items-center gap-1">
                          {getRoleIcon(director.rbac_role_level)}
                          {director.rbac_role_name || director.title || "Director"}
                        </span>
                      </Badge>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="bg-blue-50 text-blue-700 border-blue-200">
                    <Building2 className="w-3 h-3 mr-1" />
                    {director.teams.length} Team{director.teams.length !== 1 ? "s" : ""}
                  </Badge>
                </div>
              </div>

              {/* Director's Teams */}
              {isExpanded && director.teams.length > 0 && (
                <div className="border-t bg-muted/10">
                  {director.teams.map((team, idx) => {
                    const isTeamExpanded = expandedTeams.has(team.id);
                    const isHovered = hoveredTeamId === team.id;

                    return (
                      <div
                        key={team.id}
                        className={`${idx !== 0 ? "border-t" : ""}`}
                      >
                        {/* Team Header with Hover */}
                        <div
                          className="flex items-center justify-between p-3 pl-12 cursor-pointer hover:bg-muted/40 transition-colors relative group"
                          onClick={() => toggleTeam(team.id)}
                          onMouseEnter={() => setHoveredTeamId(team.id)}
                          onMouseLeave={() => setHoveredTeamId(null)}
                        >
                          <div className="flex items-center gap-3 flex-1">
                            {team.members.length > 0 ? (
                              isTeamExpanded ? (
                                <ChevronDown className="w-4 h-4 text-primary" />
                              ) : (
                                <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
                              )
                            ) : (
                              <div className="w-4" />
                            )}
                            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-green-100 to-green-50 dark:from-green-900 dark:to-green-950 flex items-center justify-center">
                              <Building2 className="w-4 h-4 text-green-600 dark:text-green-400" />
                            </div>
                            <div>
                              <div className="font-medium text-sm">{team.name}</div>
                              <div className="text-xs text-muted-foreground flex items-center gap-1">
                                <Users className="w-3 h-3" />
                                {team.metrics.member_count} member
                                {team.metrics.member_count !== 1 ? "s" : ""}
                                {team.leaders.length > 0 && (
                                  <>
                                    {" • "}
                                    {team.leaders.length} leader
                                    {team.leaders.length !== 1 ? "s" : ""}
                                  </>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Team Leaders Tooltip on Hover */}
                        {isHovered && team.leaders.length > 0 && (
                          <div className="absolute z-50 left-8 top-full mt-1 bg-popover border-2 border-primary/20 rounded-xl shadow-xl p-4 min-w-[280px]">
                            <div className="flex items-center gap-2 mb-3 pb-2 border-b">
                              <Users className="w-4 h-4 text-primary" />
                              <span className="text-xs font-semibold text-foreground">
                                Team Leadership
                              </span>
                            </div>
                            <div className="space-y-2">
                              {team.leaders.map((leader) => (
                                <div
                                  key={leader.id}
                                  className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50 transition-colors"
                                >
                                  <Avatar className="w-8 h-8 ring-2 ring-green-200 dark:ring-green-800">
                                    <AvatarFallback className={getAvatarColor(leader.rbac_role_level)}>
                                      {getInitials(leader.first_name, leader.second_name)}
                                    </AvatarFallback>
                                  </Avatar>
                                  <div className="flex-1 min-w-0">
                                    <div className="text-sm font-medium truncate">
                                      {getName(leader.first_name, leader.second_name)}
                                    </div>
                                    <div className="text-xs text-muted-foreground truncate">
                                      {leader.rbac_role_name || leader.title || "Team Leader"}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Team Members (when expanded) */}
                        <div
                          className={`overflow-hidden transition-all duration-300 ease-in-out ${
                            isTeamExpanded ? "max-h-96 opacity-100" : "max-h-0 opacity-0"
                          }`}
                        >
                          <div className="bg-background border-t">
                            {team.members.length > 0 ? (
                              <div className="p-4 pl-16 space-y-2">
                                {team.members.map((member, index) => (
                                  <div
                                    key={member.id}
                                    className="flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-muted/30 hover:border-primary/30 transition-all duration-200 animate-in fade-in slide-in-from-top-2"
                                    style={{ animationDelay: `${index * 50}ms` }}
                                  >
                                    <Avatar className="w-9 h-9">
                                      <AvatarFallback className={getAvatarColor(member.rbac_role_level)}>
                                        {getInitials(member.first_name, member.second_name)}
                                      </AvatarFallback>
                                    </Avatar>
                                    <div className="flex-1 min-w-0">
                                      <div className="text-sm font-medium truncate">
                                        {getName(member.first_name, member.second_name)}
                                      </div>
                                      <div className="flex items-center gap-2 mt-1">
                                        <Badge
                                          variant="outline"
                                          className={`text-xs ${getRoleBadgeColor(member.rbac_role_level)}`}
                                        >
                                          <span className="flex items-center gap-1">
                                            {getRoleIcon(member.rbac_role_level)}
                                            {member.rbac_role_name || member.title || "Member"}
                                          </span>
                                        </Badge>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="p-4 pl-16 text-sm text-muted-foreground italic">
                                No team members yet
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </Card>
          );
        })}
      </div>
    );
  }

  // Director Mode: Show teams with leaders on hover
  if (mode === "director") {
    if (teams.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center py-12 px-4">
          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
            <Building2 className="w-8 h-8 text-muted-foreground" />
          </div>
          <p className="text-sm font-medium text-muted-foreground">
            No Teams Assigned
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Contact your executive to assign teams to your supervision
          </p>
        </div>
      );
    }

    return (
      <div className="space-y-3">
        {teams.map((team) => {
          const isExpanded = expandedTeams.has(team.id);
          const isHovered = hoveredTeamId === team.id;

          return (
            <Card
              key={team.id}
              className="relative overflow-hidden border-2 hover:border-primary/20 transition-all duration-200"
            >
              <CardContent className="p-0">
                {/* Team Header with Hover */}
                <div
                  className="flex items-center justify-between p-4 cursor-pointer hover:bg-muted/50 transition-colors bg-gradient-to-r from-green-50/50 to-transparent dark:from-green-950/20"
                  onClick={() => toggleTeam(team.id)}
                  onMouseEnter={() => setHoveredTeamId(team.id)}
                  onMouseLeave={() => setHoveredTeamId(null)}
                >
                  <div className="flex items-center gap-3 flex-1">
                    {team.leaders.length > 0 ? (
                      isExpanded ? (
                        <ChevronDown className="w-5 h-5 text-primary" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-muted-foreground" />
                      )
                    ) : (
                      <div className="w-5" />
                    )}
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center shadow-md">
                      <Building2 className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <div className="font-semibold text-base">{team.name}</div>
                      <div className="text-sm text-muted-foreground flex items-center gap-2 mt-1">
                        <span className="flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          {team.metrics.member_count} member
                          {team.metrics.member_count !== 1 ? "s" : ""}
                        </span>
                        {team.leaders.length > 0 && (
                          <>
                            <span className="text-muted-foreground/50">•</span>
                            <span>
                              {team.leaders.length} leader
                              {team.leaders.length !== 1 ? "s" : ""}
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Team Leaders Tooltip on Hover */}
                {isHovered && team.leaders.length > 0 && (
                  <div className="absolute z-50 left-4 top-full mt-2 bg-popover border-2 border-primary/20 rounded-xl shadow-xl p-4 min-w-[300px]">
                    <div className="flex items-center gap-2 mb-3 pb-2 border-b">
                      <Users className="w-4 h-4 text-primary" />
                      <span className="text-sm font-semibold text-foreground">
                        Team Leadership
                      </span>
                    </div>
                    <div className="space-y-2">
                      {team.leaders.map((leader) => (
                        <div
                          key={leader.id}
                          className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50 transition-colors"
                        >
                          <Avatar className="w-8 h-8 ring-2 ring-green-200 dark:ring-green-800">
                            <AvatarFallback className={getAvatarColor(leader.rbac_role_level)}>
                              {getInitials(leader.first_name, leader.second_name)}
                            </AvatarFallback>
                          </Avatar>
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium truncate">
                              {getName(leader.first_name, leader.second_name)}
                            </div>
                            <div className="text-xs text-muted-foreground truncate">
                              {leader.rbac_role_name || leader.title || "Team Leader"}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    );
  }

  // Manager Mode: Show all members in the team
  if (mode === "manager") {
    if (teams.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center py-12 px-4">
          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
            <Users className="w-8 h-8 text-muted-foreground" />
          </div>
          <p className="text-sm font-medium text-muted-foreground">
            No Teams Assigned
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Contact your director to be assigned to a team
          </p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {teams.map((team) => {
          const isExpanded = expandedTeams.has(team.id);

          return (
            <Card
              key={team.id}
              className="overflow-hidden border-2 hover:border-primary/20 transition-all duration-200"
            >
              <CardContent className="p-0">
                {/* Team Header */}
                <div
                  className="flex items-center justify-between p-4 cursor-pointer hover:bg-muted/50 transition-colors border-b bg-gradient-to-r from-green-50/50 to-transparent dark:from-green-950/20"
                  onClick={() => toggleTeam(team.id)}
                >
                  <div className="flex items-center gap-3 flex-1">
                    {team.members.length > 0 ? (
                      isExpanded ? (
                        <ChevronDown className="w-5 h-5 text-primary" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-muted-foreground" />
                      )
                    ) : (
                      <div className="w-5" />
                    )}
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center shadow-md">
                      <Building2 className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <div className="font-semibold text-lg">{team.name}</div>
                      <div className="text-sm text-muted-foreground flex items-center gap-1">
                        <Users className="w-3 h-3" />
                        {team.metrics.member_count} team member
                        {team.metrics.member_count !== 1 ? "s" : ""}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Team Members */}
                <div
                  className={`overflow-hidden transition-all duration-300 ease-in-out ${
                    isExpanded ? "max-h-[600px] opacity-100" : "max-h-0 opacity-0"
                  }`}
                >
                  <div className="p-4 bg-muted/5 border-t">
                    {team.members.length > 0 ? (
                      <div className="grid gap-3">
                        {team.members.map((member, index) => (
                          <div
                            key={member.id}
                            className="flex items-center gap-3 p-3 border-2 rounded-xl bg-card hover:bg-muted/30 hover:border-primary/30 hover:shadow-md transition-all duration-200 animate-in fade-in slide-in-from-top-2"
                            style={{ animationDelay: `${index * 50}ms` }}
                          >
                            <Avatar className="w-10 h-10 ring-2 ring-background">
                              <AvatarFallback className={getAvatarColor(member.rbac_role_level)}>
                                {getInitials(member.first_name, member.second_name)}
                              </AvatarFallback>
                            </Avatar>
                            <div className="flex-1 min-w-0">
                              <div className="font-medium text-sm truncate">
                                {getName(member.first_name, member.second_name)}
                              </div>
                              <div className="flex items-center gap-2 mt-1">
                                <Badge
                                  variant="outline"
                                  className={`text-xs ${getRoleBadgeColor(member.rbac_role_level)}`}
                                >
                                  <span className="flex items-center gap-1">
                                    {getRoleIcon(member.rbac_role_level)}
                                    {member.rbac_role_name || member.title || "Team Member"}
                                  </span>
                                </Badge>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <Users className="w-8 h-8 text-muted-foreground mx-auto mb-2 opacity-50" />
                        <p className="text-sm text-muted-foreground">
                          No team members yet
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Invite members to join this team
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    );
  }

  // Default: No hierarchy available
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
        <Shield className="w-8 h-8 text-muted-foreground" />
      </div>
      <p className="text-sm font-medium text-muted-foreground">
        Hierarchy Not Available
      </p>
      <p className="text-xs text-muted-foreground mt-1 text-center max-w-sm">
        Your current role does not have access to view the organizational hierarchy
      </p>
    </div>
  );
}
