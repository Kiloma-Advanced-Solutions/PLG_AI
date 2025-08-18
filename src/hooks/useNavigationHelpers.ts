import { useRouter, usePathname } from 'next/navigation';
import { useConversationContext } from '../contexts/ConversationContext';
import { navigateToConversation, navigateToNewChat } from '../utils/navigation';

/**
 * Custom hook for navigation utilities with consistent behavior
 */
export const useNavigationHelpers = () => {
  const router = useRouter();
  const pathname = usePathname();
  const { setNavigationLoading, stopStreaming } = useConversationContext();
    
  /**
   * Navigate to a specific conversation with sidebar closing
   */
  const goToConversation = (
    conversationId: string, 
    closeSidebar?: () => void
  ) => {
    stopStreaming();
    setNavigationLoading(true);
    navigateToConversation(conversationId, router, closeSidebar);
  };
  
  /**
   * Navigate to new chat page with sidebar closing and animation
   */
  const goToNewChat = (
    closeSidebar?: () => void,
    onNewChatClick?: () => void
  ) => {
    stopStreaming();
    
    // If already on new chat page, just close sidebar and trigger animation
    if (pathname === '/chat/new') {
      if (closeSidebar) closeSidebar();
      if (onNewChatClick) onNewChatClick();
      return;
    }
    
    // Navigate to new chat page
    setNavigationLoading(true);
    navigateToNewChat(router, closeSidebar);
  };
  
  return {
    goToConversation,
    goToNewChat,
  };
}; 