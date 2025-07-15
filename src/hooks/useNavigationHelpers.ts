import { useRouter } from 'next/navigation';
import { navigateToConversation, navigateToNewChat } from '../utils/navigation';

/**
 * Custom hook for navigation utilities with consistent behavior
 * Provides centralized navigation logic with proper delays and callbacks
 */
export const useNavigationHelpers = () => {
  const router = useRouter();
  
  /**
   * Navigate to a specific conversation with optional sidebar closing
   */
  const goToConversation = (
    conversationId: string, 
    closeSidebar?: () => void
  ) => {
    navigateToConversation(conversationId, router, closeSidebar);
  };
  
  /**
   * Navigate to new chat page with optional sidebar closing and custom callback
   */
  const goToNewChat = (
    closeSidebar?: () => void,
    onNewChatClick?: () => void
  ) => {
    navigateToNewChat(router, closeSidebar, onNewChatClick);
  };
  
  return {
    goToConversation,
    goToNewChat,
  };
}; 