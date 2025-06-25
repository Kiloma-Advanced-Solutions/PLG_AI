'use client';

import { useRef, useEffect } from 'react';
import { Message } from '../../types';
import ChatMessageComponent from '../chat-message-component/chat-message-component';
import InputMessageContainer from '../input-message-container/input-message-container';
import styles from './chat-container-component.module.css';

type ChatContainerComponentProps = {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  isSidebarOpen?: boolean;
};

export default function ChatContainerComponent({ 
  messages, 
  onSendMessage, 
  isLoading = false,
  isSidebarOpen = false
}: ChatContainerComponentProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('he-IL', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className={`${styles.chatContainer} ${isSidebarOpen ? styles.shifted : ''}`}>
      <div className={styles.messagesContainer}>
        {messages.length === 0 ? (
          <div className={styles.welcomeMessage}>
            <h2>ברוכים הבאים ל-ChatPLG!</h2>
            <p>התחל שיחה חדשה על ידי שליחת הודעה</p>
          </div>
        ) : (
          messages.map((message) => (
            <ChatMessageComponent
              key={message.id}
              type={message.type}
              content={message.content}
              timestamp={formatTimestamp(message.timestamp)}
            />
          ))
        )}
        
        {isLoading && (
          <div className={`${styles.messageContainer} ${styles.assistant}`}>
            <div className={styles.typingIndicator}>
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <InputMessageContainer 
        onSendMessage={onSendMessage}
        isLoading={isLoading}
      />
    </div>
  );
} 