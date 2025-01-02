import React, { useState, useEffect, useRef } from 'react';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { addMessage, setTyping, Message, ChatState } from '../../store/slices/chatSlice';
import { v4 as uuidv4 } from 'uuid';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { RootState } from '../../store';
import { getCommandSuggestions, Command } from '../../utils/commands';

interface CodeBlockProps {
  language: string;
  value: string;
}

const CodeBlock: React.FC<CodeBlockProps> = ({ language, value }) => {
  return (
    <SyntaxHighlighter style={tomorrow} language={language} PreTag="div">
      {value}
    </SyntaxHighlighter>
  );
};

export const Chat: React.FC = () => {
  const dispatch = useAppDispatch();
  const chatState = useAppSelector<ChatState>((state: RootState) => state.chat);
  const messages = chatState.messages;
  const isTyping = chatState.isTyping;
  const [inputMessage, setInputMessage] = useState('');
  const [suggestions, setSuggestions] = useState<Command[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState(-1);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (showSuggestions && selectedSuggestion !== -1 && suggestionsRef.current) {
      const suggestionElements = suggestionsRef.current.children;
      const selectedElement = suggestionElements[selectedSuggestion] as HTMLElement;
      
      if (selectedElement) {
        const containerTop = suggestionsRef.current.scrollTop;
        const containerBottom = containerTop + suggestionsRef.current.clientHeight;
        const elementTop = selectedElement.offsetTop;
        const elementBottom = elementTop + selectedElement.offsetHeight;

        if (elementTop < containerTop) {
          suggestionsRef.current.scrollTop = elementTop;
        } else if (elementBottom > containerBottom) {
          suggestionsRef.current.scrollTop = elementBottom - suggestionsRef.current.clientHeight;
        }
      }
    }
  }, [selectedSuggestion, showSuggestions]);

  const handleWheel = (e: React.WheelEvent<HTMLDivElement>) => {
    if (suggestions.length > 0) {
      e.preventDefault();
      const delta = Math.sign(e.deltaY);
      setSelectedSuggestion((prev) => {
        const next = prev + delta;
        if (next < 0) return suggestions.length - 1;
        if (next >= suggestions.length) return 0;
        return next;
      });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      if (!showSuggestions) {
        const newSuggestions = getCommandSuggestions(inputMessage);
        if (newSuggestions.length > 0) {
          setSuggestions(newSuggestions);
          setShowSuggestions(true);
          setSelectedSuggestion(0);
        }
      } else {
        setSelectedSuggestion((prev) => 
          prev + 1 >= suggestions.length ? 0 : prev + 1
        );
      }
    } else if (e.key === 'ArrowDown' && showSuggestions) {
      e.preventDefault();
      setSelectedSuggestion((prev) => 
        prev + 1 >= suggestions.length ? 0 : prev + 1
      );
    } else if (e.key === 'ArrowUp' && showSuggestions) {
      e.preventDefault();
      setSelectedSuggestion((prev) => 
        prev - 1 < 0 ? suggestions.length - 1 : prev - 1
      );
    } else if (e.key === 'Enter' && showSuggestions && selectedSuggestion !== -1) {
      e.preventDefault();
      const selected = suggestions[selectedSuggestion];
      setInputMessage(selected.syntax);
      setShowSuggestions(false);
      setSelectedSuggestion(-1);
    } else if (e.key === 'Escape' && showSuggestions) {
      setShowSuggestions(false);
      setSelectedSuggestion(-1);
    } else if (showSuggestions && e.key !== 'ArrowUp' && e.key !== 'ArrowDown') {
      setShowSuggestions(false);
      setSelectedSuggestion(-1);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const userMessage: Message = {
      id: uuidv4(),
      text: inputMessage,
      sender: 'user',
      timestamp: Date.now(),
    };

    dispatch(addMessage(userMessage));
    dispatch(setTyping(true));
    setInputMessage('');
    setShowSuggestions(false);
    setSelectedSuggestion(-1);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          context: {}
        }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      
      const assistantMessage: Message = {
        id: uuidv4(),
        text: data.response,
        sender: 'assistant',
        timestamp: Date.now(),
      };

      dispatch(addMessage(assistantMessage));
    } catch (error) {
      console.error('Error:', error);
    } finally {
      dispatch(setTyping(false));
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((message: Message) => (
          <div
            key={message.id}
            className={`message ${message.sender === 'user' ? 'user' : 'assistant'}`}
          >
            <ReactMarkdown
              components={{
                code: ({ className, children }) => {
                  const language = className ? className.replace('language-', '') : 'text';
                  return (
                    <CodeBlock
                      language={language}
                      value={String(children).replace(/\n$/, '')}
                    />
                  );
                },
              }}
            >
              {message.text}
            </ReactMarkdown>
          </div>
        ))}
        {isTyping && (
          <div className="message assistant typing">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSendMessage} className="chat-input-container">
        <div className="input-wrapper">
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Press Tab for commands)"
            className="chat-input"
          />
          {showSuggestions && suggestions.length > 0 && (
            <div 
              ref={suggestionsRef}
              className="suggestions"
              onWheel={handleWheel}
            >
              {suggestions.map((suggestion, index) => (
                <div
                  key={suggestion.syntax}
                  className={`suggestion ${index === selectedSuggestion ? 'selected' : ''}`}
                  onClick={() => {
                    setInputMessage(suggestion.syntax);
                    setShowSuggestions(false);
                    setSelectedSuggestion(-1);
                    inputRef.current?.focus();
                  }}
                >
                  <div className="suggestion-syntax">{suggestion.syntax}</div>
                  <div className="suggestion-description">{suggestion.description}</div>
                </div>
              ))}
            </div>
          )}
        </div>
        <button type="submit" className="send-button">
          Send
        </button>
      </form>
    </div>
  );
}; 