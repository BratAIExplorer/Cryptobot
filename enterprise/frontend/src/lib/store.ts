/**
 * Global State Management with Zustand
 * Handles authentication state and user data
 */
import { create } from 'zustand';
import { api } from './api';

interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login?: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    email: string;
    username: string;
    password: string;
    full_name?: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      await api.login(email, password);
      const user = await api.getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Login failed';
      set({ error: message, isLoading: false });
      throw error;
    }
  },

  register: async (data) => {
    set({ isLoading: true, error: null });
    try {
      await api.register(data);
      // After registration, log in automatically
      await api.login(data.email, data.password);
      const user = await api.getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Registration failed';
      set({ error: message, isLoading: false });
      throw error;
    }
  },

  logout: async () => {
    try {
      await api.logout();
    } finally {
      set({ user: null, isAuthenticated: false });
    }
  },

  loadUser: async () => {
    const token = api.getToken();
    if (!token) {
      set({ isAuthenticated: false, isLoading: false });
      return;
    }

    set({ isLoading: true });
    try {
      const user = await api.getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error) {
      api.removeToken();
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  clearError: () => set({ error: null }),
}));

interface BotState {
  botStatus: any | null;
  portfolio: any | null;
  botConfigs: any[];
  recentTrades: any[];
  strategyPerformance: any[];
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchBotStatus: () => Promise<void>;
  fetchPortfolio: () => Promise<void>;
  fetchBotConfigs: () => Promise<void>;
  fetchRecentTrades: (hours: number) => Promise<void>;
  fetchStrategyPerformance: () => Promise<void>;
  updateBotConfig: (id: number, data: any) => Promise<void>;
  startBot: () => Promise<void>;
  stopBot: () => Promise<void>;
  restartBot: () => Promise<void>;
}

export const useBotStore = create<BotState>((set, get) => ({
  botStatus: null,
  portfolio: null,
  botConfigs: [],
  recentTrades: [],
  strategyPerformance: [],
  isLoading: false,
  error: null,

  fetchBotStatus: async () => {
    try {
      const botStatus = await api.getBotStatus();
      set({ botStatus });
    } catch (error: any) {
      console.error('Failed to fetch bot status:', error);
      set({ error: error.response?.data?.detail || 'Failed to load bot status' });
    }
  },

  fetchPortfolio: async () => {
    try {
      const portfolio = await api.getPortfolio();
      set({ portfolio });
    } catch (error: any) {
      console.error('Failed to fetch portfolio:', error);
      set({ error: error.response?.data?.detail || 'Failed to load portfolio' });
    }
  },

  fetchBotConfigs: async () => {
    try {
      const botConfigs = await api.getBotConfigs();
      set({ botConfigs });
    } catch (error: any) {
      console.error('Failed to fetch bot configs:', error);
      set({ error: error.response?.data?.detail || 'Failed to load bot configs' });
    }
  },

  updateBotConfig: async (id: number, data: any) => {
    set({ isLoading: true });
    try {
      await api.updateBotConfig(id, data);
      const botConfigs = await api.getBotConfigs();
      set({ botConfigs, isLoading: false });
    } catch (error: any) {
      console.error('Failed to update bot config:', error);
      set({ error: error.response?.data?.detail || 'Failed to update bot config', isLoading: false });
      throw error;
    }
  },

  fetchRecentTrades: async (hours: number) => {
    try {
      const recentTrades = await api.getRecentTrades(hours);
      set({ recentTrades });
    } catch (error: any) {
      console.error('Failed to fetch recent trades:', error);
      set({ error: error.response?.data?.detail || 'Failed to load trades' });
    }
  },

  fetchStrategyPerformance: async () => {
    try {
      const data = await api.getPerformance();
      const strategyPerformance = data.strategies || [];
      set({ strategyPerformance });
    } catch (error: any) {
      console.error('Failed to fetch strategy performance:', error);
      set({ error: error.response?.data?.detail || 'Failed to load performance' });
    }
  },

  startBot: async () => {
    set({ isLoading: true, error: null });
    try {
      await api.startBot();
      const botStatus = await api.getBotStatus();
      set({ botStatus, isLoading: false });
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to start bot';
      set({ error: message, isLoading: false });
      throw error;
    }
  },

  stopBot: async () => {
    set({ isLoading: true, error: null });
    try {
      await api.stopBot();
      const botStatus = await api.getBotStatus();
      set({ botStatus, isLoading: false });
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to stop bot';
      set({ error: message, isLoading: false });
      throw error;
    }
  },

  restartBot: async () => {
    set({ isLoading: true, error: null });
    try {
      await api.restartBot();
      const botStatus = await api.getBotStatus();
      set({ botStatus, isLoading: false });
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to restart bot';
      set({ error: message, isLoading: false });
      throw error;
    }
  },
}));
