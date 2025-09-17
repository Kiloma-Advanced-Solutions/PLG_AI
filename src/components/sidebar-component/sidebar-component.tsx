'use client';

import { useState, useEffect } from 'react';
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
  onDelete?: (conversationId: string) => void;
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
  onTitleEdit,
  onDelete
}: SidebarComponentProps) {
  const { goToConversation, goToNewChat } = useNavigationHelpers();
  const [isMobile, setIsMobile] = useState(false);

  // Detect mobile screen size with proper SSR handling
  useEffect(() => {
    const checkIsMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    // Initial check
    checkIsMobile();

    // Listen for window resize
    window.addEventListener('resize', checkIsMobile);

    return () => {
      window.removeEventListener('resize', checkIsMobile);
    };
  }, []);
  
  /**
   * Handles conversation selection
   * On mobile devices, auto-close sidebar after selection for better UX
   */
  const handleConversationSelect = (conversationId: string) => {
    // Auto-close sidebar on mobile devices for better UX
    if (isMobile) {
      // Immediately close sidebar on mobile
      onToggle();
      // Navigate after a brief delay
      setTimeout(() => {
        goToConversation(conversationId);
      }, 150);
    } else {
      // Desktop behavior - keep sidebar open
      goToConversation(conversationId);
    }
  };
  
  /**
   * Handles new chat creation with sidebar closing
   * On mobile devices, always close sidebar after creating new chat
   */
  const handleCreateNewChat = () => {
    if (isMobile) {
      // Immediately close sidebar on mobile
      onToggle();
      // Navigate after a brief delay
      setTimeout(() => {
        goToNewChat();
      }, 150);
    } else {
      // Desktop behavior - close if already open
      goToNewChat(isOpen ? onToggle : undefined);
    }
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
            onDelete={onDelete}
          />
        </div>
      )}
    </div>
  );
} 