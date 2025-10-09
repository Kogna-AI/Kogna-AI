"use client"
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/badge';
import { Progress } from '../../ui/progress';
import { Target, Plus, Calendar, TrendingUp, AlertCircle, Users } from 'lucide-react';
import { ObjectiveCreation } from './ObjectiveCreation';
import { TeamScaleSimulation } from './TeamScaleSimulation';

const initialObjectives = [
  { id: 1, title: 'Market Expansion', progress: 75, status: 'on-track', owner: 'Marketing Team', category: 'Marketing', priority: 'High' },
  { id: 2, title: 'Product Innovation', progress: 60, status: 'at-risk', owner: 'Product Team', category: 'Product', priority: 'Critical' },
  { id: 3, title: 'Operational Excellence', progress: 90, status: 'ahead', owner: 'Operations Team', category: 'Operations', priority: 'Medium' },
  { id: 4, title: 'Talent Development', progress: 85, status: 'on-track', owner: 'HR Team', category: 'HR', priority: 'High' }
];

interface StrategyHubProps {
  kogniiControlState?: any;
  onKogniiActionComplete?: () => void;
}

export function StrategyHub({ kogniiControlState, onKogniiActionComplete }: StrategyHubProps = {}) {
  const [objectives, setObjectives] = useState(initialObjectives);
  const [isCreatingObjective, setIsCreatingObjective] = useState(false);
  const [aiSuggestedTeam, setAiSuggestedTeam] = useState(null);

  // Handle Kognii control actions
  useEffect(() => {
    if (kogniiControlState?.shouldOpenObjectiveCreation) {
      setIsCreatingObjective(true);
      if (window.KogniiContext) {
        window.KogniiContext.setObjectiveCreationActive(true);
      }
      // Clear the control state after action
      if (onKogniiActionComplete) {
        onKogniiActionComplete();
      }
    }
  }, [kogniiControlState?.shouldOpenObjectiveCreation, onKogniiActionComplete]);

  // Sample team data for AI suggestions
  const teamMembers = [
    {
      id: '1',
      name: 'Sarah Chen',
      role: 'Senior Developer',
      department: 'Engineering',
      skills: ['React', 'TypeScript', 'Node.js', 'AWS'],
      currentWorkload: 75,
      expertise: ['Frontend Architecture', 'API Design'],
      collaborationHistory: ['Product Innovation', 'Market Expansion']
    },
    {
      id: '2',
      name: 'Marcus Rodriguez',
      role: 'Product Manager',
      department: 'Product',
      skills: ['Strategy', 'Analytics', 'User Research'],
      currentWorkload: 60,
      expertise: ['Product Strategy', 'Market Analysis'],
      collaborationHistory: ['Market Expansion', 'Operational Excellence']
    },
    {
      id: '3',
      name: 'Elena Kowalski',
      role: 'UX Designer',
      department: 'Design',
      skills: ['Figma', 'User Research', 'Prototyping'],
      currentWorkload: 45,
      expertise: ['User Experience', 'Design Systems'],
      collaborationHistory: ['Product Innovation', 'Talent Development']
    },
    {
      id: '5',
      name: 'Priya Patel',
      role: 'Marketing Specialist',
      department: 'Marketing',
      skills: ['Digital Marketing', 'Content Strategy', 'SEO'],
      currentWorkload: 55,
      expertise: ['Brand Strategy', 'Customer Acquisition'],
      collaborationHistory: ['Market Expansion', 'Product Innovation']
    }
  ];

  const handleNewObjective = () => {
    setIsCreatingObjective(true);
    // Notify that objective creation has started
    if (window.KogniiContext) {
      window.KogniiContext.setObjectiveCreationActive(true);
    }
  };

  const handleObjectiveCreated = (newObjective: any) => {
    setObjectives(prev => [...prev, {
      ...newObjective,
      owner: `${newObjective.assignedTeam.length} team members`
    }]);
    setIsCreatingObjective(false);
    setAiSuggestedTeam(null);
    
    // Notify that objective creation has completed
    if (window.KogniiContext) {
      window.KogniiContext.setObjectiveCreationActive(false);
    }
  };

  const handleRequestTeamSuggestion = (objectiveData: any) => {
    // AI logic to suggest optimal team based on objective requirements
    const suggestedTeam = generateTeamSuggestion(objectiveData);
    setAiSuggestedTeam(suggestedTeam);
    
    // Notify Kognii Assistant about the team suggestion
    if (window.KogniiContext) {
      window.KogniiContext.setTeamSuggestion(suggestedTeam, objectiveData);
    }
  };

  const generateTeamSuggestion = (objectiveData: any) => {
    // Simple AI logic for team suggestion based on category and requirements
    let suggestedMembers = [];
    
    switch (objectiveData.category) {
      case 'Product':
        suggestedMembers = teamMembers.filter(member => 
          member.department === 'Product' || 
          member.department === 'Engineering' || 
          member.department === 'Design'
        );
        break;
      case 'Marketing':
        suggestedMembers = teamMembers.filter(member => 
          member.department === 'Marketing' || 
          member.department === 'Design'
        );
        break;
      case 'Technology':
        suggestedMembers = teamMembers.filter(member => 
          member.department === 'Engineering' || 
          member.expertise.some(exp => exp.includes('Technology'))
        );
        break;
      default:
        // For other categories, suggest based on workload and collaboration history
        suggestedMembers = teamMembers
          .filter(member => member.currentWorkload < 80)
          .sort((a, b) => a.currentWorkload - b.currentWorkload)
          .slice(0, 3);
    }
    
    // Ensure we have at least 2-3 members and prioritize those with lower workload
    return suggestedMembers
      .sort((a, b) => a.currentWorkload - b.currentWorkload)
      .slice(0, Math.max(2, Math.min(4, suggestedMembers.length)));
  };

  const handleCloseCreation = () => {
    setIsCreatingObjective(false);
    setAiSuggestedTeam(null);
    
    // Notify that objective creation has been cancelled
    if (window.KogniiContext) {
      window.KogniiContext.setObjectiveCreationActive(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1>Strategy Hub</h1>
          <p className="text-muted-foreground">Strategic planning and objective tracking</p>
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
                <Badge variant={objective.status === 'ahead' ? 'default' : objective.status === 'at-risk' ? 'destructive' : 'secondary'}>
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
                  <span className="text-muted-foreground">{objective.owner}</span>
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
        aiSuggestedTeam={aiSuggestedTeam}
        onRequestTeamSuggestion={handleRequestTeamSuggestion}
        kogniiPrefillData={kogniiControlState?.objectiveFormData}
      />
    </div>
  );
}