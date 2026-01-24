/**
 * API Client for CryptoBot Enterprise Platform
 * Handles all HTTP requests to the backend
 */
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          this.removeToken();
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // Token management
  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('auth_token');
  }

  setToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  removeToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }

  // ===========================================================================
  // Authentication
  // ===========================================================================

  async login(email: string, password: string) {
    const response = await this.client.post('/api/auth/login/json', {
      email,
      password,
    });
    const { access_token } = response.data;
    this.setToken(access_token);
    return response.data;
  }

  async register(data: { email: string; username: string; password: string; full_name?: string }) {
    const response = await this.client.post('/api/auth/register', data);
    return response.data;
  }

  async logout() {
    try {
      await this.client.post('/api/auth/logout');
    } finally {
      this.removeToken();
    }
  }

  async getCurrentUser() {
    const response = await this.client.get('/api/auth/me');
    return response.data;
  }

  // ===========================================================================
  // Bot Management
  // ===========================================================================

  async getBotStatus() {
    const response = await this.client.get('/api/bots/status');
    return response.data;
  }

  async startBot() {
    const response = await this.client.post('/api/bots/start');
    return response.data;
  }

  async stopBot() {
    const response = await this.client.post('/api/bots/stop');
    return response.data;
  }

  async restartBot() {
    const response = await this.client.post('/api/bots/restart');
    return response.data;
  }

  async getBotConfigs() {
    const response = await this.client.get('/api/bots/configs');
    return response.data;
  }

  async createBotConfig(data: any) {
    const response = await this.client.post('/api/bots/configs', data);
    return response.data;
  }

  async updateBotConfig(id: number, data: any) {
    const response = await this.client.put(`/api/bots/configs/${id}`, data);
    return response.data;
  }

  async deleteBotConfig(id: number) {
    const response = await this.client.delete(`/api/bots/configs/${id}`);
    return response.data;
  }

  // ===========================================================================
  // Trading Data
  // ===========================================================================

  async getTrades(params?: {
    limit?: number;
    offset?: number;
    strategy?: string;
    symbol?: string;
  }) {
    const response = await this.client.get('/api/trades/', { params });
    return response.data;
  }

  async getTradeCount(params?: { strategy?: string; symbol?: string }) {
    const response = await this.client.get('/api/trades/count', { params });
    return response.data;
  }

  async getRecentTrades(hours: number = 24) {
    const response = await this.client.get(`/api/trades/recent?hours=${hours}`);
    return response.data;
  }

  async getPortfolio() {
    const response = await this.client.get('/api/trades/portfolio');
    return response.data;
  }

  async getPerformance(hours?: number) {
    const url = hours ? `/api/trades/performance?hours=${hours}` : '/api/trades/performance';
    const response = await this.client.get(url);
    return response.data;
  }

  // ===========================================================================
  // User Management
  // ===========================================================================

  async getUsers(skip: number = 0, limit: number = 100) {
    const response = await this.client.get(`/api/users/?skip=${skip}&limit=${limit}`);
    return response.data;
  }

  async getUser(id: number) {
    const response = await this.client.get(`/api/users/${id}`);
    return response.data;
  }

  async updateUser(id: number, data: any) {
    const response = await this.client.put(`/api/users/${id}`, data);
    return response.data;
  }

  async deleteUser(id: number) {
    const response = await this.client.delete(`/api/users/${id}`);
    return response.data;
  }

  async getUserActivity(id: number, skip: number = 0, limit: number = 50) {
    const response = await this.client.get(`/api/users/${id}/activity?skip=${skip}&limit=${limit}`);
    return response.data;
  }

  // ===========================================================================
  // Health Check
  // ===========================================================================

  async healthCheck() {
    const response = await this.client.get('/health');
    return response.data;
  }
}

// Export singleton instance
export const api = new ApiClient();
