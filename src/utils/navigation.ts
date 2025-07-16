/**
 * Navigation utilities for smooth transitions
 */

/**
 * Standard delay used for navigation transitions to allow animations to complete
 */
const NAVIGATION_DELAY = 10;

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
 * @param currentPath - Current pathname to check if already on new chat page
 * @param onBeforeNavigate - Optional callback to execute before navigation (e.g., close sidebar)
 * @param onNewChatClick - Optional callback for custom new chat handling (e.g., animations)
 */
export const navigateToNewChat = (
  router: any,
  currentPath: string,
  onBeforeNavigate?: () => void,
  onNewChatClick?: () => void
): void => {
  if (onBeforeNavigate) {
    onBeforeNavigate();
  }
  
  setTimeout(() => {
    // If already on new chat page, just trigger the callback without redirecting
    if (currentPath === '/chat/new' && onNewChatClick) {
      onNewChatClick();
    } else {
      // Navigate to new chat page
      if (onNewChatClick) {
        onNewChatClick();
      }
      router.push('/chat/new');
    }
  }, NAVIGATION_DELAY);
}; 