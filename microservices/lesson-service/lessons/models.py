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
        if pdf_data_collection is not None:
            pdf_count = pdf_data_collection.count_documents({})
            stats["collections"]["pdf_data"] = pdf_count
            stats["total_documents"] += pdf_count
        
        if lessons_collection is not None:
            lessons_count = lessons_collection.count_documents({})
            stats["collections"]["lessons"] = lessons_count
            stats["total_documents"] += lessons_count
        
        if user_histories_collection is not None:
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
        
        try:
            if pdf_data_collection is not None:
                result = pdf_data_collection.insert_one(document)
                return str(result.inserted_id)
            else:
                logger.warning("MongoDB unavailable, returning mock PDF ID")
                return str(document['_id'])
        except Exception as e:
            logger.error(f"Error creating PDF data: {e}")
            return str(document['_id'])  # Return mock ID as fallback
    
    @staticmethod
    def get_by_id(pdf_id):
        """Get PDF data by ID"""
        try:
            if pdf_data_collection is not None:
                return pdf_data_collection.find_one({'_id': ObjectId(pdf_id)})
            else:
                logger.warning("MongoDB unavailable, returning None")
                return None
        except Exception as e:
            logger.error(f"Error getting PDF data: {e}")
            return None
    
    @staticmethod
    def get_by_user(user_id):
        """Get all PDF data for a user"""
        try:
            if pdf_data_collection is not None:
                return list(pdf_data_collection.find({'user_id': user_id}))
            else:
                logger.warning("MongoDB unavailable, returning empty list")
                return []
        except Exception as e:
            logger.error(f"Error getting user PDF data: {e}")
            return []


class LessonModel:
    """Model for storing AI-generated lessons"""
    
    @staticmethod
    def create(user_id, pdf_id, lesson_title, lesson_content, lesson_type='interactive', metadata=None, quiz_data=None, notes_data=None, pdf_images=None):
        """Create a new lesson with quiz and notes data"""
        document = {
            '_id': ObjectId(),
            'user_id': user_id,
            'pdf_id': ObjectId(pdf_id) if pdf_id else ObjectId(),
            'lesson_title': lesson_title,
            'lesson_content': lesson_content,
            'lesson_type': lesson_type,  # interactive, quiz, summary, detailed
            'quiz_data': quiz_data or {},  # Structured quiz data
            'notes_data': notes_data or {},  # Structured notes data
            'pdf_images': pdf_images or [],  # PDF images for Visualization Service
            'metadata': metadata or {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'status': 'generated'
        }
        
        try:
            if lessons_collection is not None:
                result = lessons_collection.insert_one(document)
                print(f"� Lesson saved to MongoDB with ID: {result.inserted_id}")
                print(f"   - Quiz data included: {bool(quiz_data)}")
                print(f"   - Notes data included: {bool(notes_data)}")
                print(f"   - PDF images included: {len(pdf_images) if pdf_images else 0}")
                return str(result.inserted_id)
            else:
                logger.warning("MongoDB unavailable, returning mock lesson ID")
                return str(document['_id'])
        except Exception as e:
            logger.error(f"Error creating lesson: {e}")
            print(f" Error saving lesson to MongoDB: {e}")
            return str(document['_id'])  # Return mock ID as fallback
    
    @staticmethod
    def get_by_id(lesson_id):
        """Get lesson by ID"""
        try:
            if lessons_collection is not None:
                return lessons_collection.find_one({'_id': ObjectId(lesson_id)})
            else:
                logger.warning("MongoDB unavailable, returning None")
                return None
        except Exception as e:
            logger.error(f"Error getting lesson: {e}")
            return None
    
    @staticmethod
    def get_by_user(user_id):
        """Get all lessons for a user"""
        try:
            if lessons_collection is not None:
                return list(lessons_collection.find({'user_id': user_id}).sort('created_at', -1))
            else:
                logger.warning("MongoDB unavailable, returning empty list")
                return []
        except Exception as e:
            logger.error(f"Error getting user lessons: {e}")
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
        
        if user_histories_collection is not None:
            result = user_histories_collection.insert_one(document)
            return str(result.inserted_id)
        return None
