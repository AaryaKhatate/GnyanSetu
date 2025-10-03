# teacher_app/views.py

import logging
import json
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
import fitz  # PyMuPDF
import asyncio
from .mongo_collections import students, lessons, quizzes, progress, analytics, conversations, messages, conversations, messages
from .mongo import create_student, create_lesson, create_quiz, create_progress
from bson import ObjectId
import asyncio

# It's good practice to get a logger instance.
logger = logging.getLogger(__name__)

def teacher_view(request: HttpRequest):
    """Renders the main teacher page."""
    return render(request, "teacher_app/teacher.html")

def landing_page(request: HttpRequest):
    """Serves the landing page."""
    # For now, we'll serve a simple HTML that will load the React app
    # In production, you'd serve the built React files
    return render(request, "teacher_app/landing.html")

@csrf_exempt
@require_POST
def upload_pdf(request: HttpRequest):
    """Handles PDF file uploads, extracts text, and returns it as JSON."""
    print(f"Upload PDF request received: {request.method}")
    print(f"Request headers: {dict(request.headers)}")
    print(f"Request FILES: {list(request.FILES.keys())}")
    print(f"Request META: {request.META.get('HTTP_ORIGIN', 'No origin')}")
    
    if not request.FILES.get('pdf_file'):
        print("No pdf_file in request.FILES")
        return JsonResponse({'error': 'No PDF file found in the request.'}, status=400)

    pdf_file = request.FILES['pdf_file']
    print(f"PDF file received: {pdf_file.name}, size: {pdf_file.size}")
    
    # Validate that it's a PDF file
    if not pdf_file.name.lower().endswith('.pdf'):
        return JsonResponse({'error': 'Invalid file type. Please upload a PDF.'}, status=400)
    
    try:
        # Open the PDF from the in-memory file
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text_content = ""
        for page in doc:
            text_content += page.get_text()
        
        if not text_content.strip():
             return JsonResponse({'error': 'Could not extract any text from the PDF.'}, status=400)

        # Return only the text, as that's what the consumer needs
        response = JsonResponse({'text': text_content, 'filename': pdf_file.name})
        response["Access-Control-Allow-Origin"] = "http://localhost:3001"
        response["Access-Control-Allow-Credentials"] = "true"
        return response
    
    except Exception as e:
        logger.error(f"Error processing PDF '{pdf_file.name}': {e}")
        return JsonResponse({'error': f'An unexpected error occurred while processing the PDF: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_students(request: HttpRequest):
    """Handle student CRUD operations."""
    if request.method == 'GET':
        # List all students (async operation)
        async def get_students():
            try:
                students_list = []
                async for student in students.find():
                    student['_id'] = str(student['_id'])
                    students_list.append(student)
                return students_list
            except Exception as e:
                logger.error(f"Error fetching students: {e}")
                return []
        
        try:
            students_data = asyncio.run(get_students())
            return JsonResponse({'students': students_data})
        except Exception as e:
            logger.error(f"Error getting students: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    elif request.method == 'POST':
        # Create a new student
        try:
            data = json.loads(request.body)
            name = data.get('name')
            email = data.get('email')
            password_hash = data.get('password_hash', '')
            
            if not name or not email:
                return JsonResponse({'error': 'Name and email are required'}, status=400)
            
            async def create_student_async():
                student_doc = create_student(name, email, password_hash)
                result = await students.insert_one(student_doc)
                student_doc['_id'] = str(result.inserted_id)
                return student_doc
            
            new_student = asyncio.run(create_student_async())
            return JsonResponse({'student': new_student}, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error creating student: {e}")
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_lessons(request: HttpRequest):
    """Handle lesson CRUD operations."""
    if request.method == 'GET':
        # List all lessons
        async def get_lessons():
            try:
                lessons_list = []
                async for lesson in lessons.find():
                    lesson['_id'] = str(lesson['_id'])
                    lessons_list.append(lesson)
                return lessons_list
            except Exception as e:
                logger.error(f"Error fetching lessons: {e}")
                return []
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            lessons_data = loop.run_until_complete(get_lessons())
            return JsonResponse({'lessons': lessons_data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        finally:
            loop.close()
    
    elif request.method == 'POST':
        # Create a new lesson
        try:
            data = json.loads(request.body)
            student_id = data.get('student_id')
            pdf_data = data.get('pdf_data', {})
            llm_output = data.get('llm_output', {})
            topic = data.get('topic', '')
            
            async def create_lesson_async():
                lesson_doc = create_lesson(student_id, pdf_data, llm_output, topic)
                result = await lessons.insert_one(lesson_doc)
                lesson_doc['_id'] = str(result.inserted_id)
                return lesson_doc
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            new_lesson = loop.run_until_complete(create_lesson_async())
            return JsonResponse({'lesson': new_lesson}, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error creating lesson: {e}")
            return JsonResponse({'error': str(e)}, status=500)
        finally:
            loop.close()

@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_quizzes(request: HttpRequest):
    """Handle quiz CRUD operations."""
    if request.method == 'GET':
        # List all quizzes
        async def get_quizzes():
            try:
                quizzes_list = []
                async for quiz in quizzes.find():
                    quiz['_id'] = str(quiz['_id'])
                    quizzes_list.append(quiz)
                return quizzes_list
            except Exception as e:
                logger.error(f"Error fetching quizzes: {e}")
                return []
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            quizzes_data = loop.run_until_complete(get_quizzes())
            return JsonResponse({'quizzes': quizzes_data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        finally:
            loop.close()
    
    elif request.method == 'POST':
        # Create a new quiz submission
        try:
            data = json.loads(request.body)
            student_id = data.get('student_id')
            lesson_id = data.get('lesson_id')
            questions_data = data.get('questions', [])
            score = data.get('score', 0)
            time_taken = data.get('time_taken', '')
            
            async def create_quiz_async():
                quiz_doc = create_quiz(student_id, lesson_id, questions_data, score, time_taken)
                result = await quizzes.insert_one(quiz_doc)
                quiz_doc['_id'] = str(result.inserted_id)
                return quiz_doc
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            new_quiz = loop.run_until_complete(create_quiz_async())
            return JsonResponse({'quiz': new_quiz}, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error creating quiz: {e}")
            return JsonResponse({'error': str(e)}, status=500)
        finally:
            loop.close()

@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_progress(request: HttpRequest):
    """Handle progress tracking."""
    if request.method == 'GET':
        # Get progress for a specific student and lesson
        student_id = request.GET.get('student_id')
        lesson_id = request.GET.get('lesson_id')
        
        async def get_progress():
            try:
                query = {}
                if student_id:
                    query['student_id'] = student_id
                if lesson_id:
                    query['lesson_id'] = lesson_id
                
                progress_list = []
                async for prog in progress.find(query):
                    prog['_id'] = str(prog['_id'])
                    progress_list.append(prog)
                return progress_list
            except Exception as e:
                logger.error(f"Error fetching progress: {e}")
                return []
        
        try:
            # Use asyncio.run() instead of manual event loop management
            progress_data = asyncio.run(get_progress())
            return JsonResponse({'progress': progress_data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    elif request.method == 'POST':
        # Update progress
        try:
            data = json.loads(request.body)
            student_id = data.get('student_id')
            lesson_id = data.get('lesson_id')
            completed_steps = data.get('completed_steps', 0)
            total_steps = data.get('total_steps', 0)
            score = data.get('score', 0)
            
            async def update_progress_async():
                progress_doc = create_progress(student_id, lesson_id, completed_steps, total_steps, score)
                
                # Upsert progress (update if exists, insert if not)
                filter_query = {'student_id': student_id, 'lesson_id': lesson_id}
                result = await progress.replace_one(filter_query, progress_doc, upsert=True)
                
                if result.upserted_id:
                    progress_doc['_id'] = str(result.upserted_id)
                else:
                    # Find the existing document to get its ID
                    existing = await progress.find_one(filter_query)
                    progress_doc['_id'] = str(existing['_id'])
                
                return progress_doc
            
            # Use asyncio.run() instead of manual event loop management
            updated_progress = asyncio.run(update_progress_async())
            return JsonResponse({'progress': updated_progress})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
            return JsonResponse({'error': str(e)}, status=500)

# Authentication Views
@csrf_exempt
@require_POST
def api_login(request: HttpRequest):
    """Handle user login."""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return JsonResponse({'error': 'Email and password are required'}, status=400)
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            return JsonResponse({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            })
        else:
            return JsonResponse({'error': 'Invalid email or password'}, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return JsonResponse({'error': 'An error occurred during login'}, status=500)

@csrf_exempt
@require_POST
def api_signup(request: HttpRequest):
    """Handle user registration."""
    try:
        data = json.loads(request.body)
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        if not all([name, email, password, confirm_password]):
            return JsonResponse({'error': 'All fields are required'}, status=400)
        
        if password != confirm_password:
            return JsonResponse({'error': 'Passwords do not match'}, status=400)
        
        if len(password) < 8:
            return JsonResponse({'error': 'Password must be at least 8 characters long'}, status=400)
        
        # Check if user already exists
        if User.objects.filter(username=email).exists():
            return JsonResponse({'error': 'User with this email already exists'}, status=400)
        
        # Create new user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name.split(' ')[0] if ' ' in name else name,
            last_name=' '.join(name.split(' ')[1:]) if ' ' in name else ''
        )
        
        # Automatically log in the user after registration
        login(request, user)
        
        return JsonResponse({
            'success': True,
            'message': 'Registration successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        return JsonResponse({'error': 'An error occurred during registration'}, status=500)

@csrf_exempt
@require_POST
def api_logout(request: HttpRequest):
    """Handle user logout."""
    try:
        logout(request)
        return JsonResponse({'success': True, 'message': 'Logout successful'})
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return JsonResponse({'error': 'An error occurred during logout'}, status=500)

@csrf_exempt
@require_POST
def api_forgot_password(request: HttpRequest):
    """Handle forgot password request."""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
            # In a real application, you would send an email with a reset link
            # For now, we'll just return a success message
            return JsonResponse({
                'success': True,
                'message': 'If an account with this email exists, you will receive a password reset link.'
            })
        except User.DoesNotExist:
            # Don't reveal whether the email exists or not for security
            return JsonResponse({
                'success': True,
                'message': 'If an account with this email exists, you will receive a password reset link.'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error during forgot password: {e}")
        return JsonResponse({'error': 'An error occurred'}, status=500)

@login_required
def api_user_profile(request: HttpRequest):
    """Get current user profile."""
    try:
        user = request.user
        return JsonResponse({
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_authenticated': True
            }
        })
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return JsonResponse({'error': 'An error occurred'}, status=500)

# Chat History Endpoints
@csrf_exempt
@require_http_methods(["GET"])
def api_conversations(request: HttpRequest):
    """Get user's conversation history."""
    try:
        user_id = request.GET.get('user_id', 'anonymous')
        
        async def get_conversations():
            try:
                conversations_list = []
                async for conversation in conversations.find({"user_id": user_id, "is_active": True}).sort("updated_at", -1):
                    conversation['_id'] = str(conversation['_id'])
                    # Format for frontend sidebar
                    conversation['id'] = conversation['_id']
                    conversation['timestamp'] = conversation['updated_at'].strftime("%I:%M %p") if conversation.get('updated_at') else ""
                    conversations_list.append(conversation)
                return conversations_list
            except Exception as e:
                logger.error(f"Error fetching conversations: {e}")
                return []
        
        # Use asyncio.run() instead of manual event loop management
        try:
            conversations_data = asyncio.run(get_conversations())
            return JsonResponse({'conversations': conversations_data})
        except Exception as e:
            logger.error(f"Error in get_conversations: {e}")
            return JsonResponse({'error': str(e)}, status=500)
            
    except Exception as e:
        logger.error(f"Error in api_conversations: {e}")
        return JsonResponse({'error': 'An error occurred'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_conversation_messages(request: HttpRequest, conversation_id: str):
    """Get messages for a specific conversation."""
    try:
        async def get_messages():
            try:
                messages_list = []
                async for message in messages.find({"conversation_id": ObjectId(conversation_id)}).sort("timestamp", 1):
                    message['_id'] = str(message['_id'])
                    message['conversation_id'] = str(message['conversation_id'])
                    messages_list.append(message)
                return messages_list
            except Exception as e:
                logger.error(f"Error fetching messages: {e}")
                return []
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            messages_data = loop.run_until_complete(get_messages())
            return JsonResponse({'messages': messages_data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

            
    except Exception as e:
        logger.error(f"Error in api_conversation_messages: {e}")
        return JsonResponse({'error': 'An error occurred'}, status=500)

@csrf_exempt
@require_POST
def api_delete_conversation(request: HttpRequest, conversation_id: str):
    """Delete a conversation (soft delete)."""
    try:
        async def delete_conversation():
            result = await conversations.update_one(
                {"_id": ObjectId(conversation_id)},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(delete_conversation())
            if success:
                return JsonResponse({'success': True, 'message': 'Conversation deleted'})
            else:
                return JsonResponse({'error': 'Conversation not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

            
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        return JsonResponse({'error': 'An error occurred'}, status=500)

@csrf_exempt
@require_POST  
def api_rename_conversation(request: HttpRequest, conversation_id: str):
    """Rename a conversation."""
    try:
        data = json.loads(request.body)
        new_title = data.get('title', '').strip()
        
        if not new_title:
            return JsonResponse({'error': 'Title is required'}, status=400)
        
        async def rename_conversation():
            result = await conversations.update_one(
                {"_id": ObjectId(conversation_id)},
                {"$set": {"title": new_title, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(rename_conversation())
            if success:
                return JsonResponse({'success': True, 'message': 'Conversation renamed', 'title': new_title})
            else:
                return JsonResponse({'error': 'Conversation not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error renaming conversation: {e}")
        return JsonResponse({'error': 'An error occurred'}, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_conversations(request: HttpRequest):
    """Handle conversation CRUD operations."""
    if request.method == 'GET':
        # List user's conversations
        user_id = request.GET.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'User ID is required'}, status=400)
            
        async def get_conversations():
            try:
                conversations_list = []
                async for conversation in conversations.find({"user_id": user_id}).sort("updated_at", -1):
                    conversation['_id'] = str(conversation['_id'])
                    conversations_list.append(conversation)
                return conversations_list
            except Exception as e:
                logger.error(f"Error fetching conversations: {e}")
                return []
        
        try:
            # Use asyncio.run() instead of manual event loop management
            conversations_data = asyncio.run(get_conversations())
            return JsonResponse({'conversations': conversations_data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    elif request.method == 'POST':
        # Create a new conversation (usually handled by WebSocket, but backup endpoint)
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            title = data.get('title', 'New Conversation')
            topic = data.get('topic')
            
            async def create_conversation_async():
                from .mongo import create_conversation
                conversation_doc = create_conversation(user_id, title, topic)
                result = await conversations.insert_one(conversation_doc)
                conversation_doc['_id'] = str(result.inserted_id)
                return conversation_doc
            
            # Use asyncio.run() instead of manual event loop management
            new_conversation = asyncio.run(create_conversation_async())
            return JsonResponse({'conversation': new_conversation}, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_conversation_messages(request: HttpRequest, conversation_id: str):
    """Get messages for a specific conversation."""
    try:
        async def get_messages():
            try:
                messages_list = []
                async for message in messages.find({"conversation_id": ObjectId(conversation_id)}).sort("timestamp", 1):
                    message['_id'] = str(message['_id'])
                    message['conversation_id'] = str(message['conversation_id'])
                    messages_list.append(message)
                return messages_list
            except Exception as e:
                logger.error(f"Error fetching messages: {e}")
                return []
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        messages_data = loop.run_until_complete(get_messages())
        return JsonResponse({'messages': messages_data})
        
    except Exception as e:
        logger.error(f"Error getting conversation messages: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_conversation_delete(request: HttpRequest, conversation_id: str):
    """Delete a conversation and all its messages."""
    try:
        async def delete_conversation_async():
            # Delete all messages in the conversation
            await messages.delete_many({"conversation_id": ObjectId(conversation_id)})
            # Delete the conversation
            result = await conversations.delete_one({"_id": ObjectId(conversation_id)})
            return result.deleted_count > 0
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        deleted = loop.run_until_complete(delete_conversation_async())
        
        if deleted:
            return JsonResponse({'success': True, 'message': 'Conversation deleted successfully'})
        else:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
            
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        return JsonResponse({'error': str(e)}, status=500)
