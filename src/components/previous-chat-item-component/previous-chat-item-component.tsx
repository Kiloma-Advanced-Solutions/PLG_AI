'use client';

import { Conversation } from '../../types';
import styles from './previous-chat-item-component.module.css';

/**
 * Props for the PreviousChatItemComponent
 */
type PreviousChatItemComponentProps = {
  /** The conversation data to display */
  conversation: Conversation;
  /** Whether this chat item is currently active/selected */
  isActive: boolean;
  /** Callback function when the item is clicked */
  onSelect: () => void;
};

/**
 * Component that renders a single conversation item in the sidebar
 * Shows only the conversation title
 */
export default function PreviousChatItemComponent({
  conversation,
  isActive,
  onSelect
}: PreviousChatItemComponentProps) {
  return (
    <div
      className={`${styles.conversationItem} ${isActive ? styles.active : ''}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect();
        }
      }}
      aria-label={`Open conversation: ${conversation.title}`}
    >
      <div className={styles.conversationItemTitle}>
        {conversation.title}
      </div>
    </div>
  );
} 