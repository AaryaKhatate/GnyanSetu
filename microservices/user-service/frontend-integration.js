// User Service API Client for Frontend Integration
// File: microservices/user-service/frontend-integration.js

class UserServiceAPI {
    constructor(baseURL = 'http://localhost:8002') {
        this.baseURL = baseURL;
        this.token = this.getStoredToken();
    }

    // Token management
    getStoredToken() {
        return localStorage.getItem('gnyansetu_auth_token');
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('gnyansetu_auth_token', token);
    }

    removeToken() {
        this.token = null;
        localStorage.removeItem('gnyansetu_auth_token');
    }

    // HTTP request helper
    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // Add authorization header if token exists
        if (this.token && !config.headers.Authorization) {
            config.headers.Authorization = `Bearer ${this.token}`;
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

    // Authentication methods
    async register(userData) {
        const response = await this.makeRequest('/api/auth/register/', {
            method: 'POST',
            body: JSON.stringify(userData)
        });

        if (response.success && response.token) {
            this.setToken(response.token);
        }

        return response;
    }

    async login(credentials) {
        const response = await this.makeRequest('/api/auth/login/', {
            method: 'POST',
            body: JSON.stringify(credentials)
        });

        if (response.success && response.token) {
            this.setToken(response.token);
        }

        return response;
    }

    async logout() {
        try {
            await this.makeRequest('/api/auth/logout', {
                method: 'POST'
            });
        } finally {
            this.removeToken();
        }
    }

    // Profile methods
    async getProfile() {
        return await this.makeRequest('/api/auth/profile');
    }

    async updateProfile(profileData) {
        return await this.makeRequest('/api/auth/profile', {
            method: 'PUT',
            body: JSON.stringify(profileData)
        });
    }

    // Password methods
    async changePassword(passwordData) {
        return await this.makeRequest('/api/auth/change-password', {
            method: 'POST',
            body: JSON.stringify(passwordData)
        });
    }

    async forgotPassword(email) {
        return await this.makeRequest('/api/auth/forgot-password', {
            method: 'POST',
            body: JSON.stringify({ email })
        });
    }

    async resetPassword(token, password) {
        return await this.makeRequest('/api/auth/reset-password', {
            method: 'POST',
            body: JSON.stringify({ token, password })
        });
    }

    // Token verification
    async verifyToken() {
        try {
            return await this.makeRequest('/api/auth/verify-token');
        } catch (error) {
            this.removeToken();
            throw error;
        }
    }

    // Utility methods
    isLoggedIn() {
        return !!this.token;
    }

    isTokenExpired() {
        if (!this.token) return true;

        try {
            const payload = JSON.parse(atob(this.token.split('.')[1]));
            return payload.exp < Date.now() / 1000;
        } catch {
            return true;
        }
    }

    getCurrentUser() {
        if (!this.token) return null;

        try {
            const payload = JSON.parse(atob(this.token.split('.')[1]));
            return {
                id: payload.user_id,
                email: payload.email,
                name: payload.name,
                role: payload.role
            };
        } catch {
            return null;
        }
    }

    // Health check
    async healthCheck() {
        return await this.makeRequest('/health', {
            headers: {} // No auth needed for health check
        });
    }
}

// React Hook for User Service
function useUserService() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const userAPI = useRef(new UserServiceAPI());

    useEffect(() => {
        checkAuthStatus();
    }, []);

    const checkAuthStatus = async () => {
        setLoading(true);
        try {
            if (userAPI.current.isLoggedIn() && !userAPI.current.isTokenExpired()) {
                const response = await userAPI.current.verifyToken();
                if (response.success) {
                    setUser(response.user);
                }
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    const login = async (credentials) => {
        setLoading(true);
        setError(null);
        try {
            const response = await userAPI.current.login(credentials);
            if (response.success) {
                setUser(response.user);
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
            const response = await userAPI.current.register(userData);
            if (response.success) {
                setUser(response.user);
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
            await userAPI.current.logout();
            setUser(null);
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            setLoading(false);
        }
    };

    const updateProfile = async (profileData) => {
        setLoading(true);
        setError(null);
        try {
            const response = await userAPI.current.updateProfile(profileData);
            if (response.success) {
                setUser(response.user);
                return response;
            }
        } catch (error) {
            setError(error.message);
            throw error;
        } finally {
            setLoading(false);
        }
    };

    return {
        user,
        loading,
        error,
        login,
        register,
        logout,
        updateProfile,
        userAPI: userAPI.current,
        isLoggedIn: !!user,
        refreshAuth: checkAuthStatus
    };
}

// Export for use in React components
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { UserServiceAPI, useUserService };
}

// Example usage in React components:
/*
// Login Component
function LoginForm() {
    const { login, loading, error } = useUserService();
    const [credentials, setCredentials] = useState({ email: '', password: '' });

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await login(credentials);
            // Redirect to dashboard
        } catch (error) {
            // Error is handled by the hook
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <input
                type="email"
                value={credentials.email}
                onChange={(e) => setCredentials({...credentials, email: e.target.value})}
                placeholder="Email"
                required
            />
            <input
                type="password"
                value={credentials.password}
                onChange={(e) => setCredentials({...credentials, password: e.target.value})}
                placeholder="Password"
                required
            />
            <button type="submit" disabled={loading}>
                {loading ? 'Logging in...' : 'Login'}
            </button>
            {error && <div className="error">{error}</div>}
        </form>
    );
}

// Protected Route Component
function ProtectedRoute({ children }) {
    const { user, loading } = useUserService();

    if (loading) return <div>Loading...</div>;
    if (!user) return <Navigate to="/login" />;
    
    return children;
}

// Profile Component
function UserProfile() {
    const { user, updateProfile, loading } = useUserService();
    const [profile, setProfile] = useState(user?.profile || {});

    const handleSave = async () => {
        try {
            await updateProfile({ profile });
            alert('Profile updated successfully!');
        } catch (error) {
            alert('Failed to update profile');
        }
    };

    return (
        <div>
            <h2>User Profile</h2>
            <input
                type="text"
                value={profile.bio || ''}
                onChange={(e) => setProfile({...profile, bio: e.target.value})}
                placeholder="Bio"
            />
            <button onClick={handleSave} disabled={loading}>
                {loading ? 'Saving...' : 'Save Profile'}
            </button>
        </div>
    );
}
*/