from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import Question, QuizResult
from ai_helper import deepseek_ai
from config import MAX_QUESTIONS
import logging

logger = logging.getLogger(__name__)

questions_bp = Blueprint('questions_api', __name__, url_prefix='/api/v1/questions')

@questions_bp.route('/generate', methods=['POST'])
@login_required
def generate_ai_questions():
    """توليد أسئلة باستخدام الذكاء الاصطناعي"""
    data = request.get_json()
    
    # التحقق من الحقول الإجبارية
    required_fields = ['subject', 'topic']
    missing = [field for field in required_fields if field not in data]
    if missing:
        return jsonify({
            'success': False,
            'error': f'الحقول المطلوبة ناقصة: {", ".join(missing)}'
        }), 400
    
    # معالجة عدد الأسئلة
    try:
        requested_count = int(data.get('count', 5))
        if requested_count < 1:
            raise ValueError("يجب أن يكون عدد الأسئلة أكبر من الصفر")
    except (TypeError, ValueError) as e:
        logger.warning(f"Invalid question count: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'عدد الأسئلة يجب أن يكون رقمًا صحيحًا موجبًا'
        }), 400
    
    # تطبيق الحد الأقصى
    final_count = min(requested_count, MAX_QUESTIONS)
    
    try:
        generated = deepseek_ai.generate_custom_questions(
            params={
                'category': data['subject'],
                'topic': data['topic'],
                'difficulty': data.get('difficulty', 'medium')
            },
            count=final_count
        )
        
        response_data = {
            'success': True,
            'count': len(generated),
            'user_id': current_user.id,
            'requested': requested_count,
            'questions': generated
        }
        
        if len(generated) < requested_count:
            response_data['warning'] = (
                f'تم توليد {len(generated)} من أصل {requested_count} أسئلة '
                f'(الحد الأقصى المسموح: {MAX_QUESTIONS})'
            )
        
        return jsonify(response_data), 200
        
    except KeyError as e:
        logger.error(f"Missing key in request: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'بيانات ناقصة: {str(e)}'
        }), 400
        
    except ValueError as e:
        logger.error(f"Invalid value: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
        
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'حدث خطأ غير متوقع، يرجى المحاولة لاحقًا'
        }), 500