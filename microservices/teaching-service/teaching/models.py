# MongoDB Models for Real-Time Teaching Service
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from django.conf import settings
import uuid

logger = logging.getLogger(__name__)

class MongoDBConnection:
    """MongoDB connection manager"""
    _instance = None
    _client = None
    _db = None
    
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
                self._db = self._client[mongodb_config['DATABASE']]
                logger.info(f"Connected to MongoDB: {mongodb_config['DATABASE']}")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise
    
    @property
    def db(self):
        return self._db
    
    @property
    def client(self):
        return self._client

# Global MongoDB connection
mongo = MongoDBConnection()

class TeachingSessionModel:
    """Teaching session management"""
    
    collection_name = "teaching_sessions"
    
    @classmethod
    def get_collection(cls):
        return mongo.db[cls.collection_name]
    
    @classmethod
    def create_session(cls, lesson_id: str, user_id: str, session_data: Dict) -> str:
        """Create a new teaching session"""
        try:
            session_doc = {
                "_id": str(uuid.uuid4()),
                "lesson_id": lesson_id,
                "user_id": user_id,
                "session_name": session_data.get("session_name", f"Teaching Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}"),
                "status": "created",  # created, active, paused, completed, ended
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "settings": {
                    "voice_enabled": session_data.get("voice_enabled", True),
                    "whiteboard_enabled": session_data.get("whiteboard_enabled", True),
                    "ai_tutor_enabled": session_data.get("ai_tutor_enabled", True),
                    "interaction_mode": session_data.get("interaction_mode", "guided"),  # guided, free-form
                    "voice_speed": session_data.get("voice_speed", 1.0),
                    "voice_language": session_data.get("voice_language", "en-US"),
                },
                "participants": [user_id],
                "current_slide": 0,
                "progress": 0.0,
                "total_slides": session_data.get("total_slides", 1),
                "lesson_content": session_data.get("lesson_content", {}),
                "whiteboard_state": {},
                "chat_history": [],
                "voice_queue": [],
                "analytics": {
                    "start_time": None,
                    "end_time": None,
                    "total_duration": 0,
                    "slides_visited": [],
                    "questions_asked": 0,
                    "interactions_count": 0,
                }
            }
            
            result = cls.get_collection().insert_one(session_doc)
            logger.info(f"Created teaching session: {result.inserted_id}")
            return result.inserted_id
            
        except Exception as e:
            logger.error(f"Error creating teaching session: {e}")
            raise
    
    @classmethod
    def get_session(cls, session_id: str) -> Optional[Dict]:
        """Get teaching session by ID"""
        try:
            return cls.get_collection().find_one({"_id": session_id})
        except Exception as e:
            logger.error(f"Error getting teaching session {session_id}: {e}")
            return None
    
    @classmethod
    def update_session(cls, session_id: str, updates: Dict) -> bool:
        """Update teaching session"""
        try:
            updates["updated_at"] = datetime.now(timezone.utc)
            result = cls.get_collection().update_one(
                {"_id": session_id},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating teaching session {session_id}: {e}")
            return False
    
    @classmethod
    def get_user_sessions(cls, user_id: str, status: Optional[str] = None) -> List[Dict]:
        """Get all teaching sessions for a user"""
        try:
            query = {"user_id": user_id}
            if status:
                query["status"] = status
            
            sessions = list(cls.get_collection().find(query).sort("created_at", -1))
            return sessions
        except Exception as e:
            logger.error(f"Error getting user sessions for {user_id}: {e}")
            return []

class WhiteboardModel:
    """Whiteboard state management"""
    
    collection_name = "whiteboard_states"
    
    @classmethod
    def get_collection(cls):
        return mongo.db[cls.collection_name]
    
    @classmethod
    def save_whiteboard_state(cls, session_id: str, whiteboard_data: Dict) -> bool:
        """Save whiteboard state"""
        try:
            document = {
                "_id": f"{session_id}_whiteboard",
                "session_id": session_id,
                "whiteboard_data": whiteboard_data,
                "updated_at": datetime.now(timezone.utc),
                "version": whiteboard_data.get("version", 1)
            }
            
            cls.get_collection().replace_one(
                {"_id": f"{session_id}_whiteboard"},
                document,
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error saving whiteboard state for session {session_id}: {e}")
            return False
    
    @classmethod
    def get_whiteboard_state(cls, session_id: str) -> Optional[Dict]:
        """Get whiteboard state"""
        try:
            result = cls.get_collection().find_one({"_id": f"{session_id}_whiteboard"})
            return result.get("whiteboard_data") if result else None
        except Exception as e:
            logger.error(f"Error getting whiteboard state for session {session_id}: {e}")
            return None

class ChatMessageModel:
    """Chat message management"""
    
    collection_name = "chat_messages"
    
    @classmethod
    def get_collection(cls):
        return mongo.db[cls.collection_name]
    
    @classmethod
    def add_message(cls, session_id: str, message_data: Dict) -> str:
        """Add chat message"""
        try:
            message_doc = {
                "_id": str(uuid.uuid4()),
                "session_id": session_id,
                "user_id": message_data.get("user_id"),
                "message": message_data.get("message", ""),
                "message_type": message_data.get("message_type", "user"),  # user, ai, system
                "timestamp": datetime.now(timezone.utc),
                "metadata": message_data.get("metadata", {}),
                "voice_synthesized": False,
                "read": False
            }
            
            result = cls.get_collection().insert_one(message_doc)
            return result.inserted_id
        except Exception as e:
            logger.error(f"Error adding chat message: {e}")
            raise
    
    @classmethod
    def get_session_messages(cls, session_id: str, limit: int = 100) -> List[Dict]:
        """Get chat messages for session"""
        try:
            messages = list(
                cls.get_collection()
                .find({"session_id": session_id})
                .sort("timestamp", -1)
                .limit(limit)
            )
            return list(reversed(messages))  # Return in chronological order
        except Exception as e:
            logger.error(f"Error getting session messages for {session_id}: {e}")
            return []

class VoiceQueueModel:
    """Voice synthesis queue management"""
    
    collection_name = "voice_queue"
    
    @classmethod
    def get_collection(cls):
        return mongo.db[cls.collection_name]
    
    @classmethod
    def add_to_queue(cls, session_id: str, voice_data: Dict) -> str:
        """Add voice synthesis request to queue"""
        try:
            queue_doc = {
                "_id": str(uuid.uuid4()),
                "session_id": session_id,
                "text": voice_data.get("text", ""),
                "voice_settings": voice_data.get("voice_settings", {}),
                "priority": voice_data.get("priority", 5),  # 1-10, lower is higher priority
                "status": "queued",  # queued, processing, completed, failed
                "created_at": datetime.now(timezone.utc),
                "processed_at": None,
                "audio_url": None,
                "metadata": voice_data.get("metadata", {})
            }
            
            result = cls.get_collection().insert_one(queue_doc)
            return result.inserted_id
        except Exception as e:
            logger.error(f"Error adding to voice queue: {e}")
            raise
    
    @classmethod
    def get_next_in_queue(cls, session_id: str) -> Optional[Dict]:
        """Get next voice item to process"""
        try:
            return cls.get_collection().find_one(
                {"session_id": session_id, "status": "queued"},
                sort=[("priority", 1), ("created_at", 1)]
            )
        except Exception as e:
            logger.error(f"Error getting next voice queue item: {e}")
            return None
    
    @classmethod
    def update_queue_item(cls, item_id: str, updates: Dict) -> bool:
        """Update voice queue item"""
        try:
            result = cls.get_collection().update_one(
                {"_id": item_id},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating voice queue item {item_id}: {e}")
            return False

class LessonInteractionModel:
    """Lesson interaction tracking"""
    
    collection_name = "lesson_interactions"
    
    @classmethod
    def get_collection(cls):
        return mongo.db[cls.collection_name]
    
    @classmethod
    def track_interaction(cls, session_id: str, interaction_data: Dict) -> str:
        """Track user interaction"""
        try:
            interaction_doc = {
                "_id": str(uuid.uuid4()),
                "session_id": session_id,
                "user_id": interaction_data.get("user_id"),
                "interaction_type": interaction_data.get("interaction_type"),  # slide_change, question, drawing, etc.
                "content": interaction_data.get("content", {}),
                "timestamp": datetime.now(timezone.utc),
                "metadata": interaction_data.get("metadata", {})
            }
            
            result = cls.get_collection().insert_one(interaction_doc)
            return result.inserted_id
        except Exception as e:
            logger.error(f"Error tracking interaction: {e}")
            raise
    
    @classmethod
    def get_session_interactions(cls, session_id: str) -> List[Dict]:
        """Get all interactions for a session"""
        try:
            interactions = list(
                cls.get_collection()
                .find({"session_id": session_id})
                .sort("timestamp", 1)
            )
            return interactions
        except Exception as e:
            logger.error(f"Error getting session interactions for {session_id}: {e}")
            return []