'use client';

import ThemeToggleComponent from '../theme-toggle-component/theme-toggle-component';
import styles from './header-component.module.css';

type HeaderComponentProps = {
  onSidebarToggle: () => void;
  isSidebarOpen: boolean;
  onNewChat: () => void;
};

export default function HeaderComponent({ onSidebarToggle, isSidebarOpen, onNewChat }: HeaderComponentProps) {
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
        <h1 onClick={onNewChat} className={styles.clickable}>ChatPLG</h1>
      </div>
      
    </header>
  );
} 