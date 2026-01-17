import {
  Message,
  QuickAction,
  DemoScenario,
  ConversationStep,
  PageContext,
} from "../types/KogniiTypes";

// Demo chat scenarios for different contexts
export const getDemoScenarios = (view: string): DemoScenario[] => {
  const baseScenarios = [
    {
      userInput: "What's our team's current performance status?",
      response:
        "Based on real-time analysis, your team is performing exceptionally well! Here's the snapshot:\n\n• Team Efficiency: 92% (↑8% from last month)\n• Strategic Alignment: 87% (on track with Q2 goals)\n• Workload Balance: 3 members at optimal capacity, 2 need adjustment\n• Innovation Index: 74% (opportunity for improvement)\n\nWould you like me to dive deeper into any specific metrics?",
    },
    {
      userInput: "Can you identify any optimization opportunities?",
      response:
        "Absolutely! I've identified several optimization opportunities:\n\nImmediate Actions (this week):\n• Redistribute design tasks from Elena (85% capacity) to reduce bottleneck\n• Automate 3 recurring workflows to save 8 hours/week\n\nStrategic Improvements (next month):\n• Cross-train team on data analysis to reduce dependency\n• Implement async collaboration for 23% faster decision-making\n\nInnovation Focus:\n• Allocate 20% time for experimental projects\n• Set up innovation metrics tracking\n\nShall I create action items for any of these?",
    },
    {
      userInput: "Help me plan our next strategic initiative",
      response:
        "Perfect timing! Let me guide you through strategic planning with AI-powered insights:\n\nMarket Analysis:\n• 34% growth opportunity in sustainable products\n• Competitor gap in mobile experience\n• Team capacity at 78% - room for growth\n\nRecommended Focus Areas:\n1. Mobile-First Strategy - High impact, medium effort\n2. Sustainability Initiative - Growing market demand\n3. AI Integration - Competitive advantage opportunity\n\nI can help you create detailed objectives for any of these. Which direction interests you most?",
    },
  ];

  const viewSpecificScenarios = {
    team: [
      {
        userInput: "Who should I assign to the new project?",
        response:
          "Based on workload analysis and skill matching, here's my recommendation:\n\nOptimal Team Composition:\n• Sarah Chen (Senior Developer) - 75% capacity, perfect for technical leadership\n• Marcus Rodriguez (Product Manager) - 60% capacity, experienced in similar projects\n• Elena Kowalski (UX Designer) - 45% capacity, available for immediate start\n\nWhy this team?:\n• Balanced workload (all under 80%)\n• Complementary skills coverage\n• 94% historical collaboration success rate\n• Zero scheduling conflicts\n\nShall I create the team assignment and notify members?",
      },
    ],
    teams: [
      {
        userInput: "Who should I assign to the new project?",
        response:
          "Based on workload analysis and skill matching, here's my recommendation:\n\nOptimal Team Composition:\n• Sarah Chen (Senior Developer) - 75% capacity, perfect for technical leadership\n• Marcus Rodriguez (Product Manager) - 60% capacity, experienced in similar projects\n• Elena Kowalski (UX Designer) - 45% capacity, available for immediate start\n\nWhy this team?:\n• Balanced workload (all under 80%)\n• Complementary skills coverage\n• 94% historical collaboration success rate\n• Zero scheduling conflicts\n\nShall I create the team assignment and notify members?",
      },
    ],
    strategy: [
      {
        userInput: "What strategic objectives should we prioritize?",
        response:
          "Based on current market conditions and team capacity, here are my top recommendations:\n\nPriority 1: Customer Experience Enhancement\n• Impact: High (projected 25% satisfaction increase)\n• Effort: Medium (8-week timeline)\n• ROI: 3.2x within 6 months\n\nPriority 2: Operational Efficiency\n• Impact: Medium-High (15% cost reduction)\n• Effort: Low (automated solutions)\n• ROI: 4.1x immediate impact\n\nPriority 3: Innovation Pipeline\n• Impact: High (competitive advantage)\n• Effort: High (requires new capabilities)\n• ROI: Long-term strategic value\n\nWould you like me to create detailed execution plans for any of these?",
      },
    ],
  };

  return [
    ...baseScenarios,
    ...(viewSpecificScenarios[view as keyof typeof viewSpecificScenarios] ||
      []),
  ];
};

// Conversation mode scenarios
export const conversationScenario: ConversationStep[] = [
  {
    user: "Kogna, I need to discuss our Q3 strategy. We're seeing some challenges with team capacity and market demands.",
    kognii:
      "I understand your concern about Q3 strategy. Let me analyze your current situation in real-time...",
  },
  {
    user: "Our mobile development is falling behind schedule, and I'm worried about the product launch timeline.",
    kognii:
      "I see the mobile project timeline concern. Let me examine the team allocation and suggest optimizations...",
  },
  {
    user: "Can you recommend how we should reallocate resources to meet our deadlines?",
    kognii:
      "Based on my analysis, I recommend shifting Sarah from the analytics project to mobile development...",
  },
];

// Page context mapping
export const pageContexts: Record<string, PageContext> = {
  dashboard: {
    name: "Dashboard Overview",
    description: "Real-time performance metrics and team insights",
    capabilities: [
      "View team performance",
      "Monitor KPIs",
      "Track trends",
      "Generate insights",
    ],
  },
  team: {
    name: "Team Overview",
    description: "Team composition, roles, and performance tracking",
    capabilities: [
      "Manage team members",
      "Assign roles",
      "Track performance",
      "Optimize workload",
    ],
  },
  teams: {
    name: "Team Management",
    description: "Team composition, roles, and performance tracking",
    capabilities: [
      "Manage team members",
      "Assign roles",
      "Track performance",
      "Optimize workload",
    ],
  },
  strategy: {
    name: "Strategy Hub",
    description: "Strategic planning and objective management",
    capabilities: [
      "Create objectives",
      "Suggest teams",
      "Track progress",
      "Strategic analysis",
    ],
  },
  analytics: {
    name: "Analytics Center",
    description: "Deep performance analysis and reporting",
    capabilities: [
      "Generate reports",
      "Analyze trends",
      "Compare metrics",
      "Export data",
    ],
  },
  meetings: {
    name: "Meeting Center",
    description: "Meeting management and collaboration tools",
    capabilities: [
      "Schedule meetings",
      "Take notes",
      "Track decisions",
      "Follow up actions",
    ],
  },
  feedback: {
    name: "Feedback Hub",
    description: "Team feedback collection and analysis",
    capabilities: [
      "Collect feedback",
      "Analyze sentiment",
      "Generate reports",
      "Track improvements",
    ],
  },
  connectors: {
    name: "Data Connector Hub",
    description: "Integration management and data synchronization",
    capabilities: [
      "Connect external tools",
      "Sync data",
      "Monitor integrations",
      "Optimize workflows",
    ],
  },
  settings: {
    name: "Settings",
    description: "System configuration and preferences",
    capabilities: [
      "Configure system",
      "Manage users",
      "Set preferences",
      "Update integrations",
    ],
  },
};

// Page-specific quick actions
export const getPageQuickActions = (view: string) => {
  const baseActions: QuickAction[] = [
    {
      icon: "TrendingUp",
      label: "Performance Analysis",
      action: "performance",
    },
    { icon: "Target", label: "Strategic Planning", action: "strategy" },
    { icon: "AlertTriangle", label: "Risk Assessment", action: "risks" },
    { icon: "Lightbulb", label: "Innovation Ideas", action: "innovation" },
  ];

  const pageSpecificActions: Record<string, QuickAction[]> = {
    dashboard: [
      {
        icon: "BarChart3",
        label: "Deep Dive Analytics",
        action: "deep-analytics",
      },
      { icon: "Users", label: "Team Optimization", action: "team-optimize" },
      { icon: "Eye", label: "Trend Analysis", action: "trend-analysis" },
    ],
    team: [
      { icon: "UserPlus", label: "Suggest New Hire", action: "suggest-hire" },
      {
        icon: "Users",
        label: "Rebalance Workload",
        action: "rebalance-workload",
      },
      {
        icon: "LineChart",
        label: "Performance Review",
        action: "performance-review",
      },
    ],
    teams: [
      { icon: "UserPlus", label: "Suggest New Hire", action: "suggest-hire" },
      {
        icon: "Users",
        label: "Rebalance Workload",
        action: "rebalance-workload",
      },
      {
        icon: "LineChart",
        label: "Performance Review",
        action: "performance-review",
      },
    ],
    strategy: [
      {
        icon: "PlusCircle",
        label: "Create Objective",
        action: "create-objective",
      },
      { icon: "Users", label: "Suggest Optimal Team", action: "suggest-team" },
      {
        icon: "Target",
        label: "Strategic Analysis",
        action: "strategic-analysis",
      },
    ],
    analytics: [
      {
        icon: "LineChart",
        label: "Generate Report",
        action: "generate-report",
      },
      { icon: "Filter", label: "Custom Analysis", action: "custom-analysis" },
      { icon: "Share", label: "Export Insights", action: "export-insights" },
    ],
    meetings: [
      {
        icon: "Calendar",
        label: "Schedule Strategic Meet",
        action: "schedule-meeting",
      },
      {
        icon: "MessageCircle",
        label: "Meeting Summary",
        action: "meeting-summary",
      },
      { icon: "CheckCircle", label: "Action Items", action: "action-items" },
    ],
    feedback: [
      {
        icon: "MessageCircle",
        label: "Analyze Sentiment",
        action: "analyze-sentiment",
      },
      {
        icon: "TrendingUp",
        label: "Feedback Trends",
        action: "feedback-trends",
      },
      {
        icon: "Shield",
        label: "Anonymous Insights",
        action: "anonymous-insights",
      },
    ],
    connectors: [
      { icon: "Zap", label: "Setup Integration", action: "setup-integration" },
      { icon: "Shield", label: "Sync Status Check", action: "sync-status" },
      {
        icon: "Settings",
        label: "Optimize Connections",
        action: "optimize-connections",
      },
    ],
    settings: [
      {
        icon: "Settings",
        label: "Optimize Settings",
        action: "optimize-settings",
      },
      { icon: "Shield", label: "Security Review", action: "security-review" },
      {
        icon: "Zap",
        label: "Performance Tuning",
        action: "performance-tuning",
      },
    ],
  };

  return {
    base: baseActions,
    specific: pageSpecificActions[view] || [],
  };
};

export const getContextualInitialMessage = (view: string): Message => {
  const context = pageContexts[view];

  return {
    id: "1",
    type: "assistant",
    content: `Hello! I'm Kogna, your strategic AI assistant. I can see you're currently in the ${
      context?.name || "Dashboard"
    } section.\n\nContext-Aware Capabilities:\n${
      context?.capabilities?.map((cap) => `• ${cap}`).join("\n") ||
      "• General assistance and insights"
    }\n\nI'm fully integrated with Kogna and can help you take actions directly within this context. How can I assist you today?`,
    timestamp: new Date(),
    suggestions: [
      `Analyze ${context?.name?.toLowerCase() || "current"} performance`,
      "What can you do in this section?",
      "Identify optimization opportunities",
      "Review strategic recommendations",
    ],
  };
};

export const generateAIResponse = (
  input: string,
  activeView: string
): string => {
  const responses: Record<string, string> = {
    "Ask about team optimization":
      "Great question! I'm analyzing your team composition in real-time:\n\nCurrent Status:\n• Sarah Chen: 75% capacity (optimal)\n• Marcus Rodriguez: 60% capacity (available)\n• Elena Kowalski: 45% capacity (underutilized)\n• David Kim: 85% capacity (near limit)\n• Priya Patel: 55% capacity (available)\n\nOptimization Recommendations:\n• Redistribute data analysis tasks from David to Elena\n• Assign Marcus to lead the new mobile initiative\n• Cross-train Priya on technical skills for better flexibility\n\nWould you like me to create a detailed rebalancing plan?",

    "Request detailed analysis":
      "I'll provide a comprehensive analysis of your current situation:\n\nPerformance Metrics:\n• Team Efficiency: 92% (↑8% vs last month)\n• Strategic Alignment: 87% with Q2 goals\n• Innovation Index: 74% (opportunity area)\n• Customer Satisfaction: 91% (industry leading)\n\nKey Insights:\n• Workflow automation could save 12 hours/week\n• Cross-functional collaboration up 23%\n• Technical debt decreased by 15%\n• New feature adoption at 78%\n\nAction Items:\n• Implement advanced analytics dashboard\n• Schedule innovation workshop\n• Review resource allocation\n\nShall I dive deeper into any specific area?",

    "What can you do in this section?": `In the ${
      pageContexts[activeView]?.name || "current section"
    }, I can help you:\n\n${
      pageContexts[activeView]?.capabilities
        ?.map((cap) => `• ${cap}`)
        .join("\n") || "• General assistance and insights"
    }\n\nAI-Powered Features:\n• Real-time optimization suggestions\n• Predictive analytics and insights\n• Automated workflow recommendations\n• Strategic planning assistance\n\nI'm continuously learning from your team's patterns to provide increasingly personalized recommendations. What would you like to explore first?`,
  };

  return (
    responses[input] ||
    `I understand you're asking about "${input}". Based on the current context in ${
      pageContexts[activeView]?.name || "this section"
    }, I can provide detailed insights and actionable recommendations.\n\nLet me analyze your specific situation and provide tailored advice. What aspect would you like me to focus on first?`
  );
};
