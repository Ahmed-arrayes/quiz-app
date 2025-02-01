# app.py

from flask import Flask
from config import Config  # استيراد Config

# إنشاء تطبيق Flask
app = Flask(__name__)
app.config.from_object(Config)  # تحميل التكوين من Config

# تهيئة الإضافات
from extensions import db, login_manager

db.init_app(app)
login_manager.init_app(app)

# تسجيل الـ Blueprints
from routes import main_bp, auth_bp, quiz_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(quiz_bp)

if __name__ == '__main__':
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'])
