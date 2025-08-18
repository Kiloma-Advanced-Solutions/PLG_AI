/**
 * Simple navigation utilities
 */

import { AppRouterInstance } from 'next/dist/shared/lib/app-router-context.shared-runtime';

/**
 * Navigates to a conversation immediately
 * @param conversationId - ID of the conversation to navigate to
 * @param router - Next.js router instance
 * @param closeSidebar - Optional callback to close sidebar
 */
export const navigateToConversation = (
  conversationId: string,
  router: AppRouterInstance,
  closeSidebar?: () => void
): void => {
  if (closeSidebar) {
    closeSidebar();
  }
  router.push(`/chat/${conversationId}`);
};

/**
 * Navigates to new chat page immediately
 * @param router - Next.js router instance
 * @param closeSidebar - Optional callback to close sidebar
 */
export const navigateToNewChat = (
  router: AppRouterInstance,
  closeSidebar?: () => void
): void => {
  if (closeSidebar) {
    closeSidebar();
  }
  router.push('/chat/new');
}; 