const API_BASE_URL = 'http://localhost:8000';

interface ApiResponse<T> {
  data: T;
  status: 'success' | 'error';
  message?: string;
}

export class ApiService {
  private baseUrl = 'http://localhost:8000';

  public async sendMessage(message: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      return await response.json();
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }
} 