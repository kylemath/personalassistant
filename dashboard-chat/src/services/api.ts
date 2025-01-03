const API_BASE_URL = `http://${window.location.hostname}:8000`;

interface ApiResponse<T> {
  data: T;
  status: 'success' | 'error';
  message?: string;
}

export class ApiService {
  private baseUrl = API_BASE_URL;

  public async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  public async post<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  public async sendMessage(message: string): Promise<any> {
    return this.post('/chat', {
      body: JSON.stringify({ message }),
    });
  }
} 