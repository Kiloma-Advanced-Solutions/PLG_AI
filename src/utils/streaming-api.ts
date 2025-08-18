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
  baseUrl: 'http://195.142.145.66:15548',
  
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
  type: 'connection' | 'api' | 'streaming' | 'timeout' | 'parsing';
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
    if (!response.ok) return false;   // Uvicorn server is down
    
    const data = await response.json();
    return data.status === 'healthy';
  } 
  catch (error) {
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
        signal: abortController?.signal   // Abort the request if the user clicks stop
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

    while (true) { // Loop until the request is complete with multiple safety nets to stop generating tokens immediately
      // Check for abort before each reading each chunk
      if (abortController?.signal.aborted) {
        reader.cancel();  // Cancel the request (the ReadableStream reader)
        return; 
      }

      const { done, value } = await reader.read();
      
      if (done) {
        onComplete();
        break;
      }

      // Check for abort after read
      if (abortController?.signal.aborted) {
        reader.cancel();
        return;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        // Check for abort during processing
        if (abortController?.signal.aborted) {
          reader.cancel();
          return;
        }

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
              type: 'parsing', 
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
    
    onError({
      type: 'api',
      message: 'שגיאה בחיבור לשרת',
      retryable: true
    });
  }
}; 