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
            
            # DEBUG: Log exactly what we received
            logger.info(f"Received WebSocket message: {text_data}")
            logger.info(f"Parsed data: {data}")
            
            # Determine message type - handle different message formats
            message_type = data.get('type', 'unknown')
            
            # Check if this is a PDF document message (from Dashboard)
            if 'topic' in data and 'pdf_filename' in data:
                message_type = 'pdf_document'
            elif 'conversation_id' in data and not data.get('type'):
                message_type = 'conversation_message'
            
            logger.info(f"Message type: '{message_type}'")
            
            # Set user ID from first message
            if not self.user_id and 'user_id' in data:
                self.user_id = data['user_id']
            
            # Handle empty or None message types
            if not message_type or message_type in ['unknown', 'None']:
                logger.warning(f"Received message with missing or invalid type: {message_type}")
                await self.send_error(f"Message type is required. Received: {message_type}")
                return
            
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
            elif message_type == 'pdf_document':
                await self.handle_pdf_document(data)
            elif message_type == 'conversation_message':
                await self.handle_conversation_message(data)
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

    async def handle_pdf_document(self, data):
        """Handle PDF document upload and send to Lesson Service for processing"""
        try:
            topic = data.get('topic', 'Unknown Topic')
            pdf_filename = data.get('pdf_filename', 'document.pdf')
            pdf_text = data.get('pdf_text', '')
            conversation_id = data.get('conversation_id', self.session_id)
            user_id = data.get('user_id', 'anonymous')
            
            logger.info(f"Processing PDF document: {pdf_filename} for topic: {topic}")
            
            # Validate PDF text
            if not pdf_text or pdf_text == 'undefined' or len(pdf_text.strip()) < 10:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'PDF text is empty or invalid. Please upload a valid PDF with text content.',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }))
                return
            
            # Store PDF info in session
            if self.session_id not in self.temp_sessions:
                self.temp_sessions[self.session_id] = {}
                
            self.temp_sessions[self.session_id]['pdf_data'] = {
                'filename': pdf_filename,
                'topic': topic,
                'text_content': pdf_text,
                'conversation_id': conversation_id,
                'user_id': user_id,
                'uploaded_at': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"PDF stored in session: {pdf_filename}")
            
            # Send to Lesson Service for JSON lesson generation
            await self.send(text_data=json.dumps({
                'type': 'lesson_generation_started',
                'message': f"Analyzing '{pdf_filename}' and generating interactive lesson...",
                'timestamp': datetime.now(timezone.utc).isoformat()
            }))
            
            # Call Lesson Service to generate structured lesson
            lesson_json = await self.call_lesson_service(pdf_text, pdf_filename, user_id)
            
            if lesson_json:
                # Store lesson and start teaching
                await self.start_teaching_from_lesson(lesson_json, pdf_filename, topic)
            else:
                # Fallback to simple lesson generation
                logger.warning("Lesson Service failed, using fallback lesson generation")
                lesson_commands = await self.generate_simple_lesson_fallback(pdf_text, topic, pdf_filename)
                await self.start_teaching_from_commands(lesson_commands, pdf_filename, topic)
                
        except Exception as e:
            logger.error(f"Error handling PDF document: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error processing PDF: {str(e)}',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }))
    
    async def call_lesson_service(self, pdf_text, filename, user_id):
        """Call Lesson Service to generate structured lesson JSON"""
        import aiohttp
        import tempfile
        import os
        
        try:
            # Create temporary PDF file for Lesson Service
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(pdf_text)
                temp_path = temp_file.name
            
            # Prepare form data for Lesson Service
            lesson_service_url = "http://localhost:8003/api/generate-lesson/"
            
            async with aiohttp.ClientSession() as session:
                # Create form data
                data = aiohttp.FormData()
                data.add_field('user_id', user_id)
                data.add_field('lesson_type', 'interactive')
                
                # Add file
                with open(temp_path, 'rb') as f:
                    data.add_field('pdf_file', f, filename=filename, content_type='text/plain')
                
                logger.info(f"Calling Lesson Service at {lesson_service_url}")
                
                async with session.post(lesson_service_url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("Lesson Service responded successfully")
                        
                        # Clean up temp file
                        os.unlink(temp_path)
                        
                        return result
                    else:
                        logger.error(f"Lesson Service error: {response.status}")
                        os.unlink(temp_path)
                        return None
                        
        except Exception as e:
            logger.error(f"Error calling Lesson Service: {str(e)}")
            return None
    
    async def start_teaching_from_lesson(self, lesson_data, filename, topic):
        """Start teaching using lesson JSON from Lesson Service"""
        try:
            # Extract lesson commands from the JSON response
            lesson_content = lesson_data.get('lesson', {})
            
            # Convert lesson JSON to teaching commands
            teaching_commands = await self.convert_lesson_to_commands(lesson_content)
            
            # Store in session
            self.temp_sessions[self.session_id]['current_lesson'] = {
                'commands': teaching_commands,
                'lesson_data': lesson_data,
                'topic': topic,
                'filename': filename,
                'current_step': 0,
                'is_playing': False
            }
            
            # Send lesson ready notification
            await self.send(text_data=json.dumps({
                'type': 'lesson_ready',
                'message': f"Interactive lesson ready for '{topic}'! Starting teaching...",
                'lesson_data': {
                    'filename': filename,
                    'topic': topic,
                    'total_steps': len(teaching_commands),
                    'lesson_id': lesson_data.get('lesson_id')
                },
                'commands': teaching_commands,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }))
            
            # Auto-start teaching
            await asyncio.sleep(1)  # Brief pause
            await self.start_lesson_playback()
            
        except Exception as e:
            logger.error(f"Error starting teaching from lesson: {str(e)}")
    
    async def convert_lesson_to_commands(self, lesson_content):
        """Convert Lesson Service JSON to Teaching commands"""
        commands = []
        
        try:
            # Extract title and introduction
            title = lesson_content.get('title', 'Interactive Lesson')
            introduction = lesson_content.get('introduction', '')
            
            # Add title command
            commands.append({
                'type': 'speak',
                'text': f"Welcome to today's lesson on {title}",
                'duration': 3
            })
            
            commands.append({
                'type': 'write',
                'text': title,
                'x': 50,
                'y': 10,
                'font_size': 24,
                'color': '#2563eb'
            })
            
            # Add introduction
            if introduction:
                commands.append({
                    'type': 'speak',
                    'text': introduction,
                    'duration': 5
                })
            
            # Process sections
            sections = lesson_content.get('sections', [])
            y_position = 20
            
            for i, section in enumerate(sections):
                section_title = section.get('title', f'Section {i+1}')
                section_content = section.get('content', '')
                
                # Section title
                commands.append({
                    'type': 'speak',
                    'text': f"Let's explore {section_title}",
                    'duration': 2
                })
                
                y_position += 8
                commands.append({
                    'type': 'write',
                    'text': section_title,
                    'x': 10,
                    'y': y_position,
                    'font_size': 18,
                    'color': '#1d4ed8'
                })
                
                # Section content
                if section_content:
                    commands.append({
                        'type': 'speak',
                        'text': section_content,
                        'duration': 6
                    })
                    
                    # Write key points
                    y_position += 5
                    content_lines = section_content.split('. ')[:2]  # First 2 sentences
                    for line in content_lines:
                        if line.strip():
                            y_position += 4
                            commands.append({
                                'type': 'write',
                                'text': f"• {line.strip()}",
                                'x': 15,
                                'y': y_position,
                                'font_size': 14,
                                'color': '#374151'
                            })
                
                # Add visual elements if needed
                if i < 2:  # Add shapes for first two sections
                    commands.append({
                        'type': 'draw',
                        'shape': 'rectangle',
                        'x': 70,
                        'y': y_position - 3,
                        'width': 25,
                        'height': 6,
                        'color': '#e5e7eb',
                        'stroke': '#9ca3af'
                    })
                
                y_position += 10
            
            # Add conclusion
            commands.append({
                'type': 'speak',
                'text': "That completes our lesson. Let me know if you have any questions!",
                'duration': 4
            })
            
            logger.info(f"Converted lesson to {len(commands)} teaching commands")
            return commands
            
        except Exception as e:
            logger.error(f"Error converting lesson to commands: {str(e)}")
            return self.generate_fallback_commands()
    
    def generate_fallback_commands(self):
        """Generate basic commands if conversion fails"""
        return [
            {
                'type': 'speak',
                'text': 'Welcome to the lesson!',
                'duration': 2
            },
            {
                'type': 'write', 
                'text': 'Lesson Content',
                'x': 50,
                'y': 10,
                'font_size': 20,
                'color': '#2563eb'
            }
        ]
    
    async def start_lesson_playback(self):
        """Start automated lesson playback"""
        try:
            if self.session_id not in self.temp_sessions:
                return
                
            lesson = self.temp_sessions[self.session_id].get('current_lesson')
            if not lesson:
                return
                
            lesson['is_playing'] = True
            lesson['current_step'] = 0
            
            commands = lesson['commands']
            
            await self.send(text_data=json.dumps({
                'type': 'lesson_playback_started',
                'message': 'Starting interactive lesson playback',
                'total_steps': len(commands),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }))
            
            # Execute commands one by one
            for i, command in enumerate(commands):
                if not lesson.get('is_playing', False):
                    break
                    
                lesson['current_step'] = i
                
                # Send command to frontend
                await self.send(text_data=json.dumps({
                    'type': 'teaching_command',
                    'command': command,
                    'step': i + 1,
                    'total_steps': len(commands),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }))
                
                # Wait based on command duration
                duration = command.get('duration', 3)
                await asyncio.sleep(duration)
            
            # Lesson completed
            lesson['is_playing'] = False
            await self.send(text_data=json.dumps({
                'type': 'lesson_completed',
                'message': 'Interactive lesson completed! Great job!',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error in lesson playback: {str(e)}")
    
    async def start_teaching_from_commands(self, commands, filename, topic):
        """Start teaching using simple command structure"""
        try:
            # Store in session
            self.temp_sessions[self.session_id]['current_lesson'] = {
                'commands': commands,
                'topic': topic,
                'filename': filename,
                'current_step': 0,
                'is_playing': False
            }
            
            # Send lesson ready notification
            await self.send(text_data=json.dumps({
                'type': 'lesson_ready',
                'message': f"Simple lesson ready for '{topic}'!",
                'lesson_data': {
                    'filename': filename,
                    'topic': topic,
                    'total_steps': len(commands)
                },
                'commands': commands,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }))
            
            # Auto-start teaching
            await asyncio.sleep(1)
            await self.start_lesson_playback()
            
        except Exception as e:
            logger.error(f"Error starting teaching from commands: {str(e)}")
    
    async def generate_simple_lesson_fallback(self, pdf_text, topic, filename):
        """Generate simple lesson commands as fallback"""
        commands = []
        
        # Extract key points from PDF text
        sentences = pdf_text.split('.')[:5]  # First 5 sentences
        
        # Title
        commands.append({
            'type': 'speak',
            'text': f"Let's learn about {topic}",
            'duration': 3
        })
        
        commands.append({
            'type': 'write',
            'text': topic,
            'x': 50,
            'y': 10,
            'font_size': 22,
            'color': '#2563eb'
        })
        
        # Content points
        y_pos = 25
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                commands.append({
                    'type': 'speak',
                    'text': sentence.strip(),
                    'duration': 4
                })
                
                commands.append({
                    'type': 'write',
                    'text': f"• {sentence.strip()[:50]}...",
                    'x': 10,
                    'y': y_pos,
                    'font_size': 14,
                    'color': '#374151'
                })
                
                y_pos += 8
        
        # Add visual element
        commands.append({
            'type': 'draw',
            'shape': 'rectangle',
            'x': 70,
            'y': 20,
            'width': 25,
            'height': 30,
            'color': '#e5e7eb',
            'stroke': '#9ca3af'
        })
        
        commands.append({
            'type': 'speak',
            'text': 'That concludes our lesson. Any questions?',
            'duration': 3
        })
        
        logger.info(f"Generated {len(commands)} fallback lesson commands")
        return commands

    async def send_error(self, message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }))

    async def handle_conversation_message(self, data):
        """Handle conversation messages from Dashboard integration"""
        try:
            conversation_id = data.get('conversation_id', self.session_id)
            user_id = data.get('user_id', 'anonymous')
            
            # Extract message content from various possible fields
            message_content = data.get('message', data.get('content', data.get('text', '')))
            
            if not message_content:
                # Try to construct message from available data
                if 'topic' in data:
                    message_content = f"Let's discuss {data['topic']}"
                else:
                    message_content = "New conversation started"
            
            logger.info(f"Processing conversation message from {user_id}: {message_content[:100]}...")
            
            # Store conversation info in session (simplified)
            if self.session_id in self.temp_sessions:
                if 'conversations' not in self.temp_sessions[self.session_id]:
                    self.temp_sessions[self.session_id]['conversations'] = []
                
                self.temp_sessions[self.session_id]['conversations'].append({
                    'conversation_id': conversation_id,
                    'message': message_content,
                    'user_id': user_id,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            
            # Generate AI teacher response (simplified to avoid session dependency)
            ai_response = f"Hello! I understand you want to discuss: {message_content[:100]}. I'm here to help you learn! Feel free to ask questions and I'll use the whiteboard to explain concepts."
            
            # Send response back to client
            response_data = {
                'type': 'conversation_response',
                'message': ai_response,
                'original_message': message_content,
                'conversation_id': conversation_id,
                'session_id': self.session_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Sending conversation response for: {conversation_id}")
            await self.send(text_data=json.dumps(response_data))
            logger.info(f"Conversation response sent successfully")
            
        except Exception as e:
            logger.error(f"Error handling conversation message: {e}")
            logger.error(f"Conversation data received: {data}")
            try:
                await self.send_error('Failed to process conversation message')
            except:
                logger.error("Failed to send error response")

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

    async def generate_lesson_from_pdf(self, pdf_text, topic, filename):
        """Generate structured lesson commands from PDF content"""
        try:
            # If no text content, create a basic lesson structure
            if not pdf_text or pdf_text == 'undefined':
                return await self.create_basic_lesson(topic, filename)
            
            # Analyze PDF content and create lesson commands
            lesson_commands = []
            
            # Introduction
            lesson_commands.extend([
                {
                    "type": "speak",
                    "text": f"Welcome! Today we'll learn about {topic} from your document {filename}.",
                    "duration": 3000
                },
                {
                    "type": "write",
                    "text": topic.upper(),
                    "x": 400,
                    "y": 50,
                    "fontSize": 28,
                    "fontStyle": "bold",
                    "fill": "#2563eb",
                    "duration": 2000
                },
                {
                    "type": "draw",
                    "shape": "line",
                    "points": [200, 80, 600, 80],
                    "stroke": "#2563eb",
                    "strokeWidth": 3,
                    "duration": 1000
                }
            ])
            
            # Extract key concepts from PDF text (simplified extraction)
            key_concepts = self.extract_key_concepts(pdf_text)
            
            y_position = 120
            for i, concept in enumerate(key_concepts[:5]):  # Limit to 5 concepts
                lesson_commands.extend([
                    {
                        "type": "speak",
                        "text": f"Let's discuss {concept}.",
                        "duration": 2000
                    },
                    {
                        "type": "write",
                        "text": f"{i+1}. {concept}",
                        "x": 50,
                        "y": y_position,
                        "fontSize": 18,
                        "fill": "#1f2937",
                        "duration": 2000
                    },
                    {
                        "type": "draw",
                        "shape": "circle",
                        "x": 30,
                        "y": y_position + 5,
                        "radius": 8,
                        "fill": "#10b981",
                        "duration": 500
                    }
                ])
                y_position += 40
            
            # Add interactive elements
            lesson_commands.extend([
                {
                    "type": "speak",
                    "text": "Now I'll draw a diagram to help you visualize these concepts.",
                    "duration": 3000
                },
                {
                    "type": "draw",
                    "shape": "rect",
                    "x": 450,
                    "y": 150,
                    "width": 300,
                    "height": 200,
                    "stroke": "#3b82f6",
                    "strokeWidth": 2,
                    "fill": "rgba(59, 130, 246, 0.1)",
                    "duration": 2000
                },
                {
                    "type": "write",
                    "text": "Key Concepts",
                    "x": 550,
                    "y": 170,
                    "fontSize": 16,
                    "fontStyle": "bold",
                    "fill": "#3b82f6",
                    "duration": 1500
                },
                {
                    "type": "speak",
                    "text": "Feel free to ask me questions about any of these concepts!",
                    "duration": 3000
                }
            ])
            
            return lesson_commands
            
        except Exception as e:
            logger.error(f"Error generating lesson from PDF: {e}")
            return await self.create_basic_lesson(topic, filename)
    
    def extract_key_concepts(self, text):
        """Extract key concepts from PDF text"""
        if not text or text == 'undefined':
            return ["Introduction", "Key Points", "Examples", "Summary"]
        
        # Simple keyword extraction (can be enhanced with NLP)
        words = text.lower().split()
        
        # Common important words/concepts
        important_keywords = []
        
        # Look for capitalized words (likely concepts)
        sentences = text.split('.')
        for sentence in sentences[:10]:  # First 10 sentences
            words_in_sentence = sentence.split()
            for word in words_in_sentence:
                if word.istitle() and len(word) > 3 and word not in important_keywords:
                    important_keywords.append(word)
                    if len(important_keywords) >= 5:
                        break
            if len(important_keywords) >= 5:
                break
        
        return important_keywords if important_keywords else ["Introduction", "Key Points", "Examples", "Summary"]
    
    async def create_basic_lesson(self, topic, filename):
        """Create a basic lesson structure when PDF text is not available"""
        return [
            {
                "type": "speak",
                "text": f"I've received your document about {topic}. Let me create a lesson structure for you.",
                "duration": 4000
            },
            {
                "type": "write",
                "text": topic.upper(),
                "x": 400,
                "y": 50,
                "fontSize": 24,
                "fontStyle": "bold",
                "fill": "#2563eb",
                "duration": 2000
            },
            {
                "type": "write",
                "text": f"Document: {filename}",
                "x": 50,
                "y": 120,
                "fontSize": 16,
                "fill": "#6b7280",
                "duration": 2000
            },
            {
                "type": "speak",
                "text": "Please make sure your PDF has readable text content so I can create a more detailed lesson.",
                "duration": 4000
            },
            {
                "type": "draw",
                "shape": "rect",
                "x": 50,
                "y": 180,
                "width": 700,
                "height": 300,
                "stroke": "#d1d5db",
                "strokeWidth": 2,
                "fill": "rgba(249, 250, 251, 0.5)",
                "duration": 1500
            },
            {
                "type": "write",
                "text": "Upload a PDF with text content to generate\na comprehensive interactive lesson!",
                "x": 400,
                "y": 320,
                "fontSize": 18,
                "fill": "#374151",
                "align": "center",
                "duration": 3000
            }
        ]

    async def generate_explanation_commands(self, message, topic):
        """Generate drawing commands for explanations"""
        return [
            {
                "type": "speak",
                "text": f"Let me explain: {message}",
                "duration": 2000
            },
            {
                "type": "write",
                "text": "Explanation:",
                "x": 50,
                "y": 400,
                "fontSize": 20,
                "fontStyle": "bold",
                "fill": "#059669",
                "duration": 1500
            },
            {
                "type": "write",
                "text": message[:100] + "...",
                "x": 50,
                "y": 440,
                "fontSize": 16,
                "fill": "#374151",
                "duration": 3000
            }
        ]