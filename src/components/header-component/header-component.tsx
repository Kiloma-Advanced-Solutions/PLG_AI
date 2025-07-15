'use client';

import ThemeToggleComponent from '../theme-toggle-component/theme-toggle-component';
import { useNavigationHelpers } from '../../hooks/useNavigationHelpers';
import styles from './header-component.module.css';

/**
 * Props for the HeaderComponent
 */
type HeaderComponentProps = {
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
  onNewChatClick?: () => void;
};

/**
 * Header component that displays app branding and navigation controls
 */
export default function HeaderComponent({ 
  isSidebarOpen, 
  onToggleSidebar, 
  onNewChatClick 
}: HeaderComponentProps) {
  const { goToNewChat } = useNavigationHelpers();
  
  /**
   * Handles new chat creation from header click
   */
  const handleCreateNewChat = () => {
    goToNewChat(undefined, onNewChatClick);
  };
  
  return (
    <header className={`${styles.header} ${isSidebarOpen ? styles.shifted : ''}`}>
      <div className={styles.leftSection}>
        <ThemeToggleComponent />
        
        <div className={styles.logo}>
          <svg className={styles.logoIcon} viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
        </div>
      </div>
      
      <div className={`${styles.appName} ${isSidebarOpen ? styles.shifted : ''}`}>
        <h1 onClick={handleCreateNewChat} className={styles.clickable}>ChatPLG</h1>
      </div>

      {/* Mobile controls - only visible on mobile */}
      <div className={styles.mobileControls}>
        <button 
          className={styles.mobileBurgerButton}
          onClick={onToggleSidebar}
          aria-label={isSidebarOpen ? "Close sidebar" : "Open sidebar"}
        >
          <svg fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
          </svg>
        </button>
      </div>
    </header>
  );
} 