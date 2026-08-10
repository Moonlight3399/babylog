# ============================================================
# BabyLog - 每日邮件发送模块
# ============================================================
import smtplib
import requests
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import EMAIL_CONFIG


def get_baby_age_days(birth_str):
    """计算宝宝天数"""
    birth = datetime.strptime(birth_str, '%Y-%m-%d').date()
    return (date.today() - birth).days


def format_sleep_duration(minutes):
    """将分钟数格式化为 X小时X分钟"""
    h = minutes // 60
    m = minutes % 60
    if h > 0 and m > 0:
        return f'{h}小时{m}分钟'
    elif h > 0:
        return f'{h}小时'
    else:
        return f'{m}分钟'


def get_yesterday_stats(user, db, Record):
    """获取用户昨日统计数据"""
    yesterday = date.today() - timedelta(days=1)
    records = Record.query.filter_by(user_id=user.id, event_date=yesterday)\
        .order_by(Record.event_time.asc()).all()

    total_formula = sum(r.formula_amount for r in records if r.event_type == 'formula' and r.formula_amount)
    count_formula = sum(1 for r in records if r.event_type == 'formula')
    count_solid = sum(1 for r in records if r.event_type == 'solid')
    count_poop = sum(1 for r in records if r.event_type == 'poop')
    count_pee = sum(1 for r in records if r.event_type == 'pee')

    # 计算睡眠总时长
    total_sleep_minutes = 0
    pending_start = None

    all_sleep = Record.query.filter(
        Record.user_id == user.id,
        Record.event_type.in_(['sleep_start', 'sleep_end']),
        Record.event_date <= yesterday
    ).order_by(Record.event_date.asc(), Record.event_time.asc()).all()

    for r in all_sleep:
        if r.event_type == 'sleep_start':
            pending_start = r
        elif r.event_type == 'sleep_end' and pending_start is not None:
            start_dt = datetime.combine(pending_start.event_date, pending_start.event_time)
            end_dt = datetime.combine(r.event_date, r.event_time)
            delta = (end_dt - start_dt).total_seconds() / 60
            # 只统计结束日期为昨日的睡眠（跨天睡眠归属到结束日），
            # 避免把更早的历史睡眠重复计入
            if r.event_date == yesterday and delta > 0:
                total_sleep_minutes += int(delta)
            pending_start = None

    return {
        'date': yesterday.strftime('%Y年%m月%d日'),
        'count_formula': count_formula,
        'total_formula': total_formula,
        'count_solid': count_solid,
        'sleep_minutes': total_sleep_minutes,
        'count_poop': count_poop,
        'count_pee': count_pee,
        'total_events': len(records),
    }


def call_ai_analysis(age_days, stats):
    """调用 AI 分析今日数据，返回建议（100字以内）"""
    cfg = EMAIL_CONFIG['ai']
    if not cfg.get('api_key'):
        return '（AI 未配置）'

    prompt = (
        f"宝宝今天{age_days}天大。今日喂养记录："
        f"喝奶{stats['count_formula']}次、总奶量{stats['total_formula']}ml、"
        f"睡眠总时长{stats['sleep_minutes']}分钟、"
        f"大便{stats['count_poop']}次、小便{stats['count_pee']}次。"
        f"请根据月龄分析这些指标是否合理，并给出简短喂养/作息建议，严格控制在100字以内。"
    )

    try:
        resp = requests.post(
            f"{cfg['server']}/v1/chat/completions",
            headers={
                'Authorization': f"Bearer {cfg['api_key']}",
                'Content-Type': 'application/json',
            },
            json={
                'model': cfg.get('model', 'deepseek-chat'),
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 2048,
                'temperature': 0.7,
            },
            timeout=300,
        )
        data = resp.json()
        if 'choices' not in data:
            print(f'[AI] 返回异常: {data}')
            return '（AI 分析暂不可用）'
        msg = data['choices'][0]['message']
        content = (msg.get('content') or msg.get('reasoning_content', '')).strip()
        if not content:
            return '（AI 返回为空）'
        # 截取前200字
        return content[:200] if len(content) > 200 else content
    except Exception as e:
        print(f'[AI分析失败] {e}')
        return '（AI 分析暂不可用）'


def send_daily_email(app, db, User, Record):
    """发送每日邮件（由调度器调用）"""
    cfg = EMAIL_CONFIG
    if not cfg['active']:
        return

    with app.app_context():
        # 获取第一个用户（家庭单用户场景）
        user = User.query.first()
        if not user:
            print('[邮件] 无用户，跳过')
            return

        stats = get_yesterday_stats(user, db, Record)

        # 昨日无记录则跳过
        if stats['total_events'] == 0:
            print('[邮件] 昨日无记录，跳过')
            return

        # 计算宝宝天数
        age_days = get_baby_age_days(cfg['baby_birth_date'])

        # 获取 AI 分析
        ai_text = call_ai_analysis(age_days, stats)

        # 加载邮件模板
        with open('mail_template.html', 'r', encoding='utf-8') as f:
            template = f.read()

        # 替换模板占位符
        html = template.replace('{日期}', stats['date'])
        html = html.replace('{AI生成内容}', ai_text)
        html = html.replace('{变量1}', str(stats['count_formula']))
        html = html.replace('{变量2}', str(stats['total_formula']))
        html = html.replace('{变量3}', format_sleep_duration(stats['sleep_minutes']))
        html = html.replace('{变量4}', str(stats['count_poop']))
        html = html.replace('{变量5}', str(stats['count_pee']))

        # 解析收件人（支持逗号分隔多个）
        recipients = [r.strip() for r in cfg['recipient'].split(',') if r.strip()]

        # 发件人：优先用 from 别名，否则用登录邮箱
        smtp_cfg = cfg['smtp']
        from_addr = smtp_cfg.get('from') or smtp_cfg['email']

        # 构建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🍼 宝宝每日记录 - {stats["date"]}'
        msg['From'] = from_addr
        msg['To'] = ', '.join(recipients)
        msg.attach(MIMEText(html, 'html', 'utf-8'))

        # 发送（465=SSL, 其他=STARTTLS）
        try:
            if smtp_cfg['port'] == 465:
                with smtplib.SMTP_SSL(smtp_cfg['server'], smtp_cfg['port'], timeout=15) as server:
                    server.login(smtp_cfg['email'], smtp_cfg['password'])
                    server.sendmail(from_addr, recipients, msg.as_string())
            else:
                with smtplib.SMTP(smtp_cfg['server'], smtp_cfg['port'], timeout=15) as server:
                    server.starttls()
                    server.login(smtp_cfg['email'], smtp_cfg['password'])
                    server.sendmail(from_addr, recipients, msg.as_string())
            print(f'[邮件] 发送成功 → {", ".join(recipients)}')
        except Exception as e:
            print(f'[邮件] 发送失败: {e}')
