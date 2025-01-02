type MessageCallback = (message: string) => void;
type ErrorCallback = (error: Event) => void;

class WebSocketService {
  private static instance: WebSocketService;
  private ws: WebSocket | null = null;
  private messageCallbacks: Set<MessageCallback> = new Set();
  private errorCallbacks: Set<ErrorCallback> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: number = 1000; // Start with 1 second

  private constructor() {
    this.connect();
  }

  public static getInstance(): WebSocketService {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService();
    }
    return WebSocketService.instance;
  }

  private connect() {
    try {
      this.ws = new WebSocket('ws://localhost:8000/ws/chat');
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.reconnectTimeout = 1000;
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.handleError(new Event('error'));
    }
  }

  private handleMessage(event: MessageEvent) {
    const data = JSON.parse(event.data);
    this.messageCallbacks.forEach(callback => callback(data.message));
  }

  private handleError(error: Event) {
    console.error('WebSocket error:', error);
    this.errorCallbacks.forEach(callback => callback(error));
  }

  private handleClose() {
    console.log('WebSocket closed');
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
        this.reconnectAttempts++;
        this.reconnectTimeout *= 2; // Exponential backoff
        this.connect();
      }, this.reconnectTimeout);
    }
  }

  public sendMessage(message: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ message }));
      return true;
    }
    return false;
  }

  public onMessage(callback: MessageCallback) {
    this.messageCallbacks.add(callback);
    return () => this.messageCallbacks.delete(callback);
  }

  public onError(callback: ErrorCallback) {
    this.errorCallbacks.add(callback);
    return () => this.errorCallbacks.delete(callback);
  }

  public disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export default WebSocketService; 