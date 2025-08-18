import { useRouter, usePathname } from 'next/navigation';
import { useConversationContext } from '../contexts/ConversationContext';
import { navigateToConversation, navigateToNewChat } from '../utils/navigation';

  /**
   * Custom hook for navigation utilities with consistent behavior
   * Provides centralized navigation logic with proper delays and callbacks
   */
  export const useNavigationHelpers = () => {
  const router = useRouter();
  const pathname = usePathname();
  const { setNavigationLoading, stopStreaming } = useConversationContext();
    
    /**
     * Navigate to a specific conversation with optional sidebar closing
     */
    const goToConversation = (
      conversationId: string, 
      closeSidebar?: () => void
    ) => {
      // Stop any ongoing streaming before navigation
      stopStreaming();
      
      // Start loading immediately
      setNavigationLoading(true);
      navigateToConversation(conversationId, router, closeSidebar);
    };
    
    /**
     * Navigate to new chat page with optional sidebar closing and custom callback
     */
    const goToNewChat = (
      closeSidebar?: () => void,
      onNewChatClick?: () => void
    ) => {
      // Always stop any ongoing streaming first
      stopStreaming();
      
      // If we're already on the new chat page, just close sidebar and trigger animation
      if (pathname === '/chat/new') {
        if (closeSidebar) {
          closeSidebar();
        }
        // Call onNewChatClick to trigger input focus animation
        if (onNewChatClick) {
          onNewChatClick();
        }
        return;
      }
      
      // For actual navigation to a different page
      setNavigationLoading(true);
      navigateToNewChat(router, pathname, closeSidebar, onNewChatClick);
    };
    
    return {
      goToConversation,
      goToNewChat,
    };
  }; 