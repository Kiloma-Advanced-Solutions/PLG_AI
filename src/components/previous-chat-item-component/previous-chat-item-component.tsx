'use client';

import { useState, useRef, useEffect } from 'react';
import { Conversation } from '../../types';
import styles from './previous-chat-item-component.module.css';

/**
 * Props for the PreviousChatItemComponent
 */
type PreviousChatItemComponentProps = {
  /** The conversation data to display */
  conversation: Conversation;
  /** Whether this chat item is currently active/selected */
  isActive: boolean;
  /** Callback function when the item is clicked */
  onSelect: () => void;
  /** Callback function when the conversation title is edited */
  onTitleEdit?: (conversationId: string, newTitle: string) => void;
};

/**
 * Component that renders a single conversation item in the sidebar
 * Shows only the conversation title
 */
export default function PreviousChatItemComponent({
  conversation,
  isActive,
  onSelect,
  onTitleEdit
}: PreviousChatItemComponentProps) {
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [editTitle, setEditTitle] = useState(conversation.title);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when entering edit titlemode
  useEffect(() => {
    if (isEditingTitle && inputRef.current) {
      inputRef.current.focus();   // put the cursor in the input
      inputRef.current.select();  // highlight all text inside it
    }
  }, [isEditingTitle]);

  const handleEditTitleClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering onSelect
    setIsEditingTitle(true);
    setEditTitle(conversation.title);
  };

  const handleSave = () => {
    const trimmedTitle = editTitle.trim();
    if (trimmedTitle && trimmedTitle !== conversation.title && onTitleEdit) {
      onTitleEdit(conversation.id, trimmedTitle);
    }
    setIsEditingTitle(false);
  };

  const handleCancel = () => {
    setEditTitle(conversation.title);
    setIsEditingTitle(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };
  return (
    <div
      className={`${styles.conversationItem} ${isActive ? styles.active : ''}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          onSelect();
        }
      }}
      aria-label={`Open conversation: ${conversation.title}`}
    >
      <div className={styles.conversationItemTitle}>
        {isEditingTitle ? (
          <input
            ref={inputRef}                    // Reference for focus/select
            type="text"                       // Text input type
            value={editTitle}                 // Controlled input value
            onChange={(e) => setEditTitle(e.target.value)}  // Update state on change
            onBlur={handleSave}               // Save when user clicks away
            onKeyDown={handleKeyDown}         // Handle Enter/Escape keys
            className={styles.titleInput}     // CSS styling
            maxLength={50}                    // Limit to 50 characters
          />
        ) : (
          <span className={styles.titleText}>{conversation.title}</span>
        )}
        {/* edit conversation title icon */}
        <svg 
          width="16px" 
          height="16px" 
          viewBox="0 0 24 24" 
          fill="none" 
          className={styles.editTitleIcon} 
          onClick={handleEditTitleClick}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              handleEditTitleClick(e as any);
            }
          }}
          aria-label="Edit conversation title"
        >
          <path 
            d="M4.33295 16.048L16.5714 3.80952C17.5708 2.81015 19.1911 2.81015 20.1905 3.80952C21.1898 4.8089 21.1898 6.4292 20.1905 7.42857L7.952 19.667C7.6728 19.9462 7.3172 20.1366 6.93002 20.214L3 21L3.786 17.07C3.86344 16.6828 4.05375 16.3272 4.33295 16.048Z" 
            stroke="currentColor" 
            strokeWidth="1.5" 
            strokeLinecap="round" 
            strokeLinejoin="round"
          />
          <path 
            d="M14.5 6.5L17.5 9.5" 
            stroke="currentColor" 
            strokeWidth="1.5" 
            strokeLinecap="round" 
            strokeLinejoin="round"
          />
        </svg>
      </div>
    </div>
  );
} 