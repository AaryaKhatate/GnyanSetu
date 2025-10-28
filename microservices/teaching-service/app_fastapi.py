"""
Teaching Service - FastAPI Implementation
Real-time teaching with WebSocket support and lesson integration
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from bson import ObjectId
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# MONGODB CONNECTION
# ============================================================================

class MongoDBConnection:
    """MongoDB connection manager"""
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
                mongodb_host = os.getenv('MONGODB_HOST', 'localhost')
                mongodb_port = int(os.getenv('MONGODB_PORT', 27017))
                
                self._client = MongoClient(
                    host=mongodb_host,
                    port=mongodb_port
                )
                self._lesson_db = self._client['lesson_db']
                self._teaching_db = self._client['teaching_db']
                self._user_db = self._client['user_db']
                logger.info(" Connected to MongoDB for Teaching Service")
            except Exception as e:
                logger.error(f" Failed to connect to MongoDB: {e}")
                self._client = None
    
    @property
    def lesson_db(self):
        return self._lesson_db
    
    @property
    def teaching_db(self):
        return self._teaching_db
    
    @property
    def user_db(self):
        return self._user_db

# Global MongoDB connection
mongo = MongoDBConnection()

# ============================================================================
# DATA MODELS
# ============================================================================

class TeachingSessionModel:
    """Teaching session management"""
    
    @classmethod
    def create_session(cls, lesson_id: str, user_id: str) -> Optional[str]:
        """Create a new teaching session"""
        try:
            if mongo.teaching_db is None:
                return None
            
            sessions_collection = mongo.teaching_db.teaching_sessions
            
            session = {
                'lesson_id': lesson_id,
                'user_id': user_id,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'status': 'active',
                'konva_state': {},
                'messages': []
            }
            
            result = sessions_collection.insert_one(session)
            session_id = str(result.inserted_id)
            
            logger.info(f" Created teaching session: {session_id}")
            return session_id
        except Exception as e:
            logger.error(f" Error creating session: {e}")
            return None
    
    @classmethod
    def get_session(cls, session_id: str) -> Optional[Dict]:
        """Get a teaching session by ID"""
        try:
            if mongo.teaching_db is None or not ObjectId.is_valid(session_id):
                return None
            
            sessions_collection = mongo.teaching_db.teaching_sessions
            session = sessions_collection.find_one({'_id': ObjectId(session_id)})
            
            if session:
                session['_id'] = str(session['_id'])
                if 'created_at' in session:
                    session['created_at'] = session['created_at'].isoformat()
                if 'updated_at' in session:
                    session['updated_at'] = session['updated_at'].isoformat()
            
            return session
        except Exception as e:
            logger.error(f" Error getting session: {e}")
            return None
    
    @classmethod
    def update_session(cls, session_id: str, updates: Dict) -> bool:
        """Update a teaching session"""
        try:
            if mongo.teaching_db is None or not ObjectId.is_valid(session_id):
                return False
            
            sessions_collection = mongo.teaching_db.teaching_sessions
            updates['updated_at'] = datetime.now(timezone.utc)
            
            result = sessions_collection.update_one(
                {'_id': ObjectId(session_id)},
                {'$set': updates}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f" Error updating session: {e}")
            return False
    
    @classmethod
    def delete_session(cls, session_id: str) -> bool:
        """Delete a teaching session"""
        try:
            if mongo.teaching_db is None or not ObjectId.is_valid(session_id):
                return False
            
            sessions_collection = mongo.teaching_db.teaching_sessions
            result = sessions_collection.delete_one({'_id': ObjectId(session_id)})
            
            logger.info(f" Deleted session: {session_id}")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f" Error deleting session: {e}")
            return False

# ============================================================================
# FASTAPI APP
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app"""
    logger.info("=" * 60)
    logger.info("Starting Teaching Service (FastAPI)")
    logger.info("=" * 60)
    yield
    logger.info("Shutting down Teaching Service")

app = FastAPI(
    title="Teaching Service",
    description="Real-time teaching with WebSocket support",
    version="3.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Teaching Service (FastAPI)",
        "version": "3.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "connected" if mongo.teaching_db else "unavailable",
        "features": {
            "konva_whiteboard": True,
            "lesson_integration": True,
            "real_time_teaching": True,
            "websockets": True
        }
    }

# ============================================================================
# CONVERSATION ENDPOINTS (DASHBOARD COMPATIBILITY)
# ============================================================================

@app.get("/api/conversations/")
async def list_conversations(user_id: str = Query(..., description="User ID")):
    """Get all conversations (lessons) for a user"""
    try:
        logger.info(f"[FETCH] Fetching conversations for user: {user_id}")
        
        if mongo.lesson_db is None:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Get lessons from lesson database
        lessons_collection = mongo.lesson_db.lessons
        lessons = list(lessons_collection.find({'user_id': user_id}).sort('created_at', -1))
        
        # Transform to conversation format
        conversations = []
        for lesson in lessons:
            conversations.append({
                '_id': str(lesson['_id']),
                'conversation_id': str(lesson['_id']),
                'id': str(lesson['_id']),
                'title': lesson.get('lesson_title', 'Untitled Lesson'),
                'timestamp': lesson.get('created_at', datetime.now(timezone.utc)).isoformat(),
                'created_at': lesson.get('created_at', datetime.now(timezone.utc)).isoformat(),
                'updated_at': lesson.get('updated_at', datetime.now(timezone.utc)).isoformat(),
                'user_id': user_id,
                'lesson_type': lesson.get('lesson_type', 'interactive'),
                'status': lesson.get('status', 'generated'),
                'message_count': 0
            })
        
        logger.info(f" Returning {len(conversations)} conversations")
        
        return {
            'conversations': conversations,
            'total': len(conversations),
            'user_id': user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Error fetching conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversations: {str(e)}")

@app.post("/api/conversations/create/")
async def create_conversation(data: dict):
    """Create a new conversation"""
    try:
        user_id = data.get('user_id', 'dashboard_user')
        title = data.get('title', 'New Conversation')
        
        logger.info(f" Creating conversation: {title}")
        
        # Create a temporary conversation (will be replaced when lesson is generated)
        conversation_id = f"temp_{datetime.now(timezone.utc).timestamp()}"
        
        return {
            'conversation_id': conversation_id,
            'id': conversation_id,
            'title': title,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'user_id': user_id,
            'status': 'pending'
        }
        
    except Exception as e:
        logger.error(f" Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")

@app.delete("/api/conversations/{conversation_id}/delete/")
async def delete_conversation(conversation_id: str):
    """Delete a conversation/teaching session"""
    try:
        logger.info(f"[DELETE] Deleting conversation: {conversation_id}")
        
        # Delete teaching session if exists
        deleted_session = False
        if ObjectId.is_valid(conversation_id):
            deleted_session = TeachingSessionModel.delete_session(conversation_id)
        
        logger.info(f" Conversation deleted (session: {deleted_session})")
        
        return {
            'success': True,
            'message': f'Conversation {conversation_id} deleted successfully',
            'conversation_id': conversation_id,
            'deleted_session': deleted_session
        }
        
    except Exception as e:
        logger.error(f" Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")

# ============================================================================
# LESSON ENDPOINTS
# ============================================================================

@app.get("/api/lessons/{lesson_id}/")
async def get_lesson_detail(lesson_id: str):
    """Get detailed lesson content"""
    try:
        logger.info(f"[FETCH] Fetching lesson: {lesson_id}")
        
        if mongo.lesson_db is None or not ObjectId.is_valid(lesson_id):
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        lessons_collection = mongo.lesson_db.lessons
        lesson = lessons_collection.find_one({'_id': ObjectId(lesson_id)})
        
        if lesson is None:
            raise HTTPException(status_code=404, detail="Lesson not found")
        
        # Convert ObjectId to string
        lesson['_id'] = str(lesson['_id'])
        if 'pdf_id' in lesson:
            lesson['pdf_id'] = str(lesson['pdf_id'])
        if 'created_at' in lesson:
            lesson['created_at'] = lesson['created_at'].isoformat()
        if 'updated_at' in lesson:
            lesson['updated_at'] = lesson['updated_at'].isoformat()
        
        logger.info(f" Found lesson: {lesson.get('lesson_title')}")
        
        return {'lesson': lesson}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Error fetching lesson: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch lesson: {str(e)}")

# ============================================================================
# TEACHING SESSION ENDPOINTS
# ============================================================================

@app.post("/api/sessions/start/")
async def start_teaching_session(data: dict):
    """Start a new teaching session"""
    try:
        lesson_id = data.get('lesson_id')
        user_id = data.get('user_id', 'dashboard_user')
        
        if not lesson_id:
            raise HTTPException(status_code=400, detail="lesson_id is required")
        
        logger.info(f" Starting teaching session for lesson: {lesson_id}")
        
        session_id = TeachingSessionModel.create_session(lesson_id, user_id)
        
        if session_id is None:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        return {
            'session_id': session_id,
            'lesson_id': lesson_id,
            'user_id': user_id,
            'status': 'active',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Error starting session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")

@app.post("/api/sessions/stop/")
async def stop_teaching_session(data: dict):
    """Stop a teaching session"""
    try:
        session_id = data.get('session_id')
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        logger.info(f" Stopping teaching session: {session_id}")
        
        success = TeachingSessionModel.update_session(session_id, {
            'status': 'completed',
            'ended_at': datetime.now(timezone.utc)
        })
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            'session_id': session_id,
            'status': 'completed',
            'message': 'Session stopped successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Error stopping session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop session: {str(e)}")

# ============================================================================
# KONVA WHITEBOARD ENDPOINTS
# ============================================================================

@app.post("/api/konva/update/")
async def update_konva_state(data: dict):
    """Update Konva.js whiteboard state"""
    try:
        session_id = data.get('session_id')
        konva_state = data.get('konva_state', {})
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        logger.info(f" Updating Konva state for session: {session_id}")
        
        success = TeachingSessionModel.update_session(session_id, {
            'konva_state': konva_state
        })
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            'session_id': session_id,
            'konva_state': konva_state,
            'message': 'Konva state updated successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Error updating Konva state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update Konva state: {str(e)}")

@app.get("/api/konva/{session_id}/")
async def get_konva_state(session_id: str):
    """Get Konva.js whiteboard state"""
    try:
        logger.info(f" Getting Konva state for session: {session_id}")
        
        session = TeachingSessionModel.get_session(session_id)
        
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            'session_id': session_id,
            'konva_state': session.get('konva_state', {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Error getting Konva state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get Konva state: {str(e)}")

# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

class ConnectionManager:
    """Manage WebSocket connections"""
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"[WS] WebSocket connected: {session_id}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"[WS] WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/teaching/{session_id}")
async def teaching_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time teaching"""
    await manager.connect(session_id, websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message_type = data.get('type', 'message')
            content = data.get('content', '')
            
            logger.info(f"[MSG] Received {message_type}: {content[:50]}...")
            
            # Echo back for now (replace with actual AI teaching logic)
            response = {
                'type': 'response',
                'content': f"Received: {content}",
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            await manager.send_message(session_id, response)
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"Client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv('PORT', 8004))
    
    uvicorn.run(
        "app_fastapi:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
