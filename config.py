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
