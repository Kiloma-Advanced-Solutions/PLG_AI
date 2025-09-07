'use client';

import React from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useConversationContext } from '../../contexts/ConversationContext';
import { getConversationsWithMessages } from '../../utils/conversation';
import HeaderComponent from '../header-component/header-component';
import SidebarComponent from '../sidebar-component/sidebar-component';
import styles from './app-layout.module.css';

type AppLayoutProps = {
  children: React.ReactNode;
};

/**
 * App layout component that provides persistent sidebar, header, and main content area
 * This component prevents re-rendering of UI elements when navigating between pages
 */
export default function AppLayout({ children }: AppLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const {
    conversations,
    isSidebarOpen,
    toggleSidebar,
    updateConversationTitle
  } = useConversationContext();

  /**
   * Handles new chat creation from header or sidebar
   */
  const handleNewChatClick = () => {
    router.push('/chat/new');
  };

  /**
   * Extract current conversation ID from URL
   */
  const getCurrentConversationId = (): string | undefined => {
    const match = pathname.match(/^\/chat\/([^\/]+)$/);
    return match && match[1] !== 'new' ? match[1] : undefined;
  };

  const currentConversationId = getCurrentConversationId();

  /**
   * Get conversations with messages for sidebar display
   */
  const conversationsWithMessages = getConversationsWithMessages(conversations);

  return (
    <div className={styles.container} dir="rtl">
      <HeaderComponent 
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={toggleSidebar}
        onNewChatClick={handleNewChatClick}
      />
      
      <main className={`${styles.main} ${isSidebarOpen ? styles.shifted : ''}`}>
        {children}
      </main>
      
      <SidebarComponent
        conversations={conversationsWithMessages}
        currentConversationId={currentConversationId}
        isOpen={isSidebarOpen}
        onToggle={toggleSidebar}
        onNewChatClick={handleNewChatClick}
        onTitleEdit={updateConversationTitle}
      />
    </div>
  );
}
