# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange

class QuizSelectionForm(FlaskForm):
    subject = SelectField('المادة', choices=[], validators=[DataRequired()])
    specialization = SelectField('التخصص', choices=[], validators=[DataRequired()])
    topic = SelectField('الموضوع', choices=[], validators=[DataRequired()])
    sub_topic = SelectField('العنوان الفرعي', choices=[])
    count = IntegerField('عدد الأسئلة', validators=[DataRequired(), NumberRange(min=1, max=20)], default=10)
    difficulty = SelectField('مستوى الصعوبة', choices=[('سهل', 'سهل'), ('متوسط', 'متوسط'), ('صعب', 'صعب')], validators=[DataRequired()])
    submit = SubmitField('ابدأ الاختبار')

class RegistrationForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3, max=25)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('تسجيل')

class LoginForm(FlaskForm):
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    remember_me = SelectField('تذكرني', choices=[('yes', 'نعم'), ('no', 'لا')])
    submit = SubmitField('تسجيل الدخول')

class UpdateProfileForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3, max=25)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    submit = SubmitField('تحديث')