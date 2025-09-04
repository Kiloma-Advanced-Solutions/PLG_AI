'use client';

import { Conversation } from '../../types';
import NewChatButtonComponent from '../new-chat-button-component/new-chat-button-component';
import PreviousChatListComponent from '../previous-chat-list-component/previous-chat-list-component';
import { useNavigationHelpers } from '../../hooks/useNavigationHelpers';
import styles from './sidebar-component.module.css';

/**
 * Props for the SidebarComponent
 */
type SidebarComponentProps = {
  conversations: Conversation[];
  currentConversationId?: string;
  isOpen: boolean;
  onToggle: () => void;
  onNewChatClick?: () => void;
  onTitleEdit?: (conversationId: string, newTitle: string) => void;
};

/**
 * Sidebar component that displays navigation and conversation history
 */
export default function SidebarComponent({
  conversations,
  currentConversationId,
  isOpen,
  onToggle,
  onNewChatClick,
  onTitleEdit
}: SidebarComponentProps) {
  const { goToConversation, goToNewChat } = useNavigationHelpers();
  
  /**
   * Handles conversation selection
   */
  const handleConversationSelect = (conversationId: string) => {
    goToConversation(conversationId, undefined); // Keep sidebar open when selecting chats
  };
  
  /**
   * Handles new chat creation with sidebar closing
   */
  const handleCreateNewChat = () => {
    goToNewChat(isOpen ? onToggle : undefined, onNewChatClick);
  };
  
  return (
    <div className={`${styles.sidebar} ${isOpen ? styles.open : ''}`}>
      <div className={styles.burgerSection}>
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

      <NewChatButtonComponent 
        onClick={handleCreateNewChat}
        isOpen={isOpen}
      />

      {isOpen && (
        <div className={styles.sidebarContent}>
          <div className={styles.sidebarHeader}>
            <h2>שיחות קודמות</h2>
          </div>
          
          <PreviousChatListComponent
            conversations={conversations}
            currentConversationId={currentConversationId}
            onConversationSelect={handleConversationSelect}
            onTitleEdit={onTitleEdit}
          />
        </div>
      )}
    </div>
  );
} 