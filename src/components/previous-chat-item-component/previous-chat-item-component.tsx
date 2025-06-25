'use client';

import { Conversation } from '../../types';
import styles from './previous-chat-item-component.module.css';

/**
 * Props for the PreviousChatItemComponent.
 */
type PreviousChatItemComponentProps = {
  /** The conversation data to display. */
  conversation: Conversation;
  /** Whether this chat item is the currently active one. */
  isActive: boolean;
  /** Function to call when the item is clicked. */
  onSelect: () => void;
  /** Function to format the timestamp for display. */
  formatTimestamp: (timestamp: string) => string;
};

/**
 * A component that displays a single item in the list of previous conversations.
 * It shows the conversation's title, a preview of the last message, and a timestamp.
 */
export default function PreviousChatItemComponent({
  conversation,
  isActive,
  onSelect,
  formatTimestamp
}: PreviousChatItemComponentProps) {
  return (
    // The main container for the chat item.
    // It applies a special 'active' class if this is the current chat.
    // Clicking this div triggers the onSelect function to switch to this conversation.
    <div
      className={`${styles.conversationItem} ${isActive ? styles.active : ''}`}
      onClick={onSelect}
    >
      {/* Displays the title of the conversation. */}
      <div className={styles.conversationItemTitle}>
        {conversation.title}
      </div>
      {/* Displays the last message as a preview, or a default text if empty. */}
      <div className={styles.conversationItemPreview}>
        {conversation.lastMessage || 'שיחה ריקה'}
      </div>
      {/* Displays the formatted timestamp of the last message. */}
      <div className={styles.conversationItemTime}>
        {formatTimestamp(conversation.timestamp)}
      </div>
    </div>
  );
} 