"""
GnyanSetu - LLM Visualization Prompt Generator
==============================================
Generates specialized prompts for LLM to create perfect visualization instructions
"""

import json
from typing import List, Dict

class VisualizationPromptGenerator:
    """
    Generates prompts that instruct LLM to create visualization JSON
    """
    
    SYSTEM_PROMPT = """You are a Visual Education Expert AI for GnyanSetu, an AI tutoring system.

Your task is to transform educational content into interactive visual teaching experiences.

You will receive:
1. PDF text content (lesson material)
2. PDF images (diagrams, charts, photos)
3. Student's learning context

You must generate a JSON response with visualization instructions that will be rendered on a digital whiteboard using:
- Konva.js for shapes, diagrams, and drawings
- GSAP for smooth animations
- Audio narration synchronized with visuals

CRITICAL RULES:
1. **Perfect Coordinate Management**: Use the zone system (top_left, top_center, top_right, center_left, center, center_right, bottom_left, bottom_center, bottom_right). The system automatically prevents overlap.

2. **Canvas Dimensions**: 1920x1080 with 50px padding. Each zone is approximately 580x310px.

3. **Visual Elements Available**:
   - circle, rectangle, line, arrow, text, image, path, group

4. **Animation Types**:
   - fadeIn, fadeOut, draw, move, rotate, scale, pulse, glow, write

5. **Teaching Flow**:
   - Break content into 3-5 scenes (each 8-15 seconds)
   - Start simple, build complexity
   - Always show PDF images when relevant
   - Sync animations with audio narration

6. **Image Integration**:
   - Always use PDF images when available
   - Place images in appropriate zones
   - Add labels, arrows, and annotations
   - Explain each part of the image

OUTPUT FORMAT (JSON):
{
  "scenes": [
    {
      "scene_id": "unique_id",
      "duration": 10.0,
      "audio_text": "Narration text synchronized with visuals",
      "background": {"type": "gradient", "colors": [0, "#1e3c72", 1, "#2a5298"]},
      "elements": [
        {
          "type": "image",
          "zone": "center",
          "properties": {
            "src": "{{PDF_IMAGE_0}}",
            "width": 600,
            "height": 400
          },
          "animation": {
            "type": "fadeIn",
            "duration": 1.5,
            "delay": 0
          },
          "layer": 0,
          "sync_audio": true
        },
        {
          "type": "text",
          "zone": "top_center",
          "properties": {
            "text": "Main Concept",
            "fontSize": 28,
            "fill": "#2c3e50",
            "fontFamily": "Arial"
          },
          "animation": {
            "type": "write",
            "duration": 2.0,
            "delay": 0.5
          },
          "layer": 1
        },
        {
          "type": "arrow",
          "zone": "center",
          "properties": {
            "points": [50, 50, 200, 50],
            "stroke": "#e74c3c",
            "strokeWidth": 3,
            "pointerLength": 15,
            "pointerWidth": 15
          },
          "animation": {
            "type": "draw",
            "duration": 1.5,
            "delay": 2.0
          },
          "layer": 2
        }
      ]
    }
  ]
}

IMPORTANT:
- Use "{{PDF_IMAGE_0}}", "{{PDF_IMAGE_1}}" placeholders for PDF images
- Keep audio_text natural and conversational
- Make animations smooth (1-3 seconds each)
- Layer elements properly (background=0, main=1, annotations=2, text=3)
- Each scene should teach ONE clear concept
"""

    @staticmethod
    def generate_teaching_prompt(
        lesson_content: str,
        pdf_images: List[Dict],
        lesson_title: str,
        user_context: Dict = None
    ) -> Dict:
        """
        Generate complete prompt for LLM to create visualization
        
        Args:
            lesson_content: Extracted text from PDF
            pdf_images: List of {url, ocr_text, position} from PDF
            lesson_title: Title of the lesson
            user_context: Optional user preferences
            
        Returns:
            Dict with system_prompt and user_prompt
        """
        
        # Prepare image information
        image_info = ""
        if pdf_images:
            image_info = "\n\n**Available PDF Images:**\n"
            for idx, img in enumerate(pdf_images):
                image_info += f"\n{idx}. Image #{idx}"
                if img.get('ocr_text'):
                    image_info += f" - Contains: {img['ocr_text'][:100]}..."
                if img.get('caption'):
                    image_info += f" - Caption: {img['caption']}"
                image_info += f"\n   Use placeholder: {{{{PDF_IMAGE_{idx}}}}}"
        
        # User context
        context_str = ""
        if user_context:
            context_str = f"\n\n**Student Context:**\n"
            context_str += f"- Learning Level: {user_context.get('level', 'intermediate')}\n"
            context_str += f"- Preferences: {user_context.get('preferences', 'visual + audio')}\n"
        
        user_prompt = f"""**Lesson Title:** {lesson_title}

**Lesson Content:**
{lesson_content[:3000]}...

{image_info}

{context_str}

**Your Task:**
Create an engaging visual teaching experience with 3-5 scenes that:
1. Introduces the main concept with PDF images (if available)
2. Breaks down complex ideas into visual diagrams
3. Uses animations to show processes, relationships, or changes
4. Provides clear audio narration synchronized with each visual
5. Builds understanding progressively

Generate the complete JSON visualization now:"""

        return {
            "system_prompt": VisualizationPromptGenerator.SYSTEM_PROMPT,
            "user_prompt": user_prompt,
            "temperature": 0.7,
            "response_format": {"type": "json_object"}
        }
    
    @staticmethod
    def generate_followup_prompt(
        question: str,
        context: str,
        pdf_images: List[Dict]
    ) -> Dict:
        """
        Generate prompt for follow-up questions during teaching
        """
        
        image_refs = ""
        if pdf_images:
            image_refs = "\n\nAvailable images: " + ", ".join([f"{{{{PDF_IMAGE_{i}}}}}" for i in range(len(pdf_images))])
        
        user_prompt = f"""**Student Question:** {question}

**Context from Lesson:**
{context[:500]}

{image_refs}

**Your Task:**
Create a focused 1-2 scene visualization to answer this question. Keep it concise and directly address their doubt.

Generate the JSON visualization:"""

        return {
            "system_prompt": VisualizationPromptGenerator.SYSTEM_PROMPT,
            "user_prompt": user_prompt,
            "temperature": 0.8
        }
    
    @staticmethod
    def validate_llm_response(response: Dict) -> bool:
        """
        Validate LLM visualization response structure
        """
        try:
            if 'scenes' not in response:
                return False
            
            for scene in response['scenes']:
                # Required fields
                if not all(key in scene for key in ['scene_id', 'audio_text', 'elements']):
                    return False
                
                # Validate elements
                for elem in scene['elements']:
                    if not all(key in elem for key in ['type', 'zone', 'properties']):
                        return False
                    
                    # Check zone is valid
                    valid_zones = ['top_left', 'top_center', 'top_right', 
                                   'center_left', 'center', 'center_right',
                                   'bottom_left', 'bottom_center', 'bottom_right']
                    if elem['zone'] not in valid_zones:
                        return False
            
            return True
            
        except Exception as e:
            print(f"Validation error: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Example: Generate prompt for photosynthesis lesson
    lesson_content = """
    Photosynthesis is the process by which plants convert light energy into chemical energy.
    
    The process occurs in chloroplasts and requires:
    1. Sunlight
    2. Water (H2O)
    3. Carbon Dioxide (CO2)
    
    The outputs are:
    1. Glucose (C6H12O6) - food for the plant
    2. Oxygen (O2) - released into atmosphere
    
    The chemical equation:
    6CO2 + 6H2O + light energy → C6H12O6 + 6O2
    """
    
    pdf_images = [
        {
            "url": "photosynthesis_diagram.png",
            "ocr_text": "Chloroplast structure showing thylakoids and stroma",
            "caption": "Internal structure of chloroplast"
        }
    ]
    
    generator = VisualizationPromptGenerator()
    prompt = generator.generate_teaching_prompt(
        lesson_content=lesson_content,
        pdf_images=pdf_images,
        lesson_title="Photosynthesis - How Plants Make Food",
        user_context={"level": "high_school", "preferences": "detailed_visuals"}
    )
    
    print("SYSTEM PROMPT:")
    print(prompt['system_prompt'][:500] + "...\n")
    
    print("USER PROMPT:")
    print(prompt['user_prompt'])
