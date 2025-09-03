import { useState, useEffect } from 'react';

/**
 * Initialize sidebar open state from localStorage
 */
export const useSidebar = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('sidebar-open');
      return saved === 'true';
    }
    return false;
  });

  /**
   * Auto-save to localStorage whenever state changes
   */
  useEffect(() => {
    localStorage.setItem('sidebar-open', isSidebarOpen.toString());
  }, [isSidebarOpen]);

  /**
   * Toggle sidebar open state
   */
  const toggleSidebar = () => setIsSidebarOpen(prev => !prev);

  return { isSidebarOpen, toggleSidebar };
};
