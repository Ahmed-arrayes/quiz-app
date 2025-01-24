import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "default_secret_key")
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False