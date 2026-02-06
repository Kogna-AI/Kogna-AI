"use client"
import { useRef, useEffect } from 'react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Send } from 'lucide-react';

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
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize logic
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      // 1. Reset height to allow shrinking (must match min-height)
      textarea.style.height = '36px'; 
      
      // 2. Calculate new height
      const scrollHeight = textarea.scrollHeight;
      
      // 3. Apply new height if it exceeds the minimum, capped by CSS max-h
      if (scrollHeight > 36) {
        textarea.style.height = `${scrollHeight}px`;
      }
    }
  }, [inputValue]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Prevent new line
      onSendMessage();
    }
  };

  return (
    <div className="p-3 border-t border-white/20">
      <div className="w-full">
        <Textarea
          ref={textareaRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="Ask Kogna anything..."
          // Styles:
          // min-h-[36px]: Slightly smaller height
          // py-[7px]: Centers text vertically in 36px height
          // resize-none: Removes drag handle
          className="flex-1 bg-transparent border-white/10 text-white placeholder:text-white/30 focus-visible:ring-blue-500/50 focus-visible:border-blue-500/50 min-h-[36px] max-h-[120px] resize-none py-[7px] leading-snug"
          disabled={isTyping}
          rows={1}
          style={{ height: '36px' }} // Force initial height inline
        />
      </div>
      
      <div className="flex items-center justify-between mt-2">
        <div className="flex items-center gap-2 text-xs text-white/50 pl-1">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse shadow-[0_0_8px_rgba(74,222,128,0.5)]"></div>
          AI Active
        </div>

        <Button 
          onClick={onSendMessage}
          disabled={!inputValue.trim() || isTyping}
          size="sm"
          className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white border-0 px-4 h-8"
        >
          <Send className="w-4 h-4" />
          <span className="sr-only">Send</span>
        </Button>
      </div>
    </div>
  );
}