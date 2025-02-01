from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import User
import logging

logger = logging.getLogger(__name__)

users_bp = Blueprint('users_api', __name__, url_prefix='/api/v1/users')

@users_bp.route('/', methods=['GET'])
@login_required
def get_users():
    """الحصول على قائمة المستخدمين (للمشرفين فقط)"""
    try:
        if not current_user.is_admin:
            logger.warning(f"Unauthorized access attempt by user: {current_user.id}")
            return jsonify({
                'success': False,
                'error': 'غير مصرح بالوصول'
            }), 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        users = User.query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'success': True,
            'data': {
                'users': [user.to_dict() for user in users.items],
                'pagination': {
                    'total': users.total,
                    'pages': users.pages,
                    'current': users.page,
                    'per_page': users.per_page
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'خطأ في الخادم'
        }), 500

@users_bp.route('/<int:user_id>/progress', methods=['GET'])
@login_required
def get_user_progress(user_id):
    """الحصول على تقدم مستخدم معين"""
    try:
        user = User.query.get_or_404(user_id)
        
        if not user.quiz_results:
            return jsonify({
                'success': True,
                'data': {
                    'user': user.to_dict(),
                    'stats': {'message': 'لا توجد نتائج اختبارات بعد'}
                }
            }), 200

        total_quizzes = len(user.quiz_results)
        average_score = sum(r.score for r in user.quiz_results) / total_quizzes
        last_attempt = max(r.timestamp for r in user.quiz_results)
        
        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict(),
                'stats': {
                    'total_quizzes': total_quizzes,
                    'average_score': round(average_score, 2),
                    'last_attempt': last_attempt.isoformat(),
                    'progress_level': User.calculate_progress_level(total_quizzes)
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in user progress {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'خطأ في الخادم'
        }), 500