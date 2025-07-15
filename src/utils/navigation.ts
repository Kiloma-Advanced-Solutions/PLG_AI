/**
 * Navigation utilities for smooth transitions
 */

/**
 * Standard delay used for navigation transitions to allow animations to complete
 */
const NAVIGATION_DELAY = 150;

/**
 * Navigates to a conversation with a delay to allow UI transitions
 * @param conversationId - ID of the conversation to navigate to
 * @param router - Next.js router instance
 * @param onBeforeNavigate - Optional callback to execute before navigation (e.g., close sidebar)
 */
export const navigateToConversation = (
  conversationId: string,
  router: any,
  onBeforeNavigate?: () => void
): void => {
  if (onBeforeNavigate) {
    onBeforeNavigate();
  }
  
  setTimeout(() => {
    router.push(`/chat/${conversationId}`);
  }, NAVIGATION_DELAY);
};

/**
 * Navigates to new chat page with a delay to allow UI transitions
 * @param router - Next.js router instance
 * @param onBeforeNavigate - Optional callback to execute before navigation (e.g., close sidebar)
 * @param onNewChatClick - Optional callback for custom new chat handling (e.g., animations)
 */
export const navigateToNewChat = (
  router: any,
  onBeforeNavigate?: () => void,
  onNewChatClick?: () => void
): void => {
  if (onBeforeNavigate) {
    onBeforeNavigate();
  }
  
  setTimeout(() => {
    if (onNewChatClick) {
      onNewChatClick();
    } else {
      router.push('/chat/new');
    }
  }, NAVIGATION_DELAY);
}; 