'use client';

import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { Message, Conversation } from '../types';
import { streamChatResponse, StreamError } from '../utils/streaming-api';

type ConversationContextType = {
  conversations: Conversation[];
  isLoading: boolean;
  streamingMessage: string;
  apiError: string | null;
  createConversation: () => Conversation;
  updateConversation: (id: string, updates: Partial<Conversation>) => void;
  deleteConversation: (id: string) => void;
  sendMessage: (conversationId: string, message: string) => Promise<void>;
  getConversation: (id: string) => Conversation | null;
  retryLastMessage: () => void;
};

const ConversationContext = createContext<ConversationContextType | undefined>(undefined);

export const useConversations = () => {
  const context = useContext(ConversationContext);
  if (!context) {
    throw new Error('useConversations must be used within a ConversationProvider');
  }
  return context;
};

export const ConversationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [apiError, setApiError] = useState<string | null>(null);
  
  // refs for streaming
  const abortControllerRef = useRef<AbortController | null>(null);
  const streamingContentRef = useRef<string>('');

  // Load conversations from localStorage on mount
  useEffect(() => {
    const savedConversations = localStorage.getItem('chatplg-conversations');
    if (savedConversations) {
      const parsed = JSON.parse(savedConversations);
      setConversations(parsed);
    }
  }, []);

  // Save conversations to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('chatplg-conversations', JSON.stringify(conversations));
  }, [conversations]);

  const createConversation = (): Conversation => {
    const newConversation: Conversation = {
      id: Date.now().toString(),
      title: 'שיחה חדשה',
      lastMessage: '',
      timestamp: new Date().toISOString(),
      messages: []
    };
    
    setConversations(prev => [newConversation, ...prev]);
    return newConversation;
  };

  const updateConversation = (id: string, updates: Partial<Conversation>) => {
    setConversations(prev => prev.map(conv => 
      conv.id === id ? { ...conv, ...updates } : conv
    ));
  };

  const deleteConversation = (id: string) => {
    setConversations(prev => prev.filter(conv => conv.id !== id));
  };

  const getConversation = (id: string): Conversation | null => {
    return conversations.find(conv => conv.id === id) || null;
  };

  const sendMessage = async (conversationId: string, messageContent: string) => {
    setApiError(null);
    
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: messageContent,
      timestamp: new Date().toISOString()
    };

    // Get current conversation before updating
    const currentConversation = conversations.find(conv => conv.id === conversationId);
    
    // Update conversation with user message
    setConversations(prev => prev.map(conv => {
      if (conv.id === conversationId) {
        const isFirstMessage = conv.messages.length === 0;
        return {
          ...conv,
          title: isFirstMessage ? messageContent : conv.title,
          messages: [...conv.messages, userMessage],
          lastMessage: messageContent,
          timestamp: new Date().toISOString()
        };
      }
      return conv;
    }));

    // Start streaming
    setIsLoading(true);
    setStreamingMessage('');
    streamingContentRef.current = '';

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // Build messages array from current conversation state
    const allMessages = currentConversation ? [...currentConversation.messages, userMessage] : [userMessage];

    await streamChatResponse(
      allMessages,
      // onToken callback
      (token: string) => {
        streamingContentRef.current += token;
        setStreamingMessage(streamingContentRef.current);
      },
      // onError callback
      (error: StreamError) => {
        console.error('Streaming error:', error);
        setApiError(error.message);
        setIsLoading(false);
        setStreamingMessage('');
        streamingContentRef.current = '';
        abortControllerRef.current = null;
      },
      // onComplete callback
      () => {
        const finalContent = streamingContentRef.current;
        
        if (finalContent.trim()) {
          const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            type: 'assistant',
            content: finalContent,
            timestamp: new Date().toISOString()
          };

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
        
        setIsLoading(false);
        setStreamingMessage('');
        streamingContentRef.current = '';
        abortControllerRef.current = null;
      },
      abortController
    );
  };

  const retryLastMessage = () => {
    if (apiError) {
      setApiError(null);
    }
  };

  const value: ConversationContextType = {
    conversations,
    isLoading,
    streamingMessage,
    apiError,
    createConversation,
    updateConversation,
    deleteConversation,
    sendMessage,
    getConversation,
    retryLastMessage
  };

  return (
    <ConversationContext.Provider value={value}>
      {children}
    </ConversationContext.Provider>
  );
}; 