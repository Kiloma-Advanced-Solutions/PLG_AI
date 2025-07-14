'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Always redirect to new chat page
    router.push('/chat/new');
  }, [router]);

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
