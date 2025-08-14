'use client';

import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeRaw from 'rehype-raw';
import katex from 'katex';
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
};

/**
 * Component that renders a single chat message with appropriate styling
 * based on message type (user or assistant)
 */
export default function ChatMessageComponent({ 
  type, 
  content, 
  timestamp,
  isStreaming = false
}: ChatMessageComponentProps) {
  return (
    <div className={`${styles.messageContainer} ${styles[type]}`}>
      <div className={styles.messageBox}>
        <div className={`${styles.messageText} ${type === 'assistant' ? styles.assistantText : styles.userText}`} dir="rtl">
          {type === 'assistant' ? (
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[rehypeKatex, rehypeRaw]}
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
                    <SyntaxHighlighter
                      PreTag="div"
                      language={language}
                      style={vscDarkPlus}
                      customStyle={{
                        margin: '1rem 0',
                        borderRadius: '0.5rem',
                        fontSize: '0.9rem'
                      }}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
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
          ) : (
            content
          )}
          {isStreaming && <span className={styles.streamingCursor}>|</span>}
        </div>
        <div className={styles.messageTime}>
          {timestamp}
        </div>
      </div>
    </div>
  );
} 