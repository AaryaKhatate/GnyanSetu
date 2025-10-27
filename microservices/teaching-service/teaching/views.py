# Teaching Service Views - REST API and WebSocket endpoints
import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View

from .models import LessonService, TeachingSessionModel, UserService

logger = logging.getLogger(__name__)

# ============================================================================
# HEALTH CHECK
# ============================================================================

@csrf_exempt
def health_check(request):
    """Health check endpoint"""
    try:
        return JsonResponse({
            'status': 'healthy',
            'service': 'Teaching Service',
            'version': '2.0.0',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database': 'connected',  # Teaching service uses models.py which connects to MongoDB
            'features': {
                'konva_whiteboard': True,
                'lesson_integration': True,
                'user_profiles': True,
                'real_time_teaching': True,
                'websockets': True
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)

# ============================================================================
# LESSON HISTORY AND MANAGEMENT
# ============================================================================

@csrf_exempt
def get_user_lessons(request):
    """Get all lessons for a user - This is what Dashboard needs for history"""
    try:
        user_id = request.GET.get('user_id', 'dashboard_user')
        
        logger.info(f"Fetching lessons for user: {user_id}")
        
        # Get lessons from the lesson service database
        lessons = LessonService.get_user_lessons(user_id)
        
        # Transform lessons to match conversation format expected by Dashboard
        conversations = []
        for lesson in lessons:
            conversations.append({
                '_id': lesson['_id'],
                'conversation_id': lesson['_id'],
                'id': lesson['_id'],
                'title': lesson.get('lesson_title', 'Untitled Lesson'),
                'timestamp': lesson.get('created_at', datetime.now(timezone.utc).isoformat()),
                'created_at': lesson.get('created_at', datetime.now(timezone.utc).isoformat()),
                'updated_at': lesson.get('updated_at', datetime.now(timezone.utc).isoformat()),
                'user_id': user_id,
                'lesson_type': lesson.get('lesson_type', 'interactive'),
                'status': lesson.get('status', 'generated'),
                'message_count': 0  # Will be updated when teaching starts
            })
        
        logger.info(f"Successfully returning {len(conversations)} lessons as conversations for user {user_id}")
        
        return JsonResponse({
            'conversations': conversations,
            'total': len(conversations),
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f" Error fetching user lessons: {e}")
        return JsonResponse({
            'error': 'Failed to fetch user lessons',
            'details': str(e)
        }, status=500)

@csrf_exempt
def get_lesson_detail(request, lesson_id):
    """Get detailed lesson content for teaching"""
    try:
        logger.info(f"� Fetching lesson detail for: {lesson_id}")
        
        lesson = LessonService.get_lesson_by_id(lesson_id)
        
        if lesson is None:
            return JsonResponse({
                'error': 'Lesson not found'
            }, status=404)
        
        logger.info(f" Found lesson: {lesson.get('lesson_title', 'Untitled')}")
        
        return JsonResponse({
            'lesson': lesson,
            'ready_for_teaching': True
        })
        
    except Exception as e:
        logger.error(f" Error getting lesson detail: {e}")
        return JsonResponse({
            'error': 'Failed to get lesson detail',
            'details': str(e)
        }, status=500)

# ============================================================================
# CONVERSATION ENDPOINTS (Dashboard Integration)
# ============================================================================

@csrf_exempt
def list_conversations(request):
    """List conversations for a user - Routes to lesson history"""
    return get_user_lessons(request)

@csrf_exempt
def create_conversation(request):
    """Create a new conversation/teaching session"""
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
            
        data = json.loads(request.body)
        user_id = data.get('user_id', 'dashboard_user')
        title = data.get('title', 'New Teaching Session')
        lesson_id = data.get('lesson_id', None)
        
        logger.info(f"� Creating new teaching session for user: {user_id}, title: {title}")
        
        # If lesson_id is provided, get lesson content
        lesson_content = {}
        if lesson_id:
            lesson = LessonService.get_lesson_by_id(lesson_id)
            if lesson:
                lesson_content = lesson.get('lesson_content', {})
        
        # Create teaching session
        session_data = {
            'session_name': title,
            'voice_enabled': data.get('voice_enabled', True),
            'whiteboard_enabled': data.get('whiteboard_enabled', True),
            'konva_enabled': data.get('konva_enabled', True),
            'lesson_content': lesson_content
        }
        
        session_id = TeachingSessionModel.create_session(
            lesson_id or "general",
            user_id, 
            session_data
        )
        
        new_conversation = {
            '_id': session_id,
            'conversation_id': session_id,
            'id': session_id,
            'title': title,
            'timestamp': datetime.now(timezone.utc).strftime('%I:%M %p'),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'user_id': user_id,
            'lesson_id': lesson_id,
            'message_count': 0
        }
        
        logger.info(f" Created teaching session: {session_id}")
        
        return JsonResponse(new_conversation, status=201)
        
    except Exception as e:
        logger.error(f" Error creating conversation: {e}")
        return JsonResponse({
            'error': 'Failed to create conversation',
            'details': str(e)
        }, status=500)

@csrf_exempt
def delete_conversation(request, conversation_id):
    """Delete a conversation/teaching session"""
    try:
        if request.method != 'DELETE':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
            
        logger.info(f"Deleting conversation: {conversation_id}")
        
        # Delete teaching session if exists
        if TeachingSessionModel.delete_session(conversation_id):
            logger.info(f"Deleted teaching session: {conversation_id}")
        
        return JsonResponse({
            'success': True,
            'message': f'Conversation {conversation_id} deleted successfully',
            'conversation_id': conversation_id
        })
        
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        return JsonResponse({
            'error': 'Failed to delete conversation',
            'details': str(e)
        }, status=500)

# ============================================================================
# USER PROFILE ENDPOINTS
# ============================================================================

@csrf_exempt
def get_user_profile(request, user_id):
    """Get user profile data for the Dashboard top-right corner"""
    try:
        logger.info(f"� Fetching user profile for: {user_id}")
        
        user_profile = UserService.get_user_profile(user_id)
        
        if user_profile is None:
            return JsonResponse({
                'error': 'User not found'
            }, status=404)
        
        # Get user's lesson statistics
        lessons = LessonService.get_user_lessons(user_id)
        user_profile['lesson_count'] = len(lessons)
        
        # Get user's teaching session statistics
        sessions = TeachingSessionModel.get_user_sessions(user_id)
        user_profile['total_sessions'] = len(sessions)
        
        logger.info(f" Found user profile: {user_profile.get('username', 'Unknown')}")
        
        return JsonResponse({
            'user': user_profile,
            'stats': {
                'total_lessons': user_profile.get('lesson_count', 0),
                'total_sessions': user_profile.get('total_sessions', 0),
                'joined_date': user_profile.get('created_at')
            }
        })
        
    except Exception as e:
        logger.error(f" Error getting user profile: {e}")
        return JsonResponse({
            'error': 'Failed to get user profile',
            'details': str(e)
        }, status=500)

# ============================================================================
# TEACHING SESSION MANAGEMENT
# ============================================================================

@csrf_exempt
def start_teaching_session(request):
    """Start a teaching session with a specific lesson"""
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
            
        data = json.loads(request.body)
        lesson_id = data.get('lesson_id')
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        
        if not lesson_id or not user_id:
            return JsonResponse({
                'error': 'lesson_id and user_id are required'
            }, status=400)
        
        logger.info(f" Starting teaching session for lesson: {lesson_id}, user: {user_id}")
        
        # Get lesson content
        lesson = LessonService.get_lesson_by_id(lesson_id)
        if lesson is None:
            return JsonResponse({
                'error': 'Lesson not found'
            }, status=404)
        
        # Create or update teaching session
        if session_id:
            # Update existing session
            TeachingSessionModel.update_session(session_id, {
                'status': 'active',
                'lesson_content': lesson.get('lesson_content', {}),
                'start_time': datetime.now(timezone.utc)
            })
        else:
            # Create new session
            session_data = {
                'session_name': f"Teaching: {lesson.get('lesson_title', 'Untitled')}",
                'lesson_content': lesson.get('lesson_content', {}),
                'voice_enabled': data.get('voice_enabled', True),
                'whiteboard_enabled': data.get('whiteboard_enabled', True),
                'konva_enabled': data.get('konva_enabled', True)
            }
            session_id = TeachingSessionModel.create_session(lesson_id, user_id, session_data)
        
        return JsonResponse({
            'session_id': session_id,
            'lesson': lesson,
            'status': 'active',
            'websocket_url': f'/ws/teaching/{session_id}/',
            'message': 'Teaching session started successfully'
        }, status=200)
        
    except Exception as e:
        logger.error(f" Error starting teaching session: {e}")
        return JsonResponse({
            'error': 'Failed to start teaching session',
            'details': str(e)
        }, status=500)

@csrf_exempt
def stop_teaching_session(request):
    """Stop a teaching session"""
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
            
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        if not session_id:
            return JsonResponse({
                'error': 'session_id is required'
            }, status=400)
        
        logger.info(f" Stopping teaching session: {session_id}")
        
        # Update session status
        success = TeachingSessionModel.update_session(session_id, {
            'status': 'completed',
            'end_time': datetime.now(timezone.utc)
        })
        
        if success:
            return JsonResponse({
                'session_id': session_id,
                'status': 'completed',
                'message': 'Teaching session stopped successfully'
            })
        else:
            return JsonResponse({
                'error': 'Failed to stop teaching session'
            }, status=400)
            
    except Exception as e:
        logger.error(f" Error stopping teaching session: {e}")
        return JsonResponse({
            'error': 'Failed to stop teaching session',
            'details': str(e)
        }, status=500)

# ============================================================================
# KONVA.JS WHITEBOARD ENDPOINTS
# ============================================================================

@csrf_exempt
def update_konva_state(request):
    """Update Konva.js whiteboard state"""
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
            
        data = json.loads(request.body)
        session_id = data.get('session_id')
        konva_state = data.get('konva_state', {})
        
        if not session_id:
            return JsonResponse({
                'error': 'session_id is required'
            }, status=400)
        
        logger.info(f" Updating Konva state for session: {session_id}")
        
        # Update session with new Konva state
        success = TeachingSessionModel.update_session(session_id, {
            'konva_state': konva_state,
            'last_interaction': datetime.now(timezone.utc)
        })
        
        if success:
            return JsonResponse({
                'session_id': session_id,
                'konva_state': konva_state,
                'message': 'Konva state updated successfully'
            })
        else:
            return JsonResponse({
                'error': 'Failed to update Konva state'
            }, status=400)
            
    except Exception as e:
        logger.error(f" Error updating Konva state: {e}")
        return JsonResponse({
            'error': 'Failed to update Konva state',
            'details': str(e)
        }, status=500)

@csrf_exempt
def get_konva_state(request, session_id):
    """Get Konva.js whiteboard state"""
    try:
        logger.info(f" Getting Konva state for session: {session_id}")
        
        session = TeachingSessionModel.get_session(session_id)
        
        if session is None:
            return JsonResponse({
                'error': 'Session not found'
            }, status=404)
        
        konva_state = session.get('konva_state', {})
        
        return JsonResponse({
            'session_id': session_id,
            'konva_state': konva_state
        })
        
    except Exception as e:
        logger.error(f" Error getting Konva state: {e}")
        return JsonResponse({
            'error': 'Failed to get Konva state',
            'details': str(e)
        }, status=500)
