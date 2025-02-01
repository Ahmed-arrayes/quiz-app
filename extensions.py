from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import os
import requests
import json
from typing import Dict, Any, Optional
from flask import Flask

# تهيئة إضافات Flask
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

class AIError(Exception):
    """فئة استثناء مخصصة لأخطاء الذكاء الاصطناعي"""
    def __init__(self, message: str, status_code: int = None, details: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details
        self.log_message = f"AI Error {status_code}: {message} | Details: {details}"

class AIIntegration:
    """فئة لإدارة تكاملات الذكاء الاصطناعي"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        self.base_url = "https://api.deepseek.com/v1"
        self.max_retries = 3
        self._validate_initial_config()

    def _validate_initial_config(self):
        """التحقق من التهيئة الأولية"""
        if not self.api_key:
            raise ValueError("يجب توفير مفتاح API أو تعيينه في متغيرات البيئة")

    def init_app(self, app: Flask) -> None:
        """تهيئة التكامل مع تطبيق Flask"""
        self.api_key = app.config.get('DEEPSEEK_API_KEY', self.api_key)
        if not self.api_key:
            raise RuntimeError("لم يتم العثور على DEEPSEEK_API_KEY في تكوين التطبيق")

    def generate_quiz(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """توليد أسئلة الاختبار"""
        prompt = self._build_prompt(params)
        for attempt in range(self.max_retries):
            try:
                return self._send_request(prompt)
            except AIError as e:
                if attempt == self.max_retries - 1:
                    raise
                continue
        raise AIError("فشل بعد محاولات متعددة")

    def _build_prompt(self, params: Dict[str, Any]) -> str:
        """بناء نص الطلب المخصص"""
        levels = [
            params.get('subject', ''),
            params.get('specialization', ''),
            params.get('topic', ''),
            params.get('sub_topic', '')
        ]
        hierarchy = " → ".join(filter(None, levels))

        return f"""
        أنت معلم خبير في {hierarchy}.
        المطلوب: إنشاء {params.get('count', 10)} أسئلة اختيار من متعدد
        مستوى الصعوبة: {params.get('difficulty', 'متوسط')}

        المواصفات:
        - كل سؤال يجب أن يكون واضحًا ومحددًا
        - الخيارات متوازنة ومنطقية
        - تضمين شرح مفصل للإجابة الصحيحة
        - التنسيق النهائي: JSON
        """

    def _send_request(self, prompt: str) -> Dict[str, Any]:
        """إرسال الطلب إلى واجهة API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 3000
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=data,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
            return self._parse_response(response.json())

        except requests.exceptions.HTTPError as e:
            raise AIError(
                message=f"HTTP Error {e.response.status_code}",
                status_code=e.response.status_code,
                details=e.response.text
            )
        except requests.exceptions.RequestException as e:
            raise AIError(
                message="Connection Error",
                status_code=500,
                details=str(e)
            )

    def _parse_response(self, response_data: Dict) -> Dict:
        """تحليل الاستجابة من API"""
        try:
            content = response_data['choices'][0]['message']['content']
            return json.loads(content)
        except (KeyError, json.JSONDecodeError) as e:
            raise AIError(
                message="Invalid API Response",
                status_code=500,
                details=f"Parsing failed: {str(e)}"
            )

# تهيئة الكائن
ai = AIIntegration()
