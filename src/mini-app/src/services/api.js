
import { authService } from './auth';

const BASE_URL = '';

export const api = {
  async fetch(url, options = {}) {
    const session = await authService.getSession();
    const token = session?.access_token;
    const user = session?.user;

    const headers = {
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${BASE_URL}${url}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      // Handle unauthorized (maybe logout)
      // authService.logout();
    }

    return response;
  },

  async get(url) {
    return this.fetch(url, { method: 'GET' });
  },

  async post(url, body) {
    return this.fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  },

  async put(url, body) {
    return this.fetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  },

  async delete(url) {
    return this.fetch(url, { method: 'DELETE' });
  }
};
