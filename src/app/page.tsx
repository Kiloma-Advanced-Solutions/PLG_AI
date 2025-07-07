'use client';

import { useState, useEffect, useRef } from 'react';
import HeaderComponent from '../components/header-component/header-component';
import SidebarComponent from '../components/sidebar-component/sidebar-component';
import ChatContainerComponent from '../components/chat-container-component/chat-container-component';
import { Message, Conversation } from '../types';
import { streamChatResponse, StreamError } from '../utils/streaming-api';
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
  
  // ref to trigger input focus
  const [shouldFocusInput, setShouldFocusInput] = useState(false);
  
  // holds the current streaming message content
  const [streamingMessage, setStreamingMessage] = useState('');
  
  // ref for abort controller to cancel streaming
  const abortControllerRef = useRef<AbortController | null>(null);
  
  // ref to track streaming content for cleanup
  const streamingContentRef = useRef<string>('');
  
  // error state for API errors
  const [apiError, setApiError] = useState<string | null>(null);

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

    // if the current conversation is empty, focus the input field instead
    if (currentConversation && currentConversation.messages.length === 0) {
      setIsSidebarOpen(false);
      setShouldFocusInput(true);
      // Reset the focus trigger after a short delay
      setTimeout(() => setShouldFocusInput(false), 100);
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
    
    // Auto-close sidebar on mobile when conversation is selected
    if (typeof window !== 'undefined' && window.innerWidth <= 500) {
      setIsSidebarOpen(false);
    }
  };

  // handle the sending of a message from the user to the assistant
  const handleSendMessage = async (messageBox: string) => {
    let conversationId = currentConversationId;
    
    // Clear any previous errors
    setApiError(null);
    
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

    // start the loading state and streaming
    setIsLoading(true);
    setStreamingMessage('');
    streamingContentRef.current = '';
    
    // Create abort controller for this request
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // Get all messages in the conversation for context
    const currentConv = conversations.find(conv => conv.id === conversationId);
    const allMessages = currentConv ? [...currentConv.messages, userMessage] : [userMessage];

    // Stream the response
    await streamChatResponse(
      allMessages,
      // onToken callback - update streaming message
      (token: string) => {
        streamingContentRef.current += token;
        setStreamingMessage(streamingContentRef.current);
      },
      // onError callback - handle errors
      (error: StreamError) => {
        console.error('Streaming error:', error);
        setApiError(error.message);
        setIsLoading(false);
        setStreamingMessage('');
        streamingContentRef.current = '';
        abortControllerRef.current = null;
      },
      // onComplete callback - finalize message
      () => {
        const finalContent = streamingContentRef.current;
        
        // Only add message if we have content
        if (finalContent.trim()) {
          const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            type: 'assistant',
            content: finalContent,
            timestamp: new Date().toISOString()
          };

          // update the conversations list with the final message
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
        }
        
        // cleanup
        setIsLoading(false);
        setStreamingMessage('');
        streamingContentRef.current = '';
        abortControllerRef.current = null;
      },
      abortController
    );
  };

  // get the current conversation and the sidebar conversations
  const currentConversation = getCurrentConversation();
  const sidebarConversations = conversations.filter(conv => conv.messages.length > 0);

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
          shouldFocusInput={shouldFocusInput}
          streamingMessage={streamingMessage}
          apiError={apiError}
          onRetry={() => {
            if (apiError) {
              setApiError(null);
            }
          }}
        />
      </main>
      
      <SidebarComponent
        conversations={sidebarConversations}
        currentConversationId={currentConversationId || undefined}
        onConversationSelect={selectConversation}
        onCreateNewChat={createNewChat}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />
    </div>
  );
}
