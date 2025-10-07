# GnyanSetu User Authentication Service

## 🚀 Django-Based Authentication Microservice

A comprehensive, production-ready Django authentication service for the GnyanSetu platform. Built with Django 4.2.16, Django REST Framework, JWT authentication, and modern Python practices.

## 📋 Service Overview

**Port**: 8002  
**Purpose**: Complete user authentication, registration, session management, and JWT token handling  
**Architecture**: Django + DRF + JWT + MongoDB integration  
**Server**: Daphne ASGI for production, Django dev server for development  

## ✨ Key Features

### 🔐 Authentication & Authorization
- **JWT Authentication** with access/refresh token system
- **Custom User Model** with extended profile information
- **Email Verification** system with token-based confirmation
- **Password Reset** functionality with secure token handling
- **Session Management** with device tracking and security monitoring
- **Admin Interface** for user management

### 🏗️ Architecture & Technical Stack
- **Django 4.2.16** - Modern Python web framework
- **Django REST Framework** - Powerful API development
- **JWT Tokens** - Secure stateless authentication
- **Custom User Model** - Extended user information
- **MongoDB Integration** - NoSQL database support
- **ASGI Support** - Production-ready async server
- **CORS Configuration** - Microservice communication
- **Comprehensive Validation** - Input validation and security

### 📊 User Management
- **User Registration** with email verification
- **Profile Management** with educational preferences
- **Learning Analytics** - Progress tracking and statistics
- **Admin Dashboard** - Complete user administration
- **Session Tracking** - Security and device management

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+
- Virtual environment at `e:\Project\venv`
- Django 4.2.16 and dependencies installed

### Quick Start

1. **Development Server** (Standard Django):
   ```bash
   start_user_service.bat
   ```

2. **Production Server** (Daphne ASGI):
   ```bash
   start_user_service_asgi.bat
   ```

### Manual Setup
```bash
# Activate virtual environment
cd e:\Project
venv\Scripts\activate

# Navigate to service directory
cd Gnyansetu_Updated_Architecture\microservices\user-service-django

# Install dependencies (if needed)
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Start development server
python manage.py runserver 8002

# OR start production ASGI server
daphne -b 0.0.0.0 -p 8002 user_service.asgi:application
```

## 🌐 API Endpoints

### 🏠 General Endpoints
- `GET /` - API root with service information
- `GET /api/v1/health/` - Health check endpoint
- `GET /admin/` - Django admin interface

### 🔑 Authentication Endpoints
- `POST /api/v1/auth/register/` - User registration
- `POST /api/v1/auth/login/` - User login (JWT tokens)
- `POST /api/v1/auth/refresh/` - Refresh JWT token
- `POST /api/v1/auth/logout/` - User logout
- `POST /api/v1/auth/verify-email/` - Email verification
- `POST /api/v1/auth/resend-verification/` - Resend verification email

### 🔄 Password Management
- `POST /api/v1/auth/password-reset/` - Request password reset
- `POST /api/v1/auth/password-reset-confirm/` - Confirm password reset
- `POST /api/v1/auth/change-password/` - Change password (authenticated)

### 👤 User Management
- `GET /api/v1/profile/` - Get user profile
- `PUT /api/v1/profile/` - Update user profile
- `PATCH /api/v1/profile/` - Partial profile update
- `GET /api/v1/profile/details/` - Detailed profile information
- `GET /api/v1/sessions/` - List active user sessions

### 👨‍💼 Admin Endpoints
- `GET /api/v1/admin/users/` - List all users (admin only)
- `GET /api/v1/admin/users/{id}/` - Get user details (admin only)
- `PUT /api/v1/admin/users/{id}/` - Update user (admin only)
- `DELETE /api/v1/admin/users/{id}/` - Delete user (admin only)

## 📋 API Request Examples

### User Registration
```json
POST /api/v1/auth/register/
{
    "email": "user@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "password": "securepassword123",
    "password_confirm": "securepassword123",
    "phone_number": "+1234567890",
    "preferred_language": "en",
    "learning_level": "intermediate",
    "terms_accepted": true
}
```

### User Login
```json
POST /api/v1/auth/login/
{
    "email": "user@example.com",
    "password": "securepassword123"
}
```

### Response Example
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": "uuid-here",
        "email": "user@example.com",
        "full_name": "Test User",
        "is_verified": false,
        "learning_level": "intermediate"
    }
}
```

## 🗄️ Database Models

### User Model
- Custom Django user model extending AbstractUser
- UUID primary key for security
- Email-based authentication
- Extended profile fields (phone, bio, learning preferences)
- Email verification system
- Activity tracking

### UserProfile Model
- One-to-one relationship with User
- Educational background information
- Learning preferences and goals
- Progress tracking (lessons, study time, streaks)
- Notification settings
- Privacy settings

### UserSession Model
- Session tracking for security
- IP address and device information
- Login/logout timestamps
- Suspicious activity detection
- Failed attempt tracking

## 🔧 Configuration

### Environment Variables
- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (default: True)
- `DATABASE_URL` - Database connection string
- `EMAIL_BACKEND` - Email backend configuration

### Django Settings
- **JWT Configuration**: 1-hour access tokens, 7-day refresh tokens
- **CORS Settings**: Configured for GnyanSetu microservices
- **REST Framework**: JSON API with JWT authentication
- **Password Validation**: Strong password requirements
- **Logging**: Comprehensive logging configuration

## 🛡️ Security Features

### Authentication Security
- **JWT Tokens** with rotation and blacklisting
- **Argon2 Password Hashing** for maximum security
- **Email Verification** before account activation
- **Password Strength Validation** with Django validators
- **Session Tracking** with device fingerprinting

### API Security
- **CORS Configuration** for microservice communication
- **CSRF Protection** for web interface
- **Input Validation** on all endpoints
- **Permission Classes** for role-based access
- **Rate Limiting** ready for production

## 📊 Monitoring & Logging

### Health Monitoring
- Health check endpoint for service monitoring
- System check integration
- Database connectivity verification

### Logging Configuration
- File-based logging system
- Error tracking and debugging
- User activity logging
- Security event logging

## 🚀 Production Deployment

### ASGI Server (Recommended)
```bash
# Enable Daphne in settings
# Run with Daphne
daphne -b 0.0.0.0 -p 8002 user_service.asgi:application
```

### Environment Setup
- Virtual environment activation
- Database migrations
- Static file collection (if needed)
- Environment variable configuration

## 🔄 Integration with GnyanSetu Services

### Service Communication
- **API Gateway**: Port 8000 (routes requests)
- **Dashboard**: Port 3001 (frontend client)
- **Lesson Service**: Port 8003 (lesson management)
- **Teaching Service**: Port 8004 (real-time teaching)
- **PDF Service**: Port 8001 (document processing)
- **Landing Page**: Port 3000 (public interface)

### CORS Configuration
All GnyanSetu services are pre-configured for seamless communication.

## 📝 Development Notes

### Custom User Model
- Extends Django's AbstractUser
- Uses email as username field
- UUID primary key for scalability
- Extended with educational preferences

### JWT Implementation
- Access tokens: 1 hour lifetime
- Refresh tokens: 7 days lifetime
- Automatic token rotation
- Blacklist support for logout

### API Design
- RESTful design principles
- Comprehensive error handling
- Consistent response format
- Detailed API documentation ready

## 🎯 Future Enhancements

- [ ] API documentation with drf-spectacular
- [ ] Rate limiting implementation
- [ ] OAuth2 social authentication
- [ ] Two-factor authentication (2FA)
- [ ] Advanced analytics dashboard
- [ ] Email templates and styling
- [ ] Automated testing suite
- [ ] Docker containerization

## 📞 Support

For issues or questions related to the GnyanSetu User Authentication Service, please refer to the main GnyanSetu project documentation or contact the development team.

---

**GnyanSetu User Authentication Service** - Building the future of AI-powered education with secure, scalable authentication. 🎓✨