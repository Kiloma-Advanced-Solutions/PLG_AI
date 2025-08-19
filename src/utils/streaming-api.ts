/**
 * Simplified Streaming API Client
 * Matches the simplified llm-api backend
 */

import { Message } from '../types';
import { AppError, createAppError } from './error-handling';

// ========================================
// CONFIGURATION
// ========================================

const API_CONFIG = {
  // API URL - Set via environment variable or use cloud instance
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://172.81.127.6:10599',
  
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

// Configuration is now set with fallback, no validation needed

// ========================================
// TYPES
// ========================================

// Using standardized AppError from error-handling.ts

// ========================================
// SESSION MANAGEMENT
// ========================================

export const generateSessionId = (): string => {
  return `chat_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
};

export const getSessionId = (): string => {
  if (typeof window === 'undefined') return generateSessionId();
  
  try {
    let sessionId = sessionStorage.getItem(API_CONFIG.storage.sessionId);
    if (!sessionId) {
      sessionId = generateSessionId();
      sessionStorage.setItem(API_CONFIG.storage.sessionId, sessionId);
    }
    return sessionId;
  } catch (error) {
    // Fallback if sessionStorage access fails (private browsing, storage quota, etc.)
    return generateSessionId();
  }
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
    // Network failure or non-200 response from health endpoint (vicorn server is down)
    if (!response.ok) return false;
    
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
  onError: (error: AppError) => void,
  onComplete: () => void,
  abortController?: AbortController
): Promise<void> => {
  const sessionId = getSessionId();
  
  try {
    // Prepare request body
    let requestBody: string;
    try {
      requestBody = JSON.stringify({
        messages: messages.map(msg => ({
          role: msg.type === 'user' ? 'user' : 'assistant',
          content: msg.content
        })),
        session_id: sessionId,
        stream: true
      });
    } catch (error) {
      onError(createAppError(
        'validation',
        'שגיאה בעיבוד ההודעות',
        false
      ));
      return;
    }

    // Make request to API
    const response = await fetch(
      `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.chat}`,
      {
        method: 'POST',
        headers: getHeaders(),
        body: requestBody,
        signal: abortController?.signal   // Abort the request if the user clicks stop
      }
    );

    // Non-200 HTTP status codes from chat API
    if (!response.ok) {
      onError(createAppError(
        'api',
        `שגיאה בשרת: ${response.status}`,
        response.status >= 500
      ));
      return;
    }

    // Process streaming response
    const reader = response.body?.getReader();
    // response.body is null/undefined
    if (!reader) {
      onError(createAppError(
        'api', 
        'לא ניתן לקרוא תגובה מהשרת',
        true
      ));
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
          
          // API sends an error object in the SSE stream
          if (parsed.error) {
            onError(createAppError(
              'api', 
              parsed.error, 
              true 
            ));
            return;
          }
          
          // Handle streaming tokens
          if (parsed.choices?.[0]?.delta?.content) {
            onToken(parsed.choices[0].delta.content);
          }
        } 
        // Invalid JSON in SSE data stream
        catch (e) {
          console.warn('Invalid SSE data:', e);
          onError(createAppError(
            'streaming',
            'נתונים לא תקינים מהשרת',
            true
          ));
          return;
        }
      }
    }

  } 
  //Network failures, fetch errors, or other unhandled exceptions
  catch (error) {
    if (abortController?.signal.aborted) return;
 
    onError(createAppError(
      'network',
      'שגיאה בחיבור לשרת',
      true
    ));
  }
}; 