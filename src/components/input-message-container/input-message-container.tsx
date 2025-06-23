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

  return (
    <form className={styles.inputContainer} onSubmit={handleSubmit}>
      <div className={styles.inputWrapper}>
        <textarea
          ref={inputRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
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