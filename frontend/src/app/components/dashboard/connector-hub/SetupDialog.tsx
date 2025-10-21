import { useState } from 'react';
import { Card, CardContent } from '../../../ui/card';
import { Button } from '../../../ui/button';
import { Badge } from '../../../ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../../../ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../ui/tabs';
import { Input } from '../../../ui/input';
import { Label } from '../../../ui/label';
import { RadioGroup, RadioGroupItem } from '../../../ui/radio-group';
import { Switch } from '../../../ui/switch';
import { 
  Clock, 
  Zap, 
  Crown, 
  CheckCircle, 
  Sparkles,
  ExternalLink,
  ArrowLeftRight,
  ArrowRight,
  Shield,
  AlertCircle
} from 'lucide-react';
import { Connector } from './types';
import { syncModes } from './constants';

interface SetupDialogProps {
  connector: Connector | null;
  onClose: () => void;
}

export function SetupDialog({ connector, onClose }: SetupDialogProps) {
  const [selectedSyncMode, setSelectedSyncMode] = useState('one-way');
  const [enableRealTimeSync, setEnableRealTimeSync] = useState(true);
  
  if (!connector) return null;

  return (
    <Dialog open={!!connector} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            {connector.icon}
            Connect {connector.name}
            {connector.isRecommended && (
              <Badge className="bg-gradient-to-r from-amber-400 to-orange-500 text-white">
                <Sparkles className="w-3 h-3 mr-1" />
                Recommended
              </Badge>
            )}
          </DialogTitle>
          <DialogDescription>
            {connector.description}
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="sync">Sync Mode</TabsTrigger>
            <TabsTrigger value="setup">Setup</TabsTrigger>
            <TabsTrigger value="features">Features</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Card>
                <CardContent className="pt-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Clock className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Setup Time</span>
                  </div>
                  <p className="text-2xl font-bold">{connector.setupTime}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Zap className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Data Sync</span>
                  </div>
                  <p className="text-2xl font-bold">{connector.dataSync}</p>
                </CardContent>
              </Card>
            </div>

            {connector.isPremium && (
              <Card className="border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50">
                <CardContent className="pt-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Crown className="w-5 h-5 text-amber-600" />
                    <span className="font-semibold text-amber-800">Premium Native Integration</span>
                  </div>
                  <p className="text-sm text-amber-700">
                    Get the deepest insights and most advanced features with our native WBS system. 
                    Includes AI-powered optimization, predictive analytics, and real-time team balancing.
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="setup" className="space-y-4">
            {connector.id === 'kognacore' ? (
              <div className="space-y-4">
                <Card className="border-green-200 bg-green-50">
                  <CardContent className="pt-4">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <span className="font-semibold text-green-800">KognaCore is Built-in!</span>
                    </div>
                    <p className="text-sm text-green-700 mb-4">
                      KognaCore is already integrated into your KognaDash. Simply start creating projects to experience the full power of our AI-driven WBS system.
                    </p>
                    <Button className="bg-green-600 hover:bg-green-700">
                      Start Using KognaCore
                    </Button>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-medium">
                    1
                  </div>
                  <span className="font-medium">Authentication</span>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <Label htmlFor="api-endpoint">API Endpoint/Server URL</Label>
                    <Input 
                      id="api-endpoint" 
                      placeholder={`Enter your ${connector.name} instance URL`}
                    />
                  </div>
                  <div>
                    <Label htmlFor="api-key">API Key/Token</Label>
                    <Input 
                      id="api-key" 
                      type="password"
                      placeholder="Enter your API key or access token"
                    />
                  </div>
                  {connector.id === 'jira' && (
                    <div>
                      <Label htmlFor="username">Username/Email</Label>
                      <Input 
                        id="username" 
                        placeholder="Enter your Jira username or email"
                      />
                    </div>
                  )}
                </div>

                <div className="flex gap-2 mt-6">
                  <Button className="flex-1">
                    Test Connection
                  </Button>
                  <Button variant="outline">
                    <ExternalLink className="w-4 h-4 mr-2" />
                    Get API Key
                  </Button>
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="features" className="space-y-4">
            <div className="grid gap-3">
              {connector.features.map((feature, index) => (
                <div key={index} className="flex items-center gap-3 p-3 border rounded-lg">
                  <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                  <span>{feature}</span>
                </div>
              ))}
            </div>
            
            {connector.isPremium && (
              <Card className="border-blue-200 bg-blue-50">
                <CardContent className="pt-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="w-5 h-5 text-blue-600" />
                    <span className="font-semibold text-blue-800">AI-Enhanced Features</span>
                  </div>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• Intelligent workload distribution</li>
                    <li>• Predictive project timeline optimization</li>
                    <li>• Automated risk assessment</li>
                    <li>• Smart team composition suggestions</li>
                  </ul>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="sync" className="space-y-4">
            <Card>
              <CardContent className="pt-4">
                <div className="space-y-4">
                  <div>
                    <Label className="text-base font-semibold">Choose Sync Mode</Label>
                    <p className="text-sm text-muted-foreground mb-4">
                      Select how data should flow between KognaDash and {connector.name}
                    </p>
                  </div>

                  <RadioGroup value={selectedSyncMode} onValueChange={setSelectedSyncMode}>
                    {syncModes.map((mode) => (
                      <div key={mode.id} className="space-y-2">
                        <div className="flex items-center space-x-2">
                          <RadioGroupItem 
                            value={mode.id} 
                            id={mode.id}
                            disabled={mode.isPremium && connector.id !== 'kognacore'}
                          />
                          <Label htmlFor={mode.id} className="flex items-center gap-2 cursor-pointer">
                            <span className="text-lg">{mode.icon}</span>
                            {mode.name}
                            {mode.isPremium && (
                              <Badge className="bg-gradient-to-r from-amber-400 to-orange-500 text-white text-xs">
                                Premium
                              </Badge>
                            )}
                          </Label>
                        </div>
                        <p className="text-sm text-muted-foreground ml-6">{mode.description}</p>
                        
                        {selectedSyncMode === mode.id && (
                          <Card className="ml-6 border-blue-200 bg-blue-50/50">
                            <CardContent className="pt-3 pb-3">
                              <div className="space-y-2">
                                <p className="text-sm font-medium text-blue-900">Features included:</p>
                                <ul className="text-sm text-blue-700 space-y-1">
                                  {mode.features.map((feature, index) => (
                                    <li key={index} className="flex items-center gap-2">
                                      <CheckCircle className="w-3 h-3" />
                                      {feature}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            </CardContent>
                          </Card>
                        )}
                      </div>
                    ))}
                  </RadioGroup>

                  {selectedSyncMode === 'two-way' && (
                    <div className="space-y-4 pt-4 border-t">
                      <div>
                        <Label className="text-base font-semibold">Two-way Sync Options</Label>
                        <p className="text-sm text-muted-foreground">
                          Configure how bidirectional sync should work
                        </p>
                      </div>

                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <Label htmlFor="real-time-sync">Real-time Sync</Label>
                            <p className="text-sm text-muted-foreground">
                              Changes sync immediately as they happen
                            </p>
                          </div>
                          <Switch
                            id="real-time-sync"
                            checked={enableRealTimeSync}
                            onCheckedChange={setEnableRealTimeSync}
                          />
                        </div>

                        <Card className="border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50">
                          <CardContent className="pt-4">
                            <div className="flex items-start gap-3">
                              <Crown className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                              <div>
                                <p className="font-semibold text-amber-800 mb-1">KognaDash Two-way Benefits</p>
                                <ul className="text-sm text-amber-700 space-y-1">
                                  <li>• Updates in KognaDash automatically sync to {connector.name}</li>
                                  <li>• Team assignments and progress updates flow both ways</li>
                                  <li>• WBS changes trigger updates in connected systems</li>
                                  <li>• AI-optimized resource allocation syncs across tools</li>
                                </ul>
                              </div>
                            </div>
                          </CardContent>
                        </Card>

                        <Card className="border-blue-200 bg-blue-50">
                          <CardContent className="pt-4">
                            <div className="flex items-start gap-3">
                              <Shield className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                              <div>
                                <p className="font-semibold text-blue-800 mb-1">Data Conflict Resolution</p>
                                <p className="text-sm text-blue-700">
                                  KognaDash uses intelligent conflict resolution to handle simultaneous updates,
                                  with executive approval required for major changes.
                                </p>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      </div>
                    </div>
                  )}

                  {selectedSyncMode === 'two-way' && connector.id !== 'kognacore' && (
                    <Card className="border-orange-200 bg-orange-50">
                      <CardContent className="pt-4">
                        <div className="flex items-start gap-3">
                          <AlertCircle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
                          <div>
                            <p className="font-semibold text-orange-800 mb-1">Premium Feature</p>
                            <p className="text-sm text-orange-700">
                              Two-way sync requires a KognaDash Premium subscription. 
                              Upgrade to unlock bidirectional data flow and advanced sync features.
                            </p>
                            <Button size="sm" className="mt-2 bg-orange-600 hover:bg-orange-700">
                              Upgrade to Premium
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}