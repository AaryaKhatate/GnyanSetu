# WebSocket Consumers for Real-Time Teaching - Simplified Version
import json
import logging
import asyncio
import uuid
from datetime import datetime, timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings

from .models import TeachingSessionModel, LessonService, UserService

logger = logging.getLogger(__name__)

class TeachingConsumer(AsyncWebsocketConsumer):
    """Simplified teaching session WebSocket consumer for testing"""
    
    # Class-level storage for temporary sessions
    temp_sessions = {}
    
    async def connect(self):
        # Get session_id from URL kwargs, or generate one if not provided
        self.session_id = self.scope['url_route']['kwargs'].get('session_id')
        if not self.session_id:
            # Generate a temporary session ID for connections without one
            self.session_id = f"temp_{uuid.uuid4().hex[:8]}"
        
        self.room_group_name = f'teaching_{self.session_id}'
        self.user_id = None
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Teaching WebSocket connected: session {self.session_id}")
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'session_id': self.session_id,
            'message': 'Connected to teaching session',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }))
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"Teaching WebSocket disconnected: session {self.session_id}")
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Set user ID from first message
            if not self.user_id and 'user_id' in data:
                self.user_id = data['user_id']
            
            # Route message based on type
            if message_type == 'user_message':
                await self.handle_user_message(data)
            elif message_type == 'konva_update':
                await self.handle_konva_update(data)
            elif message_type == 'session_control':
                await self.handle_session_control(data)
            elif message_type == 'get_session_state':
                await self.handle_get_session_state(data)
            elif message_type == 'voice_message':
                await self.handle_voice_message(data)
            elif message_type == 'whiteboard_clear':
                await self.handle_whiteboard_clear(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await self.send_error(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error(f"Error processing message: {str(e)}")

    # ============================================================================
    # MESSAGE HANDLERS
    # ============================================================================

    async def handle_user_message(self, data):
        """Handle user text messages during teaching session"""
        try:
            message = data.get('message', '')
            user_id = data.get('user_id', 'anonymous')
            
            if not message.strip():
                await self.send_error('Message cannot be empty')
                return
            
            # Get session data
            session = await self.get_session_data()
            if not session:
                await self.send_error('Session not found')
                return
            
            # Generate a simple AI response
            ai_response = await self.generate_ai_response(message, session)
            
            # Update session with new interaction
            await self.update_session_interaction({
                'user_message': message,
                'ai_response': ai_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'user_id': user_id
            })
            
            # Send response back to client
            await self.send(text_data=json.dumps({
                'type': 'ai_response',
                'message': ai_response,
                'user_message': message,
                'session_id': self.session_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error handling user message: {e}")
            await self.send_error('Failed to process user message')

    async def handle_konva_update(self, data):
        """Handle Konva.js whiteboard updates"""
        try:
            konva_state = data.get('konva_data', data.get('konva_state', {}))
            action = data.get('action', 'update')
            
            # Update session with new Konva state
            await self.update_session_konva_state(konva_state)
            
            # Broadcast Konva update to all session participants
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'konva_broadcast',
                    'data': {
                        'type': 'konva_update',
                        'konva_state': konva_state,
                        'action': action,
                        'session_id': self.session_id,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling Konva update: {e}")
            await self.send_error('Failed to update whiteboard')

    async def handle_session_control(self, data):
        """Handle session control commands (start, pause, stop)"""
        try:
            # Fix: use 'action' instead of 'command' to match the test data
            command = data.get('command', data.get('action', ''))
            
            if command == 'start' or command == 'start_teaching':
                await self.start_teaching_session()
            elif command == 'pause':
                await self.pause_teaching_session()
            elif command == 'stop':
                await self.stop_teaching_session()
            elif command == 'resume':
                await self.resume_teaching_session()
            else:
                await self.send_error(f'Unknown session command: {command}')
                
        except Exception as e:
            logger.error(f"Error handling session control: {e}")
            await self.send_error('Failed to process session control')

    async def handle_get_session_state(self, data):
        """Handle request for current session state"""
        try:
            session = await self.get_session_data()
            if not session:
                await self.send_error('Session not found')
                return
            
            # Send current session state
            await self.send(text_data=json.dumps({
                'type': 'session_state',
                'session_id': self.session_id,
                'status': session.get('status', 'active'),
                'progress': session.get('progress', 0.0),
                'konva_state': session.get('konva_state', {}),
                'lesson_content': session.get('lesson_content', {}),
                'interactions_count': len(session.get('interactions', [])),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error getting session state: {e}")
            await self.send_error('Failed to get session state')

    async def handle_voice_message(self, data):
        """Handle voice messages (placeholder)"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'voice_response',
                'message': 'Voice feature will be implemented soon',
                'session_id': self.session_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error handling voice message: {e}")
            await self.send_error('Failed to process voice message')

    async def handle_whiteboard_clear(self, data):
        """Handle whiteboard clear command"""
        try:
            # Clear the whiteboard state
            await self.update_session_konva_state({})
            
            # Broadcast clear to all participants
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'konva_broadcast',
                    'data': {
                        'type': 'whiteboard_clear',
                        'konva_state': {},
                        'action': 'clear',
                        'session_id': self.session_id,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Error clearing whiteboard: {e}")
            await self.send_error('Failed to clear whiteboard')

    # ============================================================================
    # SESSION CONTROL METHODS
    # ============================================================================

    async def start_teaching_session(self):
        """Start the teaching session"""
        try:
            await self.update_session_interaction({
                'action': 'session_started',
                'status': 'active',
                'started_at': datetime.now(timezone.utc).isoformat()
            })
            
            await self.send(text_data=json.dumps({
                'type': 'session_started',
                'message': 'Teaching session started! Ready to learn?',
                'session_id': self.session_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error starting teaching session: {e}")
            await self.send_error('Failed to start session')

    async def pause_teaching_session(self):
        """Pause the teaching session"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'session_paused',
                'message': 'Teaching session paused',
                'session_id': self.session_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error pausing teaching session: {e}")
            await self.send_error('Failed to pause session')

    async def stop_teaching_session(self):
        """Stop the teaching session"""
        try:
            await self.update_session_interaction({
                'action': 'session_ended',
                'status': 'completed',
                'ended_at': datetime.now(timezone.utc).isoformat()
            })
            
            await self.send(text_data=json.dumps({
                'type': 'session_ended',
                'message': 'Teaching session completed! Great job learning today.',
                'session_id': self.session_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error stopping teaching session: {e}")
            await self.send_error('Failed to stop session')

    async def resume_teaching_session(self):
        """Resume the teaching session"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'session_resumed',
                'message': 'Teaching session resumed',
                'session_id': self.session_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error resuming teaching session: {e}")
            await self.send_error('Failed to resume session')

    # ============================================================================
    # BROADCAST HANDLERS
    # ============================================================================

    async def konva_broadcast(self, event):
        """Send Konva update to WebSocket"""
        await self.send(text_data=json.dumps(event['data']))

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    async def send_error(self, error_message: str):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'error': error_message,
            'session_id': self.session_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }))

    async def get_session_data(self):
        """Get session data from database or temporary storage"""
        try:
            # Check if it's a temporary session
            if self.session_id.startswith('temp_'):
                # Create or get temporary session data
                if self.session_id not in self.temp_sessions:
                    self.temp_sessions[self.session_id] = {
                        '_id': self.session_id,
                        'user_id': self.user_id or 'anonymous',
                        'session_name': f'Temporary Session {self.session_id[-8:]}',
                        'status': 'active',
                        'created_at': datetime.now(timezone.utc),
                        'lesson_content': {
                            'title': 'Interactive Learning Session',
                            'content': 'Welcome to your interactive learning session! Feel free to ask questions.',
                            'slides': [{'title': 'Welcome', 'content': 'Let\'s start learning together!'}]
                        },
                        'konva_state': {},
                        'interactions': [],
                        'progress': 0.0
                    }
                return self.temp_sessions[self.session_id]
            else:
                # Get from database for persistent sessions
                return await database_sync_to_async(TeachingSessionModel.get_session)(self.session_id)
        except Exception as e:
            logger.error(f"Error getting session data: {e}")
            return None

    async def update_session_interaction(self, interaction_data):
        """Update session with new interaction"""
        try:
            # Handle temporary sessions
            if self.session_id.startswith('temp_'):
                if self.session_id in self.temp_sessions:
                    self.temp_sessions[self.session_id]['last_interaction'] = interaction_data
                    self.temp_sessions[self.session_id]['updated_at'] = datetime.now(timezone.utc)
                    self.temp_sessions[self.session_id]['interactions'].append(interaction_data)
                    return True
                return False
            else:
                # Update database for persistent sessions
                return await database_sync_to_async(TeachingSessionModel.update_session)(
                    self.session_id, {
                        'last_interaction': interaction_data,
                        'updated_at': datetime.now(timezone.utc)
                    }
                )
        except Exception as e:
            logger.error(f"Error updating session interaction: {e}")
            return False

    async def update_session_konva_state(self, konva_state):
        """Update session with new Konva state"""
        try:
            # Handle temporary sessions
            if self.session_id.startswith('temp_'):
                if self.session_id in self.temp_sessions:
                    self.temp_sessions[self.session_id]['konva_state'] = konva_state
                    self.temp_sessions[self.session_id]['last_whiteboard_update'] = datetime.now(timezone.utc)
                    return True
                return False
            else:
                # Update database for persistent sessions
                return await database_sync_to_async(TeachingSessionModel.update_session)(
                    self.session_id, {
                        'konva_state': konva_state,
                        'last_whiteboard_update': datetime.now(timezone.utc)
                    }
                )
        except Exception as e:
            logger.error(f"Error updating Konva state: {e}")
            return False

    async def generate_ai_response(self, user_message: str, session) -> str:
        """Generate AI teacher response based on user message and lesson content"""
        try:
            lesson_content = session.get('lesson_content', {})
            lesson_title = lesson_content.get('title', 'Current Topic')
            
            # Basic response templates
            responses = [
                f"Great question about {lesson_title}! Let me explain that on the whiteboard.",
                f"I see you're asking about '{user_message[:50]}...' Let's work through this together.",
                f"Excellent! Now let's apply what we've learned about {lesson_title}.",
                f"That's a good observation. In the context of {lesson_title}, we can see that...",
                f"Let me draw this concept for you to make it clearer."
            ]
            
            # Simple response selection based on message content
            if "explain" in user_message.lower():
                return f"Let me explain {lesson_title} step by step on the whiteboard."
            elif "how" in user_message.lower():
                return f"Great question! Here's how {lesson_title} works..."
            elif "why" in user_message.lower():
                return f"The reason behind this in {lesson_title} is..."
            elif "hello" in user_message.lower() or "hi" in user_message.lower():
                return f"Hello! Welcome to our interactive learning session on {lesson_title}. What would you like to explore?"
            else:
                return responses[len(user_message) % len(responses)]
                
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I understand your question. Let me help you with that."