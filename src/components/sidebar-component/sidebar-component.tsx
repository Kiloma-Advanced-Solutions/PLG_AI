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
      setIsMobile(window.innerWidth < 576); // Only true mobile devices, not tablets
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
    if (isMobile) {
      // Mobile: close sidebar and navigate with delay
      goToConversation(conversationId, onToggle);
    } else {
      // Tablet/Desktop: keep sidebar open, navigate immediately
      goToConversation(conversationId);
    }
  };
  
  /**
   * Handles new chat creation with sidebar closing
   * On mobile devices, always close sidebar after creating new chat
   */
  const handleCreateNewChat = () => {
    if (isMobile) {
      // Mobile: close sidebar and navigate with delay
      goToNewChat(onToggle);
    } else {
      // Tablet/Desktop: keep sidebar open, just navigate
      goToNewChat();
    }
  };
  
  return (
    <div className={`${styles.sidebar} ${isOpen ? styles.open : ''}`}>
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