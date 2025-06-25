'use client';

import { useState, useEffect, useRef } from 'react';
import HeaderComponent from '../components/header-component/header-component';
import SidebarComponent from '../components/sidebar-component/sidebar-component';
import ChatContainerComponent from '../components/chat-container-component/chat-container-component';
import { InputHandle } from '../components/input-message-container/input-message-container';
import { Message, Conversation } from '../types';
import styles from './page.module.css';

export default function Home() {

  /* holds the master list of all chat conversations in the application */
  const [conversations, setConversations] = useState<Conversation[]>([]);   

  /* holds the id of the current conversation */
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);

  /* holds the state of the sidebar */
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  /* holds the state of the loading and waiting for the AI response */
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<InputHandle>(null);

  // Load conversations from localStorage on mount
  useEffect(() => {
    const savedConversations = localStorage.getItem('chatplg-conversations');
    if (savedConversations) {
      const parsed = JSON.parse(savedConversations);
      setConversations(parsed);
      if (parsed.length > 0) {
        setCurrentConversationId(parsed[0].id);
      }
    }
  }, []);

  // Save conversations to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('chatplg-conversations', JSON.stringify(conversations));
  }, [conversations]);

  const getCurrentConversation = (): Conversation | null => {
    return conversations.find(conv => conv.id === currentConversationId) || null;
  };

  const createNewChat = () => {
    const currentConversation = getCurrentConversation();
    if (currentConversation && currentConversation.messages.length === 0) {
      setIsSidebarOpen(false);
      return;
    }

    const newConversation: Conversation = {
      id: Date.now().toString(),
      title: 'שיחה חדשה',
      lastMessage: '',
      timestamp: new Date().toISOString(),
      messages: []
    };
    
    setConversations(prev => [newConversation, ...prev]);
    setCurrentConversationId(newConversation.id);
    setIsSidebarOpen(false);
  };

  const selectConversation = (conversationId: string) => {
    setCurrentConversationId(conversationId);
  };

  const handleSendMessage = async (messageBox: string) => {
    if (!currentConversationId) {
      createNewChat();
      // Wait for the new conversation to be created
      setTimeout(() => handleSendMessage(messageBox), 100);
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: messageBox,
      timestamp: new Date().toISOString()
    };

    // Update conversations with the new message
    setConversations(prev => prev.map(conv => {
      if (conv.id === currentConversationId) {
        const isFirstMessage = conv.messages.length === 0;
        return {
          ...conv,
          title: isFirstMessage ? messageBox : conv.title,
          messages: [...conv.messages, userMessage],
          lastMessage: messageBox,
          timestamp: new Date().toISOString()
        };
      }
      return conv;
    }));

    setIsLoading(true);
    inputRef.current?.focus();

    // Simulate AI response (replace with actual API call)
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `תודה על ההודעה שלך: "${messageBox}". זו תגובה לדוגמה מהבוט.`,
        timestamp: new Date().toISOString()
      };

      setConversations(prev => prev.map(conv => {
        if (conv.id === currentConversationId) {
          return {
            ...conv,
            messages: [...conv.messages, assistantMessage],
            lastMessage: assistantMessage.content,
            timestamp: new Date().toISOString()
          };
        }
        return conv;
      }));

      setIsLoading(false);
    }, 1500);
  };

  const currentConversation = getCurrentConversation();
  const sidebarConversations = conversations.filter(conv => conv.messages.length > 0);
  const isNewChatDisabled = currentConversation ? currentConversation.messages.length === 0 : false;

  return (
    <div className={styles.container} dir="rtl">
      <HeaderComponent 
        onSidebarToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        isSidebarOpen={isSidebarOpen}
      />
      
      <main className={`${styles.main} ${isSidebarOpen ? styles.shifted : ''}`}>
        <ChatContainerComponent
          messages={currentConversation?.messages || []}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          isSidebarOpen={isSidebarOpen}
          ref={inputRef}
        />
      </main>
      
      <SidebarComponent
        conversations={sidebarConversations}
        currentConversationId={currentConversationId || undefined}
        onConversationSelect={selectConversation}
        onCreateNewChat={createNewChat}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        isNewChatDisabled={isNewChatDisabled}
      />
    </div>
  );
}
