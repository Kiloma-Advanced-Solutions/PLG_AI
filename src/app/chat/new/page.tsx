'use client';

import { useEffect, useState } from 'react';
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
    retryLastMessage 
  } = useConversations();
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [shouldFocusInput, setShouldFocusInput] = useState(true);



  const handleSendMessage = async (messageContent: string) => {
    // Create a new conversation when sending the first message
    const newConversation = createConversation();
    
    // Redirect to the new conversation route
    router.push(`/chat/${newConversation.id}`);
    
    // Send the message
    await sendMessage(newConversation.id, messageContent);
  };

  // Get sidebar conversations (only ones with messages)
  const sidebarConversations = conversations.filter(conv => conv.messages.length > 0);

  return (
    <div className={styles.container} dir="rtl">
      <HeaderComponent 
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
      />
      
      <main className={`${styles.main} ${isSidebarOpen ? styles.shifted : ''}`}>
        <ChatContainerComponent
          messages={[]}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          isSidebarOpen={isSidebarOpen}
          shouldFocusInput={shouldFocusInput}
          streamingMessage={streamingMessage}
          apiError={apiError}
          onRetry={retryLastMessage}
        />
      </main>
      
      <SidebarComponent
        conversations={sidebarConversations}
        currentConversationId={undefined}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />
    </div>
  );
} 