'use client';

import { Conversation } from '../../types';
import NewChatButtonSidebarComponent from '../new-chat-button-sidebar-component/new-chat-button-sidebar-component';
import PreviousChatListComponent from '../previous-chat-list-component/previous-chat-list-component';
import styles from './sidebar-component.module.css';

type SidebarComponentProps = {
  conversations: Conversation[];
  currentConversationId?: string;
  onConversationSelect: (conversationId: string) => void;
  onCreateNewChat: () => void;
  isOpen: boolean;
  onToggle: () => void;
};

export default function SidebarComponent({
  conversations,
  currentConversationId,
  onConversationSelect,
  onCreateNewChat,
  isOpen,
  onToggle
}: SidebarComponentProps) {
  return (
    <div className={`${styles.sidebar} ${isOpen ? styles.open : ''}`}>
      {/* Burger icon at header height - always visible */}
      <div className={styles.rightSection}>
        <button 
          className={styles.burgerButton}
          onClick={onToggle}
          aria-label={isOpen ? "Close sidebar" : "Open sidebar"}
        >
          <svg className={styles.burgerIcon} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
          </svg>
        </button>
      </div>

      {/* Plus icon - always visible */}
      <NewChatButtonSidebarComponent 
        onClick={onCreateNewChat}
        isOpen={isOpen}
      />

      {isOpen ? (
        <div className={styles.sidebarContent}>
          <div className={styles.sidebarHeader}>
            <h2>שיחות קודמות</h2>
          </div>
          
          <PreviousChatListComponent
            conversations={conversations}
            currentConversationId={currentConversationId}
            onConversationSelect={onConversationSelect}
          />
        </div>
      ) : (
        <div className={styles.miniSidebar}>
          {/* Additional mini icons can go here if needed */}
        </div>
      )}
    </div>
  );
} 