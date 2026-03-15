
// Custom Auth Service using internal API
const API_URL = '/api/v1';

export const authService = {
  async login(email, password) {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    this.setSession(data);
    return data;
  },

  async signUp(email, password, metadata = {}) {
    const response = await fetch(`${API_URL}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, role: metadata.role || 'cook' }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Signup failed');
    }

    const data = await response.json();
    this.setSession(data);
    return data;
  },

  async logout() {
    localStorage.removeItem('neurosupply_auth_session');
    localStorage.removeItem('neurosupply_demo_user'); // Clean up old demo key if exists
  },

  async getUser() {
    const session = this.getSessionSync();
    if (!session) return null;

    // Optional: Fetch fresh user data from /auth/me
    try {
      const response = await fetch(`${API_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      });
      if (response.ok) {
        return await response.json();
      }
    } catch (e) {
      console.error('Failed to fetch user info:', e);
    }
    
    // Fallback or return cached info if we had any (session usually has token, we need user object)
    return null;
  },

  onAuthStateChange(callback) {
    // Basic implementation for compatibility
    window.addEventListener('storage', (e) => {
      if (e.key === 'neurosupply_auth_session') {
        callback(e.newValue ? 'SIGNED_IN' : 'SIGNED_OUT', this.getSessionSync());
      }
    });
    return { data: { subscription: { unsubscribe: () => {} } } };
  },

  async getSession() {
    return this.getSessionSync();
  },

  getSessionSync() {
    const session = localStorage.getItem('neurosupply_auth_session');
    return session ? JSON.parse(session) : null;
  },

  setSession(data) {
    localStorage.setItem('neurosupply_auth_session', JSON.stringify(data));
  }
};
