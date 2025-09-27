# User Management / Authentication Service
# Port: 8002
# Database: MongoDB Collection - users

import os
import logging
import jwt
import bcrypt
import json
import smtplib
import secrets
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from functools import wraps
import pika

# Initialize Flask app
app = Flask(__name__)
CORS(app, 
     origins=["http://localhost:3001", "http://localhost:8000", "http://localhost:3000"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'gnyansetu-secret-key-2024')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')

# MongoDB Configuration
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client.Gnyansetu_Users
    users_collection = db.users
    password_resets = db.password_resets
    sessions = db.sessions
    logger.info("Connected to MongoDB for User Service")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    users_collection = None
    password_resets = None
    sessions = None

# RabbitMQ Configuration for event publishing
try:
    rabbitmq_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    rabbitmq_channel = rabbitmq_connection.channel()
    
    # Declare exchanges for events
    rabbitmq_channel.exchange_declare(exchange='user_events', exchange_type='topic')
    logger.info("Connected to RabbitMQ for User Service")
except Exception as e:
    logger.error(f"Failed to connect to RabbitMQ: {e}")
    rabbitmq_connection = None
    rabbitmq_channel = None

def publish_event(event_type, data):
    """Publish event to RabbitMQ."""
    if rabbitmq_channel:
        try:
            message = {
                'event_type': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'service': 'user-service',
                'data': data
            }
            
            rabbitmq_channel.basic_publish(
                exchange='user_events',
                routing_key=f'user.{event_type}',
                body=json.dumps(message)
            )
            logger.info(f"Published event: {event_type}")
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")

def hash_password(password):
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_jwt_token(user_data):
    """Generate JWT token for user."""
    payload = {
        'user_id': str(user_data['_id']),
        'email': user_data['email'],
        'name': user_data['name'],
        'role': user_data.get('role', 'student'),
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token):
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization header required'}), 401
        
        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)
        
        if payload is None:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.user = payload
        return f(*args, **kwargs)
    
    return decorated_function

def send_password_reset_email(email, reset_token):
    """Send password reset email."""
    try:
        # This is a simple implementation - in production, use proper email service
        reset_link = f"http://localhost:3001/reset-password?token={reset_token}"
        
        msg = f"""
        Hello,
        
        You requested a password reset for your GnyanSetu account.
        
        Click the following link to reset your password:
        {reset_link}
        
        This link will expire in 1 hour.
        
        If you didn't request this reset, please ignore this email.
        
        Best regards,
        GnyanSetu Team
        """
        
        logger.info(f"Password reset email would be sent to {email} with token {reset_token}")
        logger.info(f"Reset link: {reset_link}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
        return False

@app.route('/', methods=['GET'])
def root():
    """Root endpoint."""
    return jsonify({
        'service': 'GnyanSetu User Management Service',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': [
            '/health',
            '/api/auth/signup/',
            '/api/auth/login/',
            '/api/auth/profile/',
            '/api/auth/forgot-password/',
            '/api/auth/reset-password'
        ]
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'service': 'user-service',
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'mongodb_connected': users_collection is not None,
        'rabbitmq_connected': rabbitmq_channel is not None
    })

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if data.get(field) is None:
                return jsonify({'error': f'{field} is required'}), 400
        
        name = data['name'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # Validate email format
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400

        if users_collection is None:
            return jsonify({'error': 'Database not available'}), 500
        
        # Check if user already exists
        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create new user
        user_data = {
            'name': name,
            'email': email,
            'password_hash': hash_password(password),
            'role': 'student',  # Default role
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_active': True,
            'email_verified': False,
            'last_login': None,
            'profile': {
                'avatar': None,
                'bio': '',
                'preferences': {}
            }
        }
        
        result = users_collection.insert_one(user_data)
        user_data['_id'] = result.inserted_id
        
        # Generate JWT token
        token = generate_jwt_token(user_data)
        
        # Publish user registered event
        publish_event('registered', {
            'user_id': str(user_data['_id']),
            'email': email,
            'name': name,
            'role': 'student'
        })
        
        # Return user data (without password hash)
        user_data.pop('password_hash', None)
        user_data['_id'] = str(user_data['_id'])
        
        logger.info(f"New user registered: {email}")
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': user_data,
            'token': token
        }), 201
        
    except Exception as e:
        logger.error(f"Error in register: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/auth/signup/', methods=['POST'])
def signup():
    """Signup new user (alias for register)."""
    try:
        data = request.get_json()
        
        # Handle different field names from frontend
        if 'confirm_password' in data:
            if data['password'] != data['confirm_password']:
                return jsonify({'error': 'Passwords do not match'}), 400
        
        # Validate required fields
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if data.get(field) is None:
                return jsonify({'error': f'{field} is required'}), 400
        
        name = data['name'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # Validate email format
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400

        if users_collection is None:
            return jsonify({'error': 'Database not available'}), 500
        
        # Check if user already exists
        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create new user
        user_data = {
            'name': name,
            'email': email,
            'password_hash': hash_password(password),
            'role': 'student',  # Default role
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_active': True,
            'email_verified': False,
            'last_login': None,
            'profile': {
                'avatar': None,
                'bio': '',
                'preferences': {}
            }
        }
        
        result = users_collection.insert_one(user_data)
        user_data['_id'] = result.inserted_id
        
        # Generate JWT token
        token = generate_jwt_token(user_data)
        
        # Publish user registered event
        publish_event('registered', {
            'user_id': str(user_data['_id']),
            'email': email,
            'name': name,
            'role': 'student'
        })
        
        # Return user data (without password hash)
        user_data.pop('password_hash', None)
        user_data['_id'] = str(user_data['_id'])
        
        logger.info(f"New user signed up: {email}")
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': user_data,
            'token': token
        }), 201
        
    except Exception as e:
        logger.error(f"Error in signup: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/auth/login/', methods=['POST'])
def login():
    """User login."""
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        if users_collection is None:
            return jsonify({'error': 'Database not available'}), 500
        
        # Find user by email
        user = users_collection.find_one({'email': email})
        if user is None:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Verify password
        if verify_password(password, user['password_hash']) is False:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check if user is active
        if user.get('is_active', True) is False:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Update last login
        users_collection.update_one(
            {'_id': user['_id']},
            {'$set': {'last_login': datetime.utcnow()}}
        )
        
        # Generate JWT token
        token = generate_jwt_token(user)
        
        # Publish user login event
        publish_event('login', {
            'user_id': str(user['_id']),
            'email': email,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Return user data (without password hash)
        user.pop('password_hash', None)
        user['_id'] = str(user['_id'])
        
        logger.info(f"User logged in: {email}")
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user,
            'token': token
        })
        
    except Exception as e:
        logger.error(f"Error in login: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """User logout."""
    try:
        user_id = request.user['user_id']
        
        # Publish user logout event
        publish_event('logout', {
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        logger.info(f"User logged out: {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        })
        
    except Exception as e:
        logger.error(f"Error in logout: {e}")
        return jsonify({'error': 'Logout failed'}), 500

@app.route('/api/auth/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get user profile."""
    try:
        user_id = request.user['user_id']

        if users_collection is None:
            return jsonify({'error': 'Database not available'}), 500
        
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if user is None:
            return jsonify({'error': 'User not found'}), 404
        
        # Return user data (without password hash)
        user.pop('password_hash', None)
        user['_id'] = str(user['_id'])
        
        return jsonify({
            'success': True,
            'user': user
        })
        
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        return jsonify({'error': 'Failed to get profile'}), 500

@app.route('/api/auth/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update user profile."""
    try:
        user_id = request.user['user_id']
        data = request.get_json()

        if users_collection is None:
            return jsonify({'error': 'Database not available'}), 500
        
        # Fields that can be updated
        updatable_fields = ['name', 'profile']
        update_data = {}
        
        for field in updatable_fields:
            if field in data:
                update_data[field] = data[field]
        
        if update_data is None:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        update_data['updated_at'] = datetime.utcnow()
        
        result = users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )
        
        if result.modified_count == 0:
            return jsonify({'error': 'User not found or no changes made'}), 404
        
        # Get updated user
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        user.pop('password_hash', None)
        user['_id'] = str(user['_id'])
        
        # Publish profile updated event
        publish_event('profile_updated', {
            'user_id': user_id,
            'updated_fields': list(update_data.keys())
        })
        
        logger.info(f"Profile updated for user: {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': user
        })
        
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Handle forgot password request."""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if email is None:
            return jsonify({'error': 'Email is required'}), 400
        
        if not users_collection or not password_resets:
            return jsonify({'error': 'Database not available'}), 500
        
        # Check if user exists
        user = users_collection.find_one({'email': email})
        if user is None:
            # Don't reveal if email exists or not for security
            return jsonify({
                'success': True,
                'message': 'If the email exists, a reset link has been sent'
            })
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        
        # Store reset token with expiration
        reset_data = {
            'user_id': user['_id'],
            'email': email,
            'token': reset_token,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=1),
            'used': False
        }
        
        password_resets.insert_one(reset_data)
        
        # Send reset email
        send_password_reset_email(email, reset_token)
        
        # Publish password reset event
        publish_event('password_reset_requested', {
            'user_id': str(user['_id']),
            'email': email
        })
        
        logger.info(f"Password reset requested for: {email}")
        
        return jsonify({
            'success': True,
            'message': 'If the email exists, a reset link has been sent'
        })
        
    except Exception as e:
        logger.error(f"Error in forgot password: {e}")
        return jsonify({'error': 'Failed to process request'}), 500

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """Reset password using token."""
    try:
        data = request.get_json()
        token = data.get('token', '')
        new_password = data.get('password', '')
        
        if not token or not new_password:
            return jsonify({'error': 'Token and new password are required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        if not users_collection or not password_resets:
            return jsonify({'error': 'Database not available'}), 500
        
        # Find valid reset token
        reset_request = password_resets.find_one({
            'token': token,
            'used': False,
            'expires_at': {'$gt': datetime.utcnow()}
        })

        if reset_request is None:
            return jsonify({'error': 'Invalid or expired reset token'}), 400
        
        # Update password
        new_password_hash = hash_password(new_password)
        
        result = users_collection.update_one(
            {'_id': reset_request['user_id']},
            {
                '$set': {
                    'password_hash': new_password_hash,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            return jsonify({'error': 'User not found'}), 404
        
        # Mark reset token as used
        password_resets.update_one(
            {'_id': reset_request['_id']},
            {'$set': {'used': True, 'used_at': datetime.utcnow()}}
        )
        
        # Publish password reset event
        publish_event('password_reset_completed', {
            'user_id': str(reset_request['user_id']),
            'email': reset_request['email']
        })
        
        logger.info(f"Password reset completed for: {reset_request['email']}")
        
        return jsonify({
            'success': True,
            'message': 'Password reset successful'
        })
        
    except Exception as e:
        logger.error(f"Error in reset password: {e}")
        return jsonify({'error': 'Failed to reset password'}), 500

@app.route('/api/auth/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change password for authenticated user."""
    try:
        user_id = request.user['user_id']
        data = request.get_json()
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current and new passwords are required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters long'}), 400

        if users_collection is None:
            return jsonify({'error': 'Database not available'}), 500
        
        # Get user
        user = users_collection.find_one({'_id': ObjectId(user_id)})
        if user is None:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify current password
        if verify_password(current_password, user['password_hash']) is False:
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Update password
        new_password_hash = hash_password(new_password)
        
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'password_hash': new_password_hash,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        # Publish password changed event
        publish_event('password_changed', {
            'user_id': user_id,
            'email': user['email']
        })
        
        logger.info(f"Password changed for user: {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        return jsonify({'error': 'Failed to change password'}), 500

@app.route('/api/auth/verify-token', methods=['GET'])
@require_auth
def verify_token():
    """Verify if token is valid."""
    return jsonify({
        'success': True,
        'user': request.user
    })

@app.route('/api/users', methods=['GET'])
@require_auth
def get_users():
    """Get users list (admin only)."""
    try:
        # Check if user has admin role
        if request.user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403

        if users_collection is None:
            return jsonify({'error': 'Database not available'}), 500
        
        users = []
        for user in users_collection.find({}, {'password_hash': 0}).sort('created_at', -1).limit(100):
            user['_id'] = str(user['_id'])
            users.append(user)
        
        return jsonify({
            'success': True,
            'users': users
        })
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({'error': 'Failed to get users'}), 500

# Google OAuth Routes
@app.route('/accounts/google/login/', methods=['GET'])
def google_oauth_login():
    """Redirect to Google OAuth."""
    try:
        # This is a simplified version - in production, use proper OAuth flow
        google_auth_url = "https://accounts.google.com/oauth/authorize"
        redirect_uri = request.host_url + "accounts/google/callback/"
        
        # Build OAuth URL
        oauth_url = f"{google_auth_url}?client_id={GOOGLE_CLIENT_ID}&redirect_uri={redirect_uri}&scope=email%20profile&response_type=code"
        
        return jsonify({
            'success': True,
            'auth_url': oauth_url,
            'message': 'Redirect to Google OAuth'
        })
        
    except Exception as e:
        logger.error(f"Error in Google OAuth: {e}")
        return jsonify({'error': 'Google OAuth not configured'}), 500

@app.route('/accounts/google/callback/', methods=['GET'])
def google_oauth_callback():
    """Handle Google OAuth callback."""
    try:
        # This is a placeholder for Google OAuth callback
        # In production, implement proper OAuth token exchange
        return jsonify({
            'success': False,
            'message': 'Google OAuth not fully configured',
            'redirect': 'http://localhost:3001'
        })
        
    except Exception as e:
        logger.error(f"Error in Google OAuth callback: {e}")
        return jsonify({'error': 'OAuth callback failed'}), 500

@app.route('/api/auth/google/', methods=['POST'])
def google_auth():
    """Handle Google OAuth token verification."""
    try:
        data = request.get_json()
        google_token = data.get('token', '')
        
        if google_token is None:
            return jsonify({'error': 'Google token required'}), 400
        
        # This is a placeholder - implement proper Google token verification
        return jsonify({
            'success': False,
            'message': 'Google OAuth integration not fully configured',
            'error': 'Please use email/password signup for now'
        }), 501
        
    except Exception as e:
        logger.error(f"Error in Google auth: {e}")
        return jsonify({'error': 'Google authentication failed'}), 500

if __name__ == '__main__':
    logger.info("Starting User Management Service on port 8002")
    app.run(host='0.0.0.0', port=8002, debug=True)