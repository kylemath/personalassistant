import { store } from '../store';
import { addEvent, updateEvent, deleteEvent } from '../store/slices/calendarSlice';

export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout = 1000;

  constructor() {
    this.connect();
  }

  private connect() {
    try {
      this.ws = new WebSocket('ws://localhost:8000/ws');
      this.ws.onopen = this.handleOpen;
      this.ws.onclose = this.handleClose;
      this.ws.onmessage = this.handleMessage;
      this.ws.onerror = this.handleError;
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.handleReconnect();
    }
  }

  private handleOpen = () => {
    console.log('WebSocket connected');
    this.reconnectAttempts = 0;
  };

  private handleClose = () => {
    console.log('WebSocket disconnected');
    this.handleReconnect();
  };

  private handleMessage = (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data);
      
      if (data.type === 'calendar') {
        switch (data.action) {
          case 'add':
            store.dispatch(addEvent(data.event));
            break;
          case 'update':
            store.dispatch(updateEvent(data.event));
            break;
          case 'delete':
            store.dispatch(deleteEvent(data.eventId));
            break;
          default:
            console.warn('Unknown calendar action:', data.action);
        }
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
    }
  };

  private handleError = (error: Event) => {
    console.error('WebSocket error:', error);
  };

  private handleReconnect = () => {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
      setTimeout(() => this.connect(), this.reconnectTimeout * this.reconnectAttempts);
    } else {
      console.error('Max reconnection attempts reached');
    }
  };

  public sendMessage(message: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }
}

export const wsService = new WebSocketService(); 