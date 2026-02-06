"use client";
import { useState, useEffect } from "react";
import { KogniiAssistantProps, Message } from "./types/KogniiTypes";
import {
  getDemoScenarios,
  conversationScenario,
  getPageQuickActions,
  getContextualInitialMessage,
} from "./utils/KogniiUtils";
import { ChatArea } from "../ChatArea";
import { InputArea } from "../InputArea";
import { QuickActions } from "../QuickActions";
import { ConversationMode } from "../ConversationMode";
import Header from "./Header";
import { api } from "@/services/api";

export function KogniiAssistant({
  onClose,
  strategySessionMode = false,
  activeView,
  kogniiActions,
}: KogniiAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
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

  const demoScenarios = getDemoScenarios(activeView);
  const quickActions = getPageQuickActions(activeView);

  useEffect(() => {
    const initializeChat = async () => {
      try {
        const session = await api.startChatSession();
        setSessionId(session.id);
        console.log("Chat Session Started:", session.id);
      } catch (error) {
        console.error("Failed to start session:", error);
      }

      if (strategySessionMode) {
        setMessages([
          {
            id: "session-1",
            type: "assistant",
            content:
              "Welcome to your AI Strategy Session! I'll guide you through a structured strategic planning process. We'll cover strategic analysis, goal setting, and action planning. Ready to begin?",
            timestamp: new Date(),
            suggestions: [
              "Start with SWOT Analysis",
              "Begin Strategic Goal Setting",
              "Review Current Performance",
              "Analyze Market Opportunities",
            ],
          },
        ]);
      } else if (!conversationMode) {
        setMessages([getContextualInitialMessage(activeView)]);
      }
    };

    initializeChat();
  }, [strategySessionMode, activeView, conversationMode]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isAutoPlaying && conversationStep < conversationScenario.length - 1) {
      interval = setInterval(() => {
        setConversationStep((prev) => {
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

  const processUserMessage = async (text: string) => {
    if (!sessionId) {
      setMessages((prev) => [
        ...prev,
        {
          id: "error-no-session",
          type: "assistant",
          content: "Connection error: No active session. Please reopen the chat.",
          timestamp: new Date(),
        },
      ]);
      return;
    }

    const userMsgId = Date.now().toString();
    const userMessage: Message = {
      id: userMsgId,
      type: "user",
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    try {
      const apiResponse = await api.runAgentInSession(
        sessionId,
        text,
        "auto"
      );

      let aiContent = apiResponse.final_report;

      if (!aiContent) {
        aiContent = "I processed your request, but the response was empty.";
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: aiContent,
        timestamp: new Date(),
        suggestions: ["Tell me more", "Explain the details"],
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("Failed to send message:", error);
      let errorString = "Unknown error";
      if (error instanceof Error) errorString = error.message;

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: `I'm having trouble connecting to the server.\n\nError: ${errorString}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;
    const textToSend = inputValue;
    setInputValue("");
    processUserMessage(textToSend);
  };

  const handleDemoInput = () => {
    if (currentDemoStep < demoScenarios.length) {
      const scenario = demoScenarios[currentDemoStep];
      const userMessage: Message = {
        id: `demo-user-${Date.now()}`,
        type: "user",
        content: scenario.userInput,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsTyping(true);

      setTimeout(() => {
        const aiMessage: Message = {
          id: `demo-ai-${Date.now()}`,
          type: "assistant",
          content: scenario.response,
          timestamp: new Date(),
          suggestions:
            currentDemoStep < demoScenarios.length - 1
              ? [
                  "Continue demo conversation",
                  "Ask about team optimization",
                  "Request detailed analysis",
                ]
              : [
                  "Start new conversation",
                  "Enter conversation mode",
                  "Ask another question",
                ],
        };

        setMessages((prev) => [...prev, aiMessage]);
        setIsTyping(false);
        setCurrentDemoStep((prev) => prev + 1);
      }, 1500);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    if (
      suggestion === "Continue demo conversation" &&
      currentDemoStep < demoScenarios.length
    ) {
      handleDemoInput();
      return;
    }
    if (suggestion === "Enter conversation mode") {
      setConversationMode(true);
      setMessages([]);
      setCurrentDemoStep(0);
      return;
    }
    if (suggestion === "Start new conversation") {
      setCurrentDemoStep(0);
      setMessages([getContextualInitialMessage(activeView)]);
      return;
    }
    processUserMessage(suggestion);
  };

  const handleQuickAction = (action: string) => {
    const prompts: Record<string, string> = {
      "create-objective": "Help me create a strategic objective",
      "team-optimize": "Analyze our team optimization opportunities",
      "performance": "Analyze our current performance trends",
    };
    const prompt = prompts[action] || `Tell me about ${action}`;
    processUserMessage(prompt);
  };

  const nextConversationStep = () => {
    if (conversationStep < conversationScenario.length - 1) {
      setConversationStep((prev) => prev + 1);
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
    <div className="w-96 h-full bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 relative overflow-hidden flex flex-col shadow-2xl">
      {/* Animated Background Layers */}
      <div className="absolute inset-0 opacity-30 pointer-events-none">
        <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-blue-400 to-purple-600 animate-pulse"></div>
        <div className="absolute top-1/4 left-1/4 w-24 h-24 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-full blur-3xl animate-bounce" style={{ animationDuration: '3s' }}></div>
        <div className="absolute bottom-1/4 right-1/4 w-20 h-20 bg-gradient-to-br from-purple-400 to-pink-600 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '2s' }}></div>
        <div className="absolute top-1/2 right-1/3 w-16 h-16 bg-gradient-to-br from-indigo-400 to-purple-600 rounded-full blur-3xl animate-bounce" style={{ animationDuration: '4s' }}></div>
      </div>

      <div className="relative z-10 flex flex-col h-full bg-black/10 backdrop-blur-sm">
        <Header onClose={onClose} activeView={activeView} />

        <QuickActions
          quickActions={quickActions}
          onQuickAction={handleQuickAction}
          onDemoInput={handleDemoInput}
          onEnterConversationMode={() => setConversationMode(true)}
          currentDemoStep={currentDemoStep}
          demoScenariosLength={demoScenarios.length}
        />

        <ChatArea
          messages={messages}
          isTyping={isTyping}
          onSuggestionClick={handleSuggestionClick}
        />

        <InputArea
          inputValue={inputValue}
          setInputValue={setInputValue}
          onSendMessage={handleSendMessage}
          isTyping={isTyping}
          onEnterConversationMode={() => setConversationMode(true)}
        />
      </div>
    </div>
  );
}