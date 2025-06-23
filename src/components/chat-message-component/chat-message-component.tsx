'use client';

import styles from './chat-message-component.module.css';

type ChatMessageComponentProps = {
  type: 'user' | 'assistant';
  content: string;
  timestamp: string;
};

export default function ChatMessageComponent({ 
  type, 
  content, 
  timestamp 
}: ChatMessageComponentProps) {
  return (
    <div className={`${styles.messageContainer} ${styles[type]}`}>
      <div className={styles.messageBox}>
        <div className={styles.messageText} dir="rtl">
          {content}
        </div>
        <div className={styles.messageTime}>
          {timestamp}
        </div>
      </div>
    </div>
  );
} 