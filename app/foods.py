# ============================================================
# BabyLog - 辅食查询数据（读 data/foods.json）
# ============================================================
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOODS_FILE = os.path.join(BASE_DIR, 'data', 'foods.json')

_cache = None


def load_foods():
    """读取辅食数据（进程内缓存；改 foods.json 后需重启服务）"""
    global _cache
    if _cache is None:
        with open(FOODS_FILE, 'r', encoding='utf-8') as f:
            _cache = json.load(f)
    return _cache
