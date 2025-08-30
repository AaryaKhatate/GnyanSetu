# teacher_app/mongo.py
import motor.motor_asyncio
from django.conf import settings
from datetime import datetime

# MongoDB connection with error handling
try:
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_DB_URI)
    db = client[settings.MONGO_DB_NAME]
    print(f"MongoDB connected to: {settings.MONGO_DB_NAME}")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    print("Chat history features will be disabled.")
    db = None
    client = None

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

def create_conversation(user_id, title, topic=None, pdf_text=None, pdf_filename=None):
    return {
        "user_id": user_id,
        "title": title,
        "topic": topic,
        "pdf_text": pdf_text,
        "pdf_filename": pdf_filename,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True
    }

def create_message(conversation_id, sender, content, message_type="text", step_data=None):
    message = {
        "conversation_id": conversation_id,
        "sender": sender,  # "user" or "ai"
        "content": content,
        "message_type": message_type,  # "text", "lesson_step", "quiz", "notes"
        "timestamp": datetime.utcnow()
    }
    if step_data:
        message["step_data"] = step_data
    return message

def create_conversation(user_id, title, topic=None, pdf_filename=None):
    return {
        "user_id": user_id,
        "title": title,
        "topic": topic,
        "pdf_filename": pdf_filename,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True
    }

def create_message(conversation_id, sender, content, message_type="text", step_data=None):
    return {
        "conversation_id": conversation_id,
        "sender": sender,  # "user" or "ai"
        "content": content,
        "message_type": message_type,  # "text", "lesson_step", "quiz", "notes"
        "step_data": step_data,  # For storing lesson step JSON data
        "timestamp": datetime.utcnow()
    }
