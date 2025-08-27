# teacher_app/mongo.py
import motor.motor_asyncio
from django.conf import settings
from datetime import datetime

# MongoDB connection
client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_DB_URI)
db = client[settings.MONGO_DB_NAME]

# ---------------- Document Structures ----------------
def create_student(name, email, password_hash):
    return {
        "name": name,
        "email": email,
        "password_hash": password_hash,
        "created_at": datetime.utcnow()
    }

def create_lesson(student_id, pdf_data, llm_output, topic):
    return {
        "student_id": student_id,
        "pdf_data": pdf_data,          
        "llm_output": llm_output,      
        "topic": topic,
        "created_at": datetime.utcnow()
    }

def create_quiz(student_id, lesson_id, questions, score, time_taken):
    return {
        "student_id": student_id,
        "lesson_id": lesson_id,
        "questions": questions,       # [{"question":..., "options":[..], "answer":"A"}]
        "score": score,
        "time_taken": time_taken,     # e.g. seconds or "5m 30s"
        "attempted_at": datetime.utcnow()
    }

def create_progress(student_id, lesson_id, completed_steps, total_steps, score):
    return {
        "student_id": student_id,
        "lesson_id": lesson_id,
        "completed_steps": completed_steps,
        "total_steps": total_steps,
        "score": score,
        "updated_at": datetime.utcnow()
    }

def create_analytics(lesson_id, average_score, completion_rate, attempts):
    return {
        "lesson_id": lesson_id,
        "average_score": average_score,
        "completion_rate": completion_rate,
        "attempts": attempts,
        "calculated_at": datetime.utcnow()
    }
