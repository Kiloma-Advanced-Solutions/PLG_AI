'use client';

import { useState, useRef, useEffect } from 'react';
import styles from './input-message-container.module.css';

/**
 * Props for the InputMessageContainer component
 */
type InputMessageContainerProps = {
  /** Callback function called when user submits a message */
  onSendMessage: (message: string) => void;
  /** Whether the chat is currently loading (disables input) */
  isLoading?: boolean;
  /** Whether to trigger the focus animation effect */
  triggerFocusAnimation?: boolean;
};

/**
 * Component that handles user message input with auto-resize textarea,
 * focus management, and submit functionality
 */
export default function InputMessageContainer({ 
  onSendMessage, 
  isLoading = false,
  triggerFocusAnimation = false,
}: InputMessageContainerProps) {

  const [inputValue, setInputValue] = useState('');
  const [showFocusAnimation, setShowFocusAnimation] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Trigger focus animation when prop changes
  useEffect(() => {
    if (triggerFocusAnimation) {
      setShowFocusAnimation(true);
      // Remove animation class after animation completes
      setTimeout(() => setShowFocusAnimation(false), 600);
    }
  }, [triggerFocusAnimation]);

  /**
   * Handles form submission when user sends a message
   */
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  /**
   * Handles Enter key press for message submission
   * Shift+Enter creates a new line instead of submitting
   */
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea and manage focus
  useEffect(() => {
    const input = inputRef.current;
    if (!input) return;

    // Auto-resize textarea based on content
    input.style.height = 'auto';
    input.style.height = `${input.scrollHeight}px`;

    // Focus input when not loading
    if (!isLoading) {
      input.focus();
    }
  }, [inputValue, isLoading]);


  return (
    <form className={styles.inputContainer} onSubmit={handleSubmit}>
      <div className={`${styles.inputWrapper} ${showFocusAnimation ? styles.focusAnimation : ''}`}>
        <textarea
          ref={inputRef}
          value={inputValue} 
          onChange={(e) => setInputValue(e.target.value)} 
          onKeyDown={handleKeyPress} 
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
          aria-label="Send message"
        >
          <svg className={styles.sendIcon} fill="currentColor" viewBox="0 0 20 20">
            <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
          </svg>
        </button>
      </div>
    </form>
  );
} 