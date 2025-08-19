import { redirect } from 'next/navigation';

/**
 * Main entry point component for the application
 * Immediately redirects users to the new chat page using server-side redirect
 */
export default function Home() {
  // Server-side redirect - happens before any rendering
  redirect('/chat/new');
}
