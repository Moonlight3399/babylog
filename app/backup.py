# ============================================================
# BabyLog - 数据库自动备份
# ============================================================
import os
import sqlite3
from datetime import datetime, timedelta

from config import BACKUP_DIR, BACKUP_RETENTION_DAYS

# 项目根目录（app 包的上一级，即 babylog/）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def backup_database(app):
    """在线备份 SQLite 数据库到备份目录，并清理过期备份。失败不中断服务。"""
    try:
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        db_name = db_uri.replace('sqlite:///', '')
        db_path = os.path.join(app.instance_path, db_name)
        if not os.path.exists(db_path):
            print('[备份] 数据库文件不存在，跳过本次备份')
            return

        backup_dir = BACKUP_DIR
        if not os.path.isabs(backup_dir):
            backup_dir = os.path.join(BASE_DIR, backup_dir)
        os.makedirs(backup_dir, exist_ok=True)

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        dest = os.path.join(backup_dir, f'babylog_{ts}.db')

        # 使用 SQLite 在线备份 API，保证备份文件一致性
        src = sqlite3.connect(db_path)
        dst = sqlite3.connect(dest)
        src.backup(dst)
        dst.close()
        src.close()

        # 清理过期备份（按文件修改时间）
        cutoff = datetime.now() - timedelta(days=BACKUP_RETENTION_DAYS)
        removed = 0
        for f in os.listdir(backup_dir):
            if f.startswith('babylog_') and f.endswith('.db'):
                fp = os.path.join(backup_dir, f)
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(fp))
                except OSError:
                    continue
                if mtime < cutoff:
                    os.remove(fp)
                    removed += 1

        print(f'[备份] 已备份 → {dest}（本次清理过期 {removed} 个）')
    except Exception as e:
        print(f'[备份] 失败: {e}')
