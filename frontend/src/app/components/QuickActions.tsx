"use client"
import { Button } from '../ui/button';
import { 
  TrendingUp, Target, AlertTriangle, Lightbulb, BarChart3, Users, Eye, 
  UserPlus, LineChart, PlusCircle, Filter, Share, Calendar, MessageCircle, 
  CheckCircle, Shield, Zap, Settings, Play
} from 'lucide-react';
import { KogniiThinkingIcon } from '../../../public/KogniiThinkingIcon';
import { QuickAction } from './kognii/types/KogniiTypes';

interface QuickActionsProps {
  quickActions: {
    base: QuickAction[];
    specific: QuickAction[];
  };
  onQuickAction: (action: string) => void;
  onDemoInput: () => void;
  onEnterConversationMode: () => void;
  currentDemoStep: number;
  demoScenariosLength: number;
}

const iconMap: Record<string, any> = {
  'TrendingUp': TrendingUp, 'Target': Target, 'AlertTriangle': AlertTriangle,
  'Lightbulb': Lightbulb, 'BarChart3': BarChart3, 'Users': Users, 'Eye': Eye,
  'UserPlus': UserPlus, 'LineChart': LineChart, 'PlusCircle': PlusCircle,
  'Filter': Filter, 'Share': Share, 'Calendar': Calendar, 'MessageCircle': MessageCircle,
  'CheckCircle': CheckCircle, 'Shield': Shield, 'Zap': Zap, 'Settings': Settings
};

export function QuickActions({ 
  quickActions, onQuickAction, onDemoInput, onEnterConversationMode, 
  currentDemoStep, demoScenariosLength 
}: QuickActionsProps) {
  
  const glassBtnClass = "gap-2 text-xs h-8 rounded-full bg-white/5 border-white/10 text-white/90 hover:bg-white/15 hover:text-white hover:border-white/30 transition-all";

  return (
    <div className="p-4 border-b border-white/10">
      <div className="space-y-3">
        <div className="flex flex-wrap gap-2">
          {quickActions.base.map((action, index) => {
            const IconComponent = iconMap[action.icon] || Target;
            return (
              <Button
                key={index}
                variant="outline"
                size="sm"
                onClick={() => onQuickAction(action.action)}
                className={glassBtnClass}
              >
                <IconComponent className="w-3 h-3" />
                {action.label}
              </Button>
            );
          })}
        </div>
        
        {quickActions.specific.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {quickActions.specific.map((action, index) => {
              const IconComponent = iconMap[action.icon] || Target;
              return (
                <Button
                  key={index}
                  variant="secondary"
                  size="sm"
                  onClick={() => onQuickAction(action.action)}
                  className={`${glassBtnClass} bg-white/10 border-white/20`}
                >
                  <IconComponent className="w-3 h-3" />
                  {action.label}
                </Button>
              );
            })}
          </div>
        )}
      </div>

      <div className="flex gap-2 mt-3">
        <Button
          variant="outline"
          size="sm"
          onClick={onDemoInput}
          disabled={currentDemoStep >= demoScenariosLength}
          className={`flex-1 ${glassBtnClass}`}
        >
          <Play className="w-3 h-3 mr-2" />
          Demo Chat
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onEnterConversationMode}
          className={`flex-1 ${glassBtnClass} bg-indigo-500/20 border-indigo-400/30 hover:bg-indigo-500/30`}
        >
          <KogniiThinkingIcon className="w-3 h-3 mr-2" />
          Deep Mode
        </Button>
      </div>
    </div>
  );
}