'use client';

import { Conversation } from '../../types';
import NewChatButtonComponent from '../new-chat-button-component/new-chat-button-component';
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
      {isOpen ? (
        <>
          <div className={styles.sidebarContent}>
            <div className={styles.sidebarHeader}>
              <h2>שיחות קודמות</h2>
              <NewChatButtonComponent onClick={onCreateNewChat} />
            </div>
            
            <PreviousChatListComponent
              conversations={conversations}
              currentConversationId={currentConversationId}
              onConversationSelect={onConversationSelect}
            />
          </div>
        </>
      ) : (
        /* mini sidebar icons when closed */
        <div className={styles.miniSidebar}>
          {/* new chat icon */}
          <div className={styles.miniIcon} onClick={onCreateNewChat}>
            <svg fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
          </div>
          {/* burger sidebar icon */}
          <div className={styles.miniIcon} onClick={onToggle}>
            <svg fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
            </svg>
          </div>
        </div>
      )}
    </div>
  );
} 