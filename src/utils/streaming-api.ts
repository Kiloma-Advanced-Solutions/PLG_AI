import { Message } from '../types';

// API configuration
// const API_BASE_URL = 'http://localhost:8090';
const API_BASE_URL = 'http://71.36.178.233:41310'; // External port mapped to container's 8090

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
  if (typeof window === 'undefined') return true;
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
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
  messages: Message[],                   // Conversation history   
  onToken: (token: string) => void,      // Called for each AI token
  onError: (error: StreamError) => void, // Called on errors
  onComplete: () => void,                // Called when stream ends
  abortController?: AbortController      // For canceling requests
): Promise<void> => {
  const sessionId = getSessionId();
  
  try {
    const isHealthy = await checkAPIHealth();
    if (!isHealthy) {
      onError({
        type: 'api',
        message: 'שירות הבינה המלאכותית אינו זמין כרגע. אנא נסה שוב מאוחר יותר.',
        retryable: true
      });
      return;
    }

    const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',      // for SSE (Server-Sent Events)
      },
      body: JSON.stringify({
        messages: formatMessagesForAPI(messages),
        session_id: sessionId
      }),
      signal: abortController?.signal       // abort signal for canceling the request
    });

    if (!response.ok) {
      let errorMessage = 'שגיאה בשרת';
      
      if (response.status === 400) {         // Bad Request
        errorMessage = 'בקשה לא תקינה';
      } else if (response.status === 500) {  // Internal Server Error
        errorMessage = 'שגיאה פנימית בשרת';
      } else if (response.status === 503) {  // Service Unavailable
        errorMessage = 'השירות אינו זמין כרגע';
      }
      
      onError({
        type: 'api',
        message: errorMessage,
        retryable: response.status >= 500  // Retryable if server error
      });
      return;                              // Stop the stream if there's an error
    }

    const reader = response.body?.getReader();  // Get the reader for reading chunks from the response stream
    if (!reader) {  
      onError({
        type: 'streaming',
        message: 'לא ניתן לקרוא את התגובה מהשרת',
        retryable: true
      });
      return;
    }

    const decoder = new TextDecoder();  // Decode the chunks from the stream
    let buffer = '';                    // Buffer to store the chunks (incomplete lines)
    let completed = false;              // Flag to check if the stream has completed

    try {
      while (true) {
        const { done, value } = await reader.read();  // Waits for the next chunk from the server
        
        if (done) {
          // Call onComplete if we haven't already
          if (!completed) {
            completed = true;
            onComplete();
          }
          break;
        }

        // Decode the chunk and add to buffer
        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        // Process complete lines
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';   // Keep the last incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            
            if (data === '[DONE]') {
              if (!completed) {
                completed = true;
                onComplete();
              }
              return;
            }
            
            try {
              const parsed = JSON.parse(data);
              
              // Handle error messages from the server
              if (parsed.error) {
                console.error('Server error:', parsed.error);
                onError({
                  type: 'api',
                  message: parsed.error,
                  retryable: true
                });
                return;
              }
              
              // Handle streaming tokens
              if (parsed.choices?.[0]?.delta?.content) {    // If the server sent a token
                onToken(parsed.choices[0].delta.content);  // Call the onToken function with the token
              }
            } catch (parseError) {
              console.warn('Failed to parse streaming data:', data, parseError);
            }
          }
        }
      }
    } catch (streamError) {  // Abort during stream reading (while processing chunks)
      if (abortController?.signal.aborted) {  // Request was cancelled, don't treat as error
        return;
      }
      
      console.error('Streaming error:', streamError); 
      const errorMessage = streamError instanceof Error ? streamError.message : 'הזרמת התגובה נקטעה. אנא נסה שוב.';
      onError({  // Call the onError function with the error message
        type: 'streaming',
        message: errorMessage,
        retryable: true
      });
    } finally {
      reader.releaseLock();  // Release the lock on the reader
    }
    
  } catch (error) {
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