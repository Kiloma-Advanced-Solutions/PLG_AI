/**
 * Core type definitions for the ChatPLG application
 * This file contains the main data structures used throughout the app
 */

/**
 * Represents a single message in a conversation
 */
export type Message = {
  /** Unique identifier for the message */
  id: string;
  /** Type of message sender - either user input or AI assistant response */
  type: 'user' | 'assistant';
  /** The actual message content/text */
  content: string;
  /** ISO timestamp string indicating when the message was created */
  timestamp: string;
};

/**
 * Represents a complete conversation containing multiple messages
 */
export type Conversation = {
  /** Unique identifier for the conversation */
  id: string;
  /** Display title for the conversation (usually first user message) */
  title: string;
  /** Preview text showing the last message content */
  lastMessage: string;
  /** ISO timestamp string of the conversation's last update */
  timestamp: string;
  /** Array of all messages in this conversation */
  messages: Message[];
}; 