import { store } from '../store';
import { addEvent, updateEvent, deleteEvent } from '../store/slices/calendarSlice';
import { addMessage, setTyping } from '../store/slices/chatSlice';
import { v4 as uuidv4 } from 'uuid';

export class WebSocketService {
  private ws: WebSocket | null = null;
  private messageHandlers: Set<(event: MessageEvent) => void> = new Set();

  constructor() {
    this.connect();
  }

  private connect() {
    this.ws = new WebSocket(`ws://${window.location.hostname}:8000/ws`);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      this.messageHandlers.forEach(handler => handler(event));
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected, attempting to reconnect...');
      setTimeout(() => this.connect(), 1000);
    };
  }

  public sendMessage(message: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }

  public onMessage(handler: (event: MessageEvent) => void) {
    this.messageHandlers.add(handler);
  }

  public offMessage(handler: (event: MessageEvent) => void) {
    this.messageHandlers.delete(handler);
  }
}

export const wsService = new WebSocketService(); 