import { useState, useEffect, useRef } from 'react';
import WebSocketService from '../../services/websocket';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import 'react-chat-elements/dist/main.css';

interface Message {
  content: string;
  isUser: boolean;
  timestamp: Date;
}

export const Chat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const wsService = useRef<WebSocketService>(WebSocketService.getInstance());
  const chatHistoryRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Subscribe to WebSocket messages
    const unsubscribe = wsService.current.onMessage((message) => {
      addMessage(message, false);
    });

    // Subscribe to WebSocket errors
    const unsubscribeError = wsService.current.onError((error) => {
      console.error('WebSocket error:', error);
      addMessage('Error: Connection lost. Trying to reconnect...', false);
    });

    return () => {
      unsubscribe();
      unsubscribeError();
    };
  }, []);

  const addMessage = (content: string, isUser: boolean) => {
    setMessages(prev => [{
      content,
      isUser,
      timestamp: new Date()
    }, ...prev]);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    // Add user message to chat
    addMessage(inputMessage, true);

    // Try to send via WebSocket
    const sent = wsService.current.sendMessage(inputMessage);

    if (!sent) {
      // Fallback to HTTP if WebSocket is not connected
      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: inputMessage }),
        });
        const data = await response.json();
        addMessage(data.response, false);
      } catch (error) {
        console.error('Error sending message:', error);
        addMessage('Error: Could not send message', false);
      }
    }

    setInputMessage('');
  };

  const renderMessage = (content: string) => {
    // Split content into parts (regular text and code blocks)
    const parts = content.split(/(```[\s\S]*?```)/);
    return parts.map((part, index) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        // Extract language and code
        const [, lang, ...codeParts] = part.slice(3, -3).split('\n');
        const code = codeParts.join('\n');
        
        return (
          <div key={index} className="my-2">
            <SyntaxHighlighter
              language={lang || 'text'}
              style={oneDark}
              showLineNumbers={true}
              customStyle={{
                margin: 0,
                borderRadius: '4px',
              }}
            >
              {code}
            </SyntaxHighlighter>
          </div>
        );
      } else if (part.trim()) {
        return (
          <ReactMarkdown key={index} className="prose prose-sm max-w-none">
            {part}
          </ReactMarkdown>
        );
      }
      return null;
    });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Chat history */}
      <div 
        ref={chatHistoryRef}
        className="chat-history"
      >
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`message ${msg.isUser ? 'message-user' : 'message-assistant'}`}
          >
            <div>
              {renderMessage(msg.content)}
            </div>
            <div className="message-timestamp">
              {msg.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>

      {/* Input section */}
      <div className="chat-input-wrapper">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSendMessage}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}; 