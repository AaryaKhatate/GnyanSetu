# teacher_app/mongo_collections.py
from .mongo import db

# MongoDB Collections
students = db['students']
lessons = db['lessons']
quizzes = db['quizzes']
progress = db['progress']
analytics = db['analytics']
