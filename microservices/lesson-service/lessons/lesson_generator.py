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
    
    def generate_quiz_data(self, lesson_content, lesson_title):
        """
        Generate structured quiz data from lesson content
        Returns a dictionary with quiz questions in JSON format
        """
        print("🎯 Starting quiz generation from lesson content...")
        
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
            import json
            quiz_data = json.loads(quiz_text)
            
            # Validate structure
            if 'questions' not in quiz_data:
                raise ValueError("Missing 'questions' field in quiz data")
            
            print(f"✅ Quiz generated successfully: {len(quiz_data.get('questions', []))} questions")
            return quiz_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in quiz generation: {e}")
            logger.error(f"Problematic JSON text (first 1000 chars): {quiz_text[:1000]}")
            print(f"❌ Error generating quiz: {e}")
            
            # Try to salvage what we can with a more aggressive fix
            try:
                fixed_text = self._aggressive_json_fix(quiz_text)
                quiz_data = json.loads(fixed_text)
                print(f"✅ Recovered quiz after aggressive fix: {len(quiz_data.get('questions', []))} questions")
                return quiz_data
            except:
                # Return fallback quiz structure
                print("⚠️ Using fallback quiz structure")
                return self._get_fallback_quiz(lesson_title)
                
        except Exception as e:
            logger.error(f"Error generating quiz data: {e}")
            print(f"❌ Error generating quiz: {e}")
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
                    import json
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
        print("📝 Starting notes generation from lesson content...")
        
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
            import json
            notes_data = json.loads(notes_text)
            
            # Validate structure
            if 'sections' not in notes_data:
                raise ValueError("Missing 'sections' field in notes data")
            
            sections_count = len(notes_data.get('sections', []))
            print(f"✅ Notes generated successfully: {sections_count} sections")
            return notes_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in notes generation: {e}")
            logger.error(f"Problematic JSON text (first 1000 chars): {notes_text[:1000]}")
            print(f"❌ Error generating notes: {e}")
            
            # Try to salvage what we can with aggressive fix
            try:
                fixed_text = self._aggressive_json_fix_notes(notes_text)
                notes_data = json.loads(fixed_text)
                print(f"✅ Recovered notes after aggressive fix: {len(notes_data.get('sections', []))} sections")
                return notes_data
            except:
                # Return fallback notes structure
                print("⚠️ Using fallback notes structure")
                return self._get_fallback_notes(lesson_title)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in notes generation: {e}")
            logger.error(f"Problematic JSON text: {notes_text[:500]}")
            print(f"❌ Error generating notes: {e}")
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
            print(f"❌ Error generating notes: {e}")
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
                    import json
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