/**
 * Simple navigation utilities
 */

import { AppRouterInstance } from 'next/dist/shared/lib/app-router-context.shared-runtime';

/**
 * Navigates to a conversation with sidebar closing animation
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
    // Wait for sidebar close animation to complete (0.3s transition)
    setTimeout(() => {
      router.push(`/chat/${conversationId}`);
    }, 300);
  } else {
    router.push(`/chat/${conversationId}`);
  }
};

/**
 * Navigates to new chat page with sidebar closing animation
 * @param router - Next.js router instance
 * @param closeSidebar - Optional callback to close sidebar
 */
export const navigateToNewChat = (
  router: AppRouterInstance,
  closeSidebar?: () => void
): void => {
  if (closeSidebar) {
    closeSidebar();
    // Wait for sidebar close animation to complete (0.3s transition)
    setTimeout(() => {
      router.push('/chat/new');
    }, 300);
  } else {
    router.push('/chat/new');
  }
}; 