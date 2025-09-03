'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import HeaderComponent from '../../../components/header-component/header-component';
import SidebarComponent from '../../../components/sidebar-component/sidebar-component';
import ChatContainerComponent from '../../../components/chat-container-component/chat-container-component';
import { useConversationContext } from '../../../contexts/ConversationContext';
import { getConversationsWithMessages } from '../../../utils/conversation';
import { useSidebar } from '../../../hooks/useSidebar';
import styles from '../../page.module.css';

/**
 * New chat page component for starting fresh conversations
 */
export default function NewChatPage() {
  const router = useRouter();
  const pathname = usePathname();
  const { 
    conversations,
    isStreaming, 
    streamingMessage, 
    apiError, 
    createConversation, 
    sendMessage, 
    updateConversationTitle,
    retryLastMessage,
    createStopHandler,
    setNavigationLoading
  } = useConversationContext();
  
  const { isSidebarOpen, toggleSidebar } = useSidebar();
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [triggerInputAnimation, setTriggerInputAnimation] = useState(false);
  const [prefilledMessage, setPrefilledMessage] = useState('');
  const shouldNavigateRef = useRef(false);

  // Filter out current conversation from sidebar until URL changes from /chat/new
  const sidebarConversations = pathname === '/chat/new' && currentConversationId
    ? conversations.filter(conv => conv.id !== currentConversationId)
    : conversations;
  const conversationsWithMessages = getConversationsWithMessages(sidebarConversations);

  /**
   * Reset component state when navigating back to /chat/new
   * This ensures a fresh start when clicking new chat after sending messages
   */
  useEffect(() => {
    if (pathname === '/chat/new') {
      setCurrentConversationId(null);
      setPrefilledMessage('');
      shouldNavigateRef.current = false;
    }
  }, [pathname]);

  /**
   * Handles new chat click
   */
  const handleNewChatClick = () => {
    // If currently streaming, use the proper stop handler to respect input state
    if (isStreaming) {
      handleStop(''); // Use empty string to ensure no input overwrite
      return;
    }
    
    // Only trigger animation if we're on an empty conversation
    if (!currentConversationId && !displayMessages.length) {
      setTriggerInputAnimation(true);
      setTimeout(() => setTriggerInputAnimation(false), 100);
    }
  };


  /**
   * Handles sending messages - creates new conversation only for first message
   */
  const handleSendMessage = async (messageContent: string) => {
    let conversationId: string;
    
    // Only create a new conversation if this is truly the first message
    if (!currentConversationId) {
      // Create a new conversation when sending the first message
      const newConversation = createConversation(messageContent);
      setCurrentConversationId(newConversation.id);
      conversationId = newConversation.id;
      
      // Set flag to update URL after successful completion (only for first message)
      shouldNavigateRef.current = true;
    } else {
      // Use existing conversation for subsequent messages
      conversationId = currentConversationId;
      shouldNavigateRef.current = false; // No URL change needed for subsequent messages
    }
    
    // Send the message (this will start streaming)
    await sendMessage(conversationId, messageContent);
    
    // If we reach here and shouldNavigate is still true, update URL without navigation
    if (shouldNavigateRef.current) {
      // Use replaceState to update URL without page reload/navigation
      window.history.replaceState(null, '', `/chat/${conversationId}`);
      shouldNavigateRef.current = false; // Reset flag after URL update
    }
  };

  /**
   * Handles stopping the streaming response
   */
  const handleStop = createStopHandler(setPrefilledMessage, () => {
    // Additional cleanup specific to new chat page
    shouldNavigateRef.current = false;
    setCurrentConversationId(null);
    setNavigationLoading(false);
  });

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

  // New chat page is always ready - no loading needed
  return (
    <div className={styles.container} dir="rtl">
      <HeaderComponent 
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={toggleSidebar}
        onNewChatClick={handleNewChatClick}
      />
      
      <main className={`${styles.main} ${isSidebarOpen ? styles.shifted : ''}`}>
        <ChatContainerComponent
          key={currentConversationId || 'new'}
          messages={displayMessages}
          onSendMessage={handleSendMessage}
          isStreaming={isStreaming}
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
        onToggle={toggleSidebar}
        onNewChatClick={handleNewChatClick}
        onTitleEdit={updateConversationTitle}
      />
    </div>
  );
} 