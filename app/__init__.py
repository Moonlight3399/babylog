# ============================================================
# BabyLog - 应用工厂
# ============================================================
import os
import secrets

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import inspect, text

from config import DATABASE_URL, EMAIL_CONFIG

# 项目根目录（app 包的上一级，即 babylog/）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

db = SQLAlchemy()


def migrate_schema(app):
    """轻量数据库迁移：建表，并为旧版本 users 表补充 role 列（区分管理员/普通用户）"""
    with app.app_context():
        db.create_all()
        insp = inspect(db.engine)
        if 'users' in insp.get_table_names():
            cols = [c['name'] for c in insp.get_columns('users')]
            if 'role' not in cols:
                db.session.execute(text(
                    "ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'"
                ))
                db.session.commit()
                print('[迁移] users 表已添加 role 列')


def create_app():
    app = Flask(
        __name__,
        static_folder=os.path.join(BASE_DIR, 'static'),
        template_folder=os.path.join(BASE_DIR, 'templates'),
        # 保持数据库文件位于 babylog/instance/（与拆分前一致）
        instance_path=os.path.join(BASE_DIR, 'instance'),
    )
    app.config['SECRET_KEY'] = secrets.token_hex(32)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # 注册蓝图
    from .auth import auth_bp
    from .views import main_bp
    from .api import api_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # 启动每日邮件调度器
    if EMAIL_CONFIG.get('active'):
        from .models import User, Record
        from mailer import send_daily_email

        scheduler = BackgroundScheduler()
        hour, minute = EMAIL_CONFIG['time'].split(':')
        scheduler.add_job(
            lambda: send_daily_email(app, db, User, Record),
            'cron',
            hour=int(hour),
            minute=int(minute),
        )
        scheduler.start()
        print(f'[调度器] 每日邮件已启用 → 每天 {EMAIL_CONFIG["time"]}')

    return app
