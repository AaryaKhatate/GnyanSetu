# teacher_app/consumers.py - FIXED VERSION

import json
import re
import logging
from typing import Optional
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId

import google.generativeai as genai
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from langchain.prompts import PromptTemplate
from .mongo_collections import conversations, messages
from .mongo import create_conversation, create_message

logger = logging.getLogger(__name__)

# MARKERS for deterministic streaming
STEP_START = "@@STEP_START@@"
STEP_END = "@@STEP_END@@"
LESSON_END = "@@LESSON_END@@"

# Allowed whiteboard commands (server side sanitization)
ALLOWED_ACTIONS = {"clear_all", "write_text", "draw_shape", "draw_arrow"}
ALLOWED_SHAPES = {"rect", "circle"}
MAX_PERCENT = 100
MIN_PERCENT = 0

def clamp(value, lo, hi):
    try:
        v = float(value)
    except (ValueError, TypeError):
        return lo
    return max(lo, min(hi, v))

def sanitize_command(cmd: dict) -> Optional[dict]:
    """Return sanitized command dict or None if invalid."""
    if not isinstance(cmd, dict):
        return None
    action = cmd.get("action")
    if action not in ALLOWED_ACTIONS:
        return None

    out = {"action": action}
    if action == "clear_all":
        return out

    if action == "write_text":
        text = str(cmd.get("text", ""))[:1200]
        out.update({
            "text": text,
            "x_percent": clamp(cmd.get("x_percent", 0), MIN_PERCENT, MAX_PERCENT),
            "y_percent": clamp(cmd.get("y_percent", 0), MIN_PERCENT, MAX_PERCENT),
            "font_size": int(clamp(cmd.get("font_size", 20), 8, 200)),
            "color": str(cmd.get("color", "black"))[:32],
            "align": cmd.get("align", "left") if cmd.get("align") in ("left", "center") else "left"
        })
        return out

    if action == "draw_shape":
        shape = cmd.get("shape")
        if shape not in ALLOWED_SHAPES:
            return None
        out.update({
            "shape": shape,
            "x_percent": clamp(cmd.get("x_percent", 0), MIN_PERCENT, MAX_PERCENT),
            "y_percent": clamp(cmd.get("y_percent", 0), MIN_PERCENT, MAX_PERCENT),
            "width_percent": clamp(cmd.get("width_percent", 10), 0.1, MAX_PERCENT),
            "height_percent": clamp(cmd.get("height_percent", 10), 0.1, MAX_PERCENT),
            "color": str(cmd.get("color", "#f3f4f6"))[:32],
            "stroke": str(cmd.get("stroke", "black"))[:32]
        })
        return out

    if action == "draw_arrow":
        pts = cmd.get("points", [])
        if not (isinstance(pts, list) and len(pts) == 4):
            return None
        pts_clamped = [clamp(p, MIN_PERCENT, MAX_PERCENT) for p in pts]
        out.update({
            "points": pts_clamped,
            "color": str(cmd.get("color", "black"))[:32]
        })
        return out

    return None

def strip_code_fences(text: str) -> str:
    """Remove markdown code fences from text."""
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    return text.strip()

def clean_text_for_speech(text: str) -> str:
    """Clean text to make it more suitable for speech synthesis"""
    if not text:
        return ""

    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
    text = re.sub(r'`(.*?)`', r'\1', text)        # Code

    # Replace abbreviations with full words
    replacements = {
        'e.g.': 'for example',
        'i.e.': 'that is',
        'etc.': 'and so on',
        'vs.': 'versus',
        'w/': 'with',
        'w/o': 'without'
    }
    
    for abbrev, full in replacements.items():
        text = text.replace(abbrev, full)

    # Add pauses for better speech rhythm
    text = re.sub(r'\.(?!\s)', '. ', text)
    text = re.sub(r'\?(?!\s)', '? ', text)
    text = re.sub(r'!(?!\s)', '! ', text)
    text = re.sub(r';(?!\s)', '; ', text)
    text = re.sub(r':(?!\s)', ': ', text)

    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


class TeacherConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Initialize WebSocket connection and configure AI service."""
        try:
            await self.accept()
            
            # Configure Google AI
            api_key = getattr(settings, "GOOGLE_API_KEY", None)
            if not api_key:
                logger.error("Google API key not configured")
                await self.send_json({"type": "error", "message": "AI service not configured"})
                return
                
            genai.configure(api_key=api_key)
            
            # Initialize consumer state
            self.current_conversation_id = None
            self.is_generating = False
            self.teaching_steps = []
            
            await self.send_json({"type": "status", "message": "Connected! Ready for a topic or PDF."})
            logger.info("WebSocket connection established successfully")
            
        except Exception as e:
            logger.error(f"Error in connect: {e}")
            await self.send_json({"type": "error", "message": "Connection failed"})

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        logger.info(f"WebSocket disconnected with code: {close_code}")
        # Clean up any ongoing operations
        self.is_generating = False

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages."""
        if not text_data:
            await self.send_json({"type": "error", "message": "No data received"})
            return

        # Prevent duplicate processing
        if self.is_generating:
            logger.warning("Lesson generation already in progress, ignoring duplicate request")
            return

        try:
            payload = json.loads(text_data)
            
            # Extract and validate required fields
            topic = payload.get("topic", "").strip()
            pdf_text = payload.get("pdf_text", "").strip()
            pdf_filename = payload.get("pdf_filename", "").strip()
            user_id = payload.get("user_id", "anonymous")
            conversation_id = payload.get("conversation_id")

            if not topic and not pdf_text:
                await self.send_json({"type": "error", "message": "Please provide a topic or a PDF."})
                return

            # Set generation flag early to prevent duplicates
            self.is_generating = True
            
            # Reset state for new lesson
            self.teaching_steps = []

            # Send lesson start message
            lesson_subject = topic or f"PDF: {pdf_filename}"
            await self.send_json({
                "type": "lesson_start",
                "message": f"Generating lesson content for: {lesson_subject}",
                "status": "generating"
            })

            # Handle conversation management
            await self.handle_conversation_setup(conversation_id, user_id, topic, pdf_filename)

            # Save user message to database
            await self.save_user_message(topic, pdf_filename)

            # Generate complete lesson content
            lesson_content = self.prepare_lesson_content(topic, pdf_text)
            await self.generate_complete_lesson(lesson_content)

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            await self.send_json({"type": "error", "message": "Invalid request format"})
        except Exception as e:
            logger.error(f"Error in receive: {e}")
            await self.send_json({"type": "error", "message": f"Error processing request: {str(e)}"})
        finally:
            self.is_generating = False

    async def handle_conversation_setup(self, conversation_id, user_id, topic, pdf_filename):
        """Handle conversation creation or retrieval."""
        if conversation_id:
            try:
                if isinstance(conversation_id, str) and len(conversation_id) == 24:
                    self.current_conversation_id = ObjectId(conversation_id)
                    logger.info(f"Using existing conversation: {conversation_id}")
                else:
                    logger.warning(f"Invalid conversation ID format: {conversation_id}")
                    conversation_id = None
            except Exception as e:
                logger.error(f"Invalid conversation ID: {e}")
                conversation_id = None

        if not conversation_id and conversations is not None:
            try:
                title = topic if topic else f"PDF: {pdf_filename}" if pdf_filename else "New Lesson"
                conversation_doc = create_conversation(
                    user_id=user_id,
                    title=title,
                    topic=topic,
                    pdf_filename=pdf_filename
                )
                result = await conversations.insert_one(conversation_doc)
                self.current_conversation_id = result.inserted_id

                await self.send_json({
                    "type": "conversation_created",
                    "conversation_id": str(self.current_conversation_id),
                    "title": title
                })
                logger.info(f"Created new conversation: {self.current_conversation_id}")
                
            except Exception as e:
                logger.error(f"Error creating conversation: {e}")
                self.current_conversation_id = None

    async def save_user_message(self, topic, pdf_filename):
        """Save user message to database."""
        if messages is None or not self.current_conversation_id:
            return

        try:
            user_content = f"Topic: {topic}" if topic else f"PDF: {pdf_filename}"
            user_message = create_message(
                conversation_id=self.current_conversation_id,
                sender="user",
                content=user_content,
                message_type="topic_request"
            )
            await messages.insert_one(user_message)
            logger.info("User message saved to database")
            
        except Exception as e:
            logger.error(f"Error saving user message: {e}")

    def prepare_lesson_content(self, topic, pdf_text):
        """Prepare lesson content for AI generation."""
        lesson_content = f"Topic: {topic}"
        if pdf_text:
            max_pdf_length = 15000
            truncated_text = pdf_text[:max_pdf_length]
            lesson_content += f"\n\nUse the following content to create the lesson:\n\n---\n{truncated_text}\n---"
        return lesson_content

    async def generate_complete_lesson(self, lesson_content):
        """Generate complete lesson content using AI and send synchronized steps."""
        try:
            # Create AI prompt
            prompt_template = PromptTemplate(
                input_variables=["lesson_content", "step_start", "step_end", "lesson_end"],
                template=self.get_lesson_prompt_template()
            )

            prompt = prompt_template.format(
                lesson_content=lesson_content, 
                step_start=STEP_START, 
                step_end=STEP_END, 
                lesson_end=LESSON_END
            )

            await self.send_json({
                "type": "generation_progress", 
                "status": "Starting AI generation...", 
                "progress": 0
            })

            # Generate content using Google AI
            full_content = await self.generate_ai_content(prompt)
            
            if not full_content:
                await self.send_json({"type": "error", "message": "Failed to generate lesson content"})
                return

            # Parse teaching steps from generated content
            teaching_steps = await self.parse_all_teaching_steps(full_content)

            if teaching_steps:
                # Send synchronized lesson to frontend
                await self.send_json({
                    "type": "lesson_ready",
                    "total_steps": len(teaching_steps),
                    "teaching_steps": teaching_steps,
                    "message": f"Lesson ready with {len(teaching_steps)} steps"
                })

                # Store lesson in database
                await self.store_lesson_steps(teaching_steps)
                
                logger.info(f"Lesson generated successfully with {len(teaching_steps)} steps")
            else:
                await self.send_json({
                    "type": "error",
                    "message": "Failed to parse teaching steps from generated content"
                })

        except Exception as e:
            logger.error(f"Error in lesson generation: {e}")
            await self.send_json({"type": "error", "message": f"Error generating lesson: {str(e)}"})
        finally:
            # Send lesson completion signal
            await self.send_json({"type": "lesson_end", "message": "Lesson generation finished."})

    async def generate_ai_content(self, prompt):
        """Generate content using Google AI with proper error handling."""
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            full_content = ""
            chunk_count = 0

            stream = await model.generate_content_async(prompt, stream=True)
            logger.info("AI content generation started")

            async for chunk in stream:
                chunk_count += 1
                text = getattr(chunk, "text", "") or ""
                
                if text:
                    full_content += text
                    
                    # Send progress updates periodically
                    if chunk_count % 5 == 0:
                        await self.send_json({
                            "type": "generation_progress",
                            "status": f"Generating... ({len(full_content)} characters)",
                            "progress": min(90, chunk_count * 2)  # Cap at 90% during generation
                        })

            logger.info(f"AI generation completed: {len(full_content)} characters")
            return full_content

        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return None

    def get_lesson_prompt_template(self):
        """Return the optimized lesson generation prompt template."""
        return (
            "You are an engaging AI Virtual Teacher with a whiteboard. Create an interactive visual lesson based on: '{lesson_content}'.\n\n"
            "**CRITICAL FORMAT REQUIREMENTS**:\n"
            "1. Create exactly 4-6 teaching steps, each with proper JSON format.\n"
            "2. Each step MUST be wrapped between {step_start} and {step_end} markers.\n"
            "3. Use this EXACT JSON format for each step:\n\n"
            "{step_start}\n"
            "{{\n"
            '  "step": 1,\n'
            '  "speech_text": "Let\'s explore the fundamental concepts of [specific topic]. This is crucial because [explain importance]. We\'ll start by understanding the key principles.",\n'
            '  "speech_duration": 10000,\n'
            '  "text_explanation": "Detailed explanation of the concept being taught in this step.",\n'
            '  "drawing_commands": [\n'
            '    {{\n'
            '      "time": 1000,\n'
            '      "action": "draw_text",\n'
            '      "text": "Main Topic Title",\n'
            '      "x": 400,\n'
            '      "y": 80,\n'
            '      "fontSize": 28,\n'
            '      "color": "#2563eb",\n'
            '      "fontStyle": "bold"\n'
            '    }}\n'
            '  ]\n'
            "}}\n"
            "{step_end}\n\n"
            "**CONTENT GUIDELINES**:\n"
            "- Start immediately with substantive educational content\n"
            "- NO generic greetings like 'Hello everyone' or 'Welcome to'\n"
            "- Each step should teach a specific concept or skill\n"
            "- Build progressively from basic to advanced concepts\n"
            "- Use clear, engaging educational language\n"
            "- Include practical examples and applications\n\n"
            "**DRAWING COMMANDS** (Keep simple and effective):\n"
            "- draw_text: For titles, key points, and explanations\n"
            "- draw_rectangle: For highlighting important areas\n"
            "- draw_circle: For emphasis or grouping concepts\n"
            "- draw_arrow: For showing relationships or flow\n"
            "- Use 1-3 commands per step maximum\n"
            "- Focus on clarity over complexity\n\n"
            "Create a complete, educational lesson that teaches effectively, then end with {lesson_end}.\n"
        )

    async def parse_all_teaching_steps(self, content):
        """Parse all teaching steps from generated content with improved validation."""
        teaching_steps = []

        try:
            start_pos = 0
            while True:
                # Find step boundaries
                step_start = content.find(STEP_START, start_pos)
                if step_start == -1:
                    break
                    
                step_end = content.find(STEP_END, step_start + len(STEP_START))
                if step_end == -1:
                    break

                # Extract and clean step content
                step_block = content[step_start + len(STEP_START):step_end].strip()
                
                try:
                    # Parse JSON content
                    clean_block = strip_code_fences(step_block)
                    step_data = json.loads(clean_block)

                    # Validate required fields
                    if not self.validate_step_data(step_data):
                        logger.warning(f"Invalid step data: {list(step_data.keys())}")
                        start_pos = step_end + len(STEP_END)
                        continue

                    # Clean and enhance step data
                    step_data = self.enhance_step_data(step_data, len(teaching_steps) + 1)
                    teaching_steps.append(step_data)
                    
                    logger.info(f"Parsed teaching step {step_data.get('step')}")

                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error for step: {e}")
                except Exception as e:
                    logger.error(f"Error processing step: {e}")

                start_pos = step_end + len(STEP_END)

            # Sort steps by step number and validate sequence
            teaching_steps.sort(key=lambda x: x.get('step', 0))
            
            # Final validation
            if teaching_steps:
                self.validate_lesson_quality(teaching_steps)
                
            logger.info(f"Successfully parsed {len(teaching_steps)} teaching steps")
            return teaching_steps

        except Exception as e:
            logger.error(f"Error parsing teaching steps: {e}")
            return []

    def validate_step_data(self, step_data):
        """Validate that step data contains required fields."""
        required_fields = ['step', 'speech_text']
        return (isinstance(step_data, dict) and 
                all(field in step_data for field in required_fields) and
                step_data.get('speech_text', '').strip())

    def enhance_step_data(self, step_data, step_number):
        """Enhance step data with defaults and validation."""
        # Ensure step number
        step_data['step'] = step_data.get('step', step_number)
        
        # Clean speech text
        speech_text = step_data.get('speech_text', '').strip()
        if len(speech_text) < 20:
            speech_text = step_data.get('text_explanation', speech_text)
        
        step_data['speech_text'] = clean_text_for_speech(speech_text)
        
        # Ensure text explanation exists
        if 'text_explanation' not in step_data:
            step_data['text_explanation'] = step_data['speech_text']
        
        # Ensure drawing commands exist
        if 'drawing_commands' not in step_data:
            step_data['drawing_commands'] = []
        
        # Set reasonable speech duration if missing
        if 'speech_duration' not in step_data:
            word_count = len(step_data['speech_text'].split())
            step_data['speech_duration'] = max(8000, word_count * 400)  # ~150 WPM
        
        return step_data

    def validate_lesson_quality(self, teaching_steps):
        """Perform final quality validation on the complete lesson."""
        if not teaching_steps:
            return

        first_step = teaching_steps[0]
        speech_text = first_step.get('speech_text', '').lower()
        
        # Check for generic content
        generic_phrases = ['hello everyone', 'welcome to', 'good morning', 'today we will']
        if any(phrase in speech_text for phrase in generic_phrases):
            logger.warning("First step contains generic greeting content")
            
        # Ensure meaningful content length
        if len(first_step.get('speech_text', '')) < 50:
            logger.warning("First step has insufficient content")

        logger.info("Lesson quality validation completed")

    async def store_lesson_steps(self, teaching_steps):
        """Store all teaching steps in database with improved error handling."""
        if not self.current_conversation_id or messages is None:
            logger.info("Skipping database storage - no conversation ID or MongoDB unavailable")
            return
        
        stored_count = 0
        for step in teaching_steps:
            try:
                # Use the existing event loop instead of creating a new one
                message_doc = {
                    "conversation_id": self.current_conversation_id,
                    "sender": "ai",
                    "content": step.get('speech_text', ''),
                    "message_type": "teaching_step",
                    "step_data": step,
                    "timestamp": datetime.utcnow()
                }
                
                # Insert directly using await (we're already in async context)
                result = await messages.insert_one(message_doc)
                if result.inserted_id:
                    stored_count += 1
                    logger.info(f"Successfully stored step {step.get('step', 'unknown')}")
                
            except Exception as e:
                logger.error(f"Error storing step {step.get('step')}: {e}")
                # Continue with next step instead of failing completely
                continue
        
        logger.info(f"Stored {stored_count}/{len(teaching_steps)} steps in database")
        return stored_count


    async def send_json(self, data):
        """Send JSON data with error handling."""
        try:
            await self.send(text_data=json.dumps(data))
        except Exception as e:
            logger.error(f"Error sending JSON: {e}")

    async def create_new_conversation(self):
        """Create new conversation with proper error handling."""
        try:
            if conversations is None:
                raise Exception("Database not available")
            
            conversation_doc = create_conversation("anonymous", "New Lesson")
            result = await conversations.insert_one(conversation_doc)
            
            if result.inserted_id:
                self.current_conversation_id = result.inserted_id
                logger.info(f"Created new conversation: {result.inserted_id}")
                return str(result.inserted_id)
            else:
                raise Exception("Failed to create conversation")
                
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return None
