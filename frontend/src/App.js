import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function ChatMessage({ message, isUser }) {
  return (
    <div className={`message ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-content">
        {message}
      </div>
    </div>
  );
}

function App() {
  const [messages, setMessages] = useState([
    { text: "שלום! אני כאן לעזור לך. איך אני יכול לסייע?", isUser: false }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setIsLoading(true);

    // Add user message
    setMessages(prev => [...prev, { text: userMessage, isUser: true }]);

    // Add empty assistant message for streaming
    const assistantMessageIndex = messages.length + 1;
    setMessages(prev => [...prev, { text: '', isUser: false }]);

    try {
      const response = await fetch('http://localhost:8001/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            
            if (data === '[DONE]') {
              setIsLoading(false);
              continue;
            }

            try {
              const parsed = JSON.parse(data);
              
              if (parsed.error) {
                console.error('Error from server:', parsed.error);
                setMessages(prev => {
                  const updated = [...prev];
                  updated[assistantMessageIndex] = {
                    text: "מצטער, אירעה שגיאה. אנא נסה שוב.",
                    isUser: false
                  };
                  return updated;
                });
                setIsLoading(false);
                return;
              }

              if (parsed.content) {
                // Append to the assistant message
                setMessages(prev => {
                  const updated = [...prev];
                  updated[assistantMessageIndex] = {
                    text: updated[assistantMessageIndex].text + parsed.content,
                    isUser: false
                  };
                  return updated;
                });
              }
            } catch (e) {
              console.error('Error parsing JSON:', e);
            }
          }
        }
      }

      // Process remaining buffer
      if (buffer.trim()) {
        const lines = buffer.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ') && line.slice(6) !== '[DONE]') {
            try {
              const parsed = JSON.parse(line.slice(6));
              if (parsed.content) {
                setMessages(prev => {
                  const updated = [...prev];
                  updated[assistantMessageIndex] = {
                    text: updated[assistantMessageIndex].text + parsed.content,
                    isUser: false
                  };
                  return updated;
                });
              }
            } catch (e) {
              console.error('Error parsing remaining buffer:', e);
            }
          }
        }
      }

      setIsLoading(false);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        text: "מצטער, אירעה שגיאה. אנא נסה שוב.", 
        isUser: false 
      }]);
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app">
      <div className="chat-container">
        <div className="chat-header">
          <h1>MCP Chat Assistant</h1>
        </div>
        
        <div className="messages-container">
          {messages.map((message, index) => (
            <ChatMessage
              key={index}
              message={message.text}
              isUser={message.isUser}
            />
          ))}
          {isLoading && (
            <div className="message assistant">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="input-container">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="הקלד הודעה..."
            disabled={isLoading}
            rows="1"
          />
          <button 
            onClick={sendMessage} 
            disabled={!inputValue.trim() || isLoading}
            className="send-button"
          >
            שלח
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
