'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

// Types for thinking status
export interface ThinkingStatusProps {
  isVisible: boolean;
  message?: string;
  animationType?: 'dots' | 'spinner' | 'pulse' | 'wave' | 'typing';
  fadeoutDuration?: number;
  className?: string;
  onComplete?: () => void;
}

export interface ThinkingMessage {
  action: 'animate' | 'fadeout';
  message?: string;
  animation?: string;
  frame?: number;
  duration?: number;
}

// Animation variants for different thinking types
const animationVariants = {
  dots: {
    frames: ['●○○', '○●○', '○○●', '○●○'],
    interval: 800
  },
  spinner: {
    frames: ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
    interval: 100
  },
  pulse: {
    frames: ['💭', '💭 ', '💭  ', '💭   ', '💭  ', '💭 '],
    interval: 600
  },
  wave: {
    frames: ['🌊', '🌊 ', '🌊  ', '🌊   ', '  🌊', ' 🌊'],
    interval: 500
  },
  typing: {
    frames: ['▋', '▊', '▉', '█', '▉', '▊'],
    interval: 300
  }
};

// Main ThinkingStatus component
export const ThinkingStatus: React.FC<ThinkingStatusProps> = ({
  isVisible,
  message = 'Analyzing your request...',
  animationType = 'dots',
  fadeoutDuration = 2000,
  className,
  onComplete
}) => {
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isFadingOut, setIsFadingOut] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const fadeoutTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Animation effect
  useEffect(() => {
    if (isVisible && !isFadingOut) {
      const variant = animationVariants[animationType];
      
      intervalRef.current = setInterval(() => {
        setCurrentFrame(prev => (prev + 1) % variant.frames.length);
      }, variant.interval);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isVisible, animationType, isFadingOut]);

  // Fadeout effect
  useEffect(() => {
    if (!isVisible && !isFadingOut) {
      setIsFadingOut(true);
      
      fadeoutTimeoutRef.current = setTimeout(() => {
        setIsFadingOut(false);
        setCurrentFrame(0);
        onComplete?.();
      }, fadeoutDuration);
    }

    return () => {
      if (fadeoutTimeoutRef.current) {
        clearTimeout(fadeoutTimeoutRef.current);
      }
    };
  }, [isVisible, fadeoutDuration, onComplete, isFadingOut]);

  const variant = animationVariants[animationType];
  const currentAnimation = variant.frames[currentFrame];

  return (
    <AnimatePresence mode="wait">
      {(isVisible || isFadingOut) && (
        <motion.div
          initial={{ opacity: 0, y: 10, scale: 0.95 }}
          animate={{ 
            opacity: isFadingOut ? 0 : 1, 
            y: 0, 
            scale: 1 
          }}
          exit={{ 
            opacity: 0, 
            y: -10, 
            scale: 0.95,
            transition: { duration: fadeoutDuration / 1000 }
          }}
          transition={{ 
            duration: isFadingOut ? fadeoutDuration / 1000 : 0.3,
            ease: "easeInOut"
          }}
          className={cn(
            "flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-blue-50 to-indigo-50",
            "border border-blue-200 rounded-lg shadow-sm backdrop-blur-sm",
            "dark:from-blue-950/30 dark:to-indigo-950/30 dark:border-blue-800/30",
            className
          )}
        >
          {/* Animation indicator */}
          <motion.div
            key={currentFrame}
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.2 }}
            className="text-blue-600 dark:text-blue-400 font-mono text-lg min-w-[2rem] text-center"
          >
            {currentAnimation}
          </motion.div>

          {/* Message */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            {message}
          </motion.div>

          {/* Subtle pulse background */}
          <motion.div
            animate={{
              opacity: [0.3, 0.6, 0.3],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            className="absolute inset-0 bg-gradient-to-r from-blue-100/50 to-indigo-100/50 rounded-lg -z-10"
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// Advanced ThinkingStatusManager for complex scenarios
export class ThinkingStatusManager {
  private activeStatuses: Map<string, {
    component: React.RefObject<HTMLDivElement>;
    startTime: number;
    message: string;
  }> = new Map();

  private eventListeners: Map<string, (event: ThinkingMessage) => void> = new Map();

  // Register a thinking status component
  registerStatus(sessionId: string, componentRef: React.RefObject<HTMLDivElement>, message: string) {
    this.activeStatuses.set(sessionId, {
      component: componentRef,
      startTime: Date.now(),
      message
    });
  }

  // Unregister a thinking status component
  unregisterStatus(sessionId: string) {
    this.activeStatuses.delete(sessionId);
    this.eventListeners.delete(sessionId);
  }

  // Add event listener for thinking messages
  addEventListener(sessionId: string, listener: (event: ThinkingMessage) => void) {
    this.eventListeners.set(sessionId, listener);
  }

  // Handle incoming thinking message from backend
  handleThinkingMessage(sessionId: string, message: ThinkingMessage) {
    const listener = this.eventListeners.get(sessionId);
    if (listener) {
      listener(message);
    }
  }

  // Get active status info
  getStatusInfo(sessionId: string) {
    return this.activeStatuses.get(sessionId);
  }

  // Get all active sessions
  getActiveSessions(): string[] {
    return Array.from(this.activeStatuses.keys());
  }

  // Calculate thinking duration
  getThinkingDuration(sessionId: string): number {
    const status = this.activeStatuses.get(sessionId);
    return status ? Date.now() - status.startTime : 0;
  }
}

// Hook for using ThinkingStatus with WebSocket integration
export const useThinkingStatus = (sessionId: string, websocketUrl?: string) => {
  const [isThinking, setIsThinking] = useState(false);
  const [message, setMessage] = useState('Analyzing your request...');
  const [animationType, setAnimationType] = useState<'dots' | 'spinner' | 'pulse' | 'wave' | 'typing'>('dots');
  const managerRef = useRef<ThinkingStatusManager>(new ThinkingStatusManager());
  const wsRef = useRef<WebSocket | null>(null);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (websocketUrl && sessionId) {
      wsRef.current = new WebSocket(websocketUrl);
      
      wsRef.current.onopen = () => {
        console.log('ThinkingStatus WebSocket connected');
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'thinking' && data.session_id === sessionId) {
            const thinkingMessage: ThinkingMessage = data.content;
            
            if (thinkingMessage.action === 'animate') {
              setIsThinking(true);
              if (thinkingMessage.message) {
                setMessage(thinkingMessage.message);
              }
            } else if (thinkingMessage.action === 'fadeout') {
              setIsThinking(false);
            }
            
            // Notify manager
            managerRef.current.handleThinkingMessage(sessionId, thinkingMessage);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('ThinkingStatus WebSocket error:', error);
      };

      wsRef.current.onclose = () => {
        console.log('ThinkingStatus WebSocket disconnected');
      };
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [websocketUrl, sessionId]);

  // Manual control functions
  const startThinking = (newMessage?: string, newAnimationType?: typeof animationType) => {
    if (newMessage) setMessage(newMessage);
    if (newAnimationType) setAnimationType(newAnimationType);
    setIsThinking(true);
  };

  const stopThinking = () => {
    setIsThinking(false);
  };

  const updateMessage = (newMessage: string) => {
    setMessage(newMessage);
  };

  const updateAnimation = (newAnimationType: typeof animationType) => {
    setAnimationType(newAnimationType);
  };

  return {
    isThinking,
    message,
    animationType,
    startThinking,
    stopThinking,
    updateMessage,
    updateAnimation,
    manager: managerRef.current
  };
};

// Preset configurations for different scenarios
export const ThinkingPresets = {
  validation: {
    message: 'Validating your Web3 project requirements...',
    animationType: 'pulse' as const,
    fadeoutDuration: 1500
  },
  analysis: {
    message: 'Analyzing project complexity and feasibility...',
    animationType: 'spinner' as const,
    fadeoutDuration: 2000
  },
  routing: {
    message: 'Determining optimal workflow path...',
    animationType: 'wave' as const,
    fadeoutDuration: 1000
  },
  processing: {
    message: 'Processing your request...',
    animationType: 'dots' as const,
    fadeoutDuration: 2500
  },
  generating: {
    message: 'Generating project structure...',
    animationType: 'typing' as const,
    fadeoutDuration: 3000
  }
};

// Utility component for quick preset usage
export const PresetThinkingStatus: React.FC<{
  preset: keyof typeof ThinkingPresets;
  isVisible: boolean;
  className?: string;
  onComplete?: () => void;
}> = ({ preset, isVisible, className, onComplete }) => {
  const config = ThinkingPresets[preset];
  
  return (
    <ThinkingStatus
      isVisible={isVisible}
      message={config.message}
      animationType={config.animationType}
      fadeoutDuration={config.fadeoutDuration}
      className={className}
      onComplete={onComplete}
    />
  );
};

export default ThinkingStatus;