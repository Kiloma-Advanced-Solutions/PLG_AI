'use client';

import { useRef, useEffect, useState, useCallback } from 'react';
import { Message } from '../../types';
import ChatMessageComponent from '../chat-message-component/chat-message-component';
import InputMessageContainer from '../input-message-container/input-message-container';
import { formatMessageTimestamp, getCurrentTimestamp } from '../../utils/date';
import styles from './chat-container-component.module.css';

/**
 * Props for the ChatContainerComponent
 */
type ChatContainerComponentProps = {
  messages: Message[];
  onSendMessage: (message: string) => void;
  onMessageEdit?: (messageId: string, newContent: string) => Promise<void>;
  isStreaming?: boolean;
  isSidebarOpen?: boolean;
  streamingMessage?: string;
  apiError?: string | null;
  onRetry?: () => Promise<void> | void;
  onStop?: (currentInputValue: string) => void;
  triggerInputAnimation?: boolean;
  prefilledMessage?: string;
  onPrefilledMessageCleared?: () => void;
};

/**
 * Main chat container component that displays messages and handles user input
 */
export default function ChatContainerComponent({ 
  messages, 
  onSendMessage, 
  onMessageEdit,
  isStreaming = false, 
  isSidebarOpen = false,
  streamingMessage = '',
  apiError = null,
  onRetry,
  onStop,
  triggerInputAnimation = false,
  prefilledMessage = '',
  onPrefilledMessageCleared
}: ChatContainerComponentProps) {
    const messagesContainerRef = useRef<HTMLDivElement>(null);
    const [hasUserScrolled, setHasUserScrolled] = useState(false);

    /**
     * Basic scroll function from the tutorial - scrolls if within 100px of bottom
     */
    const Scroll = useCallback(() => {
      if (!messagesContainerRef.current) return;
      
      const { offsetHeight, scrollHeight, scrollTop } = messagesContainerRef.current;
      
      // Tutorial logic: scroll if within 100px of bottom AND user hasn't manually scrolled
      if (scrollHeight <= scrollTop + offsetHeight + 100 && !hasUserScrolled) {
        messagesContainerRef.current.scrollTo(0, scrollHeight);
      }
    }, [hasUserScrolled]);

    /**
     * Force scroll to bottom (for user messages)
     */
    const forceScrollToBottom = useCallback(() => {
      if (!messagesContainerRef.current) return;
      
      const { scrollHeight } = messagesContainerRef.current;
      messagesContainerRef.current.scrollTo({
        top: scrollHeight,
        behavior: 'smooth'
      });
      setHasUserScrolled(false); // Reset manual scroll flag
    }, []);

    /**
     * Handle manual scrolling by the user
     */
    const handleScroll = useCallback(() => {
      if (!messagesContainerRef.current) return;
      
      const { offsetHeight, scrollHeight, scrollTop } = messagesContainerRef.current;
      
      // If user scrolled up from bottom (more than 10px), disable auto-scroll
      if (scrollHeight > scrollTop + offsetHeight + 10) {
        setHasUserScrolled(true);
      } else {
        // If user scrolled back to bottom, re-enable auto-scroll
        setHasUserScrolled(false);
      }
    }, []);

    // Set up scroll event listener
    useEffect(() => {
      const container = messagesContainerRef.current;
      if (!container) return;

      container.addEventListener('scroll', handleScroll, { passive: true });
      return () => {
        container.removeEventListener('scroll', handleScroll);
      };
    }, [handleScroll]);

    // Auto-scroll on new messages (tutorial approach)
    useEffect(() => {
      Scroll();
    }, [messages, Scroll]);

    // Auto-scroll on streaming updates
    useEffect(() => {
      Scroll();
    }, [streamingMessage, Scroll]);

    // Force scroll when user sends new message
    useEffect(() => {
      if (messages.length > 0 && messages[messages.length - 1]?.type === 'user') {
        forceScrollToBottom();
      }
    }, [messages, forceScrollToBottom]);

    return (
      <div className={`${styles.chatContainer} ${isSidebarOpen ? styles.shifted : ''} ${messages.length === 0 ? styles.empty : ''}`}>
        <div 
          ref={messagesContainerRef}
          className={`${styles.messagesContainer} ${messages.length === 0 ? styles.empty : ''}`}
        >
          {messages.length === 0 ? (
            <div className={styles.welcomeMessage}>
              <h2>ברוכים הבאים ל-ChatPLG!</h2>
              <p>התחל שיחה חדשה על ידי שליחת הודעה</p>
            </div>
          ) : (
            // Render all messages
            messages.map((message) => (
              <ChatMessageComponent
                key={message.id}
                type={message.type}
                content={message.content}
                timestamp={formatMessageTimestamp(message.timestamp)}
                onMessageEdit={message.type === 'user' && onMessageEdit ? 
                  (newContent: string) => onMessageEdit(message.id, newContent) : 
                  undefined
                }
              />
            ))
          )}
          
          {apiError && (
            <div className={styles.errorMessage}>
              <div className={styles.errorContent}>
                <span className={styles.errorIcon}>⚠️</span>
                <span className={styles.errorText}>{apiError}</span>
                {onRetry && (
                  <button 
                    className={styles.retryButton}
                    onClick={async () => {
                      try {
                        await onRetry();
                      } catch (error) {
                        console.error('Retry failed:', error);
                      }
                    }}
                  >
                    נסה שוב
                  </button>
                )}
              </div>
            </div>
          )}
          
          {isStreaming && (
            <div className={styles.streamingResponse}>
              {streamingMessage ? (
                <ChatMessageComponent
                  type="assistant"
                  content={streamingMessage}
                  timestamp={formatMessageTimestamp(getCurrentTimestamp())}
                  isStreaming={true}
                />
              ) : (
                <div className={styles.typingIndicator}>
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              )}
            </div>
          )}
        </div>
        
        <InputMessageContainer 
          onSendMessage={onSendMessage}
          isStreaming={isStreaming}
          triggerFocusAnimation={triggerInputAnimation}
          prefilledMessage={prefilledMessage}
          onPrefilledMessageCleared={onPrefilledMessageCleared}
          onStop={onStop}
        />
      </div>
    );
} 