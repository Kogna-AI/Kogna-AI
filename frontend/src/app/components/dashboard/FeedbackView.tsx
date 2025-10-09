import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Button } from '../../ui/button';
import { Badge } from '../../ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../../ui/dialog';
import { Textarea } from '../../ui/textarea';
import { Label } from '../../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Progress } from '../../ui/progress';
import { 
  MessageSquare, 
  Plus, 
  Star, 
  Sparkles, 
  ArrowRight, 
  CheckCircle, 
  Lightbulb,
  Target,
  Users,
  TrendingUp,
  Clock,
  Wand2,
  RefreshCw,
  ThumbsUp,
  AlertCircle,
  BarChart3
} from 'lucide-react';
import { KogniiThinkingIcon } from '../../../../public/KogniiThinkingIcon';

const feedbackItems = [
  { id: 1, author: 'Sarah Chen', type: 'suggestion', content: 'Consider implementing async stand-ups for better time management', rating: 5, timestamp: '2 hours ago' },
  { id: 2, author: 'Marcus Johnson', type: 'concern', content: 'Development timeline seems aggressive given current capacity', rating: 3, timestamp: '1 day ago' },
  { id: 3, author: 'Elena Rodriguez', type: 'praise', content: 'Great collaboration on the recent design system implementation', rating: 5, timestamp: '3 days ago' }
];

const demoScenarios = [
  {
    id: 1,
    title: 'Vague Concern → Actionable Insight',
    originalText: 'The project is not going well and we need to fix things',
    improvedText: 'Our Q2 delivery timeline is at risk due to three critical blockers: (1) API integration delays affecting 2 developers, (2) design review bottleneck causing 3-day delays, and (3) insufficient testing resources. I recommend immediate sprint re-planning with stakeholder alignment by Friday.',
    improvements: [
      'Added specific timeline context (Q2 delivery)',
      'Identified 3 concrete blockers with impact details',
      'Proposed actionable solution with deadline',
      'Specified stakeholder involvement needed'
    ],
    metrics: {
      clarity: { before: 2, after: 9 },
      actionability: { before: 1, after: 9 },
      specificity: { before: 2, after: 10 }
    }
  },
  {
    id: 2,
    title: 'Generic Praise → Strategic Recognition',
    originalText: 'Good job on the feature launch',
    improvedText: 'Outstanding execution on the mobile payment integration launch - delivered 2 days early with zero critical bugs. The cross-functional coordination between engineering, design, and QA exemplifies our collaborative culture. This achievement directly supports our Q2 revenue target of $2.3M ARR growth.',
    improvements: [
      'Specified which feature and achievement details',
      'Quantified impact (2 days early, zero bugs)',
      'Recognized team collaboration across functions',
      'Connected to strategic business outcomes'
    ],
    metrics: {
      recognition: { before: 3, after: 10 },
      motivation: { before: 4, after: 9 },
      strategic_alignment: { before: 1, after: 9 }
    }
  },
  {
    id: 3,
    title: 'Process Complaint → Improvement Proposal',
    originalText: 'Meetings are taking too long and wasting time',
    improvedText: 'Our weekly planning meetings have grown from 30 minutes to 90 minutes over the past month, reducing focused development time by 15%. I propose implementing structured agendas with time-boxed segments, pre-meeting async updates, and decision-making frameworks. This could recover 4 hours per developer weekly.',
    improvements: [
      'Quantified the problem with specific metrics',
      'Showed trend analysis (30min → 90min growth)',
      'Calculated productivity impact (15% reduction)',
      'Proposed concrete solutions with expected ROI'
    ],
    metrics: {
      problem_definition: { before: 3, after: 9 },
      solution_quality: { before: 0, after: 8 },
      business_impact: { before: 1, after: 9 }
    }
  }
];

export function FeedbackView() {
  const [showDemo, setShowDemo] = useState(false);
  const [currentScenario, setCurrentScenario] = useState(0);
  const [demoStep, setDemoStep] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showImprovement, setShowImprovement] = useState(false);
  const [typingText, setTypingText] = useState('');
  const [showMetrics, setShowMetrics] = useState(false);

  const scenario = demoScenarios[currentScenario];

  // Typing effect for demo
  useEffect(() => {
    if (demoStep === 1 && scenario) {
      let index = 0;
      setTypingText('');
      const timer = setInterval(() => {
        if (index < scenario.originalText.length) {
          setTypingText(scenario.originalText.substring(0, index + 1));
          index++;
        } else {
          clearInterval(timer);
          setTimeout(() => setDemoStep(2), 1000);
        }
      }, 50);
      return () => clearInterval(timer);
    }
  }, [demoStep, scenario]);

  const startDemo = () => {
    setShowDemo(true);
    setDemoStep(1);
    setCurrentScenario(0);
    setIsAnalyzing(false);
    setShowImprovement(false);
    setShowMetrics(false);
  };

  const handleAnalyze = () => {
    setDemoStep(3);
    setIsAnalyzing(true);
    setTimeout(() => {
      setIsAnalyzing(false);
      setShowImprovement(true);
      setDemoStep(4);
    }, 3000);
  };

  const nextScenario = () => {
    if (currentScenario < demoScenarios.length - 1) {
      setCurrentScenario(currentScenario + 1);
      setDemoStep(1);
      setShowImprovement(false);
      setShowMetrics(false);
    } else {
      setShowDemo(false);
      setDemoStep(0);
      setCurrentScenario(0);
    }
  };

  const showMetricsView = () => {
    setShowMetrics(true);
    setDemoStep(5);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1>Team Feedback Hub</h1>
          <p className="text-muted-foreground">AI-enhanced feedback collection and insights</p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={startDemo}
            className="gap-2 bg-gradient-to-r from-purple-500 to-blue-600 hover:from-purple-600 hover:to-blue-700"
          >
            <Sparkles className="w-4 h-4" />
            See AI Enhancement Demo
          </Button>
          <Button className="gap-2">
            <Plus className="w-4 h-4" />
            Add Feedback
          </Button>
        </div>
      </div>

      {/* AI Enhancement Banner */}
      <Card className="border-2 border-blue-200 bg-gradient-to-r from-blue-50 to-purple-50 hover:shadow-lg transition-shadow">
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-md">
              <KogniiThinkingIcon className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <h3 className="font-semibold text-lg">Kognii AI Feedback Enhancement</h3>
                <Badge className="bg-gradient-to-r from-amber-400 to-orange-500 text-white text-xs">
                  <Sparkles className="w-3 h-3 mr-1" />
                  New Feature
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground mb-4">
                Transform vague feedback into actionable insights. Kognii analyzes tone, clarity, and strategic alignment 
                to suggest improvements that drive better outcomes and accelerate team performance.
              </p>
              <div className="grid grid-cols-4 gap-4 text-center">
                <div className="p-3 bg-white rounded-lg border">
                  <div className="font-semibold text-blue-600 text-lg">94%</div>
                  <div className="text-xs text-muted-foreground">Clarity Improvement</div>
                </div>
                <div className="p-3 bg-white rounded-lg border">
                  <div className="font-semibold text-purple-600 text-lg">87%</div>
                  <div className="text-xs text-muted-foreground">Action Rate Increase</div>
                </div>
                <div className="p-3 bg-white rounded-lg border">
                  <div className="font-semibold text-green-600 text-lg">76%</div>
                  <div className="text-xs text-muted-foreground">Resolution Speed</div>
                </div>
                <div className="p-3 bg-white rounded-lg border">
                  <div className="font-semibold text-orange-600 text-lg">92%</div>
                  <div className="text-xs text-muted-foreground">User Satisfaction</div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Existing Feedback Items */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Recent Feedback</h2>
        {feedbackItems.map((feedback) => (
          <Card key={feedback.id} className="hover:shadow-sm transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center">
                    <MessageSquare className="w-4 h-4 text-blue-600" />
                  </div>
                  <div>
                    <span className="font-medium">{feedback.author}</span>
                    <p className="text-xs text-muted-foreground">{feedback.timestamp}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge 
                    variant={
                      feedback.type === 'praise' ? 'default' : 
                      feedback.type === 'concern' ? 'destructive' : 
                      'secondary'
                    }
                    className="capitalize"
                  >
                    {feedback.type}
                  </Badge>
                  <div className="flex items-center gap-1">
                    {[...Array(feedback.rating)].map((_, i) => (
                      <Star key={i} className="w-3 h-3 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{feedback.content}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Demo Modal */}
      <Dialog open={showDemo} onOpenChange={setShowDemo}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              <KogniiThinkingIcon className="w-6 h-6" />
              Kognii Feedback Enhancement Demo
              <Badge className="bg-gradient-to-r from-purple-400 to-blue-500 text-white">
                Scenario {currentScenario + 1} of {demoScenarios.length}
              </Badge>
            </DialogTitle>
            <DialogDescription>
              {scenario?.title} - Watch how AI transforms feedback quality
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6">
            {/* Step Indicator */}
            <div className="space-y-4">
              <div className="flex items-center justify-center space-x-2">
                {[1, 2, 3, 4, 5].map((step) => (
                  <div key={step} className="flex items-center">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all ${
                      step <= demoStep ? 'bg-blue-600 text-white shadow-md' : 'bg-gray-200 text-gray-500'
                    }`}>
                      {step < demoStep ? <CheckCircle className="w-4 h-4" /> : step}
                    </div>
                    {step < 5 && <div className={`w-8 h-0.5 transition-colors ${step < demoStep ? 'bg-blue-600' : 'bg-gray-200'}`} />}
                  </div>
                ))}
              </div>
              
              {/* Step Description */}
              <div className="text-center">
                <p className="text-sm text-muted-foreground">
                  {demoStep === 1 && "User types original feedback"}
                  {demoStep === 2 && "Feedback ready for AI enhancement"}
                  {demoStep === 3 && "Kognii analyzing for improvements"}
                  {demoStep === 4 && "Enhanced version generated"}
                  {demoStep === 5 && "Improvement metrics displayed"}
                </p>
              </div>
            </div>

            {/* Demo Content */}
            {demoStep >= 1 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="w-5 h-5" />
                    Original Feedback Input
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Textarea 
                    value={typingText}
                    placeholder="User types their feedback here..."
                    readOnly
                    className="min-h-[100px] font-mono text-sm"
                  />
                  {demoStep >= 2 && (
                    <div className="mt-4 flex justify-end">
                      <Button 
                        onClick={handleAnalyze}
                        disabled={isAnalyzing}
                        className="gap-2"
                      >
                        {isAnalyzing ? (
                          <>
                            <RefreshCw className="w-4 h-4 animate-spin" />
                            Kognii Analyzing...
                          </>
                        ) : (
                          <>
                            <Wand2 className="w-4 h-4" />
                            Enhance with Kognii
                          </>
                        )}
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Analysis Progress */}
            {isAnalyzing && (
              <Card className="border-blue-200 bg-blue-50">
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                      <KogniiThinkingIcon className="w-5 h-5 animate-pulse" />
                      <span className="font-medium">Kognii is analyzing your feedback...</span>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Analyzing tone and sentiment</span>
                        <span>100%</span>
                      </div>
                      <Progress value={100} className="h-2" />
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Identifying key issues and opportunities</span>
                        <span>85%</span>
                      </div>
                      <Progress value={85} className="h-2" />
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Generating strategic improvements</span>
                        <span>60%</span>
                      </div>
                      <Progress value={60} className="h-2" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Enhanced Feedback */}
            {showImprovement && (
              <div className="space-y-4">
                <Card className="border-green-200 bg-gradient-to-r from-green-50 to-emerald-50">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-green-800">
                      <Sparkles className="w-5 h-5" />
                      Kognii Enhanced Version
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-white p-4 rounded-lg border">
                      <p className="text-sm leading-relaxed">{scenario?.improvedText}</p>
                    </div>
                    <div className="mt-4 flex gap-2">
                      <Button onClick={showMetricsView} size="sm" className="gap-2">
                        <BarChart3 className="w-4 h-4" />
                        View Improvement Metrics
                      </Button>
                      <Button onClick={nextScenario} size="sm" variant="outline" className="gap-2">
                        {currentScenario < demoScenarios.length - 1 ? (
                          <>
                            <ArrowRight className="w-4 h-4" />
                            Next Scenario
                          </>
                        ) : (
                          <>
                            <CheckCircle className="w-4 h-4" />
                            Complete Demo
                          </>
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Lightbulb className="w-5 h-5 text-orange-500" />
                      Key Improvements Made
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {scenario?.improvements.map((improvement, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{improvement}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Metrics View */}
            {showMetrics && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-blue-500" />
                    Improvement Metrics
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {Object.entries(scenario?.metrics || {}).map(([metric, values]) => (
                      <div key={metric} className="space-y-3">
                        <h4 className="font-medium capitalize">{metric.replace('_', ' ')}</h4>
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span className="text-red-600">Before</span>
                            <span>{values.before}/10</span>
                          </div>
                          <Progress value={values.before * 10} className="h-2" />
                          <div className="flex justify-between text-sm">
                            <span className="text-green-600">After</span>
                            <span>{values.after}/10</span>
                          </div>
                          <Progress value={values.after * 10} className="h-2" />
                          <div className="text-center">
                            <Badge className="bg-green-100 text-green-800">
                              +{values.after - values.before} improvement
                            </Badge>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}