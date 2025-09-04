'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

/**
 * Type definition for the theme context
 */
type ThemeContextType = {
  /** Whether dark mode is currently active */
  isDark: boolean;
  /** Function to toggle between light and dark themes */
  toggleTheme: () => void;
};

/**
 * React context for managing theme state
 */
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

/**
 * Theme provider component that manages light/dark mode state
 * Persists theme preference in localStorage and applies CSS classes
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  const [isDark, setIsDark] = useState(false);

  // Initialize theme from localStorage on component mount
  useEffect(() => {
    // Check for saved theme preference, default to light mode
    const savedTheme = localStorage.getItem('chatplg-theme');
    const isInitiallyDark = savedTheme === 'dark';
    
    setIsDark(isInitiallyDark);
    document.documentElement.classList.toggle('dark', isInitiallyDark);
  }, []);

  /**
   * Toggles between light and dark themes
   * Updates state, localStorage, and document class
   */
  const toggleTheme = () => {
    const newIsDark = !isDark;
    setIsDark(newIsDark);
    
    document.documentElement.classList.toggle('dark', newIsDark);
    localStorage.setItem('chatplg-theme', newIsDark ? 'dark' : 'light');
  };

  return (
    <ThemeContext.Provider value={{ isDark, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

/**
 * Hook to access the theme context
 * Throws an error if used outside of ThemeProvider
 */
export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
} 