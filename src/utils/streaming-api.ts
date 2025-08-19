/**
 * Simplified Streaming API Client
 * Matches the simplified llm-api backend
 */

import { Message } from '../types';

// ========================================
// CONFIGURATION
// ========================================

const API_CONFIG = {
  // API URL - Set via environment variable
  baseUrl: 'http://142.182.153.12:47345',
  
  // API Endpoints
  endpoints: {
    chat: '/api/chat/stream',
    health: '/api/health'
  },
  
  // Storage keys
  storage: {
    sessionId: 'chat-session-id'
  }
} as const;

// Validate configuration
if (!API_CONFIG.baseUrl) {
  throw new Error('NEXT_PUBLIC_API_URL environment variable is required');
}

// ========================================
// TYPES
// ========================================

export interface StreamError {
  type: 'connection' | 'api' | 'streaming' | 'timeout';
  message: string;
  retryable?: boolean;
}

// ========================================
// SESSION MANAGEMENT
// ========================================

export const generateSessionId = (): string => {
  return `chat_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
};

export const getSessionId = (): string => {
  if (typeof window === 'undefined') return generateSessionId();
  
  let sessionId = sessionStorage.getItem(API_CONFIG.storage.sessionId);
  if (!sessionId) {
    sessionId = generateSessionId();
    sessionStorage.setItem(API_CONFIG.storage.sessionId, sessionId);
  }
  return sessionId;
};

// ========================================
// API CLIENT
// ========================================

/**
 * Get common headers for API requests
 */
const getHeaders = () => ({
  'Content-Type': 'application/json',
  'X-Client-ID': 'chatplg-ui',  // Identify client
});

/**
 * Check if API is healthy before making requests
 */
export const checkApiHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.health}`);
    if (!response.ok) return false;
    
    const data = await response.json();
    return data.status === 'healthy';
  } catch (error) {
    console.error('Health check failed:', error);
    return false;
  }
};

// ========================================
// MAIN STREAMING FUNCTION
// ========================================

export const streamChatResponse = async (
  messages: Message[],
  onToken: (token: string) => void,
  onError: (error: StreamError) => void,
  onComplete: () => void,
  abortController?: AbortController
): Promise<void> => {
  const sessionId = getSessionId();
  
  try {
    // Check API health before request
    const isHealthy = await checkApiHealth();
    if (!isHealthy) {
      onError({
        type: 'connection',
        message: 'שירות הבינה המלאכותית אינו זמין כרגע',
        retryable: true
      });
      return;
    }
    
    // Make request to API
    const response = await fetch(
      `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.chat}`,
      {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          messages: messages.map(msg => ({
            role: msg.type === 'user' ? 'user' : 'assistant',
            content: msg.content
          })),
          session_id: sessionId,
          stream: true
        }),
        signal: abortController?.signal
      }
    );

    if (!response.ok) {
      onError({
        type: 'streaming',
        message: `שגיאה בשרת: ${response.status}`,
        retryable: response.status >= 500
      });
      return;
    }

    // Process streaming response
    const reader = response.body?.getReader();
    if (!reader) {
      onError({ 
        type: 'streaming', 
        message: 'לא ניתן לקרוא תגובה מהשרת' 
      });
      return;
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        onComplete();
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        
        const data = line.slice(6).trim();
        
        if (data === '[DONE]') {
          onComplete();
          return;
        }

        try {
          const parsed = JSON.parse(data);
          
          if (parsed.error) {
            onError({ 
              type: 'api', 
              message: parsed.error, 
              retryable: true 
            });
            return;
          }
          
          // Handle streaming tokens
          if (parsed.choices?.[0]?.delta?.content) {
            onToken(parsed.choices[0].delta.content);
          }
        } catch (e) {
          // Log parse errors but continue
          console.warn('Invalid SSE data:', e);
        }
      }
    }

  } catch (error) {
    if (abortController?.signal.aborted) return;
    
    console.error('Stream error:', error);
    onError({
      type: 'connection',
      message: 'שגיאה בחיבור לשרת',
      retryable: true
    });
  }
}; 