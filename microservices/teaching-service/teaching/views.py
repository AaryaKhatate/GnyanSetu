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
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import (
    TeachingSessionModel, WhiteboardModel, ChatMessageModel, 
    VoiceQueueModel, LessonInteractionModel
)
from .voice_service import VoiceSynthesisService
from .ai_tutor import AITutorService
from .lesson_integration import LessonIntegrationService

logger = logging.getLogger(__name__)

# Health Check
@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    try:
        # Test MongoDB connection
        from .models import mongo
        db_status = "connected" if mongo.db else "disconnected"
        
        return Response({
            'status': 'healthy',
            'service': 'Teaching Service',
            'version': '1.0.0',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database': db_status,
            'features': {
                'websockets': True,
                'voice_synthesis': True,
                'ai_tutor': True,
                'whiteboard': True,
                'lesson_integration': True
            }
        })
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

# Teaching Session Management
@api_view(['POST'])
def create_teaching_session(request):
    """Create a new teaching session"""
    try:
        data = request.data
        lesson_id = data.get('lesson_id')
        user_id = data.get('user_id')
        
        if not lesson_id or not user_id:
            return Response({
                'error': 'lesson_id and user_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get lesson content from lesson service
        lesson_service = LessonIntegrationService()
        lesson_content = lesson_service.get_lesson_content(lesson_id)
        
        if not lesson_content:
            return Response({
                'error': 'Could not load lesson content'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Create teaching session
        session_data = {
            'session_name': data.get('session_name'),
            'voice_enabled': data.get('voice_enabled', True),
            'whiteboard_enabled': data.get('whiteboard_enabled', True),
            'ai_tutor_enabled': data.get('ai_tutor_enabled', True),
            'interaction_mode': data.get('interaction_mode', 'guided'),
            'voice_speed': data.get('voice_speed', 1.0),
            'voice_language': data.get('voice_language', 'en-US'),
            'total_slides': lesson_content.get('total_slides', 1),
            'lesson_content': lesson_content
        }
        
        session_id = TeachingSessionModel.create_session(lesson_id, user_id, session_data)
        
        return Response({
            'session_id': session_id,
            'lesson_content': lesson_content,
            'websocket_urls': {
                'teaching': f'/ws/teaching/{session_id}/',
                'whiteboard': f'/ws/whiteboard/{session_id}/',
                'voice': f'/ws/voice/{session_id}/',
                'ai_tutor': f'/ws/ai-tutor/{session_id}/',
                'session_control': f'/ws/session-control/{session_id}/'
            },
            'message': 'Teaching session created successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error creating teaching session: {e}")
        return Response({
            'error': 'Failed to create teaching session'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_teaching_session(request, session_id):
    """Get teaching session details"""
    try:
        session = TeachingSessionModel.get_session(session_id)
        
        if not session:
            return Response({
                'error': 'Teaching session not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'session': session,
            'websocket_urls': {
                'teaching': f'/ws/teaching/{session_id}/',
                'whiteboard': f'/ws/whiteboard/{session_id}/',
                'voice': f'/ws/voice/{session_id}/',
                'ai_tutor': f'/ws/ai-tutor/{session_id}/',
                'session_control': f'/ws/session-control/{session_id}/'
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting teaching session: {e}")
        return Response({
            'error': 'Failed to get teaching session'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
def update_teaching_session(request, session_id):
    """Update teaching session"""
    try:
        updates = request.data
        success = TeachingSessionModel.update_session(session_id, updates)
        
        if success:
            return Response({'message': 'Session updated successfully'})
        else:
            return Response({
                'error': 'Failed to update session'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error updating teaching session: {e}")
        return Response({
            'error': 'Failed to update teaching session'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_user_sessions(request, user_id):
    """Get all teaching sessions for a user"""
    try:
        status_filter = request.GET.get('status')
        sessions = TeachingSessionModel.get_user_sessions(user_id, status_filter)
        
        return Response({
            'sessions': sessions,
            'count': len(sessions)
        })
        
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        return Response({
            'error': 'Failed to get user sessions'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Voice Synthesis
@api_view(['POST'])
def synthesize_voice(request):
    """Synthesize voice from text"""
    try:
        data = request.data
        text = data.get('text', '')
        voice_settings = data.get('voice_settings', {})
        session_id = data.get('session_id')
        
        if not text:
            return Response({
                'error': 'Text is required for voice synthesis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        voice_service = VoiceSynthesisService()
        audio_url = voice_service.synthesize_speech(text, voice_settings, session_id)
        
        if audio_url:
            return Response({
                'audio_url': audio_url,
                'text': text,
                'voice_settings': voice_settings
            })
        else:
            return Response({
                'error': 'Voice synthesis failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error in voice synthesis: {e}")
        return Response({
            'error': 'Voice synthesis failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_available_voices(request):
    """Get available voices for TTS"""
    try:
        voice_service = VoiceSynthesisService()
        voices = voice_service.get_available_voices()
        
        return Response({
            'voices': voices,
            'current_engine': voice_service.tts_engine
        })
        
    except Exception as e:
        logger.error(f"Error getting available voices: {e}")
        return Response({
            'error': 'Failed to get available voices'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# AI Tutor
@api_view(['POST'])
def ask_ai_tutor(request):
    """Ask AI tutor a question"""
    try:
        data = request.data
        question = data.get('question', '')
        session_id = data.get('session_id', '')
        context = data.get('context', {})
        
        if not question or not session_id:
            return Response({
                'error': 'Question and session_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        ai_tutor = AITutorService()
        response = ai_tutor.generate_response(question, session_id, context)
        
        return Response({
            'question': question,
            'response': response,
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Error with AI tutor: {e}")
        return Response({
            'error': 'AI tutor request failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_question_suggestions(request, session_id):
    """Get AI-generated question suggestions"""
    try:
        current_slide = request.GET.get('slide', 0)
        
        ai_tutor = AITutorService()
        suggestions = ai_tutor.suggest_questions(session_id, int(current_slide))
        
        return Response({
            'suggestions': suggestions,
            'session_id': session_id,
            'current_slide': current_slide
        })
        
    except Exception as e:
        logger.error(f"Error getting question suggestions: {e}")
        return Response({
            'error': 'Failed to get question suggestions'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def generate_practice_question(request):
    """Generate a practice question"""
    try:
        data = request.data
        session_id = data.get('session_id', '')
        topic = data.get('topic')
        
        if not session_id:
            return Response({
                'error': 'session_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        ai_tutor = AITutorService()
        practice_question = ai_tutor.generate_practice_question(session_id, topic)
        
        return Response(practice_question)
        
    except Exception as e:
        logger.error(f"Error generating practice question: {e}")
        return Response({
            'error': 'Failed to generate practice question'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Chat and Messages
@api_view(['GET'])
def get_session_messages(request, session_id):
    """Get chat messages for a session"""
    try:
        limit = int(request.GET.get('limit', 100))
        messages = ChatMessageModel.get_session_messages(session_id, limit)
        
        return Response({
            'messages': messages,
            'session_id': session_id,
            'count': len(messages)
        })
        
    except Exception as e:
        logger.error(f"Error getting session messages: {e}")
        return Response({
            'error': 'Failed to get session messages'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def add_chat_message(request):
    """Add a chat message"""
    try:
        data = request.data
        session_id = data.get('session_id', '')
        message_data = {
            'user_id': data.get('user_id', ''),
            'message': data.get('message', ''),
            'message_type': data.get('message_type', 'user'),
            'metadata': data.get('metadata', {})
        }
        
        if not session_id or not message_data['message']:
            return Response({
                'error': 'session_id and message are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        message_id = ChatMessageModel.add_message(session_id, message_data)
        
        return Response({
            'message_id': message_id,
            'session_id': session_id,
            'message': 'Message added successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error adding chat message: {e}")
        return Response({
            'error': 'Failed to add chat message'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Whiteboard
@api_view(['GET'])
def get_whiteboard_state(request, session_id):
    """Get whiteboard state for a session"""
    try:
        whiteboard_data = WhiteboardModel.get_whiteboard_state(session_id)
        
        return Response({
            'whiteboard_data': whiteboard_data or {},
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Error getting whiteboard state: {e}")
        return Response({
            'error': 'Failed to get whiteboard state'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def save_whiteboard_state(request):
    """Save whiteboard state"""
    try:
        data = request.data
        session_id = data.get('session_id', '')
        whiteboard_data = data.get('whiteboard_data', {})
        
        if not session_id:
            return Response({
                'error': 'session_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        success = WhiteboardModel.save_whiteboard_state(session_id, whiteboard_data)
        
        if success:
            return Response({
                'message': 'Whiteboard state saved successfully',
                'session_id': session_id
            })
        else:
            return Response({
                'error': 'Failed to save whiteboard state'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error saving whiteboard state: {e}")
        return Response({
            'error': 'Failed to save whiteboard state'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Analytics and Interactions
@api_view(['GET'])
def get_session_analytics(request, session_id):
    """Get analytics for a teaching session"""
    try:
        session = TeachingSessionModel.get_session(session_id)
        interactions = LessonInteractionModel.get_session_interactions(session_id)
        messages = ChatMessageModel.get_session_messages(session_id)
        
        if not session:
            return Response({
                'error': 'Session not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        analytics = {
            'session_info': {
                'session_id': session_id,
                'status': session.get('status'),
                'created_at': session.get('created_at'),
                'updated_at': session.get('updated_at'),
                'current_slide': session.get('current_slide', 0),
                'progress': session.get('progress', 0.0)
            },
            'interactions': {
                'total_interactions': len(interactions),
                'interaction_types': {},
                'timeline': interactions
            },
            'communication': {
                'total_messages': len(messages),
                'user_messages': len([m for m in messages if m.get('message_type') == 'user']),
                'ai_messages': len([m for m in messages if m.get('message_type') == 'ai']),
                'recent_messages': messages[-10:] if messages else []
            },
            'session_analytics': session.get('analytics', {})
        }
        
        # Count interaction types
        for interaction in interactions:
            interaction_type = interaction.get('interaction_type', 'unknown')
            analytics['interactions']['interaction_types'][interaction_type] = \
                analytics['interactions']['interaction_types'].get(interaction_type, 0) + 1
        
        return Response(analytics)
        
    except Exception as e:
        logger.error(f"Error getting session analytics: {e}")
        return Response({
            'error': 'Failed to get session analytics'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Teaching Interface
@api_view(['GET'])
def teaching_interface(request, session_id):
    """Serve the teaching interface HTML"""
    try:
        # This would serve the actual teaching interface
        # For now, return a simple HTML response
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>GnyanSetu Teaching Interface</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .status {{ background: #e8f5e8; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎓 GnyanSetu Teaching Interface</h1>
                <div class="status">
                    <strong>Session ID:</strong> {session_id}<br>
                    <strong>Status:</strong> Ready for real-time teaching
                </div>
                <p>This teaching interface will be built with React + Konva.js for interactive teaching sessions.</p>
                <h3>Features:</h3>
                <ul>
                    <li>🎤 Real-time voice synthesis</li>
                    <li>🎨 Interactive whiteboard with Konva.js</li>
                    <li>🤖 AI tutor integration</li>
                    <li>💬 Live chat</li>
                    <li>📊 Session analytics</li>
                </ul>
                <h3>WebSocket Endpoints:</h3>
                <ul>
                    <li>Teaching: <code>/ws/teaching/{session_id}/</code></li>
                    <li>Whiteboard: <code>/ws/whiteboard/{session_id}/</code></li>
                    <li>Voice: <code>/ws/voice/{session_id}/</code></li>
                    <li>AI Tutor: <code>/ws/ai-tutor/{session_id}/</code></li>
                    <li>Session Control: <code>/ws/session-control/{session_id}/</code></li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        return HttpResponse(html_content, content_type='text/html')
        
    except Exception as e:
        logger.error(f"Error serving teaching interface: {e}")
        return HttpResponse("Error loading teaching interface", status=500)

# AI Response Generation (for lesson service integration)
@api_view(['POST'])
def generate_ai_response(request):
    """Generate AI response (used by AI tutor service)"""
    try:
        data = request.data
        prompt = data.get('prompt', '')
        
        if not prompt:
            return Response({
                'error': 'Prompt is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # This would integrate with Gemini API
        # For now, return a mock response
        response = "This is a placeholder AI response. Integration with Gemini API would happen here."
        
        return Response({
            'response': response,
            'prompt': prompt
        })
        
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        return Response({
            'error': 'Failed to generate AI response'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)