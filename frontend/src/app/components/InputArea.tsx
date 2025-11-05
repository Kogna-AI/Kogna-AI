"use client"
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Send, MessageCircle } from 'lucide-react';

interface InputAreaProps {
  inputValue: string;
  setInputValue: (value: string) => void;
  onSendMessage: () => void;
  isTyping: boolean;
  onEnterConversationMode: () => void;
}

export function InputArea({ 
  inputValue, 
  setInputValue, 
  onSendMessage, 
  isTyping, 
  onEnterConversationMode 
}: InputAreaProps) {
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      onSendMessage();
    }
  };

  return (
    <div className="p-4 border-t border-border">
      <div className="flex gap-2">
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask Kognii anything..."
          className="flex-1"
          disabled={isTyping}
        />
        <Button 
          onClick={onSendMessage}
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
          onClick={onEnterConversationMode}
          className="text-xs text-muted-foreground hover:text-foreground"
        >
          <MessageCircle className="w-3 h-3 mr-2" />
          Enter Conversation AI
        </Button>
        
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          AI Active
        </div>
      </div>
    </div>
  );
}
