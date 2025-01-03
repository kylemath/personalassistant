import React from 'react';
import Chat from '../Chat/Chat';
import CalendarWidget from './Calendar/CalendarWidget';
import EmailWidget from './Email/EmailWidget';
import { useDispatch } from 'react-redux';
import { addMessage } from '../../store/slices/chatSlice';
import { v4 as uuidv4 } from 'uuid';

const Dashboard: React.FC = () => {
  const dispatch = useDispatch();

  const handleDraftReply = (emailId: string) => {
    // Simulate sending the /email draft reply command
    const command = `/email draft reply ${emailId}`;
    dispatch(addMessage({
      id: uuidv4(),
      text: command,
      sender: 'user',
      timestamp: Date.now()
    }));
  };

  const handleAddEvent = (message: string) => {
    dispatch(addMessage({
      id: uuidv4(),
      text: message,
      sender: 'assistant',
      timestamp: Date.now()
    }));
  };

  return (
    <div className="dashboard">
      <div className="chat-container">
        <Chat />
      </div>
      <div className="widget-container">
        <CalendarWidget onAddEvent={handleAddEvent} />
        <EmailWidget onDraftReply={handleDraftReply} />
      </div>
    </div>
  );
};

export default Dashboard; 