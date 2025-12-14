"use client";
import { Plus, Target } from "lucide-react";
import { useEffect, useState } from "react";
import { Badge } from "../../ui/badge";
import { Button } from "../../ui/button";
import { Card, CardContent, CardHeader } from "../../ui/card";
import { Progress } from "../../ui/progress";
import { ObjectiveCreation } from "./ObjectiveCreation";
import { TeamScaleSimulation } from "./TeamScaleSimulation";

const initialObjectives = [
  {
    id: 1,
    title: "Market Expansion",
    progress: 75,
    status: "on-track",
    owner: "Marketing Team",
    category: "Marketing",
    priority: "High",
  },
  {
    id: 2,
    title: "Product Innovation",
    progress: 60,
    status: "at-risk",
    owner: "Product Team",
    category: "Product",
    priority: "Critical",
  },
  {
    id: 3,
    title: "Operational Excellence",
    progress: 90,
    status: "ahead",
    owner: "Operations Team",
    category: "Operations",
    priority: "Medium",
  },
  {
    id: 4,
    title: "Talent Development",
    progress: 85,
    status: "on-track",
    owner: "HR Team",
    category: "HR",
    priority: "High",
  },
];

// --- FIX: Define a type for your team members ---
type TeamMember = {
  id: string;
  name: string;
  role: string;
  department: string;
  skills: string[];
  currentWorkload: number;
  expertise: string[];
  collaborationHistory: string[];
};

interface StrategyHubProps {
  kogniiControlState?: any;
  onKogniiActionComplete?: () => void;
}

// REMOVED THE DANGEROUS LINE: const globalWindow = window as any;

// Helper function for safe window access
function getKogniiContext() {
  if (typeof window !== "undefined" && (window as any).KogniiContext) {
    return (window as any).KogniiContext;
  }
  return null;
}

export function StrategyHub({
  kogniiControlState,
  onKogniiActionComplete,
}: StrategyHubProps = {}) {
  const [objectives, setObjectives] = useState(initialObjectives);
  const [isCreatingObjective, setIsCreatingObjective] = useState(false);

  // --- FIX: Explicitly type the useState hook ---
  const [aiSuggestedTeam, setAiSuggestedTeam] = useState<TeamMember[] | null>(
    null,
  );

  // Handle Kognii control actions
  useEffect(() => {
    const KogniiContext = getKogniiContext();

    if (kogniiControlState?.shouldOpenObjectiveCreation) {
      setIsCreatingObjective(true);
      if (KogniiContext) {
        KogniiContext.setObjectiveCreationActive(true);
      }
      // Clear the control state after action
      if (onKogniiActionComplete) {
        onKogniiActionComplete();
      }
    }
  }, [kogniiControlState?.shouldOpenObjectiveCreation, onKogniiActionComplete]);

  // --- FIX: Apply the new type to the sample data ---
  const teamMembers: TeamMember[] = [
    {
      id: "1",
      name: "Sarah Chen",
      role: "Senior Developer",
      department: "Engineering",
      skills: ["React", "TypeScript", "Node.js", "AWS"],
      currentWorkload: 75,
      expertise: ["Frontend Architecture", "API Design"],
      collaborationHistory: ["Product Innovation", "Market Expansion"],
    },
    {
      id: "2",
      name: "Marcus Rodriguez",
      role: "Product Manager",
      department: "Product",
      skills: ["Strategy", "Analytics", "User Research"],
      currentWorkload: 60,
      expertise: ["Product Strategy", "Market Analysis"],
      collaborationHistory: ["Market Expansion", "Operational Excellence"],
    },
    {
      id: "3",
      name: "Elena Kowalski",
      role: "UX Designer",
      department: "Design",
      skills: ["Figma", "User Research", "Prototyping"],
      currentWorkload: 45,
      expertise: ["User Experience", "Design Systems"],
      collaborationHistory: ["Product Innovation", "Talent Development"],
    },
    {
      id: "5",
      name: "Priya Patel",
      role: "Marketing Specialist",
      department: "Marketing",
      skills: ["Digital Marketing", "Content Strategy", "SEO"],
      currentWorkload: 55,
      expertise: ["Brand Strategy", "Customer Acquisition"],
      collaborationHistory: ["Market Expansion", "Product Innovation"],
    },
  ];

  const handleNewObjective = () => {
    const KogniiContext = getKogniiContext();
    setIsCreatingObjective(true);
    // Notify that objective creation has started
    if (KogniiContext) {
      KogniiContext.setObjectiveCreationActive(true);
    }
  };

  const handleObjectiveCreated = (newObjective: any) => {
    const KogniiContext = getKogniiContext();

    setObjectives((prev) => [
      ...prev,
      {
        ...newObjective,
        owner: `${newObjective.assignedTeam.length} team members`,
      },
    ]);
    setIsCreatingObjective(false);
    setAiSuggestedTeam(null);

    // Notify that objective creation has completed
    if (KogniiContext) {
      KogniiContext.setObjectiveCreationActive(false);
    }
  };

  const handleRequestTeamSuggestion = (objectiveData: any) => {
    const KogniiContext = getKogniiContext();

    // AI logic to suggest optimal team based on objective requirements
    const suggestedTeam = generateTeamSuggestion(objectiveData);
    setAiSuggestedTeam(suggestedTeam); // This is now type-safe

    // Notify Kognii Assistant about the team suggestion
    if (KogniiContext) {
      KogniiContext.setTeamSuggestion(suggestedTeam, objectiveData);
    }
  };

  // --- FIX: Add return type to the function ---
  const generateTeamSuggestion = (objectiveData: any): TeamMember[] => {
    // Simple AI logic for team suggestion based on category and requirements
    let suggestedMembers: TeamMember[] = []; // Apply type

    switch (objectiveData.category) {
      case "Product":
        suggestedMembers = teamMembers.filter(
          (member) =>
            member.department === "Product" ||
            member.department === "Engineering" ||
            member.department === "Design",
        );
        break;
      case "Marketing":
        suggestedMembers = teamMembers.filter(
          (member) =>
            member.department === "Marketing" || member.department === "Design",
        );
        break;
      case "Technology":
        suggestedMembers = teamMembers.filter(
          (member) =>
            member.department === "Engineering" ||
            member.expertise.some((exp) => exp.includes("Technology")),
        );
        break;
      default:
        // For other categories, suggest based on workload and collaboration history
        suggestedMembers = teamMembers
          .filter((member) => member.currentWorkload < 80)
          .sort((a, b) => a.currentWorkload - b.currentWorkload)
          .slice(0, 3);
    }

    // Ensure we have at least 2-3 members and prioritize those with lower workload
    return suggestedMembers
      .sort((a, b) => a.currentWorkload - b.currentWorkload)
      .slice(0, Math.max(2, Math.min(4, suggestedMembers.length)));
  };

  const handleCloseCreation = () => {
    const KogniiContext = getKogniiContext();

    setIsCreatingObjective(false);
    setAiSuggestedTeam(null);

    // Notify that objective creation has been cancelled
    if (KogniiContext) {
      KogniiContext.setObjectiveCreationActive(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1>Strategy Hub</h1>
          <p className="text-muted-foreground">
            Strategic planning and objective tracking
          </p>
        </div>
        <Button className="gap-2" onClick={handleNewObjective}>
          <Plus className="w-4 h-4" />
          New Objective
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {objectives.map((objective) => (
          <Card key={objective.id}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <Target className="w-4 h-4 text-blue-600" />
                <Badge
                  variant={
                    objective.status === "ahead"
                      ? "default"
                      : objective.status === "at-risk"
                        ? "destructive"
                        : "secondary"
                  }
                >
                  {objective.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <h3 className="font-semibold mb-2">{objective.title}</h3>
              <div className="space-y-2">
                <Progress value={objective.progress} />
                <div className="flex justify-between text-sm">
                  <span>{objective.progress}%</span>
                  <span className="text-muted-foreground">
                    {objective.owner}
                  </span>
                </div>
                {objective.category && (
                  <Badge variant="outline" className="text-xs">
                    {objective.category}
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Team Scale Simulation */}
      <TeamScaleSimulation objectives={objectives} />

      <ObjectiveCreation
        isOpen={isCreatingObjective}
        onClose={handleCloseCreation}
        onObjectiveCreated={handleObjectiveCreated}
        aiSuggestedTeam={aiSuggestedTeam || []}
        onRequestTeamSuggestion={handleRequestTeamSuggestion}
        kogniiPrefillData={kogniiControlState?.objectiveFormData}
      />
    </div>
  );
}
