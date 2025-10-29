# AI Lesson Generation Service using Google Gemini
import logging
import json
import base64
from io import BytesIO
from PIL import Image
import google.generativeai as genai
from django.conf import settings
from datetime import datetime

logger = logging.getLogger(__name__)

class LessonGenerator:
    """AI-powered lesson generation using Google Gemini"""
    
    def __init__(self):
        """Initialize Gemini AI client with vision support"""
        self.api_key = settings.AI_SETTINGS.get('GEMINI_API_KEY')
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            
            # Use Gemini 2.0 Flash Experimental - FASTEST model with vision support
            self.model_name = 'gemini-2.0-flash-exp'
            self.max_tokens = settings.AI_SETTINGS.get('MAX_TOKENS', 16000)  # Increased for detailed lessons
            self.temperature = settings.AI_SETTINGS.get('TEMPERATURE', 0.3)  # Lower for more focused, educational content
            
            self.model = genai.GenerativeModel(self.model_name)
            self.text_model = self.model  # Use same model for both (supports both vision and text)
            logger.info(f" Initialized Gemini AI with FASTEST model: {self.model_name}")
            logger.info(f" Model supports: Vision (multimodal) + Text generation + ULTRA FAST")
        else:
            self.model = None
            self.text_model = None
            logger.warning("Gemini API key not provided - lesson generation will not work")
    
    def _safe_extract_text(self, response, fallback="Educational Content"):
        """Safely extract text from Gemini response"""
        try:
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content and candidate.content.parts:
                    return candidate.content.parts[0].text
                else:
                    logger.warning(f"Gemini response has no content parts. Finish reason: {candidate.finish_reason}")
                    return fallback
            else:
                logger.warning("Gemini response has no candidates")
                return fallback
        except Exception as e:
            logger.error(f"Error extracting text from Gemini response: {e}")
            return fallback
    
    def generate_image_explanations(self, pdf_images, lesson_content=""):
        """
        Generate AI explanations for ALL PDF images in a SINGLE BATCH API call (OPTIMIZED)
        
        Args:
            pdf_images (list): List of image dicts with base64_data
            lesson_content (str): Context from lesson for better explanations
            
        Returns:
            list: Updated images with explanations
        """
        if not pdf_images or not self.model:
            return pdf_images or []
        
        # Prepare all images for batch processing
        pil_images = []
        valid_indices = []
        
        for idx, img in enumerate(pdf_images):
            try:
                img_base64 = img.get('base64_data', '')
                if not img_base64:
                    logger.warning(f"Image {idx} has no base64 data, will use fallback")
                    continue
                
                # Decode base64 to bytes
                if 'base64,' in img_base64:
                    img_base64 = img_base64.split('base64,')[1]
                
                img_bytes = base64.b64decode(img_base64)
                pil_image = Image.open(BytesIO(img_bytes))
                pil_images.append(pil_image)
                valid_indices.append(idx)
                
            except Exception as e:
                logger.error(f"Failed to decode image {idx}: {e}")
        
        # BATCH PROCESS: Single API call for ALL images
        if pil_images:
            try:
                # Create batch prompt for all images
                prompt = f"""Analyze these {len(pil_images)} educational images extracted from a PDF lesson.

Lesson context: {lesson_content[:500]}

Provide explanations for ALL images in a JSON array format:
{{
    "images": [
        {{
            "image_index": 0,
            "description": "Brief description of what the image shows (1-2 sentences)",
            "teaching_points": ["Key point 1", "Key point 2", "Key point 3"],
            "narration": "Natural explanation suitable for text-to-speech (2-3 sentences)"
        }},
        ... (repeat for all {len(pil_images)} images)
    ]
}}

Focus on educational value and how each image supports the lesson."""

                # Single API call with all images
                logger.info(f"📸 Batch processing {len(pil_images)} images in ONE API call")
                content_parts = [prompt] + pil_images
                response = self.model.generate_content(content_parts)
                response_text = self._safe_extract_text(response, fallback='{"images": []}')
                
                # Parse batch response with error handling
                try:
                    batch_result = json.loads(response_text)
                    explanations = batch_result.get('images', [])
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse batch response JSON: {e}")
                    logger.error(f"Response text: {response_text[:500]}")
                    batch_result = {"images": []}
                    explanations = []
                
                logger.info(f"Generated explanations for {len(explanations)} images in single batch")
                
                # Apply explanations to images
                for explanation in explanations:
                    img_idx = explanation.get('image_index', 0)
                    if img_idx < len(valid_indices):
                        actual_idx = valid_indices[img_idx]
                        pdf_images[actual_idx]['id'] = pdf_images[actual_idx].get('id', f'pdf_img_{actual_idx}')
                        pdf_images[actual_idx]['description'] = explanation.get('description', 'Educational diagram')
                        pdf_images[actual_idx]['teaching_points'] = explanation.get('teaching_points', [])
                        pdf_images[actual_idx]['narration'] = explanation.get('narration', 'This image illustrates a key concept.')
                        pdf_images[actual_idx]['explanation'] = explanation.get('description', '')
                
            except Exception as e:
                logger.error(f"Batch image explanation failed: {e}, using fallback")
                # Apply fallback to all images
                for idx in valid_indices:
                    pdf_images[idx]['id'] = pdf_images[idx].get('id', f'pdf_img_{idx}')
                    pdf_images[idx]['description'] = 'Educational diagram from PDF'
                    pdf_images[idx]['teaching_points'] = []
                    pdf_images[idx]['narration'] = 'This image illustrates a concept from the lesson.'
                    pdf_images[idx]['explanation'] = 'Educational diagram'
        
        # Apply fallback to any images that weren't processed
        for idx, img in enumerate(pdf_images):
            if 'description' not in img:
                img['id'] = img.get('id', f'pdf_img_{idx}')
                img['description'] = 'Educational diagram from PDF'
                img['teaching_points'] = []
                img['narration'] = 'This image illustrates a concept from the lesson.'
                img['explanation'] = 'Educational diagram'
        
        logger.info(f"Batch explained {len(pdf_images)} images with 1 API call (OPTIMIZED)")
        return pdf_images
    
    def generate_lesson(self, pdf_text, images_ocr_text="", lesson_type="interactive", user_context=None, pdf_images=None):
        """
        Generate comprehensive lesson from PDF content with images
        
        Args:
            pdf_text (str): Extracted text from PDF
            images_ocr_text (str): OCR text from images
            lesson_type (str): Type of lesson to generate
            user_context (dict): Additional context about user preferences
            pdf_images (list): List of extracted PDF images with base64 data
        
        Returns:
            dict: Generated lesson with title and content
        """
        if not self.model:
            return self._fallback_lesson(pdf_text)
        
        try:
            # Combine all text content
            full_content = pdf_text
            if images_ocr_text:
                full_content += f"\n\n--- Content from Images ---\n{images_ocr_text}"
            
            # Log image availability
            if pdf_images and len(pdf_images) > 0:
                logger.info(f"Processing lesson with {len(pdf_images)} images from PDF")
                # Generate AI explanations for images
                pdf_images = self.generate_image_explanations(pdf_images, full_content)
            
            # Extract meaningful title from content (first line or heading)
            lesson_title = "Educational Lesson"  # Default fallback
            try:
                lines = full_content.split('\n')
                for line in lines[:20]:  # Check first 20 lines
                    clean_line = line.strip()
                    if clean_line and len(clean_line) > 10 and len(clean_line) < 150:
                        # Skip lines that look like headers, dates, or metadata
                        if not any(x in clean_line.lower() for x in ['page', 'chapter', 'section', '©', 'copyright', 'published']):
                            lesson_title = clean_line[:100]  # Limit to 100 chars
                            logger.info(f"Extracted title: {lesson_title}")
                            break
            except Exception as e:
                logger.warning(f"Failed to extract title: {e}")
            
            # Generate lesson content based on type (WITH IMAGES)
            if lesson_type == "interactive":
                lesson_content = self._generate_interactive_lesson_with_images(
                    full_content, lesson_title, pdf_images
                )
            elif lesson_type == "quiz":
                lesson_content = self._generate_quiz_lesson(full_content, lesson_title)
            elif lesson_type == "summary":
                lesson_content = self._generate_summary_lesson(full_content, lesson_title)
            elif lesson_type == "detailed":
                lesson_content = self._generate_detailed_lesson(full_content, lesson_title)
            else:
                lesson_content = self._generate_interactive_lesson_with_images(
                    full_content, lesson_title, pdf_images
                )
            
            logger.info(f"Generated {lesson_type} lesson: {lesson_title}")
            
            # NO visualization extraction - Visualization Service handles this separately
            # Lesson Service generates ONLY educational content (2000-3000 words)
            # Visualization Service generates teaching_sequence and whiteboard_commands
            
            result = {
                'title': lesson_title,
                'content': lesson_content,
                'type': lesson_type,
                'generated_at': datetime.utcnow().isoformat(),
                'success': True,
                'pdf_images': pdf_images  # Include images for Visualization Service to use
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating lesson: {e}")
            return self._fallback_lesson(pdf_text, error_msg=str(e))
    
    def _generate_lesson_title(self, content):
        """Generate an appropriate title for the lesson"""
        try:
            # More aggressive content cleaning for safety filters
            content_preview = content[:1000] if len(content) > 1000 else content
            
            # Clean the content to avoid safety filter issues
            import re
            # Remove any potentially problematic patterns
            cleaned_content = re.sub(r'[^\w\s\-\.\,\;\:\!\?\(\)]', ' ', content_preview)
            cleaned_content = re.sub(r'\s+', ' ', cleaned_content)  # Normalize whitespace
            cleaned_content = cleaned_content.strip()
            
            # More neutral prompt to avoid content policy issues
            prompt = f"""
            This is educational content for creating a learning lesson. Please generate a simple, appropriate title for this educational material.
            
            Requirements:
            - Use 3-6 words maximum
            - Make it educational and neutral
            - Focus on learning topics
            
            Educational content sample:
            {cleaned_content[:500]}
            
            Title:
            """
            
            # Use text-only model for title generation (gemini-pro-vision doesn't support text-only)
            response = self.text_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Very low temperature for consistency
                    max_output_tokens=20,  # Very short for just a title
                    candidate_count=1
                ),
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
            )
            
            # Better error handling for Gemini response
            text_result = self._safe_extract_text(response, "Educational Lesson")
            title = text_result.strip().replace('"', '').replace("'", "")
            return title if title else "Educational Lesson"
            
        except Exception as e:
            logger.error(f"Error generating lesson title: {e}")
            return "Educational Lesson"
    
    def _detect_subject_simple(self, title, content):
        """Fast subject detection without AI call - removed hardcoded rules to avoid misclassification"""
        title_lower = title.lower()
        content_lower = content[:500].lower()
        combined = title_lower + " " + content_lower
        
        # Check for explicit subject mentions first
        if 'biology' in combined:
            return 'biology'
        elif 'physics' in combined:
            return 'physics'
        elif 'chemistry' in combined:
            return 'chemistry'
        elif any(word in combined for word in ['algorithm', 'code', 'programming', 'computer', 'software', 'sdlc', 'development']):
            return 'computer_science'
        elif any(word in combined for word in ['mathematics', 'math', 'calculus', 'algebra', 'geometry']):
            return 'mathematics'
        else:
            # Default to general - let AI handle specific categorization
            return 'general'
    
    def _get_fallback_analysis(self, title, content):
        """Fallback analysis when AI fails - removed hardcoded keywords to avoid misclassification"""
        title_lower = title.lower()
        content_lower = content[:500].lower()
        combined = title_lower + " " + content_lower
        
        # Detect subject - simplified to avoid false positives like "cycle" matching biology
        if 'biology' in combined:
            subject = 'biology'
        elif 'physics' in combined:
            subject = 'physics'
        elif 'chemistry' in combined:
            subject = 'chemistry'
        elif any(word in combined for word in ['algorithm', 'code', 'programming', 'computer', 'software', 'sdlc', 'development']):
            subject = 'computer_science'
        elif any(word in combined for word in ['equation', 'graph', 'theorem', 'math', 'calculus']):
            subject = 'mathematics'
        else:
            subject = 'general'
            
        return {
            "subject_category": subject,
            "key_concepts": [title],
            "visual_elements": [],
            "relationships": [],
            "image_search_terms": [title],
            "icon_suggestions": [],
            "color_palette": {"primary": "#2196F3", "secondary": "#4CAF50", "accent": "#FF9800"},
            "diagram_type": "concept_map"
        }
    
    def _get_subject_specific_prompt_additions(self, subject_category):
        """Get subject-specific visualization guidelines"""
        
        prompts = {
            'biology': """
 BIOLOGY VISUALIZATION GUIDELINES:
**Required Elements:**
- Plants: Use path shapes for leaves (curved organic shapes), rectangles for stems, circles for cells
- Cells: Circle for cell membrane, smaller circles for nucleus/organelles, labels with arrows
- Photosynthesis: Sun (yellow circle with ray polygons), leaf (green curved path), CO2/O2 arrows with molecule labels
- DNA: Double helix using two curved paths intertwined, labels for bases (A,T,G,C)
- Processes: Use arrows to show transformations (glucose → ATP, DNA → RNA → Protein)

**Color Palette:**
- Plants: #4CAF50 (green), #8BC34A (light green), #2E7D32 (dark green)
- Sun/Energy: #FFD700 (gold), #FFA000 (orange)
- Water: #2196F3 (blue), #03A9F4 (light blue)
- Oxygen: #E3F2FD (light blue), Carbon: #424242 (gray)

**Example Shapes:**
```json
// Leaf shape (curved path)
{"type": "path", "d": "M 400,500 Q 380,450 400,400 Q 420,450 400,500 Z", "fill": "#4CAF50", "stroke": "#2E7D32", "strokeWidth": 3}

// Chloroplast (oval with internal structure)
{"type": "ellipse", "x": 960, "y": 540, "radiusX": 60, "radiusY": 40, "fill": "#8BC34A", "stroke": "#2E7D32", "strokeWidth": 2}

// Sun with rays (star polygon)
{"type": "polygon", "points": [960,200, 980,240, 1020,240, 990,265, 1005,305, 960,280, 915,305, 930,265, 900,240, 940,240], "fill": "#FFD700", "stroke": "#FFA000"}
```
""",
            
            'physics_electronics': """
 PHYSICS/ELECTRONICS VISUALIZATION GUIDELINES:
**Required Elements:**
- Circuit Components:
  * Battery: Rectangle with + and - labels
  * Resistor: Zigzag path (M x,y L x+20,y+10 L x+40,y-10 L x+60,y+10...)
  * LED: Circle with triangle inside, rays emanating
  * Capacitor: Two parallel lines
  * Wire: Curved paths connecting components
- Forces: Arrows with labels (F=ma, gravity, friction)
- Motion: Dotted path showing trajectory, velocity vectors

**Color Palette:**
- Positive: #F44336 (red), Negative: #2196F3 (blue)
- Current flow: #FF9800 (orange arrows)
- Voltage: #9C27B0 (purple)
- Neutral: #757575 (gray)

**Example Shapes:**
```json
// Battery
{"type": "rectangle", "x": 300, "y": 500, "width": 100, "height": 200, "fill": "#424242", "stroke": "#212121", "cornerRadius": 5}
{"type": "text", "x": 350, "y": 550, "text": "+", "fontSize": 40, "fill": "#F44336", "fontStyle": "bold"}
{"type": "text", "x": 350, "y": 650, "text": "-", "fontSize": 40, "fill": "#2196F3", "fontStyle": "bold"}

// Resistor (zigzag path)
{"type": "path", "d": "M 500,600 L 520,580 L 540,620 L 560,580 L 580,620 L 600,600", "stroke": "#FF9800", "strokeWidth": 4, "fill": "none"}

// LED with light rays
{"type": "circle", "x": 800, "y": 600, "radius": 30, "fill": "#FFEB3B", "stroke": "#FFA000", "strokeWidth": 3}
{"type": "polygon", "points": [800,560, 820,540, 800,550], "fill": "#FFF59D", "opacity": 0.7}
```
""",
            
            'chemistry': """
 CHEMISTRY VISUALIZATION GUIDELINES:
**Required Elements:**
- Atoms: Circles with electron orbits (smaller circles or paths)
- Molecules: Connected circles representing atoms (H₂O = 2 small + 1 large)
- Bonds: Lines connecting atoms (single, double, triple)
- Chemical Equations: Text with arrows (→) showing reactants → products
- Lab Equipment: Beakers (trapezoid shapes), test tubes (rectangles), flames (orange polygons)

**Color Palette:**
- Hydrogen: #E3F2FD (light blue)
- Oxygen: #FFCDD2 (light red)
- Carbon: #424242 (gray/black)
- Nitrogen: #C5E1A5 (light green)
- Reactions: #FF5722 (orange/red for heat)

**Example Shapes:**
```json
// Water molecule (H2O)
{"type": "circle", "x": 960, "y": 540, "radius": 40, "fill": "#FFCDD2", "stroke": "#F44336", "strokeWidth": 2}  // Oxygen
{"type": "circle", "x": 900, "y": 500, "radius": 25, "fill": "#E3F2FD", "stroke": "#2196F3", "strokeWidth": 2}  // Hydrogen 1
{"type": "circle", "x": 1020, "y": 500, "radius": 25, "fill": "#E3F2FD", "stroke": "#2196F3", "strokeWidth": 2}  // Hydrogen 2
{"type": "line", "points": [920,515, 950,530], "stroke": "#333", "strokeWidth": 3}  // Bond 1
{"type": "line", "points": [1000,515, 970,530], "stroke": "#333", "strokeWidth": 3}  // Bond 2

// Beaker
{"type": "path", "d": "M 400,400 L 400,700 Q 400,750 450,750 L 650,750 Q 700,750 700,700 L 700,400 Z", "fill": "transparent", "stroke": "#424242", "strokeWidth": 4}
```
""",
            
            'computer_science': """
� COMPUTER SCIENCE VISUALIZATION GUIDELINES:
**Required Elements:**
- CPU/Computer: Rectangle with internal components (cache, registers shown as smaller boxes)
- Memory: Grid of rectangles representing RAM cells
- Network: Nodes (circles) connected by lines, routers (hexagons)
- Data Flow: Arrows with binary labels (0101, data packets)
- Algorithms: Flowchart boxes (rectangles with rounded corners, diamonds for decisions)

**Color Palette:**
- Hardware: #607D8B (blue-gray), #455A64 (dark gray)
- Data: #00BCD4 (cyan), #0288D1 (blue)
- Processing: #FF5722 (orange)
- Memory: #9C27B0 (purple)

**Example Shapes:**
```json
// CPU chip
{"type": "rectangle", "x": 960, "y": 540, "width": 200, "height": 150, "fill": "#607D8B", "stroke": "#37474F", "strokeWidth": 3, "cornerRadius": 5}
{"type": "text", "x": 960, "y": 540, "text": "CPU", "fontSize": 32, "fill": "#FFFFFF", "fontStyle": "bold", "align": "center"}

// Binary data flow
{"type": "text", "x": 500, "y": 400, "text": "1 0 1 1 0 0 1", "fontSize": 24, "fill": "#00BCD4", "fontFamily": "monospace"}
{"type": "arrow", "points": [500, 420, 700, 420], "stroke": "#00BCD4", "strokeWidth": 3, "pointerLength": 15}

// Flowchart decision diamond
{"type": "polygon", "points": [960,400, 1060,500, 960,600, 860,500], "fill": "#FFEB3B", "stroke": "#FFA000", "strokeWidth": 3}
```
""",
            
            'mathematics': """
� MATHEMATICS VISUALIZATION GUIDELINES:
**Required Elements:**
- Graphs: Coordinate system (axes with arrows), plotted points, curves
- Equations: Large clear text with proper spacing (y = mx + b)
- Geometric Shapes: Precise circles, triangles, rectangles with angle markers
- Functions: Curves showing f(x), derivatives shown as tangent lines
- Sets: Venn diagrams (overlapping circles with labels)

**Color Palette:**
- Axes: #424242 (dark gray)
- Positive values: #4CAF50 (green)
- Negative values: #F44336 (red)
- Function curves: #2196F3 (blue), #9C27B0 (purple), #FF9800 (orange)

**Example Shapes:**
```json
// Coordinate axes
{"type": "arrow", "points": [200, 540, 1720, 540], "stroke": "#424242", "strokeWidth": 3, "pointerLength": 15}  // X-axis
{"type": "arrow", "points": [960, 900, 960, 180], "stroke": "#424242", "strokeWidth": 3, "pointerLength": 15}  // Y-axis
{"type": "text", "x": 1700, "y": 570, "text": "x", "fontSize": 32, "fill": "#424242", "fontStyle": "italic"}
{"type": "text", "x": 990, "y": 200, "text": "y", "fontSize": 32, "fill": "#424242", "fontStyle": "italic"}

// Parabola curve (quadratic function)
{"type": "path", "d": "M 400,800 Q 960,200 1520,800", "stroke": "#2196F3", "strokeWidth": 4, "fill": "none"}

// Right triangle
{"type": "polygon", "points": [600,700, 600,400, 900,700], "fill": "transparent", "stroke": "#4CAF50", "strokeWidth": 3}
{"type": "text", "x": 750, "y": 730, "text": "c (hypotenuse)", "fontSize": 20, "fill": "#333"}
```
"""
        }
        
        return prompts.get(subject_category, """
 GENERAL VISUALIZATION GUIDELINES:
- Use clear diagrams with labeled components
- Show relationships with arrows
- Use color coding for different concepts
- Include step-by-step process flows
- Add text labels above/below shapes (never overlapping)
""")
        """Generate an interactive lesson with questions and activities"""
        prompt = f"""
        Create an engaging, interactive educational lesson with DYNAMIC VISUALIZATION INSTRUCTIONS based on the provided content.
        
        Title: {title}
        
        Content to base the lesson on:
        {content}
        
        IMPORTANT: Generate visualization JSON that will create dynamic, animated diagrams to explain concepts.
        
        Create a comprehensive lesson with the following structure:
        
        1. **Introduction** (2-3 sentences introducing the topic)
        2. **Learning Objectives** (3-4 clear objectives students will achieve)
        3. **Main Content** (detailed explanation broken into digestible sections with headers)
        4. **Interactive Elements** (questions for reflection, activities, or discussion points)
        5. **Key Takeaways** (3-4 main points to remember)
        6. **Practice Questions** (2-3 questions to test understanding)
        7. **Further Exploration** (suggestions for additional learning)
        8. **VISUALIZATION JSON** (see format below)
        
        VISUALIZATION FORMAT:
        Include a JSON block with this EXACT structure for dynamic visuals:
        
        ```visualization
        {{
          "topic": "{title}",
          "explanation": "Brief explanation of what will be visualized",
          "scenes": [
            {{
              "scene_id": "scene_1",
              "title": "Introduction to Concept",
              "duration": 10.0,
              "shapes": [
                {{"type": "rectangle", "zone": "center", "width": 200, "height": 100, "fill": "#4A90E2", "stroke": "#2E5C8A", "label": "Main Concept"}},
                {{"type": "circle", "zone": "top_left", "radius": 40, "fill": "#50E3C2", "label": "Key Point 1"}},
                {{"type": "arrow", "zone": "center_left", "points": [100, 100, 200, 100], "stroke": "#F5A623", "strokeWidth": 3}}
              ],
              "animations": [
                {{"shape_index": 0, "type": "fadeIn", "duration": 2.0, "delay": 0.0, "ease": "power2.out"}},
                {{"shape_index": 1, "type": "scale", "duration": 1.5, "delay": 2.0, "from_props": {{"scaleX": 0, "scaleY": 0}}, "to_props": {{"scaleX": 1, "scaleY": 1}}}},
                {{"shape_index": 2, "type": "draw", "duration": 2.0, "delay": 3.5}}
              ],
              "effects": {{"background": "white", "glow": false}},
              "audio": {{
                "text": "Let's begin by understanding the main concept. Notice how the elements connect together.",
                "start_time": 0.0,
                "duration": 10.0
              }}
            }}
          ]
        }}
        ```
        
        VISUALIZATION RULES:
        - Use zones: top_left, top_center, top_right, center_left, center, center_right, bottom_left, bottom_center, bottom_right
        - Shapes: circle, rectangle, line, arrow, text, image, polygon
        - Animations: fadeIn, fadeOut, draw, move, rotate, scale, pulse, glow, write
        - Each scene should be 8-15 seconds
        - Create 3-5 scenes that build upon each other
        - Sync audio narration with visual animations
        - If PDF images are available, reference them as: {{"type": "image", "src": "{{{{PDF_IMAGE_0}}}}", "zone": "center"}}
        - Make visuals explain complex concepts step-by-step
        
        Format the lesson in clean markdown, then add the visualization JSON block at the end.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens
                )
            )
            return self._safe_extract_text(response, self._create_basic_lesson(content, title))
            
        except Exception as e:
            logger.error(f"Error generating interactive lesson: {e}")
            return self._create_basic_lesson(content, title)
    
    def _generate_interactive_lesson_with_images(self, content, title, pdf_images=None):
        """Generate interactive lesson with vision understanding of PDF images - WITH SMART RETRY"""
        
        # ATTEMPT 1: Try with ONE small image (300x300)
        logger.info("� ATTEMPT 1: Generating with 1 compressed image (300px)")
        result = self._try_generate_with_images(content, title, pdf_images, max_images=1, max_image_size=300)
        if result:
            logger.info(" SUCCESS: Generated lesson with image")
            # ⚠️ REMOVED: Fallback visualization - Visualization Service handles this via /visualization/v2/{lesson_id}
            logger.info("ℹ️ Visualization will be generated by Visualization Service")
            return result
        
        # ATTEMPT 2: Try without any images (text-only)
        logger.warning(" ATTEMPT 2: Image generation failed, trying TEXT-ONLY")
        result = self._try_generate_text_only(content, title)
        if result:
            logger.info(" SUCCESS: Generated text-only lesson")
            # ⚠️ REMOVED: Fallback visualization - Visualization Service handles this via /visualization/v2/{lesson_id}
            logger.info("ℹ️ Visualization will be generated by Visualization Service")
            return result
        
        # ATTEMPT 3: Complete fallback
        logger.error(" ATTEMPT 3: All attempts failed, using complete fallback")
        fallback = self._create_basic_lesson(content, title)
        # ⚠️ REMOVED: Fallback visualization - Visualization Service handles this via /visualization/v2/{lesson_id}
        logger.info("ℹ️ Visualization will be generated by Visualization Service")
        return fallback
    
    def _try_generate_text_only(self, content, title):
        """Try text-only generation (NO IMAGES) - calls _try_generate_with_images with no images"""
        logger.info("� ATTEMPT 2 (TEXT-ONLY): Calling Gemini without images")
        # Just call the main function with empty image list - it now handles this case
        return self._try_generate_with_images(content, title, pdf_images=None)
    
    def _try_generate_with_images(self, content, title, pdf_images=None, max_images=1, max_image_size=300):
        """Generate comprehensive educational lesson (2000-3000 words) - NO VISUALIZATION
        
        Visualization is handled separately by the Visualization Service.
        This function generates ONLY rich educational content.
        """
        
        # Build multimodal prompt with educational content focus
        prompt_parts = []
        
        # Extract safe content preview
        safe_content = content[:1200]
        
        prompt_parts.append(f"""Generate a comprehensive, detailed educational lesson about: {title}

CRITICAL REQUIREMENTS:
- Length: 2000-3000 words of rich educational content
- NO VISUALIZATION JSON - visualization is handled by a separate service
- Focus on thorough explanations, examples, analogies, and step-by-step breakdowns
- Include real-world applications and practical examples
- Use clear headings and subheadings
- Explain concepts progressively from simple to complex

CONTENT STRUCTURE:

# {title}

## Introduction (200-300 words)
- Hook the learner with an interesting fact or question
- Explain why this topic is important
- Provide a brief overview of what will be covered
- Real-world context and relevance

## Core Concepts (800-1200 words)
Break down the main concepts into digestible sections:
- Define key terms clearly
- Explain each concept thoroughly with examples
- Use analogies to relate to familiar concepts
- Provide step-by-step explanations for processes
- Include multiple examples for clarity
- Address common misconceptions

## Detailed Explanation (600-900 words)
- Deep dive into the most important aspects
- Explain the "why" and "how" behind the concepts
- Provide detailed examples and case studies
- Show different scenarios or variations
- Explain cause and effect relationships
- Include practical applications

## Summary & Key Takeaways (200-300 words)
- Recap the main points covered
- Highlight the most important concepts
- Provide memory aids or mnemonics
- Suggest next steps for further learning
- End with a thought-provoking conclusion

STYLE GUIDELINES:
- Use clear, conversational language
- Explain technical terms when first introduced
- Use short paragraphs (3-4 sentences max)
- Include transitions between sections
- Ask rhetorical questions to engage learners
- Use bullet points for lists and key points
- Emphasize important terms with **bold** text
- Provide concrete examples for abstract concepts

CONTENT FROM PDF:
{safe_content}

Generate a thorough, well-structured lesson with clear explanations, examples, and practical applications.
Focus on making complex concepts accessible through careful explanation and real-world context.
""")
        
        # Add images if available (for visual context)
        if pdf_images and len(pdf_images) > 0:
            try:
                import PIL.Image as PILImage
                import base64
                import io
                
                # Add up to max_images, compressed
                images_added = 0
                for idx, img_data in enumerate(pdf_images[:max_images]):
                    try:
                        img_b64 = img_data['base64'].split(',')[1] if ',' in img_data['base64'] else img_data['base64']
                        img_bytes = base64.b64decode(img_b64)
                        pil_image = PILImage.open(io.BytesIO(img_bytes))
                        
                        # Resize to prevent timeout
                        max_size = (max_image_size, max_image_size)
                        if pil_image.size[0] > max_size[0] or pil_image.size[1] > max_size[1]:
                            pil_image.thumbnail(max_size, PILImage.Resampling.LANCZOS)
                            logger.info(f"Resized image to {pil_image.size} (max {max_image_size}px)")
                        
                        prompt_parts.append(pil_image)
                        images_added += 1
                    except Exception as e:
                        logger.warning(f"Failed to add image {idx}: {e}")
                
                logger.info(f"Added {images_added} compressed images to prompt")
                
            except Exception as e:
                logger.warning(f"Failed to process images: {e}")
        else:
            logger.info("No PDF images available, generating from text content only")
        
        try:
            # Generate with vision model - WITH TIMEOUT (120 seconds for complex prompts)
            import httpx
            
            # Configure httpx timeout for Gemini API
            timeout_config = httpx.Timeout(120.0, connect=10.0)
            
            response = self.model.generate_content(
                prompt_parts,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,  # Lower for more focused, educational content
                    max_output_tokens=16000,  # Increased for detailed visualizations
                    top_p=0.95,
                    top_k=40,
                    candidate_count=1
                ),
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
            )
            
            # Log response details for debugging
            if response and response.candidates:
                finish_reason = response.candidates[0].finish_reason
                logger.info(f"Gemini finish_reason: {finish_reason}")
            
            result = self._safe_extract_text(response, None)
            
            # Log content length
            if result:
                logger.info(f"Generated content length: {len(result)} characters")
                logger.info(f"Content preview (first 200 chars): {result[:200]}")
            
            # Check if we got valid content
            if result and len(result) > 100:
                return result
            else:
                logger.warning("Generated content too short, treating as failure")
                return None
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return None
    
    def _generate_fallback_visualization(self, title, pdf_images=None, content=""):
        """Generate INTELLIGENT, topic-specific visualization with educational diagrams"""
        
        # REMOVED SUBJECT DETECTION - Let AI handle topic analysis naturally
        logger.info(f" Generating fallback visualization for '{title}'")
        
        scenes = []
        
        # Scene 1: Title Introduction (animated)
        scenes.append({
            "scene_id": "intro",
            "title": "Introduction",
            "duration": 8,
            "shapes": [
                # Background gradient rectangle
                {"type": "rectangle", "zone": "center", "x": 960, "y": 540, "width": 1800, "height": 900, "fill": "#1E88E5", "opacity": 0.1, "cornerRadius": 20},
                # Main title
                {"type": "text", "zone": "top_center", "x": 960, "y": 200, "text": title, "fontSize": 56, "fill": "#1976D2", "fontFamily": "Arial", "fontStyle": "bold", "align": "center"},
                # Decorative circles
                {"type": "circle", "zone": "top_left", "x": 200, "y": 200, "radius": 60, "fill": "#4CAF50", "opacity": 0.7},
                {"type": "circle", "zone": "top_right", "x": 1720, "y": 200, "radius": 60, "fill": "#FF9800", "opacity": 0.7},
                # Subtitle box
                {"type": "rectangle", "zone": "center", "x": 960, "y": 600, "width": 800, "height": 120, "fill": "#FFFFFF", "stroke": "#1976D2", "strokeWidth": 3, "cornerRadius": 10},
                {"type": "text", "zone": "center", "x": 960, "y": 600, "text": "Educational Content", "fontSize": 32, "fill": "#333333", "fontFamily": "Arial", "align": "center"}
            ],
            "animations": [
                {"shape_index": 0, "type": "fadeIn", "duration": 1.5, "delay": 0, "ease": "power2.out"},
                {"shape_index": 1, "type": "write", "duration": 2.5, "delay": 0.5, "ease": "power1.inOut"},
                {"shape_index": 2, "type": "scale", "duration": 1, "delay": 2, "from_props": {"scaleX": 0, "scaleY": 0}, "to_props": {"scaleX": 1, "scaleY": 1}, "ease": "back.out(1.7)"},
                {"shape_index": 3, "type": "scale", "duration": 1, "delay": 2.2, "from_props": {"scaleX": 0, "scaleY": 0}, "to_props": {"scaleX": 1, "scaleY": 1}, "ease": "back.out(1.7)"},
                {"shape_index": 4, "type": "fadeIn", "duration": 1.5, "delay": 3, "ease": "power2.out"},
                {"shape_index": 5, "type": "fadeIn", "duration": 1, "delay": 3.5, "ease": "power2.out"}
            ],
            "effects": {"background": "#F5F5F5", "glow": True},
            "audio": {"text": f"Welcome! Today we'll explore {title}. Let's dive into the key concepts.", "duration": 7}
        })
        
        # Scene 2: Key Concepts (with shapes)
        scenes.append({
            "scene_id": "concepts",
            "title": "Key Concepts",
            "duration": 12,
            "shapes": [
                # Header
                {"type": "text", "zone": "top_center", "x": 960, "y": 100, "text": "Key Concepts", "fontSize": 48, "fill": "#1976D2", "fontFamily": "Arial", "fontStyle": "bold"},
                # Concept boxes with arrows (flowchart style)
                {"type": "rectangle", "zone": "center_left", "x": 350, "y": 400, "width": 300, "height": 150, "fill": "#4CAF50", "stroke": "#2E7D32", "strokeWidth": 3, "cornerRadius": 15},
                {"type": "text", "zone": "center_left", "x": 350, "y": 400, "text": "Concept 1", "fontSize": 32, "fill": "#FFFFFF", "fontFamily": "Arial", "fontStyle": "bold", "align": "center"},
                {"type": "rectangle", "zone": "center", "x": 960, "y": 400, "width": 300, "height": 150, "fill": "#2196F3", "stroke": "#1565C0", "strokeWidth": 3, "cornerRadius": 15},
                {"type": "text", "zone": "center", "x": 960, "y": 400, "text": "Concept 2", "fontSize": 32, "fill": "#FFFFFF", "fontFamily": "Arial", "fontStyle": "bold", "align": "center"},
                {"type": "rectangle", "zone": "center_right", "x": 1570, "y": 400, "width": 300, "height": 150, "fill": "#FF9800", "stroke": "#E65100", "strokeWidth": 3, "cornerRadius": 15},
                {"type": "text", "zone": "center_right", "x": 1570, "y": 400, "text": "Concept 3", "fontSize": 32, "fill": "#FFFFFF", "fontFamily": "Arial", "fontStyle": "bold", "align": "center"},
                # Connecting arrows
                {"type": "arrow", "zone": "center", "x": 510, "y": 400, "points": [0, 0, 140, 0], "stroke": "#666666", "strokeWidth": 4, "pointerLength": 15, "pointerWidth": 15},
                {"type": "arrow", "zone": "center", "x": 1120, "y": 400, "points": [0, 0, 140, 0], "stroke": "#666666", "strokeWidth": 4, "pointerLength": 15, "pointerWidth": 15},
                # Bottom summary box
                {"type": "rectangle", "zone": "bottom_center", "x": 960, "y": 900, "width": 1000, "height": 100, "fill": "#F5F5F5", "stroke": "#1976D2", "strokeWidth": 2, "cornerRadius": 10},
                {"type": "text", "zone": "bottom_center", "x": 960, "y": 900, "text": "These concepts build upon each other", "fontSize": 28, "fill": "#333333", "fontFamily": "Arial", "align": "center"}
            ],
            "animations": [
                {"shape_index": 0, "type": "write", "duration": 2, "delay": 0},
                {"shape_index": 1, "type": "fadeIn", "duration": 1.5, "delay": 1.5, "ease": "power2.out"},
                {"shape_index": 2, "type": "fadeIn", "duration": 1, "delay": 2, "ease": "power2.out"},
                {"shape_index": 3, "type": "fadeIn", "duration": 1.5, "delay": 3, "ease": "power2.out"},
                {"shape_index": 4, "type": "fadeIn", "duration": 1, "delay": 3.5, "ease": "power2.out"},
                {"shape_index": 5, "type": "fadeIn", "duration": 1.5, "delay": 4.5, "ease": "power2.out"},
                {"shape_index": 6, "type": "fadeIn", "duration": 1, "delay": 5, "ease": "power2.out"},
                {"shape_index": 7, "type": "draw", "duration": 1.5, "delay": 2.5, "ease": "power1.inOut"},
                {"shape_index": 8, "type": "draw", "duration": 1.5, "delay": 4, "ease": "power1.inOut"},
                {"shape_index": 9, "type": "fadeIn", "duration": 1.5, "delay": 6, "ease": "power2.out"},
                {"shape_index": 10, "type": "write", "duration": 2, "delay": 6.5, "ease": "power1.out"}
            ],
            "effects": {"background": "#FFFFFF", "glow": False},
            "audio": {"text": "Let's break this down into three main concepts. Notice how they connect and build upon each other to form a complete understanding.", "duration": 11}
        })
        
        # Scene 3+: PDF Images (one scene per image, up to 5 images)
        if pdf_images and len(pdf_images) > 0:
            num_images_to_show = min(5, len(pdf_images))  # Show up to 5 images
            for img_idx in range(num_images_to_show):
                scenes.append({
                    "scene_id": f"image_{img_idx + 1}",
                    "title": f"Visual Analysis {img_idx + 1}",
                    "duration": 15,
                    "shapes": [
                        # Title
                        {"type": "text", "zone": "top_center", "x": 960, "y": 100, "text": f"Visual Content - Part {img_idx + 1}", "fontSize": 44, "fill": "#1976D2", "fontFamily": "Arial", "fontStyle": "bold", "align": "center"},
                        # Image
                        {"type": "image", "src": f"{{{{PDF_IMAGE_{img_idx}}}}}", "zone": "center", "x": 960, "y": 540, "width": 700, "height": 500},
                        # Description box
                        {"type": "rectangle", "zone": "bottom_center", "x": 960, "y": 950, "width": 1000, "height": 100, "fill": "#F5F5F5", "stroke": "#1976D2", "strokeWidth": 2, "cornerRadius": 10},
                        {"type": "text", "zone": "bottom_center", "x": 960, "y": 950, "text": "Analyzing key visual elements...", "fontSize": 28, "fill": "#333333", "fontFamily": "Arial", "align": "center"},
                        # Pointer arrows (decorative)
                        {"type": "arrow", "zone": "center_left", "x": 400, "y": 540, "points": [0, 0, 100, 0], "stroke": "#E91E63", "strokeWidth": 4, "pointerLength": 15, "pointerWidth": 15},
                        {"type": "circle", "zone": "center_left", "x": 350, "y": 540, "radius": 15, "fill": "#E91E63"}
                    ],
                    "animations": [
                        {"shape_index": 0, "type": "write", "duration": 2, "delay": 0},
                        {"shape_index": 1, "type": "fadeIn", "duration": 2.5, "delay": 2, "ease": "power2.out"},
                        {"shape_index": 2, "type": "fadeIn", "duration": 1.5, "delay": 4, "ease": "power2.out"},
                        {"shape_index": 3, "type": "write", "duration": 2, "delay": 4.5, "ease": "power1.out"},
                        {"shape_index": 4, "type": "draw", "duration": 1.5, "delay": 6.5, "ease": "power1.inOut"},
                        {"shape_index": 5, "type": "pulse", "duration": 1, "delay": 8, "ease": "power2.inOut"}
                    ],
                    "effects": {"background": "#FFFFFF", "glow": True},
                    "audio": {"text": f"Let's examine this diagram carefully. Notice the important details and how they contribute to our understanding of {title}.", "duration": 13}
                })
        
        # Final scene: Summary/Conclusion
        scenes.append({
            "scene_id": "conclusion",
            "title": "Key Takeaways",
            "duration": 10,
            "shapes": [
                # Header
                {"type": "text", "zone": "top_center", "x": 960, "y": 150, "text": "Key Takeaways", "fontSize": 52, "fill": "#1976D2", "fontFamily": "Arial", "fontStyle": "bold", "align": "center"},
                # Takeaway boxes
                {"type": "rectangle", "zone": "center", "x": 960, "y": 400, "width": 1200, "height": 100, "fill": "#4CAF50", "stroke": "#2E7D32", "strokeWidth": 3, "cornerRadius": 15},
                {"type": "text", "zone": "center", "x": 960, "y": 400, "text": "Understanding the fundamentals", "fontSize": 32, "fill": "#FFFFFF", "fontFamily": "Arial", "align": "center"},
                {"type": "rectangle", "zone": "center", "x": 960, "y": 550, "width": 1200, "height": 100, "fill": "#2196F3", "stroke": "#1565C0", "strokeWidth": 3, "cornerRadius": 15},
                {"type": "text", "zone": "center", "x": 960, "y": 550, "text": "Applying concepts in practice", "fontSize": 32, "fill": "#FFFFFF", "fontFamily": "Arial", "align": "center"},
                {"type": "rectangle", "zone": "center", "x": 960, "y": 700, "width": 1200, "height": 100, "fill": "#FF9800", "stroke": "#E65100", "strokeWidth": 3, "cornerRadius": 15},
                {"type": "text", "zone": "center", "x": 960, "y": 700, "text": "Building deeper knowledge", "fontSize": 32, "fill": "#FFFFFF", "fontFamily": "Arial", "align": "center"},
                # Checkmarks
                {"type": "circle", "zone": "center_left", "x": 300, "y": 400, "radius": 30, "fill": "#FFFFFF", "stroke": "#2E7D32", "strokeWidth": 3},
                {"type": "circle", "zone": "center_left", "x": 300, "y": 550, "radius": 30, "fill": "#FFFFFF", "stroke": "#1565C0", "strokeWidth": 3},
                {"type": "circle", "zone": "center_left", "x": 300, "y": 700, "radius": 30, "fill": "#FFFFFF", "stroke": "#E65100", "strokeWidth": 3}
            ],
            "animations": [
                {"shape_index": 0, "type": "write", "duration": 2, "delay": 0},
                {"shape_index": 1, "type": "fadeIn", "duration": 1.5, "delay": 1.5, "ease": "back.out(1.7)"},
                {"shape_index": 2, "type": "write", "duration": 1.5, "delay": 2, "ease": "power1.out"},
                {"shape_index": 3, "type": "fadeIn", "duration": 1.5, "delay": 3.5, "ease": "back.out(1.7)"},
                {"shape_index": 4, "type": "write", "duration": 1.5, "delay": 4, "ease": "power1.out"},
                {"shape_index": 5, "type": "fadeIn", "duration": 1.5, "delay": 5.5, "ease": "back.out(1.7)"},
                {"shape_index": 6, "type": "write", "duration": 1.5, "delay": 6, "ease": "power1.out"},
                {"shape_index": 7, "type": "scale", "duration": 0.8, "delay": 3, "from_props": {"scaleX": 0, "scaleY": 0}, "to_props": {"scaleX": 1, "scaleY": 1}, "ease": "back.out(1.7)"},
                {"shape_index": 8, "type": "scale", "duration": 0.8, "delay": 5, "from_props": {"scaleX": 0, "scaleY": 0}, "to_props": {"scaleX": 1, "scaleY": 1}, "ease": "back.out(1.7)"},
                {"shape_index": 9, "type": "scale", "duration": 0.8, "delay": 7, "from_props": {"scaleX": 0, "scaleY": 0}, "to_props": {"scaleX": 1, "scaleY": 1}, "ease": "back.out(1.7)"}
            ],
            "effects": {"background": "#F5F5F5", "glow": False},
            "audio": {"text": "To summarize: we've explored the fundamentals, learned how to apply these concepts, and built a foundation for deeper knowledge. Great work!", "duration": 9}
        })
        
        viz_json = {
            "topic": title,
            "scenes": scenes
        }
        
        return f'''

```visualization
{json.dumps(viz_json, indent=2)}
```
'''
    
    def _generate_quiz_lesson(self, content, title):
        """Generate a quiz-based lesson"""
        prompt = f"""
        Create a comprehensive quiz-based lesson from the provided content.
        
        Title: {title}
        
        Content to base the quiz on:
        {content}
        
        Create a quiz lesson with:
        
        1. **Introduction** (Brief overview of what will be tested)
        2. **Study Guide** (Key concepts and terms to review)
        3. **Multiple Choice Questions** (5-7 questions with 4 options each)
        4. **Short Answer Questions** (3-4 questions requiring brief explanations)
        5. **Essay Question** (1 comprehensive question)
        6. **Answer Key** (Correct answers with explanations)
        7. **Study Tips** (How to prepare and remember key concepts)
        
        Format in clean markdown. Make questions challenging but fair.
        Provide detailed explanations for answers.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens
                )
            )
            return self._safe_extract_text(response, self._create_basic_lesson(content, title))
            
        except Exception as e:
            logger.error(f"Error generating quiz lesson: {e}")
            return self._create_basic_lesson(content, title)
    
    def _generate_summary_lesson(self, content, title):
        """Generate a concise summary lesson"""
        prompt = f"""
        Create a concise but comprehensive summary lesson with VISUALIZATION from the provided content.
        
        Title: {title}
        
        Content to summarize:
        {content}
        
        Create a summary with:
        
        1. **Executive Summary** (2-3 sentences capturing the essence)
        2. **Key Concepts** (Main ideas with brief explanations)
        3. **Important Facts & Figures** (Key data points, dates, statistics)
        4. **Critical Relationships** (How concepts connect to each other)
        5. **Practical Applications** (Real-world relevance)
        6. **Quick Review** (Bullet points for easy reference)
        7. **Memory Aids** (Mnemonics, analogies, or visual associations)
        8. **VISUALIZATION JSON** (dynamic visual summary)
        
        VISUALIZATION FORMAT:
        Create a visual mind map or flowchart showing relationships between key concepts:
        
        ```visualization
        {{
          "topic": "{title} - Summary",
          "explanation": "Visual summary of key relationships",
          "scenes": [
            {{
              "scene_id": "summary_overview",
              "title": "Concept Map",
              "duration": 12.0,
              "shapes": [
                {{"type": "circle", "zone": "center", "radius": 60, "fill": "#E74C3C", "label": "Central Concept"}},
                {{"type": "rectangle", "zone": "top_center", "width": 150, "height": 60, "fill": "#3498DB", "label": "Key Point 1"}},
                {{"type": "rectangle", "zone": "center_right", "width": 150, "height": 60, "fill": "#3498DB", "label": "Key Point 2"}},
                {{"type": "arrow", "points": [640, 240, 640, 340], "stroke": "#95A5A6", "strokeWidth": 2}}
              ],
              "animations": [
                {{"shape_index": 0, "type": "pulse", "duration": 2.0, "repeat": 2}},
                {{"shape_index": 1, "type": "fadeIn", "duration": 1.5, "delay": 2.0}},
                {{"shape_index": 2, "type": "fadeIn", "duration": 1.5, "delay": 3.0}},
                {{"shape_index": 3, "type": "draw", "duration": 1.0, "delay": 4.0}}
              ],
              "audio": {{
                "text": "Let's visualize the key relationships in this topic. The central concept connects to multiple important ideas.",
                "start_time": 0.0,
                "duration": 12.0
              }}
            }}
          ]
        }}
        ```
        
        Keep it concise but comprehensive. Format in clean markdown with visualization JSON at the end.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=4000  # Shorter for summaries
                )
            )
            return self._safe_extract_text(response, self._create_basic_lesson(content, title))
            
        except Exception as e:
            logger.error(f"Error generating summary lesson: {e}")
            return self._create_basic_lesson(content, title)
    
    def _generate_detailed_lesson(self, content, title):
        """Generate a comprehensive detailed lesson"""
        prompt = f"""
        Create a detailed, comprehensive educational lesson with STEP-BY-STEP VISUALIZATION from the provided content.
        
        Title: {title}
        
        Content to expand upon:
        {content}
        
        Create an in-depth lesson with:
        
        1. **Course Overview** (What students will learn and why it matters)
        2. **Prerequisites** (What students should know beforehand)
        3. **Detailed Content Sections** (Break into logical chapters/modules)
        4. **Examples and Case Studies** (Real-world applications)
        5. **Advanced Concepts** (Deeper dive into complex topics)
        6. **Research and References** (Suggest related materials)
        7. **Assignments and Projects** (Hands-on learning activities)
        8. **Assessment Rubric** (How understanding will be evaluated)
        9. **MULTI-SCENE VISUALIZATION JSON** (detailed step-by-step visuals)
        
        VISUALIZATION FORMAT:
        Create 4-5 scenes that progressively build understanding:
        
        ```visualization
        {{
          "topic": "{title} - Detailed Exploration",
          "explanation": "Comprehensive visual breakdown of the concept",
          "scenes": [
            {{
              "scene_id": "introduction",
              "title": "Foundation",
              "duration": 10.0,
              "shapes": [
                {{"type": "text", "zone": "top_center", "text": "Understanding {title}", "fontSize": 28, "fill": "#2C3E50"}},
                {{"type": "rectangle", "zone": "center", "width": 300, "height": 150, "fill": "#ECF0F1", "stroke": "#34495E", "strokeWidth": 3}}
              ],
              "animations": [
                {{"shape_index": 0, "type": "write", "duration": 2.0}},
                {{"shape_index": 1, "type": "fadeIn", "duration": 1.5, "delay": 2.0}}
              ],
              "audio": {{
                "text": "We'll begin with the foundational concepts.",
                "start_time": 0.0,
                "duration": 10.0
              }}
            }},
            {{
              "scene_id": "core_process",
              "title": "Core Mechanism",
              "duration": 15.0,
              "shapes": [
                {{"type": "circle", "zone": "center_left", "radius": 50, "fill": "#1ABC9C", "label": "Input"}},
                {{"type": "rectangle", "zone": "center", "width": 120, "height": 80, "fill": "#3498DB", "label": "Process"}},
                {{"type": "circle", "zone": "center_right", "radius": 50, "fill": "#E67E22", "label": "Output"}},
                {{"type": "arrow", "points": [200, 340, 400, 340], "stroke": "#7F8C8D", "strokeWidth": 3}},
                {{"type": "arrow", "points": [600, 340, 800, 340], "stroke": "#7F8C8D", "strokeWidth": 3}}
              ],
              "animations": [
                {{"shape_index": 0, "type": "fadeIn", "duration": 2.0}},
                {{"shape_index": 3, "type": "draw", "duration": 2.0, "delay": 2.0}},
                {{"shape_index": 1, "type": "scale", "duration": 1.5, "delay": 4.0, "from_props": {{"scaleX": 0, "scaleY": 0}}, "to_props": {{"scaleX": 1, "scaleY": 1}}}},
                {{"shape_index": 4, "type": "draw", "duration": 2.0, "delay": 5.5}},
                {{"shape_index": 2, "type": "pulse", "duration": 2.0, "delay": 7.5, "repeat": 2}}
              ],
              "audio": {{
                "text": "The core process takes input, transforms it through several stages, and produces the final output.",
                "start_time": 0.0,
                "duration": 15.0
              }}
            }}
          ]
        }}
        ```
        
        Make it comprehensive and scholarly. Include detailed explanations and multiple visual scenes showing the process step-by-step.
        """
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens
                )
            )
            return self._safe_extract_text(response, self._create_basic_lesson(content, title))
            
        except Exception as e:
            logger.error(f"Error generating detailed lesson: {e}")
            return self._create_basic_lesson(content, title)
    
    def _create_basic_lesson(self, content, title):
        """Create a structured lesson from PDF content when AI generation fails"""
        # Split content into pages
        pages = content.split('--- Page')
        
        # Extract meaningful sections
        lesson_parts = [f"# {title}\n"]
        
        # Add introduction
        lesson_parts.append("""
## Introduction
This comprehensive lesson will guide you through understanding the key concepts and procedures outlined in the source material. Follow along with the step-by-step instructions and visual aids provided.
""")
        
        # Process each page
        for i, page in enumerate(pages):
            if not page.strip():
                continue
                
            page_lines = page.strip().split('\n')
            page_num = i  # 0 is before first page marker
            
            # Add page content with proper formatting
            if page_num > 0:
                lesson_parts.append(f"\n### Section {page_num}\n")
            
            # Extract commands, code blocks, and instructions
            in_code_block = False
            code_lines = []
            text_lines = []
            
            for line in page_lines[1:] if page_num > 0 else page_lines:  # Skip page marker line
                line = line.strip()
                if not line:
                    continue
                    
                # Detect code/command lines (start with $, sudo, or common commands)
                if line.startswith('$') or line.startswith('sudo') or line.startswith('wget') or line.startswith('java'):
                    if not in_code_block:
                        in_code_block = True
                        if text_lines:
                            lesson_parts.append('\n'.join(text_lines))
                            text_lines = []
                        lesson_parts.append('\n```bash')
                    code_lines.append(line.lstrip('$ '))
                else:
                    if in_code_block:
                        lesson_parts.append('\n'.join(code_lines))
                        lesson_parts.append('```\n')
                        code_lines = []
                        in_code_block = False
                    text_lines.append(line)
            
            # Close any open code block
            if in_code_block and code_lines:
                lesson_parts.append('\n'.join(code_lines))
                lesson_parts.append('```\n')
            
            # Add remaining text
            if text_lines:
                lesson_parts.append('\n'.join(text_lines) + '\n')
        
        # Add practical tips
        lesson_parts.append("""
## Key Learning Points
- **Follow Sequential Steps**: Complete each step before moving to the next
- **Verify Commands**: Check command syntax before execution  
- **Review Output**: Analyze terminal output to confirm successful execution
- **Troubleshoot Errors**: If errors occur, review the command and check for typos

## Practice & Review
1. **Hands-on Practice**: Execute each command in a safe test environment
2. **Document Process**: Take notes on each step and its outcome
3. **Understand Concepts**: Don't just copy commands - understand what they do
4. **Ask Questions**: Clarify any unclear steps before proceeding

## Additional Resources
- Refer to official documentation for detailed explanations
- Consult online forums for community support
- Practice in virtual environments before production use
""")
        
        return '\n'.join(lesson_parts)
    
    def _fallback_lesson(self, content, error_msg=None):
        """Fallback lesson when AI is not available"""
        title = "Study Material"
        
        # Try to extract a title from content
        lines = content.strip().split('\n')
        for line in lines[:10]:
            if line.strip() and len(line.strip()) < 100:
                title = line.strip()
                break
        
        lesson_content = self._create_basic_lesson(content, title)
        
        if error_msg:
            lesson_content += f"\n\n*Note: Advanced AI lesson generation temporarily unavailable: {error_msg}*"
        
        return {
            'title': title,
            'content': lesson_content,
            'type': 'basic',
            'generated_at': datetime.utcnow().isoformat(),
            'success': False,
            'fallback': True
        }
    
    def generate_quiz_data(self, lesson_content, lesson_title):
        """
        Generate structured quiz data from lesson content
        Returns a dictionary with quiz questions in JSON format
        """
        print(" Starting quiz generation from lesson content...")
        
        # Limit content length to avoid token limits
        content_preview = lesson_content[:2000] if len(lesson_content) > 2000 else lesson_content
        
        prompt = f"""
Generate a quiz with EXACTLY 5 multiple choice questions based on this lesson.

Lesson Title: {lesson_title}
Lesson Content: {content_preview}

CRITICAL INSTRUCTIONS:
1. Return ONLY valid JSON - no markdown, no code blocks, no explanations
2. Use proper JSON formatting with commas between all array elements
3. Ensure all strings are properly quoted
4. Each option MUST have both "key" and "text" fields

Required Format:
{{
    "title": "Quiz: {lesson_title}",
    "questions": [
        {{
            "question": "What is the main concept?",
            "options": [
                {{"key": "A", "text": "Option A"}},
                {{"key": "B", "text": "Option B"}},
                {{"key": "C", "text": "Option C"}},
                {{"key": "D", "text": "Option D"}}
            ],
            "correct_answer": "A",
            "explanation": "Brief explanation"
        }}
    ]
}}

Generate EXACTLY 5 questions following this format. Ensure proper JSON syntax with commas between all elements.
"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,  # Lower temperature for more consistent output
                    max_output_tokens=3000
                )
            )
            
            quiz_text = self._safe_extract_text(response, "{}")
            
            # Aggressive cleaning of the response
            quiz_text = quiz_text.strip()
            
            # Remove markdown code blocks
            if "```json" in quiz_text:
                quiz_text = quiz_text.split("```json")[1].split("```")[0]
            elif "```" in quiz_text:
                quiz_text = quiz_text.split("```")[1].split("```")[0]
            
            quiz_text = quiz_text.strip()
            
            # Remove any text before the first {
            if quiz_text.find('{') > 0:
                quiz_text = quiz_text[quiz_text.find('{'):]
            
            # Remove any text after the last }
            if quiz_text.rfind('}') < len(quiz_text) - 1:
                quiz_text = quiz_text[:quiz_text.rfind('}')+1]
            
            # Try to fix common JSON errors
            quiz_text = self._fix_json_errors(quiz_text)
            
            # Parse JSON
            quiz_data = json.loads(quiz_text)
            
            # Validate structure
            if 'questions' not in quiz_data:
                raise ValueError("Missing 'questions' field in quiz data")
            
            print(f" Quiz generated successfully: {len(quiz_data.get('questions', []))} questions")
            return quiz_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in quiz generation: {e}")
            logger.error(f"Problematic JSON text (first 1000 chars): {quiz_text[:1000]}")
            print(f" Error generating quiz: {e}")
            
            # Try to salvage what we can with a more aggressive fix
            try:
                fixed_text = self._aggressive_json_fix(quiz_text)
                quiz_data = json.loads(fixed_text)
                print(f" Recovered quiz after aggressive fix: {len(quiz_data.get('questions', []))} questions")
                return quiz_data
            except:
                # Return fallback quiz structure
                print(" Using fallback quiz structure")
                return self._get_fallback_quiz(lesson_title)
                
        except Exception as e:
            logger.error(f"Error generating quiz data: {e}")
            print(f" Error generating quiz: {e}")
            return {
                "title": f"Quiz: {lesson_title}",
                "questions": [
                    {
                        "question": "What is the main topic of this lesson?",
                        "options": [
                            {"key": "A", "text": "Option A"},
                            {"key": "B", "text": "Option B"},
                            {"key": "C", "text": "Option C"},
                            {"key": "D", "text": "Option D"}
                        ],
                "correct_answer": "A",
                "explanation": "Review the lesson content for details."
                }
            ]
        }
    
    def _aggressive_json_fix_notes(self, json_text):
        """More aggressive JSON fixing for notes - try to salvage what we can"""
        import re
        
        # Apply basic fixes first
        json_text = self._fix_json_errors(json_text)
        
        # Try to find the sections array and extract it
        sections_match = re.search(r'"sections"\s*:\s*\[(.*)\]', json_text, re.DOTALL)
        if sections_match:
            sections_text = sections_match.group(1)
            
            # Split by section objects
            section_parts = re.split(r'\},\s*\{', sections_text)
            
            # Clean and reconstruct each section
            cleaned_sections = []
            for part in section_parts[:5]:  # Max 5 sections
                # Ensure it starts with {
                if not part.strip().startswith('{'):
                    part = '{' + part
                # Ensure it ends with }
                if not part.strip().endswith('}'):
                    part = part + '}'
                
                # Fix the part
                part = self._fix_json_errors(part)
                cleaned_sections.append(part)
            
            # Reconstruct JSON
            reconstructed = {
                "title": "Notes",
                "summary": "Study notes for the lesson",
                "sections": [],
                "key_terms": []
            }
            
            for s_text in cleaned_sections:
                try:
                    s_obj = json.loads(s_text)
                    reconstructed["sections"].append(s_obj)
                except:
                    continue
            
            return json.dumps(reconstructed)
        
        return json_text
    
    def _get_fallback_notes(self, lesson_title):
        """Return a fallback notes structure"""
        return {
            "title": f"Notes: {lesson_title}",
            "summary": "Review the lesson content for comprehensive understanding of the key concepts.",
            "sections": [
                {
                    "heading": "Main Concepts",
                    "key_points": [
                        "Review the lesson carefully",
                        "Take your own notes",
                        "Focus on understanding key concepts"
                    ]
                }
            ],
            "key_terms": []
        }
    
    def generate_notes_data(self, lesson_content, lesson_title):
        """
        Generate structured notes from lesson content
        Returns a dictionary with organized notes in JSON format
        """
        print("� Starting notes generation from lesson content...")
        
        # Limit content length to avoid token limits
        content_preview = lesson_content[:2000] if len(lesson_content) > 2000 else lesson_content
        
        prompt = f"""
Generate structured study notes based on this lesson.

Lesson Title: {lesson_title}
Lesson Content: {content_preview}

CRITICAL INSTRUCTIONS:
1. Return ONLY valid JSON - no markdown, no code blocks, no explanations
2. Use proper JSON formatting with commas between all array elements
3. Ensure all strings are properly quoted
4. Each section MUST have both "heading" and "key_points" fields

Required Format:
{{
    "title": "Notes: {lesson_title}",
    "summary": "Brief 2-3 sentence summary",
    "sections": [
        {{
            "heading": "Main Concept",
            "key_points": [
                "First key point",
                "Second key point"
            ]
        }}
    ],
    "key_terms": [
        {{
            "term": "Important Term",
            "definition": "Clear definition"
        }}
    ]
}}

Generate notes following this format. Ensure proper JSON syntax with commas between all elements.
"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=3000
                )
            )
            
            notes_text = self._safe_extract_text(response, "{}")
            
            # Aggressive cleaning of the response
            notes_text = notes_text.strip()
            
            # Remove markdown code blocks
            if "```json" in notes_text:
                notes_text = notes_text.split("```json")[1].split("```")[0]
            elif "```" in notes_text:
                notes_text = notes_text.split("```")[1].split("```")[0]
            
            notes_text = notes_text.strip()
            
            # Remove any text before the first {
            if notes_text.find('{') > 0:
                notes_text = notes_text[notes_text.find('{'):]
            
            # Remove any text after the last }
            if notes_text.rfind('}') < len(notes_text) - 1:
                notes_text = notes_text[:notes_text.rfind('}')+1]
            
            # Try to fix common JSON errors
            notes_text = self._fix_json_errors(notes_text)
            
            # Parse JSON
            notes_data = json.loads(notes_text)
            
            # Validate structure
            if 'sections' not in notes_data:
                raise ValueError("Missing 'sections' field in notes data")
            
            sections_count = len(notes_data.get('sections', []))
            print(f" Notes generated successfully: {sections_count} sections")
            return notes_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in notes generation: {e}")
            logger.error(f"Problematic JSON text (first 1000 chars): {notes_text[:1000]}")
            print(f" Error generating notes: {e}")
            
            # Try to salvage what we can with aggressive fix
            try:
                fixed_text = self._aggressive_json_fix_notes(notes_text)
                notes_data = json.loads(fixed_text)
                print(f" Recovered notes after aggressive fix: {len(notes_data.get('sections', []))} sections")
                return notes_data
            except:
                # Return fallback notes structure
                print(" Using fallback notes structure")
                return self._get_fallback_notes(lesson_title)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in notes generation: {e}")
            logger.error(f"Problematic JSON text: {notes_text[:500]}")
            print(f" Error generating notes: {e}")
            # Return fallback notes structure
            return {
                "title": f"Notes: {lesson_title}",
                "summary": "Review the lesson content for comprehensive understanding of the key concepts.",
                "sections": [
                    {
                        "heading": "Main Concepts",
                        "key_points": [
                            "Review the lesson carefully",
                            "Take your own notes",
                            "Focus on understanding key concepts"
                        ]
                    }
                ],
                "key_terms": []
            }
        except Exception as e:
            logger.error(f"Error generating notes data: {e}")
            print(f" Error generating notes: {e}")
            return {
                "title": f"Notes: {lesson_title}",
                "summary": "Review the lesson content for comprehensive understanding.",
                "sections": [
                    {
                        "heading": "Main Concepts",
                        "key_points": [
                            "Review the lesson carefully",
                            "Take your own notes",
                            "Focus on understanding key concepts"
                        ]
                    }
                ],
                "key_terms": []
            }

    def _fix_json_errors(self, json_text):
        """Fix common JSON formatting errors"""
        import re
        
        # Fix missing commas between objects in arrays
        # Pattern: } { -> }, {
        json_text = re.sub(r'\}\s*\n\s*\{', '},\n{', json_text)
        
        # Fix missing commas between array elements
        # Pattern: ] [ -> ], [
        json_text = re.sub(r'\]\s*\n\s*\[', '],\n[', json_text)
        
        # Fix trailing commas before closing brackets
        json_text = re.sub(r',\s*\]', ']', json_text)
        json_text = re.sub(r',\s*\}', '}', json_text)
        
        return json_text
    
    def _aggressive_json_fix(self, json_text):
        """More aggressive JSON fixing - try to salvage what we can"""
        import re
        
        # Apply basic fixes first
        json_text = self._fix_json_errors(json_text)
        
        # Try to find the questions array and extract it
        questions_match = re.search(r'"questions"\s*:\s*\[(.*)\]', json_text, re.DOTALL)
        if questions_match:
            questions_text = questions_match.group(1)
            
            # Split by question objects (look for "question" field)
            question_parts = re.split(r'\},\s*\{', questions_text)
            
            # Clean and reconstruct each question
            cleaned_questions = []
            for part in question_parts[:5]:  # Max 5 questions
                # Ensure it starts with {
                if not part.strip().startswith('{'):
                    part = '{' + part
                # Ensure it ends with }
                if not part.strip().endswith('}'):
                    part = part + '}'
                
                # Fix the part
                part = self._fix_json_errors(part)
                cleaned_questions.append(part)
            
            # Reconstruct JSON
            reconstructed = {
                "title": "Quiz",
                "questions": []
            }
            
            for q_text in cleaned_questions:
                try:
                    q_obj = json.loads(q_text)
                    reconstructed["questions"].append(q_obj)
                except:
                    continue
            
            return json.dumps(reconstructed)
        
        return json_text
    
    def _get_fallback_quiz(self, lesson_title):
        """Return a fallback quiz structure"""
        return {
            "title": f"Quiz: {lesson_title}",
            "questions": [
                {
                    "question": "What is the main topic of this lesson?",
                    "options": [
                        {"key": "A", "text": "Review the lesson content"},
                        {"key": "B", "text": "Study the material carefully"},
                        {"key": "C", "text": "Focus on key concepts"},
                        {"key": "D", "text": "Practice regularly"}
                    ],
                    "correct_answer": "A",
                    "explanation": "Review the lesson content for details."
                }
            ]
        }