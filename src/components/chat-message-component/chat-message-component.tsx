'use client';

import styles from './chat-message-component.module.css';

/**
 * Props for the ChatMessageComponent
 */
type ChatMessageComponentProps = {
  /** Type of message - determines styling and alignment */
  type: 'user' | 'assistant';
  /** The message content to display */
  content: string;
  /** Formatted timestamp string for display */
  timestamp: string;
  /** Whether this message is currently being streamed (shows cursor animation) */
  isStreaming?: boolean;
};

/**
 * Component that renders a single chat message with appropriate styling
 * based on message type (user or assistant)
 */
export default function ChatMessageComponent({ 
  type, 
  content, 
  timestamp,
  isStreaming = false
}: ChatMessageComponentProps) {
  return (
    <div className={`${styles.messageContainer} ${styles[type]}`}>
      <div className={styles.messageBox}>
        <div className={styles.messageText} dir="rtl">
          {content}
          {isStreaming && <span className={styles.streamingCursor}>|</span>}
        </div>
        <div className={styles.messageTime}>
          {timestamp}
        </div>
      </div>
    </div>
  );
} 