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
  status: any | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  loadStatus: () => Promise<void>;
  startBot: () => Promise<void>;
  stopBot: () => Promise<void>;
  restartBot: () => Promise<void>;
}

export const useBotStore = create<BotState>((set) => ({
  status: null,
  isLoading: false,
  error: null,

  loadStatus: async () => {
    set({ isLoading: true, error: null });
    try {
      const status = await api.getBotStatus();
      set({ status, isLoading: false });
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to load bot status';
      set({ error: message, isLoading: false });
    }
  },

  startBot: async () => {
    set({ isLoading: true, error: null });
    try {
      await api.startBot();
      const status = await api.getBotStatus();
      set({ status, isLoading: false });
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
      const status = await api.getBotStatus();
      set({ status, isLoading: false });
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
      const status = await api.getBotStatus();
      set({ status, isLoading: false });
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Failed to restart bot';
      set({ error: message, isLoading: false });
      throw error;
    }
  },
}));
