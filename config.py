import os
from dotenv import load_dotenv


load_dotenv()

class Config:
    # إعدادات الأمان الأساسية
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', os.getenv('SECRET_KEY', 'default-secret-key'))
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    # إعدادات قاعدة البيانات
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # إعدادات الذكاء الاصطناعي
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    
    # إعدادات الخادم
    HOST = os.getenv('HOST', '127.0.0.1')
    PORT = int(os.getenv('PORT', 5000))