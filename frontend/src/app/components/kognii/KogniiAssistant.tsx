"use client"
import { useState, useEffect } from 'react';
import { Button } from '../../ui/button';
import { X } from 'lucide-react';
import { KogniiThinkingIcon } from '../../../../public/KogniiThinkingIcon';
import { KogniiAssistantProps, Message } from './types/KogniiTypes';
import { 
  getDemoScenarios, 
  conversationScenario, 
  getPageQuickActions, 
  getContextualInitialMessage, 
  generateAIResponse 
} from './utils/KogniiUtils';
import { ChatArea } from '../ChatArea';
import { InputArea } from '../InputArea';
import { QuickActions } from '../QuickActions';
import { ConversationMode } from '../ConversationMode';
import Header from './Header'



export function KogniiAssistant({ onClose, strategySessionMode = false, activeView, kogniiActions }: KogniiAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionActive, setSessionActive] = useState(strategySessionMode);
  const [sessionStep, setSessionStep] = useState(0);
  const [currentContext, setCurrentContext] = useState(activeView);
  const [demoMode, setDemoMode] = useState(true);
  const [currentDemoStep, setCurrentDemoStep] = useState(0);
  const [conversationMode, setConversationMode] = useState(false);
  const [conversationStep, setConversationStep] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);

  const demoScenarios = getDemoScenarios(activeView);
  const quickActions = getPageQuickActions(activeView);

  // Initialize messages based on context
  useEffect(() => {
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
  }, [strategySessionMode, activeView, conversationMode]);


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

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: generateAIResponse(inputValue, activeView),
        timestamp: new Date(),
        suggestions: [
          'Tell me more about this',
          'Show me detailed analysis',
          'Create an action plan',
          'What should I do next?'
        ]
      };

      setMessages(prev => [...prev, aiMessage]);
      setIsTyping(false);
    }, 1500);
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
          content: generateAIResponse(suggestion, activeView),
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiResponse]);
        setIsTyping(false);
      }, 1500);
    }
  };


  const handleQuickAction = (action: string) => {
    // Generate contextual response for quick actions
    const actionResponses: Record<string, string> = {
      'create-objective': "🎯 I'll help you create a strategic objective! Let me guide you through the process:\n\nStep 1: Objective Framing\n• What's the primary goal you want to achieve?\n• Which strategic pillar does this support?\n• What's the target timeline?\n\nAI Suggestions:\n• Market expansion opportunity (+34% growth potential)\n• Technical modernization (reduce technical debt)\n• Customer experience enhancement\n\nI can also suggest optimal team compositions based on your objective. Shall we start with objective definition?",
      
      'team-optimize': "👥 Analyzing your team for optimization opportunities...\n\nCurrent Workload Distribution:\n• 2 team members over 80% capacity\n• 1 team member under 50% capacity\n• Skills gap in data analysis\n\nRecommended Actions:\n• Redistribute design tasks to balance workload\n• Cross-train Elena on analytics tools\n• Consider bringing David into strategic planning\n\nExpected Impact:\n• 15% improvement in delivery speed\n• Better work-life balance\n• Enhanced skill diversity\n\nShall I create a detailed rebalancing proposal?",
      
      'performance': "📊 Performance Analysis Complete\n\nYour team is performing excellently! Here's the breakdown:\n\nKey Metrics:\n• Overall efficiency: 92% (above industry average)\n• Goal alignment: 87% (strong strategic focus)\n• Innovation score: 74% (room for improvement)\n\nTrends:\n• Productivity increased 15% this quarter\n• Collaboration metrics up 23%\n• Technical quality improved significantly\n\nRecommendations:\n• Allocate 20% time for innovation projects\n• Implement advanced automation tools\n• Schedule strategy alignment session\n\nWould you like me to dive deeper into any specific metric?"
    };

    const response = actionResponses[action] || 
      `I'm analyzing the ${action} request. Let me provide you with actionable insights and recommendations.`;

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


  if (conversationMode) {
    return (
      <ConversationMode
        conversationScenario={conversationScenario}
        conversationStep={conversationStep}
        isAutoPlaying={isAutoPlaying}
        onClose={onClose}
        onExitConversationMode={exitConversationMode}
        onStartAutoPlay={startAutoPlay}
        onResetConversationDemo={resetConversationDemo}
        onNextConversationStep={nextConversationStep}
      />
    );
  }

  return (
    <div className="w-96 h-full bg-background border-l border-border shadow-xl flex flex-col">
      {/* Header */}
      <Header 
      onClose={onClose}
      />

      {/* Quick Actions */}
      <QuickActions
        quickActions={quickActions}
        onQuickAction={handleQuickAction}
        onDemoInput={handleDemoInput}
        onEnterConversationMode={() => setConversationMode(true)}
        currentDemoStep={currentDemoStep}
        demoScenariosLength={demoScenarios.length}
      />

      {/* Chat History */}
      <ChatArea
        messages={messages}
        isTyping={isTyping}
        onSuggestionClick={handleSuggestionClick}
      />

      {/* Input Area */}
      <InputArea
        inputValue={inputValue}
        setInputValue={setInputValue}
        onSendMessage={handleSendMessage}
        isTyping={isTyping}
        onEnterConversationMode={() => setConversationMode(true)}
      />
    </div>
  );
}