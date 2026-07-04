import axios, { AxiosError } from 'axios';
import type { ChatMessage, ChatResponse } from '../types';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || (import.meta.env.PROD ? 'https://shl-assessment-recommender-production-6f8d.up.railway.app' : 'http://localhost:8000'),
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Retry interceptor: retry once on network disconnects or 5xx server issues
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config;
    if (!config || (config as any)._retry) {
      return Promise.reject(error);
    }

    const isNetworkError = !error.response;
    const isServerError = error.response && error.response.status >= 500;

    if (isNetworkError || isServerError) {
      (config as any)._retry = true;
      console.warn('Network or server error encountered. Retrying request once...');
      try {
        return await api(config);
      } catch (retryError) {
        return Promise.reject(retryError);
      }
    }

    return Promise.reject(error);
  }
);

export const checkHealth = async (): Promise<{ status: string }> => {
  const response = await api.get('/health');
  return response.data;
};

export const sendChatMessage = async (messages: ChatMessage[]): Promise<ChatResponse> => {
  // Strip optional client-only timestamps before posting to backend schema
  const cleanMessages = messages.map(({ role, content }) => ({ role, content }));
  const response = await api.post<ChatResponse>('/chat', { messages: cleanMessages });
  return response.data;
};
