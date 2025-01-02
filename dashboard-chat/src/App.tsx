import { useState } from 'react'
import './App.css'
import { Chat } from './components/Chat/Chat'

interface WidgetProps {
  title: string;
  children: React.ReactNode;
}

const Widget: React.FC<WidgetProps> = ({ title, children }) => {
  return (
    <div className="widget">
      <h2 className="widget-title">{title}</h2>
      <div className="widget-content">
        {children}
      </div>
    </div>
  )
}

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="dashboard">
        <div className="widgets-container">
          <Widget title="Calendar">
            <p>Calendar content will go here</p>
          </Widget>
          <Widget title="Email">
            <p>Email content will go here</p>
          </Widget>
          <Widget title="Todo">
            <p>Todo content will go here</p>
          </Widget>
        </div>
        <div className="chat-container">
          <div className="chat-header">
            <h2 className="text-xl font-semibold">Chat</h2>
          </div>
          <Chat />
        </div>
      </div>
    </div>
  )
}

export default App
