"use client"
import { Button } from '../ui/button';
import { Bot, User } from 'lucide-react';
import { Message } from './kognii/types/KogniiTypes';

interface MessageBubbleProps {
  message: Message;
  onSuggestionClick: (suggestion: string) => void;
}

export function MessageBubble({ message, onSuggestionClick }: MessageBubbleProps) {
  return (
    <div className={`flex gap-3 mb-4 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
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
                onClick={() => onSuggestionClick(suggestion)}
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
}
