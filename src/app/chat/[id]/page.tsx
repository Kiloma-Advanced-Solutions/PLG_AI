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
    isNavigationLoading,
    streamingMessage, 
    apiError, 
    getConversationSafely, 
    sendMessage, 
    retryLastMessage,
    createStopHandler,
    conversations,
    setNavigationLoading
  } = useConversationHelpers();
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [prefilledMessage, setPrefilledMessage] = useState('');
  const currentConversation = getConversationSafely(conversationId);

  // Restore preserved input from navigation if available
  useEffect(() => {
    const preservedInput = sessionStorage.getItem('preserved-input');
    if (preservedInput) {
      setPrefilledMessage(preservedInput);
      sessionStorage.removeItem('preserved-input');
    }
  }, []);

  // Handle navigation loading state - stop loading when conversation is ready
  useEffect(() => {
    if (currentConversation) {
      // Conversation is loaded, stop loading immediately
      setNavigationLoading(false);
    } else if (conversations.length > 0 && !currentConversation) {
      // Conversation doesn't exist, stop loading and redirect will happen
      setNavigationLoading(false);
    }
  }, [conversationId, currentConversation, conversations.length, setNavigationLoading]);

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
   * Handles stopping the streaming response - using simplified unified handler
   */
  const handleStop = createStopHandler(setPrefilledMessage);

  /**
   * Handles clearing the prefilled message
   */
  const handlePrefilledMessageCleared = () => {
    setPrefilledMessage('');
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
          messages={currentConversation!.messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          isSidebarOpen={isSidebarOpen}
          streamingMessage={streamingMessage}
          apiError={apiError}
          onRetry={retryLastMessage}
          onStop={handleStop}
          prefilledMessage={prefilledMessage}
          onPrefilledMessageCleared={handlePrefilledMessageCleared}
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