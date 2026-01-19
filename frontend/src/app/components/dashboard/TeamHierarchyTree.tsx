"use client";
import { useState } from "react";
import { Card, CardContent } from "../../ui/card";
import { Badge } from "../../ui/badge";
import { Avatar, AvatarFallback } from "../../ui/avatar";
import { Users, ChevronRight, ChevronDown, Building2 } from "lucide-react";

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

  // CEO Mode: Show Directors with their teams
  if (mode === "ceo") {
    if (directors.length === 0) {
      return (
        <div className="text-sm text-muted-foreground p-4">
          No directors found in this organization yet.
        </div>
      );
    }

    return (
      <div className="space-y-2">
        {directors.map((director) => {
          const isExpanded = expandedDirectors.has(director.id);
          const directorName = getName(
            director.first_name,
            director.second_name
          );

          return (
            <div key={director.id} className="border rounded-lg">
              {/* Director Header */}
              <div
                className="flex items-center justify-between p-3 cursor-pointer hover:bg-muted/50 transition-colors"
                onClick={() => toggleDirector(director.id)}
              >
                <div className="flex items-center gap-3">
                  {director.teams.length > 0 ? (
                    isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-muted-foreground" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-muted-foreground" />
                    )
                  ) : (
                    <div className="w-4" />
                  )}
                  <Avatar className="w-8 h-8">
                    <AvatarFallback className="bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
                      {getInitials(director.first_name, director.second_name)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="font-medium">{directorName}</div>
                    <div className="text-xs text-muted-foreground">
                      {director.title || "Director"}
                    </div>
                  </div>
                </div>
                <Badge variant="outline" className="ml-auto">
                  {director.teams.length} team{director.teams.length !== 1 ? "s" : ""}
                </Badge>
              </div>

              {/* Director's Teams */}
              {isExpanded && director.teams.length > 0 && (
                <div className="border-t bg-muted/20">
                  {director.teams.map((team) => {
                    const isTeamExpanded = expandedTeams.has(team.id);
                    const isHovered = hoveredTeamId === team.id;

                    return (
                      <div key={team.id} className="border-b last:border-b-0">
                        {/* Team Header with Hover */}
                        <div
                          className="flex items-center justify-between p-3 pl-8 cursor-pointer hover:bg-muted/30 transition-colors relative"
                          onClick={() => toggleTeam(team.id)}
                          onMouseEnter={() => setHoveredTeamId(team.id)}
                          onMouseLeave={() => setHoveredTeamId(null)}
                        >
                          <div className="flex items-center gap-3 flex-1">
                            {team.members.length > 0 ? (
                              isTeamExpanded ? (
                                <ChevronDown className="w-4 h-4 text-muted-foreground" />
                              ) : (
                                <ChevronRight className="w-4 h-4 text-muted-foreground" />
                              )
                            ) : (
                              <div className="w-4" />
                            )}
                            <Building2 className="w-4 h-4 text-muted-foreground" />
                            <div>
                              <div className="font-medium">{team.name}</div>
                              <div className="text-xs text-muted-foreground">
                                {team.metrics.member_count} member
                                {team.metrics.member_count !== 1 ? "s" : ""}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {team.metrics.avg_performance !== null && (
                              <Badge variant="secondary" className="text-xs">
                                {team.metrics.avg_performance}% perf
                              </Badge>
                            )}
                          </div>
                        </div>

                        {/* Team Leaders Tooltip on Hover */}
                        {isHovered && team.leaders.length > 0 && (
                          <div className="absolute z-50 left-0 top-full mt-1 bg-popover border rounded-lg shadow-lg p-3 min-w-[250px]">
                            <div className="text-xs font-semibold mb-2 text-muted-foreground">
                              Team Leaders
                            </div>
                            <div className="space-y-2">
                              {team.leaders.map((leader) => (
                                <div
                                  key={leader.id}
                                  className="flex items-center gap-2"
                                >
                                  <Avatar className="w-6 h-6">
                                    <AvatarFallback className="bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300 text-xs">
                                      {getInitials(
                                        leader.first_name,
                                        leader.second_name
                                      )}
                                    </AvatarFallback>
                                  </Avatar>
                                  <div className="flex-1 min-w-0">
                                    <div className="text-sm font-medium truncate">
                                      {getName(leader.first_name, leader.second_name)}
                                    </div>
                                    <div className="text-xs text-muted-foreground truncate">
                                      {leader.title || "Team Leader"}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Team Members (when expanded) - Only shows team leaders (level 3) */}
                        {isTeamExpanded && (
                          <div className="bg-background pl-12 pr-3 py-2 space-y-1">
                            {team.members.length > 0 ? (
                              team.members.map((member) => (
                                <div
                                  key={member.id}
                                  className="flex items-center gap-2 p-2 rounded hover:bg-muted/50"
                                >
                                  <Avatar className="w-6 h-6">
                                    <AvatarFallback className="bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 text-xs">
                                    {getInitials(member.first_name, member.second_name)}
                                  </AvatarFallback>
                                </Avatar>
                                <div className="flex-1 min-w-0">
                                  <div className="text-sm truncate">
                                    {getName(member.first_name, member.second_name)}
                                  </div>
                                  <div className="text-xs text-muted-foreground truncate">
                                    {member.title || "Member"}
                                  </div>
                                </div>
                                {member.performance !== null && (
                                  <Badge variant="outline" className="text-xs">
                                    {member.performance}%
                                  </Badge>
                                )}
                              </div>
                            ))
                            ) : (
                              <div className="text-sm text-muted-foreground italic py-2">
                                No manager found
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  }

  // Director Mode: Show teams with leaders on hover
  if (mode === "director") {
    if (teams.length === 0) {
      return (
        <div className="text-sm text-muted-foreground p-4">
          No teams found in your scope yet.
        </div>
      );
    }

    return (
      <div className="space-y-2">
        {teams.map((team) => {
          const isExpanded = expandedTeams.has(team.id);
          const isHovered = hoveredTeamId === team.id;

          return (
            <Card key={team.id} className="relative">
              <CardContent className="p-0">
                {/* Team Header with Hover */}
                <div
                  className="flex items-center justify-between p-4 cursor-pointer hover:bg-muted/50 transition-colors"
                  onClick={() => toggleTeam(team.id)}
                  onMouseEnter={() => setHoveredTeamId(team.id)}
                  onMouseLeave={() => setHoveredTeamId(null)}
                >
                  <div className="flex items-center gap-3 flex-1">
                    {team.leaders.length > 0 ? (
                      isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-muted-foreground" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-muted-foreground" />
                      )
                    ) : (
                      <div className="w-4" />
                    )}
                    <Building2 className="w-5 h-5 text-blue-600" />
                    <div>
                      <div className="font-medium text-lg">{team.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {team.metrics.member_count} member
                        {team.metrics.member_count !== 1 ? "s" : ""}
                        {team.leaders.length > 0 &&
                          ` • ${team.leaders.length} leader${team.leaders.length !== 1 ? "s" : ""}`}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {team.metrics.avg_performance !== null && (
                      <Badge variant="secondary">
                        {team.metrics.avg_performance}% avg performance
                      </Badge>
                    )}
                    {team.metrics.avg_capacity !== null && (
                      <Badge variant="outline">
                        {team.metrics.avg_capacity}% capacity
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Team Leaders Tooltip on Hover */}
                {isHovered && team.leaders.length > 0 && (
                  <div className="absolute z-50 left-4 top-full mt-1 bg-popover border rounded-lg shadow-lg p-3 min-w-[250px]">
                    <div className="text-xs font-semibold mb-2 text-muted-foreground">
                      Team Leaders
                    </div>
                    <div className="space-y-2">
                      {team.leaders.map((leader) => (
                        <div
                          key={leader.id}
                          className="flex items-center gap-2"
                        >
                          <Avatar className="w-6 h-6">
                            <AvatarFallback className="bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300 text-xs">
                              {getInitials(leader.first_name, leader.second_name)}
                            </AvatarFallback>
                          </Avatar>
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium truncate">
                              {getName(leader.first_name, leader.second_name)}
                            </div>
                            <div className="text-xs text-muted-foreground truncate">
                              {leader.title || "Team Leader"}
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
        <div className="text-sm text-muted-foreground p-4">
          No teams found in your scope yet.
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {teams.map((team) => {
          const isExpanded = expandedTeams.has(team.id);

          return (
            <Card key={team.id}>
              <CardContent className="p-0">
                {/* Team Header */}
                <div
                  className="flex items-center justify-between p-4 cursor-pointer hover:bg-muted/50 transition-colors border-b"
                  onClick={() => toggleTeam(team.id)}
                >
                  <div className="flex items-center gap-3 flex-1">
                    {team.members.length > 0 ? (
                      isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-muted-foreground" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-muted-foreground" />
                      )
                    ) : (
                      <div className="w-4" />
                    )}
                    <Building2 className="w-5 h-5 text-blue-600" />
                    <div>
                      <div className="font-medium text-lg">{team.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {team.metrics.member_count} member
                        {team.metrics.member_count !== 1 ? "s" : ""}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {team.metrics.avg_performance !== null && (
                      <Badge variant="secondary">
                        {team.metrics.avg_performance}% avg
                      </Badge>
                    )}
                    {team.metrics.avg_capacity !== null && (
                      <Badge variant="outline">
                        {team.metrics.avg_capacity}% capacity
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Team Members - Only shows team leaders (level 3) */}
                {isExpanded && (
                  <div className="p-4 space-y-2">
                    {team.members.length > 0 ? (
                      team.members.map((member) => (
                      <div
                        key={member.id}
                        className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <Avatar>
                            <AvatarFallback>
                              {getInitials(member.first_name, member.second_name)}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <div className="font-medium">
                              {getName(member.first_name, member.second_name)}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {member.title || "Team Member"}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          {member.performance !== null && (
                            <div className="text-center">
                              <div className="text-sm font-medium">
                                {member.performance}%
                              </div>
                              <div className="text-xs text-muted-foreground">
                                Perf
                              </div>
                            </div>
                          )}
                          {member.capacity !== null && (
                            <div className="text-center">
                              <div className="text-sm font-medium">
                                {member.capacity}%
                              </div>
                              <div className="text-xs text-muted-foreground">
                                Cap
                              </div>
                            </div>
                          )}
                          {member.project_count !== null && (
                            <div className="text-center">
                              <div className="text-sm font-medium">
                                {member.project_count}
                              </div>
                              <div className="text-xs text-muted-foreground">
                                Proj
                              </div>
                            </div>
                          )}
                          {member.status && (
                            <Badge
                              variant={
                                member.status === "available"
                                  ? "default"
                                  : "secondary"
                              }
                            >
                              {member.status}
                            </Badge>
                          )}
                        </div>
                      </div>
                    ))
                    ) : (
                      <div className="text-sm text-muted-foreground italic py-2 text-center">
                        No manager found
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    );
  }

  // Default: No hierarchy available
  return (
    <div className="text-sm text-muted-foreground p-4">
      No hierarchy information available for your role.
    </div>
  );
}
