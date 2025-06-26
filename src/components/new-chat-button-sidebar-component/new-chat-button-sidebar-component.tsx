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
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="#000000">
          <g>
            <path 
              d="M12,12h0a6.93,6.93,0,0,1,2-4.89l4.66-4.66a2,2,0,0,1,2.87,0h0a2,2,0,0,1,0,2.87L16.89,10A6.92,6.92,0,0,1,12,12Z"
              fill="none"
              stroke="#020202"
              strokeWidth="1.91"
              strokeMiterlimit="10"
            />
            <path 
              d="M14.86,1.48H5.32A3.82,3.82,0,0,0,1.5,5.3v9.54a3.82,3.82,0,0,0,3.82,3.82H9.14L12,21.52l2.86-2.86h3.82a3.82,3.82,0,0,0,3.82-3.82V9.11"
              fill="none"
              stroke="#020202"
              strokeWidth="1.91"
              strokeMiterlimit="10"
            />
          </g>
        </svg>
        </div>
      </button>
      <span className={styles.plusTitle}>צור שיחה חדשה</span>
    </div>
  );
} 