'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import HeaderComponent from '../../../components/header-component/header-component';
import SidebarComponent from '../../../components/sidebar-component/sidebar-component';
import ChatContainerComponent from '../../../components/chat-container-component/chat-container-component';
import { useConversations } from '../../../contexts/ConversationContext';
import styles from '../../page.module.css';

export default function NewChatPage() {
  const router = useRouter();
  const { 
    conversations, 
    isLoading, 
    streamingMessage, 
    apiError, 
    createConversation, 
    sendMessage, 
    retryLastMessage,
    setNavigationLoading
  } = useConversations();
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);

  // Clear navigation loading when the new chat page loads
  useEffect(() => {
    setNavigationLoading(false);
  }, [setNavigationLoading]);

  const handleSendMessage = async (messageContent: string) => {
    // Create a new conversation when sending the first message
    const newConversation = createConversation();
    setCurrentConversationId(newConversation.id);
    
    // Send the message
    await sendMessage(newConversation.id, messageContent);
    
    // Navigate to the conversation page
    router.push(`/chat/${newConversation.id}`);
  };

  // Get sidebar conversations (only ones with messages)
  const sidebarConversations = conversations.filter(conv => conv.messages.length > 0);

  // Get the current conversation and its messages
  const currentConversation = currentConversationId ? 
    conversations.find(conv => conv.id === currentConversationId) : null;
  const displayMessages = currentConversation?.messages || [];

  return (
    <div className={styles.container} dir="rtl">
      <HeaderComponent 
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
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
        />
      </main>
      
      <SidebarComponent
        conversations={sidebarConversations}
        currentConversationId={currentConversationId || undefined}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />
    </div>
  );
} 