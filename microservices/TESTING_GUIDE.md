# 🧪 API Gateway Testing Guide

## Overview
This guide will help you test the complete authentication flow from the frontend through the API Gateway to the User Management microservice.

## 🏗️ Architecture Overview
```
Frontend (React)    →    API Gateway    →    User Service
Port 3000/3001           Port 8000           Port 8002
                    →    PDF Service
                         Port 8001
```

## 🚀 Step-by-Step Testing

### Step 1: Start All Services
```bash
# Navigate to microservices directory
cd e:\Project\Gnyansetu_Updated_Architecture\microservices

# Start all services (this will open multiple terminal windows)
start_project.bat
```

**Expected Output:**
- API Gateway running on http://localhost:8000
- PDF Service running on http://localhost:8001  
- User Service running on http://localhost:8002

### Step 2: Verify Services are Running
```bash
# Run the automated test suite
test_gateway.bat
```

**What this tests:**
- ✅ API Gateway health check
- ✅ Individual service health checks
- ✅ User registration through gateway
- ✅ User login through gateway
- ✅ Authenticated requests
- ✅ PDF service integration
- ✅ Error handling

### Step 3: Test Frontend Integration

#### Landing Page Testing (Port 3000)
1. Navigate to the landing page directory:
   ```bash
   cd e:\Project\Gnyansetu_Updated_Architecture\virtual_teacher_project\UI\landing_page
   ```

2. Start the landing page:
   ```bash
   npm start
   ```

3. Open browser to http://localhost:3000

4. Test authentication flow:
   - Click "Sign Up" 
   - Fill in user details
   - Verify registration goes through API Gateway to User Service
   - Try logging in with the same credentials

#### Dashboard Testing (Port 3001)
1. Navigate to the dashboard directory:
   ```bash
   cd e:\Project\Gnyansetu_Updated_Architecture\virtual_teacher_project\UI\Dashboard\Dashboard
   ```

2. Start the dashboard:
   ```bash
   npm start
   ```

3. Open browser to http://localhost:3001

4. Test authentication:
   - Try logging in with the user created on landing page
   - Verify JWT token is properly handled
   - Check if user profile loads correctly

## 🔍 API Endpoints Available

### Through API Gateway (http://localhost:8000)

#### Authentication Routes
- `POST /api/auth/signup/` - User registration
- `POST /api/auth/login/` - User login  
- `GET /api/auth/profile/` - Get user profile (requires auth)
- `PUT /api/auth/profile/` - Update user profile (requires auth)
- `POST /api/auth/change-password/` - Change password (requires auth)
- `GET /api/auth/health` - User service health check

#### PDF Routes  
- `GET /api/pdf/health` - PDF service health check
- `POST /api/pdf/upload/` - Upload PDF (requires auth)
- `GET /api/pdf/documents/` - List user documents (requires auth)
- `GET /api/pdf/documents/<id>/` - Get specific document (requires auth)
- `DELETE /api/pdf/documents/<id>/` - Delete document (requires auth)

#### Gateway Routes
- `GET /health` - API Gateway health check
- `GET /services` - List registered services

## 🧪 Manual API Testing

### Test User Registration
```bash
curl -X POST http://localhost:8000/api/auth/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### Test User Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com", 
    "password": "TestPassword123!"
  }'
```

### Test Authenticated Request
```bash
# Use the token from login response
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

## 🐛 Troubleshooting

### Services Not Starting
1. Check if ports are already in use:
   ```bash
   netstat -ano | findstr ":8000"
   netstat -ano | findstr ":8001" 
   netstat -ano | findstr ":8002"
   ```

2. Ensure virtual environment is activated:
   ```bash
   cd e:\Project\Gnyansetu_Updated_Architecture\virtual_teacher_project
   venv\Scripts\activate
   ```

3. Install missing dependencies:
   ```bash
   pip install flask flask-cors requests pymongo pika bcrypt pyjwt
   ```

### MongoDB Connection Issues
1. Check if MongoDB is running:
   ```bash
   # Check MongoDB service
   sc query MongoDB
   ```

2. Verify MongoDB connection string in service configs

### Frontend Issues  
1. Clear browser cache and cookies
2. Check browser developer console for errors
3. Verify API base URLs are pointing to gateway (localhost:8000)

### Authentication Errors
1. Check JWT token format and expiration
2. Verify CORS headers are properly set
3. Check service-to-service communication

## 📊 Expected Test Results

### Successful Gateway Test Output:
```
🧪 Starting API Gateway Test Suite
📅 Test Time: 2024-01-XX XX:XX:XX
🌐 Gateway URL: http://localhost:8000

✅ PASS Gateway Health
✅ PASS Service Health  
✅ PASS User Registration
✅ PASS User Login
✅ PASS Authenticated Request
✅ PASS PDF Integration

📊 Results: 6/6 tests passed
🎉 All tests passed! API Gateway is working correctly.
```

## 🔄 Next Steps After Testing

Once authentication is working properly:

1. **Create AI Lesson Service** - Next microservice for lesson generation
2. **Create Quiz Service** - Handle quiz creation and management  
3. **Create Real-time Service** - WebSocket handling for interactive features
4. **Create Analytics Service** - Track user progress and engagement
5. **Add Docker Containerization** - Package services for deployment
6. **Setup Service Discovery** - Automatic service registration
7. **Add API Rate Limiting** - Protect against abuse
8. **Implement Service Monitoring** - Health checks and metrics

## 📝 Notes

- All services use MongoDB with separate collections
- JWT tokens are used for authentication
- RabbitMQ is used for inter-service communication
- Services are designed to be stateless and horizontally scalable
- API Gateway handles CORS and request routing
- Each service has its own health check endpoint

Remember: Test each service individually before testing the complete flow!