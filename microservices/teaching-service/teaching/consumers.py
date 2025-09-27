# WebSocket Consumers for Real-Time Teaching
import json
import logging
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from .models import (
    TeachingSessionModel, WhiteboardModel, ChatMessageModel, 
    VoiceQueueModel, LessonInteractionModel
)
from .voice_service import VoiceSynthesisService
from .ai_tutor import AITutorService
from .lesson_integration import LessonIntegrationService

logger = logging.getLogger(__name__)

class TeachingConsumer(AsyncWebsocketConsumer):
    """Main teaching session WebSocket consumer"""
    
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
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
            'message': 'Connected to teaching session'
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
            if message_type == 'start_lesson':
                await self.handle_start_lesson(data)
            elif message_type == 'navigate_slide':
                await self.handle_navigate_slide(data)
            elif message_type == 'pause_lesson':
                await self.handle_pause_lesson(data)
            elif message_type == 'resume_lesson':
                await self.handle_resume_lesson(data)
            elif message_type == 'end_lesson':
                await self.handle_end_lesson(data)
            elif message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'request_voice':
                await self.handle_voice_request(data)
            elif message_type == 'interaction':
                await self.handle_interaction(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error(f"Error processing message: {str(e)}")
    
    async def handle_start_lesson(self, data):
        """Start teaching session"""
        try:
            # Update session status
            await database_sync_to_async(TeachingSessionModel.update_session)(
                self.session_id,
                {
                    'status': 'active',
                    'analytics.start_time': data.get('start_time'),
                    'current_slide': 0
                }
            )
            
            # Load lesson content
            lesson_service = LessonIntegrationService()
            lesson_content = await lesson_service.get_lesson_content(
                data.get('lesson_id')
            )
            
            # Broadcast lesson start to all participants
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'lesson_started',
                    'lesson_content': lesson_content,
                    'current_slide': 0,
                    'timestamp': data.get('start_time')
                }
            )
            
            # Start voice synthesis for first slide if enabled
            if lesson_content and lesson_content.get('voice_enabled', True):
                await self.synthesize_slide_voice(lesson_content, 0)
                
        except Exception as e:
            logger.error(f"Error starting lesson: {e}")
            await self.send_error(f"Failed to start lesson: {str(e)}")
    
    async def handle_navigate_slide(self, data):
        """Handle slide navigation"""
        try:
            slide_number = data.get('slide_number', 0)
            
            # Update session current slide
            await database_sync_to_async(TeachingSessionModel.update_session)(
                self.session_id,
                {
                    'current_slide': slide_number,
                    'progress': data.get('progress', 0.0)
                }
            )
            
            # Track interaction
            await database_sync_to_async(LessonInteractionModel.track_interaction)(
                self.session_id,
                {
                    'user_id': self.user_id,
                    'interaction_type': 'slide_navigation',
                    'content': {'slide_number': slide_number},
                    'metadata': {'progress': data.get('progress', 0.0)}
                }
            )
            
            # Broadcast slide change to all participants
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'slide_changed',
                    'slide_number': slide_number,
                    'progress': data.get('progress', 0.0),
                    'user_id': self.user_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error navigating slide: {e}")
            await self.send_error(f"Failed to navigate slide: {str(e)}")
    
    async def handle_chat_message(self, data):
        """Handle chat message"""
        try:
            # Save message to database
            message_id = await database_sync_to_async(ChatMessageModel.add_message)(
                self.session_id,
                {
                    'user_id': self.user_id,
                    'message': data.get('message', ''),
                    'message_type': 'user',
                    'metadata': data.get('metadata', {})
                }
            )
            
            # Broadcast message to all participants
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message_broadcast',
                    'message_id': message_id,
                    'user_id': self.user_id,
                    'message': data.get('message', ''),
                    'timestamp': data.get('timestamp')
                }
            )
            
            # Trigger AI tutor response if enabled
            session = await database_sync_to_async(TeachingSessionModel.get_session)(self.session_id)
            if session and session.get('settings', {}).get('ai_tutor_enabled', True):
                await self.trigger_ai_response(data.get('message', ''))
                
        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
            await self.send_error(f"Failed to send message: {str(e)}")
    
    async def handle_voice_request(self, data):
        """Handle voice synthesis request"""
        try:
            # Add to voice queue
            queue_id = await database_sync_to_async(VoiceQueueModel.add_to_queue)(
                self.session_id,
                {
                    'text': data.get('text', ''),
                    'voice_settings': data.get('voice_settings', {}),
                    'priority': data.get('priority', 5),
                    'metadata': {'request_id': data.get('request_id')}
                }
            )
            
            # Process voice synthesis
            voice_service = VoiceSynthesisService()
            audio_url = await voice_service.synthesize_speech(
                text=data.get('text', ''),
                voice_settings=data.get('voice_settings', {}),
                session_id=self.session_id
            )
            
            # Update queue item
            await database_sync_to_async(VoiceQueueModel.update_queue_item)(
                queue_id,
                {
                    'status': 'completed',
                    'audio_url': audio_url,
                    'processed_at': data.get('timestamp')
                }
            )
            
            # Send audio URL to client
            await self.send(text_data=json.dumps({
                'type': 'voice_ready',
                'request_id': data.get('request_id'),
                'audio_url': audio_url,
                'queue_id': queue_id
            }))
            
        except Exception as e:
            logger.error(f"Error processing voice request: {e}")
            await self.send_error(f"Failed to process voice: {str(e)}")
    
    async def handle_interaction(self, data):
        """Handle general interaction tracking"""
        try:
            # Track interaction
            interaction_id = await database_sync_to_async(LessonInteractionModel.track_interaction)(
                self.session_id,
                {
                    'user_id': self.user_id,
                    'interaction_type': data.get('interaction_type'),
                    'content': data.get('content', {}),
                    'metadata': data.get('metadata', {})
                }
            )
            
            # Broadcast interaction to other participants if needed
            if data.get('broadcast', False):
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'interaction_broadcast',
                        'interaction_id': interaction_id,
                        'interaction_type': data.get('interaction_type'),
                        'content': data.get('content', {}),
                        'user_id': self.user_id
                    }
                )
                
        except Exception as e:
            logger.error(f"Error handling interaction: {e}")
            await self.send_error(f"Failed to track interaction: {str(e)}")
    
    async def synthesize_slide_voice(self, lesson_content, slide_number):
        """Synthesize voice for a slide"""
        try:
            slides = lesson_content.get('slides', [])
            if slide_number < len(slides):
                slide_content = slides[slide_number]
                text_to_speak = slide_content.get('narrator_text', slide_content.get('content', ''))
                
                if text_to_speak:
                    await self.handle_voice_request({
                        'text': text_to_speak,
                        'voice_settings': lesson_content.get('voice_settings', {}),
                        'priority': 1,
                        'request_id': f'slide_{slide_number}'
                    })
        except Exception as e:
            logger.error(f"Error synthesizing slide voice: {e}")
    
    async def trigger_ai_response(self, user_message):
        """Trigger AI tutor response"""
        try:
            ai_tutor = AITutorService()
            response = await ai_tutor.generate_response(
                user_message=user_message,
                session_id=self.session_id,
                context={}
            )
            
            if response:
                # Add AI response to chat
                await database_sync_to_async(ChatMessageModel.add_message)(
                    self.session_id,
                    {
                        'user_id': 'ai_tutor',
                        'message': response,
                        'message_type': 'ai',
                        'metadata': {'trigger_message': user_message}
                    }
                )
                
                # Broadcast AI response
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'ai_response',
                        'message': response,
                        'trigger_message': user_message
                    }
                )
                
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
    
    async def send_error(self, error_message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message
        }))
    
    # Group message handlers
    async def lesson_started(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def slide_changed(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def chat_message_broadcast(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def ai_response(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def interaction_broadcast(self, event):
        await self.send(text_data=json.dumps(event))


class WhiteboardConsumer(AsyncWebsocketConsumer):
    """Whiteboard WebSocket consumer for collaborative drawing"""
    
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'whiteboard_{self.session_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Whiteboard WebSocket connected: session {self.session_id}")
        
        # Send current whiteboard state
        whiteboard_state = await database_sync_to_async(WhiteboardModel.get_whiteboard_state)(
            self.session_id
        )
        
        if whiteboard_state:
            await self.send(text_data=json.dumps({
                'type': 'whiteboard_state',
                'data': whiteboard_state
            }))
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"Whiteboard WebSocket disconnected: session {self.session_id}")
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'whiteboard_update':
                await self.handle_whiteboard_update(data)
            elif message_type == 'clear_whiteboard':
                await self.handle_clear_whiteboard(data)
            elif message_type == 'save_whiteboard':
                await self.handle_save_whiteboard(data)
                
        except Exception as e:
            logger.error(f"Error handling whiteboard message: {e}")
    
    async def handle_whiteboard_update(self, data):
        """Handle whiteboard drawing updates"""
        try:
            # Save whiteboard state
            await database_sync_to_async(WhiteboardModel.save_whiteboard_state)(
                self.session_id,
                data.get('whiteboard_data', {})
            )
            
            # Broadcast to all participants
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'whiteboard_updated',
                    'whiteboard_data': data.get('whiteboard_data', {}),
                    'user_id': data.get('user_id')
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating whiteboard: {e}")
    
    async def whiteboard_updated(self, event):
        await self.send(text_data=json.dumps(event))


class VoiceConsumer(AsyncWebsocketConsumer):
    """Voice synthesis WebSocket consumer"""
    
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'voice_{self.session_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Voice WebSocket connected: session {self.session_id}")
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'synthesize_voice':
                await self.handle_voice_synthesis(data)
            elif message_type == 'voice_settings_update':
                await self.handle_voice_settings_update(data)
                
        except Exception as e:
            logger.error(f"Error handling voice message: {e}")
    
    async def handle_voice_synthesis(self, data):
        """Handle voice synthesis request"""
        try:
            voice_service = VoiceSynthesisService()
            audio_url = await voice_service.synthesize_speech(
                text=data.get('text', ''),
                voice_settings=data.get('voice_settings', {}),
                session_id=self.session_id
            )
            
            await self.send(text_data=json.dumps({
                'type': 'voice_synthesized',
                'audio_url': audio_url,
                'text': data.get('text', ''),
                'request_id': data.get('request_id')
            }))
            
        except Exception as e:
            logger.error(f"Error synthesizing voice: {e}")


class AITutorConsumer(AsyncWebsocketConsumer):
    """AI Tutor WebSocket consumer"""
    
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'ai_tutor_{self.session_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"AI Tutor WebSocket connected: session {self.session_id}")
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ask_question':
                await self.handle_question(data)
            elif message_type == 'request_explanation':
                await self.handle_explanation_request(data)
                
        except Exception as e:
            logger.error(f"Error handling AI tutor message: {e}")
    
    async def handle_question(self, data):
        """Handle student question"""
        try:
            ai_tutor = AITutorService()
            response = await ai_tutor.generate_response(
                user_message=data.get('question', ''),
                session_id=self.session_id,
                context=data.get('context', {})
            )
            
            await self.send(text_data=json.dumps({
                'type': 'ai_response',
                'question': data.get('question', ''),
                'response': response,
                'request_id': data.get('request_id')
            }))
            
        except Exception as e:
            logger.error(f"Error handling AI question: {e}")


class SessionControlConsumer(AsyncWebsocketConsumer):
    """Session control WebSocket consumer"""
    
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'session_control_{self.session_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Session Control WebSocket connected: session {self.session_id}")
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'session_control':
                await self.handle_session_control(data)
                
        except Exception as e:
            logger.error(f"Error handling session control message: {e}")
    
    async def handle_session_control(self, data):
        """Handle session control commands"""
        try:
            action = data.get('action')
            
            if action in ['pause', 'resume', 'end']:
                # Update session status
                status_map = {'pause': 'paused', 'resume': 'active', 'end': 'ended'}
                await database_sync_to_async(TeachingSessionModel.update_session)(
                    self.session_id,
                    {'status': status_map[action]}
                )
                
                # Broadcast to all participants
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'session_status_changed',
                        'action': action,
                        'status': status_map[action],
                        'timestamp': data.get('timestamp')
                    }
                )
                
        except Exception as e:
            logger.error(f"Error handling session control: {e}")
    
    async def session_status_changed(self, event):
        await self.send(text_data=json.dumps(event))