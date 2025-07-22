/**
 * Frontend Streaming API Client for LLM Chat Integration
 * 
 * This file serves as the bridge between the React UI and the llm-api backend.
 * It handles real-time Server-Sent Events (SSE) streaming for chat responses.
 * 
 * Architecture Flow:
 * [React UI] → [streaming-api.ts] → [llm-api:8090] → [vLLM:8000]
 * 
 * Purpose:
 * 1. SSE Stream Handling - Processes real-time streaming tokens from backend
 * 2. Session Management - Links frontend conversations to backend sessions  
 * 3. Error Recovery - Provides UI-specific error handling with Hebrew messages
 * 4. Resource Management - Properly manages browser streaming resources
 * 5. Health Monitoring - Checks API availability before making requests
 */

import { Message } from '../types';

// ========================================
// CONFIGURATION
// ========================================

const API_CONFIG = {
  // Switch between local and external API
  BASE_URL: 'http://71.36.178.233:41112', // External port mapped to container's 8090
  // BASE_URL: 'http://localhost:8090',    // For self-hosted llm-api
  
  ENDPOINTS: {
    CHAT_STREAM: '/api/chat/stream',
    HEALTH: '/api/health',
    METRICS: '/api/metrics',
  },
  
  STORAGE_KEYS: {
    SESSION_ID: 'chatplg-session-id',
  }
} as const;

// ========================================
// TYPES & INTERFACES
// ========================================

/**
 * Error Handling System
 * 
 * Provides structured error types for different failure scenarios,
 * enabling appropriate user feedback and retry logic.
 */
export interface StreamError {
  type: 'connection' | 'api' | 'streaming' | 'timeout';
  message: string;
  retryable: boolean;
}

/**
 * System Metrics Interface
 * 
 * Mirrors the backend metrics for monitoring API health and load.
 * Used by health checks and debugging tools.
 */
export interface SystemMetrics {
  active_sessions: number;
  vllm_running_requests: number | null;
  vllm_waiting_requests: number | null;
  sessions: Record<string, {
    started_at: string;
    status: string;
  }>;
}

/**
 * API Message Format (expected by llm-api)
 */
interface APIMessage {
  type: string; // 'user' or 'assistant'
  content: string;
}

/**
 * Streaming Response Callbacks
 */
interface StreamingCallbacks {
  onToken: (token: string) => void;
  onError: (error: StreamError) => void;
  onComplete: () => void;
}

/**
 * SSE Processing Result
 */
type SSEProcessResult = 'continue' | 'complete' | 'stop';

// ========================================
// SESSION MANAGEMENT
// ========================================

/**
 * Session Management System
 * 
 * Sessions link frontend conversations to backend sessions, enabling:
 * - Multi-user concurrent access on the same browser
 * - Conversation context preservation
 * - Backend session tracking and cleanup
 */

export const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
};

export const getSessionId = (): string => {
  if (typeof window === 'undefined') return generateSessionId(); // SSR safety
  
  let sessionId = sessionStorage.getItem(API_CONFIG.STORAGE_KEYS.SESSION_ID);
  if (!sessionId) {
    sessionId = generateSessionId();
    sessionStorage.setItem(API_CONFIG.STORAGE_KEYS.SESSION_ID, sessionId);
  }
  return sessionId;
};

// ========================================
// UTILITY FUNCTIONS
// ========================================

/**
 * Message Format Conversion
 * 
 * Converts React app message format to llm-api expected format.
 */
export const formatMessagesForAPI = (messages: Message[]): APIMessage[] => {
  return messages.map(msg => ({
    type: msg.type,    // 'user' or 'assistant'
    content: msg.content
  }));
};

/**
 * Error Message Generator
 * 
 * Creates appropriate Hebrew error messages based on HTTP status codes.
 */
const getErrorMessage = (status: number): string => {
  switch (status) {
    case 400: return 'בקשה לא תקינה';
    case 500: return 'שגיאה פנימית בשרת';
    case 503: return 'השירות אינו זמין כרגע';
    default: return 'שגיאה בשרת';
  }
};


// ========================================
// HEALTH MONITORING
// ========================================

/**
 * API Health Monitoring
 * 
 * Checks if the llm-api backend is available before making streaming requests.
 * Prevents unnecessary connection attempts and provides early error feedback.
 */
export const checkAPIHealth = async (): Promise<boolean> => {
  if (typeof window === 'undefined') return true;  // SSR safety - assume healthy
  
  try {
    const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.HEALTH}`);
    if (!response.ok) return false;
    
    const data = await response.json();
    return data.status === 'healthy';
  } catch (error) {
    console.error('Health check failed:', error);
    return false;
  }
};

/**
 * System Metrics Monitoring
 * 
 * Retrieves performance metrics from the llm-api backend.
 * Useful for debugging, monitoring, and understanding system load.
 */
export const getSystemMetrics = async (): Promise<SystemMetrics | null> => {
  try {
    const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.METRICS}`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error('Failed to get metrics:', error);
    return null; // Metrics failure doesn't break the app
  }
};

// ========================================
// STREAMING IMPLEMENTATION
// ========================================

/**
 * Create streaming request to llm-api
 */
const createStreamingRequest = async (
  messages: Message[], 
  sessionId: string, 
  abortController?: AbortController  // Optional: For canceling requests
): Promise<Response> => {
  return fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.CHAT_STREAM}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
      // 'Authorization': 'Bearer your-api-key-here', // Uncomment if API key auth is enabled
    },
    body: JSON.stringify({
      messages: formatMessagesForAPI(messages),
      session_id: sessionId
    }),
    signal: abortController?.signal
  });
};

/**
 * Handle HTTP response errors
 */
const handleHTTPError = (response: Response, onError: StreamingCallbacks['onError']): boolean => {
  if (response.ok) return false; // No error
  
  const errorMessage = getErrorMessage(response.status);
  const retryable = response.status >= 500;
  
  onError({
    type: 'api',
    message: errorMessage,
    retryable
  });
  
  return true; // Error occurred
};

/**
 * Process a single SSE line
 */
const processSSELine = (
  line: string, 
  callbacks: StreamingCallbacks
): SSEProcessResult => { // Returns: 'continue' = keep processing, 'complete' = stop and call onComplete(), 'stop' = stop due to error
  
  if (!line.startsWith('data: ')) {
    return 'continue';
  }
  
  const data = line.slice(6).trim();    // Remove 'data: ' prefix
  
  // Handle completion signal
  if (data === '[DONE]') {
    return 'complete';
  }
  
  try {
    const parsed = JSON.parse(data);
    
    // Handle server-side errors
    if (parsed.error) {
      console.error('Server error:', parsed.error);
      callbacks.onError({
        type: 'api',
        message: parsed.error,
        retryable: true
      });
      return 'stop';
    }
    
    // Handle streaming tokens (OpenAI-compatible format)
    if (parsed.choices?.[0]?.delta?.content) {
      callbacks.onToken(parsed.choices[0].delta.content);   // Send token to UI
    }
  } catch (parseError) {
    // Skip malformed JSON (non-critical)
    console.warn('Failed to parse streaming data:', data, parseError);
  }
  
  return 'continue';
};

/**
 * Process streaming response from ReadableStream
 */
const processStream = async (
  reader: ReadableStreamDefaultReader<Uint8Array>,
  callbacks: StreamingCallbacks
): Promise<void> => {
  const decoder = new TextDecoder();    // Convert bytes to text
  let buffer = '';                      // Buffer for incomplete SSE lines
  let completed = false;                // Prevent duplicate completion calls

  try {
    // Main Streaming Loop - Process chunks as they arrive
    while (true) {
      const { done, value } = await reader.read();  // Wait for next chunk from server
      
      if (done) {
        // Stream ended naturally - ensure completion is called
        if (!completed) {
          completed = true;
          callbacks.onComplete();
        }
        break;
      }

      // Process raw chunk data
      const chunk = decoder.decode(value, { stream: true });   // Convert bytes to text
      buffer += chunk;

      // Parse SSE lines (handle partial lines)
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';   // Keep last incomplete line for next chunk

      // Process each complete SSE line
      for (const line of lines) {
        const result = processSSELine(line, callbacks);
        
        if (result === 'complete' && !completed) {
          completed = true;
          callbacks.onComplete();
        }
        
        if (result === 'complete' || result === 'stop') {
          return;
        }
      }
    }
  } finally {
    reader.releaseLock(); // Always release the reader lock
  }
};

// ========================================
// MAIN STREAMING FUNCTION
// ========================================

/**
 * Real-Time Streaming Chat Response Handler
 * 
 * This is the core function that enables real-time chat with the LLM.
 * It handles Server-Sent Events (SSE) streaming from the llm-api backend.
 * 
 * Implementation Steps:
 * 1. Health check before request
 * 2. Send conversation history to llm-api
 * 3. Process SSE stream with proper buffering
 * 4. Handle OpenAI-compatible response format
 * 5. Robust error recovery with Hebrew messages
 * 6. Proper resource cleanup
 */
export const streamChatResponse = async (
  messages: Message[],
  onToken: (token: string) => void,
  onError: (error: StreamError) => void,
  onComplete: () => void,
  abortController?: AbortController
): Promise<void> => {
  const sessionId = getSessionId();
  const callbacks: StreamingCallbacks = { onToken, onError, onComplete };
  
  try {
    // Step 1: Health Check
    const isHealthy = await checkAPIHealth();
    if (!isHealthy) {
      onError({
        type: 'api',
        message: 'שירות הבינה המלאכותית אינו זמין כרגע. אנא נסה שוב מאוחר יותר.',
        retryable: true
      });
      return;
    }

    // Step 2: Create streaming request
    const response = await createStreamingRequest(messages, sessionId, abortController);

    // Step 3: Handle HTTP errors
    if (handleHTTPError(response, onError)) {
      return;
    }

    // Step 4: Setup streaming reader
    const reader = response.body?.getReader();
    if (!reader) {
      onError({
        type: 'streaming',
        message: 'לא ניתן לקרוא את התגובה מהשרת',
        retryable: true
      });
      return;
    }

    // Step 5: Process the stream
    await processStream(reader, callbacks);

  } catch (error) {
    // Handle connection-level errors
    if (abortController?.signal.aborted) return;
    
    if (error instanceof TypeError && error.message.includes('fetch')) {
      onError({
        type: 'connection',
        message: 'אין חיבור לשרת. אנא בדוק את החיבור שלך.',
        retryable: true
      });
    } else {
      const errorMessage = error instanceof Error ? error.message : 'אירעה שגיאה בחיבור לשרת.';
      onError({
        type: 'connection',
        message: errorMessage,
        retryable: true
      });
    }
  }
}; 