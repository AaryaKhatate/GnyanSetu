# teacher_app/consumers.py

import json
import re
import logging
from typing import Optional
from datetime import datetime
from bson import ObjectId

import google.generativeai as genai
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from langchain.prompts import PromptTemplate # Corrected import
from .mongo_collections import conversations, messages
from .mongo import create_conversation, create_message
from .mongo_collections import conversations, messages
from .mongo import create_conversation, create_message
from bson import ObjectId

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
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
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
    text = text.replace('e.g.', 'for example')
    text = text.replace('i.e.', 'that is')
    text = text.replace('etc.', 'and so on')
    text = text.replace('vs.', 'versus')
    text = text.replace('w/', 'with')
    text = text.replace('w/o', 'without')
    
    # Add pauses for better speech rhythm
    text = re.sub(r'\.', '. ', text)
    text = re.sub(r'\?', '? ', text)
    text = re.sub(r'!', '! ', text)
    text = re.sub(r';', '; ', text)
    text = re.sub(r':', ': ', text)
    
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


class TeacherConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        api_key = getattr(settings, "GOOGLE_API_KEY", None)
        print(f"DEBUG: Google API Key configured: {bool(api_key)}")
        if api_key:
            print(f"DEBUG: API Key starts with: {api_key[:10]}...")
        genai.configure(api_key=api_key)
        self._buffer = ""
        self._seen_hashes = set()
        self.current_conversation_id = None
        self.is_generating = False  # Prevent duplicate processing
        self.teaching_steps = []    # Buffer for synchronized lesson
        await self.send_json({"type": "status", "message": "Connected! Ready for a topic or PDF."})

    async def disconnect(self, close_code):
        logger.info("WebSocket disconnected: %s", close_code)

    async def receive(self, text_data=None, bytes_data=None):
        print(f"DEBUG: Received WebSocket message: {text_data[:200]}...")
        
        # Prevent duplicate processing
        if hasattr(self, 'is_generating') and self.is_generating:
            print("DEBUG: Lesson generation already in progress, ignoring duplicate request")
            return
            
        try:
            payload = json.loads(text_data)
            topic = payload.get("topic", "").strip()
            pdf_text = payload.get("pdf_text", "").strip()
            pdf_filename = payload.get("pdf_filename", "").strip()
            user_id = payload.get("user_id")  # Should be passed from frontend
            conversation_id = payload.get("conversation_id")  # For continuing existing conversation
            
            print(f"DEBUG: Topic: {topic[:50]}, PDF text length: {len(pdf_text)}")

            if not topic and not pdf_text:
                await self.send_json({"type": "error", "message": "Please provide a topic or a PDF."})
                return

            # Set generation flag
            self.is_generating = True
            
            # Reset for new lesson
            self._buffer = ""
            self._seen_hashes = set()
            self.teaching_steps = []
            
            # Send lesson start message
            await self.send_json({
                "type": "lesson_start", 
                "message": f"Generating lesson content for: {topic or pdf_filename}",
                "status": "generating"
            })

            # Create or get conversation
            if conversation_id:
                try:
                    # Validate ObjectId format (24-character hex string)
                    if isinstance(conversation_id, str) and len(conversation_id) == 24:
                        self.current_conversation_id = ObjectId(conversation_id)
                        print(f"DEBUG: Using existing conversation: {conversation_id}")
                    else:
                        print(f"DEBUG: Invalid conversation ID format '{conversation_id}', creating new conversation")
                        conversation_id = None
                except Exception as e:
                    print(f"DEBUG: Invalid conversation ID '{conversation_id}', creating new conversation: {e}")
                    conversation_id = None
                    
            if not conversation_id:
                # Create new conversation (only if MongoDB is available)
                if conversations is not None:
                    try:
                        title = topic if topic else f"PDF: {pdf_filename}" if pdf_filename else "New Lesson"
                        conversation_doc = create_conversation(
                            user_id=user_id or "anonymous",
                            title=title,
                            topic=topic,
                            pdf_filename=pdf_filename
                        )
                        result = await conversations.insert_one(conversation_doc)
                        self.current_conversation_id = result.inserted_id
                        
                        # Send conversation ID back to frontend
                        await self.send_json({
                            "type": "conversation_created", 
                            "conversation_id": str(self.current_conversation_id),
                            "title": title
                        })
                    except Exception as e:
                        print(f"DEBUG: Error creating conversation: {e}")
                        self.current_conversation_id = None
                else:
                    print("MongoDB not available - skipping conversation creation")
                    self.current_conversation_id = None

            # Save user message (only if MongoDB is available)
            if messages is not None and self.current_conversation_id:
                try:
                    user_content = f"Topic: {topic}" if topic else f"PDF: {pdf_filename}"
                    user_message = create_message(
                        conversation_id=self.current_conversation_id,
                        sender="user",
                        content=user_content,
                        message_type="topic_request"
                    )
                    await messages.insert_one(user_message)
                except Exception as e:
                    print(f"DEBUG: Error saving user message: {e}")

            lesson_content = f"Topic: {topic}"
            if pdf_text:
                max_pdf_text_length = 15000 
                lesson_content += f"\n\nUse the following content to create the lesson:\n\n---\n{pdf_text[:max_pdf_text_length]}\n---"

            # Generate lesson content synchronously
            await self.generate_complete_lesson(lesson_content)

        except json.JSONDecodeError:
            print("DEBUG: JSON decode error")
            await self.send_json({"type": "error", "message": "Invalid JSON payload."})
            self.is_generating = False
            return
        except Exception as e:
            print(f"DEBUG: Error in receive: {e}")
            await self.send_json({"type": "error", "message": f"Error processing request: {str(e)}"})
            self.is_generating = False

    async def process_buffer_for_steps(self):
        """Process buffer for complete lesson steps and send them to frontend"""
        start = 0
        while True:
            s = self._buffer.find(STEP_START, start)
            if s == -1:
                break
            e = self._buffer.find(STEP_END, s + len(STEP_START))
            if e == -1:
                break
            
            print(f"DEBUG: Found step block from {s} to {e}")
            block = self._buffer[s + len(STEP_START): e]
            
            try:
                raw = strip_code_fences(block)
                print(f"DEBUG: Raw block after strip: {raw[:200]}...")
                step_obj = json.loads(raw)
                print(f"DEBUG: Parsed step object keys: {list(step_obj.keys())}")
            except Exception as ex:
                print(f"DEBUG: JSON parse error: {str(ex)}")
                preview = (block[:200] + "...") if len(block) > 200 else block
                await self.send_json({"type": "status", "message": "JSON parse failed. Preview: " + preview})
                start = e + len(STEP_END)
                continue

            h = hash(json.dumps(step_obj, sort_keys=True))
            if h in self._seen_hashes:
                print(f"DEBUG: Duplicate step detected, skipping")
                start = e + len(STEP_END)
                continue
            self._seen_hashes.add(h)

            if isinstance(step_obj, dict) and "notes_and_quiz_ready" in step_obj:
                print(f"DEBUG: Sending notes and quiz")
                await self.send_json({"type": "notes_and_quiz_ready", "data": step_obj["notes_and_quiz_ready"]})
                
                # Save notes and quiz to chat history
                if self.current_conversation_id and messages is not None:
                    try:
                        notes_message = create_message(
                            conversation_id=self.current_conversation_id,
                            sender="ai",
                            content="Notes and quiz generated",
                            message_type="notes_and_quiz",
                            step_data=step_obj["notes_and_quiz_ready"]
                        )
                        await messages.insert_one(notes_message)
                    except Exception as e:
                        print(f"DEBUG: Error saving notes message: {e}")
                        
            elif isinstance(step_obj, dict):
                print(f"DEBUG: Processing lesson step with text: {step_obj.get('text_explanation', '')[:100]}...")
                cmds = step_obj.get("whiteboard_commands", [])
                sanitized = [sc for c in cmds if (sc := sanitize_command(c))]
                step_obj["whiteboard_commands"] = sanitized
                step_obj["text_explanation"] = step_obj.get("text_explanation", "")
                step_obj["tts_text"] = step_obj.get("tts_text", step_obj.get("text_explanation", ""))
                print(f"DEBUG: Sending lesson step to frontend")
                await self.send_json({"type": "lesson_step", "data": step_obj})
                print(f"DEBUG: Lesson step sent successfully")
                
                # Save lesson step to chat history
                if self.current_conversation_id and messages is not None:
                    try:
                        step_message = create_message(
                            conversation_id=self.current_conversation_id,
                            sender="ai",
                            content=step_obj.get("text_explanation", ""),
                            message_type="lesson_step",
                            step_data=step_obj
                        )
                        await messages.insert_one(step_message)
                    except Exception as e:
                        print(f"DEBUG: Error saving step message: {e}")
            
            self._buffer = self._buffer[e + len(STEP_END):]
            start = 0

    async def generate_complete_lesson(self, lesson_content):
        """Generate complete lesson content and send synchronized steps"""
        try:
            prompt_template = PromptTemplate(
                input_variables=["lesson_content", "step_start", "step_end", "lesson_end"],
                template=(
                    "You are an engaging AI Virtual Teacher with a whiteboard. Create an interactive visual lesson based on: '{lesson_content}'.\n\n"
                    "**CRITICAL FORMAT REQUIREMENTS**:\n"
                    "1. Create exactly 4-6 teaching steps, each with proper JSON format.\n"
                    "2. Each step MUST be wrapped between {step_start} and {step_end} markers.\n"
                    "3. Use this EXACT JSON format for each step:\n\n"
                    "{step_start}\n"
                    "{{\n"
                    '  "step": 1,\n'
                    '  "speech_text": "Hello everyone! Today we will learn about [topic]. Let me start by writing the main concept on our whiteboard.",\n'
                    '  "speech_duration": 8000,\n'
                    '  "drawing_commands": [\n'
                    '    {{\n'
                    '      "time": 1000,\n'
                    '      "action": "draw_text",\n'
                    '      "text": "Main Topic Title",\n'
                    '      "x": 400,\n'
                    '      "y": 80,\n'
                    '      "fontSize": 32,\n'
                    '      "color": "#2563eb",\n'
                    '      "fontStyle": "bold"\n'
                    '    }},\n'
                    '    {{\n'
                    '      "time": 4000,\n'
                    '      "action": "draw_rectangle",\n'
                    '      "x": 200,\n'
                    '      "y": 150,\n'
                    '      "width": 400,\n'
                    '      "height": 100,\n'
                    '      "color": "#059669",\n'
                    '      "strokeWidth": 3\n'
                    '    }}\n'
                    '  ]\n'
                    "}}\n"
                    "{step_end}\n\n"
                    "**SPEECH GUIDELINES**:\n"
                    "- Make speech natural and conversational (like 'Hello everyone!', 'Now let me show you...', 'As you can see here...')\n"
                    "- Speech should be 6-10 seconds long (speech_duration: 6000-10000)\n"
                    "- Explain what you're drawing as you draw it\n"
                    "- Use encouraging teacher language\n\n"
                    "**DRAWING COMMANDS**:\n"
                    "- draw_text: {{'action': 'draw_text', 'text': 'Your Text', 'x': 400, 'y': 100, 'fontSize': 24, 'color': '#333', 'fontStyle': 'normal'}}\n"
                    "- draw_rectangle: {{'action': 'draw_rectangle', 'x': 100, 'y': 100, 'width': 200, 'height': 100, 'color': '#0066cc', 'strokeWidth': 2}}\n"
                    "- draw_circle: {{'action': 'draw_circle', 'x': 200, 'y': 200, 'radius': 50, 'color': '#dc2626', 'strokeWidth': 2}}\n"
                    "- draw_arrow: {{'action': 'draw_arrow', 'points': [100, 100, 200, 200], 'color': '#059669', 'strokeWidth': 3}}\n\n"
                    "**COORDINATE SYSTEM**: Canvas is 800x600, (0,0) is top-left\n"
                    "**TIMING**: time in milliseconds from speech start (0 = immediately, 3000 = after 3 seconds)\n\n"
                    "Create a complete lesson with clear step-by-step teaching, then end with {lesson_end}.\n"
                )
            )

            prompt = prompt_template.format(lesson_content=lesson_content, step_start=STEP_START, step_end=STEP_END, lesson_end=LESSON_END)

            await self.send_json({"type": "generation_progress", "status": "Starting AI generation...", "buffer_length": 0})

            print("DEBUG: Starting Google Generative AI model call...")
            model = genai.GenerativeModel("gemini-1.5-flash")
            print("DEBUG: Model created, starting stream...")
            
            # Generate complete content first
            full_content = ""
            chunk_count = 0
            
            try:
                stream = await model.generate_content_async(prompt, stream=True)
                print("DEBUG: Stream started, processing chunks...")

                async for chunk in stream:
                    chunk_count += 1
                    print(f"DEBUG: Processing chunk {chunk_count}")
                    text = getattr(chunk, "text", "") or ""
                    print(f"DEBUG: Chunk text length: {len(text)}")
                    
                    if not text:
                        print("DEBUG: Empty chunk, continuing...")
                        continue
                        
                    full_content += text
                    print(f"DEBUG: Full content length now: {len(full_content)}")

                    # Send progress updates
                    if len(full_content) % 200 < 50:  # Update every ~200 characters
                        await self.send_json({
                            "type": "generation_progress", 
                            "buffer_length": len(full_content),
                            "status": f"Generating... ({len(full_content)} characters)"
                        })
                        
            except Exception as ai_error:
                print(f"DEBUG: AI generation error: {ai_error}")
                await self.send_json({"type": "error", "message": f"AI service error: {str(ai_error)}"})
                return

            print(f"DEBUG: Complete content generated, length: {len(full_content)}")
            
            # Process all teaching steps at once
            teaching_steps = await self.parse_all_teaching_steps(full_content)
            
            if teaching_steps:
                # Send all steps to frontend for synchronized playback
                await self.send_json({
                    "type": "lesson_ready",
                    "total_steps": len(teaching_steps),
                    "teaching_steps": teaching_steps,
                    "message": f"Lesson ready with {len(teaching_steps)} steps"
                })
                
                # Store the lesson in database
                await self.store_lesson_steps(teaching_steps)
                
                print(f"DEBUG: Lesson sent with {len(teaching_steps)} synchronized steps")
            else:
                await self.send_json({
                    "type": "error",
                    "message": "Failed to parse teaching steps from generated content"
                })

        except Exception as e:
            print(f"DEBUG: Error in lesson generation: {e}")
            await self.send_json({"type": "error", "message": f"Error generating lesson: {str(e)}"})
        finally:
            # Reset generation flag
            self.is_generating = False
            # Only send lesson_end if we actually generated content (not for duplicate requests)
            if hasattr(self, 'teaching_steps') and len(self.teaching_steps) > 0:
                await self.send_json({"type": "lesson_end", "message": "Lesson generation finished."})
            else:
                print("DEBUG: Skipping lesson_end - no content generated (likely duplicate request)")

    async def parse_all_teaching_steps(self, content):
        """Parse all teaching steps from complete content"""
        teaching_steps = []
        
        try:
            # Look for step blocks in the content
            start = 0
            while True:
                s = content.find(STEP_START, start)
                if s == -1:
                    break
                e = content.find(STEP_END, s + len(STEP_START))
                if e == -1:
                    break
                
                print(f"DEBUG: Found step block from {s} to {e}")
                block = content[s + len(STEP_START): e]
                
                try:
                    # Clean and parse the JSON
                    clean_block = strip_code_fences(block.strip())
                    step_data = json.loads(clean_block)
                    
                    # Validate required fields
                    if all(key in step_data for key in ['step', 'speech_text', 'speech_duration', 'drawing_commands']):
                        # Clean speech text
                        step_data['speech_text'] = clean_text_for_speech(step_data['speech_text'])
                        teaching_steps.append(step_data)
                        print(f"DEBUG: Parsed teaching step {step_data.get('step', len(teaching_steps))}")
                    else:
                        print(f"DEBUG: Invalid step format: {step_data}")
                        
                except json.JSONDecodeError as json_error:
                    print(f"DEBUG: JSON parse error for step: {json_error}")
                    print(f"DEBUG: Block content: {block[:200]}...")
                    
                start = e + len(STEP_END)
                
        except Exception as e:
            print(f"DEBUG: Error parsing teaching steps: {e}")
        
        # Sort steps by step number
        teaching_steps.sort(key=lambda x: x.get('step', 0))
        print(f"DEBUG: Total teaching steps parsed: {len(teaching_steps)}")
        
        return teaching_steps

    async def store_lesson_steps(self, teaching_steps):
        """Store all teaching steps in database"""
        if not self.current_conversation_id or messages is None:
            print("DEBUG: Skipping database storage - no conversation ID or MongoDB unavailable")
            return
            
        try:
            for step in teaching_steps:
                message_doc = {
                    "conversation_id": self.current_conversation_id,
                    "sender": "ai",
                    "content": step['speech_text'],
                    "message_type": "teaching_step",
                    "step_data": step,
                    "timestamp": datetime.utcnow()
                }
                
                try:
                    await messages.insert_one(message_doc)
                except Exception as e:
                    print(f"DEBUG: Error storing step {step.get('step')}: {e}")
                    
        except Exception as e:
            print(f"DEBUG: Error storing lesson steps: {e}")


    async def send_json(self, obj):
        await self.send(text_data=json.dumps(obj))