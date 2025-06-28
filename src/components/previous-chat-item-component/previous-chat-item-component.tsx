'use client';

import { Conversation } from '../../types';
import styles from './previous-chat-item-component.module.css';

// Props for the PreviousChatItemComponent component
type PreviousChatItemComponentProps = {
  conversation: Conversation;   // The conversation data to display
  isActive: boolean;  // Whether this chat item is the currently active one
  onSelect: () => void;  // Function to call when the item is clicked
  formatTimestamp: (timestamp: string) => string;  // Function to format the timestamp for display
};

// function to render the PreviousChatItemComponent component
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