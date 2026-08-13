# ============================================================
# BabyLog - 服务运行配置（支持多实例 / 新旧版本共存）
# ============================================================
import os

# 服务监听端口：默认 5001（避开旧版本默认 5000），可用环境变量 PORT 覆盖
PORT = int(os.environ.get('PORT', '5001'))

# SQLite 数据库文件名或路径：默认 babylog_new.db（位于 instance/ 目录，避开旧版本 babylog.db）
# 可通过环境变量 BABYLOG_DB 覆盖，实现多实例数据隔离
#   相对路径: BABYLOG_DB=babylog_v3.db   -> instance/babylog_v3.db
#   绝对路径: BABYLOG_DB=/data/babylog.db
BABYLOG_DB = os.environ.get('BABYLOG_DB', 'babylog_new.db')
DATABASE_URL = f'sqlite:///{BABYLOG_DB}'

# ============================================================
# BabyLog - 会话安全配置
# ============================================================

# 会话签名密钥：用于给登录 session cookie 签名
# - 环境变量 SECRET_KEY 优先（部署时务必设置，见《部署公网加固清单》第 2 步）
# - 下方默认值为“开发默认”，仅供本地使用；部署到服务器前请重新生成并覆盖，切勿提交真实密钥到公开仓库
# - 生成新密钥: python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'babylog-dev-default-secret-key-please-replace-in-production-00000000',
)

# 是否给 session cookie 加 Secure 标志（仅 HTTPS 下应开启）
# - 服务器启用 HTTPS 后设置环境变量 BABYLOG_COOKIE_SECURE=1（见《部署公网加固清单》第 7 步）
# - 本地 http 开发环境不要开启，否则登录 cookie 无法保存
COOKIE_SECURE = os.environ.get('BABYLOG_COOKIE_SECURE', '0') in ('1', 'true', 'yes')

# ============================================================
# BabyLog - 数据库自动备份配置
# ============================================================

# 是否启用数据库自动备份（默认开启）
BACKUP_ENABLED = os.environ.get('BABYLOG_BACKUP_ENABLED', 'true').lower() in ('1', 'true', 'yes')

# 备份目录：默认 instance/backups（相对项目根目录）；可用 BABYLOG_BACKUP_DIR 覆盖为绝对路径
BACKUP_DIR = os.environ.get('BABYLOG_BACKUP_DIR', os.path.join('instance', 'backups'))

# 每天备份时间 (格式 HH:MM，建议选在家人不使用的时间段)
BACKUP_TIME = '03:30'

# 备份保留天数（超过自动清理）
BACKUP_RETENTION_DAYS = 30


# ============================================================
# BabyLog - 每日邮件提醒配置
# ============================================================

EMAIL_CONFIG = {
    # 是否启用每日邮件
    'active': False,

    # 每天发送时间 (格式 HH:MM，如 "10:00")
    'time': '06:00',

    # 宝宝出生日期
    'baby_birth_date': '2026-01-01',

    # SMTP 发件服务器
    'smtp': {
        'server': 'smtp.example.com',
        'port': 465,  # 465=SSL, 587=STARTTLS
        'email': 'your_email@example.com',       # 登录账号
        'password': 'your_password',
        'from': 'BabyLog <your_email@example.com>',                        # 发件人显示地址（留空则用 email）
    },

    # 收件邮箱（多个用逗号隔开）
    'recipient': 'recipient@example.com',

    # AI 配置 (OpenAI 兼容接口)
    'ai': {
        'server': 'https://api.deepseek.com',
        'api_key': 'sk-your-api-key',
        'model': 'deepseek-chat',
    },
}
