'use client';

import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { Message, Conversation } from '../types';
import { streamChatResponse, generateConversationTitle } from '../utils/streaming-api';
import { AppError } from '../utils/error-handling';
import { generateConversationId, generateMessageId } from '../utils/conversation';
import { getCurrentTimestamp } from '../utils/date';

/**
 * Type definition for the conversation context
 */
type ConversationContextType = {
  conversations: Conversation[];
  isStreaming: boolean;
  isNavigationLoading: boolean;
  streamingMessage: string;
  apiError: string | null;
  createConversation: (firstMessage?: string) => Conversation;
  sendMessage: (conversationId: string, message: string) => Promise<void>;
  getConversation: (id: string) => Conversation | null;
  updateConversationTitle: (conversationId: string, title: string) => void;
  editMessage: (conversationId: string, messageId: string, newContent: string) => Promise<void>;
  retryLastMessage: () => Promise<void>;
  stopStreaming: () => string | null;
  createStopHandler: (setPrefilledMessage: (message: string) => void, onAdditionalCleanup?: () => void) => (currentInputValue: string) => void;
  createMessageEditHandler: (conversationId: string | null) => (messageId: string, newContent: string) => Promise<void>;
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


  const [isStreaming, setIsStreaming] = useState(false);
  const [isNavigationLoading, setIsNavigationLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [apiError, setApiError] = useState<string | null>(null);
  const [retryState, setRetryState] = useState<RetryState>(null);
  
  // === REFS FOR STREAMING STATE MANAGEMENT ===
  const abortControllerRef = useRef<AbortController | null>(null);
  const streamingContentRef = useRef<string>('');
  const lastUserMessageRef = useRef<string | null>(null);
  const currentConversationIdRef = useRef<string | null>(null);

  // === HELPER FUNCTIONS FOR STREAMING OPERATIONS ===
  
  /**
   * Helper function to initialize streaming state
   */
  const initializeStreaming = (conversationId: string, userMessage: string): AbortController => {
    setIsStreaming(true);
    setStreamingMessage('');
    streamingContentRef.current = '';
    setApiError(null);
    
    lastUserMessageRef.current = userMessage;
    currentConversationIdRef.current = conversationId;
    
    const abortController = new AbortController();
    abortControllerRef.current = abortController;
    
    return abortController;
  };

  /**
   * Helper function to clean up streaming state
   */
  const cleanupStreaming = () => {
    setIsStreaming(false);
    setStreamingMessage('');
    streamingContentRef.current = '';
    abortControllerRef.current = null;
    lastUserMessageRef.current = null;
    currentConversationIdRef.current = null;
  };

  /**
   * Helper function to revert conversation by removing the last user message
   */
  const revertConversation = (conversationId: string) => {
    setConversations(prev => 
      prev.map(conv => {
        // If the conversation ID is not the same as the one we want to revert, return the conversation as is
        if (conv.id !== conversationId) return conv;
        
        // Remove the last message (the user message we just added)
        const updatedMessages = conv.messages.slice(0, -1);
        
        // If conversation becomes empty, mark for deletion
        if (updatedMessages.length === 0) return null;
        
        // Update conversation with remaining messages
        const lastMessage = updatedMessages[updatedMessages.length - 1];
        return {
          ...conv,
          messages: updatedMessages,
          lastMessage: lastMessage.content,
          timestamp: getCurrentTimestamp()
        };
      })
      .filter((conv): conv is Conversation => conv !== null) // Remove empty conversations
    );
  };

  /**
   * Helper function to update conversation title
   */
  const updateConversationTitle = (conversationId: string, title: string) => {
    setConversations(prev => prev.map(conv => {
      if (conv.id === conversationId) {
        return {
          ...conv,
          title: title,
          timestamp: getCurrentTimestamp()
        };
      }
      return conv;
    }));
  };

  /**
   * Helper function to add a message to conversation
   * @param conversationId - ID of the conversation to add message to
   * @param content - Content of the message
   * @param type - Type of message ('user' or 'assistant')
   * @returns The created message (useful for user messages that need to be referenced)
   */
  const addMessage = (
    conversationId: string, 
    content: string, 
    type: 'user' | 'assistant'
  ): Message => {
    const message: Message = {
      id: generateMessageId(type === 'assistant' ? 1 : 0),
      type,
      content,
      timestamp: getCurrentTimestamp()
    };

    setConversations(prev => prev.map(conv => {
      if (conv.id === conversationId) {
        return {
          ...conv,
          messages: [...conv.messages, message],
          lastMessage: content,
          timestamp: getCurrentTimestamp()
        };
      }
      return conv;
    }));

    return message;
  };

  /**
   * Helper function to handle streaming chat response
   * @param conversationId - ID of the conversation
   * @param messages - Messages to send to AI
   * @param userMessage - The user message content (for retry state)
   * @param isRetry - Whether this is a retry attempt
   */
  const handleStreamingResponse = async (
    conversationId: string,
    messages: Message[],
    userMessage: string,
    isRetry: boolean = false
  ) => {
    const abortController = initializeStreaming(conversationId, userMessage);

    await streamChatResponse(
      messages,
      // Token callback
      (token: string) => {
        streamingContentRef.current += token;
        setStreamingMessage(streamingContentRef.current);
      },
      // Error callback
      (error: AppError) => {
        console.error(isRetry ? '❌ Retry streaming error:' : '❌ Streaming error:', {
          error,
          type: error?.type,
          message: error?.message,
          retryable: error?.retryable
        });
        
        if (!isRetry) {
          // Store retry information for new messages
          const currentConversation = conversations.find(conv => conv.id === conversationId);
          setRetryState({
            conversationId,
            lastUserMessage: userMessage,
            messagesBeforeError: currentConversation?.messages || []
          });
        }
        // For retries, keep existing retryState for future retry attempts
        
        setApiError(error.message);
        cleanupStreaming();
      },
      // Complete callback
      () => {
        if (streamingContentRef.current.trim()) {
          addMessage(conversationId, streamingContentRef.current, 'assistant');
        }
        cleanupStreaming();
        setRetryState(null);
      },
      abortController
    );
  };

  // Persist conversations to localStorage whenever they change
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('chatplg-conversations', JSON.stringify(conversations));
    }
  }, [conversations]);



  // === CONVERSATION CRUD OPERATIONS ===
  
  /**
   * Creates a new conversation with default values
   */
  const createConversation = (firstMessage?: string): Conversation => {
    const newConversation: Conversation = {
      id: generateConversationId(),
      title: 'שיחה חדשה',
      lastMessage: '',
      timestamp: getCurrentTimestamp(),
      messages: []
    };
    
    setConversations(prev => [newConversation, ...prev]);
    
    // Generate title for first message (don't await, let it run in background)
    if (firstMessage) {
      generateConversationTitle(firstMessage)
        .then((title: string) => {
          updateConversationTitle(newConversation.id, title);
        })
        .catch((error: unknown) => {
          console.warn('Failed to generate conversation title:', error);
          // Keep the default title if generation fails
        });
    }
    
    return newConversation;
  };

  /**
   * Retrieves a conversation by ID
   */
  const getConversation = (id: string): Conversation | null => {
    return conversations.find(conv => conv.id === id) || null;
  };

  // === MESSAGE SENDING AND STREAMING OPERATIONS ===
  
  /**
   * Sends a user message and streams the AI response
   */
  const sendMessage = async (conversationId: string, messageContent: string) => {
    setRetryState(null); // Clear any previous retry state
    
    const currentConversation = conversations.find(conv => conv.id === conversationId);
    
    // Add user message to conversation
    const userMessage = addMessage(conversationId, messageContent, 'user');
    
    // Build message history for API request
    const messagesForRequest = currentConversation ? [...currentConversation.messages, userMessage] : [userMessage];
    
    // Handle streaming response
    await handleStreamingResponse(conversationId, messagesForRequest, messageContent, false);
  };

  /**
   * Edits a message and clears the conversation from that point
   */
  const editMessage = async (conversationId: string, messageId: string, newContent: string) => {
    setRetryState(null); // Clear any previous retry state
    
    const currentConversation = conversations.find(conv => conv.id === conversationId);
    if (!currentConversation) return;

    // Find the message to edit
    const messageIndex = currentConversation.messages.findIndex(msg => msg.id === messageId);
    if (messageIndex === -1) return;

    const messageToEdit = currentConversation.messages[messageIndex];
    if (messageToEdit.type !== 'user') return; // Only allow editing user messages

    // Create updated message
    const updatedMessage = {
      ...messageToEdit,
      content: newContent,
      timestamp: getCurrentTimestamp()
    };

    // Create messages array up to and including the edited message
    const newConversationMessages = [
      ...currentConversation.messages.slice(0, messageIndex),
      updatedMessage
    ];

    // Update conversation state in one go
    setConversations(prev => prev.map(conv => {
      if (conv.id !== conversationId) return conv;
      
      return {
        ...conv,
        messages: newConversationMessages,
        lastMessage: newContent,
        timestamp: getCurrentTimestamp()
      };
    }));

    // Send the edited message to get new AI response
    await handleStreamingResponse(conversationId, newConversationMessages, newContent, false);
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
    const currentConversation = conversations.find(conv => conv.id === conversationId);
    
    if (!currentConversation) return;

    // Handle streaming response for retry
    await handleStreamingResponse(conversationId, currentConversation.messages, lastUserMessage, true);
  };

  /**
   * Stops the current streaming response and reverts the conversation state
   * Returns the last user message content for restoration to input
   */
  const stopStreaming = (): string | null => {
    // Capture state before cleanup
    const userMessageToRestore = lastUserMessageRef.current;
    const conversationId = currentConversationIdRef.current;

    // Abort ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Clear all state and UI
    cleanupStreaming();
    setApiError(null);
    setRetryState(null);

    // Revert conversation if we have the necessary data
    if (conversationId && userMessageToRestore) {
      revertConversation(conversationId);
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

  /**
   * Creates a standardized message edit handler for pages
   */
  const createMessageEditHandler = (conversationId: string | null) => 
    async (messageId: string, newContent: string) => {
      if (conversationId) {
        await editMessage(conversationId, messageId, newContent);
      }
    };

  // === CONTEXT VALUE ASSEMBLY ===
  
  const value: ConversationContextType = {
    conversations,         // Array of all conversations
    isStreaming,           // Boolean: Is AI currently responding?
    isNavigationLoading,   // Boolean: Is page navigation happening?
    streamingMessage,      // String: Current AI response being typed
    apiError,              // String | null: Any error messages
    createConversation,    // (firstMessage?) => Creates new conversation
    sendMessage,           // (id, message) => Sends message and streams response
    getConversation,       // (id) => Retrieves specific conversation
    updateConversationTitle, // (id, title) => Updates conversation title
    editMessage,           // (id, messageId, newContent) => Edits message and clears conversation
    retryLastMessage,      // () => Retries failed message
    stopStreaming,         // () => Stops AI response, returns user message
    createStopHandler,     // Factory for creating stop handlers
    createMessageEditHandler, // Factory for creating message edit handlers
    setNavigationLoading: setIsNavigationLoading,  // (boolean) => Sets navigation loading state
  };

  return (
    // Provides the context value to all components within the ConversationProvider
    <ConversationContext.Provider value={value}>
      {children}
    </ConversationContext.Provider>
  );
}; 