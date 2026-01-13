"use client"
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { 
  X, 
  ArrowLeft, 
  ArrowRight, 
  AlertTriangle, 
  CheckCircle 
} from 'lucide-react';
import { KogniiThinkingIcon } from '../../../public/KogniiThinkingIcon';
import { ConversationStep } from './kognii/types/KogniiTypes';

interface ConversationModeProps {
  conversationScenario: ConversationStep[];
  conversationStep: number;
  isAutoPlaying: boolean;
  onClose: () => void;
  onExitConversationMode: () => void;
  onStartAutoPlay: () => void;
  onResetConversationDemo: () => void;
  onNextConversationStep: () => void;
}

export function ConversationMode({
  conversationScenario,
  conversationStep,
  isAutoPlaying,
  onClose,
  onExitConversationMode,
  onStartAutoPlay,
  onResetConversationDemo,
  onNextConversationStep
}: ConversationModeProps) {
  return (
    <div className="w-96 h-full bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-blue-400 to-purple-600 animate-pulse"></div>
        <div className="absolute top-1/4 left-1/4 w-24 h-24 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-full blur-3xl animate-bounce" style={{ animationDuration: '3s' }}></div>
        <div className="absolute bottom-1/4 right-1/4 w-20 h-20 bg-gradient-to-br from-purple-400 to-pink-600 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '2s' }}></div>
        <div className="absolute top-1/2 right-1/3 w-16 h-16 bg-gradient-to-br from-indigo-400 to-purple-600 rounded-full blur-3xl animate-bounce" style={{ animationDuration: '4s' }}></div>
      </div>

      {/* Content */}
      <div className="relative z-10 h-full p-4 flex flex-col">
        <div className="bg-white/5 backdrop-blur-lg rounded-xl border border-white/10 h-full p-4 flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={onExitConversationMode}
                className="text-white/80 hover:text-white hover:bg-white/10"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Chat
              </Button>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose} className="text-white/80 hover:text-white hover:bg-white/10">
              <X className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-400 to-purple-600 flex items-center justify-center shadow-lg">
              <KogniiThinkingIcon className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-white">Conversation Mode</h3>
              <p className="text-xs text-white/60">Immersive AI strategic planning</p>
            </div>
          </div>

          {/* Control Panel */}
          <div className="mb-4 flex items-center justify-center gap-2">
            <Button 
              onClick={onStartAutoPlay}
              disabled={isAutoPlaying || conversationStep >= conversationScenario.length - 1}
              size="sm"
              className="gap-2 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-xs"
            >
              <KogniiThinkingIcon className="w-3 h-3" />
              {isAutoPlaying ? 'Auto-Playing...' : 'Start Auto Demo'}
            </Button>
            <Button 
              onClick={onResetConversationDemo}
              variant="outline"
              size="sm"
              className="gap-2 border-white/20 text-white/80 hover:text-white hover:bg-white/10 text-xs"
            >
              Reset Demo
            </Button>
          </div>

          {/* Conversation Content */}
          <div className="flex-1 bg-white/5 backdrop-blur border border-white/10 rounded-lg p-4 overflow-hidden">
            <div className="space-y-4 h-full flex flex-col">
              {/* Live Analysis Indicator */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm text-white/60">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  AI Analysis Active
                </div>
                <Badge className="bg-green-500/20 text-green-300 border-green-400/30">
                  Step {conversationStep + 1} of {conversationScenario.length}
                </Badge>
              </div>

              {/* Active Conversation */}
              <div className="flex-1 space-y-3 overflow-y-auto">
                <div className="bg-blue-500/10 p-3 rounded border border-blue-400/20">
                  <div className="text-xs text-blue-300 mb-2 flex items-center gap-2">
                    <div className="w-5 h-5 rounded-full bg-gradient-to-br from-gray-400 to-gray-600 flex items-center justify-center text-xs font-medium text-white">
                      A
                    </div>
                    Allen (Founder)
                  </div>
                  <p className="text-sm text-white/90 leading-relaxed">
                    {conversationScenario[conversationStep]?.user}
                  </p>
                </div>
                <div className="bg-purple-500/10 p-3 rounded border border-purple-400/20">
                  <div className="text-xs text-purple-300 mb-2 flex items-center gap-2">
                    <div className="w-5 h-5 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                      <KogniiThinkingIcon className="w-3 h-3 text-white" />
                    </div>
                    Kognii AI
                  </div>
                  <p className="text-sm text-white/90 leading-relaxed">
                    {conversationScenario[conversationStep]?.kognii}
                  </p>
                </div>

                {/* Live Metrics */}
                {conversationStep >= 1 && (
                  <div className="bg-orange-500/10 backdrop-blur border border-orange-400/20 rounded-lg p-3 animate-in slide-in-from-bottom duration-500">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle className="w-4 h-4 text-orange-300" />
                      <span className="text-sm font-medium text-white">Risk Assessment</span>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                        <span className="text-xs text-white/80">Mobile dev 2 weeks behind</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                        <span className="text-xs text-white/80">Resource bottleneck detected</span>
                      </div>
                    </div>
                  </div>
                )}

                {conversationStep >= 2 && (
                  <div className="bg-green-500/10 backdrop-blur border border-green-400/20 rounded-lg p-3 animate-in slide-in-from-bottom duration-700">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="w-4 h-4 text-green-300" />
                      <span className="text-sm font-medium text-white">AI Recommendations</span>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                        <span className="text-xs text-white/80">Move Sarah to mobile team (85% match)</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                        <span className="text-xs text-white/80">Hire contractor for analytics (temp solution)</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Action Button */}
              <Button 
                onClick={onNextConversationStep}
                className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
                disabled={isAutoPlaying}
              >
                <ArrowRight className="w-4 h-4 mr-2" />
                {conversationStep < conversationScenario.length - 1 ? 'Continue Analysis' : 'Complete Session'}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
