"use client"
import { useState, useEffect, useRef } from 'react';
import { api } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { ScrollArea } from '../ui/scroll-area';
import { Progress } from '../ui/progress';
import { Separator } from '../ui/seperator';
import { 
  Send, 
  X, 
  Lightbulb, 
  TrendingUp, 
  AlertTriangle,
  Target,
  Sparkles,
  Users,
  Clock,
  CheckCircle,
  FileText,
  Zap,
  Play,
  Pause,
  Square,
  MessageSquare,
  BarChart3,
  Calendar,
  Settings,
  MessageCircle,
  Bell,
  PlusCircle,
  Eye,
  Edit,
  Filter,
  UserPlus,
  LineChart,
  Shield,
  Mic,
  Share,
  Video,
  ArrowRight,
  ArrowLeft,
  User,
  Bot
} from 'lucide-react';
import { KogniiThinkingIcon } from '../../../public/KogniiThinkingIcon';

interface KogniiAssistantProps {
  onClose: () => void;
  strategySessionMode?: boolean;
  activeView: string;
  kogniiActions?: any;
}

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  suggestions?: string[];
  teamSuggestion?: any;
}

// Demo chat scenarios for different contexts
const getDemoScenarios = (view: string) => {
  const baseScenarios = [
    {
      userInput: "What's our team's current performance status?",
      response: "Based on real-time analysis, your team is performing exceptionally well! Here's the snapshot:\n\n• Team Efficiency: 92% (↑8% from last month)\n• Strategic Alignment: 87% (on track with Q2 goals)\n• Workload Balance: 3 members at optimal capacity, 2 need adjustment\n• Innovation Index: 74% (opportunity for improvement)\n\nWould you like me to dive deeper into any specific metrics?"
    },
    {
      userInput: "Can you identify any optimization opportunities?",
      response: "Absolutely! I've identified several optimization opportunities:\n\n🎯 Immediate Actions (this week):\n• Redistribute design tasks from Elena (85% capacity) to reduce bottleneck\n• Automate 3 recurring workflows to save 8 hours/week\n\n📈 Strategic Improvements (next month):\n• Cross-train team on data analysis to reduce dependency\n• Implement async collaboration for 23% faster decision-making\n\n💡 Innovation Focus:\n• Allocate 20% time for experimental projects\n• Set up innovation metrics tracking\n\nShall I create action items for any of these?"
    },
    {
      userInput: "Help me plan our next strategic initiative",
      response: "Perfect timing! Let me guide you through strategic planning with AI-powered insights:\n\n🔍 Market Analysis:\n• 34% growth opportunity in sustainable products\n• Competitor gap in mobile experience\n• Team capacity at 78% - room for growth\n\n🎯 Recommended Focus Areas:\n1. Mobile-First Strategy - High impact, medium effort\n2. Sustainability Initiative - Growing market demand\n3. AI Integration - Competitive advantage opportunity\n\nI can help you create detailed objectives for any of these. Which direction interests you most?"
    }
  ];

  const viewSpecificScenarios = {
    team: [
      {
        userInput: "Who should I assign to the new project?",
        response: "Based on workload analysis and skill matching, here's my recommendation:\n\n👥 Optimal Team Composition:\n• Sarah Chen (Senior Developer) - 75% capacity, perfect for technical leadership\n• Marcus Rodriguez (Product Manager) - 60% capacity, experienced in similar projects\n• Elena Kowalski (UX Designer) - 45% capacity, available for immediate start\n\n📊 Why this team?:\n• Balanced workload (all under 80%)\n• Complementary skills coverage\n• 94% historical collaboration success rate\n• Zero scheduling conflicts\n\nShall I create the team assignment and notify members?"
      }
    ],
    teams: [
      {
        userInput: "Who should I assign to the new project?",
        response: "Based on workload analysis and skill matching, here's my recommendation:\n\n👥 Optimal Team Composition:\n• Sarah Chen (Senior Developer) - 75% capacity, perfect for technical leadership\n• Marcus Rodriguez (Product Manager) - 60% capacity, experienced in similar projects\n• Elena Kowalski (UX Designer) - 45% capacity, available for immediate start\n\n📊 Why this team?:\n• Balanced workload (all under 80%)\n• Complementary skills coverage\n• 94% historical collaboration success rate\n• Zero scheduling conflicts\n\nShall I create the team assignment and notify members?"
      }
    ],
    strategy: [
      {
        userInput: "What strategic objectives should we prioritize?",
        response: "Based on current market conditions and team capacity, here are my top recommendations:\n\n🏆 Priority 1: Customer Experience Enhancement\n• Impact: High (projected 25% satisfaction increase)\n• Effort: Medium (8-week timeline)\n• ROI: 3.2x within 6 months\n\n🚀 Priority 2: Operational Efficiency\n• Impact: Medium-High (15% cost reduction)\n• Effort: Low (automated solutions)\n• ROI: 4.1x immediate impact\n\n💡 Priority 3: Innovation Pipeline\n• Impact: High (competitive advantage)\n• Effort: High (requires new capabilities)\n• ROI: Long-term strategic value\n\nWould you like me to create detailed execution plans for any of these?"
      }
    ]
  };

  return [...baseScenarios, ...(viewSpecificScenarios[view as keyof typeof viewSpecificScenarios] || [])];
};

// Conversation mode scenarios
const conversationScenario = [
  {
    user: "Kognii, I need to discuss our Q3 strategy. We're seeing some challenges with team capacity and market demands.",
    kognii: "I understand your concern about Q3 strategy. Let me analyze your current situation in real-time..."
  },
  {
    user: "Our mobile development is falling behind schedule, and I'm worried about the product launch timeline.",
    kognii: "I see the mobile project timeline concern. Let me examine the team allocation and suggest optimizations..."
  },
  {
    user: "Can you recommend how we should reallocate resources to meet our deadlines?",
    kognii: "Based on my analysis, I recommend shifting Sarah from the analytics project to mobile development..."
  }
];

// Page context mapping
const pageContexts = {
  dashboard: {
    name: "Dashboard Overview",
    description: "Real-time performance metrics and team insights",
    capabilities: ["View team performance", "Monitor KPIs", "Track trends", "Generate insights"]
  },
  team: {
    name: "Team Overview",
    description: "Team composition, roles, and performance tracking",
    capabilities: ["Manage team members", "Assign roles", "Track performance", "Optimize workload"]
  },
  teams: {
    name: "Team Management",
    description: "Team composition, roles, and performance tracking",
    capabilities: ["Manage team members", "Assign roles", "Track performance", "Optimize workload"]
  },
  strategy: {
    name: "Strategy Hub",
    description: "Strategic planning and objective management",
    capabilities: ["Create objectives", "Suggest teams", "Track progress", "Strategic analysis"]
  },
  analytics: {
    name: "Analytics Center",
    description: "Deep performance analysis and reporting",
    capabilities: ["Generate reports", "Analyze trends", "Compare metrics", "Export data"]
  },
  meetings: {
    name: "Meeting Center",
    description: "Meeting management and collaboration tools",
    capabilities: ["Schedule meetings", "Take notes", "Track decisions", "Follow up actions"]
  },
  feedback: {
    name: "Feedback Hub",
    description: "Team feedback collection and analysis",
    capabilities: ["Collect feedback", "Analyze sentiment", "Generate reports", "Track improvements"]
  },
  connectors: {
    name: "Data Connector Hub",
    description: "Integration management and data synchronization",
    capabilities: ["Connect external tools", "Sync data", "Monitor integrations", "Optimize workflows"]
  },
  settings: {
    name: "Settings",
    description: "System configuration and preferences",
    capabilities: ["Configure system", "Manage users", "Set preferences", "Update integrations"]
  }
};

// Page-specific quick actions
const getPageQuickActions = (view: string) => {
  const baseActions = [
    { icon: TrendingUp, label: 'Performance Analysis', action: 'performance' },
    { icon: Target, label: 'Strategic Planning', action: 'strategy' },
    { icon: AlertTriangle, label: 'Risk Assessment', action: 'risks' },
    { icon: Lightbulb, label: 'Innovation Ideas', action: 'innovation' }
  ];

  const pageSpecificActions = {
    dashboard: [
      { icon: BarChart3, label: 'Deep Dive Analytics', action: 'deep-analytics' },
      { icon: Users, label: 'Team Optimization', action: 'team-optimize' },
      { icon: Eye, label: 'Trend Analysis', action: 'trend-analysis' }
    ],
    team: [
      { icon: UserPlus, label: 'Suggest New Hire', action: 'suggest-hire' },
      { icon: Users, label: 'Rebalance Workload', action: 'rebalance-workload' },
      { icon: LineChart, label: 'Performance Review', action: 'performance-review' }
    ],
    teams: [
      { icon: UserPlus, label: 'Suggest New Hire', action: 'suggest-hire' },
      { icon: Users, label: 'Rebalance Workload', action: 'rebalance-workload' },
      { icon: LineChart, label: 'Performance Review', action: 'performance-review' }
    ],
    strategy: [
      { icon: PlusCircle, label: 'Create Objective', action: 'create-objective' },
      { icon: Users, label: 'Suggest Optimal Team', action: 'suggest-team' },
      { icon: Target, label: 'Strategic Analysis', action: 'strategic-analysis' }
    ],
    analytics: [
      { icon: LineChart, label: 'Generate Report', action: 'generate-report' },
      { icon: Filter, label: 'Custom Analysis', action: 'custom-analysis' },
      { icon: Share, label: 'Export Insights', action: 'export-insights' }
    ],
    meetings: [
      { icon: Calendar, label: 'Schedule Strategic Meet', action: 'schedule-meeting' },
      { icon: MessageCircle, label: 'Meeting Summary', action: 'meeting-summary' },
      { icon: CheckCircle, label: 'Action Items', action: 'action-items' }
    ],
    feedback: [
      { icon: MessageCircle, label: 'Analyze Sentiment', action: 'analyze-sentiment' },
      { icon: TrendingUp, label: 'Feedback Trends', action: 'feedback-trends' },
      { icon: Shield, label: 'Anonymous Insights', action: 'anonymous-insights' }
    ],
    connectors: [
      { icon: Zap, label: 'Setup Integration', action: 'setup-integration' },
      { icon: Shield, label: 'Sync Status Check', action: 'sync-status' },
      { icon: Settings, label: 'Optimize Connections', action: 'optimize-connections' }
    ],
    settings: [
      { icon: Settings, label: 'Optimize Settings', action: 'optimize-settings' },
      { icon: Shield, label: 'Security Review', action: 'security-review' },
      { icon: Zap, label: 'Performance Tuning', action: 'performance-tuning' }
    ]
  };

  return {
    base: baseActions,
    specific: pageSpecificActions[view as keyof typeof pageSpecificActions] || []
  };
};

const getContextualInitialMessage = (view: string): Message => {
  const context = pageContexts[view as keyof typeof pageContexts];
  
  return {
    id: '1',
    type: 'assistant',
    content: `Hello! I'm Kognii, your strategic AI assistant. I can see you're currently in the ${context?.name || 'Dashboard'} section.\n\nContext-Aware Capabilities:\n${context?.capabilities?.map(cap => `• ${cap}`).join('\n') || '• General assistance and insights'}\n\nI'm fully integrated with KognaDash and can help you take actions directly within this context. How can I assist you today?`,
    timestamp: new Date(),
    suggestions: [
      `Analyze ${context?.name?.toLowerCase() || 'current'} performance`,
      'What can you do in this section?',
      'Identify optimization opportunities',
      'Review strategic recommendations'
    ]
  };
};

export function KogniiAssistant({ onClose, strategySessionMode = false, activeView, kogniiActions }: KogniiAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
   const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionActive, setSessionActive] = useState(strategySessionMode);
  const [sessionStep, setSessionStep] = useState(0);
  const [currentContext, setCurrentContext] = useState(activeView);
  const [demoMode, setDemoMode] = useState(true);
  const [currentDemoStep, setCurrentDemoStep] = useState(0);
  const [conversationMode, setConversationMode] = useState(false);
  const [conversationStep, setConversationStep] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatAreaRef = useRef<HTMLDivElement>(null);

  const demoScenarios = getDemoScenarios(activeView);
  const quickActions = getPageQuickActions(activeView);

  // Initialize messages based on context
  useEffect(() => {
    // This function runs when the component opens.
    const initializeChat = async () => {
      setIsTyping(true);
      try {
        // 1. Call the new API endpoint to start a session
        const session = await api.startChatSession();
        setSessionId(session.id); // <-- Store the new session ID
        console.log("New Chat Session Started:", session.id);

        // 2. Set the initial message (this is unchanged)
        if (strategySessionMode) {
          setMessages([{
            id: 'session-1',
            type: 'assistant',
            content: 'Welcome to your AI Strategy Session! I\'ll guide you through a structured strategic planning process. We\'ll cover strategic analysis, goal setting, and action planning. Ready to begin?',
            timestamp: new Date(),
            suggestions: [
              'Start with SWOT Analysis',
              'Begin Strategic Goal Setting',
              'Review Current Performance',
              'Analyze Market Opportunities'
            ]
          }]);
        } else if (!conversationMode) {
          setMessages([getContextualInitialMessage(activeView)]);
        }

      } catch (error) {
        console.error("Failed to start chat session:", error);

        let errorMessage = "An unknown error occurred";
        if (error instanceof Error) {
          errorMessage = error.message;
        }
        setMessages([{
          id: 'error-1',
          type: 'assistant',
          content: `Sorry, I couldn't connect to the AI. Please try again.\n\n**Error:** ${errorMessage}`,
          timestamp: new Date()
        }]);
      } finally {
        setIsTyping(false);
      }
    };

    initializeChat();
    
    // We only want this to run ONCE when the component mounts.
    // The eslint-disable is to prevent warnings about missing dependencies,
    // as this effect is intentionally designed to run only on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    const scrollToBottom = () => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    };

    if (messages.length > 0) {
      const timeoutId = setTimeout(scrollToBottom, 100);
      return () => clearTimeout(timeoutId);
    }
  }, [messages.length]);

  // Conversation mode auto-play
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isAutoPlaying && conversationStep < conversationScenario.length - 1) {
      interval = setInterval(() => {
        setConversationStep(prev => {
          if (prev < conversationScenario.length - 1) {
            return prev + 1;
          } else {
            setIsAutoPlaying(false);
            return prev;
          }
        });
      }, 4000);
    }
    return () => clearInterval(interval);
  }, [isAutoPlaying, conversationStep]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    // --- This is the new check ---
    if (!sessionId) {
      console.error("No session ID. Cannot send message.");
      setMessages(prev => [...prev, {
        id: 'error-no-session',
        type: 'assistant',
        content: 'There was an error connecting to the chat session. Please close and reopen the assistant.',
        timestamp: new Date()
      }]);
      return;
    }

    // 1. Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      // 2. No longer need to format history! The backend does it.

      // 3. Call the NEW, CORRECT API endpoint
      const apiResponse = await api.runAgentInSession(
        sessionId,
        userMessage.content,
        'auto' // 'auto' is the new "autonomous"
      );

      let aiContent: string;
      
      // The response format is simpler now
      if (apiResponse.final_report) {
        aiContent = apiResponse.final_report;
      } else {
        // This handles errors reported by the AI (e.g., error_handler_node)
        aiContent = `An error occurred during processing: ${apiResponse.final_report || 'Unknown workflow error'}`;
      }

      // 4. Add the AI's response message
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: aiContent,
        timestamp: new Date(),
        suggestions: [ // You can have the AI generate these later
          'Tell me more',
          'What are the next steps?'
        ]
      };
      setMessages(prev => [...prev, aiMessage]);

    } catch (error) {
      // 5. This catches network/server errors (like 500s or 400s)
      console.error("Failed to send message:", error);
      let errorString = "An unknown error occurred";
        if (error instanceof Error) {
          errorString = error.message;
        }
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `Sorry, I couldn't connect to the AI. Please try again.\n\n**Error:** ${errorString}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      // 6. Stop typing indicator
      setIsTyping(false);
    }
  };

  const handleDemoInput = () => {
    if (currentDemoStep < demoScenarios.length) {
      const scenario = demoScenarios[currentDemoStep];
      
      // Add user message
      const userMessage: Message = {
        id: `demo-user-${Date.now()}`,
        type: 'user',
        content: scenario.userInput,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, userMessage]);
      setIsTyping(true);
      
      // Add AI response after delay
      setTimeout(() => {
        const aiMessage: Message = {
          id: `demo-ai-${Date.now()}`,
          type: 'assistant',
          content: scenario.response,
          timestamp: new Date(),
          suggestions: currentDemoStep < demoScenarios.length - 1 ? 
            ['Continue demo conversation', 'Ask about team optimization', 'Request detailed analysis'] : 
            ['Start new conversation', 'Enter conversation mode', 'Ask another question']
        };
        
        setMessages(prev => [...prev, aiMessage]);
        setIsTyping(false);
        setCurrentDemoStep(prev => prev + 1);
      }, 1500);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    if (suggestion === 'Continue demo conversation' && currentDemoStep < demoScenarios.length) {
      handleDemoInput();
    } else if (suggestion === 'Enter conversation mode') {
      setConversationMode(true);
      setMessages([]);
      setCurrentDemoStep(0);
    } else if (suggestion === 'Start new conversation') {
      setCurrentDemoStep(0);
      setMessages([getContextualInitialMessage(activeView)]);
    } else {
      // Handle other suggestions as before
      const userMessage: Message = {
        id: Date.now().toString(),
        type: 'user',
        content: suggestion,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, userMessage]);
      setIsTyping(true);

      setTimeout(() => {
        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: generateAIResponse(suggestion),
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiResponse]);
        setIsTyping(false);
      }, 1500);
    }
  };

  const generateAIResponse = (input: string): string => {
    const responses = {
      'Ask about team optimization': "Great question! I'm analyzing your team composition in real-time:\n\n📊 Current Status:\n• Sarah Chen: 75% capacity (optimal)\n• Marcus Rodriguez: 60% capacity (available)\n• Elena Kowalski: 45% capacity (underutilized)\n• David Kim: 85% capacity (near limit)\n• Priya Patel: 55% capacity (available)\n\n🎯 Optimization Recommendations:\n• Redistribute data analysis tasks from David to Elena\n• Assign Marcus to lead the new mobile initiative\n• Cross-train Priya on technical skills for better flexibility\n\nWould you like me to create a detailed rebalancing plan?",
      
      'Request detailed analysis': "I'll provide a comprehensive analysis of your current situation:\n\n📈 Performance Metrics:\n• Team Efficiency: 92% (↑8% vs last month)\n• Strategic Alignment: 87% with Q2 goals\n• Innovation Index: 74% (opportunity area)\n• Customer Satisfaction: 91% (industry leading)\n\n🔍 Key Insights:\n• Workflow automation could save 12 hours/week\n• Cross-functional collaboration up 23%\n• Technical debt decreased by 15%\n• New feature adoption at 78%\n\n⚡ Action Items:\n• Implement advanced analytics dashboard\n• Schedule innovation workshop\n• Review resource allocation\n\nShall I dive deeper into any specific area?",
      
      'What can you do in this section?': `In the ${pageContexts[activeView as keyof typeof pageContexts]?.name || 'current section'}, I can help you:\n\n${pageContexts[activeView as keyof typeof pageContexts]?.capabilities?.map(cap => `• ${cap}`).join('\n') || '• General assistance and insights'}\n\n🤖 AI-Powered Features:\n• Real-time optimization suggestions\n• Predictive analytics and insights\n• Automated workflow recommendations\n• Strategic planning assistance\n\nI'm continuously learning from your team's patterns to provide increasingly personalized recommendations. What would you like to explore first?`
    };

    return responses[input as keyof typeof responses] || `I understand you're asking about "${input}". Based on the current context in ${pageContexts[activeView as keyof typeof pageContexts]?.name || 'this section'}, I can provide detailed insights and actionable recommendations.\n\nLet me analyze your specific situation and provide tailored advice. What aspect would you like me to focus on first?`;
  };

  const handleQuickAction = (action: string) => {
    const context = pageContexts[activeView as keyof typeof pageContexts];
    
    // Generate contextual response for quick actions
    const actionResponses = {
      'create-objective': "🎯 I'll help you create a strategic objective! Let me guide you through the process:\n\nStep 1: Objective Framing\n• What's the primary goal you want to achieve?\n• Which strategic pillar does this support?\n• What's the target timeline?\n\nAI Suggestions:\n• Market expansion opportunity (+34% growth potential)\n• Technical modernization (reduce technical debt)\n• Customer experience enhancement\n\nI can also suggest optimal team compositions based on your objective. Shall we start with objective definition?",
      
      'team-optimize': "👥 Analyzing your team for optimization opportunities...\n\nCurrent Workload Distribution:\n• 2 team members over 80% capacity\n• 1 team member under 50% capacity\n• Skills gap in data analysis\n\nRecommended Actions:\n• Redistribute design tasks to balance workload\n• Cross-train Elena on analytics tools\n• Consider bringing David into strategic planning\n\nExpected Impact:\n• 15% improvement in delivery speed\n• Better work-life balance\n• Enhanced skill diversity\n\nShall I create a detailed rebalancing proposal?",
      
      'performance': "📊 Performance Analysis Complete\n\nYour team is performing excellently! Here's the breakdown:\n\nKey Metrics:\n• Overall efficiency: 92% (above industry average)\n• Goal alignment: 87% (strong strategic focus)\n• Innovation score: 74% (room for improvement)\n\nTrends:\n• Productivity increased 15% this quarter\n• Collaboration metrics up 23%\n• Technical quality improved significantly\n\nRecommendations:\n• Allocate 20% time for innovation projects\n• Implement advanced automation tools\n• Schedule strategy alignment session\n\nWould you like me to dive deeper into any specific metric?"
    };

    const response = actionResponses[action as keyof typeof actionResponses] || 
      `I'm analyzing the ${action} request in the context of ${context?.name}. Let me provide you with actionable insights and recommendations.`;

    const actionMessage: Message = {
      id: Date.now().toString(),
      type: 'assistant',
      content: response,
      timestamp: new Date(),
      suggestions: [
        'Show me detailed metrics',
        'Create action plan',
        'Schedule follow-up',
        'Export analysis'
      ]
    };

    setMessages(prev => [...prev, actionMessage]);
  };

  const nextConversationStep = () => {
    if (conversationStep < conversationScenario.length - 1) {
      setConversationStep(prev => prev + 1);
    } else {
      setConversationMode(false);
      setConversationStep(0);
      setMessages([getContextualInitialMessage(activeView)]);
    }
  };

  const startAutoPlay = () => {
    setIsAutoPlaying(true);
  };

  const resetConversationDemo = () => {
    setConversationStep(0);
    setIsAutoPlaying(false);
  };

  const exitConversationMode = () => {
    setConversationMode(false);
    setConversationStep(0);
    setIsAutoPlaying(false);
    setMessages([getContextualInitialMessage(activeView)]);
  };
  const formatChatHistory = (msgs: Message[]) => {
    // Only send the last 10 messages to keep the payload light
    return msgs.slice(-10).map(msg => ({
      role: msg.type, // 'user', 'assistant', or 'system'
      content: msg.content
    }));
  };

  const renderMessage = (message: Message) => {
    return (
      <div key={message.id} className={`flex gap-3 mb-4 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
        {message.type === 'assistant' && (
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow-lg">
            <Bot className="w-4 h-4 text-white" />
          </div>
        )}
        
        <div className={`max-w-[85%] ${message.type === 'user' ? 'order-2' : 'order-1'}`}>
          <div className={`rounded-2xl p-3 ${
            message.type === 'user' 
              ? 'bg-primary text-primary-foreground ml-auto' 
              : 'bg-muted text-muted-foreground'
          }`}>
            <div className="text-sm whitespace-pre-line leading-relaxed">
              {message.content}
            </div>
          </div>
          
          {message.suggestions && message.suggestions.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {message.suggestions.map((suggestion, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="text-xs h-7 px-2 rounded-full border-border/50 hover:border-border text-muted-foreground hover:text-foreground"
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          )}
        </div>

        {message.type === 'user' && (
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-gray-500 to-gray-700 flex items-center justify-center flex-shrink-0 shadow-lg order-1">
            <User className="w-4 h-4 text-white" />
          </div>
        )}
      </div>
    );
  };

  if (conversationMode) {
    return (
      <div className="w-96 h-full bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 relative overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-blue-400 to-purple-600 animate-pulse"></div>
          <div className="absolute top-1/4 left-1/4 w-24 h-24 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-full blur-3xl animate-bounce" style={{ animationDuration: '3s' }}></div>
          <div className="absolute bottom-1/4 right-1/4 w-20 h-20 bg-gradient-to-br from-purple-400 to-pink-600 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '2s' }}></div>
          <div className="absolute top-1/2 right-1/3 w-16 h-16 bg-gradient-to-br from-indigo-400 to-purple-600 rounded-full blur-3xl animate-bounce" style={{ animationDuration: '4s' }}></div>
        </div>

        {/* Content */}
        <div className="relative z-10 h-full p-4 flex flex-col">
          <div className="bg-white/5 backdrop-blur-lg rounded-xl border border-white/10 h-full p-4 flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={exitConversationMode}
                  className="text-white/80 hover:text-white hover:bg-white/10"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Chat
                </Button>
              </div>
              <Button variant="ghost" size="sm" onClick={onClose} className="text-white/80 hover:text-white hover:bg-white/10">
                <X className="w-4 h-4" />
              </Button>
            </div>

            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-400 to-purple-600 flex items-center justify-center shadow-lg">
                <KogniiThinkingIcon className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-white">Conversation Mode</h3>
                <p className="text-xs text-white/60">Immersive AI strategic planning</p>
              </div>
            </div>

            {/* Control Panel */}
            <div className="mb-4 flex items-center justify-center gap-2">
              <Button 
                onClick={startAutoPlay}
                disabled={isAutoPlaying || conversationStep >= conversationScenario.length - 1}
                size="sm"
                className="gap-2 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-xs"
              >
                <KogniiThinkingIcon className="w-3 h-3" />
                {isAutoPlaying ? 'Auto-Playing...' : 'Start Auto Demo'}
              </Button>
              <Button 
                onClick={resetConversationDemo}
                variant="outline"
                size="sm"
                className="gap-2 border-white/20 text-white/80 hover:text-white hover:bg-white/10 text-xs"
              >
                Reset Demo
              </Button>
            </div>

            {/* Conversation Content */}
            <div className="flex-1 bg-white/5 backdrop-blur border border-white/10 rounded-lg p-4 overflow-hidden">
              <div className="space-y-4 h-full flex flex-col">
                {/* Live Analysis Indicator */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-white/60">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    AI Analysis Active
                  </div>
                  <Badge className="bg-green-500/20 text-green-300 border-green-400/30">
                    Step {conversationStep + 1} of {conversationScenario.length}
                  </Badge>
                </div>

                {/* Active Conversation */}
                <div className="flex-1 space-y-3 overflow-y-auto">
                  <div className="bg-blue-500/10 p-3 rounded border border-blue-400/20">
                    <div className="text-xs text-blue-300 mb-2 flex items-center gap-2">
                      <div className="w-5 h-5 rounded-full bg-gradient-to-br from-gray-400 to-gray-600 flex items-center justify-center text-xs font-medium text-white">
                        A
                      </div>
                      Allen (Founder)
                    </div>
                    <p className="text-sm text-white/90 leading-relaxed">
                      {conversationScenario[conversationStep]?.user}
                    </p>
                  </div>
                  <div className="bg-purple-500/10 p-3 rounded border border-purple-400/20">
                    <div className="text-xs text-purple-300 mb-2 flex items-center gap-2">
                      <div className="w-5 h-5 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                        <KogniiThinkingIcon className="w-3 h-3 text-white" />
                      </div>
                      Kognii AI
                    </div>
                    <p className="text-sm text-white/90 leading-relaxed">
                      {conversationScenario[conversationStep]?.kognii}
                    </p>
                  </div>

                  {/* Live Metrics */}
                  {conversationStep >= 1 && (
                    <div className="bg-orange-500/10 backdrop-blur border border-orange-400/20 rounded-lg p-3 animate-in slide-in-from-bottom duration-500">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="w-4 h-4 text-orange-300" />
                        <span className="text-sm font-medium text-white">Risk Assessment</span>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                          <span className="text-xs text-white/80">Mobile dev 2 weeks behind</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                          <span className="text-xs text-white/80">Resource bottleneck detected</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {conversationStep >= 2 && (
                    <div className="bg-green-500/10 backdrop-blur border border-green-400/20 rounded-lg p-3 animate-in slide-in-from-bottom duration-700">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="w-4 h-4 text-green-300" />
                        <span className="text-sm font-medium text-white">AI Recommendations</span>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                          <span className="text-xs text-white/80">Move Sarah to mobile team (85% match)</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                          <span className="text-xs text-white/80">Hire contractor for analytics (temp solution)</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Action Button */}
                <Button 
                  onClick={nextConversationStep}
                  className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
                  disabled={isAutoPlaying}
                >
                  <ArrowRight className="w-4 h-4 mr-2" />
                  {conversationStep < conversationScenario.length - 1 ? 'Continue Analysis' : 'Complete Session'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-96 h-full bg-background border-l border-border shadow-xl flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
              <KogniiThinkingIcon className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold">Kognii Assistant</h3>
              <p className="text-xs text-muted-foreground">Strategic AI companion</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="p-4 border-b border-border">
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {quickActions.base.map((action, index) => (
              <Button
                key={index}
                variant="outline"
                size="sm"
                onClick={() => handleQuickAction(action.action)}
                className="gap-2 text-xs h-8 rounded-full"
              >
                <action.icon className="w-3 h-3" />
                {action.label}
              </Button>
            ))}
          </div>
          
          {quickActions.specific.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {quickActions.specific.map((action, index) => (
                <Button
                  key={index}
                  variant="secondary"
                  size="sm"
                  onClick={() => handleQuickAction(action.action)}
                  className="gap-2 text-xs h-8 rounded-full"
                >
                  <action.icon className="w-3 h-3" />
                  {action.label}
                </Button>
              ))}
            </div>
          )}
        </div>

        <div className="flex gap-2 mt-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleDemoInput}
            disabled={currentDemoStep >= demoScenarios.length}
            className="flex-1 text-xs h-8"
          >
            <Play className="w-3 h-3 mr-2" />
            Demo Chat
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setConversationMode(true)}
            className="flex-1 text-xs h-8"
          >
            <KogniiThinkingIcon className="w-3 h-3 mr-2" />
            Deep Mode
          </Button>
        </div>
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full">
          <div ref={chatAreaRef} className="p-4">
            {messages.map(renderMessage)}
            
            {isTyping && (
              <div className="flex gap-3 mb-4 justify-start">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0 shadow-lg">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="max-w-[85%]">
                  <div className="rounded-2xl p-3 bg-muted text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <KogniiThinkingIcon className="w-4 h-4 animate-pulse" />
                      <span className="text-sm">Kognii is thinking...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-border">
        <div className="flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Ask Kognii anything..."
            className="flex-1"
            disabled={isTyping}
          />
          <Button 
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isTyping}
            size="sm"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
        
        <div className="flex items-center justify-between mt-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setConversationMode(true)}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            <MessageCircle className="w-3 h-3 mr-2" />
            Enter Conversation AI
          </Button>
          
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {/* We check for sessionId to show the real status */}
            {sessionId ? (
              <>
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                AI Active
              </>
            ) : (
              <>
                <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                AI Offline
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}