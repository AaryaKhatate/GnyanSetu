# AI Lesson Generation Service using Google Gemini
import logging
import json
import google.generativeai as genai
from django.conf import settings
from datetime import datetime

logger = logging.getLogger(__name__)

class LessonGenerator:
    """AI-powered lesson generation using Google Gemini"""
    
    def __init__(self):
        """Initialize Gemini AI client"""
        self.api_key = settings.AI_SETTINGS.get('GEMINI_API_KEY')
        self.model_name = 'gemini-2.5-flash'  # Use available model name
        self.max_tokens = settings.AI_SETTINGS.get('MAX_TOKENS', 8000)
        self.temperature = settings.AI_SETTINGS.get('TEMPERATURE', 0.7)
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"Initialized Gemini AI with model: {self.model_name}")
        else:
            self.model = None
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
    
    def generate_lesson(self, pdf_text, images_ocr_text="", lesson_type="interactive", user_context=None):
        """
        Generate comprehensive lesson from PDF content
        
        Args:
            pdf_text (str): Extracted text from PDF
            images_ocr_text (str): OCR text from images
            lesson_type (str): Type of lesson to generate
            user_context (dict): Additional context about user preferences
        
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
            
            # Generate lesson title first
            lesson_title = self._generate_lesson_title(full_content)
            
            # Generate lesson content based on type
            if lesson_type == "interactive":
                lesson_content = self._generate_interactive_lesson(full_content, lesson_title)
            elif lesson_type == "quiz":
                lesson_content = self._generate_quiz_lesson(full_content, lesson_title)
            elif lesson_type == "summary":
                lesson_content = self._generate_summary_lesson(full_content, lesson_title)
            elif lesson_type == "detailed":
                lesson_content = self._generate_detailed_lesson(full_content, lesson_title)
            else:
                lesson_content = self._generate_interactive_lesson(full_content, lesson_title)
            
            logger.info(f"Generated {lesson_type} lesson: {lesson_title}")
            
            return {
                'title': lesson_title,
                'content': lesson_content,
                'type': lesson_type,
                'generated_at': datetime.utcnow().isoformat(),
                'success': True
            }
            
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
            
            response = self.model.generate_content(
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
    
    def _generate_interactive_lesson(self, content, title):
        """Generate an interactive lesson with questions and activities"""
        prompt = f"""
        Create an engaging, interactive educational lesson based on the provided content.
        
        Title: {title}
        
        Content to base the lesson on:
        {content}
        
        Create a comprehensive lesson with the following structure:
        
        1. **Introduction** (2-3 sentences introducing the topic)
        2. **Learning Objectives** (3-4 clear objectives students will achieve)
        3. **Main Content** (detailed explanation broken into digestible sections with headers)
        4. **Interactive Elements** (questions for reflection, activities, or discussion points)
        5. **Key Takeaways** (3-4 main points to remember)
        6. **Practice Questions** (2-3 questions to test understanding)
        7. **Further Exploration** (suggestions for additional learning)
        
        Format the response in clean markdown. Make it engaging and educational.
        Focus on making complex concepts accessible and include interactive elements throughout.
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
        Create a concise but comprehensive summary lesson from the provided content.
        
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
        
        Keep it concise but comprehensive. Format in clean markdown.
        Focus on clarity and easy recall.
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
        Create a detailed, comprehensive educational lesson from the provided content.
        
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
        
        Make it comprehensive and scholarly. Format in clean markdown.
        Include detailed explanations and multiple examples for each concept.
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
        """Create a basic lesson structure when AI generation fails"""
        return f"""
# {title}

## Overview
This lesson is based on the provided educational material.

## Content Summary
{content[:2000]}{'...' if len(content) > 2000 else ''}

## Key Points
- Review the material carefully
- Take notes on important concepts
- Ask questions about unclear topics
- Practice applying the concepts

## Next Steps
- Review the content multiple times
- Discuss with peers or instructors
- Look for additional resources on this topic
"""
    
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