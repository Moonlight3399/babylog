# ============================================================
# BabyLog - 应用工厂
# ============================================================
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import inspect, text
from werkzeug.middleware.proxy_fix import ProxyFix

from config import DATABASE_URL, EMAIL_CONFIG, SECRET_KEY

# 项目根目录（app 包的上一级，即 babylog/）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

db = SQLAlchemy()


def migrate_schema(app):
    """轻量数据库迁移：建表，并为旧版本 users 表补充 role / baby_id / identity 列"""
    with app.app_context():
        db.create_all()
        insp = inspect(db.engine)
        if 'users' in insp.get_table_names():
            cols = [c['name'] for c in insp.get_columns('users')]
            if 'role' not in cols:
                db.session.execute(text(
                    "ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'"
                ))
                print('[迁移] users 表已添加 role 列')
            if 'baby_id' not in cols:
                db.session.execute(text(
                    "ALTER TABLE users ADD COLUMN baby_id INTEGER"
                ))
                print('[迁移] users 表已添加 baby_id 列')
            if 'identity' not in cols:
                db.session.execute(text(
                    "ALTER TABLE users ADD COLUMN identity VARCHAR(20)"
                ))
                print('[迁移] users 表已添加 identity 列')
            if 'created_by' not in cols:
                db.session.execute(text(
                    "ALTER TABLE users ADD COLUMN created_by INTEGER"
                ))
                print('[迁移] users 表已添加 created_by 列')
            if 'install_guide_seen' not in cols:
                db.session.execute(text(
                    "ALTER TABLE users ADD COLUMN install_guide_seen INTEGER NOT NULL DEFAULT 0"
                ))
                print('[迁移] users 表已添加 install_guide_seen 列')
            db.session.commit()
        # records 表补充 foods 列（辅食）
        if 'records' in insp.get_table_names():
            rcols = [c['name'] for c in insp.get_columns('records')]
            if 'foods' not in rcols:
                db.session.execute(text(
                    "ALTER TABLE records ADD COLUMN foods VARCHAR(200)"
                ))
                db.session.commit()
                print('[迁移] records 表已添加 foods 列')
            if 'baby_id' not in rcols:
                db.session.execute(text(
                    "ALTER TABLE records ADD COLUMN baby_id INTEGER"
                ))
                db.session.commit()
                print('[迁移] records 表已添加 baby_id 列')
            if 'meal' not in rcols:
                db.session.execute(text(
                    "ALTER TABLE records ADD COLUMN meal VARCHAR(10)"
                ))
                db.session.commit()
                print('[迁移] records 表已添加 meal 列')
        # babies 表补充 created_by 列（创建者，仅创建者可删除）
        if 'babies' in insp.get_table_names():
            bcols = [c['name'] for c in insp.get_columns('babies')]
            if 'created_by' not in bcols:
                db.session.execute(text(
                    "ALTER TABLE babies ADD COLUMN created_by INTEGER"
                ))
                db.session.commit()
                print('[迁移] babies 表已添加 created_by 列')
            if 'birth_date' not in bcols:
                db.session.execute(text(
                    "ALTER TABLE babies ADD COLUMN birth_date DATE"
                ))
                db.session.commit()
                print('[迁移] babies 表已添加 birth_date 列')
        # growth_records 表（身高体重）
        if 'growth_records' not in insp.get_table_names():
            db.session.execute(text(
                """
                CREATE TABLE growth_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    baby_id INTEGER,
                    height REAL,
                    weight REAL,
                    record_date DATE NOT NULL,
                    created_at DATETIME
                )
                """
            ))
            db.session.commit()
            print('[迁移] 已创建 growth_records 身高体重表')


def create_app():
    app = Flask(
        __name__,
        static_folder=os.path.join(BASE_DIR, 'static'),
        template_folder=os.path.join(BASE_DIR, 'templates'),
        # 保持数据库文件位于 babylog/instance/（与拆分前一致）
        instance_path=os.path.join(BASE_DIR, 'instance'),
    )
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # 建表 + 轻量迁移（所有入口统一执行，含 gunicorn run:app）
    migrate_schema(app)

    # 反向代理（Nginx）后正确识别客户端真实 IP，用于登录限速等
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # 注册蓝图
    from .auth import auth_bp
    from .views import main_bp
    from .api import api_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # 启动后台调度器（自动备份默认开启；每日邮件可选）
    from datetime import datetime, timedelta
    from config import BACKUP_ENABLED, BACKUP_TIME

    scheduler = BackgroundScheduler()

    # 数据库自动备份：启动后立即备份一次 + 每天定时备份
    if BACKUP_ENABLED:
        from .backup import backup_database
        backup_hour, backup_minute = BACKUP_TIME.split(':')
        scheduler.add_job(
            lambda: backup_database(app),
            'cron',
            hour=int(backup_hour),
            minute=int(backup_minute),
        )
        # 服务启动后立即备份一次（覆盖服务重启前的数据变化）
        scheduler.add_job(
            lambda: backup_database(app),
            'date',
            run_date=datetime.now() + timedelta(seconds=5),
        )
        print(f'[备份] 数据库自动备份已启用 → 每天 {BACKUP_TIME}（启动时也会备份一次）')

    # 每日邮件（可选）
    if EMAIL_CONFIG.get('active'):
        from .models import User, Record
        from mailer import send_daily_email
        hour, minute = EMAIL_CONFIG['time'].split(':')
        scheduler.add_job(
            lambda: send_daily_email(app, db, User, Record),
            'cron',
            hour=int(hour),
            minute=int(minute),
        )
        print(f'[调度器] 每日邮件已启用 → 每天 {EMAIL_CONFIG["time"]}')

    if scheduler.get_jobs():
        scheduler.start()

    return app
