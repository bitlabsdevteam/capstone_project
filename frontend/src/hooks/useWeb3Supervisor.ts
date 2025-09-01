/**
 * Web3 Supervisor Hook
 * 
 * React hook for integrating with the Web3 supervisor agent system.
 * Provides real-time validation, streaming updates, and professional UI feedback.
 */

import { useState, useEffect, useCallback, useRef } from 'react';

// Generate UUID alternative
const generateId = (): string => {
  return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
};

// Types
export interface Web3ProjectRequest {
  prompt: string;
  sessionId?: string;
  userContext?: Record<string, unknown>;
  priority?: 'low' | 'medium' | 'high';
}

export interface ValidationResult {
  sessionId: string;
  validationStatus: string;
  validationScore: number;
  routingDecision: string;
  processingTime: number;
  issues: string[];
  suggestions: string[];
  metadata: Record<string, unknown>;
  timestamp: string;
}

export interface StreamingUpdate {
  type: 'thinking' | 'status' | 'validation' | 'routing' | 'complete' | 'error' | 'connection_established' | 'heartbeat';
  message?: string;
  sessionId: string;
  progress?: number;
  metadata?: Record<string, unknown>;
  timestamp: string;
  result?: ValidationResult;
  error?: string;
}

export interface SystemStats {
  activeSessions: number;
  totalSessionsProcessed: number;
  averageProcessingTime: number;
  successRate: number;
  routingDistribution: Record<string, number>;
  timestamp: string;
}

export interface Web3SupervisorState {
  // Connection state
  isConnected: boolean;
  connectionError: string | null;
  
  // Processing state
  isProcessing: boolean;
  currentSessionId: string | null;
  
  // Thinking animation state
  isThinking: boolean;
  thinkingMessage: string;
  
  // Results
  validationResult: ValidationResult | null;
  streamingUpdates: StreamingUpdate[];
  
  // Status
  statusMessage: string;
  progress: number;
  
  // Error handling
  error: string | null;
  
  // System stats
  systemStats: SystemStats | null;
}

export interface Web3SupervisorActions {
  // Main validation function
  validateWeb3Project: (request: Web3ProjectRequest) => Promise<ValidationResult | null>;
  
  // Connection management
  connect: (sessionId?: string) => Promise<void>;
  disconnect: () => void;
  
  // State management
  clearResults: () => void;
  clearError: () => void;
  
  // System information
  getSystemStats: () => Promise<SystemStats | null>;
  getSessionInfo: (sessionId: string) => Promise<Record<string, unknown> | null>;
  
  // Cleanup
  cleanupSession: (sessionId: string) => Promise<void>;
}

export interface UseWeb3SupervisorOptions {
  apiBaseUrl?: string;
  enableWebSocket?: boolean;
  enableSSE?: boolean;
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
  onValidationComplete?: (result: ValidationResult) => void;
  onError?: (error: string) => void;
  onStatusUpdate?: (update: StreamingUpdate) => void;
}

const DEFAULT_OPTIONS: UseWeb3SupervisorOptions = {
  apiBaseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  enableWebSocket: true,
  enableSSE: false,
  autoConnect: false,
  reconnectAttempts: 3,
  reconnectDelay: 2000,
};

/**
 * Custom hook for Web3 supervisor integration
 */
export const useWeb3Supervisor = (options: UseWeb3SupervisorOptions = {}): [Web3SupervisorState, Web3SupervisorActions] => {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  
  // State
  const [state, setState] = useState<Web3SupervisorState>({
    isConnected: false,
    connectionError: null,
    isProcessing: false,
    currentSessionId: null,
    isThinking: false,
    thinkingMessage: '',
    validationResult: null,
    streamingUpdates: [],
    statusMessage: '',
    progress: 0,
    error: null,
    systemStats: null,
  });
  
  // Refs for connection management
  const websocketRef = useRef<WebSocket | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  
  // Update state helper
  const updateState = useCallback((updates: Partial<Web3SupervisorState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);
  
  // Add streaming update
  const addStreamingUpdate = useCallback((update: StreamingUpdate) => {
    setState(prev => ({
      ...prev,
      streamingUpdates: [...prev.streamingUpdates.slice(-49), update], // Keep last 50 updates
    }));
    
    // Call callback if provided
    if (opts.onStatusUpdate) {
      opts.onStatusUpdate(update);
    }
  }, [opts]);
  
  // WebSocket connection
  const connectWebSocket = useCallback(async (sessionId: string) => {
    if (!opts.enableWebSocket) return;
    
    try {
      const wsUrl = `${opts.apiBaseUrl?.replace('http', 'ws')}/api/v1/web3/stream/${sessionId}`;
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        updateState({ isConnected: true, connectionError: null });
        reconnectAttemptsRef.current = 0;
      };
      
      ws.onmessage = (event) => {
        try {
          const update: StreamingUpdate = JSON.parse(event.data);
          
          // Handle different update types
          switch (update.type) {
            case 'thinking':
              updateState({
                isThinking: true,
                thinkingMessage: update.message || 'Processing...',
              });
              break;
              
            case 'status':
              updateState({
                statusMessage: update.message || '',
                progress: update.progress || 0,
              });
              break;
              
            case 'validation':
              if (update.result) {
                updateState({
                  validationResult: update.result,
                  isThinking: false,
                });
                
                if (opts.onValidationComplete) {
                  opts.onValidationComplete(update.result);
                }
              }
              break;
              
            case 'complete':
              updateState({
                isProcessing: false,
                isThinking: false,
                statusMessage: 'Validation complete',
                progress: 100,
              });
              break;
              
            case 'error':
              const errorMsg = update.error || 'Unknown error occurred';
              updateState({
                error: errorMsg,
                isProcessing: false,
                isThinking: false,
              });
              
              if (opts.onError) {
                opts.onError(errorMsg);
              }
              break;
              
            case 'connection_established':
              console.log('WebSocket connection established');
              break;
              
            case 'heartbeat':
              // Keep connection alive
              break;
          }
          
          // Add to streaming updates
          addStreamingUpdate(update);
          
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        updateState({ isConnected: false });
        
        // Attempt reconnection if not intentional
        if (event.code !== 1000 && reconnectAttemptsRef.current < (opts.reconnectAttempts || 3)) {
          reconnectAttemptsRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Reconnecting WebSocket (attempt ${reconnectAttemptsRef.current})...`);
            connectWebSocket(sessionId);
          }, opts.reconnectDelay || 2000);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateState({
          connectionError: 'WebSocket connection error',
          isConnected: false,
        });
      };
      
      websocketRef.current = ws;
      
    } catch (error) {
      console.error('Error connecting WebSocket:', error);
      updateState({
        connectionError: 'Failed to connect WebSocket',
        isConnected: false,
      });
    }
  }, [opts, updateState, addStreamingUpdate]);
  
  // SSE connection
  const connectSSE = useCallback(async (sessionId: string) => {
    if (!opts.enableSSE) return;
    
    try {
      const sseUrl = `${opts.apiBaseUrl}/api/v1/web3/stream/${sessionId}`;
      const eventSource = new EventSource(sseUrl);
      
      eventSource.onopen = () => {
        console.log('SSE connected');
        updateState({ isConnected: true, connectionError: null });
      };
      
      eventSource.onmessage = (event) => {
        try {
          const update: StreamingUpdate = JSON.parse(event.data);
          addStreamingUpdate(update);
          
          // Handle updates similar to WebSocket
          if (update.type === 'thinking') {
            updateState({
              isThinking: true,
              thinkingMessage: update.message || 'Processing...',
            });
          } else if (update.type === 'complete') {
            updateState({
              isProcessing: false,
              isThinking: false,
            });
          }
          
        } catch (error) {
          console.error('Error parsing SSE message:', error);
        }
      };
      
      eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        updateState({
          connectionError: 'SSE connection error',
          isConnected: false,
        });
      };
      
      eventSourceRef.current = eventSource;
      
    } catch (error) {
      console.error('Error connecting SSE:', error);
      updateState({
        connectionError: 'Failed to connect SSE',
        isConnected: false,
      });
    }
  }, [opts, updateState, addStreamingUpdate]);
  
  // Connect function
  const connect = useCallback(async (sessionId?: string) => {
    const id = sessionId || generateId();
    
    updateState({ currentSessionId: id });
    
    if (opts.enableWebSocket) {
      await connectWebSocket(id);
    } else if (opts.enableSSE) {
      await connectSSE(id);
    }
  }, [connectWebSocket, connectSSE, opts, updateState]);
  
  // Disconnect function
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (websocketRef.current) {
      websocketRef.current.close(1000, 'Intentional disconnect');
      websocketRef.current = null;
    }
    
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    
    updateState({
      isConnected: false,
      connectionError: null,
      currentSessionId: null,
    });
  }, [updateState]);
  
  // Validate Web3 project
  const validateWeb3Project = useCallback(async (request: Web3ProjectRequest): Promise<ValidationResult | null> => {
    try {
      updateState({
        isProcessing: true,
        error: null,
        validationResult: null,
        progress: 0,
        statusMessage: 'Starting validation...',
      });
      
      // Generate session ID if not provided
      const sessionId = request.sessionId || generateId();
      
      // Connect if not already connected
      if (!state.isConnected) {
        await connect(sessionId);
      }
      
      // Send validation request via WebSocket if connected
      if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
        websocketRef.current.send(JSON.stringify({
          type: 'validate_request',
          prompt: request.prompt,
          user_context: request.userContext || {},
          priority: request.priority || 'medium',
        }));
        
        // Return null as result will come via WebSocket
        return null;
      }
      
      // Fallback to HTTP API
      const response = await fetch(`${opts.apiBaseUrl}/api/v1/web3/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: request.prompt,
          session_id: sessionId,
          user_context: request.userContext || {},
          priority: request.priority || 'medium',
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result: ValidationResult = await response.json();
      
      updateState({
        validationResult: result,
        isProcessing: false,
        statusMessage: 'Validation complete',
        progress: 100,
      });
      
      if (opts.onValidationComplete) {
        opts.onValidationComplete(result);
      }
      
      return result;
      
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Validation failed';
      
      updateState({
        error: errorMsg,
        isProcessing: false,
        isThinking: false,
      });
      
      if (opts.onError) {
        opts.onError(errorMsg);
      }
      
      return null;
    }
  }, [state.isConnected, connect, opts, updateState]);
  
  // Get system stats
  const getSystemStats = useCallback(async (): Promise<SystemStats | null> => {
    try {
      const response = await fetch(`${opts.apiBaseUrl}/api/v1/web3/stats`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const stats: SystemStats = await response.json();
      updateState({ systemStats: stats });
      
      return stats;
      
    } catch (error) {
      console.error('Error fetching system stats:', error);
      return null;
    }
  }, [opts.apiBaseUrl, updateState]);
  
  // Get session info
  const getSessionInfo = useCallback(async (sessionId: string): Promise<Record<string, unknown> | null> => {
    try {
      const response = await fetch(`${opts.apiBaseUrl}/api/v1/web3/session/${sessionId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
      
    } catch (error) {
      console.error('Error fetching session info:', error);
      return null;
    }
  }, [opts.apiBaseUrl]);
  
  // Cleanup session
  const cleanupSession = useCallback(async (sessionId: string): Promise<void> => {
    try {
      await fetch(`${opts.apiBaseUrl}/api/v1/web3/session/${sessionId}`, {
        method: 'DELETE',
      });
    } catch (error) {
      console.error('Error cleaning up session:', error);
    }
  }, [opts.apiBaseUrl]);
  
  // Clear results
  const clearResults = useCallback(() => {
    updateState({
      validationResult: null,
      streamingUpdates: [],
      error: null,
      statusMessage: '',
      progress: 0,
      isThinking: false,
      thinkingMessage: '',
    });
  }, [updateState]);
  
  // Clear error
  const clearError = useCallback(() => {
    updateState({ error: null });
  }, [updateState]);
  
  // Auto-connect on mount if enabled
  useEffect(() => {
    if (opts.autoConnect) {
      connect();
    }
    
    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [opts.autoConnect, connect, disconnect]);
  
  // Actions object
  const actions: Web3SupervisorActions = {
    validateWeb3Project,
    connect,
    disconnect,
    clearResults,
    clearError,
    getSystemStats,
    getSessionInfo,
    cleanupSession,
  };
  
  return [state, actions];
};

export default useWeb3Supervisor;