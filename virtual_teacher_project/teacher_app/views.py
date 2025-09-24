# teacher_app/views.py - FIXED VERSION

import logging
import json
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
import fitz  # PyMuPDF
import asyncio
from .mongo_collections import students, lessons, quizzes, progress, analytics, conversations, messages
from .mongo import create_student, create_lesson, create_quiz, create_progress
from bson import ObjectId

logger = logging.getLogger(__name__)
User = get_user_model()

def teacher_view(request: HttpRequest):
    """Renders the main teacher page."""
    return render(request, "teacher_app/teacher.html")

def landing_page(request: HttpRequest):
    """Serves the landing page."""
    return render(request, "teacher_app/landing.html")

@csrf_exempt
@require_POST
def upload_pdf(request: HttpRequest):
    """Handles PDF file uploads, extracts text, and returns it as JSON."""
    try:
        logger.info(f"PDF upload request received from {request.META.get('HTTP_ORIGIN', 'unknown')}")
        
        if not request.FILES.get('pdf_file'):
            logger.warning("No PDF file found in request")
            return JsonResponse({'error': 'No PDF file found in the request.'}, status=400)

        pdf_file = request.FILES['pdf_file']
        logger.info(f"Processing PDF: {pdf_file.name} ({pdf_file.size} bytes)")
        
        # Validate file type
        if not pdf_file.name.lower().endswith('.pdf'):
            return JsonResponse({'error': 'Invalid file type. Please upload a PDF.'}, status=400)
        
        # Validate file size (limit to 50MB)
        if pdf_file.size > 50 * 1024 * 1024:
            return JsonResponse({'error': 'File too large. Please upload a PDF smaller than 50MB.'}, status=400)
        
        # Extract text from PDF
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text_content = ""
        page_count = len(doc)
        
        for page_num, page in enumerate(doc):
            try:
                page_text = page.get_text()
                text_content += page_text + "\n\n"
                
                # Log progress for large PDFs
                if page_count > 10 and (page_num + 1) % 10 == 0:
                    logger.info(f"Processed {page_num + 1}/{page_count} pages")
                    
            except Exception as page_error:
                logger.warning(f"Error extracting text from page {page_num + 1}: {page_error}")
                continue
        
        doc.close()
        
        # Validate extracted content
        if not text_content.strip():
            return JsonResponse({
                'error': 'Could not extract any text from the PDF. The file may be image-based or corrupted.'
            }, status=400)

        # Log extraction results
        word_count = len(text_content.split())
        logger.info(f"Successfully extracted {word_count} words from {page_count} pages")

        # Prepare response with CORS headers
        response_data = {
            'text': text_content.strip(),
            'filename': pdf_file.name,
            'page_count': page_count,
            'word_count': word_count
        }
        
        response = JsonResponse(response_data)
        response["Access-Control-Allow-Origin"] = "http://localhost:3001"
        response["Access-Control-Allow-Credentials"] = "true"
        return response
    
    except Exception as e:
        logger.error(f"Error processing PDF '{pdf_file.name if 'pdf_file' in locals() else 'unknown'}': {str(e)}")
        return JsonResponse({
            'error': f'An unexpected error occurred while processing the PDF: {str(e)}'
        }, status=500)

# Safe async wrapper function
# Safe async wrapper function
def run_async_safely(coro):
    """Safely run async coroutine in sync context with proper event loop handling."""
    try:
        # Create a new event loop for this operation
        import asyncio
        import threading
        import concurrent.futures
        
        def run_in_new_loop():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro)
            except Exception as e:
                logger.error(f"Error in new event loop: {e}")
                return None
            finally:
                try:
                    new_loop.close()
                except Exception:
                    pass
        
        # Run in a separate thread to avoid loop conflicts
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_new_loop)
            return future.result(timeout=30)
            
    except concurrent.futures.TimeoutError:
        logger.error("Async operation timed out after 30 seconds")
        return None
    except Exception as e:
        logger.error(f"Error in run_async_safely: {e}")
        return None

@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_students(request: HttpRequest):
    """Handle student CRUD operations with improved error handling."""
    if request.method == 'GET':
        async def get_students():
            if students is None:
                return []
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
            students_data = run_async_safely(get_students())
            return JsonResponse({'students': students_data})
        except Exception as e:
            logger.error(f"Error in api_students GET: {e}")
            return JsonResponse({'error': 'Failed to fetch students'}, status=500)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            email = data.get('email', '').strip()
            password_hash = data.get('password_hash', '')
            
            if not name or not email:
                return JsonResponse({'error': 'Name and email are required'}, status=400)
            
            async def create_student_async():
                if students is None:
                    raise Exception("Database not available")
                    
                student_doc = create_student(name, email, password_hash)
                result = await students.insert_one(student_doc)
                student_doc['_id'] = str(result.inserted_id)
                return student_doc
            
            new_student = run_async_safely(create_student_async())
            return JsonResponse({'student': new_student}, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            logger.error(f"Error creating student: {e}")
            return JsonResponse({'error': 'Failed to create student'}, status=500)

@csrf_exempt  
@require_http_methods(["GET"])
def api_conversations(request: HttpRequest):
    """Get user's conversation history with improved filtering."""
    try:
        user_id = request.GET.get('user_id', 'anonymous')
        
        if not user_id:
            return JsonResponse({'error': 'User ID is required'}, status=400)
        
        # Use synchronous approach to avoid event loop issues
        if conversations is None:
            return JsonResponse({'conversations': []})
        
        # Use sync MongoDB operations
        from pymongo import MongoClient
        from django.conf import settings
        
        try:
            # Get sync client - adjust connection string based on your settings
            client = MongoClient('mongodb://localhost:27017/')  # Replace with your MongoDB connection
            db = client.Gnyansetu
            conversations_sync = db.conversations
            
            conversations_list = []
            query = {'user_id': user_id, 'is_active': {'$ne': False}}
            
            for conversation in conversations_sync.find(query).sort('updated_at', -1).limit(50):
                conversation['_id'] = str(conversation['_id'])
                conversation['conversation_id'] = conversation['_id']  # Frontend compatibility
                
                # Format timestamp for display
                if conversation.get('updated_at'):
                    conversation['timestamp'] = conversation['updated_at'].strftime("%I:%M %p")
                else:
                    conversation['timestamp'] = ""
                
                # Ensure required fields exist
                conversation.setdefault('title', 'Untitled Lesson')
                conversation.setdefault('topic', '')
                
                conversations_list.append(conversation)
            
            client.close()  # Close connection
            return JsonResponse({'conversations': conversations_list})
            
        except Exception as db_error:
            logger.error(f"Database connection error: {db_error}")
            return JsonResponse({'conversations': []})
        
    except Exception as e:
        logger.error(f"Error in api_conversations: {e}")
        return JsonResponse({'conversations': []})

@csrf_exempt
@require_http_methods(["GET"])
def api_conversation_messages(request: HttpRequest, conversation_id: str):
    """Get messages for a specific conversation with validation."""
    try:
        # Validate conversation ID format
        if not conversation_id or len(conversation_id) != 24:
            return JsonResponse({'error': 'Invalid conversation ID'}, status=400)
        
        async def get_messages():
            if messages is None:
                return []
            try:
                messages_list = []
                query = {"conversation_id": ObjectId(conversation_id)}
                
                async for message in messages.find(query).sort("timestamp", 1):
                    message['_id'] = str(message['_id'])
                    message['conversation_id'] = str(message['conversation_id'])
                    
                    # Ensure required fields
                    message.setdefault('sender', 'unknown')
                    message.setdefault('content', '')
                    message.setdefault('message_type', 'text')
                    
                    # Format timestamp
                    if message.get('timestamp'):
                        message['formatted_time'] = message['timestamp'].strftime("%I:%M %p")
                    
                    messages_list.append(message)
                
                return messages_list
            except Exception as e:
                logger.error(f"Error fetching messages for conversation {conversation_id}: {e}")
                return []
        
        messages_data = run_async_safely(get_messages())
        return JsonResponse({'messages': messages_data})
        
    except Exception as e:
        logger.error(f"Error in api_conversation_messages: {e}")
        return JsonResponse({'error': 'Failed to fetch messages'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_delete_conversation(request: HttpRequest, conversation_id: str):
    """Delete a conversation using synchronous MongoDB operations."""
    try:
        # Validate conversation ID format
        if not conversation_id or len(conversation_id) != 24:
            return JsonResponse({'error': 'Invalid conversation ID'}, status=400)
        
        if conversations is None:
            return JsonResponse({'error': 'Database not available'}, status=500)
        
        # Use synchronous MongoDB operations
        from pymongo import MongoClient
        from bson import ObjectId
        
        try:
            # Get sync client
            client = MongoClient('mongodb://localhost:27017/')  # Replace with your MongoDB connection
            db = client.Gnyansetu
            conversations_sync = db.conversations
            messages_sync = db.messages
            
            # Validate ObjectId format
            try:
                obj_id = ObjectId(conversation_id)
            except:
                client.close()
                return JsonResponse({'error': 'Invalid conversation ID format'}, status=400)
            
            # Delete the conversation
            conversation_result = conversations_sync.delete_one({'_id': obj_id})
            
            # Delete associated messages
            messages_result = messages_sync.delete_many({'conversation_id': obj_id})
            
            client.close()
            
            if conversation_result.deleted_count > 0:
                logger.info(f"Deleted conversation {conversation_id} and {messages_result.deleted_count} messages")
                return JsonResponse({
                    'success': True,
                    'deleted_messages': messages_result.deleted_count
                })
            else:
                return JsonResponse({'error': 'Conversation not found'}, status=404)
                
        except Exception as db_error:
            logger.error(f"Database error deleting conversation: {db_error}")
            return JsonResponse({'error': 'Database operation failed'}, status=500)
        
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {e}")
        return JsonResponse({'error': 'Failed to delete conversation'}, status=500)

@csrf_exempt
@require_POST  
def api_rename_conversation(request: HttpRequest, conversation_id: str):
    """Rename a conversation with validation."""
    try:
        # Validate conversation ID
        if not conversation_id or len(conversation_id) != 24:
            return JsonResponse({'error': 'Invalid conversation ID'}, status=400)
        
        data = json.loads(request.body)
        new_title = data.get('title', '').strip()
        
        if not new_title:
            return JsonResponse({'error': 'Title is required and cannot be empty'}, status=400)
        
        if len(new_title) > 100:
            return JsonResponse({'error': 'Title too long (maximum 100 characters)'}, status=400)
        
        async def rename_conversation():
            if conversations is None:
                return False
            try:
                result = await conversations.update_one(
                    {"_id": ObjectId(conversation_id)},
                    {
                        "$set": {
                            "title": new_title,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                return result.modified_count > 0
            except Exception as e:
                logger.error(f"Error renaming conversation {conversation_id}: {e}")
                return False
        
        success = run_async_safely(rename_conversation())
        
        if success:
            return JsonResponse({
                'success': True, 
                'message': 'Conversation renamed successfully', 
                'title': new_title
            })
        else:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        logger.error(f"Error in api_rename_conversation: {e}")
        return JsonResponse({'error': 'Failed to rename conversation'}, status=500)

# Authentication Views with improved error handling
@csrf_exempt
@require_POST
def api_login(request: HttpRequest):
    """Handle user login with enhanced validation."""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return JsonResponse({'error': 'Email and password are required'}, status=400)
        
        # Basic email validation
        if '@' not in email or '.' not in email:
            return JsonResponse({'error': 'Please enter a valid email address'}, status=400)

        # Authenticate user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if not user.is_active:
                return JsonResponse({'error': 'Account is disabled'}, status=403)
                
            # Explicitly set backend to avoid multiple backends error
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            
            logger.info(f"User {email} logged in successfully")

            return JsonResponse({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': f"{user.first_name} {user.last_name}".strip()
                }
            })
        else:
            logger.warning(f"Failed login attempt for email: {email}")
            return JsonResponse({'error': 'Invalid email or password'}, status=401)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request format'}, status=400)
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return JsonResponse({'error': 'An error occurred during login'}, status=500)

@csrf_exempt
@require_POST
def api_signup(request: HttpRequest):
    """Handle user registration with comprehensive validation."""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')

        # Validation
        if not all([name, email, password, confirm_password]):
            return JsonResponse({'error': 'All fields are required'}, status=400)

        if password != confirm_password:
            return JsonResponse({'error': 'Passwords do not match'}, status=400)

        if len(password) < 8:
            return JsonResponse({'error': 'Password must be at least 8 characters long'}, status=400)
        
        # Basic email validation
        if '@' not in email or '.' not in email:
            return JsonResponse({'error': 'Please enter a valid email address'}, status=400)
        
        # Name validation
        if len(name) < 2:
            return JsonResponse({'error': 'Name must be at least 2 characters long'}, status=400)

        # Check if user already exists
        if User.objects.filter(username=email).exists():
            return JsonResponse({'error': 'An account with this email already exists'}, status=400)

        # Split name into first and last
        name_parts = name.split()
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

        # Create new user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Explicitly set backend for login
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        
        logger.info(f"New user registered: {email}")

        return JsonResponse({
            'success': True,
            'message': 'Registration successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': f"{user.first_name} {user.last_name}".strip()
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request format'}, status=400)
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        return JsonResponse({'error': 'An error occurred during registration'}, status=500)

@csrf_exempt
@require_POST
def api_logout(request: HttpRequest):
    """Handle user logout."""
    try:
        user_email = getattr(request.user, 'email', 'anonymous')
        logout(request)
        logger.info(f"User {user_email} logged out")
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
        email = data.get('email', '').strip().lower()

        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        
        # Basic email validation
        if '@' not in email or '.' not in email:
            return JsonResponse({'error': 'Please enter a valid email address'}, status=400)

        # Check if user exists, but don't reveal existence for security
        try:
            user = User.objects.get(email=email)
            logger.info(f"Password reset requested for existing user: {email}")
        except User.DoesNotExist:
            logger.info(f"Password reset requested for non-existent user: {email}")

        # In a real app, send reset link here
        # For now, always return success to prevent email enumeration
        return JsonResponse({
            'success': True,
            'message': 'If an account with this email exists, you will receive a password reset link.'
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request format'}, status=400)
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
                'full_name': f"{user.first_name} {user.last_name}".strip(),
                'is_authenticated': True,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None
            }
        })
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return JsonResponse({'error': 'Failed to fetch user profile'}, status=500)

# Remove duplicate function definitions and clean up remaining functions
@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_lessons(request: HttpRequest):
    """Handle lesson CRUD operations with better error handling."""
    if request.method == 'GET':
        async def get_lessons():
            if lessons is None:
                return []
            try:
                lessons_list = []
                async for lesson in lessons.find().limit(100):  # Limit results
                    lesson['_id'] = str(lesson['_id'])
                    lessons_list.append(lesson)
                return lessons_list
            except Exception as e:
                logger.error(f"Error fetching lessons: {e}")
                return []
        
        try:
            lessons_data = run_async_safely(get_lessons())
            return JsonResponse({'lessons': lessons_data})
        except Exception as e:
            logger.error(f"Error in api_lessons GET: {e}")
            return JsonResponse({'error': 'Failed to fetch lessons'}, status=500)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_id = data.get('student_id')
            pdf_data = data.get('pdf_data', {})
            llm_output = data.get('llm_output', {})
            topic = data.get('topic', '').strip()
            
            if not topic:
                return JsonResponse({'error': 'Topic is required'}, status=400)
            
            async def create_lesson_async():
                if lessons is None:
                    raise Exception("Database not available")
                    
                lesson_doc = create_lesson(student_id, pdf_data, llm_output, topic)
                result = await lessons.insert_one(lesson_doc)
                lesson_doc['_id'] = str(result.inserted_id)
                return lesson_doc
            
            new_lesson = run_async_safely(create_lesson_async())
            return JsonResponse({'lesson': new_lesson}, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            logger.error(f"Error creating lesson: {e}")
            return JsonResponse({'error': 'Failed to create lesson'}, status=500)
        
@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_quizzes(request: HttpRequest):
    """Handle quiz CRUD operations with improved error handling."""
    
    if request.method == 'GET':
        async def get_quizzes():
            if quizzes is None:
                return []
            try:
                quizzes_list = []
                async for quiz in quizzes.find().limit(100):  # Limit results
                    quiz['_id'] = str(quiz['_id'])
                    quizzes_list.append(quiz)
                return quizzes_list
            except Exception as e:
                logger.error(f"Error fetching quizzes: {e}")
                return []
        
        try:
            quizzes_data = run_async_safely(get_quizzes())
            return JsonResponse({'quizzes': quizzes_data})
        except Exception as e:
            logger.error(f"Error in api_quizzes GET: {e}")
            return JsonResponse({'error': 'Failed to fetch quizzes'}, status=500)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            lesson_id = data.get('lesson_id')
            quiz_data = data.get('quiz_data', {})
            questions = data.get('questions', [])
            title = data.get('title', '').strip()
            
            if not title:
                return JsonResponse({'error': 'Quiz title is required'}, status=400)
            
            if not questions:
                return JsonResponse({'error': 'At least one question is required'}, status=400)
            
            async def create_quiz_async():
                if quizzes is None:
                    raise Exception("Database not available")
                
                quiz_doc = create_quiz(lesson_id, quiz_data, questions, title)
                result = await quizzes.insert_one(quiz_doc)
                quiz_doc['_id'] = str(result.inserted_id)
                return quiz_doc
            
            new_quiz = run_async_safely(create_quiz_async())
            return JsonResponse({'quiz': new_quiz}, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            logger.error(f"Error creating quiz: {e}")
            return JsonResponse({'error': 'Failed to create quiz'}, status=500)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_progress(request: HttpRequest):
    """Handle progress CRUD operations with improved error handling."""
    
    if request.method == 'GET':
        async def get_progress():
            if progress is None:
                return []
            try:
                progress_list = []
                student_id = request.GET.get('student_id')
                
                query = {}
                if student_id:
                    query['student_id'] = student_id
                
                async for prog in progress.find(query).limit(100):
                    prog['_id'] = str(prog['_id'])
                    progress_list.append(prog)
                return progress_list
            except Exception as e:
                logger.error(f"Error fetching progress: {e}")
                return []
        
        try:
            progress_data = run_async_safely(get_progress())
            return JsonResponse({'progress': progress_data})
        except Exception as e:
            logger.error(f"Error in api_progress GET: {e}")
            return JsonResponse({'error': 'Failed to fetch progress'}, status=500)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_id = data.get('student_id')
            lesson_id = data.get('lesson_id')
            quiz_id = data.get('quiz_id', '')
            completion_percentage = data.get('completion_percentage', 0)
            score = data.get('score', 0)
            
            if not student_id or not lesson_id:
                return JsonResponse({'error': 'Student ID and Lesson ID are required'}, status=400)
            
            async def create_progress_async():
                if progress is None:
                    raise Exception("Database not available")
                
                progress_doc = create_progress(student_id, lesson_id, quiz_id, completion_percentage, score)
                result = await progress.insert_one(progress_doc)
                progress_doc['_id'] = str(result.inserted_id)
                return progress_doc
            
            new_progress = run_async_safely(create_progress_async())
            return JsonResponse({'progress': new_progress}, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            logger.error(f"Error creating progress: {e}")
            return JsonResponse({'error': 'Failed to create progress'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_rename_conversation(request: HttpRequest, conversation_id: str):
    """Rename a conversation."""
    try:
        data = json.loads(request.body)
        new_title = data.get('title', '').strip()
        
        if not new_title:
            return JsonResponse({'error': 'Title is required'}, status=400)
        
        async def rename_conversation_async():
            if conversations is None:
                raise Exception("Database not available")
            
            try:
                obj_id = ObjectId(conversation_id)
            except:
                raise Exception("Invalid conversation ID format")
            
            result = await conversations.update_one(
                {'_id': obj_id},
                {'$set': {'title': new_title, 'updated_at': datetime.utcnow()}}
            )
            
            if result.matched_count == 0:
                raise Exception("Conversation not found")
            
            return {'success': True, 'title': new_title}
        
        result = run_async_safely(rename_conversation_async())
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        logger.error(f"Error renaming conversation: {e}")
        return JsonResponse({'error': str(e)}, status=500)
