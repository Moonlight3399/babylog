# ============================================================
# BabyLog - 育儿小知识（按宝宝年龄推荐 + 特殊日祝贺）
# ============================================================
import json
import os
from datetime import date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIPS_FILE = os.path.join(BASE_DIR, 'data', 'tips.json')

_stages = None


def _load_stages():
    global _stages
    if _stages is None:
        with open(TIPS_FILE, 'r', encoding='utf-8') as f:
            _stages = json.load(f).get('stages', [])
    return _stages


def days_since_birth(birth_date, today=None):
    """返回出生到今天的天数"""
    today = today or date.today()
    return (today - birth_date).days


def stage_for_days(days):
    """根据出生天数找到所属阶段"""
    for s in _load_stages():
        if s['min_days'] <= days <= s['max_days']:
            return s
    return None


def special_day(days):
    """特殊纪念日检测：百天 / 周岁 / 满月，返回祝贺语或 None"""
    if days == 100:
        return '🎉 宝宝百天啦！百日宴祝福，愿宝宝健康快乐成长！'
    if days > 0 and days % 365 == 0:
        years = days // 365
        return f'🎂 宝宝{years}周岁啦！愿宝贝健康、快乐、平安地长大！'
    if days > 0 and days % 30 == 0 and days <= 360:
        n = days // 30
        return f'🎉 宝宝满{n}个月啦！又长大了一点，继续加油！'
    return None


def get_daily_tip(birth_date, today=None):
    """根据宝宝生日返回：所属阶段、今日小知识、特殊日祝贺、天数/月数"""
    today = today or date.today()
    if not birth_date:
        return {'available': False, 'reason': '未设置宝宝生日，无法推荐小知识'}

    days = max(0, days_since_birth(birth_date, today))
    # 自然月数
    months = (today.year - birth_date.year) * 12 + (today.month - birth_date.month)
    if today.day < birth_date.day:
        months -= 1
    months = max(0, months)

    stage = stage_for_days(days)
    if not stage:
        return {'available': False, 'reason': '暂无适配的小知识', 'days': days, 'months': months}

    # 按天固定选取（同一天返回同一条，避免刷新就变）
    idx = (days * 7 + 13) % len(stage['tips'])
    tip = stage['tips'][idx]

    return {
        'available': True,
        'stage': stage['name'],
        'tip': tip,
        'special': special_day(days),
        'days': days,
        'months': months,
    }
