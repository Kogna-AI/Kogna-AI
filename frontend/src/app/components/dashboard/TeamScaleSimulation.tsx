import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/Button';
import { Progress } from '../../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs';
import { 
  Users, 
  TrendingUp, 
  AlertTriangle, 
  Bot, 
  BarChart3,
  DollarSign,
  Calendar,
  Target,
  Zap,
  Shield,
  CheckCircle
} from 'lucide-react';
import { KogniiThinkingIcon } from '../../../../public/KogniiThinkingIcon';
import { AreaChart, Area, XAxis, YAxis, ResponsiveContainer, LineChart, Line } from 'recharts';
import { growthStages, projectionsData } from './team-scale/constants';
import { generateContextualRecommendations, getUrgencyColor, type Objective } from './team-scale/utils';
import { RoleDetailModal } from './team-scale/RoleDetailModal';

interface TeamScaleSimulationProps {
  objectives: Objective[];
}

export function TeamScaleSimulation({ objectives }: TeamScaleSimulationProps) {
  const [currentStage, setCurrentStage] = useState(0);
  const [selectedRole, setSelectedRole] = useState<any>(null);
  const [isRoleModalOpen, setIsRoleModalOpen] = useState(false);
  const [contextualRecommendations, setContextualRecommendations] = useState<any[]>([]);

  useEffect(() => {
    const recommendations = generateContextualRecommendations(objectives);
    setContextualRecommendations(recommendations);
  }, [objectives]);

  const handleRoleClick = (role: any, stage: any) => {
    setSelectedRole({ ...role, stage: stage.stage });
    setIsRoleModalOpen(true);
  };

  const getCurrentStageData = () => growthStages[currentStage];
  const currentStageData = getCurrentStageData();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-600" />
            Team Scale Simulation
          </h2>
          <p className="text-sm text-muted-foreground">
            AI-powered hiring roadmap for robotic food delivery growth
          </p>
        </div>
        <Badge variant="secondary" className="gap-1">
          <Bot className="w-3 h-3" />
          Context-Aware
        </Badge>
      </div>

      <Tabs defaultValue="roadmap" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="roadmap">Growth Roadmap</TabsTrigger>
          <TabsTrigger value="immediate">Immediate Needs</TabsTrigger>
          <TabsTrigger value="projections">Projections</TabsTrigger>
          <TabsTrigger value="insights">AI Insights</TabsTrigger>
        </TabsList>

        <TabsContent value="roadmap" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Growth Stages</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between mb-4">
                {growthStages.map((stage, index) => (
                  <Button
                    key={index}
                    variant={currentStage === index ? "default" : "outline"}
                    size="sm"
                    onClick={() => setCurrentStage(index)}
                    className="flex-1 mx-1"
                  >
                    {stage.stage}
                  </Button>
                ))}
              </div>
              
              <div className="bg-muted/30 p-4 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="font-semibold">{currentStageData.stage}</h3>
                    <p className="text-sm text-muted-foreground">{currentStageData.description}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold">{currentStageData.teamSize}</div>
                    <div className="text-sm text-muted-foreground">employees</div>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-blue-600" />
                    <span className="text-sm">{currentStageData.monthsToReach} months</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-green-600" />
                    <span className="text-sm">{currentStageData.range}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-purple-600" />
                    <span className="text-sm">{currentStageData.keyMilestones.length} milestones</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="text-sm font-medium">Key Milestones:</h4>
                  <div className="flex flex-wrap gap-2">
                    {currentStageData.keyMilestones.map((milestone, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {milestone}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-600" />
                Critical Roles - {currentStageData.stage}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {currentStageData.criticalRoles.map((role, index) => (
                  <div
                    key={index}
                    className={`p-3 border rounded-lg cursor-pointer hover:shadow-sm transition-all ${getUrgencyColor(role.urgency)}`}
                    onClick={() => handleRoleClick(role, currentStageData)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium">{role.role}</h4>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs">
                          {role.count}x
                        </Badge>
                        <Badge 
                          variant={role.urgency === 'critical' ? 'destructive' : role.urgency === 'high' ? 'default' : 'secondary'}
                          className="text-xs"
                        >
                          {role.urgency}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {role.skills.slice(0, 2).map((skill, skillIndex) => (
                        <Badge key={skillIndex} variant="outline" className="text-xs">
                          {skill}
                        </Badge>
                      ))}
                      {role.skills.length > 2 && (
                        <Badge variant="outline" className="text-xs">
                          +{role.skills.length - 2} more
                        </Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="immediate" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-600" />
                Immediate Hiring Needs
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                Based on current objectives and growth stage
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              {contextualRecommendations.map((rec, index) => (
                <div key={index} className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium">{rec.objectiveTitle}</h4>
                    <div className="flex items-center gap-2">
                      <Progress value={rec.objectiveProgress} className="w-20" />
                      <span className="text-sm text-muted-foreground">{rec.objectiveProgress}%</span>
                    </div>
                  </div>
                  
                  <p className="text-sm text-muted-foreground">{rec.reasoning}</p>
                  
                  <div className="space-y-2">
                    <div>
                      <span className="text-sm font-medium">Immediate needs:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {rec.immediateNeeds.map((need: string, needIndex: number) => (
                          <Badge key={needIndex} variant="destructive" className="text-xs">
                            {need}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <span className="text-sm font-medium">Future considerations:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {rec.futureNeeds.map((need: string, needIndex: number) => (
                          <Badge key={needIndex} variant="outline" className="text-xs">
                            {need}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="projections" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Team Growth Projection</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={projectionsData}>
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Area 
                      type="monotone" 
                      dataKey="employees" 
                      stroke="#3b82f6" 
                      fill="#3b82f6" 
                      fillOpacity={0.1}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Revenue vs Deliveries</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={projectionsData}>
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Line type="monotone" dataKey="revenue" stroke="#10b981" strokeWidth={2} />
                    <Line type="monotone" dataKey="deliveries" stroke="#f59e0b" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-600" />
                Hiring Velocity Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">2-3</div>
                  <div className="text-sm text-muted-foreground">Hires per month</div>
                  <div className="text-xs text-muted-foreground mt-1">Current Stage</div>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-green-600">5-7</div>
                  <div className="text-sm text-muted-foreground">Hires per month</div>
                  <div className="text-xs text-muted-foreground mt-1">Growth Phase</div>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">10+</div>
                  <div className="text-sm text-muted-foreground">Hires per month</div>
                  <div className="text-xs text-muted-foreground mt-1">Scale Phase</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="insights" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <KogniiThinkingIcon className="w-5 h-5" />
                  Kognii Insights
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="border-l-4 border-blue-500 pl-4">
                  <h4 className="font-medium">Technical Talent Priority</h4>
                  <p className="text-sm text-muted-foreground">
                    Focus on robotics and ML engineers first. The complexity of autonomous delivery requires deep technical expertise before scaling operations.
                  </p>
                </div>
                <div className="border-l-4 border-green-500 pl-4">
                  <h4 className="font-medium">Regional Scaling Strategy</h4>
                  <p className="text-sm text-muted-foreground">
                    Each new city requires 3-5 dedicated operations staff. Plan hiring 2 months before market entry.
                  </p>
                </div>
                <div className="border-l-4 border-orange-500 pl-4">
                  <h4 className="font-medium">Quality Assurance Critical</h4>
                  <p className="text-sm text-muted-foreground">
                    Robotic systems require specialized QA. Hire QA engineers with robotics experience early in the process.
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-green-600" />
                  Risk Mitigation
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <h4 className="font-medium text-red-800">Critical Risk</h4>
                  <p className="text-sm text-red-700">
                    Technical talent shortage in robotics. Start recruiting 6+ months in advance.
                  </p>
                </div>
                <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                  <h4 className="font-medium text-orange-800">Medium Risk</h4>
                  <p className="text-sm text-orange-700">
                    Regulatory compliance varies by city. Legal expertise needed for each expansion.
                  </p>
                </div>
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-medium text-blue-800">Opportunity</h4>
                  <p className="text-sm text-blue-700">
                    Remote work possible for 40% of roles. Access to global talent pool.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      <RoleDetailModal 
        selectedRole={selectedRole}
        isOpen={isRoleModalOpen}
        onClose={() => setIsRoleModalOpen(false)}
      />
    </div>
  );
}