import { Message } from '../types';

// API configuration
// const API_BASE_URL = 'http://localhost:8090';
const API_BASE_URL = 'http://166.113.52.39:42350';

// Generate a unique session ID for each user session
export const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
};

// Store session ID in sessionStorage
export const getSessionId = (): string => {
  if (typeof window === 'undefined') return generateSessionId();
  
  let sessionId = sessionStorage.getItem('chatplg-session-id');
  if (!sessionId) {
    sessionId = generateSessionId();
    sessionStorage.setItem('chatplg-session-id', sessionId);
  }
  return sessionId;
};

// Error types for better error handling
export interface StreamError {
  type: 'connection' | 'api' | 'streaming' | 'timeout';
  message: string;
  retryable: boolean;
}

// System metrics interface
export interface SystemMetrics {
  active_sessions: number;
  vllm_running_requests: number | null;
  vllm_waiting_requests: number | null;
  sessions: Record<string, {
    started_at: string;
    status: string;
  }>;
}

// Convert React app messages to API format
export const formatMessagesForAPI = (messages: Message[]): Array<{type: string, content: string}> => {
  return messages.map(msg => ({
    type: msg.type,
    content: msg.content
  }));
};

// Health check function
export const checkAPIHealth = async (): Promise<boolean> => {
  // Only run on client side
  if (typeof window === 'undefined') {
    console.log('Health check skipped on server side');
    return true;
  }
  
  console.log('Health check running on client side, API_BASE_URL:', API_BASE_URL);
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) return false;
    
    const data = await response.json();
    return data.status === 'healthy';
  } catch (error) {
    console.error('Health check failed:', error);
    return false;
  }
};

// Streaming response handler
export const streamChatResponse = async (
  messages: Message[],
  onToken: (token: string) => void,
  onError: (error: StreamError) => void,
  onComplete: () => void,
  abortController?: AbortController
): Promise<void> => {
  const sessionId = getSessionId();
  
  try {
    // Check API health first (temporarily bypassed)
    // const isHealthy = await checkAPIHealth();
    // if (!isHealthy) {
    //   onError({
    //     type: 'api',
    //     message: 'שירות הבינה המלאכותית אינו זמין כרגע. אנא נסה שוב מאוחר יותר.',
    //     retryable: true
    //   });
    //   return;
    // }

    const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({
        messages: formatMessagesForAPI(messages),
        session_id: sessionId
      }),
      signal: abortController?.signal
    });

    if (!response.ok) {
      let errorMessage = 'שגיאה בשרת';
      
      if (response.status === 400) {
        errorMessage = 'בקשה לא תקינה';
      } else if (response.status === 500) {
        errorMessage = 'שגיאה פנימית בשרת';
      } else if (response.status === 503) {
        errorMessage = 'השירות אינו זמין כרגע';
      }
      
      onError({
        type: 'api',
        message: errorMessage,
        retryable: response.status >= 500
      });
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      onError({
        type: 'streaming',
        message: 'לא ניתן לקרוא את התגובה מהשרת',
        retryable: true
      });
      return;
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          break;
        }

        // Decode the chunk and add to buffer
        buffer += decoder.decode(value, { stream: true });

        // Process complete lines
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep the last incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            
            if (data === '[DONE]') {
              onComplete();
              return;
            }
            
            try {
              const parsed = JSON.parse(data);
              
              // Handle error messages from the server
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
            } catch {
              // Skip invalid JSON lines
              console.warn('Failed to parse streaming data:', data);
            }
          }
        }
      }
    } catch {
      if (abortController?.signal.aborted) {
        // Request was cancelled, don't treat as error
        return;
      }
      
      onError({
        type: 'streaming',
        message: 'הזרמת התגובה נקטעה. אנא נסה שוב.',
        retryable: true
      });
    } finally {
      reader.releaseLock();
    }
    
  } catch (error) {
    // Handle fetch errors
    if (abortController?.signal.aborted) {
      return;
    }
    
    if (error instanceof TypeError && error.message.includes('fetch')) {
      onError({
        type: 'connection',
        message: 'אין חיבור לשרת. אנא בדוק את החיבור שלך.',
        retryable: true
      });
    } else {
      onError({
        type: 'connection',
        message: 'אירעה שגיאה בחיבור לשרת.',
        retryable: true
      });
    }
  }
};

// Get system metrics (for debugging/monitoring)
export const getSystemMetrics = async (): Promise<SystemMetrics | null> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/metrics`);
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    console.error('Failed to get metrics:', error);
    return null;
  }
}; 