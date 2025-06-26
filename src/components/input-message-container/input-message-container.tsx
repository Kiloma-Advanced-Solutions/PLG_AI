'use client';

import { useState, useRef, useEffect } from 'react';
import styles from './input-message-container.module.css';

type InputMessageContainerProps = {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
};

export default function InputMessageContainer({ 
  onSendMessage, 
  isLoading = false 
}: InputMessageContainerProps) {
  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue.trim());
      setInputValue('');
      // Immediate refocus
      ensureFocus();
    }
  };

  // Function to ensure input is always focused
  const ensureFocus = () => {
    if (inputRef.current && !isLoading) {
      inputRef.current.focus();
    }
  };
  
  

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${inputRef.current.scrollHeight}px`;
    }
  }, [inputValue]);

  // Persistent focus management
  useEffect(() => {
    const input = inputRef.current;
    if (!input) return;

    // Initial focus
    ensureFocus();

    // Handle blur events - refocus immediately unless loading
    const handleBlur = () => {
      // Small delay to allow for legitimate focus changes (like clicking send button)
      setTimeout(() => {
        ensureFocus();
      }, 10);
    };

    // Handle window focus - refocus when user returns to tab
    const handleWindowFocus = () => {
      ensureFocus();
    };

    // Add event listeners
    input.addEventListener('blur', handleBlur);
    window.addEventListener('focus', handleWindowFocus);

    // Cleanup
    return () => {
      input.removeEventListener('blur', handleBlur);
      window.removeEventListener('focus', handleWindowFocus);
    };
  }, [isLoading]);

  // Focus when loading state changes
  useEffect(() => {
    if (!isLoading) {
      // Small delay to ensure DOM is updated
      setTimeout(() => {
        ensureFocus();
      }, 50);
    }
  }, [isLoading]);

  return (
    <form className={styles.inputContainer} onSubmit={handleSubmit}>
      <div className={styles.inputWrapper}>
        <textarea
          ref={inputRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          onBlur={(e) => {
            // Prevent blur unless it's due to loading or legitimate UI interaction
            if (!isLoading) {
              setTimeout(() => ensureFocus(), 10);
            }
          }}
          placeholder="הקלד הודעה..."
          className={styles.messageInput}
          rows={1}
          disabled={isLoading}
          dir="rtl"
        />
        <button
          type="submit"
          className={styles.sendButton}
          disabled={!inputValue.trim() || isLoading}
        >
          <svg className={styles.sendIcon} fill="currentColor" viewBox="0 0 20 20">
            <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
          </svg>
        </button>
      </div>
    </form>
  );
} 