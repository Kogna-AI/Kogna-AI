import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Textarea } from '../../ui/textarea';
import { Label } from '../../ui/label';
import { Badge } from '../../ui/badge';
//import { Progress } from '../ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Checkbox } from '../../ui/checkbox';

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../../ui/dialog';
import { X, Calendar as CalendarIcon, Users, Target, Clock, CheckCircle, ArrowRight, ArrowLeft } from 'lucide-react';
import { format } from 'date-fns';

interface ObjectiveCreationProps {
  isOpen: boolean;
  onClose: () => void;
  onObjectiveCreated: (objective: any) => void;
  aiSuggestedTeam?: any[];
  onRequestTeamSuggestion?: (objectiveData: any) => void;
  kogniiPrefillData?: any;
}

interface TeamMember {
  id: string;
  name: string;
  role: string;
  department: string;
  skills: string[];
  currentWorkload: number;
  expertise: string[];
  collaborationHistory: string[];
}

const teamMembers: TeamMember[] = [
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
    id: '4',
    name: 'David Kim',
    role: 'Data Scientist',
    department: 'Analytics',
    skills: ['Python', 'ML', 'SQL', 'Tableau'],
    currentWorkload: 80,
    expertise: ['Machine Learning', 'Data Analysis'],
    collaborationHistory: ['Operational Excellence', 'Market Expansion']
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

export function ObjectiveCreation({ 
  isOpen, 
  onClose, 
  onObjectiveCreated, 
  aiSuggestedTeam,
  onRequestTeamSuggestion,
  kogniiPrefillData
}: ObjectiveCreationProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [dateInput, setDateInput] = useState('');
  const [objectiveData, setObjectiveData] = useState({
    title: '',
    description: '',
    category: '',
    priority: '',
    deadline: undefined as Date | undefined,
    metrics: [] as string[],
    assignedTeam: [] as string[],
    budget: '',
    dependencies: [] as string[],
    risks: [] as string[]
  });

  const [showTeamSuggestion, setShowTeamSuggestion] = useState(false);

  const categories = ['Product', 'Marketing', 'Operations', 'Technology', 'Finance', 'HR'];
  const priorities = ['Critical', 'High', 'Medium', 'Low'];

  // Apply Kognii prefill data when available
  useEffect(() => {
    if (kogniiPrefillData && isOpen) {
      setObjectiveData(prev => ({
        ...prev,
        ...kogniiPrefillData
      }));
      
      // Auto-advance to appropriate step if enough data is provided
      if (kogniiPrefillData.title && kogniiPrefillData.description && kogniiPrefillData.category) {
        if (kogniiPrefillData.priority && kogniiPrefillData.metrics) {
          setCurrentStep(3); // Skip to team assignment
        } else {
          setCurrentStep(2); // Skip to details
        }
      }
    }
  }, [kogniiPrefillData, isOpen]);
  const predefinedMetrics = [
    'Revenue Growth', 'User Acquisition', 'Customer Satisfaction', 'Time to Market',
    'Cost Reduction', 'Quality Score', 'Team Productivity', 'Market Share'
  ];

  const steps = [
    { number: 1, title: 'Basic Info', description: 'Define objective basics' },
    { number: 2, title: 'Details', description: 'Add specifics and metrics' },
    { number: 3, title: 'Team & Resources', description: 'Assign team and budget' },
    { number: 4, title: 'Review', description: 'Final review and submit' }
  ];

  useEffect(() => {
    if (currentStep === 3 && objectiveData.title && objectiveData.category && onRequestTeamSuggestion) {
      // Trigger AI team suggestion when reaching team assignment step
      const delay = setTimeout(() => {
        onRequestTeamSuggestion(objectiveData);
      }, 1000);
      return () => clearTimeout(delay);
    }
  }, [currentStep, objectiveData.title, objectiveData.category, onRequestTeamSuggestion]);

  const updateObjectiveData = (field: string, value: any) => {
    setObjectiveData(prev => ({ ...prev, [field]: value }));
  };

  const addToArray = (field: string, value: string) => {
    if (value.trim()) {
      setObjectiveData(prev => ({
        ...prev,
        [field]: [...(prev[field] as string[]), value.trim()]
      }));
    }
  };

  const removeFromArray = (field: string, index: number) => {
    setObjectiveData(prev => ({
      ...prev,
      [field]: (prev[field] as string[]).filter((_, i) => i !== index)
    }));
  };

  const acceptAISuggestion = () => {
    if (aiSuggestedTeam) {
      updateObjectiveData('assignedTeam', aiSuggestedTeam.map(member => member.id));
      setShowTeamSuggestion(false);
    }
  };

  const getWorkloadColor = (workload: number) => {
    if (workload < 50) return 'text-green-600';
    if (workload < 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return objectiveData.title && objectiveData.description && objectiveData.category;
      case 2:
        return objectiveData.priority && objectiveData.deadline && objectiveData.metrics.length > 0;
      case 3:
        return objectiveData.assignedTeam.length > 0;
      default:
        return true;
    }
  };

  const handleSubmit = () => {
    const newObjective = {
      id: Date.now(),
      ...objectiveData,
      status: 'planning',
      progress: 0,
      createdAt: new Date()
    };
    onObjectiveCreated(newObjective);
    onClose();
    // Reset form
    setCurrentStep(1);
    setDateInput('');
    setObjectiveData({
      title: '',
      description: '',
      category: '',
      priority: '',
      deadline: undefined,
      metrics: [],
      assignedTeam: [],
      budget: '',
      dependencies: [],
      risks: []
    });
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="title">Objective Title</Label>
              <Input
                id="title"
                placeholder="Enter objective title..."
                value={objectiveData.title}
                onChange={(e) => updateObjectiveData('title', e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Describe the objective in detail..."
                value={objectiveData.description}
                onChange={(e) => updateObjectiveData('description', e.target.value)}
                rows={4}
              />
            </div>
            <div>
              <Label htmlFor="category">Category</Label>
              <Select value={objectiveData.category} onValueChange={(value) => updateObjectiveData('category', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map(category => (
                    <SelectItem key={category} value={category}>{category}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="priority">Priority Level</Label>
              <Select value={objectiveData.priority} onValueChange={(value) => updateObjectiveData('priority', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select priority" />
                </SelectTrigger>
                <SelectContent>
                  {priorities.map(priority => (
                    <SelectItem key={priority} value={priority}>{priority}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="deadline">Target Deadline</Label>
              <div className="relative">
                <Input
                  id="deadline"
                  type="text"
                  placeholder="DD/MM/YYYY"
                  value={dateInput}
                  onChange={(e) => {
                    const value = e.target.value;
                    // Allow only numbers and forward slashes
                    const sanitized = value.replace(/[^\d\/]/g, '');
                    
                    // Auto-format with slashes
                    let formatted = sanitized;
                    if (sanitized.length === 2 && !sanitized.includes('/')) {
                      formatted = sanitized + '/';
                    } else if (sanitized.length === 5 && sanitized.charAt(4) !== '/') {
                      formatted = sanitized.slice(0, 2) + '/' + sanitized.slice(2, 4) + '/' + sanitized.slice(4);
                    }
                    
                    // Limit to 10 characters (DD/MM/YYYY)
                    if (formatted.length <= 10) {
                      setDateInput(formatted);
                      
                      // Try to parse the date if it's complete
                      if (formatted.length === 10) {
                        const parts = formatted.split('/');
                        const day = parseInt(parts[0]);
                        const month = parseInt(parts[1]) - 1; // JS months are 0-indexed
                        const year = parseInt(parts[2]);
                        
                        if (day >= 1 && day <= 31 && month >= 0 && month <= 11 && year >= new Date().getFullYear()) {
                          const date = new Date(year, month, day);
                          // Validate that the date is actually valid (handles cases like Feb 31)
                          if (date.getDate() === day && date.getMonth() === month && date.getFullYear() === year) {
                            updateObjectiveData('deadline', date);
                          } else {
                            updateObjectiveData('deadline', undefined);
                          }
                        } else {
                          updateObjectiveData('deadline', undefined);
                        }
                      } else {
                        updateObjectiveData('deadline', undefined);
                      }
                    }
                  }}
                  className="pl-10"
                />
                <CalendarIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Enter date in DD/MM/YYYY format
              </p>
              {dateInput.length === 10 && !objectiveData.deadline && (
                <p className="text-xs text-destructive mt-1">
                  Please enter a valid date
                </p>
              )}
            </div>
            <div>
              <Label>Success Metrics</Label>
              <div className="grid grid-cols-2 gap-2 mt-2">
                {predefinedMetrics.map(metric => (
                  <div key={metric} className="flex items-center space-x-2">
                    <Checkbox
                      id={metric}
                      checked={objectiveData.metrics.includes(metric)}
                      onCheckedChange={(checked) => {
                        if (checked) {
                          addToArray('metrics', metric);
                        } else {
                          const index = objectiveData.metrics.indexOf(metric);
                          if (index > -1) removeFromArray('metrics', index);
                        }
                      }}
                    />
                    <Label htmlFor={metric} className="text-sm">{metric}</Label>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-4">
            {aiSuggestedTeam && !showTeamSuggestion && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-blue-900">🤖 AI Team Suggestion</h4>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => setShowTeamSuggestion(true)}
                  >
                    View Suggestion
                  </Button>
                </div>
                <p className="text-sm text-blue-700">
                  Kognii has analyzed team skills and workload to suggest an optimal team composition.
                </p>
              </div>
            )}

            {showTeamSuggestion && aiSuggestedTeam && (
              <Card className="border-blue-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    🤖 AI Recommended Team
                    <Badge variant="secondary">Optimized</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {aiSuggestedTeam.map(member => (
                      <div key={member.id} className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                        <div>
                          <div className="font-medium">{member.name}</div>
                          <div className="text-sm text-muted-foreground">{member.role} • {member.department}</div>
                          <div className="text-xs text-blue-600">Skills: {member.skills.slice(0, 3).join(', ')}</div>
                        </div>
                        <div className="text-right">
                          <div className={`text-sm font-medium ${getWorkloadColor(member.currentWorkload)}`}>
                            {member.currentWorkload}% load
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-2 mt-4">
                    <Button onClick={acceptAISuggestion} className="flex-1">
                      Accept Suggestion
                    </Button>
                    <Button variant="outline" onClick={() => setShowTeamSuggestion(false)}>
                      Manual Selection
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {!showTeamSuggestion && (
              <div>
                <Label>Team Assignment</Label>
                <div className="space-y-2 mt-2 max-h-60 overflow-y-auto">
                  {teamMembers.map(member => (
                    <div key={member.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <Checkbox
                          checked={objectiveData.assignedTeam.includes(member.id)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              updateObjectiveData('assignedTeam', [...objectiveData.assignedTeam, member.id]);
                            } else {
                              updateObjectiveData('assignedTeam', objectiveData.assignedTeam.filter(id => id !== member.id));
                            }
                          }}
                        />
                        <div>
                          <div className="font-medium">{member.name}</div>
                          <div className="text-sm text-muted-foreground">{member.role} • {member.department}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-sm font-medium ${getWorkloadColor(member.currentWorkload)}`}>
                          {member.currentWorkload}% load
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div>
              <Label htmlFor="budget">Budget (Optional)</Label>
              <Input
                id="budget"
                placeholder="e.g., $50,000"
                value={objectiveData.budget}
                onChange={(e) => updateObjectiveData('budget', e.target.value)}
              />
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div>
              <h3 className="font-medium mb-4">Review Your Objective</h3>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm text-muted-foreground">Title</Label>
                    <p className="font-medium">{objectiveData.title}</p>
                  </div>
                  <div>
                    <Label className="text-sm text-muted-foreground">Category</Label>
                    <p className="font-medium">{objectiveData.category}</p>
                  </div>
                  <div>
                    <Label className="text-sm text-muted-foreground">Priority</Label>
                    <Badge variant={objectiveData.priority === 'Critical' ? 'destructive' : 'secondary'}>
                      {objectiveData.priority}
                    </Badge>
                  </div>
                  <div>
                    <Label className="text-sm text-muted-foreground">Deadline</Label>
                    <p className="font-medium">
                      {objectiveData.deadline ? format(objectiveData.deadline, 'PPP') : 'Not set'}
                    </p>
                  </div>
                </div>
                
                <div>
                  <Label className="text-sm text-muted-foreground">Description</Label>
                  <p className="text-sm">{objectiveData.description}</p>
                </div>

                <div>
                  <Label className="text-sm text-muted-foreground">Success Metrics</Label>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {objectiveData.metrics.map((metric, index) => (
                      <Badge key={index} variant="outline">{metric}</Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <Label className="text-sm text-muted-foreground">Assigned Team</Label>
                  <div className="space-y-1 mt-1">
                    {objectiveData.assignedTeam.map(memberId => {
                      const member = teamMembers.find(m => m.id === memberId);
                      return member ? (
                        <div key={memberId} className="text-sm">
                          {member.name} - {member.role}
                        </div>
                      ) : null;
                    })}
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
    }
  };

  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" onPointerDownOutside={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            Create New Objective
          </DialogTitle>
          <DialogDescription>
            Create a new strategic objective with team assignments, metrics, and deadlines.
          </DialogDescription>
        </DialogHeader>

        {/* Progress Indicator */}
        <div className="flex items-center justify-between mb-6">
          {steps.map((step) => (
            <div key={step.number} className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                ${currentStep >= step.number ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}`}>
                {currentStep > step.number ? <CheckCircle className="w-4 h-4" /> : step.number}
              </div>
              {step.number < steps.length && (
                <div className={`w-16 h-0.5 mx-2 
                  ${currentStep > step.number ? 'bg-primary' : 'bg-muted'}`} />
              )}
            </div>
          ))}
        </div>

        <div className="mb-4">
          <h3 className="font-medium">{steps[currentStep - 1].title}</h3>
          <p className="text-sm text-muted-foreground">{steps[currentStep - 1].description}</p>
        </div>

        {renderStepContent()}

        <div className="flex justify-between mt-6">
          <Button
            variant="outline"
            onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
            disabled={currentStep === 1}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Previous
          </Button>
          
          {currentStep < steps.length ? (
            <Button
              onClick={() => setCurrentStep(currentStep + 1)}
              disabled={!canProceed()}
            >
              Next
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          ) : (
            <Button onClick={handleSubmit} disabled={!canProceed()}>
              Create Objective
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}