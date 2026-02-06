"use client"
import { Button } from '../ui/button';
import { Bot } from 'lucide-react';
import { Message } from './kognii/types/KogniiTypes';

interface MessageBubbleProps {
  message: Message;
  isLast: boolean; // Added prop
  onSuggestionClick: (suggestion: string) => void;
}

export function MessageBubble({ message, isLast, onSuggestionClick }: MessageBubbleProps) {
  const isUser = message.type === 'user';

  return (
    <div className={`flex flex-col gap-2 mb-6 ${isUser ? 'items-end' : 'items-start'}`}>
      
      {/* AI Header: Icon Above Text */}
      {!isUser && (
        <div className="flex items-center gap-2 mb-1">
          <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg ring-1 ring-white/20">
            <Bot className="w-3 h-3 text-white" />
          </div>
          <span className="text-xs font-medium text-blue-200/80">Kogna</span>
        </div>
      )}
      
      <div className={`max-w-[90%] ${isUser ? '' : ''}`}>
        <div className={`
          ${isUser 
            ? 'bg-blue-500/20 border border-blue-400/30 text-white rounded-2xl rounded-tr-sm p-3 backdrop-blur-md' 
            : 'text-white/90 leading-relaxed pl-1' // AI: No Box, Just Text
          }
        `}>
          <div className="text-sm whitespace-pre-line">
            {message.content}
          </div>
        </div>
        
        {/* Suggestions - Only show if it's the LAST message */}
        {isLast && message.suggestions && message.suggestions.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3 pl-1 animate-in fade-in duration-500 slide-in-from-bottom-2">
            {message.suggestions.map((suggestion, index) => (
              <Button
                key={index}
                variant="outline"
                size="sm"
                onClick={() => onSuggestionClick(suggestion)}
                className="text-xs h-7 px-3 rounded-full bg-white/5 border-white/10 text-white/70 hover:text-white hover:bg-white/10 hover:border-white/30 transition-colors"
              >
                {suggestion}
              </Button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}