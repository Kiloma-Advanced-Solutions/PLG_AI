'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import HeaderComponent from '../../../components/header-component/header-component';
import SidebarComponent from '../../../components/sidebar-component/sidebar-component';
import ChatContainerComponent from '../../../components/chat-container-component/chat-container-component';
import { useConversationHelpers } from '../../../hooks/useConversations';
import styles from '../../page.module.css';

/**
 * Chat page component for displaying a specific conversation
 */
export default function ChatPage() {
  const router = useRouter();
  const params = useParams();
  const conversationId = params.id as string;
  
  const { 
    conversationsWithMessages,
    isLoading, 
    streamingMessage, 
    apiError, 
    getConversationSafely, 
    sendMessage, 
    retryLastMessage,
    conversations
  } = useConversationHelpers();
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isNavigationLoading, setIsNavigationLoading] = useState(true);
  const currentConversation = getConversationSafely(conversationId);

  // Handle navigation loading state
  useEffect(() => {
    // Start with loading true for initial page load
    setIsNavigationLoading(true);
    
    // Small delay to show loading state even for fast localStorage access
    const loadingTimer = setTimeout(() => {
      if (currentConversation || (conversations.length > 0 && !currentConversation)) {
        setIsNavigationLoading(false);
      }
    }, 100); // Brief loading period for better UX

    return () => clearTimeout(loadingTimer);
  }, [conversationId, currentConversation, conversations.length]);

  // Redirect to /chat/new if conversation doesn't exist
  useEffect(() => {
    if (conversations.length > 0 && !currentConversation && !isNavigationLoading) {
      router.push('/chat/new');
    }
  }, [conversations, currentConversation, router, isNavigationLoading]);

  /**
   * Handles sending a new message in the current conversation
   */
  const handleSendMessage = async (messageContent: string) => {
    if (currentConversation) {
      await sendMessage(currentConversation.id, messageContent);
    }
  };

  /**
   * Renders loading state when conversation is loading or not found
   */
  if (isNavigationLoading || !currentConversation) {
    return (
      <div className={styles.container} dir="rtl">
        <HeaderComponent 
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        />
        
        <main className={`${styles.main} ${isSidebarOpen ? styles.shifted : ''}`}>
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', width: '100%', flex: 1 }}>
            <div className={styles.loadingContainer}>
              <div className={styles.spinner}></div>
              <p>טוען...</p>
            </div>
          </div>
        </main>
        
        <SidebarComponent
          conversations={conversationsWithMessages}
          currentConversationId={conversationId}
          isOpen={isSidebarOpen}
          onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        />
      </div>
    );
  }

  return (
    <div className={styles.container} dir="rtl">
      <HeaderComponent 
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
      />
      
      <main className={`${styles.main} ${isSidebarOpen ? styles.shifted : ''}`}>
        <ChatContainerComponent
          messages={currentConversation.messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          isSidebarOpen={isSidebarOpen}
          streamingMessage={streamingMessage}
          apiError={apiError}
          onRetry={retryLastMessage}
        />
      </main>
      
      <SidebarComponent
        conversations={conversationsWithMessages}
        currentConversationId={conversationId}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />
    </div>
  );
} 