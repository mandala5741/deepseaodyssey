#!/usr/bin/env python3
"""重建物品表 - 包含所有游戏物品和系统商品"""
from models import get_db, get_cursor

# 完整物品数据（effect_type匹配use_item函数的期望）
GAME_ITEMS = [
    # 消耗品 - HP恢复
    {"id": 1, "name": "体力药水", "icon": "🧪", "type": "consumable", "price": 100, "description": "恢复50点体力", "effect_type": "energy", "effect_value": 50, "rarity": "common"},
    {"id": 2, "name": "超级体力药剂", "icon": "⚗️", "type": "consumable", "price": 300, "description": "恢复500点体力", "effect_type": "energy", "effect_value": 500, "rarity": "rare"},
    {"id": 3, "name": "海藻丸", "icon": "💊", "type": "consumable", "price": 30, "description": "HP/MP/体力全部恢复满", "effect_type": "all", "effect_value": 9999, "rarity": "common"},
    {"id": 4, "name": "珍珠露", "icon": "💧", "type": "consumable", "price": 50, "description": "恢复HP和MP各50点", "effect_type": "both", "effect_value": 50, "rarity": "common"},
    {"id": 5, "name": "深海灵芝", "icon": "🌿", "type": "consumable", "price": 80, "description": "恢复HP和MP各100点", "effect_type": "both", "effect_value": 100, "rarity": "common"},
    {"id": 6, "name": "珊瑚精华", "icon": "🪸", "type": "consumable", "price": 90, "description": "恢复MP 60点", "effect_type": "mp", "effect_value": 60, "rarity": "common"},

    # 永久增益
    {"id": 10, "name": "钳力灵石", "icon": "💎", "type": "permanent", "price": 600, "description": "永久+1钳力（限购5次）", "effect_type": "perm_claw", "effect_value": 1, "rarity": "rare"},
    {"id": 11, "name": "甲壳水晶", "icon": "🔮", "type": "permanent", "price": 600, "description": "永久+1甲壳（限购5次）", "effect_type": "perm_shell", "effect_value": 1, "rarity": "rare"},
    {"id": 12, "name": "疾速鱼鳃", "icon": "🌊", "type": "permanent", "price": 600, "description": "永久+1游速（限购5次）", "effect_type": "perm_speed", "effect_value": 1, "rarity": "rare"},
    {"id": 13, "name": "智慧宝珠", "icon": "🔮", "type": "permanent", "price": 600, "description": "永久+1虾慧（限购5次）", "effect_type": "perm_wisdom", "effect_value": 1, "rarity": "rare"},

    # 战斗增益
    {"id": 20, "name": "力量贝壳", "icon": "🐚", "type": "consumable", "price": 100, "description": "下次战斗+20%攻击", "effect_type": "buff", "effect_value": 20, "rarity": "common"},
    {"id": 21, "name": "铁鳞护甲", "icon": "🛡️", "type": "consumable", "price": 100, "description": "下次战斗+20%防御", "effect_type": "buff", "effect_value": 20, "rarity": "common"},
    {"id": 22, "name": "迅疾水流", "icon": "🌊", "type": "consumable", "price": 100, "description": "下次战斗+20%速度", "effect_type": "buff", "effect_value": 20, "rarity": "common"},
    {"id": 23, "name": "幸运珍珠", "icon": "💠", "type": "consumable", "price": 100, "description": "幸运+10%", "effect_type": "luck", "effect_value": 10, "rarity": "common"},

    # 特殊
    {"id": 30, "name": "免战牌", "icon": "🛡️", "type": "consumable", "price": 200, "description": "使用后进入保护状态30分钟", "effect_type": "peace", "effect_value": 30, "rarity": "rare"},
    {"id": 31, "name": "双倍经验卡", "icon": "🎫", "type": "consumable", "price": 300, "description": "使用后1小时内经验翻倍", "effect_type": "xp_2x", "effect_value": 0, "rarity": "rare"},

    # 系统商品（固定ID 9001+）
    {"id": 9001, "name": "双倍经验卡", "icon": "🎫", "type": "consumable", "price": 500, "description": "使用后1小时内经验翻倍", "effect_type": "xp_2x", "effect_value": 0, "rarity": "rare"},
    {"id": 9002, "name": "免战牌", "icon": "🛡️", "type": "consumable", "price": 300, "description": "使用后进入保护状态30分钟", "effect_type": "peace", "effect_value": 30, "rarity": "rare"},
    {"id": 9003, "name": "钳力灵石", "icon": "💎", "type": "permanent", "price": 1000, "description": "永久增加钳力+5", "effect_type": "perm_claw", "effect_value": 5, "rarity": "rare"},
    {"id": 9004, "name": "甲壳水晶", "icon": "🔮", "type": "permanent", "price": 1000, "description": "永久增加甲壳+5", "effect_type": "perm_shell", "effect_value": 5, "rarity": "rare"},
    {"id": 9005, "name": "疾速鱼鳃", "icon": "🌊", "type": "permanent", "price": 1000, "description": "永久增加游速+5", "effect_type": "perm_speed", "effect_value": 5, "rarity": "rare"},
    {"id": 9006, "name": "智慧宝珠", "icon": "🔮", "type": "permanent", "price": 1000, "description": "永久增加虾慧+5", "effect_type": "perm_wisdom", "effect_value": 5, "rarity": "rare"},
    {"id": 9007, "name": "虾黄丹", "icon": "⚗️", "type": "consumable", "price": 700, "description": "恢复HP和MP各500点", "effect_type": "all", "effect_value": 500, "rarity": "epic"},
    {"id": 9008, "name": "深渊活力剂", "icon": "🧪", "type": "consumable", "price": 500, "description": "恢复体力500点", "effect_type": "energy", "effect_value": 500, "rarity": "epic"},
    {"id": 9009, "name": "力量贝壳", "icon": "🐚", "type": "permanent", "price": 300, "description": "钳力+20，战力+20", "effect_type": "buff", "effect_value": 20, "rarity": "epic"},
    {"id": 9010, "name": "铁鳞护甲", "icon": "🛡️", "type": "permanent", "price": 300, "description": "甲壳+20，战力+20", "effect_type": "shell", "effect_value": 20, "rarity": "epic"},
    {"id": 9011, "name": "迅疾水流", "icon": "🌊", "type": "permanent", "price": 300, "description": "游速+20，战力+20", "effect_type": "speed", "effect_value": 20, "rarity": "epic"},
    {"id": 9012, "name": "海藻丸", "icon": "💊", "type": "consumable", "price": 80, "description": "HP/MP/体力全部恢复满", "effect_type": "all", "effect_value": 9999, "rarity": "legendary"},
    {"id": 9013, "name": "珍珠露", "icon": "💧", "type": "consumable", "price": 120, "description": "HP恢复2000点", "effect_type": "hp", "effect_value": 2000, "rarity": "legendary"},
    {"id": 9014, "name": "深海灵芝", "icon": "🌿", "type": "consumable", "price": 150, "description": "MP恢复1000点", "effect_type": "mp", "effect_value": 1000, "rarity": "legendary"},
]

def import_all_items():
    with get_db() as conn:
        with get_cursor(conn) as cur:
            for item in GAME_ITEMS:
                cur.execute("""
                    INSERT INTO items (id, name, icon, type, price, description, effect_type, effect_value, rarity)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name=EXCLUDED.name, icon=EXCLUDED.icon, type=EXCLUDED.type,
                        price=EXCLUDED.price, description=EXCLUDED.description,
                        effect_type=EXCLUDED.effect_type, effect_value=EXCLUDED.effect_value, rarity=EXCLUDED.rarity
                """, (
                    item["id"], item["name"], item["icon"], item["type"], item["price"],
                    item["description"], item["effect_type"], item["effect_value"], item["rarity"]
                ))
            conn.commit()
            print(f"Imported {len(GAME_ITEMS)} items")

if __name__ == "__main__":
    import_all_items()
