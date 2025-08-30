# teacher_app/mongo_collections.py
from .mongo import db

# MongoDB Collections - only create if db is available
if db is not None:
    students = db['students']
    lessons = db['lessons']
    quizzes = db['quizzes']
    progress = db['progress']
    analytics = db['analytics']
    conversations = db['conversations']
    messages = db['messages']
    print("MongoDB collections initialized successfully")
else:
    # Create dummy collections when MongoDB is not available
    students = None
    lessons = None
    quizzes = None
    progress = None
    analytics = None
    conversations = None
    messages = None
    print("MongoDB collections not available - using None placeholders")
