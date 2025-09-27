# Django Views for Lesson Service API
import logging
import json
from datetime import datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

from .models import PDFDataModel, LessonModel, UserHistoryModel, check_database_connection, get_database_stats
from .pdf_processor_simple import PDFProcessor
from .lesson_generator import LessonGenerator

logger = logging.getLogger(__name__)

# Initialize processors
pdf_processor = PDFProcessor()
lesson_generator = LessonGenerator()

@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    db_status = check_database_connection()
    stats = get_database_stats()
    
    return Response({
        'service': 'lesson-service',
        'status': 'healthy' if db_status else 'unhealthy',
        'port': 8003,
        'database': 'connected' if db_status else 'disconnected',
        'ai_model': settings.AI_SETTINGS.get('MODEL_NAME', 'not_configured'),
        'stats': stats,
        'timestamp': datetime.utcnow().isoformat()
    })

@csrf_exempt
@api_view(['POST'])
def process_pdf_and_generate_lesson(request):
    """
    Main endpoint: Process PDF and generate AI lesson
    Expects: PDF file, user_id, lesson_type (optional)
    """
    try:
        # Validate request
        if 'pdf_file' not in request.FILES:
            return Response({
                'error': 'No PDF file provided',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        pdf_file = request.FILES['pdf_file']
        user_id = request.data.get('user_id')
        lesson_type = request.data.get('lesson_type', 'interactive')
        
        if user_id is None:
            return Response({
                'error': 'User ID is required',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Processing PDF lesson request: {pdf_file.name} for user {user_id}")
        
        # Validate PDF
        is_valid, validation_msg = pdf_processor.validate_pdf(pdf_file)
        if is_valid is None:
            return Response({
                'error': f'Invalid PDF: {validation_msg}',
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Process PDF
        pdf_result = pdf_processor.process_pdf(pdf_file, user_id, pdf_file.name)
        if pdf_result['success'] is False:
            return Response({
                'error': 'Failed to process PDF',
                'details': pdf_result.get('metadata', {}),
                'success': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Store PDF data
        pdf_id = PDFDataModel.create(
            user_id=user_id,
            filename=pdf_file.name,
            text_content=pdf_result['text_content'],
            images_data=pdf_result['images_data'],
            metadata=pdf_result['metadata']
        )
        
        if pdf_id is None:
            return Response({
                'error': 'Failed to store PDF data',
                'success': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Extract OCR text from images
        images_ocr_text = ""
        for img_data in pdf_result['images_data']:
            if img_data.get('ocr_text'):
                images_ocr_text += f"\n{img_data['ocr_text']}"
        
        # Generate AI lesson
        lesson_result = lesson_generator.generate_lesson(
            pdf_text=pdf_result['text_content'],
            images_ocr_text=images_ocr_text,
            lesson_type=lesson_type,
            user_context={'user_id': user_id}
        )
        
        # Store lesson
        lesson_id = LessonModel.create(
            user_id=user_id,
            pdf_id=pdf_id,
            lesson_title=lesson_result['title'],
            lesson_content=lesson_result['content'],
            lesson_type=lesson_type,
            metadata={
                'ai_generated': lesson_result.get('success', False),
                'generation_time': lesson_result.get('generated_at'),
                'fallback_used': lesson_result.get('fallback', False)
            }
        )
        
        # Create history entry
        if lesson_id:
            UserHistoryModel.create_entry(user_id, pdf_id, lesson_id, 'lesson_generated')
        
        return Response({
            'success': True,
            'pdf_id': pdf_id,
            'lesson_id': lesson_id,
            'lesson': {
                'title': lesson_result['title'],
                'content': lesson_result['content'],
                'type': lesson_type
            },
            'pdf_stats': {
                'pages': pdf_result['metadata'].get('total_pages', 0),
                'images': pdf_result['metadata'].get('total_images', 0),
                'text_length': pdf_result['metadata'].get('text_length', 0)
            },
            'message': 'PDF processed and lesson generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in process_pdf_and_generate_lesson: {e}")
        return Response({
            'error': 'Internal server error',
            'details': str(e),
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_user_lessons(request, user_id):
    """Get all lessons for a specific user"""
    try:
        lessons = LessonModel.get_by_user(user_id)
        
        # Convert ObjectId to string for JSON serialization
        lessons_data = []
        for lesson in lessons:
            lesson['_id'] = str(lesson['_id'])
            lesson['pdf_id'] = str(lesson['pdf_id'])
            lesson['created_at'] = lesson['created_at'].isoformat()
            lesson['updated_at'] = lesson['updated_at'].isoformat()
            lessons_data.append(lesson)
        
        return Response({
            'success': True,
            'user_id': user_id,
            'lessons': lessons_data,
            'count': len(lessons_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting user lessons: {e}")
        return Response({
            'error': 'Failed to retrieve lessons',
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_lesson_detail(request, lesson_id):
    """Get detailed information about a specific lesson"""
    try:
        lesson = LessonModel.get_by_id(lesson_id)
        
        if lesson is None:
            return Response({
                'error': 'Lesson not found',
                'success': False
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Convert ObjectId to string
        lesson['_id'] = str(lesson['_id'])
        lesson['pdf_id'] = str(lesson['pdf_id'])
        lesson['created_at'] = lesson['created_at'].isoformat()
        lesson['updated_at'] = lesson['updated_at'].isoformat()
        
        return Response({
            'success': True,
            'lesson': lesson
        })
        
    except Exception as e:
        logger.error(f"Error getting lesson detail: {e}")
        return Response({
            'error': 'Failed to retrieve lesson',
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_user_history(request, user_id):
    """Get user's lesson generation history"""
    try:
        from .models import UserHistoryModel
        
        history = UserHistoryModel.get_user_history(user_id, limit=50)
        
        # Convert ObjectId to string for JSON serialization
        history_data = []
        for entry in history:
            entry['_id'] = str(entry['_id'])
            entry['pdf_id'] = str(entry['pdf_id'])
            entry['lesson_id'] = str(entry['lesson_id'])
            entry['timestamp'] = entry['timestamp'].isoformat()
            history_data.append(entry)
        
        return Response({
            'success': True,
            'user_id': user_id,
            'history': history_data,
            'count': len(history_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting user history: {e}")
        return Response({
            'error': 'Failed to retrieve history',
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
def regenerate_lesson(request, lesson_id):
    """Regenerate a lesson with different type or parameters"""
    try:
        lesson = LessonModel.get_by_id(lesson_id)
        if lesson is None:
            return Response({
                'error': 'Lesson not found',
                'success': False
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get original PDF data
        pdf_data = PDFDataModel.get_by_id(str(lesson['pdf_id']))
        if pdf_data is None:
            return Response({
                'error': 'Original PDF data not found',
                'success': False
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get new lesson type
        new_lesson_type = request.data.get('lesson_type', lesson['lesson_type'])
        
        # Extract OCR text from images
        images_ocr_text = ""
        for img_data in pdf_data.get('images_data', []):
            if img_data.get('ocr_text'):
                images_ocr_text += f"\n{img_data['ocr_text']}"
        
        # Generate new lesson
        lesson_result = lesson_generator.generate_lesson(
            pdf_text=pdf_data['text_content'],
            images_ocr_text=images_ocr_text,
            lesson_type=new_lesson_type,
            user_context={'user_id': lesson['user_id']}
        )
        
        # Create new lesson
        new_lesson_id = LessonModel.create(
            user_id=lesson['user_id'],
            pdf_id=str(lesson['pdf_id']),
            lesson_title=lesson_result['title'],
            lesson_content=lesson_result['content'],
            lesson_type=new_lesson_type,
            metadata={
                'ai_generated': lesson_result.get('success', False),
                'generation_time': lesson_result.get('generated_at'),
                'regenerated_from': lesson_id,
                'fallback_used': lesson_result.get('fallback', False)
            }
        )
        
        # Create history entry
        if new_lesson_id:
            UserHistoryModel.create_entry(
                lesson['user_id'], 
                str(lesson['pdf_id']), 
                new_lesson_id, 
                'lesson_regenerated'
            )
        
        return Response({
            'success': True,
            'original_lesson_id': lesson_id,
            'new_lesson_id': new_lesson_id,
            'lesson': {
                'title': lesson_result['title'],
                'content': lesson_result['content'],
                'type': new_lesson_type
            },
            'message': 'Lesson regenerated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error regenerating lesson: {e}")
        return Response({
            'error': 'Failed to regenerate lesson',
            'success': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
