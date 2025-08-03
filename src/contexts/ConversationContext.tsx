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
  retryLastMessage: () => Promise<void>;
  setNavigationLoading: (loading: boolean) => void;
};

/**
 * State for tracking retry information
 */
type RetryState = {
  conversationId: string;
  lastUserMessage: string;
  messagesBeforeError: Message[];
} | null;

/**
 * React context for managing conversation state and operations
 */
const ConversationContext = createContext<ConversationContextType | undefined>(undefined);

/**
 * Hook to access the conversation context
 * Throws an error if used outside of ConversationProvider
 */
export const useConversationContext = () => {
  const context = useContext(ConversationContext);
  if (!context) {
    throw new Error('useConversationContext must be used within a ConversationProvider');
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
  const [isNavigationLoading, setIsNavigationLoading] = useState(true);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [apiError, setApiError] = useState<string | null>(null);
  const [retryState, setRetryState] = useState<RetryState>(null);
  
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
    setRetryState(null); // Clear any previous retry state
    
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

    // Store state for potential retry
    const messagesBeforeRequest = currentConversation ? [...currentConversation.messages, userMessage] : [userMessage];
    
    // Initialize streaming state
    setIsLoading(true);
    setStreamingMessage('');
    streamingContentRef.current = '';

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // Build complete message history for API request
    const allMessages = messagesBeforeRequest;

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
        
        // Store retry information for the failed message
        setRetryState({
          conversationId,
          lastUserMessage: messageContent,
          messagesBeforeError: currentConversation?.messages || []
        });
        
        // If error occurred during streaming, remove any partial assistant response
        setConversations(prev => prev.map(conv => {
          if (conv.id === conversationId) {
            return {
              ...conv,
              messages: currentConversation?.messages || [],
              lastMessage: currentConversation?.messages && currentConversation.messages.length > 0 
                ? currentConversation.messages[currentConversation.messages.length - 1].content 
                : '',
              timestamp: getCurrentTimestamp()
            };
          }
          return conv;
        }));
        
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
        
        // Clean up streaming state and retry info
        setIsLoading(false);
        setStreamingMessage('');
        streamingContentRef.current = '';
        abortControllerRef.current = null;
        setRetryState(null);
      },
      abortController
    );
  };

  /**
   * Retries the last failed message by resending it
   */
  const retryLastMessage = async () => {
    if (!retryState) {
      // If no retry state, just clear the error
      setApiError(null);
      return;
    }

    const { conversationId, lastUserMessage, messagesBeforeError } = retryState;
    
    // Reset conversation to state before the failed message
    setConversations(prev => prev.map(conv => {
      if (conv.id === conversationId) {
        return {
          ...conv,
          messages: messagesBeforeError,
          lastMessage: messagesBeforeError.length > 0 
            ? messagesBeforeError[messagesBeforeError.length - 1].content 
            : '',
          timestamp: getCurrentTimestamp()
        };
      }
      return conv;
    }));

    // Clear error state
    setApiError(null);
    
    // Resend the message
    await sendMessage(conversationId, lastUserMessage);
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