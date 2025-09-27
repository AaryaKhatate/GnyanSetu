// Authentication Context for React Frontend
import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

class UserServiceAPI {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async makeRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };

    const token = localStorage.getItem('gnyansetu_auth_token');
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `HTTP error! status: ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error(`API Error (${endpoint}):`, error);
      throw error;
    }
  }

  async register(userData) {
    return await this.makeRequest('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  }

  async login(credentials) {
    return await this.makeRequest('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    });
  }

  async logout() {
    return await this.makeRequest('/api/auth/logout', {
      method: 'POST'
    });
  }

  async getProfile() {
    return await this.makeRequest('/api/auth/profile');
  }

  async verifyToken() {
    return await this.makeRequest('/api/auth/verify-token');
  }

  async forgotPassword(email) {
    return await this.makeRequest('/api/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email })
    });
  }
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const userAPI = new UserServiceAPI();

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('gnyansetu_auth_token');
      if (token) {
        const response = await userAPI.verifyToken();
        if (response.success) {
          setUser({
            id: response.user.user_id,
            email: response.user.email,
            name: response.user.name,
            role: response.user.role
          });
        } else {
          localStorage.removeItem('gnyansetu_auth_token');
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('gnyansetu_auth_token');
      setError(null); // Don't show error for initial auth check
    } finally {
      setLoading(false);
    }
  };

  const login = async (credentials) => {
    setLoading(true);
    setError(null);
    try {
      const response = await userAPI.login(credentials);
      if (response.success) {
        localStorage.setItem('gnyansetu_auth_token', response.token);
        setUser({
          id: response.user._id,
          email: response.user.email,
          name: response.user.name,
          role: response.user.role
        });
        return response;
      }
    } catch (error) {
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    setLoading(true);
    setError(null);
    try {
      const response = await userAPI.register(userData);
      if (response.success) {
        localStorage.setItem('gnyansetu_auth_token', response.token);
        setUser({
          id: response.user._id,
          email: response.user.email,
          name: response.user.name,
          role: response.user.role
        });
        return response;
      }
    } catch (error) {
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await userAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('gnyansetu_auth_token');
      setUser(null);
      setLoading(false);
    }
  };

  const forgotPassword = async (email) => {
    setError(null);
    try {
      const response = await userAPI.forgotPassword(email);
      return response;
    } catch (error) {
      setError(error.message);
      throw error;
    }
  };

  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    forgotPassword,
    isLoggedIn: !!user,
    refreshAuth: checkAuthStatus
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};