# -*- coding: utf-8 -*-
"""多宝宝数据隔离测试脚本（使用真实 API）"""
import requests

BASE = 'http://127.0.0.1:5001'
S = requests.Session()
passed, failed = [], []

def check(name, cond, extra=''):
    if cond:
        passed.append(name)
        print(f'  ✅ {name}')
    else:
        failed.append(name)
        print(f'  ❌ {name} {extra}')

# ---------- 1. 注册一个测试用户 ----------
uname = 'test_mb_用户'
r = S.post(BASE + '/api/register', json={'username': uname, 'password': '123456'})
print('注册测试用户:', r.status_code, r.json())

# ---------- 2. 未绑定宝宝时记录应被拒绝 ----------
r = S.post(BASE + '/api/login', json={'username': uname, 'password': '123456'})
print('登录测试用户:', r.status_code, r.json())
check('未绑定用户登录成功', r.json().get('ok') is True)

# 尝试记录
r = S.post(BASE + '/api/record', json={'event_type': 'formula', 'event_time': '08:00', 'formula_amount': 120})
check('未绑定用户记录被拒(403)', r.status_code == 403, str(r.status_code) + ' ' + r.text)
check('拒绝原因正确', '绑定宝宝' in r.json().get('error', ''))

# api/babies 应返回空
r = S.get(BASE + '/api/babies')
check('未绑定用户 api/babies 为空', r.json().get('babies') == [])

# /api/user baby 应为 null
r = S.get(BASE + '/api/user')
check('未绑定用户 /api/user baby 为 null', r.json().get('baby') is None)

# ---------- 3. 管理员绑定用户到宝宝 ----------
A = requests.Session()
r = A.post(BASE + '/api/login', json={'username': 'admin', 'password': 'admin'})
print('管理员登录:', r.status_code, r.json())

# 获取宝宝列表
r = A.get(BASE + '/api/admin/babies')
babies = r.json().get('babies', [])
print('管理员宝宝列表:', babies)
check('管理员有宝宝', len(babies) > 0)

# 获取用户列表，找测试用户 id
r = A.get(BASE + '/api/admin/users')
users = r.json().get('users', [])
uid = None
for u in users:
    if u['username'] == uname:
        uid = u['id']
        break
check('找到测试用户', uid is not None)

# 管理员绑定：设置测试用户的 baby_id
baby_id = babies[0]['id']
r = A.put(BASE + f'/api/admin/users/{uid}', json={'baby_id': baby_id})
print('管理员绑定用户:', r.status_code, r.json())
check('管理员绑定成功', r.json().get('ok') is True)

# ---------- 4. 绑定后用户可记录，数据归属宝宝 ----------
r = S.post(BASE + '/api/record', json={'event_type': 'formula', 'event_time': '08:00', 'formula_amount': 120})
print('绑定后记录:', r.status_code, r.json())
check('绑定后记录成功', r.status_code == 200 and r.json().get('ok') is True)
if r.status_code == 200:
    rec = r.json().get('record', {})
    check('记录归属 baby_id 正确', rec.get('baby_id') == baby_id, 'baby_id=' + str(rec.get('baby_id')))

# api/babies 只返回绑定宝宝
r = S.get(BASE + '/api/babies')
blist = r.json().get('babies', [])
check('绑定后 api/babies 只返回该宝宝', len(blist) == 1 and blist[0]['id'] == baby_id, str(blist))

# /api/user baby 显示
r = S.get(BASE + '/api/user')
check('绑定后 /api/user 显示 baby', r.json().get('baby') and r.json()['baby']['id'] == baby_id)

# 记录查询只显示绑定宝宝记录
r = S.get(BASE + '/api/records?date=' + __import__('datetime').date.today().isoformat())
recs = r.json().get('records', [])
check('记录查询含新记录', any(x.get('baby_id') == baby_id for x in recs))

# ---------- 5. profile 只设身份，不能改宝宝 ----------
r = S.put(BASE + '/api/user/profile', json={'identity': '妈妈', 'baby_id': None})
print('用户设置身份(尝试改宝宝):', r.status_code, r.json())
check('用户设置身份成功', r.json().get('ok') is True)

r = S.get(BASE + '/api/user')
u = r.json()
check('用户改身份后 baby 不变', u.get('baby') and u['baby']['id'] == baby_id)
check('身份已更新为妈妈', u.get('identity') == '妈妈')

# 尝试把 baby_id 改成 None 应被忽略/拒绝
r = S.put(BASE + '/api/user/profile', json={'baby_id': None})
r2 = S.get(BASE + '/api/user')
check('用户无法解除绑定', r2.json().get('baby') is not None)

# ---------- 6. 清理：删除测试用户（管理员） ----------
r = A.delete(BASE + f'/api/admin/users/{uid}')
print('清理测试用户:', r.status_code, r.json())
check('清理测试用户成功', r.json().get('ok') is True)

# 清理测试记录（按 user_id 删除）——直接通过 sqlite
import sqlite3, os
# 脚本位于 test/ 下，数据库在项目根 instance/ 下
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(_BASE, 'instance', 'babylog_new.db')
conn = sqlite3.connect(db_path)
# 找出测试用户记录并删除（用户已删除，遗留孤儿记录也清理）
cur = conn.execute("DELETE FROM records WHERE user_id NOT IN (SELECT id FROM users)")
conn.commit()
conn.close()

print('\n========== 结果 ==========')
print(f'通过 {len(passed)} 项，失败 {len(failed)} 项')
if failed:
    print('失败项:', failed)
    raise SystemExit(1)
print('全部通过！')
