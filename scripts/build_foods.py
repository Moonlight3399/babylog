#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析 data/婴幼儿辅食清单100种+.md → data/foods.json

用法: python3 scripts/build_foods.py
生成的 foods.json 供 /api/foods 使用（前端查辅食模块）。
"""
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, 'data', '婴幼儿辅食清单100种+.md')
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
    '菜', '饭', '米', '皮', '肉', '肉饼', '肉馅', '肉末', '排骨',
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
    '猪肉末': '猪肉', '面': '面条',
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


def parse():
    with open(SRC, encoding='utf-8') as f:
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

        ingredients = split_ingredients(ing_text)
        # 过敏源匹配：只用归一化后的食材（原文可能含'栗面'等品种词会误标'面'，
        # 归一化已过滤 IGNORE_WORDS 并把'宝宝面→面条'等统一，避免漏标/误标）
        match_text = '、'.join(ingredients)
        allergens = []
        for a, kws in ALLERGEN_MAP.items():
            if any(kw in match_text for kw in kws):
                allergens.append(a)

        foods.append({
            'id': len(foods) + 1,
            'name': name,
            'min_month': min_m,
            'max_month': max_m,
            'stage': stage_label,
            'ingredients': ingredients,
            'ingredient_text': ing_text,
            'method': method,
            'notes': notes,
            'allergens': allergens,
        })

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

    print(f'解析 {len(foods)} 条辅食，可选食材 {len(ing_set)} 种')
    print('过敏源分布:', {a: sum(1 for x in foods if a in x['allergens']) for a in ALLERGEN_MAP})
    print('食材:', '、'.join(ing_set))
    return data


if __name__ == '__main__':
    parse()
