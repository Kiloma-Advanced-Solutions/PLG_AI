/**
 * Simplified Streaming API Client
 * Matches the simplified llm-api backend
 */

import { Message } from '../types';

// ========================================
// CONFIGURATION
// ========================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8090';

// ========================================
// SIMPLE TYPES
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
  
  let sessionId = sessionStorage.getItem('chat-session-id');
  if (!sessionId) {
    sessionId = generateSessionId();
    sessionStorage.setItem('chat-session-id', sessionId);
  }
  return sessionId;
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
    // Simple request to simplified backend
    const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: messages.map(msg => ({
          role: msg.type === 'user' ? 'user' : 'assistant', // Convert type → role
          content: msg.content
        })),
        session_id: sessionId,
        stream: true
      }),
      signal: abortController?.signal
    });

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
      onError({ type: 'streaming', message: 'לא ניתן לקרוא תגובה מהשרת' });
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
            onError({ type: 'api', message: parsed.error, retryable: true });
            return;
          }
          
          // Handle streaming tokens
          if (parsed.choices?.[0]?.delta?.content) {
            onToken(parsed.choices[0].delta.content);
          }
        } catch (e) {
          // Skip malformed JSON
          console.warn('Invalid SSE data:', data);
        }
      }
    }

  } catch (error) {
    if (abortController?.signal.aborted) return;
    
    onError({
      type: 'connection',
      message: 'שגיאה בחיבור לשרת',
      retryable: true
    });
  }
}; 