'use client';

import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { Message, Conversation } from '../types';
import { streamChatResponse, StreamError } from '../utils/streaming-api';
import { generateConversationId, generateMessageId } from '../utils/conversation';
import { getCurrentTimestamp } from '../utils/date';

/**
 * Type definition for the conversation context
 */
type ConversationContextType = {
  conversations: Conversation[];
  isLoading: boolean;
  isNavigationLoading: boolean;
  streamingMessage: string;
  apiError: string | null;
  createConversation: () => Conversation;
  updateConversation: (id: string, updates: Partial<Conversation>) => void;
  deleteConversation: (id: string) => void;
  sendMessage: (conversationId: string, message: string) => Promise<void>;
  getConversation: (id: string) => Conversation | null;
  retryLastMessage: () => void;
  setNavigationLoading: (loading: boolean) => void;
};

/**
 * React context for managing conversation state and operations
 */
const ConversationContext = createContext<ConversationContextType | undefined>(undefined);

/**
 * Hook to access the conversation context
 * Throws an error if used outside of ConversationProvider
 */
export const useConversations = () => {
  const context = useContext(ConversationContext);
  if (!context) {
    throw new Error('useConversations must be used within a ConversationProvider');
  }
  return context;
};

/**
 * Provider component for conversation context
 * Manages all conversation state, localStorage persistence, and API communication
 */
export const ConversationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isNavigationLoading, setIsNavigationLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [apiError, setApiError] = useState<string | null>(null);
  
  // Refs for managing streaming state
  const abortControllerRef = useRef<AbortController | null>(null);
  const streamingContentRef = useRef<string>('');

  // Load conversations from localStorage on component mount
  useEffect(() => {
    const savedConversations = localStorage.getItem('chatplg-conversations');
    if (savedConversations) {
      setConversations(JSON.parse(savedConversations));
    }
  }, []);

  // Persist conversations to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('chatplg-conversations', JSON.stringify(conversations));
  }, [conversations]);

  /**
   * Creates a new conversation with default values
   */
  const createConversation = (): Conversation => {
    const newConversation: Conversation = {
      id: generateConversationId(),
      title: 'שיחה חדשה',
      lastMessage: '',
      timestamp: getCurrentTimestamp(),
      messages: []
    };
    
    setConversations(prev => [newConversation, ...prev]);
    return newConversation;
  };

  /**
   * Updates an existing conversation with partial data
   */
  const updateConversation = (id: string, updates: Partial<Conversation>) => {
    setConversations(prev => prev.map(conv => 
      conv.id === id ? { ...conv, ...updates } : conv
    ));
  };

  /**
   * Deletes a conversation by ID
   */
  const deleteConversation = (id: string) => {
    setConversations(prev => prev.filter(conv => conv.id !== id));
  };

  /**
   * Retrieves a conversation by ID
   */
  const getConversation = (id: string): Conversation | null => {
    return conversations.find(conv => conv.id === id) || null;
  };

  /**
   * Sends a message and streams the AI response
   */
  const sendMessage = async (conversationId: string, messageContent: string) => {
    setApiError(null);
    
    const userMessage: Message = {
      id: generateMessageId(),
      type: 'user',
      content: messageContent,
      timestamp: getCurrentTimestamp()
    };

    const currentConversation = conversations.find(conv => conv.id === conversationId);
    
    // Update conversation with user message
    setConversations(prev => prev.map(conv => {
      if (conv.id === conversationId) {
        return {
          ...conv,
          title: conv.messages.length === 0 ? messageContent : conv.title,
          messages: [...conv.messages, userMessage],
          lastMessage: messageContent,
          timestamp: getCurrentTimestamp()
        };
      }
      return conv;
    }));

    // Initialize streaming state
    setIsLoading(true);
    setStreamingMessage('');
    streamingContentRef.current = '';

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // Build complete message history for API request
    const allMessages = currentConversation ? [...currentConversation.messages, userMessage] : [userMessage];

    await streamChatResponse(
      allMessages,
      // Token callback - called for each streamed token
      (token: string) => {
        streamingContentRef.current += token;
        setStreamingMessage(streamingContentRef.current);
      },
      // Error callback - called when streaming fails
      (error: StreamError) => {
        console.error('❌ Streaming error:', error);
        setApiError(error.message);
        setIsLoading(false);
        setStreamingMessage('');
        streamingContentRef.current = '';
        abortControllerRef.current = null;
      },
      // Complete callback - called when streaming finishes successfully
      () => {
        const finalContent = streamingContentRef.current;
        
        if (finalContent.trim()) {
          const assistantMessage: Message = {
            id: generateMessageId(1), // Add offset to ensure unique ID
            type: 'assistant',
            content: finalContent,
            timestamp: getCurrentTimestamp()
          };

          setConversations(prev => prev.map(conv => {
            if (conv.id === conversationId) {
              return {
                ...conv,
                messages: [...conv.messages, assistantMessage],
                lastMessage: assistantMessage.content,
                timestamp: getCurrentTimestamp()
              };
            }
            return conv;
          }));
        }
        
        // Clean up streaming state
        setIsLoading(false);
        setStreamingMessage('');
        streamingContentRef.current = '';
        abortControllerRef.current = null;
      },
      abortController
    );
  };

  /**
   * Clears API error state (used for retry functionality)
   */
  const retryLastMessage = () => {
    setApiError(null);
  };

  const value: ConversationContextType = {
    conversations,
    isLoading,
    isNavigationLoading,
    streamingMessage,
    apiError,
    createConversation,
    updateConversation,
    deleteConversation,
    sendMessage,
    getConversation,
    retryLastMessage,
    setNavigationLoading: setIsNavigationLoading,
  };

  return (
    <ConversationContext.Provider value={value}>
      {children}
    </ConversationContext.Provider>
  );
}; 