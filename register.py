"""
BabyLog 用户注册脚本

运行方式:
    python register.py                          # 交互式注册
    python register.py <用户名> <密码>           # 命令行注册（普通用户）
    python register.py <用户名> <密码> --admin   # 命令行注册（管理员）
"""
import hashlib
import secrets
import sys

from app import create_app, db, migrate_schema
from app.models import User
from app.auth import hash_password

app = create_app()


def register(username, password, role='user'):
    with app.app_context():
        migrate_schema(app)
        existing = User.query.filter_by(username=username).first()
        if existing:
            print(f'[!] 用户 "{username}" 已存在！')
            return False
        pw = hash_password(password)
        user = User(username=username, password_hash=pw, salt='', role=role)
        db.session.add(user)
        db.session.commit()
        role_cn = '管理员' if role == 'admin' else '普通用户'
        print(f'[✓] 用户 "{username}"（{role_cn}）注册成功！')
        return True


def interactive():
    print('=' * 40)
    print('  BabyLog - 用户注册')
    print('=' * 40)
    username = input('请输入用户名: ').strip()
    if not username:
        print('[!] 用户名不能为空')
        return
    password = input('请输入密码: ')
    if not password:
        print('[!] 密码不能为空')
        return
    role_input = input('角色（输入 admin 创建管理员，直接回车创建普通用户）: ').strip()
    role = 'admin' if role_input == 'admin' else 'user'
    register(username, password, role)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--admin']
    is_admin = '--admin' in sys.argv[1:]
    if len(args) == 2:
        register(args[0], args[1], 'admin' if is_admin else 'user')
    else:
        interactive()
