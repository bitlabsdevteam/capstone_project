/**
 * Web3 Supervisor Demo Component
 * 
 * Comprehensive demonstration of the Web3 supervisor agent system with:
 * - Real-time validation and streaming updates
 * - Professional UI feedback mechanisms
 * - Thinking status animations
 * - Human-in-loop integration
 * - Responsive status updates
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Alert, AlertDescription } from './ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import { ThinkingStatus } from './ui/ThinkingStatus';
import { useWeb3Supervisor, ValidationResult, StreamingUpdate, SystemStats } from '../hooks/useWeb3Supervisor';
import { 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Clock, 
  Zap, 
  Activity, 
  TrendingUp, 
  Users, 
  Server,
  Wifi,
  WifiOff,
  RefreshCw,
  Send,
  Trash2,
  BarChart3
} from 'lucide-react';

// Sample prompts for testing
const SAMPLE_PROMPTS = [
  {
    title: "Comprehensive DeFi Platform",
    prompt: "Create a comprehensive DeFi lending and borrowing platform with automated market making, yield farming capabilities, governance token distribution, multi-chain support for Ethereum and Polygon, smart contract security audits, and integration with major DeFi protocols like Uniswap and Compound. Include detailed tokenomics, liquidity mining rewards, and a user-friendly interface for both beginners and advanced users.",
    category: "Valid - Comprehensive"
  },
  {
    title: "NFT Marketplace",
    prompt: "Build an NFT marketplace with minting, trading, and auction features",
    category: "Needs More Detail"
  },
  {
    title: "Vague Crypto Request",
    prompt: "I want to make money with crypto",
    category: "Invalid - Too Vague"
  },
  {
    title: "DAO Governance System",
    prompt: "Develop a decentralized autonomous organization (DAO) governance system with proposal creation, voting mechanisms, treasury management, member onboarding, reputation scoring, and integration with Snapshot for off-chain voting. Include multi-signature wallet support and automated execution of approved proposals.",
    category: "Valid - Detailed"
  }
];

// Validation status colors and icons
const getValidationStatusDisplay = (status: string, score: number) => {
  if (status === 'VALID' || score >= 0.8) {
    return {
      color: 'bg-green-100 text-green-800 border-green-200',
      icon: <CheckCircle className="w-4 h-4" />,
      label: 'Valid'
    };
  } else if (status === 'NEEDS_MORE_INFO' || (score >= 0.4 && score < 0.8)) {
    return {
      color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      icon: <AlertCircle className="w-4 h-4" />,
      label: 'Needs More Info'
    };
  } else {
    return {
      color: 'bg-red-100 text-red-800 border-red-200',
      icon: <XCircle className="w-4 h-4" />,
      label: 'Invalid'
    };
  }
};

// Routing decision colors
const getRoutingDecisionDisplay = (decision: string) => {
  switch (decision.toLowerCase()) {
    case 'frontend_agent':
      return {
        color: 'bg-blue-100 text-blue-800 border-blue-200',
        icon: <Zap className="w-4 h-4" />,
        label: 'Frontend Agent'
      };
    case 'human_in_loop':
      return {
        color: 'bg-purple-100 text-purple-800 border-purple-200',
        icon: <Users className="w-4 h-4" />,
        label: 'Human Review'
      };
    case 'end':
      return {
        color: 'bg-gray-100 text-gray-800 border-gray-200',
        icon: <XCircle className="w-4 h-4" />,
        label: 'End Process'
      };
    default:
      return {
        color: 'bg-gray-100 text-gray-800 border-gray-200',
        icon: <Activity className="w-4 h-4" />,
        label: decision
      };
  }
};

const Web3SupervisorDemo: React.FC = () => {
  const [state, actions] = useWeb3Supervisor({
    apiBaseUrl: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
    enableWebSocket: true,
    autoConnect: false,
    onValidationComplete: (result) => {
      console.log('Validation completed:', result);
    },
    onError: (error) => {
      console.error('Supervisor error:', error);
    },
    onStatusUpdate: (update) => {
      console.log('Status update:', update);
    }
  });
  
  // Local state
  const [currentPrompt, setCurrentPrompt] = useState('');
  const [selectedSample, setSelectedSample] = useState<number | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // Load sample prompt
  const loadSamplePrompt = useCallback((index: number) => {
    setCurrentPrompt(SAMPLE_PROMPTS[index].prompt);
    setSelectedSample(index);
  }, []);
  
  // Handle validation
  const handleValidation = useCallback(async () => {
    if (!currentPrompt.trim()) {
      return;
    }
    
    await actions.validateWeb3Project({
      prompt: currentPrompt,
      userContext: {
        source: 'demo',
        timestamp: new Date().toISOString(),
        selectedSample: selectedSample !== null ? SAMPLE_PROMPTS[selectedSample].title : null
      },
      priority: 'high'
    });
  }, [currentPrompt, selectedSample, actions]);
  
  // Connect/disconnect handlers
  const handleConnect = useCallback(async () => {
    await actions.connect();
  }, [actions]);
  
  const handleDisconnect = useCallback(() => {
    actions.disconnect();
  }, [actions]);
  
  // Clear results
  const handleClearResults = useCallback(() => {
    actions.clearResults();
    setCurrentPrompt('');
    setSelectedSample(null);
  }, [actions]);
  
  // Load system stats
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const loadSystemStats = useCallback(async () => {
    const stats = await actions.getSystemStats();
    setSystemStats(stats);
  }, [actions]);
  
  // Auto-load stats periodically
  useEffect(() => {
    loadSystemStats();
    const interval = setInterval(loadSystemStats, 10000); // Every 10 seconds
    return () => clearInterval(interval);
  }, [loadSystemStats]);
  
  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">
          Web3 Supervisor Agent Demo
        </h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Experience real-time Web3 project validation with intelligent routing, 
          human-in-loop integration, and professional UI feedback.
        </p>
      </div>
      
      {/* Connection Status */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {state.isConnected ? (
                <>
                  <Wifi className="w-5 h-5 text-green-600" />
                  <span className="text-green-600 font-medium">Connected</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-5 h-5 text-red-600" />
                  <span className="text-red-600 font-medium">Disconnected</span>
                </>
              )}
              {state.currentSessionId && (
                <Badge variant="outline" className="ml-2">
                  Session: {state.currentSessionId.slice(-8)}
                </Badge>
              )}
            </div>
            
            <div className="flex space-x-2">
              {!state.isConnected ? (
                <Button onClick={handleConnect} size="sm">
                  <Wifi className="w-4 h-4 mr-2" />
                  Connect
                </Button>
              ) : (
                <Button onClick={handleDisconnect} variant="outline" size="sm">
                  <WifiOff className="w-4 h-4 mr-2" />
                  Disconnect
                </Button>
              )}
              <Button onClick={handleClearResults} variant="outline" size="sm">
                <Trash2 className="w-4 h-4 mr-2" />
                Clear
              </Button>
            </div>
          </div>
          
          {state.connectionError && (
            <Alert className="mt-3">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{state.connectionError}</AlertDescription>
            </Alert>
          )}
        </CardHeader>
      </Card>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Section */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Web3 Project Prompt</CardTitle>
              <CardDescription>
                Enter your Web3 project description for validation
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Sample Prompts */}
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">
                  Sample Prompts
                </label>
                <div className="grid grid-cols-1 gap-2">
                  {SAMPLE_PROMPTS.map((sample, index) => (
                    <Button
                      key={index}
                      variant={selectedSample === index ? "default" : "outline"}
                      size="sm"
                      className="justify-start text-left h-auto p-3"
                      onClick={() => loadSamplePrompt(index)}
                    >
                      <div>
                        <div className="font-medium">{sample.title}</div>
                        <div className="text-xs text-gray-500 mt-1">
                          {sample.category}
                        </div>
                      </div>
                    </Button>
                  ))}
                </div>
              </div>
              
              {/* Prompt Input */}
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">
                  Project Description
                </label>
                <Textarea
                  value={currentPrompt}
                  onChange={(e) => setCurrentPrompt(e.target.value)}
                  placeholder="Describe your Web3 project in detail..."
                  className="min-h-[120px] resize-none"
                  disabled={state.isProcessing}
                />
                <div className="text-xs text-gray-500 mt-1">
                  {currentPrompt.length} characters
                </div>
              </div>
              
              {/* Submit Button */}
              <Button
                onClick={handleValidation}
                disabled={!currentPrompt.trim() || state.isProcessing}
                className="w-full"
                size="lg"
              >
                {state.isProcessing ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Validate Project
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
          
          {/* System Stats */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center space-x-2">
                  <BarChart3 className="w-5 h-5" />
                  <span>System Statistics</span>
                </CardTitle>
                <Button onClick={loadSystemStats} variant="outline" size="sm">
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {systemStats ? (
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {systemStats.activeSessions}
                    </div>
                    <div className="text-xs text-gray-500">Active Sessions</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {systemStats.totalSessionsProcessed}
                    </div>
                    <div className="text-xs text-gray-500">Total Processed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {systemStats.averageProcessingTime.toFixed(1)}s
                    </div>
                    <div className="text-xs text-gray-500">Avg Time</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {systemStats.successRate.toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500">Success Rate</div>
                  </div>
                </div>
              ) : (
                <div className="text-center text-gray-500">
                  <Server className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <div>Loading statistics...</div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
        
        {/* Results Section */}
        <div className="space-y-4">
          {/* Thinking Status */}
          {state.isThinking && (
            <Card>
              <CardContent className="pt-6">
                <ThinkingStatus
                  isVisible={true}
                  message={state.thinkingMessage || "Analyzing your Web3 project..."}
                  animationType="pulse"
                />
              </CardContent>
            </Card>
          )}
          
          {/* Processing Status */}
          {state.isProcessing && !state.isThinking && (
            <Card>
              <CardContent className="pt-6">
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Activity className="w-5 h-5 text-blue-600 animate-pulse" />
                    <span className="font-medium">{state.statusMessage || "Processing..."}</span>
                  </div>
                  {state.progress > 0 && (
                    <Progress value={state.progress} className="w-full" />
                  )}
                </div>
              </CardContent>
            </Card>
          )}
          
          {/* Error Display */}
          {state.error && (
            <Alert className="border-red-200 bg-red-50">
              <XCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800">
                {state.error}
              </AlertDescription>
            </Alert>
          )}
          
          {/* Validation Results */}
          {state.validationResult && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span>Validation Results</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="summary" className="w-full">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="summary">Summary</TabsTrigger>
                    <TabsTrigger value="details">Details</TabsTrigger>
                    <TabsTrigger value="routing">Routing</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="summary" className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-gray-700">Status</label>
                        <div className="mt-1">
                          {(() => {
                            const display = getValidationStatusDisplay(
                              state.validationResult.validationStatus,
                              state.validationResult.validationScore
                            );
                            return (
                              <Badge className={display.color}>
                                {display.icon}
                                <span className="ml-1">{display.label}</span>
                              </Badge>
                            );
                          })()}
                        </div>
                      </div>
                      
                      <div>
                        <label className="text-sm font-medium text-gray-700">Score</label>
                        <div className="mt-1">
                          <div className="flex items-center space-x-2">
                            <Progress 
                              value={state.validationResult.validationScore * 100} 
                              className="flex-1" 
                            />
                            <span className="text-sm font-medium">
                              {(state.validationResult.validationScore * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <label className="text-sm font-medium text-gray-700">Processing Time</label>
                      <div className="mt-1 flex items-center space-x-1">
                        <Clock className="w-4 h-4 text-gray-500" />
                        <span className="text-sm">
                          {state.validationResult.processingTime.toFixed(2)} seconds
                        </span>
                      </div>
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="details" className="space-y-4">
                    {state.validationResult.issues.length > 0 && (
                      <div>
                        <label className="text-sm font-medium text-red-700">Issues Found</label>
                        <div className="mt-2 space-y-1">
                          {state.validationResult.issues.map((issue, index) => (
                            <div key={index} className="flex items-start space-x-2 text-sm">
                              <XCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                              <span>{issue}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {state.validationResult.suggestions.length > 0 && (
                      <div>
                        <label className="text-sm font-medium text-blue-700">Suggestions</label>
                        <div className="mt-2 space-y-1">
                          {state.validationResult.suggestions.map((suggestion, index) => (
                            <div key={index} className="flex items-start space-x-2 text-sm">
                              <CheckCircle className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                              <span>{suggestion}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </TabsContent>
                  
                  <TabsContent value="routing" className="space-y-4">
                    <div>
                      <label className="text-sm font-medium text-gray-700">Routing Decision</label>
                      <div className="mt-1">
                        {(() => {
                          const display = getRoutingDecisionDisplay(state.validationResult.routingDecision);
                          return (
                            <Badge className={display.color}>
                              {display.icon}
                              <span className="ml-1">{display.label}</span>
                            </Badge>
                          );
                        })()}
                      </div>
                    </div>
                    
                    <div>
                      <label className="text-sm font-medium text-gray-700">Next Steps</label>
                      <div className="mt-2 text-sm text-gray-600">
                        {state.validationResult.routingDecision === 'frontend_agent' && (
                          "✅ Your project will be forwarded to the Frontend Agent for implementation."
                        )}
                        {state.validationResult.routingDecision === 'human_in_loop' && (
                          "👥 Your project requires human review for clarification or additional information."
                        )}
                        {state.validationResult.routingDecision === 'end' && (
                          "❌ Your project cannot be processed in its current form. Please review the issues and suggestions."
                        )}
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          )}
          
          {/* Streaming Updates */}
          {state.streamingUpdates.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Activity className="w-5 h-5" />
                  <span>Real-time Updates</span>
                  <Badge variant="outline">{state.streamingUpdates.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-48">
                  <div className="space-y-2">
                    {state.streamingUpdates.slice(-10).reverse().map((update, index) => (
                      <div key={index} className="flex items-start space-x-2 text-sm">
                        <div className="text-xs text-gray-500 mt-0.5 w-16 flex-shrink-0">
                          {new Date(update.timestamp).toLocaleTimeString()}
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {update.type}
                        </Badge>
                        <div className="flex-1">
                          {update.message || JSON.stringify(update.metadata || {})}
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default Web3SupervisorDemo;