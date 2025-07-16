'use client';

import { useRef, useEffect, useState } from 'react';
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
  isLoading?: boolean;
  isSidebarOpen?: boolean;
  streamingMessage?: string;
  apiError?: string | null;
  onRetry?: () => Promise<void> | void;
  triggerInputAnimation?: boolean;
};

/**
 * Main chat container component that displays messages and handles user input
 */
export default function ChatContainerComponent({ 
  messages, 
  onSendMessage, 
  isLoading = false, 
  isSidebarOpen = false,
  streamingMessage = '',
  apiError = null,
  onRetry,
  triggerInputAnimation = false
}: ChatContainerComponentProps) {
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [isRetrying, setIsRetrying] = useState(false);

    /**
     * Scrolls to the bottom of the messages container
     */
    const scrollToBottom = () => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    // Scroll to bottom when messages or streaming message updates
    useEffect(() => {
      scrollToBottom();
    }, [messages, streamingMessage]);

    return (
      <div className={`${styles.chatContainer} ${isSidebarOpen ? styles.shifted : ''}`}>
        <div className={styles.messagesContainer}>
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
                    disabled={isRetrying || isLoading}
                    onClick={async () => {
                      if (isRetrying || isLoading) return;
                      
                      setIsRetrying(true);
                      try {
                        await onRetry();
                      } catch (error) {
                        console.error('Retry failed:', error);
                      } finally {
                        setIsRetrying(false);
                      }
                    }}
                  >
                    {isRetrying ? 'מנסה שוב...' : 'נסה שוב'}
                  </button>
                )}
              </div>
            </div>
          )}
          
          {isLoading && (
            <div className={styles.loadingMessage}>
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
          
          <div ref={messagesEndRef} />
        </div>
        
        <InputMessageContainer 
          onSendMessage={onSendMessage}
          isLoading={isLoading}
          triggerFocusAnimation={triggerInputAnimation}
        />
      </div>
    );
} 