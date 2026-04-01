# -*- coding: utf-8 -*-
"""
深海掠夺者 - 9大神器配置
"""

# 神器图标（数据库只存名称，图标从这取）
ARTIFACT_ICONS = {
    "黑龙权杖": "🐉",
    "金龙权杖": "✨",
    "空间之刃": "💠",
    "时间之锤": "⏳",
    "魔女斗篷": "🦇",
    "繁荣权杖": "🌿",
    "圣诞权杖": "🎄",
    "龙行之剑": "⚡",
    "龙影雕像": "🔮",
}

# 神器属性
# 主属性 +200 (or 180/150 for lower tier)
# 副属性 +100 (or 120 for lower tier)
# 特效
ARTIFACT_ATTRIBUTES = {
    "黑龙权杖": {
        "main": "claw_power",
        "main_val": 200,
        "sub": "luck",
        "sub_val": 100,
        "effect": "attack_vampire_10",  # 攻击10%吸血
        "rarity": "legendary",
    },
    "金龙权杖": {
        "main": "perception",
        "main_val": 200,
        "sub": "shell",
        "sub_val": 100,
        "effect": "heal_boost_30",  # 治疗效果+30%
        "rarity": "legendary",
    },
    "空间之刃": {
        "main": "swim_speed",
        "main_val": 200,
        "sub": "claw_power",
        "sub_val": 100,
        "effect": "dodge_15",  # 闪避+15%
        "rarity": "legendary",
    },
    "时间之锤": {
        "main": "shell",
        "main_val": 200,
        "sub": "perception",
        "sub_val": 100,
        "effect": "cd_reduction_20",  # 技能冷却-20%
        "rarity": "legendary",
    },
    "魔女斗篷": {
        "main": "shrimp_wit",
        "main_val": 200,
        "sub": "swim_speed",
        "sub_val": 100,
        "effect": "stealth_10",  # 隐身+10%
        "rarity": "legendary",
    },
    "繁荣权杖": {
        "main": "luck",
        "main_val": 200,
        "sub": "claw_power",
        "sub_val": 100,
        "effect": "gold_bonus_25",  # 金贝收益+25%
        "rarity": "legendary",
    },
    "圣诞权杖": {
        "main": "perception",
        "main_val": 150,
        "sub": "shrimp_wit",
        "sub_val": 150,
        "effect": "xp_bonus_30",  # 经验+30%
        "rarity": "epic",
    },
    "龙行之剑": {
        "main": "swim_speed",
        "main_val": 180,
        "sub": "claw_power",
        "sub_val": 120,
        "effect": "combo_rate_20",  # 连击率+20%
        "rarity": "epic",
    },
    "龙影雕像": {
        "main": "luck",
        "main_val": 180,
        "sub": "shell",
        "sub_val": 120,
        "effect": "no_drop_on_death",  # 死亡不掉落
        "rarity": "epic",
    },
}

# 获取神器图标
def get_artifact_icon(name: str) -> str:
    return ARTIFACT_ICONS.get(name, "❓")

# 获取神器完整信息
def get_artifact_info(name: str) -> dict:
    base = {
        "name": name,
        "icon": ARTIFACT_ICONS.get(name, "❓"),
    }
    if name in ARTIFACT_ATTRIBUTES:
        base.update(ARTIFACT_ATTRIBUTES[name])
    return base

# 获取所有神器列表
def get_all_artifacts() -> list:
    return [get_artifact_info(name) for name in ARTIFACT_ICONS.keys()]
