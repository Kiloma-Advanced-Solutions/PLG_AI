import { Conversation } from '../types';

/**
 * Utility functions for conversation operations
 */

/**
 * Filters conversations that have messages (for sidebar display)
 * @param conversations - Array of all conversations
 * @returns Array of conversations with messages
 */
export const getConversationsWithMessages = (conversations: Conversation[]): Conversation[] => {
  return conversations.filter(conv => conv.messages.length > 0);
};

/**
 * Generates a unique conversation ID
 * @returns Unique ID string based on current timestamp
 */
export const generateConversationId = (): string => {
  return Date.now().toString();
};

/**
 * Generates a unique message ID
 * @param offset - Optional offset to ensure uniqueness when creating multiple IDs quickly
 * @returns Unique ID string
 */
export const generateMessageId = (offset: number = 0): string => {
  return (Date.now() + offset).toString();
}; 