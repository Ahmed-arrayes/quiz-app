from datetime import datetime, timezone
from flask_login import UserMixin
from extensions import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    quiz_results = db.relationship('QuizResult', backref='user', lazy=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_admin = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def calculate_progress_level(total_quizzes: int) -> str:
        """تحديد مستوى التقدم بناءً على عدد الاختبارات"""
        if total_quizzes == 0:
            return "مبتدئ"
        elif 1 <= total_quizzes <= 5:
            return "متوسط"
        elif 6 <= total_quizzes <= 10:
            return "متقدم"
        return "محترف"

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False, default='متوسط')
    explanation = db.Column(db.Text)

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    time_taken = db.Column(db.Integer)
    date_taken = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    correct_count = db.Column(db.Integer, default=0)
    total_count = db.Column(db.Integer, default=0)
    last_study_tip = db.Column(db.Text)
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
