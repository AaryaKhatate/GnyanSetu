# User Management / Authentication Service

A comprehensive microservice for user authentication, authorization, and profile management in the GnyanSetu platform.

## 🎯 **Service Responsibilities**

- **User Registration**: Create new user accounts with validation
- **User Authentication**: Login/logout with JWT token generation
- **Password Management**: Change password, forgot/reset password functionality
- **Profile Management**: Update user profiles and preferences
- **Role-Based Access Control**: Student/Admin role management
- **Session Management**: JWT token validation and refresh
- **OAuth Integration**: Google Sign-In support (configurable)
- **Event Publishing**: Publish user events to other services

## 📊 **Database Schema**

### MongoDB Collections

#### `users` Collection
```javascript
{
  "_id": ObjectId("..."),
  "name": "John Doe",
  "email": "john@example.com",
  "password_hash": "$2b$12$...",
  "role": "student", // "student" | "admin"
  "created_at": ISODate("2024-01-01T10:00:00Z"),
  "updated_at": ISODate("2024-01-01T10:00:00Z"),
  "is_active": true,
  "email_verified": false,
  "last_login": ISODate("2024-01-01T10:00:00Z"),
  "profile": {
    "avatar": "https://example.com/avatar.jpg",
    "bio": "Student bio...",
    "preferences": {
      "theme": "dark",
      "notifications": true
    }
  }
}
```

#### `password_resets` Collection
```javascript
{
  "_id": ObjectId("..."),
  "user_id": ObjectId("..."),
  "email": "john@example.com",
  "token": "secure-reset-token",
  "created_at": ISODate("2024-01-01T10:00:00Z"),
  "expires_at": ISODate("2024-01-01T11:00:00Z"),
  "used": false,
  "used_at": null
}
```

#### `sessions` Collection (Optional)
```javascript
{
  "_id": ObjectId("..."),
  "user_id": ObjectId("..."),
  "token": "jwt-token-or-session-id",
  "created_at": ISODate("2024-01-01T10:00:00Z"),
  "expires_at": ISODate("2024-01-02T10:00:00Z"),
  "is_active": true,
  "user_agent": "Mozilla/5.0...",
  "ip_address": "192.168.1.1"
}
```

## 🚀 **API Endpoints**

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "service": "user-service",
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00Z",
  "mongodb_connected": true,
  "rabbitmq_connected": true
}
```

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "User registered successfully",
  "user": {
    "_id": "64f1234567890abcdef12345",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "student",
    "created_at": "2024-01-01T10:00:00Z"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Login User
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "_id": "64f1234567890abcdef12345",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "student",
    "last_login": "2024-01-01T10:00:00Z"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Logout User
```http
POST /api/auth/logout
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "message": "Logout successful"
}
```

### Profile Management

#### Get User Profile
```http
GET /api/auth/profile
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "user": {
    "_id": "64f1234567890abcdef12345",
    "name": "John Doe",
    "email": "john@example.com",
    "role": "student",
    "profile": {
      "avatar": null,
      "bio": "",
      "preferences": {}
    }
  }
}
```

#### Update User Profile
```http
PUT /api/auth/profile
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "John Updated",
  "profile": {
    "bio": "Updated bio",
    "preferences": {
      "theme": "dark"
    }
  }
}
```

### Password Management

#### Forgot Password
```http
POST /api/auth/forgot-password
Content-Type: application/json

{
  "email": "john@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "If the email exists, a reset link has been sent"
}
```

#### Reset Password
```http
POST /api/auth/reset-password
Content-Type: application/json

{
  "token": "secure-reset-token",
  "password": "newpassword123"
}
```

#### Change Password
```http
POST /api/auth/change-password
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "current_password": "oldpassword123",
  "new_password": "newpassword123"
}
```

### Token Management

#### Verify Token
```http
GET /api/auth/verify-token
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "user": {
    "user_id": "64f1234567890abcdef12345",
    "email": "john@example.com",
    "name": "John Doe",
    "role": "student",
    "exp": 1704182400,
    "iat": 1704096000
  }
}
```

### Admin Endpoints

#### Get Users List (Admin Only)
```http
GET /api/users
Authorization: Bearer <admin_jwt_token>
```

## 📡 **Event Publishing**

The service publishes events to RabbitMQ exchange `user_events`:

### User Registered Event
```json
{
  "event_type": "registered",
  "timestamp": "2024-01-01T10:00:00Z",
  "service": "user-service",
  "data": {
    "user_id": "64f1234567890abcdef12345",
    "email": "john@example.com",
    "name": "John Doe",
    "role": "student"
  }
}
```

### User Login Event
```json
{
  "event_type": "login",
  "timestamp": "2024-01-01T10:00:00Z",
  "service": "user-service",
  "data": {
    "user_id": "64f1234567890abcdef12345",
    "email": "john@example.com",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

### Other Events
- `logout` - User logged out
- `profile_updated` - User profile updated
- `password_reset_requested` - Password reset requested
- `password_reset_completed` - Password reset completed
- `password_changed` - Password changed

## 🔧 **Setup & Installation**

### Prerequisites
- Python 3.10+
- MongoDB (running on localhost:27017)
- RabbitMQ (optional, for event publishing)

### Installation Steps

1. **Navigate to service directory:**
   ```bash
   cd microservices/user-service
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env  # Edit as needed
   ```

4. **Start the service:**
   ```bash
   python app.py
   ```

## 🧪 **Testing**

Run the test script to verify service functionality:

```bash
python test_service.py
```

Test endpoints manually:

```bash
# Health check
curl http://localhost:8002/health

# Register user
curl -X POST http://localhost:8002/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"testpass123"}'

# Login user
curl -X POST http://localhost:8002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'
```

## 🐳 **Docker Deployment**

### Build Image
```bash
docker build -t gnyansetu-user-service .
```

### Run Container
```bash
docker run -p 8002:8002 -e MONGO_URI=mongodb://host.docker.internal:27017/ gnyansetu-user-service
```

## ⚙️ **Configuration**

Environment variables in `.env`:

```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=Gnyansetu_Users

# JWT Configuration
JWT_SECRET=gnyansetu-secret-key-2024-ultra-secure
JWT_EXPIRATION_HOURS=24

# OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Service Configuration
SERVICE_PORT=8002
DEBUG=true

# CORS Configuration
CORS_ORIGINS=http://localhost:3001,http://localhost:8000,http://localhost:3000
```

## 🔐 **Security Features**

- **Password Hashing**: Uses bcrypt for secure password storage
- **JWT Tokens**: Stateless authentication with configurable expiration
- **Input Validation**: Validates all user inputs and sanitizes data
- **Rate Limiting**: TODO - Implement rate limiting for auth endpoints
- **CORS Protection**: Configurable CORS origins
- **SQL Injection Prevention**: Uses MongoDB with proper query sanitization
- **Password Reset Security**: Secure tokens with expiration

## 🔄 **Integration with Other Services**

### Frontend Integration
- Register/Login forms send requests to auth endpoints
- Store JWT token in localStorage/sessionStorage
- Include token in Authorization header for protected requests
- Handle token expiration and refresh

### Other Microservices
- **PDF Service**: Validates user tokens for file uploads
- **AI Lesson Service**: Validates user authentication for lesson generation
- **Quiz Service**: Validates user access for quiz operations
- **Analytics Service**: Tracks user behavior and activity

### Event Consumers
Other services can subscribe to user events:
- **Analytics Service**: Track user registration and login patterns
- **Email Service**: Send welcome emails on registration
- **Notification Service**: Send alerts for password changes

## 📈 **Monitoring & Logging**

- **Health Check**: `/health` endpoint for service monitoring
- **Structured Logging**: JSON formatted logs with different levels
- **Event Tracking**: All user actions are logged and published as events
- **Error Handling**: Comprehensive error handling with proper HTTP status codes

## 🚨 **Error Handling**

The service handles various error scenarios:

- **Invalid credentials**: Returns 401 with appropriate message
- **User already exists**: Returns 409 for duplicate email registration
- **Invalid token**: Returns 401 for expired or malformed tokens
- **Missing fields**: Returns 400 with field validation errors
- **Database errors**: Returns 500 with generic error message
- **Rate limiting**: TODO - Returns 429 for too many requests

## 🌐 **Frontend Integration Guide**

### React Integration Example

```javascript
// Auth Context
const AuthContext = createContext();

// API calls
const authAPI = {
  register: async (userData) => {
    const response = await fetch('http://localhost:8002/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    return response.json();
  },
  
  login: async (credentials) => {
    const response = await fetch('http://localhost:8002/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });
    return response.json();
  },
  
  getProfile: async (token) => {
    const response = await fetch('http://localhost:8002/api/auth/profile', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  }
};

// Token management
const TokenManager = {
  setToken: (token) => localStorage.setItem('auth_token', token),
  getToken: () => localStorage.getItem('auth_token'),
  removeToken: () => localStorage.removeItem('auth_token'),
  isValidToken: (token) => {
    // Check token expiration
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp > Date.now() / 1000;
    } catch {
      return false;
    }
  }
};
```

## 📋 **Next Steps**

1. **Test the User Service** by running the startup script
2. **Verify authentication flow** with the frontend
3. **Check database collections** to confirm user storage
4. **Test password reset** functionality
5. **Proceed to AI Lesson Service** creation

---

**Port**: 8002  
**Database**: MongoDB Collections `users`, `password_resets`, `sessions`  
**Events**: RabbitMQ exchange `user_events`  
**Authentication**: JWT-based stateless authentication