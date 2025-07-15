'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import HeaderComponent from '../../../components/header-component/header-component';
import SidebarComponent from '../../../components/sidebar-component/sidebar-component';
import ChatContainerComponent from '../../../components/chat-container-component/chat-container-component';
import { useConversationHelpers } from '../../../hooks/useConversations';
import styles from '../../page.module.css';

/**
 * New chat page component for starting fresh conversations
 */
export default function NewChatPage() {
  const router = useRouter();
  const { 
    conversationsWithMessages,
    isLoading, 
    isNavigationLoading,
    streamingMessage, 
    apiError, 
    createConversation, 
    sendMessage, 
    retryLastMessage,
    conversations,
    setNavigationLoading
  } = useConversationHelpers();
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [triggerInputAnimation, setTriggerInputAnimation] = useState(false);

  // Handle initial page loading state - stop loading immediately when page is ready
  useEffect(() => {
    setNavigationLoading(false);
  }, [setNavigationLoading]);

  /**
   * Handles new chat click animation trigger
   */
  const handleNewChatClick = () => {
    // Only trigger animation if we're on an empty conversation
    if (!currentConversationId && !displayMessages.length) {
      setTriggerInputAnimation(true);
      setTimeout(() => setTriggerInputAnimation(false), 100);
    }
  };

  /**
   * Handles sending the first message and creating a new conversation
   */
  const handleSendMessage = async (messageContent: string) => {
    // Create a new conversation when sending the first message
    const newConversation = createConversation();
    setCurrentConversationId(newConversation.id);
    
    // Send the message
    await sendMessage(newConversation.id, messageContent);
    
    // Navigate to the conversation page
    router.push(`/chat/${newConversation.id}`);
  };

  // Get the current conversation and its messages for display
  const currentConversation = currentConversationId ? 
    conversations.find(conv => conv.id === currentConversationId) : null;
  const displayMessages = currentConversation?.messages || [];

  // Show loading state briefly for smooth navigation experience
  if (isNavigationLoading) {
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
          currentConversationId={currentConversationId || undefined}
          isOpen={isSidebarOpen}
          onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
          onNewChatClick={handleNewChatClick}
        />
      </div>
    );
  }

  return (
    <div className={styles.container} dir="rtl">
      <HeaderComponent 
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        onNewChatClick={handleNewChatClick}
      />
      
      <main className={`${styles.main} ${isSidebarOpen ? styles.shifted : ''}`}>
        <ChatContainerComponent
          messages={displayMessages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          isSidebarOpen={isSidebarOpen}
          streamingMessage={streamingMessage}
          apiError={apiError}
          onRetry={retryLastMessage}
          triggerInputAnimation={triggerInputAnimation}
        />
      </main>
      
      <SidebarComponent
        conversations={conversationsWithMessages}
        currentConversationId={currentConversationId || undefined}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        onNewChatClick={handleNewChatClick}
      />
    </div>
  );
} 