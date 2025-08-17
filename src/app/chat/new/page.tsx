'use client';

import { useState, useEffect, useRef } from 'react';
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
    isInitializing,
    streamingMessage, 
    apiError, 
    createConversation, 
    sendMessage, 
    retryLastMessage,
    stopStreaming,
    conversations,
    setNavigationLoading
  } = useConversationHelpers();
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [triggerInputAnimation, setTriggerInputAnimation] = useState(false);
  const [prefilledMessage, setPrefilledMessage] = useState('');
  const shouldNavigateRef = useRef(false);



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
    
    // Set flag to navigate after successful completion
    shouldNavigateRef.current = true;
    
    // Send the message (this will start streaming)
    await sendMessage(newConversation.id, messageContent);
    
    // If we reach here and shouldNavigate is still true, navigate
    if (shouldNavigateRef.current) {
      router.push(`/chat/${newConversation.id}`);
    }
  };

  /**
   * Handles stopping the streaming response
   */
  const handleStop = () => {
    // Cancel any pending navigation
    shouldNavigateRef.current = false;
    
    const restoredMessage = stopStreaming();
    
    // Reset conversation state on new chat page immediately
    setCurrentConversationId(null);
    
    // Ensure no navigation loading state interferes
    setNavigationLoading(false);
    
    // Set prefilled message immediately
    if (restoredMessage) {
      setPrefilledMessage(restoredMessage);
    }
  };

  /**
   * Handles clearing the prefilled message
   */
  const handlePrefilledMessageCleared = () => {
    setPrefilledMessage('');
  };

  // Get the current conversation and its messages for display
  const currentConversation = currentConversationId ? 
    conversations.find(conv => conv.id === currentConversationId) : null;
  const displayMessages = currentConversation?.messages || [];

  // Don't show loading state when we have a prefilled message (after stop)
  const shouldShowInitializing = isInitializing && !prefilledMessage;

  // Show loading state only during initial context setup and not when we have a prefilled message
  if (shouldShowInitializing) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        direction: 'rtl' 
      }}>
        <p>טוען...</p>
      </div>
    );
  }

  // Main component render

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
          onStop={handleStop}
          triggerInputAnimation={triggerInputAnimation}
          prefilledMessage={prefilledMessage}
          onPrefilledMessageCleared={handlePrefilledMessageCleared}
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