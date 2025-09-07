'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import ChatContainerComponent from '../../../components/chat-container-component/chat-container-component';
import { useConversationContext } from '../../../contexts/ConversationContext';

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
    retryLastMessage,
    createStopHandler,
    createMessageEditHandler,
    setNavigationLoading,
    isSidebarOpen
  } = useConversationContext();
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [triggerInputAnimation, setTriggerInputAnimation] = useState(false);
  const [prefilledMessage, setPrefilledMessage] = useState('');
  const shouldNavigateRef = useRef(false);

  // Filter out current conversation from sidebar until URL changes from /chat/new
  const sidebarConversations = pathname === '/chat/new' && currentConversationId
    ? conversations.filter(conv => conv.id !== currentConversationId)
    : conversations;

  // Reset state when navigating to new chat page
  useEffect(() => {
    if (pathname === '/chat/new') {
      setCurrentConversationId(null);
      setPrefilledMessage('');
      shouldNavigateRef.current = false;
      
      // Trigger animation
      setTriggerInputAnimation(true);
    }
  }, [pathname]);

  // Listen for animation triggers from sidebar/header buttons
  useEffect(() => {
    const triggerAnimation = () => {
      setTriggerInputAnimation(false); // Reset first
      setTimeout(() => setTriggerInputAnimation(true), 10); // Then trigger
    };
    
    window.addEventListener('triggerInputAnimation', triggerAnimation);
    return () => window.removeEventListener('triggerInputAnimation', triggerAnimation);
  }, []);


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
    <ChatContainerComponent
      key={currentConversationId || 'new'}
      messages={displayMessages}
      onSendMessage={handleSendMessage}
      onMessageEdit={createMessageEditHandler(currentConversationId)}
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
  );
} 