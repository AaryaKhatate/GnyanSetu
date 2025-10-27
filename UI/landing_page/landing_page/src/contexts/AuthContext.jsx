// Authentication Context for Landing Page
import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// API Configuration - Use API Gateway
const API_BASE_URL = "http://localhost:8000";

// API Helper function
const apiCall = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultOptions = {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    credentials: "include",
  };

  const token = localStorage.getItem('gnyansetu_auth_token');
  if (token && !defaultOptions.headers.Authorization) {
    defaultOptions.headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(url, { ...defaultOptions, ...options });
  
  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage;
    try {
      const errorData = JSON.parse(errorText);
      errorMessage = errorData.error || "An error occurred";
    } catch {
      errorMessage = errorText || "An error occurred";
    }
    throw new Error(errorMessage);
  }

  const data = await response.json();
  return data;
};

class LandingAuthAPI {
  // Authentication methods
  static async login(email, password) {
    return await apiCall("/api/auth/login/", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  static async signup(name, email, password, confirm_password) {
    return await apiCall("/api/auth/signup/", {
      method: "POST",
      body: JSON.stringify({ name, email, password, confirm_password }),
    });
  }

  static async forgotPassword(email) {
    return await apiCall("/api/auth/forgot-password/", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  }

  static async logout() {
    return await apiCall("/api/auth/logout/", {
      method: "POST",
    });
  }

  static async verifyToken() {
    return await apiCall("/api/auth/verify-token/");
  }

  static async getProfile() {
    return await apiCall("/api/auth/profile/");
  }
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('gnyansetu_auth_token');
      if (token) {
        const response = await LandingAuthAPI.verifyToken();
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

  const login = async (email, password) => {
    setLoading(true);
    setError(null);
    try {
      const response = await LandingAuthAPI.login(email, password);
      console.log('� Login API Response:', response);
      
      // Django returns { access, refresh, user } - check for access token
      if (response.access || response.token) {
        const token = response.access || response.token; // Support both formats
        const userId = response.user?.id || response.user?._id;
        const userEmail = response.user?.email;
        const userName = response.user?.full_name || response.user?.name;
        
        console.log('� Extracted data:', { token: token?.substring(0, 20) + '...', userId, userEmail, userName });
        
        // Store auth tokens
        localStorage.setItem('gnyansetu_auth_token', token);
        localStorage.setItem('access_token', token);
        if (response.refresh) {
          localStorage.setItem('refresh_token', response.refresh);
        }
        
        // Store user data for dashboard
        if (userId) {
          sessionStorage.setItem('userId', userId);
          localStorage.setItem('userId', userId);
          console.log(' User ID stored in storage:', userId);
        } else {
          console.error(' No userId found in response:', response);
        }
        
        if (userEmail) {
          sessionStorage.setItem('userEmail', userEmail);
          localStorage.setItem('userEmail', userEmail);
        }
        
        if (userName) {
          sessionStorage.setItem('userName', userName);
          localStorage.setItem('userName', userName);
        }
        
        // Store complete user object
        localStorage.setItem('user', JSON.stringify(response.user));
        
        setUser({
          id: userId,
          email: userEmail,
          name: userName,
          role: response.user?.role
        });
        
        console.log(' Login successful - redirecting to dashboard');
        return response;
      } else {
        console.error(' No access token in response:', response);
        throw new Error('Invalid response format from server');
      }
    } catch (error) {
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const signup = async (name, email, password, confirmPassword) => {
    setLoading(true);
    setError(null);
    try {
      const response = await LandingAuthAPI.signup(name, email, password, confirmPassword);
      if (response.success || response.token) {
        const token = response.token;
        localStorage.setItem('gnyansetu_auth_token', token);
        
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
      await LandingAuthAPI.logout();
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
      const response = await LandingAuthAPI.forgotPassword(email);
      return response;
    } catch (error) {
      setError(error.message);
      throw error;
    }
  };

  // Redirect to dashboard if logged in
  const redirectToDashboard = () => {
    window.location.href = 'http://localhost:3001';
  };

  const value = {
    user,
    loading,
    error,
    login,
    signup,
    logout,
    forgotPassword,
    redirectToDashboard,
    isLoggedIn: !!user,
    refreshAuth: checkAuthStatus
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Export the API class for direct use if needed
export { LandingAuthAPI };