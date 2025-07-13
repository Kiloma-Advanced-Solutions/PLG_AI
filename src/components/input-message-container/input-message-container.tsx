'use client';

import { useState, useRef, useEffect } from 'react';
import styles from './input-message-container.module.css';

// the props of the input message container component
type InputMessageContainerProps = {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  shouldFocusInput?: boolean;
};

// the input message container component
export default function InputMessageContainer({ 
  onSendMessage, 
  isLoading = false,
  shouldFocusInput = false
}: InputMessageContainerProps) {

  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Function to handle the submission of the message
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  // Function to allow users to send a message by pressing Enter
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea and focus management
  useEffect(() => {
    const input = inputRef.current;
    if (!input) return;

    // Auto-resize
    input.style.height = 'auto';
    input.style.height = `${input.scrollHeight}px`;

    // Focus management
    if (!isLoading) {
      input.focus();
    }
  }, [inputValue, isLoading]);

  // Focus when shouldFocusInput changes
  useEffect(() => {
    if (shouldFocusInput && inputRef.current) {
      inputRef.current.focus();
    }
  }, [shouldFocusInput]);

  return (
    <form className={styles.inputContainer} onSubmit={handleSubmit}>
      <div className={styles.inputWrapper}>
        <textarea
          ref={inputRef}
          value={inputValue} 
          onChange={(e) => setInputValue(e.target.value)} 
          onKeyDown={handleKeyPress} 
          placeholder="הקלד הודעה..."
          className={styles.messageInput} 
          rows={1}  // the number of rows of the textarea
          disabled={isLoading} // the disabled state of the textarea
          dir="rtl" // the direction of the textarea
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