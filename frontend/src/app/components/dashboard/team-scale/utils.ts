import { objectiveHiringTriggers } from './constants';

export interface Objective {
  id: number;
  title: string;
  category: string;
  progress: number;
  priority: string;
}

export const generateContextualRecommendations = (objectives: Objective[]) => {
  const recommendations: any[] = [];
  
  objectives.forEach(objective => {
    const trigger = objectiveHiringTriggers[objective.title as keyof typeof objectiveHiringTriggers];
    if (trigger) {
      recommendations.push({
        objectiveTitle: objective.title,
        objectiveProgress: objective.progress,
        priority: objective.priority,
        immediateNeeds: trigger.immediateNeeds,
        futureNeeds: trigger.futureNeeds,
        urgency: trigger.urgency,
        reasoning: `Based on "${objective.title}" objective progress (${objective.progress}%), immediate hiring focus should be on ${trigger.immediateNeeds.join(', ')}`
      });
    }
  });

  return recommendations;
};

export const getUrgencyColor = (urgency: string) => {
  switch (urgency) {
    case 'critical': return 'text-red-600 bg-red-50 border-red-200';
    case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
    case 'medium': return 'text-blue-600 bg-blue-50 border-blue-200';
    default: return 'text-gray-600 bg-gray-50 border-gray-200';
  }
};

export const getRoleResponsibilities = (role: string) => {
  if (role?.includes('Engineer')) {
    return [
      '• Design and implement scalable robotic systems',
      '• Collaborate with cross-functional teams',
      '• Ensure system reliability and performance'
    ];
  }
  if (role?.includes('Manager')) {
    return [
      '• Lead and develop team members',
      '• Drive strategic initiatives and execution',
      '• Manage stakeholder relationships'
    ];
  }
  if (role?.includes('Designer')) {
    return [
      '• Create intuitive user experiences',
      '• Conduct user research and testing',
      '• Maintain design system consistency'
    ];
  }
  return [
    '• Drive strategic initiatives and execution',
    '• Collaborate with cross-functional teams',
    '• Deliver high-quality results on time'
  ];
};