#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""技能数据"""

SKILLS = {
    # 通用技能
    "shrimp_punch": {
        "name": "虾拳",
        "type": "attack",
        "mp_cost": 0,
        "damage_formula": "claw * 1.0",
        "description": "最基本的攻击技能，所有龙虾天生就会"
    },
    "hard_shell": {
        "name": "硬壳功",
        "type": "defense",
        "mp_cost": 5,
        "defense_bonus": 0.3,
        "description": "将内力灌注甲壳，减少受到30%伤害"
    },
    
    # 铁钳派技能
    "iron_claw_strike": {
        "name": "铁钳重击",
        "faction": "iron_claw",
        "type": "attack",
        "mp_cost": 10,
        "damage_formula": "claw * 1.5",
        "crit_chance": 0.2,
        "description": "铁钳派绝技，有20%几率暴击"
    },
    "crushing_clamp": {
        "name": "碎甲钳",
        "faction": "iron_claw",
        "type": "attack",
        "mp_cost": 25,
        "damage_formula": "claw * 2.0",
        "description": "无视对方部分防御的重击"
    },
    
    # 玄甲派技能
    "shell_reflect": {
        "name": "甲壳反震",
        "faction": "mystic_shell",
        "type": "defense",
        "mp_cost": 15,
        "defense_bonus": 0.5,
        "reflect": 0.2,
        "description": "大幅减少伤害，并反弹20%给对手"
    },
    "titanium_shell": {
        "name": "钛甲护体",
        "faction": "mystic_shell",
        "type": "defense",
        "mp_cost": 30,
        "defense_bonus": 0.7,
        "description": "化为钛甲，减少70%伤害"
    },
    
    # 幻影派技能
    "shadow_strike": {
        "name": "影步突袭",
        "faction": "phantom",
        "type": "attack",
        "mp_cost": 10,
        "damage_formula": "speed * 1.8",
        "always_crit": True,
        "description": "必定先手并暴击"
    },
    "phantom_slash": {
        "name": "残影连斩",
        "faction": "phantom",
        "type": "attack",
        "mp_cost": 25,
        "damage_formula": "speed * 1.0",
        "hits": 3,
        "description": "化为残影，三连击"
    },
    "deep_sea_phantom": {
        "name": "深海幻灭",
        "faction": "phantom",
        "type": "attack",
        "mp_cost": 50,
        "damage_formula": "speed * 3.5",
        "always_crit": True,
        "description": "幻影派终极技能，必定暴击"
    },
    
    # 智谋派技能
    "wisdom_blast": {
        "name": "智慧冲击",
        "faction": "wisdom_school",
        "type": "attack",
        "mp_cost": 15,
        "damage_formula": "wisdom * 2.0",
        "mp_drain": 0.1,
        "description": "消耗对方10%当前MP"
    },
    "mana_shield": {
        "name": "法力护盾",
        "faction": "wisdom_school",
        "type": "defense",
        "mp_cost": 20,
        "damage_reduction": 0.4,
        "mp_absorb": 0.2,
        "description": "用MP抵挡伤害，并吸收20%转为己用"
    },
    "enlightenment": {
        "name": "大彻大悟",
        "faction": "wisdom_school",
        "type": "ultimate",
        "mp_cost": 100,
        "effect": "heal_and_buff",
        "description": "智谋派终极技能，恢复满状态并获得增益"
    }
}
