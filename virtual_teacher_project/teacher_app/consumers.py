import json
import google.generativeai as genai
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer

class TeacherConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        genai.configure(api_key=settings.GOOGLE_API_KEY)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        topic = text_data_json["topic"]

        await self.send(text_data=json.dumps({
            "type": "status",
            "message": f"Preparing your lesson on '{topic}'..."
        }))

        try:
            model = genai.GenerativeModel('gemini-2.5-pro')

            prompt = f"""
            You are an AI Virtual Teacher. Teach the topic "{topic}" step by step in JSON format.
            **VERY IMPORTANT**: Use a virtual whiteboard for visualization in every step.
            The board is 100% width and 100% height (x_percent and y_percent go from 0 to 100).
            Do NOT exceed these limits.

            Use only these whiteboard commands:
            1. {{ "action": "clear_all" }}
            2. {{ "action": "write_text", "text": "...", "x_percent": number, "y_percent": number, "font_size": number, "color": "...", "align": "center|left" }}
            3. {{ "action": "draw_shape", "shape": "rect|circle", "x_percent": number, "y_percent": number, "width_percent": number, "height_percent": number, "color": "...", "stroke": "..." }}
            4. {{ "action": "draw_arrow", "points": [x1, y1, x2, y2], "color": "..." }}

            Example of a step:
            {{
              "text_explanation": "Voltage is the potential difference across a resistor.",
              "tts_text": "Voltage is the potential difference across a resistor.",
              "whiteboard_commands": [
                {{ "action": "clear_all" }},
                {{ "action": "write_text", "text": "Voltage (V)", "x_percent": 10, "y_percent": 10, "font_size": 28, "color": "blue", "align": "left" }},
                {{ "action": "draw_shape", "shape": "rect", "x_percent": 40, "y_percent": 20, "width_percent": 20, "height_percent": 10, "color": "#f3f4f6", "stroke": "black" }},
                {{ "action": "draw_arrow", "points": [30, 30, 50, 30], "color": "red" }}
              ]
            }}

            Finally, return:
            {{
              "steps": [...],
              "notes_and_quiz_ready": {{
                "notes_content": "<h2>Summary</h2><p>Key points...</p>",
                "quiz": [
                  {{
                    "question": "What is Voltage?",
                    "options": ["Current flow", "Potential difference", "Resistance", "Power"],
                    "correct": 1,
                    "feedback": "Correct! Voltage is the potential difference."
                  }}
                ]
              }}
            }}
            Strictly return valid JSON only. Do NOT include markdown or extra text.
            """

            stream = await model.generate_content_async(prompt, stream=True)
            buffer = ""

            async for chunk in stream:
                if chunk.text:
                    buffer += chunk.text
                    await self.send(text_data=json.dumps({
                        "type": "status",
                        "message": f"Generating lesson... ({len(buffer)} chars)"
                    }))

            cleaned = buffer.strip().replace("```json", "").replace("```", "")
            lesson_data = json.loads(cleaned)

            for step in lesson_data.get("steps", []):
                await self.send(text_data=json.dumps({
                    "type": "lesson_step",
                    "data": step
                }))

            await self.send(text_data=json.dumps({
                "type": "notes_and_quiz_ready",
                "data": lesson_data.get("notes_and_quiz_ready", {})
            }))

            await self.send(text_data=json.dumps({
                "type": "lesson_end",
                "message": "Lesson complete!"
            }))

        except Exception as e:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Error: {str(e)}"
            }))
