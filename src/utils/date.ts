/**
 * Utility functions for date and timestamp formatting
 */

/**
 * Formats timestamp for chat messages display (time only)
 * @param timestamp - ISO timestamp string
 * @returns Formatted time string (HH:MM)
 */
export const formatMessageTimestamp = (timestamp: string): string => {
  return new Date(timestamp).toLocaleTimeString('he-IL', {
    hour: '2-digit',
    minute: '2-digit'
  });
};

/**
 * Formats timestamp for conversation list display (date and time)
 * @param timestamp - ISO timestamp string  
 * @returns Formatted date and time string
 */
export const formatConversationTimestamp = (timestamp: string): string => {
  return new Date(timestamp).toLocaleDateString('he-IL', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

/**
 * Creates a new ISO timestamp string for the current time
 * @returns Current timestamp as ISO string
 */
export const getCurrentTimestamp = (): string => {
  return new Date().toISOString();
}; 