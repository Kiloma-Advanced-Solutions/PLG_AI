'use client';

import styles from './new-chat-button-component.module.css';

type NewChatButtonComponentProps = {
  onClick: () => void;
};

export default function NewChatButtonComponent({ onClick }: NewChatButtonComponentProps) {
  return (
    <button 
      className={styles.newChatButton}
      onClick={onClick}
    >
      <svg className={styles.plusIcon} fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
      </svg>
      צור שיחה חדשה
    </button>
  );
} 