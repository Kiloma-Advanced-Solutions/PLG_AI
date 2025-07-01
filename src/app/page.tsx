'use client';

import { useState, useEffect } from 'react';
import HeaderComponent from '../components/header-component/header-component';
import SidebarComponent from '../components/sidebar-component/sidebar-component';
import ChatContainerComponent from '../components/chat-container-component/chat-container-component';
import { Message, Conversation } from '../types';
import styles from './page.module.css';

export default function Home() {

  // holds the master list of all chat conversations in the application 
  const [conversations, setConversations] = useState<Conversation[]>([]);

  // holds the id of the current conversation 
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);

  // holds the state of the sidebar
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // holds the state of the loading and waiting for the AI response
  const [isLoading, setIsLoading] = useState(false);

  // Load conversations from localStorage on mount
  useEffect(() => {
    const savedConversations = localStorage.getItem('chatplg-conversations');
    const savedCurrentConversationId = localStorage.getItem('chatplg-current-conversation-id');
    
    if (savedConversations) {
      const parsed = JSON.parse(savedConversations);
      setConversations(parsed);
      
      // Restore the last active conversation, or default to first if none saved
      if (savedCurrentConversationId && parsed.find((conv: Conversation) => conv.id === savedCurrentConversationId)) {
        setCurrentConversationId(savedCurrentConversationId);
      } else if (parsed.length > 0) {
        setCurrentConversationId(parsed[0].id);
      }
    }
  }, []);

  // Save conversations to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('chatplg-conversations', JSON.stringify(conversations));
  }, [conversations]);

  // Save current conversation ID whenever it changes
  useEffect(() => {
    if (currentConversationId) {
      localStorage.setItem('chatplg-current-conversation-id', currentConversationId);
    }
  }, [currentConversationId]);

  const getCurrentConversation = (): Conversation | null => {
    return conversations.find(conv => conv.id === currentConversationId) || null;
  };

  const createNewChat = () => {
    const currentConversation = getCurrentConversation();

    // if the current conversation is empty, don't create a new chat and close sidebar
    if (currentConversation && currentConversation.messages.length === 0) {
      setIsSidebarOpen(false);
      return;
    }

    const newConversation: Conversation = {
      id: Date.now().toString(),
      title: 'שיחה חדשה',   // temporary placeholder title 
      lastMessage: '',
      timestamp: new Date().toISOString(),
      messages: []
    };
    
    // add the new conversation to the conversations list
    setConversations(prev => [newConversation, ...prev]);

    // set the current conversation id to the new conversation
    setCurrentConversationId(newConversation.id);

    // close the sidebar
    setIsSidebarOpen(false);
  };


  // select a conversation from the sidebar
  const selectConversation = (conversationId: string) => {
    setCurrentConversationId(conversationId);
  };

  // handle the sending of a message from the user to the assistant
  const handleSendMessage = async (messageBox: string) => {
    let conversationId = currentConversationId;
    
    // If no current conversation, create one first
    if (!conversationId) {
      const newConversation: Conversation = {
        id: Date.now().toString(),
        title: 'שיחה חדשה',
        lastMessage: '',
        timestamp: new Date().toISOString(),
        messages: []
      };
      
      // Add the new conversation to the list
      setConversations(prev => [newConversation, ...prev]);
      setCurrentConversationId(newConversation.id);
      conversationId = newConversation.id;
    }

    // create a new message from the user
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: messageBox,
      timestamp: new Date().toISOString()
    };

    // Update conversations with the new message
    setConversations(prev => prev.map(conv => {
      if (conv.id === conversationId) {
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

    // start the loading state
    setIsLoading(true);

    // Simulate AI response
    setTimeout(() => {
      // create a new message from the assistant
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `תודה על ההודעה שלך: "${messageBox}". זו תגובה לדוגמה מהבוט.`,
        timestamp: new Date().toISOString()
      };

      // update the conversations list with the new message
      setConversations(prev => prev.map(conv => {
        if (conv.id === conversationId) {
          return {
            ...conv,
            messages: [...conv.messages, assistantMessage],
            lastMessage: assistantMessage.content,
            timestamp: new Date().toISOString()
          };
        }
        return conv;
      }));

      // stop the loading state
      setIsLoading(false);
    }, 1500);
  };

  // get the current conversation and the sidebar conversations
  const currentConversation = getCurrentConversation();
  const sidebarConversations = conversations.filter(conv => conv.messages.length > 0);
  const isNewChatDisabled = currentConversation ? currentConversation.messages.length === 0 : true;

  // render the main page
  return (
    <div className={styles.container} dir="rtl">
      <HeaderComponent 
        isSidebarOpen={isSidebarOpen}
        onCreateNewChat={createNewChat}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
      />
      
      <main className={`${styles.main} ${isSidebarOpen ? styles.shifted : ''}`}>
        <ChatContainerComponent
          messages={currentConversation?.messages || []}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          isSidebarOpen={isSidebarOpen}
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
