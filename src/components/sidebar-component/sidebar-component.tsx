'use client';

import { useRouter } from 'next/navigation';
import { Conversation } from '../../types';
import NewChatButtonComponent from '../new-chat-button-component/new-chat-button-component';
import PreviousChatListComponent from '../previous-chat-list-component/previous-chat-list-component';
import styles from './sidebar-component.module.css';

// Props for the SidebarComponent component
type SidebarComponentProps = {
  conversations: Conversation[];
  currentConversationId?: string;
  isOpen: boolean;
  onToggle: () => void;
};

// function to render the SidebarComponent component
export default function SidebarComponent({
  conversations,
  currentConversationId,
  isOpen,
  onToggle
}: SidebarComponentProps) {
  const router = useRouter();
  
  const handleConversationSelect = (conversationId: string) => {
    router.push(`/chat/${conversationId}`);
  };
  
  const handleCreateNewChat = () => {
    router.push('/chat/new');
  };
  
  return (
    <div className={`${styles.sidebar} ${isOpen ? styles.open : ''}`}>
      {/* Burger icon at header height */}
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

      {/* newChatIcon icon */}
      <NewChatButtonComponent 
        onClick={handleCreateNewChat}
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
            onConversationSelect={handleConversationSelect}
          />
        </div>
      ) : null}
    </div>
  );
} 