'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useConversations } from '../contexts/ConversationContext';

export default function Home() {
  const router = useRouter();
  const { conversations } = useConversations();

  useEffect(() => {
    // Check if there's a recent conversation with messages
    const recentConversation = conversations.find(conv => conv.messages.length > 0);
    
    if (recentConversation) {
      // Redirect to the most recent conversation
      router.push(`/chat/${recentConversation.id}`);
    } else {
      // No conversations or all are empty, redirect to new chat
      router.push('/chat/new');
    }
  }, [conversations, router]);

  // Show loading while redirecting
  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      height: '100vh',
      direction: 'rtl' 
    }}>
      <p>טוען...</p>
    </div>
  );
}
