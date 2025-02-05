# routes.py
from flask import session, Blueprint
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, login_user, logout_user
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import secrets

from extensions import db, login_manager
from models import User, QuizSession, QuizResult, Question, UserProgress, QuizSessionQuestion
from forms import RegistrationForm, LoginForm, QuizSelectionForm, UpdateProfileForm
from hierarchy import SUBJECT_TREE

# --- تهيئة الـ Blueprints ---
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
quiz_bp = Blueprint('quiz', __name__)
logger = logging.getLogger(__name__)

# --- دوال مساعدة ---
def sanitize_input(input_str):
    """تطهير المدخلات من الأحرف الخطرة."""
    return input_str.strip()

def generate_session_token():
    """توليد رمز جلسة فريد."""
    return secrets.token_urlsafe(16)

def validate_hierarchy(form_data):
    """التحقق من صحة التدرج الهرمي."""
    current_level = SUBJECT_TREE
    try:
        for level in ['subject', 'specialization', 'topic', 'sub_topic']:
            if not form_data.get(level):
                continue
            value = form_data[level]
            if value not in current_level:
                return False
            current_level = current_level[value]
        return True
    except Exception as e:
        logger.error(f"خطأ في التحقق من التدرج: {str(e)}")
        return False

def calculate_adaptive_difficulty(user_id, subject):
    """حساب الصعوبة التكيفية بناءً على أداء المستخدم."""
    progress = UserProgress.query.filter_by(user_id=user_id, category=subject).first()
    if not progress or progress.total_count < 5:
        return 'متوسط'
    success_rate = progress.correct_count / progress.total_count
    if success_rate > 0.8:
        return 'صعب'
    elif success_rate < 0.4:
        return 'سهل'
    return 'متوسط'

def update_user_progress(user_id, question, is_correct):
    """تحديث تقدم المستخدم في قاعدة البيانات."""
    progress = UserProgress.query.filter_by(
        user_id=user_id,
        category=question.category,
        topic=question.topic
    ).first()

    if not progress:
        progress = UserProgress(
            user_id=user_id,
            category=question.category,
            topic=question.topic,
            correct_count=0,
            total_count=0
        )
        db.session.add(progress)

    progress.total_count += 1
    if is_correct:
        progress.correct_count += 1
    progress.last_updated = datetime.now(timezone.utc)
    db.session.commit()

# --- مسارات المصادقة ---

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter(
            (User.email == form.email.data) | (User.username == form.username.data)
        ).first()
        if existing_user:
            flash('اسم المستخدم أو البريد الإلكتروني موجود مسبقًا', 'danger')
            return redirect(url_for('auth.register'))

        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('تم التسجيل بنجاح! يمكنك تسجيل الدخول الآن', 'success')
            return redirect(url_for('auth_bp.login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"فشل التسجيل: {str(e)}")
            flash('حدث خطأ أثناء التسجيل', 'danger')
    return render_template('register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('تم تسجيل الدخول بنجاح!', 'success')
            return redirect(url_for('main.home'))
        flash('بيانات الدخول غير صحيحة', 'danger')
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('main_bp.home'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('تم تحديث البيانات الشخصية بنجاح', 'success')
        return redirect(url_for('auth_bp.profile'))
    return render_template('profile.html', form=form)

# --- المسارات الرئيسية ---

@main_bp.route('/')
def home():
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    try:
        quiz_results = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.date_taken.desc()).all()
        return render_template('dashboard.html', quiz_results=quiz_results)
    except Exception as e:
        logger.error(f"خطأ في تحميل لوحة التحكم: {str(e)}", exc_info=True)
        flash('حدث خطأ أثناء تحميل لوحة التحكم', 'danger')
        return redirect(url_for('main.home'))

@main_bp.route('/leaderboard')
@login_required
def leaderboard():
    try:
        top_users = User.query.join(QuizResult, User.id == QuizResult.user_id)\
            .group_by(User.id)\
            .order_by(db.func.sum(QuizResult.score).desc())\
            .limit(10)\
            .all()
        return render_template('leaderboard.html', top_users=top_users)
    except Exception as e:
        logger.error(f"خطأ في تحميل قائمة المتصدرين: {str(e)}", exc_info=True)
        flash('حدث خطأ أثناء تحميل قائمة المتصدرين', 'danger')
        return redirect(url_for('main_bp.home'))

# --- مسارات الاختبارات ---

@quiz_bp.route('/selection', methods=['GET', 'POST'])
@login_required
def selection():
    form = QuizSelectionForm()
    form.subject.choices = [(subj, subj) for subj in SUBJECT_TREE.keys()]

    if request.method == 'POST':
        # التحقق من صحة البيانات وحفظها
        if form.validate_on_submit():
            # حفظ بيانات الاختيار والانتقال إلى بدء الاختبار
            session['quiz_selection'] = {
                'subject': form.subject.data,
                'specialization': form.specialization.data,
                'topic': form.topic.data,
                'sub_topic': form.sub_topic.data,
                'count': form.count.data,
                'difficulty': form.difficulty.data
            }
            return redirect(url_for('quiz.start_quiz'))
    else:
        # إذا كان الطلب GET، تعيين الخيارات الافتراضية
        form.specialization.choices = [('', 'اختر المادة أولاً')]
        form.topic.choices = [('', 'اختر التخصص أولاً')]
        form.sub_topic.choices = [('', 'اختر الموضوع أولاً')]


    return render_template('selection.html', form=form, subject_tree=SUBJECT_TREE)

@quiz_bp.route('/start', methods=['GET'])
@login_required
def start_quiz():
    """بدء اختبار جديد مع التركيز على الأخطاء السابقة."""
    try:
        form_data = session.get('quiz_selection')
        if not form_data:
            flash('يرجى اختيار تفاصيل الاختبار أولاً', 'danger')
            return redirect(url_for('quiz.selection'))

        # التحقق من صحة التدرج الهرمي
        if not validate_hierarchy(form_data):
            flash('مسار الموضوع غير صالح', 'danger')
            return redirect(url_for('quiz.selection'))

        # حساب الصعوبة التكيفية
        form_data['difficulty'] = calculate_adaptive_difficulty(current_user.id, form_data['subject'])

        # جلب الأسئلة ذات الصلة
        questions = Question.query.filter_by(
            category=form_data['subject'],
            topic=form_data['topic'],
            difficulty=form_data['difficulty']
        ).order_by(db.func.random()).limit(form_data['count']).all()

        if not questions:
            flash('لا توجد أسئلة متاحة لهذا الاختبار. الرجاء اختيار إعدادات مختلفة.', 'warning')
            return redirect(url_for('quiz.selection'))

        # إنشاء جلسة الاختبار
        new_session = QuizSession(
            user_id=current_user.id,
            session_data={
                'current_index': 0,
                'score': 0,
                'time_spent': 0.0
            },
            subject_path=[
                form_data['subject'],
                form_data.get('specialization', ''),
                form_data.get('topic', ''),
                form_data.get('sub_topic', '')
            ],
            session_token=generate_session_token()
        )
        db.session.add(new_session)
        db.session.flush()

        # إضافة الأسئلة إلى الجلسة
        for idx, question in enumerate(questions):
            session_question = QuizSessionQuestion(
                session_id=new_session.id,
                question_id=question.id,
                order=idx
            )
            db.session.add(session_question)

        db.session.commit()
        session['quiz_session'] = new_session.session_token

        return redirect(url_for('quiz.show_question'))
    except Exception as e:
        logger.error(f"خطأ في بدء الاختبار: {str(e)}", exc_info=True)
        flash('فشل في بدء الاختبار، يرجى المحاولة لاحقًا', 'danger')
        return redirect(url_for('main_bp.home'))

@quiz_bp.route('/question', methods=['GET', 'POST'])
@login_required
def show_question():
    """عرض السؤال الحالي"""
    try:
        quiz_session = QuizSession.query.filter_by(
            session_token=session.get('quiz_session'),
            user_id=current_user.id
        ).first()

        if not quiz_session:
            flash('لا يوجد اختبار نشط', 'warning')
            return redirect(url_for('main_bp.dashboard'))

        current_index = quiz_session.session_data['current_index']
        session_questions = quiz_session.questions
        if current_index >= len(session_questions):
            return redirect(url_for('quiz.submit_quiz'))

        question = session_questions[current_index].question
        progress = {
            'current': current_index + 1,
            'total': len(session_questions),
            'percentage': ((current_index + 1) / len(session_questions)) * 100
        }

        if request.method == 'POST':
            selected_option = request.form.get('answer')
            if not selected_option:
                flash('يرجى اختيار إجابة', 'warning')
                return redirect(url_for('quiz.show_question'))

            is_correct = selected_option == question.correct_answer
            session_questions[current_index].user_answer = selected_option
            session_questions[current_index].is_correct = is_correct
            session_questions[current_index].is_answered = True

            quiz_session.session_data['current_index'] += 1
            if is_correct:
                quiz_session.session_data['score'] += 1

            # تحديث تقدم المستخدم
            update_user_progress(current_user.id, question, is_correct)

            db.session.commit()

            return redirect(url_for('quiz.show_question'))

        return render_template('question.html',
                               question=question,
                               progress=progress)

    except Exception as e:
        logger.error(f"خطأ في عرض السؤال: {str(e)}")
        flash('حدث خطأ في تحميل السؤال', 'danger')
        return redirect(url_for('main_bp.dashboard'))

@quiz_bp.route('/submit', methods=['GET'])
@login_required
def submit_quiz():
    """إنهاء الاختبار وعرض النتائج"""
    try:
        quiz_session = QuizSession.query.filter_by(
            session_token=session.get('quiz_session'),
            user_id=current_user.id
        ).first()
        if not quiz_session:
            flash('لا يوجد اختبار نشط', 'danger')
            return redirect(url_for('main_bp.dashboard'))

        total_questions = len(quiz_session.questions)
        correct_answers = quiz_session.session_data['score']

        # حفظ نتيجة الاختبار
        quiz_result = QuizResult(
            user_id=current_user.id,
            score=correct_answers,
            total_questions=total_questions,
            time_taken=int((datetime.now(timezone.utc) - quiz_session.created_at).total_seconds()),
            date_taken=datetime.now(timezone.utc)
        )
        db.session.add(quiz_result)

        # حذف الجلسة
        db.session.delete(quiz_session)
        db.session.commit()
        session.pop('quiz_session', None)
        session.pop('quiz_selection', None)

        flash('تم إنهاء الاختبار بنجاح!', 'success')
        return redirect(url_for('quiz.view_results', result_id=quiz_result.id))

    except Exception as e:
        logger.error(f"خطأ في إنهاء الاختبار: {str(e)}", exc_info=True)
        flash('حدث خطأ أثناء إنهاء الاختبار', 'danger')
        return redirect(url_for('main_bp.dashboard'))

@quiz_bp.route('/results/<int:result_id>')
@login_required
def view_results(result_id):
    """عرض نتائج الاختبار مع تحليل الأخطاء."""
    quiz_result = QuizResult.query.get_or_404(result_id)
    if quiz_result.user_id != current_user.id:
        flash('ليس لديك صلاحية لعرض هذه النتائج', 'danger')
        return redirect(url_for('main_bp.dashboard'))

    # تحليل الأخطاء
    incorrect_questions = QuizSessionQuestion.query.join(QuizSession).filter(
        QuizSession.user_id == current_user.id,
        QuizSessionQuestion.is_correct == False
    ).all()
    weak_topics = {}
    for q in incorrect_questions:
        topic = q.question.topic
        weak_topics[topic] = weak_topics.get(topic, 0) + 1

    return render_template('results.html', quiz_result=quiz_result, weak_topics=weak_topics)

@quiz_bp.route('/review/<int:result_id>')
@login_required
def review_quiz(result_id):
    """مراجعة الاختبار مع شرح الأخطاء."""
    quiz_result = QuizResult.query.get_or_404(result_id)
    if quiz_result.user_id != current_user.id:
        flash('ليس لديك صلاحية لمراجعة هذا الاختبار', 'danger')
        return redirect(url_for('main_bp.dashboard'))

    # جلب الأسئلة والإجابات
    quiz_questions = QuizSessionQuestion.query.join(QuizSession).filter(
        QuizSession.user_id == current_user.id,
        QuizResult.id == result_id
    ).all()

    return render_template('review.html', quiz_result=quiz_result, questions=quiz_questions)
