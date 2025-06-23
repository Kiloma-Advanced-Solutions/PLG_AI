'use client';

import styles from './new-chat-button-sidebar-component.module.css';

type NewChatButtonSidebarComponentProps = {
  onClick: () => void;
  isOpen: boolean;
};

export default function NewChatButtonSidebarComponent({ 
  onClick, 
  isOpen 
}: NewChatButtonSidebarComponentProps) {
  return (
    <div className={styles.plusSection} onClick={onClick}>
      <div className={styles.miniIcon}>
        <svg fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
        </svg>
      </div>
      {isOpen && (
        <span className={styles.plusTitle}>צור שיחה חדשה</span>
      )}
    </div>
  );
} 