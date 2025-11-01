"use client"
import { useState, useEffect } from 'react';
import { KogniiAssistantProps, Message } from '../types/KogniiTypes';
import { 
  getDemoScenarios, 
  conversationScenario, 
  getPageQuickActions,  
  getContextualInitialMessage, 
  generateAIResponse 
} from '../utils/KogniiUtils';


export default function  useKogniiLogic({ onClose, strategySessionMode, activeView }: KogniiAssistantProps){
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [currentDemoStep, setCurrentDemoStep] = useState(0);
    const [conversationMode, setConversationMode] = useState(false);
    const [conversationStep, setConversationStep] = useState(0);
    const [isAutoPlaying, setIsAutoPlaying] = useState(false);
    
    const demoScenarios = getDemoScenarios(activeView);
    const quickActions = getPageQuickActions(activeView);

    return{ 
        //State
        messages,inputValue,isTyping, currentDemoStep,conversationMode, 
        

        // Handlers
        handleSendMessage, handleQuickAction, handleSuggestionClick,
        
        // Setters
     
        setInputValue,setConversationMode, setConversationStep, setIsAutoPlaying    , 
    
        // idk
        demoScenariosLength: demoScenarios.length,
   
        conversationStep, isAutoPlaying,
        onClose,
    
    }

}