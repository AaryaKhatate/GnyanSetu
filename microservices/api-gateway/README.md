# API Gateway

Central routing and load balancing service for the GnyanSetu microservices architecture. Acts as a single entry point for all client requests and routes them to appropriate microservices.

##  **Gateway Responsibilities**

- **Request Routing**: Route requests to appropriate microservices based on URL patterns
- **Load Balancing**: Distribute requests across multiple service instances (future)
- **Authentication Proxying**: Handle auth requests and forward to User Management Service
- **Service Discovery**: Maintain registry of available microservices
- **Health Monitoring**: Check health status of all registered services
- **Error Handling**: Provide consistent error responses across services
- **Request/Response Transformation**: Adapt requests between different service formats
- **CORS Management**: Handle cross-origin requests centrally

##  **Service Registry**

| Service | Port | URL | Routes |
|---------|------|-----|--------|
| **API Gateway** | 8000 | http://localhost:8000 | All routes |
| **PDF Service** | 8001 | http://localhost:8001 | `/api/upload`, `/api/documents` |
| **User Service** | 8002 | http://localhost:8002 | `/api/auth`, `/api/users` |
| **AI Service** | 8003 | http://localhost:8003 | `/api/lessons`, `/api/generate` |
| **Quiz Service** | 8004 | http://localhost:8004 | `/api/quizzes`, `/api/notes` |
| **Realtime Service** | 8005 | http://localhost:8005 | `/api/sessions`, `/ws` |
| **Analytics Service** | 8006 | http://localhost:8006 | `/api/analytics`, `/api/progress` |

## � **API Endpoints**

### Gateway Health & Service Discovery

#### Gateway Health Check
```http
GET /health
```

**Response:**
```json
{
  "gateway": "healthy",
  "timestamp": "2024-01-01T10:00:00Z",
  "services": {
    "pdf-service": {
      "url": "http://localhost:8001",
      "healthy": true
    },
    "user-service": {
      "url": "http://localhost:8002", 
      "healthy": true
    }
  },
  "overall_health": "healthy"
}
```

#### List All Services
```http
GET /api/services
```

**Response:**
```json
{
  "services": {
    "pdf-service": {
      "url": "http://localhost:8001",
      "routes": ["/api/upload", "/api/documents"],
      "healthy": true
    },
    "user-service": {
      "url": "http://localhost:8002",
      "routes": ["/api/auth", "/api/users"],
      "healthy": true
    }
  },
  "gateway_url": "http://localhost:8000"
}
```

#### Check Specific Service Health
```http
GET /api/services/{service_name}/health
```

**Response:**
```json
{
  "service": "user-service",
  "url": "http://localhost:8002",
  "healthy": true,
  "timestamp": "2024-01-01T10:00:00Z"
}
```

### Authentication Routes (Proxied to User Service)

#### Login
```http
POST /api/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

#### Signup/Register
```http
POST /api/auth/signup/
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com", 
  "password": "password123",
  "confirm_password": "password123"
}
```

#### Forgot Password
```http
POST /api/auth/forgot-password/
Content-Type: application/json

{
  "email": "user@example.com"
}
```

#### Logout
```http
POST /api/auth/logout/
Authorization: Bearer <jwt_token>
```

#### Get/Update Profile
```http
GET /api/auth/profile/
PUT /api/auth/profile/
Authorization: Bearer <jwt_token>
```

#### Verify Token
```http
GET /api/auth/verify-token/
Authorization: Bearer <jwt_token>
```

### PDF Service Routes (Proxied)

#### Upload PDF
```http
POST /upload_pdf/
POST /api/upload
Content-Type: multipart/form-data

Body: pdf_file (file)
```

#### Get Documents
```http
GET /api/documents
GET /api/documents/{document_id}
DELETE /api/documents/{document_id}
```

### Generic Proxy Routes

All other API routes are automatically proxied to the appropriate service based on the URL pattern:

```http
GET|POST|PUT|DELETE /api/{path}
```

The gateway will:
1. Determine which service should handle the request
2. Check if the service is healthy
3. Proxy the request to the service
4. Return the response to the client

## � **Request Flow**

```
Client Request
     ↓
API Gateway (Port 8000)
     ↓
Route Analysis (/api/auth/* → User Service)
     ↓
Service Health Check
     ↓
Request Proxying
     ↓
Target Microservice (Port 8001-8006)
     ↓
Response Processing
     ↓
Client Response
```

## � **Error Handling**

The gateway provides consistent error responses:

- **404**: Endpoint not found or no service registered for route
- **503**: Target service is unavailable or unhealthy
- **504**: Request timeout (service took too long to respond)
- **500**: Internal gateway error

## � **Frontend Integration**

### Landing Page Integration

The landing page now connects to the API Gateway instead of individual services:

```javascript
// Before (Direct service connection)
const API_BASE_URL = "http://localhost:8001";

// After (API Gateway)
const API_BASE_URL = "http://localhost:8000";

// All auth requests now go through the gateway
const authAPI = {
  login: (email, password) =>
    apiCall("/api/auth/login/", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  // ... other methods
};
```

### Dashboard Integration

The React dashboard should also use the API Gateway:

```javascript
// Update API base URL to use gateway
const API_BASE_URL = "http://localhost:8000";

// All service calls go through gateway
const pdfUpload = async (file) => {
  const formData = new FormData();
  formData.append('pdf_file', file);
  
  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: 'POST',
    body: formData
  });
  
  return response.json();
};
```

## � **Setup & Installation**

### Prerequisites
- Python 3.10+
- All microservices should be running on their respective ports

### Installation Steps

1. **Navigate to gateway directory:**
   ```bash
   cd microservices/api-gateway
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env  # Edit as needed
   ```

4. **Start the gateway:**
   ```bash
   python app.py
   ```

The gateway will start on port 8000 and begin routing requests to registered services.

##  **Testing**

### Test Gateway Health
```bash
curl http://localhost:8000/health
```

### Test Authentication Flow
```bash
# Register user
curl -X POST http://localhost:8000/api/auth/signup/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"testpass123","confirm_password":"testpass123"}'

# Login user  
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'
```

### Test Service Discovery
```bash
# List all services
curl http://localhost:8000/api/services

# Check user service health
curl http://localhost:8000/api/services/user-service/health
```

##  **Configuration**

Environment variables in `.env`:

```env
# Gateway Configuration
GATEWAY_PORT=8000
GATEWAY_HOST=0.0.0.0
DEBUG=true

# Service URLs (can be customized)
PDF_SERVICE_URL=http://localhost:8001
USER_SERVICE_URL=http://localhost:8002
AI_SERVICE_URL=http://localhost:8003

# Timeout Configuration
REQUEST_TIMEOUT=30
HEALTH_CHECK_TIMEOUT=5

# CORS Configuration
CORS_ORIGINS=http://localhost:3001,http://localhost:8000,http://localhost:3000
```

## � **Monitoring & Logging**

- **Request Logging**: All requests are logged with method, path, and source IP
- **Service Health Monitoring**: Regular health checks for all registered services
- **Error Tracking**: Detailed error logging for failed requests and service issues
- **Response Headers**: Each response includes gateway identification headers

## � **Security Features**

- **CORS Protection**: Configurable cross-origin request handling
- **Header Filtering**: Removes sensitive headers when proxying requests
- **Token Forwarding**: Automatically forwards authentication tokens to services
- **Rate Limiting**: TODO - Implement rate limiting for API protection
- **Service Authentication**: TODO - Add service-to-service authentication

## � **Service Health Monitoring**

The gateway continuously monitors all registered services:

- **Health Check Endpoint**: Each service must implement `/health`
- **Automatic Failover**: Requests to unhealthy services return 503 errors
- **Service Discovery**: Dynamic service registration (future enhancement)
- **Circuit Breaker**: TODO - Implement circuit breaker pattern

## � **Next Steps**

1. **Start the API Gateway** using the startup script
2. **Verify all services** are healthy via `/health` endpoint
3. **Test authentication flow** from landing page
4. **Update frontend** to use gateway URLs instead of direct service URLs
5. **Proceed to create AI Lesson Service** (next microservice)

## � **Service Communication Flow**

```
Landing Page (Port 3000)
         ↓
API Gateway (Port 8000)
         ↓
┌─────────────────────────────────┐
│  Service Router & Load Balancer │
└─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│     User Service (Port 8002)    │ ← Authentication
│     PDF Service (Port 8001)     │ ← File Upload
│     AI Service (Port 8003)      │ ← Lesson Generation
│     Quiz Service (Port 8004)    │ ← Quiz Creation
│     Analytics Service (Port 8006)│ ← Usage Tracking
└─────────────────────────────────┘
```

---

**Port**: 8000  
**Purpose**: Central API routing and service orchestration  
**Key Features**: Request routing, service discovery, health monitoring, authentication proxying