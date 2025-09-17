import { useRouter, usePathname } from 'next/navigation';
import { useConversationContext } from '../contexts/ConversationContext';

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
    toggleSidebar?: () => void
  ) => {
    stopStreaming();
    
    // If already on the target conversation page, just close sidebar
    if (pathname === `/chat/${conversationId}`) {
      if (toggleSidebar) toggleSidebar();
      return;
    }
    
    // Navigate to conversation page
    setNavigationLoading(true);
    
    // Close sidebar if toggle function is provided (mobile devices)
    if (toggleSidebar) {
      toggleSidebar();
      // Add small delay to allow sidebar close animation before navigation
      setTimeout(() => router.push(`/chat/${conversationId}`), 150);
    } else {
      router.push(`/chat/${conversationId}`);
    }
  };
  
  /**
   * Navigate to new chat page with sidebar closing and animation
   */
  const goToNewChat = (toggleSidebar?: () => void) => {
    stopStreaming();
    
    // If already on new chat page, close sidebar and trigger animation
    if (pathname === '/chat/new') {
      toggleSidebar?.();
      window.dispatchEvent(new CustomEvent('triggerInputAnimation'));
      return;
    }
    
    // Navigate to new chat page
    setNavigationLoading(true);
    if (toggleSidebar) {
      toggleSidebar();
      setTimeout(() => router.push('/chat/new'), 300);
    } else {
      router.push('/chat/new');
    }
  };
  
  return {
    goToConversation,
    goToNewChat,
  };
}; 