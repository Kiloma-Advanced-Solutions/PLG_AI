'use client';

import styles from './new-chat-button-sidebar-component.module.css';

type NewChatButtonSidebarComponentProps = {
  onClick: () => void;
  isOpen: boolean;
  disabled: boolean;
};

export default function NewChatButtonSidebarComponent({ 
  onClick, 
  isOpen,
  disabled
}: NewChatButtonSidebarComponentProps) {
  return (
    <div className={`${styles.plusSectionWrapper} ${isOpen ? styles.open : ''}`}>
      <button 
        className={styles.plusButton} 
        onClick={onClick}
        disabled={disabled}
        aria-label="Create new chat"
      >
        <div className={styles.plusIcon}>
          <svg fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
          </svg>
        </div>
      </button>
      <span className={styles.plusTitle}>צור שיחה חדשה</span>
    </div>
  );
} 