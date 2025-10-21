"use client"

import { ReactPortal, Key, ReactElement, ReactNode, JSXElementConstructor, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { Button } from '../../ui/button';
import { Badge } from '../../ui/badge';
import { 
  Database, 
  Plug, 
  CheckCircle, 
  BarChart3,
  Settings,
  Crown,
  Sparkles,
  Shield,
  Zap,
  AlertCircle
} from 'lucide-react';
import { connectors, categories } from './connector-hub/constants';
import { getStatusIcon, getStatusText } from './connector-hub/utils';
import { SetupDialog } from './connector-hub/SetupDialog';
import { Connector } from './connector-hub/types';

export function DataConnectorHub() {
  const [selectedConnector, setSelectedConnector] = useState<Connector | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const filteredConnectors = selectedCategory === 'all' 
    ? connectors 
    : connectors.filter((connector: { category: string; }) => connector.category === selectedCategory);

  const kognaCoreConnector = connectors.find((c: { id: string; }) => c.id === 'kognacore');

  interface Category{
    id: string;
    icon: React.ReactNode;
    name: string;
  }


  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Data Connector Hub</h1>
          <p className="text-muted-foreground">
            Connect your existing tools and data sources for comprehensive project insights
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-green-600 border-green-200">
            <CheckCircle className="w-3 h-3 mr-1" />
            3 Connected
          </Badge>
          <Badge variant="outline" className="text-blue-600 border-blue-200">
            <Database className="w-3 h-3 mr-1" />
            8 Available
          </Badge>
        </div>
      </div>

      {/* KognaCore Highlight */}
      {kognaCoreConnector && (
        <Card className="border-2 border-amber-200 bg-gradient-to-r from-amber-50 via-orange-50 to-amber-50 shadow-lg">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center">
                  <Crown className="w-6 h-6 text-white" />
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-lg font-semibold">{kognaCoreConnector.name}</h3>
                    <Badge className="bg-gradient-to-r from-amber-400 to-orange-500 text-white">
                      <Sparkles className="w-3 h-3 mr-1" />
                      Recommended
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">
                    {kognaCoreConnector.description}
                  </p>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Shield className="w-3 h-3" />
                      Enterprise Security
                    </span>
                    <span className="flex items-center gap-1">
                      <Zap className="w-3 h-3" />
                      Real-time Sync
                    </span>
                    <span className="flex items-center gap-1">
                      <BarChart3 className="w-3 h-3" />
                      Advanced Analytics
                    </span>
                  </div>
                </div>
              </div>
              <Button 
                className="bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700"
                onClick={() => setSelectedConnector(kognaCoreConnector)}
              >
                Explore KognaCore
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Category Filter */}
      <div className="flex gap-2 overflow-x-auto">
        {categories.map((category: Category) => (
          <Button
            key={category.id}
            variant={selectedCategory === category.id ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedCategory(category.id)}
            className="flex items-center gap-2 whitespace-nowrap"
          >
            {category.icon}
            {category.name}
          </Button>
        ))}
      </div>

      {/* Connectors Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredConnectors.filter((c: { id: string; }) => c.id !== 'kognacore').map((connector: { id: Key | null | undefined; icon: string | number | bigint | boolean | ReactElement<unknown, string | JSXElementConstructor<any>> | Iterable<ReactNode> | ReactPortal | Promise<string | number | bigint | boolean | ReactPortal | ReactElement<unknown, string | JSXElementConstructor<any>> | Iterable<ReactNode> | null | undefined> | null | undefined; name: string | number | bigint | boolean | ReactElement<unknown, string | JSXElementConstructor<any>> | Iterable<ReactNode> | ReactPortal | Promise<string | number | bigint | boolean | ReactPortal | ReactElement<unknown, string | JSXElementConstructor<any>> | Iterable<ReactNode> | null | undefined> | null | undefined; status: string; description: string | number | bigint | boolean | ReactElement<unknown, string | JSXElementConstructor<any>> | Iterable<ReactNode> | ReactPortal | Promise<string | number | bigint | boolean | ReactPortal | ReactElement<unknown, string | JSXElementConstructor<any>> | Iterable<ReactNode> | null | undefined> | null | undefined; setupTime: string | number | bigint | boolean | ReactElement<unknown, string | JSXElementConstructor<any>> | Iterable<ReactNode> | ReactPortal | Promise<string | number | bigint | boolean | ReactPortal | ReactElement<unknown, string | JSXElementConstructor<any>> | Iterable<ReactNode> | null | undefined> | null | undefined; dataSync: string | number | bigint | boolean | ReactElement<unknown, string | JSXElementConstructor<any>> | Iterable<ReactNode> | ReactPortal | Promise<string | number | bigint | boolean | ReactPortal | ReactElement<unknown, string | JSXElementConstructor<any>> | Iterable<ReactNode> | null | undefined> | null | undefined; features: any[]; }) => (
          <Card key={connector.id} className="hover:shadow-md transition-shadow cursor-pointer group">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  {connector.icon}
                  <CardTitle className="text-base">{connector.name}</CardTitle>
                </div>
                <div className="flex items-center gap-1">
                  {getStatusIcon(connector.status)}
                  <span className="text-xs text-muted-foreground">
                    {getStatusText(connector.status)}
                  </span>
                </div>
              </div>
              <CardDescription className="text-sm">
                {connector.description}
              </CardDescription>
            </CardHeader>
            
            <CardContent className="pt-0">
              <div className="space-y-3">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Setup: {connector.setupTime}</span>
                  <span>Sync: {connector.dataSync}</span>
                </div>
                
                <div className="flex flex-wrap gap-1">
                  {connector.features.slice(0, 2).map((feature: string | number | bigint | boolean | ReactElement<unknown, string | JSXElementConstructor<any>> | Iterable<ReactNode> | ReactPortal | Promise<string | number | bigint | boolean | ReactPortal | ReactElement<unknown, string | JSXElementConstructor<any>> | Iterable<ReactNode> | null | undefined> | null | undefined, index: Key | null | undefined) => (
                    <Badge key={index} variant="secondary" className="text-xs">
                      {feature}
                    </Badge>
                  ))}
                  {connector.features.length > 2 && (
                    <Badge variant="outline" className="text-xs">
                      +{connector.features.length - 2} more
                    </Badge>
                  )}
                </div>

                <Button 
                  className="w-full group-hover:bg-primary group-hover:text-primary-foreground transition-colors"
                  variant={connector.status === 'connected' ? 'outline' : 'default'}
                  onClick={() => setSelectedConnector(connector as Connector)}
                >
                  <Plug className="w-4 h-4 mr-2" />
                  {connector.status === 'connected' ? 'Manage' : 'Connect'}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Integration Stats & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Integration Overview
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">3</div>
                <div className="text-sm text-muted-foreground">Active Connections</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">24/7</div>
                <div className="text-sm text-muted-foreground">Real-time Monitoring</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">99.9%</div>
                <div className="text-sm text-muted-foreground">Uptime</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">15min</div>
                <div className="text-sm text-muted-foreground">Avg Sync Time</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              Quick Actions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button variant="outline" className="w-full justify-start gap-2">
              <Zap className="w-4 h-4" />
              Sync All Data
            </Button>
            <Button variant="outline" className="w-full justify-start gap-2">
              <Shield className="w-4 h-4" />
              Security Settings
            </Button>
            <Button variant="outline" className="w-full justify-start gap-2">
              <AlertCircle className="w-4 h-4" />
              Connection Health
            </Button>
          </CardContent>
        </Card>
      </div>

      <SetupDialog 
        connector={selectedConnector} 
        onClose={() => setSelectedConnector(null)}
      />
    </div>
  );
}