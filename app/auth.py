# ============================================================
# BabyLog - 认证辅助函数与登录相关路由
# ============================================================
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps

from flask import (Blueprint, current_app, jsonify, redirect,
                   render_template, request, url_for)

from . import db
from .models import Record, User

auth_bp = Blueprint('auth', __name__)


# ------------------------------------------------------------
# 认证辅助函数
# ------------------------------------------------------------
def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return salt + ':' + key.hex()


def verify_password(stored, password):
    salt, hash_val = stored.split(':', 1)
    return hash_password(password, salt) == stored


def get_user_from_cookie():
    token = request.cookies.get('session')
    if not token:
        return None
    parts = token.split(':', 2)
    if len(parts) != 3:
        return None
    user_id, expires_str, sig = parts
    try:
        expires = float(expires_str)
    except ValueError:
        return None
    if datetime.utcnow().timestamp() > expires:
        return None
    expected = hashlib.sha256(
        f"{user_id}:{expires_str}:{current_app.config['SECRET_KEY']}".encode()
    ).hexdigest()
    if not secrets.compare_digest(sig, expected):
        return None
    return User.query.get(int(user_id))


def make_session_cookie(user_id, days=30):
    expires = datetime.utcnow() + timedelta(days=days)
    expires_ts = expires.timestamp()
    sig = hashlib.sha256(
        f"{user_id}:{expires_ts}:{current_app.config['SECRET_KEY']}".encode()
    ).hexdigest()
    return f"{user_id}:{expires_ts}:{sig}", expires


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_user_from_cookie()
        if not user:
            if request.path.startswith('/api/'):
                return jsonify({'error': '未登录'}), 401
            return redirect(url_for('auth.login_page'))
        return f(user, *args, **kwargs)
    return decorated


def admin_required(f):
    """仅管理员可访问的装饰器（需同时满足登录 + 角色为 admin）"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_user_from_cookie()
        if not user:
            if request.path.startswith('/api/'):
                return jsonify({'error': '未登录'}), 401
            return redirect(url_for('auth.login_page'))
        if getattr(user, 'role', 'user') != 'admin':
            return jsonify({'error': '无权限，仅管理员可操作'}), 403
        return f(user, *args, **kwargs)
    return decorated


# ------------------------------------------------------------
# 登录页面
# ------------------------------------------------------------
@auth_bp.route('/login')
def login_page():
    user = get_user_from_cookie()
    if user:
        return redirect(url_for('main.index'))
    return render_template('login.html')


# ------------------------------------------------------------
# 认证 API
# ------------------------------------------------------------
@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify({'error': '请提供用户名和密码'}), 400
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not verify_password(user.password_hash, password):
        return jsonify({'error': '用户名或密码错误'}), 401

    token, expires = make_session_cookie(user.id)
    resp = jsonify({'ok': True, 'username': user.username})
    resp.set_cookie('session', token, expires=expires, httponly=True, samesite='Lax', secure=False)
    return resp


@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    resp = jsonify({'ok': True})
    resp.delete_cookie('session')
    return resp


@auth_bp.route('/api/user')
@login_required
def api_user(user):
    return jsonify({
        'username': user.username,
        'role': user.role,
        'created_at': user.created_at.isoformat(),
    })


# ------------------------------------------------------------
# 注册
# ------------------------------------------------------------
@auth_bp.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    if not data:
        return jsonify({'error': '请提供用户名和密码'}), 400
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    if len(username) < 2 or len(username) > 20:
        return jsonify({'error': '用户名长度需为 2-20 个字符'}), 400
    if len(password) < 6:
        return jsonify({'error': '密码长度至少 6 位'}), 400

    existing = User.query.filter_by(username=username).first()
    if existing:
        return jsonify({'error': '用户名已存在'}), 400

    user = User(username=username, password_hash=hash_password(password), salt='', role='user')
    db.session.add(user)
    db.session.commit()

    # 注册成功后自动登录
    token, expires = make_session_cookie(user.id)
    resp = jsonify({'ok': True, 'username': user.username, 'role': user.role})
    resp.set_cookie('session', token, expires=expires, httponly=True, samesite='Lax', secure=False)
    return resp, 201


# ------------------------------------------------------------
# 管理员：用户管理
# ------------------------------------------------------------
@auth_bp.route('/api/admin/users')
@admin_required
def api_admin_users(admin):
    users = User.query.order_by(User.id.asc()).all()
    return jsonify({
        'users': [
            {
                'id': u.id,
                'username': u.username,
                'role': u.role,
                'created_at': u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]
    })


@auth_bp.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def api_admin_delete_user(admin, user_id):
    target = User.query.get(user_id)
    if not target:
        return jsonify({'error': '用户不存在'}), 404
    if target.id == admin.id:
        return jsonify({'error': '不能删除当前登录的管理员账号'}), 400
    Record.query.filter_by(user_id=target.id).delete()
    db.session.delete(target)
    db.session.commit()
    return jsonify({'ok': True})
