#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析辅食 md → data/foods.json（合并两个清单文件，归一化名称去重）

- data/婴幼儿辅食清单100种+.md（基础，分阶段）
- data/13-24月龄每月辅食清单(食物+做法).md（按月，补充新增 + 更详细做法）

用法: python3 scripts/build_foods.py
生成的 foods.json 供 /api/foods 使用（前端查辅食模块）。
"""
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC1 = os.path.join(BASE, 'data', '婴幼儿辅食清单100种+.md')
SRC2 = os.path.join(BASE, 'data', '13-24月龄每月辅食清单(食物+做法).md')
OUT = os.path.join(BASE, 'data', 'foods.json')

# 过敏源 → 关键词（按食材文本匹配；注意避免误匹配，如"母乳/土豆"）
ALLERGEN_MAP = {
    '麸质': ['面粉', '小麦', '面条', '意面', '燕麦', '全麦', '馒头', '馄饨', '饺子',
             '包子', '发糕', '松饼', '面包', '蒸糕', '蛋糕', '饼干', '炒面', '汤面', '面'],
    '鸡蛋': ['鸡蛋', '蛋黄', '蛋白', '蛋羹', '蛋卷', '蛋饺', '蛋饼', '炒蛋', '蒸蛋', '蛋液', '蛋花', '蛋'],
    '虾蟹': ['虾仁', '虾皮', '虾', '蟹'],
    '鱼': ['鳕鱼', '三文鱼', '龙利鱼', '鱼肉', '鱼块', '鱼'],
    '奶制品': ['配方奶', '牛奶', '酸奶', '奶酪', '牛乳', '奶'],
    '豆类': ['豆腐', '黄豆', '红豆', '绿豆', '豆浆', '豌豆'],
    '坚果': ['核桃', '黑芝麻', '芝麻', '花生', '杏仁', '腰果'],
}

# 非食材词（拆分后丢弃）
IGNORE_WORDS = {
    '温水', '水', '母乳', '盐', '糖', '油', '汤', '去油', '少许', '少量', '适量',
    '无糖', '极少量', '去腥', '姜', '葱花', '生抽', '低钠', '蛋液', '小火',
    '贝贝', '栗面', '干', '鲜', '白心', '苹果等', '多种蔬菜', '应季蔬菜',
    '菜', '饭', '米', '肉', '肉饼', '肉馅', '肉末', '排骨',
    '对应食材', '手指食物',
}

# 食材归一化（合并同义）
NORMALIZE = {
    '嫩豆腐': '豆腐', '鸡胸肉': '鸡肉', '牛里脊': '牛肉', '猪里脊': '猪肉',
    '燕麦片': '燕麦', '鲜虾': '虾', '虾仁': '虾', '全麦粉': '全麦',
    '熟黑芝麻': '黑芝麻', '大米/杂粮': '杂粮', '配方奶': '奶', '牛奶': '奶',
    '铁棍山药': '山药', '鲜豌豆': '豌豆', '鲜玉米': '玉米', '小米粉': '小米',
    '宝宝面': '面条', '原味酸奶': '酸奶', '无糖酸奶': '酸奶',
    '鸡蛋': '蛋', '蛋黄': '蛋', '小白菜': '油菜', '鱼肉': '鱼', '虾皮': '虾',
    '强化铁婴儿米粉': '米粉', '多种杂粮': '杂粮', '龙利鱼': '鱼',
    '猪肉末': '猪肉', '面': '面条', '皮': '面皮',
    '瘦猪肉': '猪肉', '鸡蛋黄': '蛋', '宝宝奶酪': '奶酪',
    '哈密瓜': '蜜瓜', '无麸质可用米粉': '米粉', '无麸质用米粉': '米粉', '多种已排敏软水果': '水果',
}

# 名称归一化别名（同物不同名）
NAME_ALIAS = {
    '大米小米粥': '二米粥',
}

# 食材为空时，从名称补食材（特殊辅食）
NAME_HINT = {
    '茄子丁': ['茄子'],
    '水果丁拼盘': ['水果'],
    '彩蔬小炒': ['蔬菜'],
    '清炒时蔬': ['蔬菜'],
}


def split_ingredients(text):
    parts = re.split(r'[、/，,（）()\s]+', text)
    out = []
    for p in parts:
        p = p.strip().strip('（）()')
        if not p:
            continue
        p = NORMALIZE.get(p, p)
        if p in IGNORE_WORDS or len(p) < 1:
            continue
        if p not in out:
            out.append(p)
    return out


def norm_name(n):
    """名称归一化：去★、去括号内容、别名映射（用于跨文件合并去重）"""
    n = n.replace('★', '').strip()
    n = re.sub(r'[（(][^）)]*[）)]', '', n).strip()
    n = NAME_ALIAS.get(n, n)
    return n


def make_food(min_m, max_m, stage, name, ing_text, method, notes):
    """构建单条辅食记录（含食材拆分与过敏源匹配）"""
    ingredients = split_ingredients(ing_text)
    if not ingredients:
        ingredients = list(NAME_HINT.get(norm_name(name), []))
    # 过敏源匹配：只用归一化后的食材（原文可能含'栗面'等品种词会误标'面'，
    # 归一化已过滤 IGNORE_WORDS 并把'宝宝面→面条'等统一，避免漏标/误标）
    match_text = '、'.join(ingredients)
    allergens = []
    for a, kws in ALLERGEN_MAP.items():
        if any(kw in match_text for kw in kws):
            allergens.append(a)
    return {
        'name': name.replace('★', '').strip(),
        'min_month': min_m,
        'max_month': max_m,
        'stage': stage,
        'ingredients': ingredients,
        'ingredient_text': ing_text,
        'method': method,
        'notes': notes,
        'allergens': allergens,
    }


def parse_base():
    """解析 婴幼儿辅食清单100种+.md（分阶段）→ food 列表"""
    with open(SRC1, encoding='utf-8') as f:
        lines = f.read().splitlines()

    foods = []
    stage = None  # (min, max)
    stage_label = ''
    stage_re = re.compile(r'^##\s*(\d+)\s*[-–]\s*(\d+)\s*月')
    row_re = re.compile(
        r'^\|\s*(\d+)月起\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|'
    )

    for ln in lines:
        m = stage_re.search(ln)
        if m:
            stage = (int(m.group(1)), int(m.group(2)))
            stage_label = f"{m.group(1)}-{m.group(2)}月"
            continue
        if not stage:
            continue
        r = row_re.match(ln)
        if not r:
            continue
        min_m = int(r.group(1))
        name = r.group(2).strip()
        ing_text = r.group(3).strip()
        method = r.group(4).strip()
        notes = r.group(5).strip()

        # max 月龄：阶段上限；18-24 阶段兜底到 36（>24 月仍适用）
        max_m = 36 if stage[1] >= 24 else stage[1]
        max_m = max(max_m, min_m)
        foods.append(make_food(min_m, max_m, stage_label, name, ing_text, method, notes))
    return foods


def parse_monthly():
    """解析 13-24月龄每月辅食清单(食物+做法).md（按月）→ (min_m, name, ing, method, notes) 列表"""
    with open(SRC2, encoding='utf-8') as f:
        lines = f.read().splitlines()

    rows = []
    row_re = re.compile(
        r'^\|\s*(\d+)月龄\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|'
    )
    for ln in lines:
        r = row_re.match(ln)
        if not r:
            continue
        rows.append((
            int(r.group(1)),
            r.group(2).strip(),
            r.group(3).strip(),
            r.group(4).strip(),
            r.group(5).strip(),
        ))
    return rows


def merge_and_dump():
    """合并两个文件：名称归一化去重；已存在则补充更详细做法；新增则保留新文件月龄"""
    by_key = {}
    for f in parse_base():
        by_key[norm_name(f['name'])] = f

    added = 0
    enriched = 0
    for (min_m, name, ing_text, method, notes) in parse_monthly():
        key = norm_name(name)
        if key in by_key:
            old = by_key[key]
            if len(method) > len(old['method']):
                old['method'] = method
            if len(notes) > len(old['notes']):
                old['notes'] = notes
            enriched += 1
        else:
            max_m = 36
            stage = f'{min_m}月龄'
            by_key[key] = make_food(min_m, max_m, stage, name, ing_text, method, notes)
            added += 1

    foods = list(by_key.values())
    for i, f in enumerate(foods):
        f['id'] = i + 1

    # 可选食材集合（保留出现顺序）
    ing_set = []
    for f in foods:
        for i in f['ingredients']:
            if i not in ing_set:
                ing_set.append(i)

    data = {
        'foods': foods,
        'allergens': list(ALLERGEN_MAP.keys()),
        'ingredients': ing_set,
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print(f'基础文件 {len(parse_base())} 条 + 月龄文件去重后新增 {added} 条 → 共 {len(foods)} 条')
    print(f'做法补充/比对（新文件与已有匹配）: {enriched} 条')
    print('过敏源分布:', {a: sum(1 for x in foods if a in x['allergens']) for a in ALLERGEN_MAP})
    print('食材:', '、'.join(ing_set))
    return data


if __name__ == '__main__':
    merge_and_dump()
