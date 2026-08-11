# BabyLog

> 宝宝日常成长记录工具（PWA 应用）· 支持 x86 / ARM64 双平台 · 开源免费

BabyLog 是一款面向宝爸宝妈的宝宝日常成长记录工具，支持快速记录喂养、睡眠、排便等活动。采用 PWA 技术，可安装到手机主屏幕，像原生 App 一样使用，并支持离线模式。

---

## 一、快速开始

### 1.1 环境要求

- Python 3.9+
- 操作系统：Windows / macOS / Linux

### 1.2 安装与启动

```bash
# 1. 进入项目目录
cd babylog

# 2. 安装依赖
pip install -r requirements.txt

# 3. （可选）命令行添加用户（也可登录后由管理员在"用户管理"中手动添加）
python register.py

# 4. 启动服务
python run.py
```

启动后，在手机或电脑浏览器中访问 `http://<你的IP>:5001` 即可使用。

### 1.3 添加用户（由管理员手动创建）

BabyLog 的账号由**管理员手动创建**，登录页仅保留登录，不再开放自助注册（避免公网垃圾注册）。
> ⚠️ **初始部署：必须先手动注册第一个管理员**
> 新部署的数据库是空的，**没有任何预置账号**（包括 admin）。请先创建第一个管理员，再启动服务：
> ```bash
> python register.py 你的用户名 你的强密码 --admin
> python run.py
> ```
> 然后用该账号登录，即可在管理界面添加普通用户、宝宝。**请使用强密码**（`admin` / `admin123` 等弱密码已公开，切勿使用）。
**方式一：管理界面添加（推荐）**

管理员登录后，进入"用户 → 用户管理"，在"＋ 添加用户"中输入用户名和初始密码即可创建普通用户。

**方式二：命令行注册（后端脚本）**

```bash
python register.py                        # 交互式注册
python register.py <用户名> <密码>         # 命令行注册（普通用户）
python register.py <用户名> <密码> --admin # 命令行注册（管理员）
```

例如：

```bash
python register.py admin 123456            # 创建普通用户 admin
python register.py admin 123456 --admin    # 创建管理员 admin
```

> **关于管理员：**
> - 管理员拥有"用户管理"权限（查看用户、添加用户、为用户绑定宝宝/设置身份、删除用户），普通用户无此权限
> - 首次部署建议先用 `--admin` 创建一个管理员账号
> - 注册接口 `/api/register` 仅管理员可用（未登录返回 401，普通用户返回 403）

---

## 二、功能说明

### 2.1 快捷记录（首页）

首页提供 5 个快捷按钮（**年龄分级**：6 个月前的宝宝不显示"吃辅食"，改为"小便了"）。点击任一按钮会弹出**确认弹窗**：左侧显示行为、右侧显示**当前时间（可修改）**，下方"确认/取消"按钮；点确认后记录该行为。

| 按钮 | 说明 |
|------|------|
| 喝奶粉 | 弹窗内含奶粉量输入框，并有**快捷量选项**（30/60/90/120/150/180/210 ml），点击快捷选项即自动填入 |
| 吃辅食（≥6个月） | 弹窗内含辅食选择：**分类快捷多选**（主食/蛋白质/蛋类/豆类/蔬菜/水果/其他）+ **常用选项**（可保存/删除）+ 手动输入 |
| 小便了（<6个月） | 6 个月前的宝宝替代"吃辅食"按钮，确认弹窗与拉粑粑一致（仅时间+确认），统计页同步显示"小便了"次数 |
| 开始睡 | 弹窗确认后记录睡眠开始时间 |
| 睡醒了 | 弹窗确认后记录睡眠结束时间，**需先有"开始睡"记录** |
| 拉粑粑 | 弹窗确认后记录一次排便 |

**撤回功能：** 记录添加后，页面底部会显示 Toast 提示，15 秒内可点击"撤回"撤销操作。

### 2.2 今日统计

切换到"今日统计"标签页，可查看当天的汇总数据：

- 喝奶粉次数和总奶量（ml）
- 睡眠总时长（自动计算"开始睡"到"睡醒了"的时间差）
- 吃辅食（≥6个月）/ 小便了（<6个月）、拉粑粑次数
- 当日所有记录的详细列表

**记录列表操作：**
- 点击时间可编辑记录时间
- 点击右侧 ✕ 可删除该条记录
- 删除前会有确认提示

### 2.3 历史记录

切换到"历史记录"标签页，可查看任意日期的记录：

- 通过日期选择器选择日期，或使用 `<` `>` 箭头快速切换前后日期
- 显示选中日期的统计汇总和详细记录列表
- **身高体重**：与今日统计一致，显示所选日期当天的身高体重（未记录显示 `--` / `点击记录`，点击可记录或修改该日期数值）
- 支持编辑时间、删除记录等操作
- **不能选择未来日期**

### 2.4 手动添加记录

在"今日统计"或"历史记录"页面的统计卡片中，点击 **＋ 手动添加** 卡片：

1. 选择事件类型（喝奶粉 / 吃辅食或小便了(按年龄分级) / 开始睡 / 睡醒了 / 拉粑粑）
2. 如果选择"喝奶粉"，需填写奶粉量（ml）
3. 如果选择"吃辅食"，需输入辅食名称（多个用逗号/顿号分隔，如"大米、南瓜"）
4. 选择日期和时间
5. 点击"确认添加"

**注意：** 不能添加未来时间的记录。

### 2.5 身高体重记录

在"今日统计"页面中，点击 **📐 身高体重** 卡片：

1. 选择日期（默认今天，不能选择未来日期）
2. 填写身高（cm）和/或体重（kg），可只填一项
3. 点击"保存"

**说明：**

- 同一宝宝同一天的身高体重会自动**覆盖更新**（再次保存即修改当天数值）
- 卡片上会显示当天记录的身高与体重，未记录显示 `--`
- 与其它记录一样，未绑定宝宝的用户无法记录（提示"请先由管理员绑定宝宝"）

**常驻显示最近一次：**

- 身高体重卡片**常驻显示最近一次**的测量结果（不限于当天），并以**小字标注**距离上次测量的天数：
  - 上次测量距今 N 天 → 显示 `距上次测量 N 天`
  - 今天刚测量过 → 显示 `今天已测量`
  - 从未记录 → 显示 `点击记录`
- 方便一眼看出该多久测量一次、有没有长高长胖

### 2.6 数据导出

在"用户"页面中，可以导出 CSV 数据：

1. 选择开始日期和结束日期
2. 选择导出模式：
   - **详细信息：** 每条记录的日期、时间、事件类型、奶粉量、辅食
   - **汇总信息：** 按日汇总的喝奶次数、总奶量、吃辅食次数、睡眠次数、拉粑粑次数
3. 点击"导出 CSV"按钮下载文件

### 2.7 多宝宝与用户身份

BabyLog 支持**多宝宝数据隔离**：每个用户由管理员绑定到一个宝宝，未绑定前无法记录任何数据；绑定后，用户的所有操作（记录、查询、统计、导出）都只作用于该宝宝，且只能看到自己的宝宝。

**绑定规则：**
- **宝宝由管理员绑定**：普通用户不能自行选择/更改宝宝，宝宝在"用户 → 宝宝管理"中由管理员添加，并在"用户管理 → 身份"弹窗中为用户绑定
- **未绑定不能记录**：用户点击快捷键或手动添加时，会提示"请先由管理员绑定宝宝，才能记录"
- **数据按宝宝隔离 + 家人共享**：绑定后，用户的所有记录自动归属该宝宝（记录带 `baby_id`）；**同一宝宝的家人共享该宝宝的全部记录**（查看/统计/导出/编辑/删除均按宝宝，谁记的都能看到），**不同宝宝之间完全隔离**
- **撤回仅限自己的记录**：15 秒内"撤回"只能撤回自己刚记的那条，防止误撤他人记录

**用户身份：** 每个用户可设置自己的家庭身份（爸爸 / 妈妈 / 爷爷 / 奶奶 / 外公 / 外婆）。设置后，用户页面会显示为 **"宝宝名字 的 身份"**（如"小宝的爸爸"）。

- 普通用户在"用户 → 我的身份"中可设置身份（宝宝为只读显示，由管理员绑定）
- 管理员可在"用户管理"中点击"身份"按钮，为用户设置身份并绑定/更换宝宝
- 身份可选：爸爸、妈妈、爷爷、奶奶、外公、外婆

**宝宝生日设置：** 管理员和普通用户都可在"用户 → 我的身份"中设置**宝宝生日**（日期选择器）。后续所有需要计算宝宝日期/月龄的功能（如"今日育儿小知识"的年龄段推荐、特殊纪念日祝贺）都以这个生日为准。未设置生日时，育儿小知识会提示先设置生日。

**宝宝管理（管理员）：**
- 管理员可在"用户 → 宝宝管理"中添加宝宝（输入名字）、查看宝宝列表、删除宝宝
- 每个宝宝旁显示**绑定家人数**（如"2 位家人"），一眼看出该宝宝关联了哪些用户
- 删除宝宝时自动解除用户对该宝宝的关联

**用户管理（管理员）：** 查看所有用户（含**绑定宝宝**徽章）、添加用户、为用户绑定/更换/解除宝宝、设置身份、设置角色、删除用户。

- **按宝宝分组显示**：用户列表按宝宝名字分组（`👶 宝宝名（N 人）`），不同用户挂靠在对应宝宝下面；未绑定宝宝的用户归入"🚫 未绑定宝宝"组
- 每个用户行显示其绑定的宝宝（如"👶 玥玥"）或"未绑定宝宝"
- 点"设置"按钮弹窗内显示"当前绑定：👶 玥玥"，可切换绑定的宝宝、设置身份，并可**将该用户设为管理员**（普通用户 ↔ 管理员）
- 安全限制：管理员**不能修改自己的角色**；系统**至少保留一名管理员**（不会因降级而失去所有管理员）

**创建者归属：** 宝宝和用户记录"由哪个管理员创建"（`created_by`）。
- **管理员只能删除自己添加的宝宝/用户**，不能删除其他管理员添加的
- 历史数据（迁移前）无创建者归属，任何管理员都可删除，方便清理
- 删除按钮会按权限自动隐藏，越权删除后端返回 403

**修改密码：** 每个用户在"用户 → 我的身份 → 修改密码"中修改自己的密码（需验证当前密码，新密码至少 6 位）。

### 2.8 今日育儿小知识（快捷键页）

在"快捷键"页顶部常驻显示一张 **"💡 今日育儿小知识"** 卡片，每天自动从育儿知识库中挑一条适合宝宝当前年龄的简短小知识：

- **按年龄推荐**：根据宝宝生日计算出生天数，自动匹配年龄段（0-1个月 / 1-3个月 / 4-6个月 / 7-12个月 / 1-2岁 / 2-3岁），展示对应阶段的知识，并显示"📅 宝宝 X 天 · 年龄段"；**3 岁以上暂时沿用 2-3 岁阶段的知识**（后续可再扩充更高年龄段）
- **每天固定一条**：同一天始终显示同一条（避免刷新变化），第二天自动换一条
- **未设置生日时**：卡片提示"请先在「我的身份」中设置宝宝生日"

**特殊纪念日祝贺：** 在宝宝的里程碑日子，卡片会额外显示祝贺提示词：

| 日子 | 祝贺词 |
|------|--------|
| 满月（出生第 30 天） | 🎉 宝宝满1个月啦！ |
| 每满 2/3/... 个月（每 30 天） | 🎉 宝宝满 N 个月啦！ |
| 百天（出生第 100 天） | 🎉 宝宝百天啦！ |
| 周岁（每满 365 天） | 🎂 宝宝 N 周岁啦！ |

**育儿知识库：** 知识存放于 `data/tips.json`，内置 **100 条**（目前覆盖 0-3 岁，参照崔玉涛等育儿专家观点，涵盖喂养、睡眠、护理、辅食、早教等），每条带 `min_days`/`max_days` 年龄段范围。可直接编辑该文件增删改知识内容，重启服务后生效；后续如需 3 岁以上知识，在该文件追加新阶段即可。

---

## 三、每日邮件功能（可选）

### 3.1 功能说明

每天定时发送前一天的喂养汇总邮件到指定邮箱，邮件内容包括：

- 前一天的喂养、睡眠、排便统计
- AI 智能分析建议（基于月龄，调用 DeepSeek API）

### 3.2 配置方法

编辑 `config.py` 文件：

```python
EMAIL_CONFIG = {
    # 是否启用每日邮件
    'active': True,

    # 每天发送时间
    'time': '06:00',

    # 宝宝出生日期（用于 AI 计算月龄）
    'baby_birth_date': '2026-01-01',

    # SMTP 发件服务器配置
    'smtp': {
        'server': 'smtp.example.com',   # SMTP 服务器地址
        'port': 465,                     # 465=SSL, 587=STARTTLS
        'email': 'your_email@example.com',  # 发件邮箱账号
        'password': 'your_password',        # 发件邮箱密码/授权码
        'from': 'BabyLog <your_email@example.com>',  # 发件人显示名称
    },

    # 收件邮箱（多个用逗号隔开）
    'recipient': 'recipient@example.com',

    # AI 分析配置（DeepSeek API）
    'ai': {
        'server': 'https://api.deepseek.com',
        'api_key': 'sk-your-api-key',
        'model': 'deepseek-chat',
    },
}
```

**常用 SMTP 服务器参考：**

| 邮箱服务商 | SMTP 服务器 | 端口 |
|-----------|------------|------|
| QQ 邮箱 | smtp.qq.com | 465 (SSL) |
| 163 邮箱 | smtp.163.com | 465 (SSL) |
| Gmail | smtp.gmail.com | 587 (STARTTLS) |

> **注意：** QQ 邮箱和 163 邮箱需要使用"授权码"而非登录密码，请在邮箱设置中生成。

### 3.3 AI 分析说明

AI 分析功能调用 DeepSeek API，根据宝宝当天的喂养数据结合月龄给出简短建议。API Key 可在 [DeepSeek 开放平台](https://platform.deepseek.com) 申请。

如果 AI 配置未启用，邮件中会显示"（AI 未配置）"。

---

## 四、PWA 安装

BabyLog 支持 PWA 模式，可将网页安装到手机主屏幕：

### 4.1 Android（Chrome）

1. 在 Chrome 中打开 BabyLog 网址
2. 浏览器地址栏右侧会出现"安装"图标，点击即可安装
3. 或通过菜单 → "添加到主屏幕"

### 4.2 iOS（Safari）

1. 在 Safari 中打开 BabyLog 网址
2. 点击底部的"分享"按钮
3. 选择"添加到主屏幕"

安装后，BabyLog 将以独立 App 窗口运行，支持离线查看缓存的页面。

---

## 五、部署指南

> **平台支持：** 本程序支持 **x86_64** 与 **arm64 (aarch64)** 双平台，部署方式完全相同，无架构差异。

### 5.1 局域网部署（家庭使用）

```bash
# 启动服务（默认监听 0.0.0.0:5001）
python run.py
```

同一局域网内的设备通过 `http://<电脑IP>:5001` 访问。

查看本机 IP 的方法：

- **Windows：** `ipconfig`
- **macOS / Linux：** `ifconfig` 或 `ip addr`

### 5.2 使用 Waitress（生产环境，Windows）

```bash
pip install waitress
waitress-serve --host=0.0.0.0 --port=5001 run:app
```

### 5.3 使用 Gunicorn（生产环境，Linux/macOS）

```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:5001 run:app
```

### 5.4 使用 systemd 设置开机自启（Linux）

创建服务文件 `/etc/systemd/system/babylog.service`：

```ini
[Unit]
Description=BabyLog Service
After=network.target

[Service]
User=your_user
WorkingDirectory=/path/to/babylog
ExecStart=/usr/bin/python3 /path/to/babylog/run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable babylog
sudo systemctl start babylog
```

### 5.5 新旧版本同时运行（多实例部署）

BabyLog 的**端口**和**数据库文件**均支持通过环境变量配置。**新版本默认配置已自动避开旧版本**，两者可直接在同一台服务器同时运行，互不干扰。

| 环境变量 | 作用 | 默认值 |
|---------|------|--------|
| `PORT` | 服务监听端口 | `5001` |
| `BABYLOG_DB` | SQLite 数据库文件名或路径 | `babylog_new.db`（位于 `instance/`） |

**新旧版本默认配置对照：**

| 版本 | 端口 | 数据库 | 访问地址 |
|------|------|--------|----------|
| 旧版本（初始版） | 5000 | `babylog.db` | `http://<服务器IP>:5000` |
| 新版本（当前版） | 5001 | `babylog_new.db` | `http://<服务器IP>:5001` |

**同时运行（无需任何环境变量）：**

```bash
# ===== 旧版本（默认 5000 端口 + babylog.db）=====
cd /path/to/babylog_old
python run.py

# ===== 新版本（默认 5001 端口 + babylog_new.db）=====
cd /path/to/babylog_new
python run.py
```

**如需再部署第三个实例（自定义端口与数据库）：**

```bash
PORT=5002 BABYLOG_DB=babylog_v3.db python run.py
```

**systemd 多实例示例**（创建 `babylog-old.service` 与 `babylog-new.service` 两个服务文件）：

```ini
# /etc/systemd/system/babylog-new.service（新版，默认即 5001 端口 + babylog_new.db）
[Unit]
Description=BabyLog New Version
After=network.target

[Service]
User=your_user
WorkingDirectory=/path/to/babylog_new
ExecStart=/usr/bin/python3 /path/to/babylog_new/run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

> **注意事项：**
> - 新版本默认端口 `5001`、数据库 `babylog_new.db`，与旧版本（5000 / babylog.db）**天然隔离**，同时运行无需额外配置
> - `BABYLOG_DB` 支持相对路径（相对 `instance/` 目录）或绝对路径
> - 升级前建议先备份旧版本数据库文件

---

## 六、数据库说明

数据库文件：`instance/babylog_new.db`（SQLite），首次运行自动创建，包含以下表：

### users（用户表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 主键 |
| username | String(50) UNIQUE | 用户名 |
| password_hash | String(128) | PBKDF2-SHA256 加盐哈希 |
| salt | String(64) | 盐值 |
| role | String(20) | 角色：`admin` 管理员 / `user` 普通用户（默认 user） |
| baby_id | Integer FK → babies.id | 绑定的宝宝（由管理员设置，可为空） |
| identity | String(20) | 家庭身份：爸爸/妈妈/爷爷/奶奶/外公/外婆（可为空） |
| created_at | DateTime | 创建时间 |

### records（记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 主键 |
| user_id | FK → users.id | 所属用户 |
| baby_id | FK → babies.id | 所属宝宝（多宝宝数据隔离，可为空） |
| event_type | String(20) | 事件类型（formula / solid / sleep_start / sleep_end / poop / pee） |
| event_date | Date | 记录日期 |
| event_time | Time | 记录时间 |
| formula_amount | Integer | 奶粉量（ml，仅喝奶粉有值） |
| foods | String(200) | 辅食食物列表（逗号分隔，仅吃辅食有值） |
| created_at | DateTime | 创建时间（用于撤回时限判断） |

### babies（宝宝表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 主键 |
| name | String(50) | 宝宝名字 |
| birth_date | Date | 宝宝生日（可空，用于计算年龄/月龄/特殊纪念日） |
| created_at | DateTime | 创建时间 |

### growth_records（身高体重记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 主键 |
| user_id | FK → users.id | 所属用户 |
| baby_id | FK → babies.id | 所属宝宝（可为空） |
| height | Float | 身高（cm，可空） |
| weight | Float | 体重（kg，可空） |
| record_date | Date | 记录日期（每宝宝每天一条） |
| created_at | DateTime | 创建时间 |

### custom_foods（用户常用辅食表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 主键 |
| user_id | FK → users.id | 所属用户 |
| name | String(20) | 辅食名称 |
| created_at | DateTime | 创建时间 |

### login_attempts（登录失败记录表，防暴力破解）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 主键 |
| key | String(120) UNIQUE | 限速维度：`用户名|IP` |
| fail_count | Integer | 连续失败次数 |
| last_fail | DateTime | 最近一次失败时间 |
| locked_until | DateTime | 锁定截止时间（15 分钟后自动解除） |

**安全机制：**
- 用户密码使用 PBKDF2-SHA256（10 万次迭代）加盐哈希存储，不保存明文
- **登录限速**：同一「用户名+IP」连续失败 5 次锁定 15 分钟（数据库持久化，跨进程/重启有效）
- Session 基于自研签名 Cookie 认证（格式 `user_id:过期时间戳:签名`），默认 30 天有效，`HttpOnly` + `SameSite=Lax`
- `SECRET_KEY` 固定（`config.py` 默认值 + 环境变量 `SECRET_KEY` 覆盖），重启服务**不会**导致用户掉线；公网部署请重新生成并设置环境变量

**自动备份：**
- 默认每天 `03:30` 自动备份数据库到 `instance/backups/`（`babylog_时间戳.db`），保留最近 30 天，超出自动清理
- 服务启动后也会立即备份一次（保证覆盖重启前的数据变化）
- 配置项见 `config.py`：`BACKUP_ENABLED` / `BACKUP_DIR` / `BACKUP_TIME` / `BACKUP_RETENTION_DAYS`，均可用环境变量覆盖（如 `BABYLOG_BACKUP_DIR`）
- 使用 SQLite 在线备份 API，备份文件保证一致性

---

| 层级 | 技术 |
|------|------|
| 后端框架 | Flask 3.x |
| ORM | Flask-SQLAlchemy（SQLite） |
| 任务调度 | APScheduler（每日邮件） |
| 前端 | 原生 HTML/CSS/JS（无框架） |
| PWA | Service Worker + Web App Manifest |
| AI | DeepSeek API（OpenAI 兼容接口） |

---

## 八、平台兼容性要求（开发规范）⚠️

### 8.1 支持平台

| 平台 | 架构 | 支持状态 |
|------|------|----------|
| Linux / Windows / macOS | x86_64 | ✅ 完全支持 |
| Linux（树莓派、高通盒子、ARM 服务器等） | arm64 (aarch64) | ✅ 完全支持 |

> BabyLog 全部依赖为纯 Python 或带官方 ARM64 wheel 的包，代码层面无平台特定逻辑，**x86 与 ARM64 双平台可无缝运行**。

### 8.2 强制规范（后续所有改动必须遵守）

1. **禁止引入平台相关编译依赖**：新增任何依赖前，必须先验证其在 ARM64 上可用
   - 优先选择纯 Python 包（`py3-none-any` wheel）
   - 若必须使用带 C 扩展的包，须确认 PyPI 提供 `manylinux2014_aarch64`（或更新）wheel
   - 验证命令：
     ```bash
     pip download --only-binary=:all: --platform manylinux2014_aarch64 \
       --python-version 312 --implementation cp --abi cp312 <包名>
     ```
2. **禁止架构相关系统调用**：不得引入 `numpy`、`opencv`、`ctypes`、内联汇编、`os.uname()` 架构分支等架构特定代码
3. **路径处理中性化**：使用 `os.path` / `pathlib` 处理路径，不得硬编码绝对路径或 Windows/Linux 特有路径分隔符
4. **依赖同步记录**：新增第三方库时同步更新 `requirements.txt`，并注明其平台兼容性
5. **配置默认值中性化**：配置项默认值不得包含平台特定内容（如绝对路径、平台专属环境变量）
6. **双平台验证**：改动必须至少通过一个 x86_64 环境 + 一个 arm64 环境（或通过上述 pip 模拟验证）的依赖安装与基础运行验证

---

## 九、项目目录结构

```
babylog/
├── run.py                # 应用入口（精简，仅启动服务）
├── config.py             # 配置：端口/数据库/SECRET_KEY、邮件、SMTP、AI
├── mailer.py             # 每日邮件发送模块
├── register.py           # 用户注册脚本（交互式 / 命令行，管理员创建用户）
├── mail_template.html    # 每日邮件 HTML 模板
├── requirements.txt      # Python 依赖
├── README.md              # 项目说明文档
├── app/                  # 应用主包（工厂 + 蓝图结构）
│   ├── __init__.py       # 应用工厂 create_app()：初始化 db、注册蓝图、启动调度器
│   ├── models.py         # 数据模型（User/Baby/Record/Food/GrowthRecord/LoginAttempt）
│   ├── auth.py           # 认证辅助函数 + 登录相关路由（auth 蓝图）
│   ├── views.py          # 页面路由（main 蓝图：首页）
│   ├── api.py            # API 路由（api 蓝图：记录、统计、导出、sw.js）
│   ├── tips.py           # 育儿小知识：年龄阶段匹配、每日选条、特殊纪念日
│   └── backup.py         # 数据库自动备份模块
├── data/                 # 数据文件
│   └── tips.json         # 育儿知识库（100 条，0-3 岁，按年龄段，可自行编辑）
├── static/               # 前端静态资源
│   ├── style.css         # 全局样式
│   ├── manifest.json     # PWA 清单
│   ├── sw.js             # Service Worker（离线缓存）
│   └── icons/            # PWA 各尺寸图标（64~512px）
├── templates/
│   ├── index.html        # 主页面（快捷记录/统计/历史/用户 四个标签页）
│   └── login.html        # 登录页
└── instance/             # SQLite 数据库目录（运行时生成）
    └── backups/          # 自动备份目录（每天生成 babylog_时间戳.db）
```

---

## 十、API 接口

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | `/api/login` | 登录，设置 Session Cookie（连续失败 5 次锁定 15 分钟，返回 429） | 否 |
| POST | `/api/logout` | 退出登录 | 否 |
| POST | `/api/register` | 管理员手动添加用户（body: {username, password}；未登录 401、普通用户 403） | 管理员 |
| GET | `/api/user` | 当前用户信息（含角色 role、身份 identity、绑定宝宝 baby） | 是 |
| PUT | `/api/user/profile` | 用户设置自己的身份与宝宝生日（body: {identity?, baby_birth_date?}；宝宝由管理员绑定，用户不可更改） | 是 |
| PUT | `/api/user/password` | 用户修改自己的密码（body: {old_password, new_password}，新密码≥6位） | 是 |
| GET | `/api/babies` | 查看我绑定的宝宝（未绑定返回空） | 是 |
| GET | `/api/foods` | 查看我的常用辅食 | 是 |
| POST | `/api/foods` | 保存常用辅食（body: {name}） | 是 |
| DELETE | `/api/foods/<id>` | 删除常用辅食 | 是 |
| GET | `/api/admin/users` | 查看所有用户（含身份、绑定宝宝 baby_name） | 管理员 |
| PUT | `/api/admin/users/<id>` | 管理员为用户设置身份/绑定宝宝/角色（body: {identity?, baby_id?, role?}；role 为 admin/user，不可改自己，至少保留一名管理员） | 管理员 |
| DELETE | `/api/admin/users/<id>` | 删除用户及其全部记录 | 管理员 |
| GET | `/api/admin/babies` | 查看所有宝宝（含绑定家人数 user_count） | 管理员 |
| POST | `/api/admin/babies` | 添加宝宝（body: {name}） | 管理员 |
| DELETE | `/api/admin/babies/<id>` | 删除宝宝（自动解除用户关联） | 管理员 |
| POST | `/api/record` | 新增记录（可手动指定日期时间；未绑定宝宝返回 403） | 是 |
| PUT | `/api/record/<id>` | 修改记录时间（HH:MM） | 是 |
| DELETE | `/api/record/<id>` | 删除记录 | 是 |
| POST | `/api/record/undo` | 撤回最近一条记录（15 秒内） | 是 |
| GET | `/api/records?date=YYYY-MM-DD` | 查询某日记录列表（仅本人绑定宝宝） | 是 |
| GET | `/api/stats?date=YYYY-MM-DD` | 查询某日统计汇总（仅本人绑定宝宝） | 是 |
| GET | `/api/export/csv?start=&end=&mode=` | 导出 CSV（detail 详细 / summary 汇总，仅本人绑定宝宝） | 是 |
| GET | `/api/growth?date=YYYY-MM-DD` | 查询某日身高体重（仅本人绑定宝宝，无记录返回 null） | 是 |
| POST | `/api/growth` | 保存/覆盖身高体重（body: {date?, height?, weight?}；未绑定宝宝返回 403） | 是 |
| GET | `/api/growth/latest` | 最近一次身高体重（返回 height/weight/record_date/days_ago 距上次天数） | 是 |
| GET | `/api/tips/daily` | 今日育儿小知识（基于宝宝生日：返回 stage/tip/special 特殊纪念日/days 天数） | 是 |

**事件类型：** `formula`（喝奶粉）/ `solid`（吃辅食）/ `sleep_start`（开始睡）/ `sleep_end`（睡醒了）/ `poop`（拉粑粑）/ `pee`（小便了）

**年龄分级：** 根据宝宝生日自动判断——6 个月前（<180 天）首页和手动添加弹窗均不显示"吃辅食"，改为"小便了"；满 6 个月自动恢复为"吃辅食"。今日统计/历史记录的对应卡片同步切换（💧 小便了 ↔ 🥣 吃辅食）。

**业务规则：**
- 未绑定宝宝的用户无法记录（返回 403："请先由管理员绑定宝宝，才能记录"）
- 存在未结束的睡眠时，禁止再次"开始睡"；没有"开始睡"记录时，禁止"睡醒了"
- 睡眠时长统计支持**跨天配对**（按所有日期顺序配对）
- 撤回仅限最近一条、创建 15 秒内
- 不允许添加/选择未来日期

---

## 十一、常见问题

### Q：服务重启后需要重新登录？

A：不会。`SECRET_KEY` 已固定（`config.py` 默认值 + 环境变量 `SECRET_KEY` 覆盖），重启服务后已登录用户**保持登录**，不会掉线。

### Q：如何修改端口号？

A：通过环境变量 `PORT` 覆盖（如 `PORT=5002 python run.py`），或修改 `config.py` 中的 `PORT` 默认值。

### Q：数据如何备份？

A：系统已内置**自动备份**：默认每天 `03:30` 自动备份数据库到 `instance/backups/`（保留最近 30 天，服务启动时也会立即备份一次）。也可用"用户 → 导出 CSV"导出数据；手动备份直接复制 `instance/babylog_new.db` 即可。

### Q：如何重置密码？

A：让管理员在"用户管理"中删除该用户后用相同用户名重新添加（会提示"用户已存在"，先删除再添加即可）。或直接在 Python 中操作数据库更新 `users` 表的 `password_hash`（用 `app.auth.hash_password` 生成）。

### Q：支持哪些平台？x86 和 ARM 都能跑吗？

A：支持。项目全部为纯 Python + 官方跨平台 wheel 依赖，**x86_64 与 arm64 (aarch64) 均可直接运行**，无需任何修改。若在 ARM 上遇到某依赖安装失败，请先确认 PyPI 是否有对应 aarch64 wheel（验证方法见"八、平台兼容性要求"）。

---

## 开源许可（MIT License）

BabyLog 基于 **MIT License** 开源发布，允许任何人自由**使用、修改、复制、分发（含商业用途）**，只需保留原始版权声明与许可声明。

本项目基于原项目作者 **https://yuubari.cn/** 的作品开发，保留原作者的版权归属。

```
MIT License

Copyright (c) 2026 zhongyutian
Original project author: https://yuubari.cn/

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

完整许可文本见项目根目录 `LICENSE` 文件。
