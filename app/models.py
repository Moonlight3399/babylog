# ============================================================
# BabyLog - 数据模型
# ============================================================
from datetime import datetime

from . import db


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    salt = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin' | 'user'
    baby_id = db.Column(db.Integer, db.ForeignKey('babies.id'), nullable=True)  # 关联宝宝
    identity = db.Column(db.String(20), nullable=True)  # 爸爸/妈妈/爷爷/奶奶/外公/外婆
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Baby(db.Model):
    __tablename__ = 'babies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Record(db.Model):
    __tablename__ = 'records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_type = db.Column(db.String(20), nullable=False)
    # event_type: 'formula' | 'solid' | 'sleep_start' | 'sleep_end' | 'poop' | 'pee'(旧)
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.Time, nullable=False)
    formula_amount = db.Column(db.Integer, nullable=True)
    foods = db.Column(db.String(200), nullable=True)  # 辅食食物列表（逗号分隔）
    baby_id = db.Column(db.Integer, db.ForeignKey('babies.id'), nullable=True)  # 所属宝宝
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Food(db.Model):
    """用户自定义常用辅食"""
    __tablename__ = 'custom_foods'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
