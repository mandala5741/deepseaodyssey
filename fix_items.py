#!/usr/bin/env python3
"""重建items表 - 所有物品都有TEXT item_id，兼容use_item函数"""
from items import ITEMS
from models import get_db, get_cursor

# 完整物品列表（TEXT item_id）
ALL_ITEMS = [
    # ===== items.py 原生物品 =====
    # 消耗品 - HP恢复
    {"item_id": "1", "name": "体力药水", "icon": "🧪", "type": "consumable", "price": 100, "description": "恢复50点体力", "effect_type": "energy", "effect_value": 50},
    {"item_id": "2", "name": "超级体力药剂", "icon": "⚗️", "type": "consumable", "price": 300, "description": "恢复500点体力", "effect_type": "energy", "effect_value": 500},
    {"item_id": "3", "name": "海藻丸", "icon": "💊", "type": "consumable", "price": 30, "description": "HP/MP/体力全部恢复满", "effect_type": "all", "effect_value": 9999},
    {"item_id": "4", "name": "珍珠露", "icon": "💧", "type": "consumable", "price": 50, "description": "恢复HP和MP各50点", "effect_type": "both", "effect_value": 50},
    {"item_id": "5", "name": "深海灵芝", "icon": "🌿", "type": "consumable", "price": 80, "description": "恢复HP和MP各100点", "effect_type": "both", "effect_value": 100},
    {"item_id": "6", "name": "珊瑚精华", "icon": "🪸", "type": "consumable", "price": 90, "description": "恢复MP 60点", "effect_type": "mp", "effect_value": 60},

    # 永久增益
    {"item_id": "10", "name": "钳力灵石", "icon": "💎", "type": "permanent", "price": 600, "description": "永久+1钳力（限购5次）", "effect_type": "perm_claw", "effect_value": 1},
    {"item_id": "11", "name": "甲壳水晶", "icon": "🔮", "type": "permanent", "price": 600, "description": "永久+1甲壳（限购5次）", "effect_type": "perm_shell", "effect_value": 1},
    {"item_id": "12", "name": "疾速鱼鳃", "icon": "🌊", "type": "permanent", "price": 600, "description": "永久+1游速（限购5次）", "effect_type": "perm_speed", "effect_value": 1},
    {"item_id": "13", "name": "智慧宝珠", "icon": "🔮", "type": "permanent", "price": 600, "description": "永久+1虾慧（限购5次）", "effect_type": "perm_wisdom", "effect_value": 1},

    # 战斗增益
    {"item_id": "20", "name": "力量贝壳", "icon": "🐚", "type": "consumable", "price": 100, "description": "下次战斗+20%攻击", "effect_type": "buff", "effect_value": 20},
    {"item_id": "21", "name": "铁鳞护甲", "icon": "🛡️", "type": "consumable", "price": 100, "description": "下次战斗+20%防御", "effect_type": "buff", "effect_value": 20},
    {"item_id": "22", "name": "迅疾水流", "icon": "🌊", "type": "consumable", "price": 100, "description": "下次战斗+20%速度", "effect_type": "buff", "effect_value": 20},
    {"item_id": "23", "name": "幸运珍珠", "icon": "💠", "type": "consumable", "price": 100, "description": "幸运+10%", "effect_type": "luck", "effect_value": 10},

    # 特殊
    {"item_id": "30", "name": "免战牌", "icon": "🛡️", "type": "consumable", "price": 200, "description": "使用后进入保护状态30分钟", "effect_type": "peace", "effect_value": 30},
    {"item_id": "31", "name": "双倍经验卡", "icon": "🎫", "type": "consumable", "price": 300, "description": "使用后1小时内经验翻倍", "effect_type": "xp_2x", "effect_value": 0},

    # ===== 系统商品（9001+ TEXT item_id）=====
    {"item_id": "exp_boost", "name": "双倍经验卡", "icon": "🎫", "type": "consumable", "price": 500, "description": "使用后1小时内经验翻倍", "effect_type": "xp_2x", "effect_value": 0},
    {"item_id": "peace_token", "name": "免战牌", "icon": "🛡️", "type": "consumable", "price": 300, "description": "使用后进入保护状态30分钟", "effect_type": "peace", "effect_value": 30},
    {"item_id": "claw_stone", "name": "钳力灵石", "icon": "💎", "type": "permanent", "price": 1000, "description": "永久增加钳力+5", "effect_type": "perm_claw", "effect_value": 5},
    {"item_id": "shell_crystal", "name": "甲壳水晶", "icon": "🔮", "type": "permanent", "price": 1000, "description": "永久增加甲壳+5", "effect_type": "perm_shell", "effect_value": 5},
    {"item_id": "speed_gill", "name": "疾速鱼鳃", "icon": "🌊", "type": "permanent", "price": 1000, "description": "永久增加游速+5", "effect_type": "perm_speed", "effect_value": 5},
    {"item_id": "wisdom_orb", "name": "智慧宝珠", "icon": "🔮", "type": "permanent", "price": 1000, "description": "永久增加虾慧+5", "effect_type": "perm_wisdom", "effect_value": 5},
    {"item_id": "shrimp_elixir", "name": "虾黄丹", "icon": "⚗️", "type": "consumable", "price": 700, "description": "恢复HP和MP各500点", "effect_type": "all", "effect_value": 500},
    {"item_id": "abyss_vigor", "name": "深渊活力剂", "icon": "🧪", "type": "consumable", "price": 500, "description": "恢复体力500点", "effect_type": "energy", "effect_value": 500},
    {"item_id": "power_shell", "name": "力量贝壳", "icon": "🐚", "type": "permanent", "price": 300, "description": "钳力+20，战力+20", "effect_type": "perm_claw", "effect_value": 20},
    {"item_id": "iron_scales", "name": "铁鳞护甲", "icon": "🛡️", "type": "permanent", "price": 300, "description": "甲壳+20，战力+20", "effect_type": "perm_shell", "effect_value": 20},
    {"item_id": "swift_current", "name": "迅疾水流", "icon": "🌊", "type": "permanent", "price": 300, "description": "游速+20，战力+20", "effect_type": "perm_speed", "effect_value": 20},
    {"item_id": "seaweed_pill", "name": "海藻丸", "icon": "💊", "type": "consumable", "price": 80, "description": "HP/MP/体力全部恢复满", "effect_type": "all", "effect_value": 9999},
    {"item_id": "pearl_dew", "name": "珍珠露", "icon": "💧", "type": "consumable", "price": 120, "description": "HP恢复2000点", "effect_type": "hp", "effect_value": 2000},
    {"item_id": "deep_sea_herb", "name": "深海灵芝", "icon": "🌿", "type": "consumable", "price": 150, "description": "MP恢复1000点", "effect_type": "mp", "effect_value": 1000},
]

def fix_items():
    with get_db() as conn:
        with get_cursor(conn) as cur:
            for item in ALL_ITEMS:
                # 先删除已有（按item_id）
                cur.execute("DELETE FROM items WHERE item_id = %s", (item["item_id"],))
                # 插入新数据（同时设置id和item_id）
                cur.execute("""
                    INSERT INTO items (item_id, name, icon, type, price, description, effect_type, effect_value)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    item["item_id"], item["name"], item["icon"], item["type"],
                    item["price"], item["description"],
                    item["effect_type"], item["effect_value"]
                ))
            conn.commit()
            print(f"Inserted/updated {len(ALL_ITEMS)} items")

if __name__ == "__main__":
    fix_items()
