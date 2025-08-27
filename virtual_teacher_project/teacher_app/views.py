# teacher_app/views.py

import logging
import json
from django.shortcuts import render
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import fitz  # PyMuPDF
from .mongo_collections import students, lessons, quizzes, progress, analytics
from .mongo import create_student, create_lesson, create_quiz, create_progress
from bson import ObjectId
import asyncio

# It's good practice to get a logger instance.
logger = logging.getLogger(__name__)

def teacher_view(request: HttpRequest):
    """Renders the main teacher page."""
    return render(request, "teacher_app/teacher.html")

@csrf_exempt
@require_POST
def upload_pdf(request: HttpRequest):
    """Handles PDF file uploads, extracts text, and returns it as JSON."""
    if not request.FILES.get('pdf_file'):
        return JsonResponse({'error': 'No PDF file found in the request.'}, status=400)

    pdf_file = request.FILES['pdf_file']
    
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
        return JsonResponse({'text': text_content, 'filename': pdf_file.name})
    
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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            students_data = loop.run_until_complete(get_students())
            return JsonResponse({'students': students_data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        finally:
            loop.close()
    
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
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            new_student = loop.run_until_complete(create_student_async())
            return JsonResponse({'student': new_student}, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error creating student: {e}")
            return JsonResponse({'error': str(e)}, status=500)
        finally:
            loop.close()

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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            progress_data = loop.run_until_complete(get_progress())
            return JsonResponse({'progress': progress_data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        finally:
            loop.close()
    
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
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            updated_progress = loop.run_until_complete(update_progress_async())
            return JsonResponse({'progress': updated_progress})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
            return JsonResponse({'error': str(e)}, status=500)
        finally:
            loop.close()