# 深海掠夺者 - Deep Sea Odyssey

## 项目概述

深海冒险游戏是一个基于浏览器的海洋探索与战斗游戏，玩家可以在海域中探索、拾取物品、与其他玩家或海洋生物战斗。

**技术栈：** Python Flask + HTML5 + JavaScript + PostgreSQL

**服务地址：** `http://172.16.110.113:5000`

---

## 核心功能模块

### 1. 深海冒险系统 (`static/deep_adventure.html`)

#### 海域系统
- 4个海域：珊瑚礁域、幽暗深渊、炽热岩浆、极寒冰窟
- 底部传送门切换海域
- 每个海域有独特的渐变背景和装饰

#### 海底物品系统
- **100+种可拾取物品**，分为：
  - 生物壳体类（鲍鱼、扇贝、海螺、蛤蜊等）
  - 甲壳类（龙虾、螃蟹、皮皮虾等）
  - 棘皮动物（海星、海胆、海参等）
  - 鱼类（小丑鱼、蝴蝶鱼、河豚等）
  - 海洋哺乳动物（海豚、鲸鱼、海狮等）
  - 腔肠动物（水母、珊瑚、海葵等）
  - 植物类（海带、紫菜、石花菜等）
  - 人工制品（渔网、浮球、瓷器碎片等）
  - 化石类（菊石化石、珊瑚化石等）
  - 特殊物品（珍珠、宝石、传说装备）

#### 物品稀有度
| 稀有度 | 颜色 | 说明 |
|--------|------|------|
| common | 灰色 | 普通物品 |
| uncommon | 绿色 | 优秀物品 |
| rare | 蓝色 | 稀有物品 |
| epic | 紫色 | 史诗物品 |
| legendary | 金色 | 传说物品 |

#### 战斗系统
- **保护盾系统**：默认开启，无法被攻击
- **战力计算**：`战力 = 基础战力 + 攻击*2 + 防御 + 速度 + 幸运*3`
- **战斗结果**：胜利获得标本，失败显示挑战失败
- **标本系统**：击败的生物变成标本存入收纳袋

#### 海洋生物系统
- 初始20只生物在海域中游动
- 被击败后3-5秒从边缘重生新生物
- 攻击有护盾的生物无效
- 生物战力根据稀有度随机生成

#### 收纳袋系统
- 物品自动合并显示数量
- 物品永久保存到数据库
- 物品卡片显示：防伪标识、拾取时间、拾取海域、稀有度、价值、介绍

---

### 2. 数据库表结构

#### `sea_collected_items` - 已收集物品表
```sql
CREATE TABLE sea_collected_items (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL,
    item_id VARCHAR(50) NOT NULL,
    emoji VARCHAR(20),
    name VARCHAR(100),
    rarity VARCHAR(20),
    value INTEGER,
    zone VARCHAR(50),
    collected_at TIMESTAMP DEFAULT NOW()
);
```

---

### 3. API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/sea/collected` | GET | 获取玩家已收集物品 |
| `/api/sea/collect` | POST | 添加物品到收藏 |
| `/api/player/stats` | GET | 获取玩家战斗属性 |

---

## 装备强化系统

- **强化消耗**：1000银贝/次
- **强化属性**：攻击+1500、防御+1500、生命+1500/级
- **强化上限**：+5级
- **强化加成实时更新**：装备属性和总战力同步增加

---

## 世界BOSS卡片系统

- 击败世界BOSS掉落卡片
- 卡片显示：击杀者、击杀编号、击杀时间
- 每个玩家的击杀记录独立显示

---

## 邮件系统

- 限时装备购买后发送邮件附件
- 附件类型：item、artifact、equipment
- 只有已领取或无附件的邮件可删除

---

## 拍卖行系统

- 玩家可上架物品和装备
- 支持物品、装备、神器三种类型
- 上架时自动获取物品名称和图标

---

## 数据库配置

```python
host = '172.16.110.113'
port = 5432
user = 'postgres'
password = '6WmfEvMqhOqlRdn3'
database = 'deep_sea_odyssey'
```

---

## 启动服务

```bash
cd /root/.openclaw/workspace/games/deep_sea_odyssey
python3 game.py
```

---

## 开发日志

### 2026-04-01

#### 新增功能
- 全新深海冒险页设计
- 海底物品100+种
- 战斗系统（战力对比、胜负判定、标本获取）
- 收纳袋永久存储
- 海洋生物20只持续存在
- 保护盾系统

#### 修复问题
- 装备仓库邮件领取bug
- 拍卖行装备名称null
- 装备强化UI和属性计算
- 邮件删除权限
- 世界BOSS卡片显示逻辑

---

## 文件结构

```
deep_sea_odyssey/
├── game.py              # Flask主服务
├── models.py            # 数据库模型
├── db_config.py         # 数据库配置
├── market.py            # 拍卖行API
├── changelog.html       # 更新日志页面
├── static/
│   ├── shared.js        # 共享JS函数
│   ├── shared.css       # 共享样式
│   ├── deep_adventure.html  # 深海冒险主页面
│   ├── role.html        # 角色页面
│   ├── inbox.html       # 邮件页面
│   ├── auction.html     # 拍卖行页面
│   ├── handbook.html    # 游戏手册
│   └── ...
└── templates/
    └── ...
```
