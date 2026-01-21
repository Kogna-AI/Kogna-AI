"use client";
import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../../ui/card";
import { Badge } from "../../ui/badge";
import { Button } from "../../ui/button";
import { Progress } from "../../ui/progress";
import { Avatar, AvatarFallback, AvatarImage } from "../../ui/avatar";
import { Input } from "../../ui/input";
import { Label } from "../../ui/label";
import { Textarea } from "../../ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../ui/select";
import { Checkbox } from "../../ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../../ui/dialog";
import {
  Users,
  TrendingUp,
  Clock,
  Target,
  Star,
  MessageSquare,
  Calendar,
  Award,
  Bot,
  UserPlus,
  PlusCircle,
  Building2,
} from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
} from "recharts";
import api from "@/services/api";
import { useUser } from "@/app/components/auth/UserContext";
import type { Team, TeamMember } from "@/types/backend";
import { TeamHierarchyTree } from "./TeamHierarchyTree";
const teamMembers = [
  {
    id: 1,
    name: "Sarah Chen",
    role: "Product Manager",
    avatar:
      "https://images.unsplash.com/photo-1494790108755-2616c47b1e09?w=150&h=150&fit=crop&crop=faces",
    performance: 95,
    capacity: 85,
    projects: 3,
    status: "available",
  },
  {
    id: 2,
    name: "Marcus Johnson",
    role: "Lead Developer",
    avatar:
      "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=faces",
    performance: 88,
    capacity: 92,
    projects: 2,
    status: "busy",
  },
  {
    id: 3,
    name: "Elena Rodriguez",
    role: "UX Designer",
    avatar:
      "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=faces",
    performance: 92,
    capacity: 78,
    projects: 4,
    status: "available",
  },
  {
    id: 4,
    name: "David Kim",
    role: "Data Analyst",
    avatar:
      "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=faces",
    performance: 89,
    capacity: 88,
    projects: 2,
    status: "available",
  },
  {
    id: 5,
    name: "Lisa Wang",
    role: "Marketing Lead",
    avatar:
      "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&h=150&fit=crop&crop=faces",
    performance: 91,
    capacity: 95,
    projects: 3,
    status: "busy",
  },
];

const skillsData = [
  { name: "Frontend", value: 85, color: "#3b82f6" },
  { name: "Backend", value: 78, color: "#8b5cf6" },
  { name: "Design", value: 92, color: "#10b981" },
  { name: "Analytics", value: 87, color: "#f59e0b" },
  { name: "Strategy", value: 82, color: "#ef4444" },
];

const performanceData = [
  { month: "Jan", productivity: 85, satisfaction: 88 },
  { month: "Feb", productivity: 88, satisfaction: 90 },
  { month: "Mar", productivity: 82, satisfaction: 85 },
  { month: "Apr", productivity: 90, satisfaction: 92 },
  { month: "May", productivity: 93, satisfaction: 94 },
  { month: "Jun", productivity: 95, satisfaction: 96 },
];

interface MeetingFormData {
  title: string;
  description: string;
  date: string;
  time: string;
  duration: string;
  type: string;
  selectedMember: string;
  includeKognii: boolean;
}

// function OneOnOneSchedulingDialog() {
//   const [isOpen, setIsOpen] = useState(false);
//   const [meetingData, setMeetingData] = useState<MeetingFormData>({
//     title: "",
//     description: "",
//     date: "",
//     time: "",
//     duration: "30",
//     type: "1on1",
//     selectedMember: "",
//     includeKognii: false,
//   });

//   const handlePresetSelection = (
//     preset: "kognii-1on1" | "team-member-1on1"
//   ) => {
//     if (preset === "kognii-1on1") {
//       setMeetingData({
//         ...meetingData,
//         title: "1:1 Strategy Session with Kognii",
//         description:
//           "Personal career development and strategic insights discussion",
//         type: "ai-strategy",
//         selectedMember: "",
//         includeKognii: true,
//       });
//     } else {
//       setMeetingData({
//         ...meetingData,
//         title: "1:1 Check-in",
//         description:
//           "Regular one-on-one meeting to discuss progress, challenges, and development",
//         type: "1on1",
//         includeKognii: false,
//       });
//     }
//   };

//   const handleSubmit = () => {
//     console.log("1:1 Meeting scheduled:", meetingData);
//     setIsOpen(false);
//     // Reset form
//     setMeetingData({
//       title: "",
//       description: "",
//       date: "",
//       time: "",
//       duration: "30",
//       type: "1on1",
//       selectedMember: "",
//       includeKognii: false,
//     });
//   };

//   const availableMembers = teamMembers.filter(
//     (member) => member.status === "available"
//   );

//   return (
//     <Dialog open={isOpen} onOpenChange={setIsOpen}>
//       <DialogTrigger asChild>
//         <Button variant="outline" className="gap-2">
//           <Calendar className="w-4 h-4" />
//           Schedule 1:1s
//         </Button>
//       </DialogTrigger>
//       <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
//         <DialogHeader>
//           <DialogTitle>Schedule 1:1 Meeting</DialogTitle>
//           <DialogDescription>
//             Create a personal one-on-one meeting with team members or Kognii for
//             strategic discussions
//           </DialogDescription>
//         </DialogHeader>

//         <div className="space-y-6">
//           {/* Meeting Presets */}
//           <div className="space-y-3">
//             <Label>Quick Setup</Label>
//             <div className="grid grid-cols-2 gap-3">
//               <Button
//                 type="button"
//                 variant="outline"
//                 className="h-auto p-4 flex flex-col items-start gap-2"
//                 onClick={() => handlePresetSelection("kognii-1on1")}
//               >
//                 <div className="flex items-center gap-2">
//                   <Bot className="w-4 h-4 text-blue-600" />
//                   <span>1:1 with Kognii</span>
//                 </div>
//                 <p className="text-xs text-muted-foreground text-left">
//                   Strategic career development session
//                 </p>
//               </Button>
//               <Button
//                 type="button"
//                 variant="outline"
//                 className="h-auto p-4 flex flex-col items-start gap-2"
//                 onClick={() => handlePresetSelection("team-member-1on1")}
//               >
//                 <div className="flex items-center gap-2">
//                   <UserPlus className="w-4 h-4 text-green-600" />
//                   <span>Team Member 1:1</span>
//                 </div>
//                 <p className="text-xs text-muted-foreground text-left">
//                   Regular check-in and development
//                 </p>
//               </Button>
//             </div>
//           </div>

//           {/* Team Member Selection - only show if not Kognii meeting */}
//           {!meetingData.includeKognii && (
//             <div>
//               <Label htmlFor="selectedMember">Select Team Member</Label>
//               <Select
//                 value={meetingData.selectedMember}
//                 onValueChange={(value) =>
//                   setMeetingData((prev) => ({ ...prev, selectedMember: value }))
//                 }
//               >
//                 <SelectTrigger>
//                   <SelectValue placeholder="Choose a team member" />
//                 </SelectTrigger>
//                 <SelectContent>
//                   {teamMembers.map((member) => (
//                     <SelectItem
//                       key={member.id}
//                       value={member.id.toString()}
//                       disabled={member.status !== "available"}
//                     >
//                       <div className="flex items-center gap-2">
//                         <div
//                           className={`w-2 h-2 rounded-full ${
//                             member.status === "available"
//                               ? "bg-green-500"
//                               : "bg-yellow-500"
//                           }`}
//                         />
//                         <span>{member.name}</span>
//                         <span className="text-xs text-muted-foreground">
//                           ({member.role})
//                         </span>
//                       </div>
//                     </SelectItem>
//                   ))}
//                 </SelectContent>
//               </Select>
//               {availableMembers.length === 0 && (
//                 <p className="text-sm text-muted-foreground mt-1">
//                   No team members are currently available. You can still
//                   schedule with Kognii.
//                 </p>
//               )}
//             </div>
//           )}

//           {/* Meeting Details */}
//           <div className="grid grid-cols-2 gap-4">
//             <div className="col-span-2">
//               <Label htmlFor="title">Meeting Title</Label>
//               <Input
//                 id="title"
//                 value={meetingData.title}
//                 onChange={(e) =>
//                   setMeetingData((prev) => ({ ...prev, title: e.target.value }))
//                 }
//                 placeholder="Enter meeting title"
//               />
//             </div>

//             <div className="col-span-2">
//               <Label htmlFor="description">Meeting Agenda</Label>
//               <Textarea
//                 id="description"
//                 value={meetingData.description}
//                 onChange={(e) =>
//                   setMeetingData((prev) => ({
//                     ...prev,
//                     description: e.target.value,
//                   }))
//                 }
//                 placeholder="Discussion topics and objectives"
//                 rows={3}
//               />
//             </div>

//             <div>
//               <Label htmlFor="date">Date</Label>
//               <Input
//                 id="date"
//                 type="date"
//                 value={meetingData.date}
//                 onChange={(e) =>
//                   setMeetingData((prev) => ({ ...prev, date: e.target.value }))
//                 }
//               />
//             </div>

//             <div>
//               <Label htmlFor="time">Time</Label>
//               <Input
//                 id="time"
//                 type="time"
//                 value={meetingData.time}
//                 onChange={(e) =>
//                   setMeetingData((prev) => ({ ...prev, time: e.target.value }))
//                 }
//               />
//             </div>

//             <div>
//               <Label htmlFor="duration">Duration</Label>
//               <Select
//                 value={meetingData.duration}
//                 onValueChange={(value) =>
//                   setMeetingData((prev) => ({ ...prev, duration: value }))
//                 }
//               >
//                 <SelectTrigger>
//                   <SelectValue />
//                 </SelectTrigger>
//                 <SelectContent>
//                   <SelectItem value="15">15 minutes</SelectItem>
//                   <SelectItem value="30">30 minutes</SelectItem>
//                   <SelectItem value="45">45 minutes</SelectItem>
//                   <SelectItem value="60">1 hour</SelectItem>
//                 </SelectContent>
//               </Select>
//             </div>

//             <div>
//               <Label htmlFor="type">Meeting Type</Label>
//               <Select
//                 value={meetingData.type}
//                 onValueChange={(value) =>
//                   setMeetingData((prev) => ({ ...prev, type: value }))
//                 }
//               >
//                 <SelectTrigger>
//                   <SelectValue />
//                 </SelectTrigger>
//                 <SelectContent>
//                   <SelectItem value="1on1">Regular 1:1</SelectItem>
//                   <SelectItem value="ai-strategy">AI Strategy</SelectItem>
//                   <SelectItem value="performance">
//                     Performance Review
//                   </SelectItem>
//                   <SelectItem value="career">Career Development</SelectItem>
//                   <SelectItem value="feedback">Feedback Session</SelectItem>
//                 </SelectContent>
//               </Select>
//             </div>
//           </div>

//           {/* Include Kognii for regular meetings */}
//           {!meetingData.includeKognii && (
//             <div className="flex items-center space-x-2">
//               <Checkbox
//                 id="includeKognii"
//                 checked={meetingData.includeKognii}
//                 onCheckedChange={(checked) =>
//                   setMeetingData((prev) => ({
//                     ...prev,
//                     includeKognii: !!checked,
//                   }))
//                 }
//               />
//               <Label
//                 htmlFor="includeKognii"
//                 className="flex items-center gap-2"
//               >
//                 <Bot className="w-4 h-4 text-blue-600" />
//                 Include Kognii for strategic insights
//               </Label>
//             </div>
//           )}

//           {/* Actions */}
//           <div className="flex justify-end gap-3 pt-4 border-t">
//             <Button
//               type="button"
//               variant="outline"
//               onClick={() => setIsOpen(false)}
//             >
//               Cancel
//             </Button>
//             <Button
//               type="button"
//               onClick={handleSubmit}
//               disabled={
//                 !meetingData.title ||
//                 !meetingData.date ||
//                 !meetingData.time ||
//                 (!meetingData.selectedMember && !meetingData.includeKognii)
//               }
//             >
//               Schedule 1:1
//             </Button>
//           </div>
//         </div>
//       </DialogContent>
//     </Dialog>
//   );
// }

interface TeamManagementDialogProps {
  organizationId: string;
  roleLevel: number;
  members: any[];
  onMemberRemoved: (userId: string) => void;
}

function TeamManagementDialog({
  organizationId,
  roleLevel,
  members,
  onMemberRemoved,
}: TeamManagementDialogProps) {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"create" | "invite" | "remove">("invite");

  const [teamName, setTeamName] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [selectedMemberId, setSelectedMemberId] = useState<
    string | undefined
  >();
  const [targetTeamId, setTargetTeamId] = useState<string | undefined>();
  const [selectedTeamIds, setSelectedTeamIds] = useState<string[]>([]);

  const [teams, setTeams] = useState<any[]>([]);
  const [teamsLoading, setTeamsLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [confirmingRemove, setConfirmingRemove] = useState(false);

  const canCreateTeam = roleLevel >= 4;
  const canManageMembers = roleLevel >= 3;

  useEffect(() => {
    if (!organizationId || !canManageMembers || !open) return;

    const loadTeams = async () => {
      setTeamsLoading(true);
      try {
        // When inviting a director (CEO only), exclude teams with CEOs
        const excludeCeoTeams =
          mode === "invite" && inviteRole === "director" && roleLevel >= 5;
        const res = await api.listOrganizationTeams(
          organizationId,
          excludeCeoTeams,
        );
        const data = (res as any).data || res || [];
        setTeams(data);

        // Set default target team if not set (only for non-director invites)
        if (
          !targetTeamId &&
          data.length > 0 &&
          !(mode === "invite" && inviteRole === "director" && roleLevel >= 5)
        ) {
          setTargetTeamId(String(data[0].id));
        }

        // If director role and selected teams are no longer available, clear selection
        // This only runs when teams are loaded, not on every selection change
        if (excludeCeoTeams) {
          const availableTeamIds = data.map((t: any) => String(t.id));
          setSelectedTeamIds((prev) =>
            prev.filter((id) => availableTeamIds.includes(id)),
          );
        }
      } catch (e) {
        console.error("Failed to load organization teams", e);
        setError(
          e instanceof Error ? e.message : "Failed to load organization teams",
        );
      } finally {
        setTeamsLoading(false);
      }
    };

    loadTeams();
  }, [organizationId, canManageMembers, open, mode, inviteRole, roleLevel]);

  const resetMessages = () => {
    setError(null);
    setSuccess(null);
    setConfirmingRemove(false);
  };

  const handleCreateTeam = async () => {
    resetMessages();
    if (!teamName.trim()) {
      setError("Please enter a team name");
      return;
    }
    setLoading(true);
    try {
      await api.createTeam({
        organization_id: organizationId,
        name: teamName.trim(),
      });
      setSuccess("Team created successfully");
      setTeamName("");
    } catch (e) {
      const message = e instanceof Error ? e.message : "Failed to create team";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async () => {
    resetMessages();
    if (!inviteEmail.trim()) {
      setError("Please enter an email address");
      return;
    }

    // For directors, require at least one team selected
    // For others, use single team selection
    const isDirector = inviteRole === "director" && roleLevel >= 5;
    if (isDirector) {
      if (selectedTeamIds.length === 0) {
        setError(
          "Please select at least one team for the director to supervise",
        );
        return;
      }
    } else {
      if (!targetTeamId) {
        setError("Please select a team to invite into");
        return;
      }
    }

    setLoading(true);
    try {
      // For directors with multiple teams, use the first team ID in the path
      // but send team_ids in the body
      const teamIdForPath =
        isDirector && selectedTeamIds.length > 0
          ? selectedTeamIds[0]
          : targetTeamId!;

      const invitationData: any = {
        email: inviteEmail,
        role: inviteRole,
      };

      // Add team_ids for directors
      if (isDirector && selectedTeamIds.length > 0) {
        invitationData.team_ids = selectedTeamIds;
      }

      const result = await api.createTeamInvitation(
        teamIdForPath,
        invitationData,
      );
      const token = (result as any).token || result.token;
      const baseUrl =
        typeof window !== "undefined" ? window.location.origin : "";
      const link = `${baseUrl}/signup/invite/${token}`;
      const teamCount = isDirector ? selectedTeamIds.length : 1;
      setSuccess(
        `Invite link created for ${teamCount} team${teamCount > 1 ? "s" : ""}: ${link}`,
      );

      // Reset form
      setInviteEmail("");
      setInviteRole("member");
      setSelectedTeamIds([]);
      setTargetTeamId(teams.length > 0 ? String(teams[0].id) : undefined);
    } catch (e) {
      const message =
        e instanceof Error ? e.message : "Failed to create invitation";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleTeamToggle = (teamId: string) => {
    setSelectedTeamIds((prev) => {
      if (prev.includes(teamId)) {
        return prev.filter((id) => id !== teamId);
      } else {
        return [...prev, teamId];
      }
    });
  };

  const handleRemoveMember = () => {
    resetMessages();
    if (!selectedMemberId) {
      setError("Please select a member to remove");
      return;
    }
    if (!targetTeamId) {
      setError("Please select a team");
      return;
    }
    setConfirmingRemove(true);
  };

  const handleConfirmRemove = async () => {
    resetMessages();
    if (!selectedMemberId || !targetTeamId) {
      return;
    }
    setLoading(true);
    try {
      await api.removeTeamMember(targetTeamId, selectedMemberId);
      setSuccess("Member removed from team");
      onMemberRemoved(selectedMemberId);
      setSelectedMemberId(undefined);
      setConfirmingRemove(false);
    } catch (e) {
      const message =
        e instanceof Error ? e.message : "Failed to remove member";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => {
        setOpen(isOpen);
        if (!isOpen) {
          // Reset form when dialog closes
          setInviteEmail("");
          setInviteRole("member");
          setSelectedTeamIds([]);
          setTargetTeamId(teams.length > 0 ? String(teams[0].id) : undefined);
        }
      }}
    >
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2">
          <Users className="w-4 h-4" />
          Manage Team
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Team management</DialogTitle>
          <DialogDescription>
            Create teams, invite members, or remove members from teams.
          </DialogDescription>
        </DialogHeader>

        <div className="flex gap-2 mb-4">
          {canCreateTeam && (
            <Button
              type="button"
              variant={mode === "create" ? "default" : "outline"}
              size="sm"
              onClick={() => {
                setMode("create");
                resetMessages();
              }}
            >
              New Team
            </Button>
          )}
          {canManageMembers && (
            <Button
              type="button"
              variant={mode === "invite" ? "default" : "outline"}
              size="sm"
              onClick={() => {
                setMode("invite");
                resetMessages();
              }}
            >
              Invite Member
            </Button>
          )}
          {canManageMembers && (
            <Button
              type="button"
              variant={mode === "remove" ? "default" : "outline"}
              size="sm"
              onClick={() => {
                setMode("remove");
                resetMessages();
              }}
            >
              Remove Member
            </Button>
          )}
        </div>

        {/* Shared team selector for invite (non-directors only) and remove */}
        {canManageMembers &&
          (mode === "remove" ||
            (mode === "invite" &&
              (inviteRole !== "director" || roleLevel < 5))) && (
            <div className="space-y-2 mb-4">
              <Label htmlFor="mgmt-team">Team</Label>
              {teamsLoading ? (
                <p className="text-sm text-muted-foreground">
                  Loading teams...
                </p>
              ) : teams.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No teams found in this organization. Create a team first.
                </p>
              ) : (
                <Select
                  value={targetTeamId}
                  onValueChange={(value) => setTargetTeamId(value)}
                >
                  <SelectTrigger id="mgmt-team">
                    <SelectValue placeholder="Select a team" />
                  </SelectTrigger>
                  <SelectContent>
                    {teams.map((t) => (
                      <SelectItem key={t.id} value={String(t.id)}>
                        {t.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
          )}

        {mode === "create" && canCreateTeam && (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="team-name">Team name</Label>
              <Input
                id="team-name"
                value={teamName}
                onChange={(e) => setTeamName(e.target.value)}
                placeholder="e.g. Product, Sales, Data Science"
              />
            </div>
          </div>
        )}

        {mode === "invite" && canManageMembers && (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="invite-email">Email</Label>
              <Input
                id="invite-email"
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="person@company.com"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="invite-role">Role</Label>
              <Select
                value={inviteRole}
                onValueChange={(value) => {
                  setInviteRole(value);
                  // Reset team selection when role changes
                  if (value !== "director" || roleLevel < 5) {
                    setSelectedTeamIds([]);
                  }
                }}
              >
                <SelectTrigger id="invite-role">
                  <SelectValue placeholder="Select role" />
                </SelectTrigger>
                <SelectContent>
                  {roleLevel >= 5 && (
                    <SelectItem value="director">Director</SelectItem>
                  )}
                  {roleLevel >= 4 && roleLevel < 5 && (
                    <SelectItem value="director">Director</SelectItem>
                  )}
                  {roleLevel >= 3 && (
                    <SelectItem value="manager">
                      Team Leader / Manager
                    </SelectItem>
                  )}
                  <SelectItem value="member">Team Member</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Multi-select teams for directors (CEO only) */}
            {inviteRole === "director" && roleLevel >= 5 && (
              <div className="space-y-2">
                <Label>Select Teams to Supervise</Label>
                {teamsLoading ? (
                  <p className="text-sm text-muted-foreground">
                    Loading teams...
                  </p>
                ) : teams.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No teams found. Create a team first.
                  </p>
                ) : (
                  <div className="border rounded-lg p-3 max-h-60 overflow-y-auto space-y-2">
                    {teams.map((team) => (
                      <div
                        key={team.id}
                        className="flex items-center space-x-2"
                      >
                        <Checkbox
                          id={`team-${team.id}`}
                          checked={selectedTeamIds.includes(String(team.id))}
                          onCheckedChange={() =>
                            handleTeamToggle(String(team.id))
                          }
                        />
                        <Label
                          htmlFor={`team-${team.id}`}
                          className="text-sm font-normal cursor-pointer flex-1"
                        >
                          {team.name}
                          {team.member_count !== undefined && (
                            <span className="text-muted-foreground ml-2">
                              ({team.member_count} members)
                            </span>
                          )}
                        </Label>
                      </div>
                    ))}
                  </div>
                )}
                {selectedTeamIds.length > 0 && (
                  <p className="text-xs text-muted-foreground">
                    {selectedTeamIds.length} team
                    {selectedTeamIds.length !== 1 ? "s" : ""} selected
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {mode === "remove" && canManageMembers && (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="remove-member">Team member</Label>
              {members.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No visible team members to remove.
                </p>
              ) : (
                <Select
                  value={selectedMemberId}
                  onValueChange={(value) => setSelectedMemberId(value)}
                >
                  <SelectTrigger id="remove-member">
                    <SelectValue placeholder="Select a member" />
                  </SelectTrigger>
                  <SelectContent>
                    {members.map((m) => (
                      <SelectItem
                        key={m.id || m.user_id}
                        value={String(m.user_id || m.id)}
                      >
                        {m.name || `${m.first_name} ${m.second_name || ""}`}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
            <div
              className={`rounded-md border px-3 py-2 text-xs ${
                confirmingRemove
                  ? "border-red-500 bg-red-50 text-red-700"
                  : "border-muted bg-muted text-muted-foreground"
              }`}
            >
              {confirmingRemove ? (
                <p>
                  Confirm removal: this will detach the member from the selected
                  team but will <span className="font-semibold">not</span>{" "}
                  delete their user account in the organization.
                </p>
              ) : (
                <p>
                  Removing a member only detaches them from the team. Their user
                  account in the organization remains active.
                </p>
              )}
            </div>
          </div>
        )}

        {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
        {success && (
          <p className="text-sm text-green-600 mt-2 whitespace-pre-wrap">
            {success}
          </p>
        )}

        <div className="flex justify-end gap-2 pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => setOpen(false)}
          >
            Close
          </Button>
          {mode === "create" && canCreateTeam && (
            <Button type="button" onClick={handleCreateTeam} disabled={loading}>
              {loading ? "Creating..." : "Create team"}
            </Button>
          )}
          {mode === "invite" && canManageMembers && (
            <Button type="button" onClick={handleInvite} disabled={loading}>
              {loading ? "Creating invite..." : "Create invite"}
            </Button>
          )}
          {mode === "remove" && canManageMembers && !confirmingRemove && (
            <Button
              type="button"
              variant="destructive"
              onClick={handleRemoveMember}
              disabled={loading}
            >
              Remove member
            </Button>
          )}
          {mode === "remove" && canManageMembers && confirmingRemove && (
            <>
              <Button
                type="button"
                variant="outline"
                onClick={() => setConfirmingRemove(false)}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant="destructive"
                onClick={handleConfirmRemove}
                disabled={loading}
              >
                {loading ? "Removing..." : "Confirm removal"}
              </Button>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function TeamOverview() {
  const { user } = useUser();
  console.log(user);
  const [team, setTeam] = useState<any>(null);
  const [members, setMembers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hierarchy, setHierarchy] = useState<any | null>(null);
  const [hierarchyLoading, setHierarchyLoading] = useState(false);
  const [hierarchyError, setHierarchyError] = useState<string | null>(null);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "available":
        return "bg-green-500";
      case "busy":
        return "bg-yellow-500";
      default:
        return "bg-gray-500";
    }
  };

  useEffect(() => {
    const fetchVisiblePeople = async () => {
  if (!user?.id) return;

      try {
        setLoading(true);
        setError(null);

        // 1. Get all people this user is allowed to see
        const visibleResponse = await api.listVisibleUsers();
        const visibleMembers =
          (visibleResponse as any)?.data || visibleResponse || [];
        setMembers(visibleMembers);

        // 2. Load hierarchical view of teams/users based on RBAC
        try {
          setHierarchyLoading(true);
          setHierarchyError(null);
          const hierarchyResponse = await api.teamHierarchy();
          const hierarchyData =
            (hierarchyResponse as any).data || hierarchyResponse || null;
          setHierarchy(hierarchyData);
        } catch (hierarchyErr) {
          console.error("Error loading team hierarchy:", hierarchyErr);
          setHierarchyError(
            hierarchyErr instanceof Error
              ? hierarchyErr.message
              : "Failed to load team hierarchy",
          );
        } finally {
          setHierarchyLoading(false);
        }

        // 3. Optional: still fetch the user's primary team for the header
        //    For executives/founders, we show an org-wide label instead.
        let teamLabel: any = null;

        try {
          const teamResponse = await api.getUserTeam(user.id);
          const teamData = (teamResponse as any)?.data || teamResponse || null;
          teamLabel = teamData;
        } catch {
          // User might not belong to a specific team (e.g., founder/CEO),
          // it's fine to just treat them as org-wide.
        }

        const isExecutive = (user.rbac?.role_level ?? 0) >= 4;

        if (isExecutive) {
          setTeam({ name: teamLabel?.name || "Entire Organization" });
        } else if (teamLabel?.id) {
          setTeam(teamLabel);
        } else {
          setTeam(null);
        }
      } catch (err) {
        console.error("Error loading visible people:", err);
        setError(
          err instanceof Error ? err.message : "Failed to load team data",
        );
      } finally {
        setLoading(false);
      }
    };

    fetchVisiblePeople();
  }, [user]);

  const teamMembersCount = members.length;

  const averagePerformance = members.length
    ? Math.round(
        members.reduce((sum, member) => sum + (member.performance || 0), 0) /
          members.length,
      )
    : 0;

  const averageCapacity = members.length
    ? Math.round(
        members.reduce((sum, member) => sum + (member.capacity || 0), 0) /
          members.length,
      )
    : 0;

  const totalProjects = members.reduce(
    (sum, member) => sum + (member.project_count || member.projects || 0),
    0,
  );

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1>Team Overview</h1>
          <p className="text-muted-foreground">
            {team?.name
              ? `${team.name} - View team structure and organizational hierarchy`
              : "View your team structure and organizational hierarchy"}
          </p>
        </div>
        <div className="flex gap-2">
          {/* <OneOnOneSchedulingDialog /> */}
          {user?.rbac?.role_level &&
            user.rbac.role_level >= 3 &&
            user.organization_id && (
              <TeamManagementDialog
                organizationId={user.organization_id}
                roleLevel={user.rbac.role_level}
                members={members}
                onMemberRemoved={(removedId) => {
                  setMembers((prev) =>
                    prev.filter((m) => String(m.user_id || m.id) !== removedId),
                  );
                }}
              />
            )}
          {/* <Button className="gap-2">
            <MessageSquare className="w-4 h-4" />
            Team Feedback
          </Button> */}
        </div>
      </div>

      {/* Organizational Hierarchy */}
      <Card className="border-2">
        <CardHeader className="bg-gradient-to-r from-blue-50/50 to-transparent dark:from-blue-950/20">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
              <Building2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl">Organizational Structure</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                Visual representation of your organization's hierarchy and team composition
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          {hierarchyLoading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4 animate-pulse">
                <Building2 className="w-8 h-8 text-muted-foreground" />
              </div>
              <p className="text-sm text-muted-foreground">
                Loading organizational structure...
              </p>
            </div>
          ) : hierarchyError ? (
            <div className="flex flex-col items-center justify-center py-12 px-4">
              <div className="w-16 h-16 rounded-full bg-yellow-100 dark:bg-yellow-900 flex items-center justify-center mb-4">
                <Building2 className="w-8 h-8 text-yellow-600 dark:text-yellow-400" />
              </div>
              <p className="text-sm font-medium text-yellow-700 dark:text-yellow-400">
                Unable to Load Hierarchy
              </p>
              <p className="text-xs text-muted-foreground mt-1 text-center max-w-md">
                {hierarchyError}
              </p>
            </div>
          ) : hierarchy ? (
            <TeamHierarchyTree
              mode={hierarchy.mode || "member"}
              directors={hierarchy.directors || []}
              teams={hierarchy.teams || []}
            />
          ) : (
            <div className="flex flex-col items-center justify-center py-12 px-4">
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                <Building2 className="w-8 h-8 text-muted-foreground" />
              </div>
              <p className="text-sm font-medium text-muted-foreground">
                No Hierarchy Data
              </p>
              <p className="text-xs text-muted-foreground mt-1 text-center max-w-sm">
                Organizational hierarchy information is not currently available
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
