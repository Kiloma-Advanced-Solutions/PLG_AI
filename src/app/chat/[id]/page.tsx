'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import HeaderComponent from '../../../components/header-component/header-component';
import SidebarComponent from '../../../components/sidebar-component/sidebar-component';
import ChatContainerComponent from '../../../components/chat-container-component/chat-container-component';
import { useConversations } from '../../../contexts/ConversationContext';
import styles from '../../page.module.css';

export default function ChatPage() {
  const router = useRouter();
  const params = useParams();
  const conversationId = params.id as string;
  
  const { 
    conversations, 
    isLoading, 
    streamingMessage, 
    apiError, 
    getConversation, 
    sendMessage, 
    retryLastMessage 
  } = useConversations();
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [shouldFocusInput, setShouldFocusInput] = useState(false);

  const currentConversation = getConversation(conversationId);

  // Redirect to /chat/new if conversation doesn't exist
  useEffect(() => {
    if (conversations.length > 0 && !currentConversation) {
      router.push('/chat/new');
    }
  }, [conversations, currentConversation, router]);



  const handleSendMessage = async (messageContent: string) => {
    if (currentConversation) {
      await sendMessage(currentConversation.id, messageContent);
    }
  };

  // Get sidebar conversations (only ones with messages)
  const sidebarConversations = conversations.filter(conv => conv.messages.length > 0);

  // Show loading or redirect if conversation doesn't exist
  if (!currentConversation) {
    return (
      <div className={styles.container} dir="rtl">
        <HeaderComponent 
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        />
        
        <main className={`${styles.main} ${isSidebarOpen ? styles.shifted : ''}`}>
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <p>טוען...</p>
          </div>
        </main>
        
        <SidebarComponent
          conversations={sidebarConversations}
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
          shouldFocusInput={shouldFocusInput}
          streamingMessage={streamingMessage}
          apiError={apiError}
          onRetry={retryLastMessage}
        />
      </main>
      
      <SidebarComponent
        conversations={sidebarConversations}
        currentConversationId={conversationId}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />
    </div>
  );
} 