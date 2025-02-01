from flask import Blueprint
from .questions import questions_bp
from .users import users_bp

api_bp = Blueprint('api', __name__)
api_bp.register_blueprint(questions_bp)
api_bp.register_blueprint(users_bp)