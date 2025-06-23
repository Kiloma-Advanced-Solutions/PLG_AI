'use client';

import { Conversation } from '../../types';
import styles from './previous-chat-item-component.module.css';

type PreviousChatItemComponentProps = {
  conversation: Conversation;
  isActive: boolean;
  onSelect: () => void;
  formatTimestamp: (timestamp: string) => string;
};

export default function PreviousChatItemComponent({
  conversation,
  isActive,
  onSelect,
  formatTimestamp
}: PreviousChatItemComponentProps) {
  return (
    <div
      className={`${styles.conversationItem} ${isActive ? styles.active : ''}`}
      onClick={onSelect}
    >
      <div className={styles.conversationItemTitle}>
        {conversation.title}
      </div>
      <div className={styles.conversationItemPreview}>
        {conversation.lastMessage || 'שיחה ריקה'}
      </div>
      <div className={styles.conversationItemTime}>
        {formatTimestamp(conversation.timestamp)}
      </div>
    </div>
  );
} 