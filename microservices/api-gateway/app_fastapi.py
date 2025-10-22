"""
API Gateway - Central routing and load balancing for microservices (FastAPI)
Port: 8000
Routes requests to User Service (8002), Lesson Service (8003), Teaching Service (8004), Quiz & Notes Service (8005)
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import httpx
from fastapi import FastAPI, Request, Response, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="GnyanSetu API Gateway",
    description="Central routing and load balancing for microservices",
    version="2.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service Registry - Define all microservices
SERVICES = {
    'user-service': {
        'url': 'http://localhost:8002',
        'health': '/api/v1/health',
        'routes': ['/api/v1/auth', '/api/auth', '/api/users', '/api/v1/users']
    },
    'lesson-service': {
        'url': 'http://localhost:8003',
        'health': '/health',
        'routes': ['/api/generate-lesson', '/api/lessons', '/upload_pdf', '/api/upload']
    },
    'teaching-service': {
        'url': 'http://localhost:8004',
        'health': '/health',
        'routes': ['/api/conversations', '/api/teaching', '/ws/teaching']
    },
    'quiz-notes-service': {
        'url': 'http://localhost:8005',
        'health': '/health',
        'routes': ['/api/quiz', '/api/notes']
    }
}

# Create HTTP client with longer timeout for file operations
http_client = httpx.AsyncClient(timeout=180.0)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_service_for_route(path: str):
    """Determine which service should handle the request based on the path."""
    for service_name, service_config in SERVICES.items():
        for route_prefix in service_config['routes']:
            if path.startswith(route_prefix):
                return service_name, service_config
    return None, None

async def check_service_health(service_name: str, service_config: Dict) -> bool:
    """Check if a service is healthy."""
    try:
        health_url = f"{service_config['url']}{service_config['health']}"
        response = await http_client.get(health_url, timeout=5.0)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Health check failed for {service_name}: {e}")
        return False

async def proxy_request(
    target_url: str,
    method: str,
    headers: Dict = None,
    json_data: Any = None,
    form_data: Dict = None,
    files: Dict = None,
    params: Dict = None
) -> Response:
    """Proxy request to target service."""
    try:
        # Prepare headers - exclude host and content-length
        proxy_headers = {}
        if headers:
            excluded_headers = {'host', 'content-length', 'content-type'}
            for key, value in headers.items():
                if key.lower() not in excluded_headers:
                    proxy_headers[key] = value
        
        # Make request based on method
        if method == 'GET':
            response = await http_client.get(target_url, headers=proxy_headers, params=params)
        elif method == 'POST':
            if files:
                # Multipart form data with files
                response = await http_client.post(target_url, headers=proxy_headers, data=form_data, files=files)
            elif form_data:
                # Form data without files
                response = await http_client.post(target_url, headers=proxy_headers, data=form_data)
            else:
                # JSON data
                response = await http_client.post(target_url, headers=proxy_headers, json=json_data)
        elif method == 'PUT':
            response = await http_client.put(target_url, headers=proxy_headers, json=json_data)
        elif method == 'DELETE':
            response = await http_client.delete(target_url, headers=proxy_headers)
        else:
            raise HTTPException(status_code=405, detail="Method not supported")
        
        # Return response with original status code and headers
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get('content-type', 'application/json')
        )
        
    except httpx.TimeoutException:
        logger.error(f"Request timeout to {target_url}")
        raise HTTPException(status_code=504, detail="Service timeout")
    except httpx.ConnectError:
        logger.error(f"Connection error to {target_url}")
        raise HTTPException(status_code=503, detail="Service unavailable")
    except Exception as e:
        logger.error(f"Error proxying request to {target_url}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ============================================================================
# MIDDLEWARE
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and add custom headers."""
    logger.info(f"{request.method} {request.url.path} from {request.client.host}")
    
    response = await call_next(request)
    
    # Add custom headers
    response.headers['X-Gateway'] = 'GnyanSetu-API-Gateway'
    response.headers['X-Timestamp'] = datetime.utcnow().isoformat()
    
    return response

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get('/health')
async def gateway_health():
    """API Gateway health check and service status."""
    service_status = {}
    
    for service_name, service_config in SERVICES.items():
        service_status[service_name] = {
            'url': service_config['url'],
            'healthy': await check_service_health(service_name, service_config)
        }
    
    overall_health = any(status['healthy'] for status in service_status.values())
    
    return {
        'gateway': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': service_status,
        'overall_health': 'healthy' if overall_health else 'degraded'
    }

# ============================================================================
# AUTHENTICATION ROUTES (User Service Integration)
# ============================================================================

@app.post('/api/auth/login/')
async def auth_login(request: Request):
    """Proxy login request to User Service."""
    logger.info(f"POST /api/auth/login/ received from {request.client.host}")
    target_url = f"{SERVICES['user-service']['url']}/api/auth/login/"
    
    data = await request.json()
    logger.info(f"Proxying login request for: {data.get('email', 'unknown')}")
    
    return await proxy_request(target_url, 'POST', dict(request.headers), json_data=data)

@app.post('/api/auth/signup/')
@app.post('/api/auth/register/')
async def auth_signup(request: Request):
    """Proxy signup request to User Service."""
    target_url = f"{SERVICES['user-service']['url']}/api/auth/register/"
    
    data = await request.json()
    # Remove confirm_password if present (frontend validation)
    if 'confirm_password' in data:
        data.pop('confirm_password')
    
    logger.info(f"Proxying signup request for: {data.get('email', 'unknown')}")
    return await proxy_request(target_url, 'POST', dict(request.headers), json_data=data)

@app.post('/api/auth/forgot-password/')
async def auth_forgot_password(request: Request):
    """Proxy forgot password request to User Service."""
    target_url = f"{SERVICES['user-service']['url']}/api/auth/forgot-password/"
    data = await request.json()
    
    logger.info(f"Proxying forgot password request for: {data.get('email', 'unknown')}")
    return await proxy_request(target_url, 'POST', dict(request.headers), json_data=data)

@app.post('/api/auth/reset-password/')
async def auth_reset_password(request: Request):
    """Proxy reset password request to User Service."""
    target_url = f"{SERVICES['user-service']['url']}/api/auth/reset-password/"
    data = await request.json()
    
    logger.info("Proxying reset password request")
    return await proxy_request(target_url, 'POST', dict(request.headers), json_data=data)

@app.post('/api/auth/logout/')
async def auth_logout(request: Request):
    """Proxy logout request to User Service."""
    target_url = f"{SERVICES['user-service']['url']}/api/auth/logout/"
    
    logger.info("Proxying logout request")
    return await proxy_request(target_url, 'POST', dict(request.headers))

@app.post('/api/auth/google/')
@app.post('/api/v1/auth/google/')
async def auth_google_oauth(request: Request):
    """Proxy Google OAuth request to User Service."""
    target_url = f"{SERVICES['user-service']['url']}/api/auth/google/"
    
    data = await request.json()
    logger.info("Proxying Google OAuth request")
    return await proxy_request(target_url, 'POST', dict(request.headers), json_data=data)

@app.get('/api/auth/profile/')
@app.put('/api/auth/profile/')
async def auth_profile(request: Request):
    """Proxy profile requests to User Service."""
    target_url = f"{SERVICES['user-service']['url']}/api/auth/profile/"
    
    data = None
    if request.method == 'PUT':
        data = await request.json()
    
    logger.info(f"Proxying profile {request.method} request")
    return await proxy_request(target_url, request.method, dict(request.headers), json_data=data)

@app.get('/api/auth/verify-token/')
async def auth_verify_token(request: Request):
    """Proxy token verification to User Service."""
    target_url = f"{SERVICES['user-service']['url']}/api/auth/verify-token"
    
    logger.info("Proxying token verification request")
    return await proxy_request(target_url, 'GET', dict(request.headers))

# ============================================================================
# LESSON SERVICE ROUTES
# ============================================================================

@app.post('/api/generate-lesson/')
@app.post('/upload_pdf/')
@app.post('/api/upload')
async def upload_pdf(
    request: Request,
    pdf_file: UploadFile = File(...),
    user_id: str = Form(...),
    student_id: Optional[str] = Form(None),
    learning_level: Optional[str] = Form('beginner')
):
    """Proxy PDF upload to Lesson Service."""
    logger.info(f"POST /api/generate-lesson/ received from {request.client.host}")
    target_url = f"{SERVICES['lesson-service']['url']}/api/generate-lesson/"
    
    # Prepare file for upload
    files = {'pdf_file': (pdf_file.filename, await pdf_file.read(), pdf_file.content_type)}
    
    # Prepare form data
    form_data = {
        'user_id': user_id,
        'learning_level': learning_level
    }
    if student_id:
        form_data['student_id'] = student_id
    
    logger.info(f"File received: {pdf_file.filename}, User: {user_id}")
    logger.info("Proxying PDF upload request to Lesson Service")
    
    return await proxy_request(target_url, 'POST', dict(request.headers), form_data=form_data, files=files)

# ============================================================================
# CONVERSATIONS ROUTES (Teaching Service)
# ============================================================================

@app.get('/api/conversations/')
async def get_conversations(request: Request):
    """Proxy get conversations request to Teaching Service."""
    teaching_service = SERVICES.get('teaching-service')
    target_url = f"{teaching_service['url']}/api/conversations/"
    
    params = dict(request.query_params)
    return await proxy_request(target_url, 'GET', dict(request.headers), params=params)

@app.post('/api/conversations/')
async def create_conversation(request: Request):
    """Proxy create conversation request to Teaching Service."""
    teaching_service = SERVICES.get('teaching-service')
    create_url = f"{teaching_service['url']}/api/conversations/create/"
    
    data = await request.json()
    return await proxy_request(create_url, 'POST', dict(request.headers), json_data=data)

@app.delete('/api/conversations/{conversation_id}')
@app.delete('/api/conversations/{conversation_id}/delete/')
async def delete_conversation(conversation_id: str, request: Request):
    """Proxy conversation deletion to Teaching Service."""
    teaching_service = SERVICES.get('teaching-service')
    target_url = f"{teaching_service['url']}/api/conversations/{conversation_id}/delete/"
    
    return await proxy_request(target_url, 'DELETE', dict(request.headers))

# ============================================================================
# GENERIC PROXY ROUTES
# ============================================================================

@app.api_route('/api/{path:path}', methods=['GET', 'POST', 'PUT', 'DELETE'])
async def generic_proxy(path: str, request: Request):
    """Generic proxy for all other API routes."""
    full_path = f"/api/{path}"
    service_name, service_config = get_service_for_route(full_path)
    
    if not service_name:
        raise HTTPException(status_code=404, detail=f"No service found for path: {full_path}")
    
    # Check if service is healthy
    if not await check_service_health(service_name, service_config):
        raise HTTPException(status_code=503, detail=f"Service {service_name} is unavailable")
    
    target_url = f"{service_config['url']}{full_path}"
    
    # Handle request data
    data = None
    files = None
    form_data = None
    params = dict(request.query_params) if request.query_params else None
    
    if request.method in ['POST', 'PUT']:
        content_type = request.headers.get('content-type', '')
        if 'multipart/form-data' in content_type:
            # Handle file uploads
            form = await request.form()
            files = {}
            form_data = {}
            for key, value in form.items():
                if hasattr(value, 'read'):  # It's a file
                    files[key] = (value.filename, await value.read(), value.content_type)
                else:
                    form_data[key] = value
        else:
            # Handle JSON data
            try:
                data = await request.json()
            except:
                data = None
    
    logger.info(f"Proxying {request.method} request to {service_name}: {full_path}")
    return await proxy_request(target_url, request.method, dict(request.headers), json_data=data, form_data=form_data, files=files, params=params)

# ============================================================================
# SERVICE DISCOVERY
# ============================================================================

@app.get('/api/services')
async def list_services(request: Request):
    """List all available services and their status."""
    service_info = {}
    
    for service_name, service_config in SERVICES.items():
        service_info[service_name] = {
            'url': service_config['url'],
            'routes': service_config['routes'],
            'healthy': await check_service_health(service_name, service_config)
        }
    
    return {
        'services': service_info,
        'gateway_url': str(request.base_url).rstrip('/')
    }

@app.get('/api/services/{service_name}/health')
async def check_specific_service_health_endpoint(service_name: str):
    """Check health of a specific service."""
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")
    
    service_config = SERVICES[service_name]
    is_healthy = await check_service_health(service_name, service_config)
    
    return {
        'service': service_name,
        'url': service_config['url'],
        'healthy': is_healthy,
        'timestamp': datetime.utcnow().isoformat()
    }

# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info("=" * 60)
    logger.info("Starting GnyanSetu API Gateway (FastAPI) on port 8000")
    logger.info("=" * 60)
    logger.info("Service Registry:")
    for service_name, config in SERVICES.items():
        logger.info(f"  {service_name}: {config['url']} -> {config['routes']}")
    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """Close HTTP client on shutdown."""
    await http_client.aclose()
    logger.info("API Gateway shutdown complete")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        "app_fastapi:app",
        host='0.0.0.0',
        port=8000,
        reload=True,
        log_level="info"
    )
