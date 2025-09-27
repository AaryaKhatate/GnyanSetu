# AI Tutor Service for Real-Time Q&A and Teaching Assistance
import logging
import asyncio
from typing import Dict, List, Optional, Any
import requests
import json
from django.conf import settings
from .models import TeachingSessionModel, ChatMessageModel, LessonInteractionModel

logger = logging.getLogger(__name__)

class AITutorService:
    """AI-powered tutor for real-time teaching assistance and Q&A"""
    
    def __init__(self):
        self.teaching_settings = settings.TEACHING_SETTINGS
        self.lesson_service_url = self.teaching_settings.get('LESSON_SERVICE_URL', 'http://localhost:8003')
        
    async def generate_response(self, user_message: str, session_id: str, context: Dict = None) -> str:
        """
        Generate AI tutor response based on user question and lesson context
        """
        try:
            # Get session information
            session = await self._get_session_info(session_id)
            if not session:
                return "I'm sorry, I couldn't access the session information. Please try again."
            
            # Get lesson context
            lesson_context = await self._get_lesson_context(session.get('lesson_id'))
            
            # Get recent chat history for context
            chat_history = await self._get_recent_chat_history(session_id, limit=5)
            
            # Prepare AI prompt
            ai_prompt = self._create_ai_prompt(
                user_message=user_message,
                lesson_context=lesson_context,
                chat_history=chat_history,
                session_info=session,
                additional_context=context or {}
            )
            
            # Generate response using Gemini AI (same as lesson service)
            response = await self._call_gemini_api(ai_prompt)
            
            if response:
                # Track AI interaction
                await self._track_ai_interaction(session_id, user_message, response)
                return response
            else:
                return "I'm having trouble generating a response right now. Please try rephrasing your question."
                
        except Exception as e:
            logger.error(f"Error generating AI tutor response: {e}")
            return "I encountered an error while processing your question. Please try again."
    
    async def _get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get teaching session information"""
        try:
            from asgiref.sync import sync_to_async
            session = await sync_to_async(TeachingSessionModel.get_session)(session_id)
            return session
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return None
    
    async def _get_lesson_context(self, lesson_id: str) -> Dict:
        """Get lesson content from lesson service"""
        try:
            if not lesson_id:
                return {}
            
            # Call lesson service API
            response = requests.get(
                f"{self.lesson_service_url}/api/lessons/{lesson_id}/",
                timeout=10
            )
            
            if response.status_code == 200:
                lesson_data = response.json()
                return {
                    'lesson_title': lesson_data.get('lesson_title', ''),
                    'lesson_content': lesson_data.get('lesson_content', ''),
                    'lesson_type': lesson_data.get('lesson_type', ''),
                    'key_concepts': self._extract_key_concepts(lesson_data.get('lesson_content', ''))
                }
            else:
                logger.warning(f"Failed to get lesson context: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting lesson context: {e}")
            return {}
    
    async def _get_recent_chat_history(self, session_id: str, limit: int = 5) -> List[Dict]:
        """Get recent chat messages for context"""
        try:
            from asgiref.sync import sync_to_async
            messages = await sync_to_async(ChatMessageModel.get_session_messages)(session_id, limit)
            return messages[-limit:] if messages else []
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
    def _create_ai_prompt(self, user_message: str, lesson_context: Dict, chat_history: List[Dict], 
                         session_info: Dict, additional_context: Dict) -> str:
        """Create comprehensive AI prompt for tutoring"""
        
        prompt = f"""You are an intelligent AI tutor helping a student learn. You are currently in a teaching session about "{lesson_context.get('lesson_title', 'the current lesson')}".

LESSON CONTEXT:
Title: {lesson_context.get('lesson_title', 'N/A')}
Type: {lesson_context.get('lesson_type', 'N/A')}
Content Summary: {lesson_context.get('lesson_content', '')[:500]}...

KEY CONCEPTS:
{', '.join(lesson_context.get('key_concepts', []))}

RECENT CONVERSATION:
"""
        
        # Add recent chat history
        for msg in chat_history[-3:]:  # Last 3 messages for context
            sender = "Student" if msg.get('message_type') == 'user' else "AI Tutor"
            prompt += f"{sender}: {msg.get('message', '')}\n"
        
        prompt += f"""
CURRENT STUDENT QUESTION: {user_message}

INSTRUCTIONS:
1. Answer the student's question clearly and concisely
2. Relate your answer to the current lesson content when relevant
3. Use simple, educational language appropriate for learning
4. If the question is off-topic, gently redirect to the lesson
5. Encourage further questions and engagement
6. Provide examples or analogies when helpful
7. Keep responses under 200 words for real-time interaction

RESPONSE:"""
        
        return prompt
    
    async def _call_gemini_api(self, prompt: str) -> Optional[str]:
        """Call Gemini API for AI response generation"""
        try:
            # This would integrate with the same Gemini API used in lesson service
            # For now, simulate with a call to lesson service
            response = requests.post(
                f"{self.lesson_service_url}/api/generate-ai-response/",
                json={
                    'prompt': prompt,
                    'max_tokens': 200,
                    'temperature': 0.7
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('response', '')
            else:
                logger.warning(f"Gemini API call failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return None
    
    def _extract_key_concepts(self, lesson_content: str) -> List[str]:
        """Extract key concepts from lesson content"""
        try:
            # Simple keyword extraction - could be enhanced with NLP
            import re
            
            # Look for headers, bold text, or key phrases
            concepts = []
            
            # Extract headers (markdown style)
            headers = re.findall(r'#+\s+(.+)', lesson_content)
            concepts.extend(headers)
            
            # Extract bold text
            bold_text = re.findall(r'\*\*(.+?)\*\*', lesson_content)
            concepts.extend(bold_text)
            
            # Extract items from lists
            list_items = re.findall(r'^[-*]\s+(.+)', lesson_content, re.MULTILINE)
            concepts.extend(list_items)
            
            # Clean and deduplicate
            concepts = [concept.strip() for concept in concepts if concept.strip()]
            concepts = list(set(concepts))  # Remove duplicates
            
            return concepts[:10]  # Return top 10 concepts
            
        except Exception as e:
            logger.error(f"Error extracting key concepts: {e}")
            return []
    
    async def _track_ai_interaction(self, session_id: str, user_message: str, ai_response: str):
        """Track AI tutor interaction for analytics"""
        try:
            from asgiref.sync import sync_to_async
            
            await sync_to_async(LessonInteractionModel.track_interaction)(
                session_id,
                {
                    'user_id': 'system',
                    'interaction_type': 'ai_tutor_qa',
                    'content': {
                        'user_message': user_message,
                        'ai_response': ai_response,
                        'response_length': len(ai_response)
                    },
                    'metadata': {
                        'tutor_type': 'ai',
                        'response_generated': True
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Error tracking AI interaction: {e}")
    
    async def suggest_questions(self, session_id: str, current_slide: int = 0) -> List[str]:
        """Suggest relevant questions based on current lesson content"""
        try:
            session = await self._get_session_info(session_id)
            if not session:
                return []
            
            lesson_context = await self._get_lesson_context(session.get('lesson_id'))
            
            # Generate question suggestions based on lesson content
            suggestions = [
                "Can you explain this concept in simpler terms?",
                "What are some real-world examples of this?",
                "How does this relate to what we learned earlier?",
                "What should I remember most about this topic?",
                "Can you provide more details about this section?"
            ]
            
            # Customize based on lesson content
            if lesson_context.get('lesson_type') == 'quiz':
                suggestions.extend([
                    "Can you give me a practice question?",
                    "What are the key points I should study?",
                    "How can I test my understanding?"
                ])
            elif lesson_context.get('lesson_type') == 'interactive':
                suggestions.extend([
                    "What activities can help me learn this better?",
                    "Can we try an example together?",
                    "How can I apply this knowledge?"
                ])
            
            return suggestions[:6]  # Return top 6 suggestions
            
        except Exception as e:
            logger.error(f"Error generating question suggestions: {e}")
            return []
    
    async def provide_explanation(self, concept: str, session_id: str, detail_level: str = 'medium') -> str:
        """Provide detailed explanation of a specific concept"""
        try:
            session = await self._get_session_info(session_id)
            lesson_context = await self._get_lesson_context(session.get('lesson_id')) if session else {}
            
            prompt = f"""Explain the concept "{concept}" in the context of the lesson "{lesson_context.get('lesson_title', 'current lesson')}".

Detail Level: {detail_level}
Lesson Context: {lesson_context.get('lesson_content', '')[:300]}...

Provide a {detail_level}-level explanation that:
1. Defines the concept clearly
2. Relates it to the current lesson
3. Includes examples if helpful
4. Uses appropriate complexity for the detail level

Explanation:"""
            
            response = await self._call_gemini_api(prompt)
            return response or "I couldn't generate an explanation right now. Please try again."
            
        except Exception as e:
            logger.error(f"Error providing explanation: {e}")
            return "I encountered an error while generating the explanation."
    
    async def generate_practice_question(self, session_id: str, topic: str = None) -> Dict:
        """Generate a practice question based on lesson content"""
        try:
            session = await self._get_session_info(session_id)
            lesson_context = await self._get_lesson_context(session.get('lesson_id')) if session else {}
            
            topic_text = f" about {topic}" if topic else ""
            
            prompt = f"""Generate a practice question{topic_text} based on this lesson:

Lesson Title: {lesson_context.get('lesson_title', 'Current Lesson')}
Lesson Content: {lesson_context.get('lesson_content', '')[:400]}...

Create a question that:
1. Tests understanding of key concepts
2. Is appropriate for the lesson level
3. Has a clear, correct answer
4. Helps reinforce learning

Return in this format:
QUESTION: [Your question here]
ANSWER: [Correct answer here]
EXPLANATION: [Brief explanation of why this answer is correct]

Practice Question:"""
            
            response = await self._call_gemini_api(prompt)
            
            if response:
                # Parse response into structured format
                return self._parse_practice_question(response)
            else:
                return {
                    'question': 'What is the main concept we\'re learning about in this lesson?',
                    'answer': 'Please refer to the lesson content for the answer.',
                    'explanation': 'This is a general question to help you review the lesson.'
                }
                
        except Exception as e:
            logger.error(f"Error generating practice question: {e}")
            return {}
    
    def _parse_practice_question(self, response: str) -> Dict:
        """Parse AI response into structured practice question"""
        try:
            import re
            
            question_match = re.search(r'QUESTION:\s*(.+?)(?=ANSWER:|$)', response, re.DOTALL)
            answer_match = re.search(r'ANSWER:\s*(.+?)(?=EXPLANATION:|$)', response, re.DOTALL)
            explanation_match = re.search(r'EXPLANATION:\s*(.+)', response, re.DOTALL)
            
            return {
                'question': question_match.group(1).strip() if question_match else response,
                'answer': answer_match.group(1).strip() if answer_match else '',
                'explanation': explanation_match.group(1).strip() if explanation_match else ''
            }
            
        except Exception as e:
            logger.error(f"Error parsing practice question: {e}")
            return {'question': response, 'answer': '', 'explanation': ''}

# Singleton instance
ai_tutor_service = AITutorService()