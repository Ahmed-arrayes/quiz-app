
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime, timezone

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    quiz_results = db.relationship('QuizResult', backref='user', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # المادة الدراسية
    topic = db.Column(db.String(50), nullable=False)     # الموضوع المحدد
    difficulty = db.Column(db.String(20), nullable=False, default='متوسط')  # مستوى الصعوبة
    explanation = db.Column(db.Text)  # شرح الإجابة الصحيحة

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    time_taken = db.Column(db.Integer)  # بالثواني
    date_taken = db.Column(db.DateTime, nullable=False, 
                          default=lambda: datetime.now(timezone.utc))

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    correct_count = db.Column(db.Integer, default=0)
    total_count = db.Column(db.Integer, default=0)
    last_study_tip = db.Column(db.Text)
    last_updated = db.Column(db.DateTime, 
                            default=lambda: datetime.now(timezone.utc))

@app.route('/submit-quiz', methods=['POST'])
@login_required
def submit_quiz():
    try:
        # الحصول على إجابات المستخدم
        user_answers = request.form.to_dict()
        quiz_questions = session.get('quiz_questions', [])
        
        if not quiz_questions:
            flash('لم يتم العثور على أسئلة الاختبار.', 'error')
            return redirect(url_for('dashboard'))

        # حساب النتيجة
        correct_count = 0
        total_questions = len(quiz_questions)
        question_results = []

        for i, question in enumerate(quiz_questions):
            user_answer = user_answers.get(f'question_{i}')
            is_correct = user_answer == question['correct_answer']
            if is_correct:
                correct_count += 1

            # تحليل الإجابة باستخدام الذكاء الاصطناعي
            analysis = ai.analyze_answer(
                question['question'],
                user_answer,
                question['correct_answer']
            )

            question_results.append({
                'question_text': question['question'],
                'options': question['options'],
                'correct_answer': question['correct_answer'],
                'user_answer': user_answer,
                'is_correct': is_correct,
                'feedback': analysis.get('feedback', ''),
                'tip': analysis.get('tip', '')
            })

        # حساب النسبة المئوية
        score = (correct_count / total_questions) * 100 if total_questions > 0 else 0

        # الحصول على تحليل الأداء
        performance_data = {
            'score': score,
            'correct_count': correct_count,
            'total_questions': total_questions,
            'subject': session.get('quiz_subject'),
            'topic': session.get('quiz_topic'),
            'questions': question_results
        }

        ai_analysis = ai.get_performance_analysis(performance_data)
        study_tips = ai.get_study_tips(performance_data)
        encouragement = ai.get_encouragement_message({
            'score': score,
            'previous_scores': []  # يمكن إضافة الدرجات السابقة هنا
        })

        # حساب الوقت المستغرق
        start_time = session.get('quiz_start_time')
        time_taken = int(datetime.now().timestamp() - start_time) if start_time else 0

        # حفظ النتيجة في قاعدة البيانات
        quiz_result = QuizResult(
            user_id=current_user.id,
            score=score,
            total_questions=total_questions,
            time_taken=time_taken,
            date_taken=datetime.now()
        )
        db.session.add(quiz_result)
        db.session.commit()

        # تحضير البيانات للعرض
        result_data = {
            'score': score,
            'correct_count': correct_count,
            'total_questions': total_questions,
            'time_taken': time_taken,
            'questions': question_results,
            'ai_analysis': {
                'performance_analysis': ai_analysis,
                'encouragement_message': encouragement
            },
            'study_tips': study_tips
        }

        # حفظ البيانات في الجلسة للعرض
        session['quiz_result'] = result_data
        
        return redirect(url_for('quiz_result'))

    except Exception as e:
        app.logger.error(f"Error submitting quiz: {str(e)}")
        flash('حدث خطأ أثناء تقديم الاختبار. الرجاء المحاولة مرة أخرى.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/quiz-result')
@login_required
def quiz_result():
    result_data = session.get('quiz_result')
    if not result_data:
        flash('لم يتم العثور على نتائج الاختبار.', 'error')
        return redirect(url_for('dashboard'))
        
    return render_template('quiz_result.html', **result_data)

@app.route('/start-quiz', methods=['POST'])
@login_required
def start_quiz():
    try:
        # التحقق من وجود بيانات الجلسة
        # هنا نتحقق مما إذا كانت الأسئلة موجودة بالفعل في الجلسة
        if 'quiz_questions' not in session:  # نستخدم نفس المفتاح كما في الكود الأصلي
            # الحصول على بيانات الاختبار من النموذج
            # هنا نأخذ المعلومات التي أدخلها المستخدم
            subject = request.form.get('subject')  # المادة الدراسية
            topic = request.form.get('topic')      # الموضوع
            question_count = int(request.form.get('question_count', 5))  # عدد الأسئلة

            # توليد الأسئلة باستخدام الذكاء الاصطناعي
            # هنا نطلب من الذكاء الاصطناعي إنشاء الأسئلة
            questions = ai.generate_custom_questions({
                'category': subject,
                'topic': topic,
                'difficulty': 'متوسط'  # نمرر مستوى الصعوبة
            }, question_count)

            if not questions:
                # إذا لم يتم إنشاء الأسئلة، نعرض رسالة خطأ
                flash('تعذر إنشاء أسئلة للاختبار. الرجاء المحاولة لاحقًا.', 'error')
                return redirect(url_for('dashboard'))

            # تخزين البيانات في الجلسة
            # هنا نحفظ الأسئلة والمعلومات الأخرى في الجلسة
            session['quiz_questions'] = questions
            session['quiz_subject'] = subject
            session['quiz_topic'] = topic
            session['quiz_start_time'] = datetime.now().timestamp()

        # إعادة التوجيه إلى صفحة الاختبار
        return render_template('quiz.html', subject=subject, topic=topic, questions=questions, total_questions=question_count)

    except Exception as e:
        # إذا حدث خطأ، نقوم بتسجيله وعرض رسالة خطأ
        app.logger.error(f"Error starting quiz: {str(e)}")
        flash('حدث خطأ أثناء بدء الاختبار. الرجاء المحاولة مرة أخرى.', 'error')
        return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='127.0.0.1', port=5000, debug=True)
