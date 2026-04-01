# 🌊 深海掠夺者 (Deep Sea Odyssey)

一个Agent驱动的深海冒险MUD游戏。

## 游戏特色

- 🦐 六维属性系统：钳力、甲壳、游速、虾慧
- ⚔️ 六大门派：铁钳派、玄甲派、幻影派、智谋派
- 🗺️ 巡逻、义工、战斗多种玩法
- 💰 商店系统、背包管理
- 💾 本地存档、自动保存

## 运行方式

```bash
cd /root/.openclaw/workspace/games/deep_sea_odyssey
python3 game.py
```

## 游戏指令

| 指令 | 说明 |
|------|------|
| 状态 / stats | 查看角色状态 |
| 巡逻 / patrol | 执行巡逻任务 |
| 义工 / chore | 做义工赚取金贝 |
| 商店 / shop | 打开商店 |
| 背包 / inv | 查看背包 |
| 使用 [物品] | 使用物品 |
| 技能 / skills | 查看已学技能 |
| 学习 [技能] | 学习新技能 |
| 战斗 / battle | 挑战敌人 |
| 门派 / faction | 查看门派信息 |
| 休息 / rest | 恢复体力 |
| 冥想 / meditate | 恢复HP/MP |
| 对话 / talk | 与NPC对话 |
| 保存 / save | 保存游戏 |
| 退出 / quit | 退出游戏 |

## 门派系统

| 门派 | 属性要求 | 被动效果 |
|------|---------|---------|
| 铁钳派 | 钳力≥8 | 暴击伤害+20% |
| 玄甲派 | 甲壳≥8 | 伤害减免+15% |
| 幻影派 | 游速≥8 | 闪避率+15% |
| 智谋派 | 虾慧≥8 | 技能效果+20% |

## 文件结构

```
deep_sea_odyssey/
├── game.py          # 主游戏入口
├── player.py        # 玩家类
├── combat.py        # 战斗系统
├── shop.py          # 商店系统
├── quests.py        # 任务系统
├── factions.py      # 门派系统
├── npc.py           # NPC系统
├── items.py         # 物品数据
├── skills.py        # 技能数据
├── README.md        # 说明文档
├── data/            # 游戏数据
└── 存档/            # 存档目录
```

# 数据库配置
DB_CONFIG = {
    "host": "172.16.110.113",
    "port": 5432,
    "user": "postgres",
    "password": "6WmfEvMqhOqlRdn3",
    "database": "deep_sea_odyssey"
}

# redis
172.16.110.113, port=30379, password：gbq2KlOwPeVmQFRv

## 游戏截图

![游戏截图1](scripts/images/1.jpg)
![游戏截图2](scripts/images/2.jpg)
![游戏截图3](scripts/images/3.jpg)
![游戏截图4](scripts/images/4.jpg)
![游戏截图5](scripts/images/5.jpg)
![游戏截图6](scripts/images/6.jpg)
![游戏截图7](scripts/images/7.jpg)
![游戏截图8](scripts/images/8.jpg)
![游戏截图9](scripts/images/9.jpg)
![游戏截图10](scripts/images/10.jpg)
![游戏截图11](scripts/images/11.jpg)
![游戏截图12](scripts/images/12.jpg)
![游戏截图13](scripts/images/13.jpg)
![游戏截图14](scripts/images/14.jpg)
![游戏截图15](scripts/images/15.jpg)
![游戏截图16](scripts/images/16.jpg)
![游戏截图17](scripts/images/17.jpg)
![游戏截图18](scripts/images/18.jpg)
![游戏截图19](scripts/images/19.jpg)
![游戏截图20](scripts/images/20.jpg)
![游戏截图21](scripts/images/21.png)

数据库解压密码请看21图片加好友详谈
## 版权说明

本游戏由AI生成，仅供学习和娱乐使用。
