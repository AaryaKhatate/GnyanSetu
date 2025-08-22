# teacher_app/consumers.py

import json
import re
import logging
from typing import Optional

import google.generativeai as genai
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from langchain.prompts import PromptTemplate # Corrected import

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


class TeacherConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        genai.configure(api_key=getattr(settings, "GOOGLE_API_KEY", None))
        self._buffer = ""
        self._seen_hashes = set()
        await self.send_json({"type": "status", "message": "Connected! Ready for a topic or PDF."})

    async def disconnect(self, close_code):
        logger.info("WebSocket disconnected: %s", close_code)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            payload = json.loads(text_data)
            topic = payload.get("topic", "").strip()
            pdf_text = payload.get("pdf_text", "").strip()

            if not topic and not pdf_text:
                await self.send_json({"type": "error", "message": "Please provide a topic or a PDF."})
                return

            lesson_content = f"Topic: {topic}"
            if pdf_text:
                max_pdf_text_length = 15000 
                lesson_content += f"\n\nUse the following content to create the lesson:\n\n---\n{pdf_text[:max_pdf_text_length]}\n---"

        except json.JSONDecodeError:
            await self.send_json({"type": "error", "message": "Invalid JSON payload."})
            return

        prompt_template = PromptTemplate(
            input_variables=["lesson_content", "step_start", "step_end", "lesson_end"],
            template=(
                "You are an engaging AI Virtual Teacher. Your student is a complete beginner. "
                "Your task is to create a simple, step-by-step lesson based on the provided content:\n'{lesson_content}'.\n\n"
                "**VERY IMPORTANT RULES**:\n"
                "1.  Break the lesson into 4-8 small, easily digestible steps.\n"
                "2.  For each step, generate a JSON object wrapped between the exact markers {step_start} and {step_end}.\n"
                "3.  After the final step, generate one last JSON object for notes and a quiz, also wrapped in the markers.\n"
                "4.  End the entire generation with the single token {lesson_end} on a new line.\n"
                "5.  Use the whiteboard creatively! Use shapes to create diagrams, use text of different sizes and colors, and arrows to show connections. Make it feel like a real teacher at a whiteboard.\n\n"
                "**JSON Schemas**:\n\n"
                "// For a lesson step:\n"
                "{{\n"
                '  "text_explanation": "Simple explanation for the student.",\n'
                '  "tts_text": "Slightly more conversational text for text-to-speech.",\n'
                '  "whiteboard_commands": [ /* Array of whiteboard drawing commands */ ]\n'
                "}}\n\n"
                "// For the final notes & quiz object:\n"
                "{{\n"
                '  "notes_and_quiz_ready": {{\n'
                '      "notes_content": "<h2>Key Takeaways</h2><ul><li>...</li></ul>",\n'
                '      "quiz": [ {{ "question": "...", "options":[...], "correct": 0, "feedback":"..." }} ]\n'
                "  }}\n"
                "}}\n\n"
                "Now, begin the lesson.\n"
            )
        )

        prompt = prompt_template.format(lesson_content=lesson_content, step_start=STEP_START, step_end=STEP_END, lesson_end=LESSON_END)

        await self.send_json({"type": "status", "message": "Generating lesson..."})

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            stream = await model.generate_content_async(prompt, stream=True)

            async for chunk in stream:
                text = getattr(chunk, "text", "") or ""
                if not text:
                    continue
                self._buffer += text

                if len(self._buffer) % 100 < 20:
                     await self.send_json({"type": "status", "message": f"Streaming... (buf {len(self._buffer)})"})

                start = 0
                while True:
                    s = self._buffer.find(STEP_START, start)
                    if s == -1:
                        break
                    e = self._buffer.find(STEP_END, s + len(STEP_START))
                    if e == -1:
                        break
                    
                    block = self._buffer[s + len(STEP_START): e]
                    
                    try:
                        raw = strip_code_fences(block)
                        step_obj = json.loads(raw)
                    except Exception:
                        preview = (block[:200] + "...") if len(block) > 200 else block
                        await self.send_json({"type": "status", "message": "JSON parse failed. Preview: " + preview})
                        start = e + len(STEP_END)
                        continue

                    h = hash(json.dumps(step_obj, sort_keys=True))
                    if h in self._seen_hashes:
                        start = e + len(STEP_END)
                        continue
                    self._seen_hashes.add(h)

                    if isinstance(step_obj, dict) and "notes_and_quiz_ready" in step_obj:
                        await self.send_json({"type": "notes_and_quiz_ready", "data": step_obj["notes_and_quiz_ready"]})
                    elif isinstance(step_obj, dict):
                        cmds = step_obj.get("whiteboard_commands", [])
                        sanitized = [sc for c in cmds if (sc := sanitize_command(c))]
                        step_obj["whiteboard_commands"] = sanitized
                        step_obj["text_explanation"] = step_obj.get("text_explanation", "")
                        step_obj["tts_text"] = step_obj.get("tts_text", step_obj.get("text_explanation", ""))
                        await self.send_json({"type": "lesson_step", "data": step_obj})
                    
                    self._buffer = self._buffer[e + len(STEP_END):]
                    start = 0

        except Exception as e:
            logger.exception("Error during lesson generation: %s", e)
            preview = (self._buffer[:2000] + "...") if len(self._buffer) > 2000 else self._buffer
            await self.send_json({"type": "error", "message": f"An error occurred: {str(e)}", "raw_preview": preview})
        finally:
            # FIX: Ensure the client UI is re-enabled even if generation finishes abruptly
            await self.send_json({"type": "lesson_end", "message": "Lesson generation finished."})


    async def send_json(self, obj):
        await self.send(text_data=json.dumps(obj))