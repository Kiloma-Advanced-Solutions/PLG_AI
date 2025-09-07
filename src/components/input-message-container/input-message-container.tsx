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
  isStreaming?: boolean;
  /** Whether to trigger the focus animation effect */
  triggerFocusAnimation?: boolean;
  /** Pre-filled message value for restoration */
  prefilledMessage?: string;
  /** Callback when prefilled message is used or cleared */
  onPrefilledMessageCleared?: () => void;
  /** Callback function called when user clicks stop button */
  onStop?: (currentInputValue: string) => void;
};

/**
 * Component that handles user message input with auto-resize textarea,
 * focus management, and submit functionality
 */
export default function InputMessageContainer({ 
  onSendMessage, 
  isStreaming = false,
  triggerFocusAnimation = false,
  prefilledMessage = '',
  onPrefilledMessageCleared,
  onStop,
}: InputMessageContainerProps) {

  const [inputValue, setInputValue] = useState('');
  const [showFocusAnimation, setShowFocusAnimation] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Handle prefilled message when it changes - only if input is empty
  useEffect(() => {
    if (prefilledMessage && prefilledMessage !== inputValue && (!inputValue || inputValue.trim() === '')) {
      setInputValue(prefilledMessage);
    }
  }, [prefilledMessage, inputValue]);

  // Clear prefilled message when input changes (user starts editing)
  useEffect(() => {
    if (prefilledMessage && inputValue !== prefilledMessage && onPrefilledMessageCleared) {
      onPrefilledMessageCleared();
    }
  }, [inputValue, prefilledMessage, onPrefilledMessageCleared]);

  // Trigger focus animation when prop changes
  useEffect(() => {
    if (triggerFocusAnimation) {
      setShowFocusAnimation(true);
      inputRef.current?.focus();
      
      const timer = setTimeout(() => setShowFocusAnimation(false), 600);
      return () => clearTimeout(timer);
    }
  }, [triggerFocusAnimation]);

  /**
   * Handles form submission when user sends a message
   */
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isStreaming) {
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
      if (!isStreaming) {
        handleSubmit(e);
      }
    }
  };

  // Auto-resize textarea based on content
  useEffect(() => {
    const input = inputRef.current;
    if (!input) return;
    input.style.height = 'auto';
    input.style.height = `${input.scrollHeight}px`;
  }, [inputValue]);


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
          dir="rtl"
          autoFocus
        />
        {isStreaming && onStop ? (
          <button
            type="button"
            className={styles.sendButton}
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onStop(inputValue);
            }}
            aria-label="עצור יצירת תגובה"
          >
            <svg className={styles.sendIcon} fill="currentColor" viewBox="0 0 20 20">
              <rect x="5" y="5" width="10" height="10" rx="1" />
            </svg>
          </button>
        ) : (
          <button
            type="submit"
            className={styles.sendButton}
            disabled={!inputValue.trim() || isStreaming}
            aria-label="Send message"
          >
            <svg className={styles.sendIcon} fill="currentColor" viewBox="0 0 20 20">
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
            </svg>
          </button>
        )}
      </div>
    </form>
  );
} 