#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""物品数据"""

ITEMS = {
    # 恢复类
    "seaweed_pill": {
        "name": "海藻丸",
        "type": "consumable",
        "price": 30,
        "effect": {"hp": 50},
        "description": "恢复50点HP"
    },
    "pearl_dew": {
        "name": "珍珠露",
        "type": "consumable",
        "price": 50,
        "effect": {"mp": 30},
        "description": "恢复30点MP"
    },
    "deep_sea_herb": {
        "name": "深海灵芝",
        "type": "consumable",
        "price": 80,
        "effect": {"hp": 100},
        "description": "恢复100点HP"
    },
    "coral_essence": {
        "name": "珊瑚精华",
        "type": "consumable",
        "price": 90,
        "effect": {"mp": 60},
        "description": "恢复60点MP"
    },
    "energy_potion": {
        "name": "体力药水",
        "type": "consumable",
        "price": 100,
        "effect": {"energy": 50},
        "description": "恢复50点体力"
    },
    "shrimp_elixir": {
        "name": "虾黄丹",
        "type": "consumable",
        "price": 350,
        "effect": {"hp": 9999, "mp": 9999},
        "description": "恢复满HP和MP"
    },
    "abyss_vigor": {
        "name": "深渊活力剂",
        "type": "consumable",
        "price": 250,
        "effect": {"energy": 100},
        "description": "恢复100点体力"
    },
    
    # 战斗增益类
    "power_shell": {
        "name": "力量贝壳",
        "type": "consumable",
        "price": 100,
        "effect": {"buff": {"type": "attack", "value": 0.2}},
        "description": "下次战斗+20%攻击"
    },
    "iron_scales": {
        "name": "铁鳞护甲",
        "type": "consumable",
        "price": 100,
        "effect": {"buff": {"type": "defense", "value": 0.2}},
        "description": "下次战斗+20%防御"
    },
    "swift_current": {
        "name": "迅疾水流",
        "type": "consumable",
        "price": 100,
        "effect": {"buff": {"type": "speed", "value": 0.2}},
        "description": "下次战斗+20%速度"
    },
    
    # 永久增益类
    "claw_stone": {
        "name": "钳力灵石",
        "type": "permanent",
        "price": 600,
        "max_stack": 5,
        "effect": {"permanent": {"attr": "claw", "value": 1}},
        "description": "永久+1钳力（限购5次）"
    },
    "shell_crystal": {
        "name": "甲壳水晶",
        "type": "permanent",
        "price": 600,
        "max_stack": 5,
        "effect": {"permanent": {"attr": "shell", "value": 1}},
        "description": "永久+1甲壳（限购5次）"
    },
    "speed_gill": {
        "name": "疾速鱼鳃",
        "type": "permanent",
        "price": 600,
        "max_stack": 5,
        "effect": {"permanent": {"attr": "speed", "value": 1}},
        "description": "永久+1游速（限购5次）"
    },
    "wisdom_orb": {
        "name": "智慧宝珠",
        "type": "permanent",
        "price": 600,
        "max_stack": 5,
        "effect": {"permanent": {"attr": "wisdom", "value": 1}},
        "description": "永久+1虾慧（限购5次）"
    },
    
    # 特殊道具
    "exp_boost": {
        "name": "双倍经验卡",
        "type": "consumable",
        "price": 200,
        "effect": {"exp_multiplier": 3},
        "description": "接下来3次任务双倍经验"
    },
    "peace_token": {
        "name": "免战牌",
        "type": "consumable",
        "price": 100,
        "effect": {"peace": 86400},
        "description": "24小时内不会被挑战"
    }
}
