'use client';

import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeRaw from 'rehype-raw';
import katex from 'katex';
import { useTheme } from '../../contexts/ThemeContext';
import styles from './chat-message-component.module.css';

/**
 * Props for the ChatMessageComponent
 */
type ChatMessageComponentProps = {
  /** Type of message - determines styling and alignment */
  type: 'user' | 'assistant';
  /** The message content to display */
  content: string;
  /** Formatted timestamp string for display */
  timestamp: string;
  /** Whether this message is currently being streamed (shows cursor animation) */
  isStreaming?: boolean;
  /** Callback for when message content is edited (only for user messages) */
  onMessageEdit?: (newContent: string) => void;
};

/**
 * Component that renders a single chat message with appropriate styling
 * based on message type (user or assistant)
 */
export default function ChatMessageComponent({ 
  type, 
  content, 
  timestamp,
  isStreaming = false,
  onMessageEdit
}: ChatMessageComponentProps) {
  const { isDark } = useTheme();
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(content);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Focus textarea when entering edit mode
  useEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.select();
    }
  }, [isEditing]);

  const handleEditMessageClick = () => {
    setIsEditing(true);
    setEditedContent(content);
  };

  const handleSaveMessage = () => {
    const trimmedContent = editedContent.trim();
    if (trimmedContent && trimmedContent !== content && onMessageEdit) {
      onMessageEdit(trimmedContent);
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditedContent(content);
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSaveMessage();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  return (
    <div className={`${styles.messageContainer} ${styles[type]}`}>
      {type === 'user' ? (
        <div className={`${styles.userMessageWrapper} ${isEditing ? styles.editing : ''}`}>
          <div className={styles.messageBox}>
            {isEditing ? (
              <div className={styles.editContainer}>
                <textarea
                  ref={textareaRef}
                  value={editedContent}
                  onChange={(e) => setEditedContent(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className={styles.editTextarea}
                  dir="rtl"
                  placeholder=""
                />
                <div className={styles.editButtons} dir="ltr">
                  <button onClick={handleSaveMessage} className={styles.saveButton}>
                    שמור
                  </button>
                  <button onClick={handleCancel} className={styles.cancelButton}>
                    ביטול
                  </button>
                </div>
              </div>
            ) : (
              <div className={`${styles.messageText} ${styles.userText}`} dir="rtl">
                {content}
              </div>
            )}
          </div>
          {!isEditing && (
            <div className={styles.messageFeatures} dir="ltr">
              <span className={styles.messageTime}>
                {timestamp}
              </span>
              <button className={styles.editIcon} title="ערוך הודעה" onClick={handleEditMessageClick}>
                <svg width="16px" height="16px" viewBox="0 0 24 24" fill="none">
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
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className={styles.messageText} dir="rtl" data-streaming={isStreaming}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkMath]}
            rehypePlugins={[rehypeKatex]}
            components={{
              code(props) {
                const { children, className, inline, ...rest } = props as unknown as {
                  children: React.ReactNode;
                  className?: string;
                  inline?: boolean;
                };
                const match = /language-(\w+)/.exec(className || '');
                const language = match ? match[1] : '';
                
                if (language === 'latex') {
                  const latexSource = String(children).replace(/\n$/, '');
                  const html = katex.renderToString(latexSource, {
                    throwOnError: false,
                    displayMode: !inline,
                    strict: 'ignore'
                  });
                  return (
                    <span
                      // KaTeX returns HTML that is safe to inject here
                      dangerouslySetInnerHTML={{ __html: html }}
                    />
                  );
                }
                
                return match ? (
                  // Code blocks
                  <div className={styles.codeBlockContainer}>
                    <SyntaxHighlighter
                      PreTag="div"
                      language={language}
                      style={isDark ? vscDarkPlus : oneLight}
                      customStyle={{
                        margin: '0',
                        borderRadius: '0.5rem',
                        maxWidth: '100%',
                        overflow: 'auto',
                        padding: '1rem',
                        direction: 'ltr',
                      }}
                      showLineNumbers={false}
                      wrapLines={false}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  </div>
                ) : (
                  <code {...rest} className={`${className || ''} ${styles.inlineCode}`}>
                    {children}
                  </code>
                );
              },
              p: ({ children }) => <p className={styles.paragraph}>{children}</p>,
              ul: ({ children }) => <ul className={styles.list}>{children}</ul>,
              ol: ({ children }) => <ol className={styles.orderedList}>{children}</ol>,
              li: ({ children }) => <li className={styles.listItem}>{children}</li>,
              table: ({ children }) => <table className={styles.table}>{children}</table>,
              thead: ({ children }) => <thead className={styles.thead}>{children}</thead>,
              th: ({ children }) => <th className={styles.th}>{children}</th>,
              td: ({ children }) => <td className={styles.td}>{children}</td>,
              h1: ({ children }) => <h1 className={styles.heading1}>{children}</h1>,
              h2: ({ children }) => <h2 className={styles.heading2}>{children}</h2>,
              h3: ({ children }) => <h3 className={styles.heading3}>{children}</h3>,
              blockquote: ({ children }) => <blockquote className={styles.blockquote}>{children}</blockquote>,
              a: ({ children, href }) => (
                <a href={href} className={styles.link} target="_blank" rel="noopener noreferrer">
                  {children}
                </a>
              ),
              // Allow basic HTML like <u>, <div> via rehypeRaw; no special mapping needed here
            }}
            >
            {content}
          </ReactMarkdown>
          {isStreaming && (
            <span className={styles.streamingCursor}>|</span>
          )}
          {!isStreaming && (
            <span className={styles.inlineTimestamp}>
              {timestamp}
            </span>
          )}
        </div>
      )}
    </div>
  );
} 