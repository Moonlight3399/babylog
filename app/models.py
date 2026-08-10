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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Record(db.Model):
    __tablename__ = 'records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_type = db.Column(db.String(20), nullable=False)
    # event_type: 'formula' | 'sleep_start' | 'sleep_end' | 'poop' | 'pee'
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.Time, nullable=False)
    formula_amount = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
