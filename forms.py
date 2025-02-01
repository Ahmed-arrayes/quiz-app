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
