export interface Connector {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  status: 'connected' | 'available' | 'premium';
  category: 'project' | 'communication' | 'analytics' | 'storage';
  features: string[];
  setupTime: string;
  dataSync: string;
  isPremium?: boolean;
  isRecommended?: boolean;
}

export interface Category {
  id: string;
  name: string;
  icon: React.ReactNode;
}

export interface SyncMode {
  id: string;
  name: string;
  description: string;
  icon: string;
  features: string[];
  isPremium?: boolean;
}