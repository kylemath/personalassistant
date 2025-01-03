import React, { useState, useEffect, useRef, KeyboardEvent, ChangeEvent } from 'react';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { RootState } from '../../store';
import { getCommandSuggestions, Command } from '../../utils/commands';
import { wsService } from '../../services/websocket';
import { ApiService } from '../../services/api';
import { addMessage, setTyping, setError } from '../../store/slices/chatSlice';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { v4 as uuidv4 } from 'uuid';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: number;
}

const Chat: React.FC = () => {
  const [message, setMessage] = useState('');
  const [suggestions, setSuggestions] = useState<Command[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState(-1);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const dispatch = useAppDispatch();
  const { messages, isTyping } = useAppSelector((state: RootState) => state.chat);
  const apiService = new ApiService();

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  useEffect(() => {
    // Set up WebSocket message handler
    const handleWebSocketMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        const response = {
          id: uuidv4(),
          text: typeof data === 'string' ? data : JSON.stringify(data, null, 2),
          sender: 'assistant' as const,
          timestamp: Date.now()
        };
        dispatch(addMessage(response));
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    wsService.onMessage(handleWebSocketMessage);

    return () => {
      wsService.offMessage(handleWebSocketMessage);
    };
  }, [dispatch]);

  const handleSendMessage = async () => {
    if (!message.trim()) return;

    const newMessage: Message = {
      id: uuidv4(),
      text: message,
      sender: 'user',
      timestamp: Date.now()
    };

    // Add user message to Redux store
    dispatch(addMessage(newMessage));

    if (message.startsWith('/')) {
      // Send command via WebSocket
      wsService.sendMessage({ command: message });
    } else {
      try {
        dispatch(setTyping(true));
        const response = await apiService.sendMessage(message);
        
        // Add assistant's response to Redux store
        dispatch(addMessage({
          id: uuidv4(),
          text: response.response,
          sender: 'assistant',
          timestamp: Date.now()
        }));
      } catch (error) {
        console.error('Error sending message:', error);
        dispatch(setError('Failed to send message'));
      } finally {
        dispatch(setTyping(false));
      }
    }

    setMessage('');
    setSuggestions([]);
    setShowSuggestions(false);
    setSelectedSuggestion(-1);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    } else if (e.key === 'Tab' && !showSuggestions) {
      e.preventDefault();
      const newSuggestions = getCommandSuggestions(message);
      if (newSuggestions.length > 0) {
        setSuggestions(newSuggestions);
        setShowSuggestions(true);
        setSelectedSuggestion(0);
      }
    } else if (showSuggestions) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedSuggestion(prev => 
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedSuggestion(prev => 
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
      } else if (e.key === 'Enter' && selectedSuggestion !== -1) {
        e.preventDefault();
        setMessage(suggestions[selectedSuggestion].command);
        setShowSuggestions(false);
        setSelectedSuggestion(-1);
      } else if (e.key === 'Escape') {
        setShowSuggestions(false);
        setSelectedSuggestion(-1);
      }
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setMessage(newValue);
    
    if (newValue.startsWith('/')) {
      const newSuggestions = getCommandSuggestions(newValue);
      setSuggestions(newSuggestions);
      setShowSuggestions(true);
      setSelectedSuggestion(newSuggestions.length > 0 ? 0 : -1);
    } else {
      setShowSuggestions(false);
      setSelectedSuggestion(-1);
    }
  };

  const handleWheel = (e: WheelEvent) => {
    if (showSuggestions) {
      e.preventDefault();
      const delta = Math.sign(e.deltaY);
      setSelectedSuggestion(prev => {
        const next = prev + delta;
        if (next < 0) return suggestions.length - 1;
        if (next >= suggestions.length) return 0;
        return next;
      });
    }
  };

  const components = {
    code({ node, inline, className, children, ...props }: any) {
      const match = /language-(\w+)/.exec(className || '');
      return !inline && match ? (
        <SyntaxHighlighter
          style={tomorrow}
          language={match[1]}
          PreTag="div"
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      ) : (
        <code className={className} {...props}>
          {children}
        </code>
      );
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.sender}`}>
            <ReactMarkdown components={components}>{msg.text}</ReactMarkdown>
          </div>
        ))}
        {isTyping && (
          <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input-container">
        <div className="input-wrapper">
          <input
            type="text"
            value={message}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            className="chat-input"
            placeholder="Type a message or command (start with /)"
          />
          {showSuggestions && suggestions.length > 0 && (
            <div 
              className="suggestions" 
              ref={suggestionsRef}
              onWheel={handleWheel as any}
            >
              {suggestions.map((suggestion, index) => (
                <div
                  key={suggestion.command}
                  className={`suggestion ${index === selectedSuggestion ? 'selected' : ''}`}
                  onClick={() => {
                    setMessage(suggestion.command);
                    setShowSuggestions(false);
                    setSelectedSuggestion(-1);
                  }}
                >
                  <div className="suggestion-syntax">{suggestion.command}</div>
                  <div className="suggestion-description">{suggestion.description}</div>
                </div>
              ))}
            </div>
          )}
        </div>
        <button onClick={handleSendMessage} className="send-button">
          Send
        </button>
      </div>
    </div>
  );
};

export default Chat; 