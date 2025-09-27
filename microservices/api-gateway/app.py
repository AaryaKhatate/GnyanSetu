# API Gateway - Central routing and load balancing for microservices
# Port: 8000
# Routes requests to PDF Service (8001), User Service (8002), AI Service (8003), etc.

import os
import logging
import asyncio
import aiohttp
import json
from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=["http://localhost:3001", "http://localhost:8000", "http://localhost:3000"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service Registry - Define all microservices
SERVICES = {
    'pdf-service': {
        'url': 'http://localhost:8001',
        'health': '/health',
        'routes': ['/api/upload', '/api/documents']
    },
    'user-service': {
        'url': 'http://localhost:8002', 
        'health': '/health',
        'routes': ['/api/auth', '/api/users']
    },
    'ai-service': {
        'url': 'http://localhost:8003',
        'health': '/health', 
        'routes': ['/api/lessons', '/api/generate']
    },
    'quiz-service': {
        'url': 'http://localhost:8004',
        'health': '/health',
        'routes': ['/api/quizzes', '/api/notes']
    },
    'realtime-service': {
        'url': 'http://localhost:8005',
        'health': '/health',
        'routes': ['/api/sessions', '/ws']
    },
    'analytics-service': {
        'url': 'http://localhost:8006',
        'health': '/health',
        'routes': ['/api/analytics', '/api/progress']
    }
}

def get_service_for_route(path):
    """Determine which service should handle the request based on the path."""
    for service_name, service_config in SERVICES.items():
        for route_prefix in service_config['routes']:
            if path.startswith(route_prefix):
                return service_name, service_config
    return None, None

def check_service_health(service_name, service_config):
    """Check if a service is healthy."""
    try:
        health_url = f"{service_config['url']}{service_config['health']}"
        response = requests.get(health_url, timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Health check failed for {service_name}: {e}")
        return False

def proxy_request(target_url, method, headers=None, data=None, files=None):
    """Proxy request to target service."""
    try:
        # Prepare headers
        proxy_headers = {}
        if headers:
            # Forward important headers, exclude some that should not be forwarded
            excluded_headers = {'host', 'content-length'}
            for key, value in headers.items():
                if key.lower() not in excluded_headers:
                    proxy_headers[key] = value
        
        # Make request to target service
        if method == 'GET':
            response = requests.get(target_url, headers=proxy_headers, params=request.args, timeout=30)
        elif method == 'POST':
            if files:
                response = requests.post(target_url, headers={k: v for k, v in proxy_headers.items() if k.lower() != 'content-type'}, 
                                       data=data, files=files, timeout=30)
            else:
                response = requests.post(target_url, headers=proxy_headers, json=data, timeout=30)
        elif method == 'PUT':
            response = requests.put(target_url, headers=proxy_headers, json=data, timeout=30)
        elif method == 'DELETE':
            response = requests.delete(target_url, headers=proxy_headers, timeout=30)
        else:
            return jsonify({'error': 'Method not supported'}), 405
        
        # Return response
        return Response(
            response.content,
            status=response.status_code,
            headers=dict(response.headers)
        )
        
    except requests.exceptions.Timeout:
        logger.error(f"Request timeout to {target_url}")
        return jsonify({'error': 'Service timeout'}), 504
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error to {target_url}")
        return jsonify({'error': 'Service unavailable'}), 503
    except Exception as e:
        logger.error(f"Error proxying request to {target_url}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def gateway_health():
    """API Gateway health check and service status."""
    service_status = {}
    
    for service_name, service_config in SERVICES.items():
        service_status[service_name] = {
            'url': service_config['url'],
            'healthy': check_service_health(service_name, service_config)
        }
    
    overall_health = any(status['healthy'] for status in service_status.values())
    
    return jsonify({
        'gateway': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': service_status,
        'overall_health': 'healthy' if overall_health else 'degraded'
    })

# ============================================================================
# AUTHENTICATION ROUTES (User Service Integration)
# ============================================================================

@app.route('/api/auth/login/', methods=['POST'])
def auth_login():
    """Proxy login request to User Service."""
    target_url = f"{SERVICES['user-service']['url']}/api/auth/login"
    data = request.get_json()
    
    logger.info(f"Proxying login request for: {data.get('email', 'unknown')}")
    return proxy_request(target_url, 'POST', request.headers, data)

@app.route('/api/auth/signup/', methods=['POST'])
def auth_signup():
    """Proxy signup request to User Service."""
    target_url = f"{SERVICES['user-service']['url']}/api/auth/register"
    data = request.get_json()
    
    # Transform the request to match User Service format
    if data and 'confirm_password' in data:
        # Remove confirm_password as User Service doesn't expect it
        # Frontend should validate password confirmation
        data.pop('confirm_password', None)
    
    logger.info(f"Proxying signup request for: {data.get('email', 'unknown')}")
    return proxy_request(target_url, 'POST', request.headers, data)

@app.route('/api/auth/forgot-password/', methods=['POST'])
def auth_forgot_password():
    """Proxy forgot password request to User Service."""
    target_url = f"{SERVICES['user-service']['url']}/api/auth/forgot-password"
    data = request.get_json()
    
    logger.info(f"Proxying forgot password request for: {data.get('email', 'unknown')}")
    return proxy_request(target_url, 'POST', request.headers, data)

@app.route('/api/auth/reset-password/', methods=['POST'])
def auth_reset_password():
    """Proxy reset password request to User Service."""
    target_url = f"{SERVICES['user-service']['url']}/api/auth/reset-password"
    data = request.get_json()
    
    logger.info("Proxying reset password request")
    return proxy_request(target_url, 'POST', request.headers, data)

@app.route('/api/auth/logout/', methods=['POST'])
def auth_logout():
    """Proxy logout request to User Service."""
    target_url = f"{SERVICES['user-service']['url']}/api/auth/logout"
    
    logger.info("Proxying logout request")
    return proxy_request(target_url, 'POST', request.headers)

@app.route('/api/auth/profile/', methods=['GET', 'PUT'])
def auth_profile():
    """Proxy profile requests to User Service."""
    target_url = f"{SERVICES['user-service']['url']}/api/auth/profile"
    data = request.get_json() if request.method == 'PUT' else None
    
    logger.info(f"Proxying profile {request.method} request")
    return proxy_request(target_url, request.method, request.headers, data)

@app.route('/api/auth/verify-token/', methods=['GET'])
def auth_verify_token():
    """Proxy token verification to User Service."""
    target_url = f"{SERVICES['user-service']['url']}/api/auth/verify-token"
    
    logger.info("Proxying token verification request")
    return proxy_request(target_url, 'GET', request.headers)

# ============================================================================
# PDF SERVICE ROUTES
# ============================================================================

@app.route('/upload_pdf/', methods=['POST'])
@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    """Proxy PDF upload to PDF Service."""
    target_url = f"{SERVICES['pdf-service']['url']}/api/upload"
    
    # Handle file upload
    files = {}
    if 'pdf_file' in request.files:
        pdf_file = request.files['pdf_file']
        files['pdf_file'] = (pdf_file.filename, pdf_file.stream, pdf_file.content_type)
    
    logger.info("Proxying PDF upload request")
    return proxy_request(target_url, 'POST', request.headers, request.form.to_dict(), files)

@app.route('/api/documents', methods=['GET'])
@app.route('/api/documents/<document_id>', methods=['GET', 'DELETE'])
def pdf_documents(document_id=None):
    """Proxy PDF document requests to PDF Service."""
    if document_id:
        target_url = f"{SERVICES['pdf-service']['url']}/api/documents/{document_id}"
    else:
        target_url = f"{SERVICES['pdf-service']['url']}/api/documents"
    
    logger.info(f"Proxying PDF documents {request.method} request")
    return proxy_request(target_url, request.method, request.headers)

# ============================================================================
# GENERIC PROXY ROUTES
# ============================================================================

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def generic_proxy(path):
    """Generic proxy for all other API routes."""
    full_path = f"/api/{path}"
    service_name, service_config = get_service_for_route(full_path)
    
    if not service_name:
        return jsonify({'error': f'No service found for path: {full_path}'}), 404
    
    # Check if service is healthy
    if not check_service_health(service_name, service_config):
        return jsonify({'error': f'Service {service_name} is unavailable'}), 503
    
    target_url = f"{service_config['url']}{full_path}"
    
    # Handle request data
    data = None
    files = None
    
    if request.method in ['POST', 'PUT']:
        if request.content_type and 'multipart/form-data' in request.content_type:
            files = {}
            for key, file in request.files.items():
                files[key] = (file.filename, file.stream, file.content_type)
            data = request.form.to_dict()
        else:
            data = request.get_json()
    
    logger.info(f"Proxying {request.method} request to {service_name}: {full_path}")
    return proxy_request(target_url, request.method, request.headers, data, files)

# ============================================================================
# SERVICE DISCOVERY AND LOAD BALANCING
# ============================================================================

@app.route('/api/services', methods=['GET'])
def list_services():
    """List all available services and their status."""
    service_info = {}
    
    for service_name, service_config in SERVICES.items():
        service_info[service_name] = {
            'url': service_config['url'],
            'routes': service_config['routes'],
            'healthy': check_service_health(service_name, service_config)
        }
    
    return jsonify({
        'services': service_info,
        'gateway_url': request.host_url.rstrip('/')
    })

@app.route('/api/services/<service_name>/health', methods=['GET'])
def check_specific_service_health(service_name):
    """Check health of a specific service."""
    if service_name not in SERVICES:
        return jsonify({'error': 'Service not found'}), 404
    
    service_config = SERVICES[service_name]
    is_healthy = check_service_health(service_name, service_config)
    
    return jsonify({
        'service': service_name,
        'url': service_config['url'],
        'healthy': is_healthy,
        'timestamp': datetime.utcnow().isoformat()
    })

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(503)
def service_unavailable(error):
    return jsonify({'error': 'Service temporarily unavailable'}), 503

# ============================================================================
# MIDDLEWARE
# ============================================================================

@app.before_request
def log_request():
    """Log all incoming requests."""
    logger.info(f"{request.method} {request.path} from {request.remote_addr}")

@app.after_request
def after_request(response):
    """Add common headers to all responses."""
    response.headers['X-Gateway'] = 'GnyanSetu-API-Gateway'
    response.headers['X-Timestamp'] = datetime.utcnow().isoformat()
    return response

if __name__ == '__main__':
    logger.info("Starting API Gateway on port 8000")
    logger.info("Service Registry:")
    for service_name, config in SERVICES.items():
        logger.info(f"  {service_name}: {config['url']} -> {config['routes']}")
    
    app.run(host='0.0.0.0', port=8000, debug=True)