"""
MongoDB Manager for User Sessions
Stores user sessions in MongoDB instead of SQLite to avoid UNIQUE constraint issues
"""
import logging
from datetime import datetime
from pymongo import MongoClient
from django.conf import settings

logger = logging.getLogger(__name__)


class MongoDBSessionManager:
    """
    Manages user sessions in MongoDB
    """
    
    def __init__(self):
        """Initialize MongoDB connection"""
        mongo_settings = settings.MONGODB_SETTINGS
        self.client = MongoClient(
            host=mongo_settings['HOST'],
            port=mongo_settings['PORT']
        )
        self.db = self.client[mongo_settings['DATABASE']]
        self.sessions_collection = self.db['user_sessions']
        
        # Create index on session_token for faster lookups (NOT UNIQUE)
        self.sessions_collection.create_index('session_token')
        self.sessions_collection.create_index('user_email')
        self.sessions_collection.create_index('is_active')
        
        logger.info(f"[SUCCESS] MongoDB Session Manager initialized - Database: {mongo_settings['DATABASE']}")
    
    def create_session(self, user_email, session_token, ip_address, user_agent, device_info=None):
        """
        Create a new user session in MongoDB
        """
        try:
            session_data = {
                'user_email': user_email,
                'session_token': session_token,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'device_info': device_info or {},
                'is_active': True,
                'login_time': datetime.utcnow(),
                'last_activity': datetime.utcnow(),
                'is_suspicious': False,
                'failed_attempts': 0
            }
            
            result = self.sessions_collection.insert_one(session_data)
            logger.info(f"[SUCCESS] Session created in MongoDB for {user_email} - ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to create session in MongoDB: {str(e)}")
            raise
    
    def get_session(self, session_token):
        """
        Get session by session_token
        """
        try:
            session = self.sessions_collection.find_one({'session_token': session_token})
            return session
        except Exception as e:
            logger.error(f"[ERROR] Failed to get session: {str(e)}")
            return None
    
    def get_user_sessions(self, user_email, active_only=True):
        """
        Get all sessions for a user
        """
        try:
            query = {'user_email': user_email}
            if active_only:
                query['is_active'] = True
            
            sessions = list(self.sessions_collection.find(query).sort('login_time', -1))
            return sessions
        except Exception as e:
            logger.error(f"[ERROR] Failed to get user sessions: {str(e)}")
            return []
    
    def update_session_activity(self, session_token):
        """
        Update last activity time for a session
        """
        try:
            result = self.sessions_collection.update_one(
                {'session_token': session_token},
                {'$set': {'last_activity': datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"[ERROR] Failed to update session activity: {str(e)}")
            return False
    
    def deactivate_session(self, session_token):
        """
        Deactivate a session (logout)
        """
        try:
            result = self.sessions_collection.update_one(
                {'session_token': session_token},
                {
                    '$set': {
                        'is_active': False,
                        'logout_time': datetime.utcnow()
                    }
                }
            )
            logger.info(f"[SUCCESS] Session deactivated: {session_token[:20]}...")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"[ERROR] Failed to deactivate session: {str(e)}")
            return False
    
    def deactivate_user_sessions(self, user_email):
        """
        Deactivate all sessions for a user
        """
        try:
            result = self.sessions_collection.update_many(
                {'user_email': user_email, 'is_active': True},
                {
                    '$set': {
                        'is_active': False,
                        'logout_time': datetime.utcnow()
                    }
                }
            )
            logger.info(f"[SUCCESS] Deactivated {result.modified_count} sessions for {user_email}")
            return result.modified_count
        except Exception as e:
            logger.error(f"[ERROR] Failed to deactivate user sessions: {str(e)}")
            return 0
    
    def delete_session(self, session_token):
        """
        Delete a session permanently
        """
        try:
            result = self.sessions_collection.delete_one({'session_token': session_token})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"[ERROR] Failed to delete session: {str(e)}")
            return False
    
    def cleanup_old_sessions(self, days=30):
        """
        Delete inactive sessions older than specified days
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = self.sessions_collection.delete_many({
                'is_active': False,
                'logout_time': {'$lt': cutoff_date}
            })
            
            logger.info(f"[CLEANUP] Cleaned up {result.deleted_count} old sessions")
            return result.deleted_count
        except Exception as e:
            logger.error(f"[ERROR] Failed to cleanup old sessions: {str(e)}")
            return 0


# Singleton instance
_mongo_session_manager = None

def get_session_manager():
    """
    Get or create the MongoDB session manager singleton
    """
    global _mongo_session_manager
    if _mongo_session_manager is None:
        _mongo_session_manager = MongoDBSessionManager()
    return _mongo_session_manager
