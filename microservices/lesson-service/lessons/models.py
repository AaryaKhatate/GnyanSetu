# MongoDB Models for Lesson Service
# Using PyMongo for direct MongoDB operations

from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def check_database_connection():
    """Check if database connection is working"""
    try:
        if client is None:
            return False, "MongoDB client not initialized"
        
        # Test the connection
        client.admin.command('ismaster')
        return True, "Connected to MongoDB successfully"
    except Exception as e:
        return False, f"MongoDB connection failed: {str(e)}"
    
def get_connection_info():
    """Get detailed connection information"""
    try:
        if client is None:
            return {"status": "disconnected", "error": "Client not initialized"}
        
        server_info = client.server_info()
        return {
            "status": "connected",
            "version": server_info.get("version"),
            "database": db.name if db else "unknown"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def get_database_stats():
    """Get database statistics for monitoring"""
    try:
        if client is None or db is None:
            return {
                "status": "disconnected",
                "collections": 0,
                "documents": 0
            }
        
        stats = {
            "status": "connected",
            "database_name": db.name,
            "collections": {},
            "total_documents": 0
        }
        
        # Get stats for each collection
        if pdf_data_collection:
            pdf_count = pdf_data_collection.count_documents({})
            stats["collections"]["pdf_data"] = pdf_count
            stats["total_documents"] += pdf_count
        
        if lessons_collection:
            lessons_count = lessons_collection.count_documents({})
            stats["collections"]["lessons"] = lessons_count
            stats["total_documents"] += lessons_count
        
        if user_histories_collection:
            history_count = user_histories_collection.count_documents({})
            stats["collections"]["user_histories"] = history_count
            stats["total_documents"] += history_count
        
        return stats
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "collections": 0,
            "documents": 0
        }

# MongoDB Connection
try:
    mongodb_settings = settings.MONGODB_SETTINGS
    client = MongoClient(
        host=mongodb_settings['host'],
        port=mongodb_settings['port']
    )
    db = client[mongodb_settings['db']]
    
    # Collections
    pdf_data_collection = db.pdf_data
    lessons_collection = db.lessons
    user_histories_collection = db.user_histories
    
    logger.info(f"Connected to MongoDB: {mongodb_settings['db']}")
    
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    client = None
    db = None
    pdf_data_collection = None
    lessons_collection = None
    user_histories_collection = None


class PDFDataModel:
    """Model for storing PDF data with images and OCR text"""
    
    @staticmethod
    def create(user_id, filename, text_content, images_data=None, metadata=None):
        """Create a new PDF data entry"""
        document = {
            '_id': ObjectId(),
            'user_id': user_id,
            'filename': filename,
            'text_content': text_content,
            'images_data': images_data or [],
            'metadata': metadata or {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'status': 'processed'
        }
        
        if pdf_data_collection:
            result = pdf_data_collection.insert_one(document)
            return str(result.inserted_id)
        return None
    
    @staticmethod
    def get_by_id(pdf_id):
        """Get PDF data by ID"""
        if pdf_data_collection:
            return pdf_data_collection.find_one({'_id': ObjectId(pdf_id)})
        return None
    
    @staticmethod
    def get_by_user(user_id):
        """Get all PDF data for a user"""
        if pdf_data_collection:
            return list(pdf_data_collection.find({'user_id': user_id}))
        return []


class LessonModel:
    """Model for storing AI-generated lessons"""
    
    @staticmethod
    def create(user_id, pdf_id, lesson_title, lesson_content, lesson_type='interactive', metadata=None):
        """Create a new lesson"""
        document = {
            '_id': ObjectId(),
            'user_id': user_id,
            'pdf_id': ObjectId(pdf_id),
            'lesson_title': lesson_title,
            'lesson_content': lesson_content,
            'lesson_type': lesson_type,  # interactive, quiz, summary, detailed
            'metadata': metadata or {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'status': 'generated'
        }
        
        if lessons_collection:
            result = lessons_collection.insert_one(document)
            return str(result.inserted_id)
        return None
    
    @staticmethod
    def get_by_user(user_id):
        """Get all lessons for a user"""
        if lessons_collection:
            return list(lessons_collection.find({'user_id': user_id}).sort('created_at', -1))
        return []


class UserHistoryModel:
    """Model for tracking user lesson generation history"""
    
    @staticmethod
    def create_entry(user_id, pdf_id, lesson_id, action='lesson_generated'):
        """Create a history entry"""
        document = {
            '_id': ObjectId(),
            'user_id': user_id,
            'pdf_id': ObjectId(pdf_id),
            'lesson_id': ObjectId(lesson_id),
            'action': action,
            'timestamp': datetime.utcnow()
        }
        
        if user_histories_collection:
            result = user_histories_collection.insert_one(document)
            return str(result.inserted_id)
        return None
