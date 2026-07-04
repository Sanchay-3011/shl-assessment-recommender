import { useState, useEffect, useCallback, useRef } from 'react';
import type { ChatMessage, RecommendationItem, HiringConstraints } from '../types';
import { sendChatMessage, checkHealth } from '../services/api';
import { extractConstraintsFromHistory } from '../utils/constraintExtractor';

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'offline';

export interface BackendError {
  type: 'backend_offline' | 'timeout' | 'network_unavailable' | 'cors_failure' | 'server_error' | 'unhealthy' | 'unknown';
  message: string;
}

export const useChat = () => {
  const [messages, setMessages] = useState<(ChatMessage & {
    recommendations?: RecommendationItem[];
    comparisonTargets?: string[];
  })[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Connection & Health status states
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('connecting');
  const [backendError, setBackendError] = useState<BackendError | null>(null);
  const [retryCountdown, setRetryCountdown] = useState<number>(0);
  const [retryAttempt, setRetryAttempt] = useState<number>(0);
  
  const [constraints, setConstraints] = useState<HiringConstraints>({
    role: null,
    skills: [],
    programming_languages: [],
    job_level: null,
    experience: null,
    duration: null,
    language: null,
    adaptive: null,
    remote: null,
    assessment_keys: []
  });

  const timerRef = useRef<any>(null);
  const countdownIntervalRef = useRef<any>(null);

  // Parse constraints on messages update
  useEffect(() => {
    const parsed = extractConstraintsFromHistory(messages);
    setConstraints(parsed);
  }, [messages]);

  // Clean timers on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
    };
  }, []);

  // Map Axios/Fetch exceptions to precise user-facing error messages
  const parseAxiosError = (err: any): BackendError => {
    if (!navigator.onLine) {
      return {
        type: 'network_unavailable',
        message: 'Network unavailable: Please check your internet connection.'
      };
    }

    if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
      return {
        type: 'timeout',
        message: 'Request timeout: The server took too long to respond. Please try again.'
      };
    }

    if (err.response) {
      const status = err.response.status;
      if (status >= 500) {
        return {
          type: 'server_error',
          message: `Server unavailable (Status ${status}): The service is temporarily down.`
        };
      }
      return {
        type: 'unknown',
        message: err.response.data?.detail || `API request failed with status ${status}.`
      };
    }

    // Network error with no response, but client is online - typically connection refused or CORS failure
    if (err.message === 'Network Error') {
      return {
        type: 'backend_offline',
        message: 'Backend offline: Cannot connect to the local server. Verify uvicorn is running on port 8000.'
      };
    }

    return {
      type: 'unknown',
      message: err.message || 'An unexpected connection error occurred.'
    };
  };

  // Perform single health check pass
  const verifyHealthStatus = useCallback(async (): Promise<boolean> => {
    try {
      if (!navigator.onLine) {
        setConnectionStatus('offline');
        setBackendError({
          type: 'network_unavailable',
          message: 'Network unavailable: Please check your local network connection.'
        });
        return false;
      }

      const res = await checkHealth();
      if (res && (res.status === 'ok' || res.status === 'healthy')) {
        setConnectionStatus('connected');
        setBackendError(null);
        setRetryAttempt(0);
        setRetryCountdown(0);
        return true;
      } else {
        setConnectionStatus('disconnected');
        setBackendError({
          type: 'unhealthy',
          message: 'Catalog loading failure: The backend server is online, but database initialization failed.'
        });
        return false;
      }
    } catch (err: any) {
      const parsedErr = parseAxiosError(err);
      setConnectionStatus('disconnected');
      setBackendError(parsedErr);
      return false;
    }
  }, []);

  // Reconnection loop with exponential backoff
  const triggerReconnectionTimer = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);

    // Exponential Backoff calculation: 2s, 4s, 8s, 16s, max 30s
    const currentAttempt = retryAttempt + 1;
    setRetryAttempt(currentAttempt);
    const delaySeconds = Math.min(Math.pow(2, currentAttempt), 30);
    
    setRetryCountdown(delaySeconds);

    // Countdown interval countdown updates every second
    countdownIntervalRef.current = setInterval(() => {
      setRetryCountdown((prev) => {
        if (prev <= 1) {
          if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    // Reconnection health check execution timer
    timerRef.current = setTimeout(async () => {
      setConnectionStatus('connecting');
      const isHealthy = await verifyHealthStatus();
      if (!isHealthy) {
        triggerReconnectionTimer();
      }
    }, delaySeconds * 1000);
  }, [retryAttempt, verifyHealthStatus]);

  // Initial startup health check
  useEffect(() => {
    let mounted = true;
    const runStartupCheck = async () => {
      setConnectionStatus('connecting');
      const isHealthy = await verifyHealthStatus();
      if (!isHealthy && mounted) {
        triggerReconnectionTimer();
      }
    };
    runStartupCheck();
    return () => { mounted = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Sync state with browser network drop listeners
  useEffect(() => {
    const handleOnline = () => {
      setConnectionStatus('connecting');
      verifyHealthStatus().then((isHealthy) => {
        if (!isHealthy) triggerReconnectionTimer();
      });
    };

    const handleOffline = () => {
      setConnectionStatus('offline');
      setBackendError({
        type: 'network_unavailable',
        message: 'Network offline: Check your computer internet connection status.'
      });
      if (timerRef.current) clearTimeout(timerRef.current);
      if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Manual Trigger to refresh connection status immediately
  const forceCheckConnection = async () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
    
    setConnectionStatus('connecting');
    setRetryCountdown(0);
    
    const isHealthy = await verifyHealthStatus();
    if (!isHealthy) {
      triggerReconnectionTimer();
    }
  };

  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;

    setError(null);
    setIsLoading(true);

    const userMessage: ChatMessage = {
      role: 'user',
      content,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);

    try {
      const response = await sendChatMessage(updatedMessages);
      const comparisonTargets = extractComparisonTargets(content);

      const assistantMessage = {
        role: 'assistant' as const,
        content: response.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        recommendations: response.recommendations,
        comparisonTargets: comparisonTargets.length > 0 ? comparisonTargets : undefined
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      console.error('Chat transaction failure:', err);
      const parsedErr = parseAxiosError(err);
      setError(parsedErr.message);
      
      // If we encounter a transport/network error, flag backend health as offline
      if (parsedErr.type === 'backend_offline' || parsedErr.type === 'network_unavailable' || parsedErr.type === 'server_error') {
        setConnectionStatus('disconnected');
        setBackendError(parsedErr);
        triggerReconnectionTimer();
      }

      // Rollback last user turn so they can retry
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  const resetConversation = () => {
    setMessages([]);
    setError(null);
    setConstraints({
      role: null,
      skills: [],
      programming_languages: [],
      job_level: null,
      experience: null,
      duration: null,
      language: null,
      adaptive: null,
      remote: null,
      assessment_keys: []
    });
  };

  const extractComparisonTargets = (text: string): string[] => {
    const textLower = text.toLowerCase();
    if (
      textLower.includes('compare') || 
      textLower.includes('vs') || 
      textLower.includes('versus') || 
      textLower.includes('difference')
    ) {
      const targets: string[] = [];
      if (textLower.includes('opq') && textLower.includes('guide')) {
        targets.push('OPQ MQ Sales Report', 'Sales Interview Guide');
      } else if (textLower.includes('solution') && textLower.includes('simulation')) {
        targets.push('Customer Service Phone Simulation', 'Customer Service Phone Solution');
      } else if (textLower.includes('manager') && textLower.includes('transformation')) {
        targets.push('Sales Transformation Report 1.0 - Sales Manager', 'Sales Transformation Report 2.0 - Sales Manager');
      } else if (textLower.includes('java') && textLower.includes('entry') && textLower.includes('advanced')) {
        targets.push('Core Java (Entry Level) (New)', 'Core Java (Advanced Level) (New)');
      }
      return targets;
    }
    return [];
  };

  return {
    messages,
    isLoading,
    error,
    constraints,
    connectionStatus,
    backendError,
    retryCountdown,
    sendMessage,
    resetConversation,
    forceCheckConnection
  };
};
