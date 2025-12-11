export interface Message {
  id: string;
  type: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  suggestions?: string[];
  teamSuggestion?: any;
}

export interface KogniiAssistantProps {
  onClose: () => void;
  strategySessionMode?: boolean;
  activeView: string;
  kogniiActions?: any;
}

export interface QuickAction {
  icon: any;
  label: string;
  action: string;
}

export interface DemoScenario {
  userInput: string;
  response: string;
}

export interface ConversationStep {
  user: string;
  kognii: string;
}

export interface PageContext {
  name: string;
  description: string;
  capabilities: string[];
}
