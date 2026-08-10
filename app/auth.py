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
from .models import Baby, LoginAttempt, Record, User

auth_bp = Blueprint('auth', __name__)

# 用户可设置的家庭身份
IDENTITIES = ('爸爸', '妈妈', '爷爷', '奶奶', '外公', '外婆')


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
# 登录限速（防暴力破解）：同一 用户名|IP 失败 5 次锁定 15 分钟
# 使用数据库持久化（login_attempts 表），跨进程/重启依然有效
_MAX_FAIL = 5
_LOCK_SEC = 15 * 60


def _login_key(username):
    return f"{username}|{request.remote_addr or ''}"


def _is_locked(key):
    a = LoginAttempt.query.filter_by(key=key).first()
    if a and a.locked_until and a.locked_until > datetime.utcnow():
        return True
    return False


def _record_fail(key):
    now = datetime.utcnow()
    a = LoginAttempt.query.filter_by(key=key).first()
    if not a:
        a = LoginAttempt(key=key, fail_count=0, last_fail=None, locked_until=None)
        db.session.add(a)
    # 滑动窗口：距上次失败超过锁定周期则重新计数
    if a.last_fail and (now - a.last_fail).total_seconds() > _LOCK_SEC:
        a.fail_count = 0
    a.fail_count += 1
    a.last_fail = now
    if a.fail_count >= _MAX_FAIL:
        a.locked_until = now + timedelta(seconds=_LOCK_SEC)
        a.fail_count = 0
    db.session.commit()


def _clear_fails(key):
    LoginAttempt.query.filter_by(key=key).delete()
    db.session.commit()


@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify({'error': '请提供用户名和密码'}), 400
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400

    # 限速：锁定期间直接拒绝
    key = _login_key(username)
    if _is_locked(key):
        return jsonify({'error': f'尝试次数过多，请 {_LOCK_SEC // 60} 分钟后再试'}), 429

    user = User.query.filter_by(username=username).first()
    if not user or not verify_password(user.password_hash, password):
        _record_fail(key)
        return jsonify({'error': '用户名或密码错误'}), 401

    # 登录成功，清除失败记录
    _clear_fails(key)
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
    baby = Baby.query.get(user.baby_id) if user.baby_id else None
    return jsonify({
        'username': user.username,
        'role': user.role,
        'identity': user.identity,
        'baby': {'id': baby.id, 'name': baby.name} if baby else None,
        'created_at': user.created_at.isoformat(),
    })


# ------------------------------------------------------------
# 注册（仅管理员可用：在管理界面手动添加用户）
# ------------------------------------------------------------
@auth_bp.route('/api/register', methods=['POST'])
@admin_required
def api_register(admin):
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
    return jsonify({'ok': True, 'username': user.username}), 201


# ------------------------------------------------------------
# 管理员：用户管理
# ------------------------------------------------------------
@auth_bp.route('/api/admin/users')
@admin_required
def api_admin_users(admin):
    users = User.query.order_by(User.id.asc()).all()
    baby_map = {b.id: b.name for b in Baby.query.all()}
    return jsonify({
        'users': [
            {
                'id': u.id,
                'username': u.username,
                'role': u.role,
                'identity': u.identity,
                'baby_id': u.baby_id,
                'baby_name': baby_map.get(u.baby_id),
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


@auth_bp.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@admin_required
def api_admin_update_user(admin, user_id):
    """管理员为用户设置身份/关联宝宝/角色（可设另一用户为管理员）"""
    target = User.query.get(user_id)
    if not target:
        return jsonify({'error': '用户不存在'}), 404
    data = request.get_json() or {}
    role = data.get('role')
    identity = (data.get('identity') or '').strip()
    baby_id = data.get('baby_id')

    # 角色变更：仅当角色值实际变化时才处理（管理员可设置其他用户为管理员）
    if role is not None and role != target.role:
        if role not in ('admin', 'user'):
            return jsonify({'error': '无效的角色'}), 400
        if target.id == admin.id:
            return jsonify({'error': '不能修改自己的角色'}), 400
        if target.role == 'admin' and role == 'user':
            admin_count = User.query.filter_by(role='admin').count()
            if admin_count <= 1:
                return jsonify({'error': '至少保留一名管理员'}), 400
        target.role = role

    if identity and identity not in IDENTITIES:
        return jsonify({'error': '无效的身份，可选：爸爸/妈妈/爷爷/奶奶/外公/外婆'}), 400
    if baby_id:
        baby = Baby.query.get(int(baby_id))
        if not baby:
            return jsonify({'error': '宝宝不存在'}), 404
        target.baby_id = baby.id
    else:
        target.baby_id = None
    target.identity = identity or None
    db.session.commit()
    baby = Baby.query.get(target.baby_id) if target.baby_id else None
    return jsonify({
        'ok': True,
        'role': target.role,
        'identity': target.identity,
        'baby': {'id': baby.id, 'name': baby.name} if baby else None,
    })


# ------------------------------------------------------------
# 用户：查看宝宝列表 / 设置自己的身份
# ------------------------------------------------------------
@auth_bp.route('/api/babies')
@login_required
def api_babies(user):
    """用户只能看到自己绑定的宝宝"""
    babies = [Baby.query.get(user.baby_id)] if user.baby_id else []
    return jsonify({
        'babies': [{'id': b.id, 'name': b.name} for b in babies if b]
    })


@auth_bp.route('/api/user/profile', methods=['PUT'])
@login_required
def api_user_profile(user):
    """用户设置自己的身份（宝宝由管理员绑定，用户不可自行更改）"""
    data = request.get_json() or {}
    identity = (data.get('identity') or '').strip()
    if identity and identity not in IDENTITIES:
        return jsonify({'error': '无效的身份，可选：爸爸/妈妈/爷爷/奶奶/外公/外婆'}), 400
    user.identity = identity or None
    db.session.commit()
    baby = Baby.query.get(user.baby_id) if user.baby_id else None
    return jsonify({
        'ok': True,
        'identity': user.identity,
        'baby': {'id': baby.id, 'name': baby.name} if baby else None,
    })


@auth_bp.route('/api/user/password', methods=['PUT'])
@login_required
def api_change_password(user):
    """用户修改自己的密码（需验证旧密码）"""
    data = request.get_json() or {}
    old_pw = data.get('old_password', '')
    new_pw = data.get('new_password', '')
    if not old_pw or not new_pw:
        return jsonify({'error': '请填写当前密码和新密码'}), 400
    if len(new_pw) < 6:
        return jsonify({'error': '新密码长度至少 6 位'}), 400
    if not verify_password(user.password_hash, old_pw):
        return jsonify({'error': '当前密码错误'}), 400
    user.password_hash = hash_password(new_pw)
    db.session.commit()
    return jsonify({'ok': True})


# ------------------------------------------------------------
# 管理员：宝宝管理
# ------------------------------------------------------------
@auth_bp.route('/api/admin/babies')
@admin_required
def api_admin_babies(admin):
    babies = Baby.query.order_by(Baby.id.asc()).all()
    return jsonify({
        'babies': [{
            'id': b.id,
            'name': b.name,
            'user_count': User.query.filter_by(baby_id=b.id).count(),
        } for b in babies]
    })


@auth_bp.route('/api/admin/babies', methods=['POST'])
@admin_required
def api_admin_add_baby(admin):
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': '宝宝名字不能为空'}), 400
    if len(name) > 20:
        return jsonify({'error': '宝宝名字过长'}), 400
    baby = Baby(name=name)
    db.session.add(baby)
    db.session.commit()
    return jsonify({'ok': True, 'baby': {'id': baby.id, 'name': baby.name}}), 201


@auth_bp.route('/api/admin/babies/<int:baby_id>', methods=['DELETE'])
@admin_required
def api_admin_delete_baby(admin, baby_id):
    baby = Baby.query.get(baby_id)
    if not baby:
        return jsonify({'error': '宝宝不存在'}), 404
    # 解除与该宝宝关联的用户
    User.query.filter_by(baby_id=baby_id).update({'baby_id': None})
    db.session.delete(baby)
    db.session.commit()
    return jsonify({'ok': True})
