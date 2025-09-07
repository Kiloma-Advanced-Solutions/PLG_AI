'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import ChatContainerComponent from '../../../components/chat-container-component/chat-container-component';
import { useConversationContext } from '../../../contexts/ConversationContext';
import styles from './page.module.css';

/**
 * Chat page component for displaying a specific conversation
 */
export default function ChatPage() {
  const router = useRouter();
  const params = useParams();
  const conversationId = params.id as string;
  
  const { 
    conversations,
    isStreaming, 
    isNavigationLoading,
    streamingMessage, 
    apiError, 
    getConversation, 
    sendMessage, 
    retryLastMessage,
    createStopHandler,
    createMessageEditHandler,
    setNavigationLoading,
    isSidebarOpen
  } = useConversationContext();
  const [prefilledMessage, setPrefilledMessage] = useState('');
  const currentConversation = getConversation(conversationId);

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
   * Renders the page content - only the chat container or loading state
   */
  return (
    <>
      {(isNavigationLoading || !currentConversation) ? (
        <div className={styles.loadingContainer}>
          <div className={styles.spinner}></div>
          <p>טוען...</p>
        </div>
      ) : (
        <ChatContainerComponent
          key={conversationId}
          messages={currentConversation.messages}
          onSendMessage={handleSendMessage}
          onMessageEdit={createMessageEditHandler(conversationId)}
          isStreaming={isStreaming}
          isSidebarOpen={isSidebarOpen}
          streamingMessage={streamingMessage}
          apiError={apiError}
          onRetry={retryLastMessage}
          onStop={handleStop}
          prefilledMessage={prefilledMessage}
          onPrefilledMessageCleared={handlePrefilledMessageCleared}
        />
      )}
    </>
  );
} 