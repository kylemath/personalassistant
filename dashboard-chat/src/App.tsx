import { Chat } from './components/Chat/Chat';
import { CalendarWidget } from './components/Dashboard/Calendar/CalendarWidget';
import './App.css';

function App() {
  return (
    <div className="dashboard">
      <div className="dashboard-grid">
        <div className="widget-container">
          <CalendarWidget />
        </div>
      </div>
      <div className="chat-wrapper">
        <Chat />
      </div>
    </div>
  );
}

export default App;
