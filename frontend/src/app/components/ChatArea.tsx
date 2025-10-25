"use client"
import { useEffect, useRef } from 'react';
import { ScrollArea } from '../ui/scroll-area';
import { Bot } from 'lucide-react';
import { Message } from './types/KogniiTypes';
import { MessageBubble } from './MessageBubble';
import { KogniiThinkingIcon } from '../../../public/KogniiThinkingIcon';

interface ChatAreaProps {
  messages: Message[];
  isTyping: boolean;
  onSuggestionClick: (suggestion: string) => void;
}

export function ChatArea({ messages, isTyping, onSuggestionClick }: ChatAreaProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatAreaRef = useRef<HTMLDivElement>(null);

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

  return (
    <div className="flex-1 overflow-hidden">
      <ScrollArea className="h-full">
        <div ref={chatAreaRef} className="p-4">
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              onSuggestionClick={onSuggestionClick}
            />
          ))}
          
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
  );
}
