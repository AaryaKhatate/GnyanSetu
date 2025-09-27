# Lesson Integration Service for Teaching Sessions
import logging
import requests
from typing import Dict, List, Optional, Any
from django.conf import settings
import json

logger = logging.getLogger(__name__)

class LessonIntegrationService:
    """Service to integrate with the lesson service for teaching sessions"""
    
    def __init__(self):
        self.teaching_settings = settings.TEACHING_SETTINGS
        self.lesson_service_url = self.teaching_settings.get('LESSON_SERVICE_URL', 'http://localhost:8003')
    
    async def get_lesson_content(self, lesson_id: str) -> Optional[Dict]:
        """
        Get lesson content from lesson service and format for teaching
        """
        try:
            if not lesson_id:
                return None
            
            # Call lesson service API
            response = requests.get(
                f"{self.lesson_service_url}/api/lessons/{lesson_id}/",
                timeout=15
            )
            
            if response.status_code == 200:
                lesson_data = response.json()
                
                # Transform lesson data for teaching interface
                teaching_content = self._transform_lesson_for_teaching(lesson_data)
                
                logger.info(f"Successfully loaded lesson content for teaching: {lesson_id}")
                return teaching_content
            else:
                logger.error(f"Failed to get lesson content: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting lesson content: {e}")
            return None
    
    def _transform_lesson_for_teaching(self, lesson_data: Dict) -> Dict:
        """Transform lesson data into teaching-friendly format"""
        try:
            lesson_content = lesson_data.get('lesson_content', '')
            lesson_title = lesson_data.get('lesson_title', 'Untitled Lesson')
            lesson_type = lesson_data.get('lesson_type', 'interactive')
            
            # Parse lesson content into slides/sections
            slides = self._parse_lesson_into_slides(lesson_content, lesson_type)
            
            # Extract key concepts and learning objectives
            key_concepts = self._extract_key_concepts(lesson_content)
            learning_objectives = self._extract_learning_objectives(lesson_content)
            
            # Generate interactive elements based on lesson type
            interactive_elements = self._generate_interactive_elements(lesson_content, lesson_type)
            
            # Create voice narration text for each slide
            voice_narration = self._generate_voice_narration(slides, lesson_type)
            
            teaching_content = {
                'lesson_id': lesson_data.get('_id', ''),
                'lesson_title': lesson_title,
                'lesson_type': lesson_type,
                'total_slides': len(slides),
                'estimated_duration': self._estimate_duration(slides),
                'slides': slides,
                'key_concepts': key_concepts,
                'learning_objectives': learning_objectives,
                'interactive_elements': interactive_elements,
                'voice_narration': voice_narration,
                'voice_enabled': True,
                'whiteboard_enabled': lesson_type in ['interactive', 'detailed'],
                'ai_tutor_enabled': True,
                'voice_settings': {
                    'language': 'en-US',
                    'speed': 1.0,
                    'voice_type': 'neural'
                },
                'metadata': {
                    'created_at': lesson_data.get('created_at'),
                    'user_id': lesson_data.get('user_id'),
                    'original_content_length': len(lesson_content)
                }
            }
            
            return teaching_content
            
        except Exception as e:
            logger.error(f"Error transforming lesson for teaching: {e}")
            return {}
    
    def _parse_lesson_into_slides(self, content: str, lesson_type: str) -> List[Dict]:
        """Parse lesson content into individual slides"""
        try:
            slides = []
            
            # Split by markdown headers
            import re
            sections = re.split(r'\n(?=#{1,3}\s)', content)
            
            for i, section in enumerate(sections):
                if not section.strip():
                    continue
                
                # Extract title
                title_match = re.match(r'^(#{1,3})\s+(.+)', section)
                if title_match:
                    title = title_match.group(2).strip()
                    content_text = section[len(title_match.group(0)):].strip()
                else:
                    title = f"Slide {i + 1}"
                    content_text = section.strip()
                
                # Create slide
                slide = {
                    'slide_number': i,
                    'title': title,
                    'content': content_text,
                    'slide_type': self._determine_slide_type(content_text, lesson_type),
                    'duration_estimate': self._estimate_slide_duration(content_text),
                    'visual_elements': self._extract_visual_elements(content_text),
                    'key_points': self._extract_key_points(content_text),
                    'narrator_text': self._generate_narrator_text(title, content_text),
                    'interactive_components': self._extract_interactive_components(content_text, lesson_type)
                }
                
                slides.append(slide)
            
            # If no headers found, create a single slide
            if not slides and content.strip():
                slides.append({
                    'slide_number': 0,
                    'title': 'Main Content',
                    'content': content.strip(),
                    'slide_type': 'content',
                    'duration_estimate': self._estimate_slide_duration(content),
                    'visual_elements': [],
                    'key_points': self._extract_key_points(content),
                    'narrator_text': self._generate_narrator_text('Main Content', content),
                    'interactive_components': []
                })
            
            return slides
            
        except Exception as e:
            logger.error(f"Error parsing lesson into slides: {e}")
            return []
    
    def _determine_slide_type(self, content: str, lesson_type: str) -> str:
        """Determine the type of slide based on content"""
        content_lower = content.lower()
        
        if '?' in content and lesson_type == 'quiz':
            return 'quiz'
        elif 'activity' in content_lower or 'exercise' in content_lower:
            return 'activity'
        elif 'example' in content_lower or 'demonstration' in content_lower:
            return 'example'
        elif 'summary' in content_lower or 'conclusion' in content_lower:
            return 'summary'
        elif 'introduction' in content_lower or 'overview' in content_lower:
            return 'introduction'
        else:
            return 'content'
    
    def _estimate_slide_duration(self, content: str) -> int:
        """Estimate duration in seconds for a slide"""
        # Rough estimate: 150 words per minute for reading + processing time
        word_count = len(content.split())
        reading_time = (word_count / 150) * 60  # Convert to seconds
        processing_time = 10  # Base processing time
        
        return max(30, int(reading_time + processing_time))  # Minimum 30 seconds
    
    def _estimate_duration(self, slides: List[Dict]) -> int:
        """Estimate total lesson duration in minutes"""
        total_seconds = sum(slide.get('duration_estimate', 60) for slide in slides)
        return max(5, int(total_seconds / 60))  # Minimum 5 minutes
    
    def _extract_visual_elements(self, content: str) -> List[Dict]:
        """Extract visual elements that could be displayed"""
        visual_elements = []
        
        # Look for lists, code blocks, emphasis
        import re
        
        # Extract lists
        lists = re.findall(r'((?:^[-*+]\s+.+\n?)+)', content, re.MULTILINE)
        for list_content in lists:
            visual_elements.append({
                'type': 'list',
                'content': list_content,
                'display_type': 'bullet_points'
            })
        
        # Extract code blocks
        code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', content, re.DOTALL)
        for lang, code in code_blocks:
            visual_elements.append({
                'type': 'code',
                'language': lang or 'text',
                'content': code,
                'display_type': 'code_block'
            })
        
        # Extract emphasized text
        emphasized = re.findall(r'\*\*(.+?)\*\*', content)
        for emphasis in emphasized:
            visual_elements.append({
                'type': 'emphasis',
                'content': emphasis,
                'display_type': 'highlight'
            })
        
        return visual_elements
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from slide content"""
        import re
        
        key_points = []
        
        # Extract from lists
        list_items = re.findall(r'^[-*+]\s+(.+)', content, re.MULTILINE)
        key_points.extend(list_items)
        
        # Extract emphasized text
        emphasized = re.findall(r'\*\*(.+?)\*\*', content)
        key_points.extend(emphasized)
        
        # Extract first sentence of each paragraph as potential key point
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            sentences = para.split('. ')
            if sentences and len(sentences[0]) < 100:  # Not too long
                key_points.append(sentences[0].strip())
        
        # Clean and limit
        key_points = [point.strip() for point in key_points if point.strip()]
        return key_points[:5]  # Top 5 key points
    
    def _generate_narrator_text(self, title: str, content: str) -> str:
        """Generate natural narrator text for voice synthesis"""
        # Remove markdown formatting for voice
        import re
        
        clean_content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)  # Remove bold
        clean_content = re.sub(r'`(.+?)`', r'\1', clean_content)  # Remove code formatting
        clean_content = re.sub(r'#{1,6}\s+', '', clean_content)  # Remove headers
        clean_content = re.sub(r'[-*+]\s+', 'First, ', clean_content, count=1)  # First list item
        clean_content = re.sub(r'[-*+]\s+', 'Next, ', clean_content)  # Other list items
        
        # Create natural introduction
        narrator_text = f"Let's explore {title.lower()}. {clean_content}"
        
        # Ensure it ends naturally
        if not narrator_text.endswith(('.', '!', '?')):
            narrator_text += '.'
        
        return narrator_text
    
    def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key concepts from entire lesson"""
        import re
        
        concepts = []
        
        # Extract headers
        headers = re.findall(r'#{1,6}\s+(.+)', content)
        concepts.extend(headers)
        
        # Extract bold terms
        bold_terms = re.findall(r'\*\*(.+?)\*\*', content)
        concepts.extend(bold_terms)
        
        # Clean and deduplicate
        concepts = [concept.strip() for concept in concepts if len(concept.strip()) > 2]
        concepts = list(dict.fromkeys(concepts))  # Remove duplicates while preserving order
        
        return concepts[:10]  # Top 10 concepts
    
    def _extract_learning_objectives(self, content: str) -> List[str]:
        """Extract or generate learning objectives"""
        import re
        
        objectives = []
        
        # Look for explicit objectives section
        objectives_match = re.search(r'(?:learning objectives?|objectives?|goals?):?\s*(.*?)(?:\n\n|\n#|$)', 
                                   content, re.IGNORECASE | re.DOTALL)
        
        if objectives_match:
            objectives_text = objectives_match.group(1)
            # Extract list items
            list_items = re.findall(r'[-*+]\s+(.+)', objectives_text)
            objectives.extend(list_items)
        
        # If no explicit objectives, generate from content
        if not objectives:
            headers = re.findall(r'#{1,6}\s+(.+)', content)
            for header in headers[:5]:  # Use first 5 headers
                objectives.append(f"Understand {header.lower()}")
        
        return objectives[:6]  # Maximum 6 objectives
    
    def _generate_interactive_elements(self, content: str, lesson_type: str) -> List[Dict]:
        """Generate interactive elements based on lesson type"""
        elements = []
        
        if lesson_type == 'quiz':
            # Generate quiz elements
            elements.extend(self._extract_quiz_elements(content))
        
        if lesson_type == 'interactive':
            # Generate interactive activities
            elements.extend(self._generate_activities(content))
        
        # Always add discussion prompts
        elements.extend(self._generate_discussion_prompts(content))
        
        return elements
    
    def _extract_quiz_elements(self, content: str) -> List[Dict]:
        """Extract quiz questions from content"""
        import re
        
        quiz_elements = []
        
        # Look for questions
        questions = re.findall(r'(\d+\.?\s*[^\n]*\?[^\n]*)', content)
        
        for i, question in enumerate(questions):
            quiz_elements.append({
                'type': 'quiz_question',
                'question': question.strip(),
                'question_number': i + 1,
                'interaction_type': 'multiple_choice'  # Default
            })
        
        return quiz_elements
    
    def _generate_activities(self, content: str) -> List[Dict]:
        """Generate interactive activities"""
        activities = [
            {
                'type': 'think_about',
                'prompt': 'Take a moment to think about how this applies to your experience.',
                'interaction_type': 'reflection'
            },
            {
                'type': 'draw_concept',
                'prompt': 'Try drawing or diagramming this concept on the whiteboard.',
                'interaction_type': 'whiteboard'
            }
        ]
        
        return activities
    
    def _generate_discussion_prompts(self, content: str) -> List[Dict]:
        """Generate discussion prompts"""
        prompts = [
            {
                'type': 'discussion',
                'prompt': 'What questions do you have about this topic?',
                'interaction_type': 'chat'
            },
            {
                'type': 'discussion',
                'prompt': 'How might you use this knowledge in practice?',
                'interaction_type': 'chat'
            }
        ]
        
        return prompts
    
    def _extract_interactive_components(self, content: str, lesson_type: str) -> List[Dict]:
        """Extract interactive components from slide content"""
        components = []
        
        # Look for interactive markers
        if '🤔' in content or 'think about' in content.lower():
            components.append({
                'type': 'reflection',
                'trigger': 'Think About It',
                'content': 'Reflection prompt detected'
            })
        
        if '🔬' in content or 'activity' in content.lower():
            components.append({
                'type': 'activity',
                'trigger': 'Try This',
                'content': 'Interactive activity detected'
            })
        
        if '?' in content:
            components.append({
                'type': 'question',
                'trigger': 'Question',
                'content': 'Question for discussion detected'
            })
        
        return components
    
    def _generate_voice_narration(self, slides: List[Dict], lesson_type: str) -> Dict:
        """Generate voice narration mapping"""
        narration = {
            'intro': f"Welcome to this {lesson_type} lesson. Let's begin our learning journey.",
            'outro': "That concludes our lesson. Great job following along!",
            'slide_transitions': {
                'next': "Now let's move on to the next topic.",
                'previous': "Let's review the previous section.",
                'pause': "Take a moment to absorb this information."
            },
            'slides': {}
        }
        
        for slide in slides:
            slide_num = slide.get('slide_number', 0)
            narration['slides'][slide_num] = slide.get('narrator_text', '')
        
        return narration

# Singleton instance
lesson_integration_service = LessonIntegrationService()