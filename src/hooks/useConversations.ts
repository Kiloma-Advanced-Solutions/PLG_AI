import { useMemo } from 'react';
import { useConversationContext } from '../contexts/ConversationContext';
import { getConversationsWithMessages } from '../utils/conversation';

/**
 * Custom hook that provides conversation utilities and filtered data
 * This abstracts common conversation operations and reduces component complexity
 */
export const useConversationHelpers = () => {
  const context = useConversationContext();
  
  /**
   * Memoized list of conversations that have messages (for sidebar display)
   */
  const conversationsWithMessages = useMemo(() => {
    return getConversationsWithMessages(context.conversations);
  }, [context.conversations]);
  
  /**
   * Checks if a conversation exists
   */
  const conversationExists = (id: string): boolean => {
    return context.conversations.some(conv => conv.id === id);
  };
  
  /**
   * Gets a conversation by ID with null check
   */
  const getConversationSafely = (id: string) => {
    return context.getConversation(id);
  };
  
  return {
    ...context,
    conversationsWithMessages,
    conversationExists,
    getConversationSafely,
  };
}; 