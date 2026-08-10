# ============================================================
# BabyLog - API 路由
# ============================================================
import csv
import io
from collections import defaultdict
from datetime import datetime
from urllib.parse import quote

from flask import (Blueprint, current_app, jsonify, make_response,
                   request, send_from_directory)

from . import db
from .models import Food, GrowthRecord, Record
from .auth import login_required

api_bp = Blueprint('api', __name__)

LABEL_MAP = {
    'formula': '喝奶粉',
    'solid': '吃辅食',
    'sleep_start': '开始睡',
    'sleep_end': '睡醒了',
    'poop': '拉粑粑',
    'pee': '小便了',  # 兼容历史数据展示
}


# ------------------------------------------------------------
# 记录：新增 / 修改 / 删除 / 撤回
# ------------------------------------------------------------
@api_bp.route('/api/record', methods=['POST'])
@login_required
def api_create_record(user):
    data = request.get_json()
    if not data:
        return jsonify({'error': '无效请求'}), 400

    event_type = data.get('event_type', '').strip()
    valid_types = {'formula', 'solid', 'sleep_start', 'sleep_end', 'poop'}
    if event_type not in valid_types:
        return jsonify({'error': '无效的事件类型'}), 400

    # 支持手动指定日期和时间，否则使用当前时间
    event_date = data.get('event_date', '').strip()
    event_time = data.get('event_time', '').strip()
    if event_date and event_time:
        try:
            event_date = datetime.strptime(event_date, '%Y-%m-%d').date()
            event_time = datetime.strptime(event_time, '%H:%M').time()
        except ValueError:
            return jsonify({'error': '日期或时间格式错误'}), 400
    else:
        now = datetime.now()
        event_date = now.date()
        event_time = now.time().replace(microsecond=0)

    # 必须绑定宝宝后才能记录（宝宝由管理员绑定）
    if not user.baby_id:
        return jsonify({'error': '请先由管理员绑定宝宝，才能记录'}), 403

    record = Record(
        user_id=user.id,
        baby_id=user.baby_id,
        event_type=event_type,
        event_date=event_date,
        event_time=event_time,
        formula_amount=None,
    )

    # 辅食：食物列表（逗号分隔存储）
    if event_type == 'solid':
        foods = data.get('foods')
        if foods is not None:
            if not isinstance(foods, list):
                return jsonify({'error': '辅食参数格式错误'}), 400
            cleaned = []
            for f in foods[:10]:
                f = str(f).strip()
                if f and f not in cleaned and len(f) <= 20:
                    cleaned.append(f)
            record.foods = ','.join(cleaned)

    # 睡眠约束：检查是否存在未配对的睡眠记录（跨所有日期）
    if event_type == 'sleep_start':
        sleep_start_count = Record.query.filter_by(user_id=user.id, event_type='sleep_start').count()
        sleep_end_count = Record.query.filter_by(user_id=user.id, event_type='sleep_end').count()
        if sleep_start_count > sleep_end_count:
            return jsonify({'error': '当前有未结束的睡眠，请先"睡醒了"再开始新的睡眠'}), 400

    if event_type == 'sleep_end':
        sleep_start_count = Record.query.filter_by(user_id=user.id, event_type='sleep_start').count()
        sleep_end_count = Record.query.filter_by(user_id=user.id, event_type='sleep_end').count()
        if sleep_start_count <= sleep_end_count:
            return jsonify({'error': '还没有"开始睡"记录，无法"睡醒了"'}), 400

    if event_type == 'formula':
        amount = data.get('formula_amount')
        if amount is None:
            return jsonify({'error': '请填写奶粉量'}), 400
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            return jsonify({'error': '奶粉量必须为数字'}), 400
        if amount <= 0:
            return jsonify({'error': '奶粉量必须大于0'}), 400
        record.formula_amount = amount

    db.session.add(record)
    db.session.commit()

    return jsonify({
        'ok': True,
        'record': {
            'id': record.id,
            'baby_id': record.baby_id,
            'event_type': record.event_type,
            'event_label': LABEL_MAP.get(record.event_type, record.event_type),
            'event_date': str(record.event_date),
            'event_time': str(record.event_time),
            'formula_amount': record.formula_amount,
            'foods': record.foods.split(',') if record.foods else [],
        }
    })


@api_bp.route('/api/record/<int:record_id>', methods=['PUT'])
@login_required
def api_update_record(user, record_id):
    record = Record.query.filter_by(id=record_id, user_id=user.id).first()
    if not record:
        return jsonify({'error': '记录不存在'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': '无效请求'}), 400

    new_time_str = data.get('event_time', '').strip()
    try:
        new_time = datetime.strptime(new_time_str, '%H:%M').time()
    except ValueError:
        return jsonify({'error': '时间格式错误，请使用 HH:MM'}), 400

    record.event_time = new_time
    db.session.commit()

    return jsonify({
        'ok': True,
        'record': {
            'id': record.id,
            'baby_id': record.baby_id,
            'event_type': record.event_type,
            'event_label': LABEL_MAP.get(record.event_type, record.event_type),
            'event_date': str(record.event_date),
            'event_time': str(record.event_time),
            'formula_amount': record.formula_amount,
            'foods': record.foods.split(',') if record.foods else [],
        }
    })


@api_bp.route('/api/record/<int:record_id>', methods=['DELETE'])
@login_required
def api_delete_record(user, record_id):
    record = Record.query.filter_by(id=record_id, user_id=user.id).first()
    if not record:
        return jsonify({'error': '记录不存在'}), 404

    db.session.delete(record)
    db.session.commit()
    return jsonify({'ok': True})


@api_bp.route('/api/record/undo', methods=['POST'])
@login_required
def api_undo_record(user):
    last_record = Record.query.filter_by(user_id=user.id, baby_id=user.baby_id)\
        .order_by(Record.id.desc()).first()

    if not last_record:
        return jsonify({'error': '没有可撤回的记录'}), 404

    diff = (datetime.utcnow() - last_record.created_at).total_seconds()
    if diff > 15:
        return jsonify({'error': '已超过撤回时间（15秒）'}), 400

    db.session.delete(last_record)
    db.session.commit()
    return jsonify({'ok': True})


# ------------------------------------------------------------
# 查询：某日记录列表 / 某日统计
# ------------------------------------------------------------
@api_bp.route('/api/records')
@login_required
def api_records(user):
    date_str = request.args.get('date')
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': '日期格式错误'}), 400

    records = Record.query.filter_by(user_id=user.id, baby_id=user.baby_id, event_date=date)\
                          .order_by(Record.event_time.asc()).all()

    return jsonify({
        'date': str(date),
        'records': [
            {
                'id': r.id,
                'baby_id': r.baby_id,
                'event_type': r.event_type,
                'event_label': LABEL_MAP.get(r.event_type, r.event_type),
                'event_time': str(r.event_time),
                'formula_amount': r.formula_amount,
                'foods': r.foods.split(',') if r.foods else [],
            }
            for r in records
        ]
    })


@api_bp.route('/api/stats')
@login_required
def api_stats(user):
    date_str = request.args.get('date')
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': '日期格式错误'}), 400

    records = Record.query.filter_by(user_id=user.id, baby_id=user.baby_id, event_date=date)\
                          .order_by(Record.event_time.asc()).all()

    total_formula = sum(r.formula_amount for r in records if r.event_type == 'formula' and r.formula_amount)
    count_formula = sum(1 for r in records if r.event_type == 'formula')
    count_solid = sum(1 for r in records if r.event_type == 'solid')
    count_poop = sum(1 for r in records if r.event_type == 'poop')
    count_pee = sum(1 for r in records if r.event_type == 'pee')

    # 计算睡眠总时长：按时间顺序配对 sleep_start 和 sleep_end
    total_sleep_minutes = 0
    sleep_count = 0
    pending_start = None  # 当前未配对的开始睡时间

    # 从数据库中获取该用户跨所有日期的睡眠记录，以便正确配对（考虑跨天睡眠）
    all_sleep = Record.query.filter(
        Record.user_id == user.id,
        Record.baby_id == user.baby_id,
        Record.event_type.in_(['sleep_start', 'sleep_end']),
        Record.event_date <= date
    ).order_by(Record.event_date.asc(), Record.event_time.asc()).all()

    for r in all_sleep:
        if r.event_type == 'sleep_start':
            pending_start = r
        elif r.event_type == 'sleep_end' and pending_start is not None:
            # 计算时间差（分钟）
            start_dt = datetime.combine(pending_start.event_date, pending_start.event_time)
            end_dt = datetime.combine(r.event_date, r.event_time)
            delta = (end_dt - start_dt).total_seconds() / 60
            # 只统计结束日期为目标日期的睡眠（跨天睡眠归属到结束日），
            # 避免把目标日期之前的历史睡眠重复计入
            if r.event_date == date and delta > 0:
                total_sleep_minutes += int(delta)
                sleep_count += 1
            pending_start = None

    return jsonify({
        'date': str(date),
        'total_formula': total_formula,
        'count_formula': count_formula,
        'count_solid': count_solid,
        'sleep_count': sleep_count,
        'total_sleep_minutes': total_sleep_minutes,
        'count_poop': count_poop,
        'count_pee': count_pee,
        'total_events': len(records),
    })


# ------------------------------------------------------------
# 数据导出：CSV
# ------------------------------------------------------------
@api_bp.route('/api/export/csv')
@login_required
def api_export_csv(user):
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    mode = request.args.get('mode', 'detail')

    if not start_str or not end_str:
        return jsonify({'error': '请选择开始和结束日期'}), 400

    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': '日期格式错误'}), 400

    if start_date > end_date:
        return jsonify({'error': '开始日期不能晚于结束日期'}), 400

    records = Record.query.filter(
        Record.user_id == user.id,
        Record.baby_id == user.baby_id,
        Record.event_date >= start_date,
        Record.event_date <= end_date
    ).order_by(Record.event_date.asc(), Record.event_time.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    if mode == 'summary':
        writer.writerow(['日期', '喝奶粉次数', '总奶量(ml)', '吃辅食次数', '开始睡次数', '睡醒次数', '拉粑粑次数', '小便次数'])
        # 按日期分组
        groups = defaultdict(lambda: {'formula_count': 0, 'formula_total': 0, 'solid': 0, 'sleep_start': 0, 'sleep_end': 0, 'poop': 0, 'pee': 0})
        for r in records:
            d = str(r.event_date)
            g = groups[d]
            if r.event_type == 'formula':
                g['formula_count'] += 1
                g['formula_total'] += (r.formula_amount or 0)
            elif r.event_type == 'solid':
                g['solid'] += 1
            elif r.event_type == 'sleep_start':
                g['sleep_start'] += 1
            elif r.event_type == 'sleep_end':
                g['sleep_end'] += 1
            elif r.event_type == 'poop':
                g['poop'] += 1
            elif r.event_type == 'pee':
                g['pee'] += 1

        for d in sorted(groups.keys()):
            g = groups[d]
            writer.writerow([d, g['formula_count'], g['formula_total'], g['solid'], g['sleep_start'], g['sleep_end'], g['poop'], g['pee']])
    else:
        writer.writerow(['日期', '时间', '事件类型', '奶粉量(ml)', '辅食'])
        for r in records:
            foods = r.foods if r.foods else ''
            writer.writerow([str(r.event_date), str(r.event_time), LABEL_MAP.get(r.event_type, r.event_type), r.formula_amount or '', foods])

    csv_content = output.getvalue()
    output.close()

    filename = f'baby_{start_str}_{end_str}_{"汇总" if mode == "summary" else "详细"}.csv'

    response = make_response(csv_content)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
    response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
    return response


# ------------------------------------------------------------
# Service Worker（必须位于根路径以保证正确作用域）
# ------------------------------------------------------------
@api_bp.route('/sw.js')
def service_worker():
    return send_from_directory(current_app.static_folder, 'sw.js', mimetype='application/javascript')


# ------------------------------------------------------------
# 用户常用辅食选项
# ------------------------------------------------------------
@api_bp.route('/api/foods')
@login_required
def api_foods(user):
    foods = Food.query.filter_by(user_id=user.id).order_by(Food.id.asc()).all()
    return jsonify({
        'foods': [{'id': f.id, 'name': f.name} for f in foods]
    })


@api_bp.route('/api/foods', methods=['POST'])
@login_required
def api_add_food(user):
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': '食物名称不能为空'}), 400
    if len(name) > 20:
        return jsonify({'error': '食物名称过长'}), 400
    existing = Food.query.filter_by(user_id=user.id, name=name).first()
    if existing:
        return jsonify({'error': '该食物已在常用中'}), 400
    food = Food(user_id=user.id, name=name)
    db.session.add(food)
    db.session.commit()
    return jsonify({'ok': True, 'food': {'id': food.id, 'name': food.name}}), 201


@api_bp.route('/api/foods/<int:food_id>', methods=['DELETE'])
@login_required
def api_delete_food(user, food_id):
    food = Food.query.filter_by(id=food_id, user_id=user.id).first()
    if not food:
        return jsonify({'error': '食物不存在'}), 404
    db.session.delete(food)
    db.session.commit()
    return jsonify({'ok': True})


# ------------------------------------------------------------
# 身高体重（成长记录）
# ------------------------------------------------------------
@api_bp.route('/api/growth')
@login_required
def api_get_growth(user):
    date_str = request.args.get('date', '').strip()
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': '日期格式错误'}), 400
    if not user.baby_id:
        return jsonify({'ok': True, 'growth': None})
    g = GrowthRecord.query.filter_by(
        user_id=user.id, baby_id=user.baby_id, record_date=date
    ).first()
    if not g:
        return jsonify({'ok': True, 'growth': None})
    return jsonify({'ok': True, 'growth': {
        'id': g.id,
        'height': g.height,
        'weight': g.weight,
        'date': str(g.record_date),
    }})


@api_bp.route('/api/growth', methods=['POST'])
@login_required
def api_save_growth(user):
    data = request.get_json() or {}
    if not user.baby_id:
        return jsonify({'error': '请先由管理员绑定宝宝，才能记录'}), 403

    date_str = (data.get('date') or '').strip() or datetime.now().strftime('%Y-%m-%d')
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': '日期格式错误'}), 400

    def _parse_num(v):
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        try:
            val = float(v)
        except (ValueError, TypeError):
            return None
        if val <= 0 or val > 999:
            return None
        return val

    height = _parse_num(data.get('height'))
    weight = _parse_num(data.get('weight'))
    if height is None and weight is None:
        return jsonify({'error': '请至少填写身高或体重'}), 400

    g = GrowthRecord.query.filter_by(
        user_id=user.id, baby_id=user.baby_id, record_date=date
    ).first()
    if g:
        g.height = height
        g.weight = weight
    else:
        g = GrowthRecord(user_id=user.id, baby_id=user.baby_id,
                         record_date=date, height=height, weight=weight)
        db.session.add(g)
    db.session.commit()
    return jsonify({'ok': True, 'growth': {
        'id': g.id,
        'height': g.height,
        'weight': g.weight,
        'date': str(g.record_date),
    }})
