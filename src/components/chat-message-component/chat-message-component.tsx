'use client';

import styles from './chat-message-component.module.css';

// the props of the chat message component
type ChatMessageComponentProps = {
  type: 'user' | 'assistant';
  content: string;
  timestamp: string;
  isStreaming?: boolean;
};

// the chat message component
export default function ChatMessageComponent({ 
  type, 
  content, 
  timestamp,
  isStreaming = false
}: ChatMessageComponentProps) {
  // render the chat message component
  return (
    // the container of the message
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