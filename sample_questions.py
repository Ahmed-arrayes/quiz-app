from app import app, db, Question
import os
import json  # <-- تأكد من وجود هذا الاستيراد
import requests  # <-- إضافة هذا الاستيراد
from ai_helper import DeepSeekAI
from dotenv import load_dotenv

load_dotenv()

def add_sample_questions():
    """هذه الوظيفة تحذف الأسئلة الموجودة في قاعدة البيانات وتضيف أسئلة جديدة أو تولد أسئلة باستخدام DeepSeek."""
    with app.app_context():
        try:
            Question.query.delete()
            questions = generate_questions_from_deepseek()  # <-- تغيير هنا
            if not questions:
                raise ValueError("لم يتم توليد أي أسئلة.")
            db.session.add_all(questions)
            db.session.commit()
            print("تمت إضافة الأسئلة بنجاح!")
        except Exception as e:
            print(f"حدث خطأ أثناء إضافة الأسئلة: {str(e)}")
            db.session.rollback()

def generate_questions_from_deepseek():
    """توليد أسئلة باستخدام DeepSeek API."""
    ai = DeepSeekAI()
    
    prompt = """قم بإنشاء 5 أسئلة اختيار من متعدد باللغة العربية في مادة الرياضيات.
    التنسيق المطلوب:
    {
        "questions": [
            {
                "question": "السؤال هنا",
                "options": {
                    "أ": "الخيار الأول",
                    "ب": "الخيار الثاني",
                    "ج": "الخيار الثالث",
                    "د": "الخيار الرابع"
                },
                "correct_answer": "أ",
                "explanation": "شرح الإجابة الصحيحة"
            }
        ]
    }"""
    
    try:
        response = ai._send_request(prompt)
        print(f"API Response: {response}")
        
        # تنظيف استجابة JSON
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        elif response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]
            
        result = json.loads(response)
        
        # التحقق من وجود الأسئلة
        if 'questions' not in result or not isinstance(result['questions'], list) or len(result['questions']) == 0:
            print("No questions found in response or questions list is empty")
            return []
            
        # تحويل الأسئلة إلى التنسيق المطلوب
        formatted_questions = []
        for q in result['questions']:
            # التحقق من نوع الخيارات
            if not isinstance(q.get('options'), dict):
                print("Invalid options format")
                continue
                
            formatted_question = {
                'question': q.get('question', ''),
                'options': [
                    q['options'].get('أ', ''),
                    q['options'].get('ب', ''),
                    q['options'].get('ج', ''),
                    q['options'].get('د', '')
                ],
                'correct_answer': q.get('correct_answer', ''),
                'explanation': q.get('explanation', '')
            }
            
            # التحقق من عدد الخيارات
            if len(formatted_question['options']) != 4:
                print("Question has invalid number of options")
                continue
                
            # التحقق من صحة الإجابة الصحيحة
            if formatted_question['correct_answer'] not in ['أ', 'ب', 'ج', 'د']:
                print("Invalid correct answer")
                continue
                
            formatted_questions.append(formatted_question)
        
        return formatted_questions
        
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {str(e)}")
        print(f"Response was: {response}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Network or API request error: {str(e)}")
        return []
    except KeyError as e:
        print(f"Key error in response: {str(e)}")
        return []
    except Exception as e:
        print(f"خطأ في توليد الأسئلة: {str(e)}")
        return []
    
def parse_questions(questions_data):
    """تحليل البيانات المستلمة من OpenAI إلى قائمة من كائنات Question."""
    questions = []
    
    # تحسين نمط regex لدعم أي فوارق بين الأسئلة.
    question_pattern = r"السؤال (.*?)\nالخيار الأول: (.*?)\nالخيار الثاني: (.*?)\nالخيار الثالث: (.*?)\nالخيار الرابع: (.*?)\nالإجابة الصحيحة: (.*?)"
    matches = re.findall(question_pattern, questions_data, re.DOTALL)
    
    # في حالة عدم وجود أي تطابق للنمط، طباعة رسالة تحذير.
    if not matches:
        print("لم يتم العثور على أسئلة صحيحة في البيانات.")
    
    for match in matches:
        question_text, option_a, option_b, option_c, option_d, correct_answer = match
        question = Question(
            question_text=question_text.strip(),
            option_a=option_a.strip(),
            option_b=option_b.strip(),
            option_c=option_c.strip(),
            option_d=option_d.strip(),
            correct_answer=correct_answer.strip(),
            category="رياضيات"
        )
        questions.append(question)
    
    return questions

def generate_questions_from_deepseek():
    """توليد أسئلة باستخدام DeepSeek API."""
    ai = DeepSeekAI()
    
    prompt = """قم بإنشاء 5 أسئلة اختيار من متعدد باللغة العربية في مادة الرياضيات.
    التنسيق المطلوب:
    {
        "questions": [
            {
                "question": "السؤال هنا",
                "options": {
                    "أ": "الخيار الأول",
                    "ب": "الخيار الثاني",
                    "ج": "الخيار الثالث",
                    "د": "الخيار الرابع"
                },
                "correct_answer": "أ",
                "explanation": "شرح الإجابة الصحيحة"
            }
        ]
    }"""
    
    try:
        response = ai._send_request(prompt)
        print(f"API Response: {response}")  # للتصحيح
        
        # تنظيف استجابة JSON
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        if response.endswith('```'):
            response = response[:-3]
            
        result = json.loads(response)
        if 'questions' not in result:
            print("No questions found in response")
            return []
            
        # تحويل الأسئلة إلى التنسيق المطلوب
        formatted_questions = []
        for q in result['questions']:
            formatted_question = {
                'question': q['question'],
                'options': [q['options']['أ'], q['options']['ب'], q['options']['ج'], q['options']['د']],
                'correct_answer': q['correct_answer'],
                'explanation': q['explanation']
            }
            formatted_questions.append(formatted_question)
        
        return formatted_questions
        
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {str(e)}")
        print(f"Response was: {response}")
        return []
    except Exception as e:
        print(f"خطأ في توليد الأسئلة: {str(e)}")
        return []

if __name__ == '__main__':
    add_sample_questions()
