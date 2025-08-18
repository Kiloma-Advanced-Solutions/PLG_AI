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
  stopStreaming: () => string | null;
  createStopHandler: (setPrefilledMessage: (message: string) => void, onAdditionalCleanup?: () => void) => (currentInputValue: string) => void;
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
  // Initialize conversations from localStorage immediately (client-side only)
  const [conversations, setConversations] = useState<Conversation[]>(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('chatplg-conversations');
        return saved ? JSON.parse(saved) : [];
      } catch {
        return [];
      }
    }
    return [];
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [isNavigationLoading, setIsNavigationLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [apiError, setApiError] = useState<string | null>(null);
  const [retryState, setRetryState] = useState<RetryState>(null);
  
  // Refs for managing streaming state
  const abortControllerRef = useRef<AbortController | null>(null);
  const streamingContentRef = useRef<string>('');
  const lastUserMessageRef = useRef<string | null>(null);
  const currentConversationIdRef = useRef<string | null>(null);

  // Persist conversations to localStorage whenever they change
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('chatplg-conversations', JSON.stringify(conversations));
    }
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
    
    // Store the user message and conversation ID for potential stop/revert
    lastUserMessageRef.current = messageContent;
    currentConversationIdRef.current = conversationId;
    
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

    // Creates a new AbortController instance - a Web API that can cancel network request
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
        
        // If error occurred during streaming, keep user message but remove any partial assistant response
        setConversations(prev => prev.map(conv => {
          if (conv.id === conversationId) {
            const messagesWithUser = currentConversation ? [...currentConversation.messages, userMessage] : [userMessage];
            return {
              ...conv,
              messages: messagesWithUser,
              lastMessage: userMessage.content,
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
        lastUserMessageRef.current = null;
        currentConversationIdRef.current = null;
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

    const { conversationId, lastUserMessage } = retryState;
    
    // Clear error state but keep conversation as is (with user message)
    setApiError(null);
    
    // Get current conversation with user message already included
    const currentConversation = conversations.find(conv => conv.id === conversationId);
    if (!currentConversation) return;

    // Initialize streaming state
    setIsLoading(true);
    setStreamingMessage('');
    streamingContentRef.current = '';

    // Create new AbortController for retry
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // Store references for potential stop/revert
    lastUserMessageRef.current = lastUserMessage;
    currentConversationIdRef.current = conversationId;

    // Retry streaming with existing messages (user message already in conversation)
    await streamChatResponse(
      currentConversation.messages,
      // Token callback
      (token: string) => {
        streamingContentRef.current += token;
        setStreamingMessage(streamingContentRef.current);
      },
      // Error callback
      (error: StreamError) => {
        console.error('❌ Retry streaming error:', error);
        setApiError(error.message);
        setIsLoading(false);
        setStreamingMessage('');
        streamingContentRef.current = '';
        abortControllerRef.current = null;
      },
      // Complete callback
      () => {
        if (streamingContentRef.current) {
          const assistantMessage: Message = {
            id: generateMessageId(),
            type: 'assistant',
            content: streamingContentRef.current,
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
   * Stops the current streaming response and reverts the conversation state
   * Returns the last user message content for restoration to input
   */
  const stopStreaming = (): string | null => {
    // Get the user message to restore before we clear refs
    const userMessageToRestore = lastUserMessageRef.current;
    const conversationId = currentConversationIdRef.current;

    // Clear UI state
    setIsLoading(false);
    setStreamingMessage('');
    streamingContentRef.current = '';
    setApiError(null);
    setRetryState(null);

    // Abort the current streaming request after clearing state
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    // Clear refs after abort to prevent any callback issues
    lastUserMessageRef.current = null;
    currentConversationIdRef.current = null;

    if (conversationId && userMessageToRestore) {
      // Revert the conversation state - remove the last user message
      setConversations(prev => {
        const updatedConversations = prev.map(conv => {
          if (conv.id === conversationId) {
            // Remove the last message (which should be the user message we just added)
            const updatedMessages = conv.messages.slice(0, -1);
            
            // If conversation becomes empty after removing message, mark for deletion
            if (updatedMessages.length === 0) {
              return null; // Will be filtered out
            }
            
            return {
              ...conv,
              messages: updatedMessages,
              lastMessage: updatedMessages.length > 0 
                ? updatedMessages[updatedMessages.length - 1].content 
                : '',
              timestamp: getCurrentTimestamp()
            };
          }
          return conv;
        }).filter((conv): conv is Conversation => conv !== null); // Remove null conversations (empty ones)
        
        return updatedConversations;
      });
    }

    return userMessageToRestore;
  };

  /**
   * Creates a standardized stop handler for pages
   */
  const createStopHandler = (
    setPrefilledMessage: (message: string) => void,
    onAdditionalCleanup?: () => void
  ) => (currentInputValue: string) => {
    // Call any additional cleanup first
    if (onAdditionalCleanup) {
      onAdditionalCleanup();
    }
    
    // Stop streaming and get restored message
    const restoredMessage = stopStreaming();
    
    // Only set prefilled message if input is empty
    if (restoredMessage && (!currentInputValue || currentInputValue.trim() === '')) {
      setPrefilledMessage(restoredMessage);
    }
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
    stopStreaming,
    createStopHandler,
    setNavigationLoading: setIsNavigationLoading,
  };

  return (
    <ConversationContext.Provider value={value}>
      {children}
    </ConversationContext.Provider>
  );
}; 