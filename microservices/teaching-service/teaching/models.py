# Teaching Service Models - MongoDB Integrationfrom django.db import models

import logging

from datetime import datetime, timezone# Create your models here.

from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from django.conf import settings
import uuid
import requests

logger = logging.getLogger(__name__)

class MongoDBConnection:
    """MongoDB connection manager for Teaching Service"""
    _instance = None
    _client = None
    _lesson_db = None
    _teaching_db = None
    _user_db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            try:
                mongodb_config = settings.MONGODB_SETTINGS
                self._client = MongoClient(
                    host=mongodb_config['HOST'],
                    port=mongodb_config['PORT']
                )
                self._lesson_db = self._client[mongodb_config['LESSON_DB']]
                self._teaching_db = self._client[mongodb_config['TEACHING_DB']]
                self._user_db = self._client[mongodb_config['USER_DB']]
                logger.info("Connected to MongoDB for Teaching Service")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                self._client = None
                self._lesson_db = None
                self._teaching_db = None
                self._user_db = None
    
    @property
    def lesson_db(self):
        return self._lesson_db
    
    @property
    def teaching_db(self):
        return self._teaching_db
    
    @property
    def user_db(self):
        return self._user_db
    
    @property
    def client(self):
        return self._client

# Global MongoDB connection
mongo = MongoDBConnection()

class LessonService:
    """Service to fetch lessons from Lesson Service database"""
    
    @classmethod
    def get_user_lessons(cls, user_id: str) -> List[Dict]:
        """Get all lessons for a user from the lesson database"""
        try:
            if mongo.lesson_db is not None:
                lessons_collection = mongo.lesson_db.lessons
                lessons = list(lessons_collection.find({'user_id': user_id}).sort('created_at', -1))
                
                # Convert ObjectId to string for JSON serialization
                for lesson in lessons:
                    lesson['_id'] = str(lesson['_id'])
                    if 'pdf_id' in lesson:
                        lesson['pdf_id'] = str(lesson['pdf_id'])
                    if 'created_at' in lesson:
                        lesson['created_at'] = lesson['created_at'].isoformat()
                    if 'updated_at' in lesson:
                        lesson['updated_at'] = lesson['updated_at'].isoformat()
                
                logger.info(f"Found {len(lessons)} lessons for user {user_id}")
                return lessons
            else:
                logger.warning("MongoDB unavailable, returning mock lessons")
                return cls._get_mock_lessons(user_id)
        except Exception as e:
            logger.error(f"Error getting user lessons: {e}")
            return cls._get_mock_lessons(user_id)
    
    @classmethod
    def get_lesson_by_id(cls, lesson_id: str) -> Optional[Dict]:
        """Get a specific lesson by ID"""
        try:
            if mongo.lesson_db is not None:
                lessons_collection = mongo.lesson_db.lessons
                lesson = lessons_collection.find_one({'_id': lesson_id})
                
                if lesson:
                    lesson['_id'] = str(lesson['_id'])
                    if 'pdf_id' in lesson:
                        lesson['pdf_id'] = str(lesson['pdf_id'])
                    if 'created_at' in lesson:
                        lesson['created_at'] = lesson['created_at'].isoformat()
                    if 'updated_at' in lesson:
                        lesson['updated_at'] = lesson['updated_at'].isoformat()
                
                return lesson
            else:
                logger.warning("MongoDB unavailable, returning mock lesson")
                return cls._get_mock_lesson(lesson_id)
        except Exception as e:
            logger.error(f"Error getting lesson {lesson_id}: {e}")
            return cls._get_mock_lesson(lesson_id)
    
    @classmethod
    def _get_mock_lessons(cls, user_id: str) -> List[Dict]:
        """Mock lessons for fallback"""
        return [
            {
                '_id': 'mock_lesson_1',
                'user_id': user_id,
                'lesson_title': 'Introduction to Python Programming',
                'lesson_content': {
                    'title': 'Introduction to Python Programming',
                    'content': 'Python is a versatile programming language. Let\'s start with variables and basic syntax.',
                    'slides': [
                        {'title': 'What is Python?', 'content': 'Python is a high-level programming language.'},
                        {'title': 'Variables', 'content': 'Variables store data values. Example: x = 5'},
                        {'title': 'Data Types', 'content': 'Python has several data types: int, float, str, bool'}
                    ]
                },
                'lesson_type': 'interactive',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'status': 'generated'
            },
            {
                '_id': 'mock_lesson_2',
                'user_id': user_id,
                'lesson_title': 'Data Structures in Programming',
                'lesson_content': {
                    'title': 'Data Structures in Programming',
                    'content': 'Understanding arrays, lists, and dictionaries is crucial for programming.',
                    'slides': [
                        {'title': 'Arrays vs Lists', 'content': 'Arrays have fixed size, lists are dynamic.'},
                        {'title': 'Dictionaries', 'content': 'Key-value pairs for efficient data lookup.'},
                        {'title': 'When to Use What', 'content': 'Choose the right data structure for your needs.'}
                    ]
                },
                'lesson_type': 'interactive',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'status': 'generated'
            }
        ]
    
    @classmethod
    def _get_mock_lesson(cls, lesson_id: str) -> Dict:
        """Mock lesson for fallback"""
        return {
            '_id': lesson_id,
            'user_id': 'mock_user',
            'lesson_title': 'Sample Programming Lesson',
            'lesson_content': {
                'title': 'Sample Programming Lesson',
                'content': 'This is a sample lesson content for teaching purposes.',
                'slides': [
                    {'title': 'Introduction', 'content': 'Welcome to this programming lesson.'},
                    {'title': 'Concepts', 'content': 'Let\'s explore key programming concepts.'},
                    {'title': 'Practice', 'content': 'Now let\'s practice what we\'ve learned.'}
                ]
            },
            'lesson_type': 'interactive',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'status': 'generated'
        }

class TeachingSessionModel:
    """Teaching session management with Konva.js integration"""
    
    collection_name = "teaching_sessions"
    
    @classmethod
    def get_collection(cls):
        if mongo.teaching_db is not None:
            return mongo.teaching_db[cls.collection_name]
        return None
    
    @classmethod
    def create_session(cls, lesson_id: str, user_id: str, session_data: Dict) -> str:
        """Create a new teaching session"""
        try:
            session_id = str(uuid.uuid4())
            session_doc = {
                "_id": session_id,
                "lesson_id": lesson_id,
                "user_id": user_id,
                "session_name": session_data.get("session_name", f"Teaching Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}"),
                "status": "created",  # created, active, paused, completed, ended
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "settings": {
                    "voice_enabled": session_data.get("voice_enabled", True),
                    "whiteboard_enabled": session_data.get("whiteboard_enabled", True),
                    "konva_enabled": session_data.get("konva_enabled", True),
                    "interaction_mode": session_data.get("interaction_mode", "guided"),
                    "voice_speed": session_data.get("voice_speed", 1.0),
                    "voice_language": session_data.get("voice_language", "en-US"),
                },
                "participants": [user_id],
                "current_slide": 0,
                "progress": 0.0,
                "total_slides": session_data.get("total_slides", 1),
                "lesson_content": session_data.get("lesson_content", {}),
                "konva_state": {},  # Konva.js whiteboard state
                "teaching_steps": [],
                "interactions": [],
                "analytics": {
                    "start_time": None,
                    "end_time": None,
                    "total_duration": 0,
                    "slides_visited": [],
                    "questions_asked": 0,
                    "interactions_count": 0,
                }
            }
            
            collection = cls.get_collection()
            if collection is not None:
                result = collection.insert_one(session_doc)
                logger.info(f"Created teaching session: {result.inserted_id}")
                return str(result.inserted_id)
            else:
                logger.warning("MongoDB collection not available, returning mock session ID")
                return session_id
            
        except Exception as e:
            logger.error(f"Error creating teaching session: {e}")
            return str(uuid.uuid4())  # Return mock session ID as fallback
    
    @classmethod
    def get_session(cls, session_id: str) -> Optional[Dict]:
        """Get teaching session by ID"""
        try:
            collection = cls.get_collection()
            if collection is not None:
                return collection.find_one({"_id": session_id})
            return None
        except Exception as e:
            logger.error(f"Error getting teaching session {session_id}: {e}")
            return None
    
    @classmethod
    def update_session(cls, session_id: str, updates: Dict) -> bool:
        """Update teaching session"""
        try:
            collection = cls.get_collection()
            if collection is not None:
                updates["updated_at"] = datetime.now(timezone.utc)
                result = collection.update_one(
                    {"_id": session_id},
                    {"$set": updates}
                )
                return result.modified_count > 0
            return False
        except Exception as e:
            logger.error(f"Error updating teaching session {session_id}: {e}")
            return False
    
    @classmethod
    def delete_session(cls, session_id: str) -> bool:
        """Delete a teaching session"""
        try:
            collection = cls.get_collection()
            if collection is not None:
                result = collection.delete_one({"_id": session_id})
                return result.deleted_count > 0
            return False
        except Exception as e:
            logger.error(f"Error deleting teaching session {session_id}: {e}")
            return False
    
    @classmethod
    def get_user_sessions(cls, user_id: str, status: Optional[str] = None) -> List[Dict]:
        """Get all teaching sessions for a user"""
        try:
            query = {"user_id": user_id}
            if status:
                query["status"] = status
            
            collection = cls.get_collection()
            if collection is not None:
                sessions = list(collection.find(query).sort("created_at", -1))
                return sessions
            else:
                # Fallback: return mock sessions when MongoDB is unavailable
                logger.warning("MongoDB unavailable, returning mock sessions")
                return [
                    {
                        "_id": "mock_session_1",
                        "user_id": user_id,
                        "session_name": "Sample Teaching Session 1",
                        "status": "completed",
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    },
                    {
                        "_id": "mock_session_2", 
                        "user_id": user_id,
                        "session_name": "Sample Teaching Session 2",
                        "status": "active",
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                ]
        except Exception as e:
            logger.error(f"Error getting user sessions for {user_id}: {e}")
            return []

class UserService:
    """Service to fetch user data from User Service"""
    
    @classmethod
    def get_user_profile(cls, user_id: str) -> Optional[Dict]:
        """Get user profile data"""
        try:
            if mongo.user_db is not None:
                users_collection = mongo.user_db.users
                user = users_collection.find_one({'_id': user_id})
                
                if user:
                    user['_id'] = str(user['_id'])
                    if 'created_at' in user:
                        user['created_at'] = user['created_at'].isoformat()
                    if 'updated_at' in user:
                        user['updated_at'] = user['updated_at'].isoformat()
                
                return user
            else:
                logger.warning("MongoDB unavailable, returning mock user")
                return cls._get_mock_user(user_id)
        except Exception as e:
            logger.error(f"Error getting user profile {user_id}: {e}")
            return cls._get_mock_user(user_id)
    
    @classmethod
    def _get_mock_user(cls, user_id: str) -> Dict:
        """Mock user for fallback"""
        return {
            '_id': user_id,
            'username': 'demo_user',
            'email': 'demo@gnyansetu.com',
            'full_name': 'Demo User',
            'profile_picture': None,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'lesson_count': 5,
            'total_sessions': 12
        }