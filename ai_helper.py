
### الكود النهائي المدمج مع التحسينات:

import json
import logging
import os
import re
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# تهيئة نظام التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('ai_debug.log'), logging.StreamHandler()]
)

load_dotenv()

class DeepSeekAI:
    def __init__(self):
        """تهيئة كائن الذكاء الاصطناعي مع التحقق من المفتاح"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.max_retries = 3
        
        if not self.api_key:
            self.logger.critical("API key not found in .env file")
            raise ValueError("مفتاح API غير موجود في ملف البيئة")

    def _extract_json(self, response: str) -> Optional[str]:
        """
        استخراج JSON من الاستجابة باستخدام التعابير النمطية
        معالجة التنسيقات المختلفة:
        1. ```json {...} ```
        2. JSON داخل نص عادي
        3. أخطاء تنسيق بسيطة
        """
        try:
            # البحث عن كتل JSON باستخدام regex
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json_match.group().strip()
            return None
        except Exception as e:
            self.logger.error(f"فشل استخراج JSON: {str(e)}")
            return None

    def _validate_question(self, question: Dict) -> bool:
        """التحقق من الهيكل الكامل للسؤال"""
        required_structure = {
            'question_text': str,
            'option_a': str,
            'option_b': str,
            'option_c': str,
            'option_d': str,
            'correct_answer': lambda x: x in ['أ', 'ب', 'ج', 'د'],
            'category': str,
            'topic': str,
            'difficulty': lambda x: x in ['سهل', 'متوسط', 'صعب']
        }
        
        for key, validator in required_structure.items():
            if key not in question:
                self.logger.warning(f"المفتاح المفقود: {key}")
                return False
            if not isinstance(validator, type) and not callable(validator):
                continue
            try:
                if not validator(question[key]):
                    self.logger.warning(f"قيمة غير صالحة للمفتاح {key}: {question[key]}")
                    return False
            except Exception as e:
                self.logger.error(f"خطأ في التحقق من {key}: {str(e)}")
                return False
        return True

    def generate_questions(self, params: Dict[str, Any], count: int = 5) -> List[Dict[str, Any]]:
        """
        توليد أسئلة مع التحقق من الصحة وإعادة المحاولة التلقائية
        """
        for attempt in range(self.max_retries):
            try:
                prompt = self._build_prompt(params, count)
                response = self._send_api_request(prompt)
                
                if not response:
                    raise ValueError("استجابة فارغة من API")
                
                json_str = self._extract_json(response)
                if not json_str:
                    raise ValueError("لا يوجد JSON في الاستجابة")
                
                data = json.loads(json_str)
                questions = data.get('questions', [])
                
                valid_questions = [q for q in questions if self._validate_question(q)]
                
                if len(valid_questions) >= count:
                    return valid_questions[:count]
                
                self.logger.warning(f"المحاولة {attempt + 1}: تم الحصول على {len(valid_questions)} أسئلة صالحة فقط")

            except (json.JSONDecodeError, KeyError) as e:
                self.logger.error(f"خطأ في معالجة البيانات: {str(e)}")
                if attempt == self.max_retries - 1:
                    return []
                continue
                
            except Exception as e:
                self.logger.exception(f"خطأ غير متوقع: {str(e)}")
                return []

        return []

    def _build_prompt(self, params: Dict, count: int) -> str:
        """بناء رسالة الطلب مع أمثلة التنسيق"""
        return f"""
        قم بإنشاء {count} أسئلة في {params.get('category', 'عام')} حول {params.get('topic', 'عام')}.
        مستوى الصعوبة: {params.get('difficulty', 'متوسط')}
        
        التنسيق المطلوب:
        {{
            "questions": [
                {{
                    "question_text": "نص السؤال هنا",
                    "option_a": "الخيار الأول",
                    "option_b": "الخيار الثاني",
                    "option_c": "الخيار الثالث",
                    "option_d": "الخيار الرابع",
                    "correct_answer": "أ",
                    "category": "{params.get('category', 'عام')}",
                    "topic": "{params.get('topic', 'عام')}",
                    "difficulty": "{params.get('difficulty', 'متوسط')}",
                    "explanation": "شرح الإجابة الصحيحة"
                }}
            ]
        }}
        """

    def _send_api_request(self, prompt: str) -> Optional[str]:
        """إرسال طلب API مع إدارة الأخطاء"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            response_data = response.json()
            if 'choices' not in response_data:
                raise ValueError("استجابة API غير متوقعة")
                
            return response_data['choices'][0]['message']['content']
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"خطأ HTTP {e.response.status_code}: {e.response.text}")
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"خطأ اتصال: {str(e)}")
            return None

if __name__ == "__main__":
    # اختبار التشغيل
    ai = DeepSeekAI()
    test_params = {
        "category": "الرياضيات",
        "topic": "الجبر",
        "difficulty": "متوسط"
    }
    questions = ai.generate_questions(test_params, 3)
    print(f"الأسئلة المولدة ({len(questions)}):")
    print(json.dumps(questions, ensure_ascii=False, indent=2))

