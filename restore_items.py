#!/usr/bin/env python3
"""恢复所有缺失的物品到items表"""
from models import get_db, get_cursor

# 根据原items.py + 游戏常见物品恢复
RESTORE_ITEMS = [
    {"item_id": "0", "name": "空物品", "icon": "📦", "type": "misc", "price": 0, "description": "无", "effect_type": None, "effect_value": 0},
    {"item_id": "1", "name": "体力药水", "icon": "🧪", "type": "consumable", "price": 100, "description": "恢复50点体力", "effect_type": "energy", "effect_value": 50},
    {"item_id": "2", "name": "超级体力药剂", "icon": "⚗️", "type": "consumable", "price": 300, "description": "恢复500点体力", "effect_type": "energy", "effect_value": 500},
    {"item_id": "3", "name": "海藻丸", "icon": "💊", "type": "consumable", "price": 30, "description": "HP/MP/体力全部恢复满", "effect_type": "all", "effect_value": 9999},
    {"item_id": "4", "name": "珍珠露", "icon": "💧", "type": "consumable", "price": 50, "description": "恢复HP和MP各50点", "effect_type": "both", "effect_value": 50},
    {"item_id": "5", "name": "深海灵芝", "icon": "🌿", "type": "consumable", "price": 80, "description": "恢复HP和MP各100点", "effect_type": "both", "effect_value": 100},
    {"item_id": "6", "name": "珊瑚精华", "icon": "🪸", "type": "consumable", "price": 90, "description": "恢复MP 60点", "effect_type": "mp", "effect_value": 60},
    {"item_id": "9", "name": "海星碎片", "icon": "⭐", "type": "material", "price": 20, "description": "合成材料", "effect_type": None, "effect_value": 0},
    {"item_id": "11", "name": "甲壳水晶", "icon": "🔮", "type": "permanent", "price": 600, "description": "永久+1甲壳", "effect_type": "perm_shell", "effect_value": 1},
    {"item_id": "15", "name": "力量精华", "icon": "💪", "type": "material", "price": 50, "description": "强化材料", "effect_type": None, "effect_value": 0},
    {"item_id": "17", "name": "防御碎片", "icon": "🛡️", "type": "material", "price": 50, "description": "强化材料", "effect_type": None, "effect_value": 0},
    {"item_id": "18", "name": "敏捷鱼鳞", "icon": "🐟", "type": "material", "price": 50, "description": "强化材料", "effect_type": None, "effect_value": 0},
    {"item_id": "19", "name": "智慧之滴", "icon": "💡", "type": "material", "price": 50, "description": "强化材料", "effect_type": None, "effect_value": 0},
    {"item_id": "20", "name": "力量贝壳", "icon": "🐚", "type": "consumable", "price": 100, "description": "下次战斗+20%攻击", "effect_type": "buff", "effect_value": 20},
    {"item_id": "21", "name": "铁鳞护甲", "icon": "🛡️", "type": "consumable", "price": 100, "description": "下次战斗+20%防御", "effect_type": "buff", "effect_value": 20},
    {"item_id": "24", "name": "幸运符", "icon": "🍀", "type": "consumable", "price": 100, "description": "幸运+10%", "effect_type": "luck", "effect_value": 10},
    {"item_id": "25", "name": "经验水晶", "icon": "💎", "type": "consumable", "price": 150, "description": "获得200经验", "effect_type": "xp", "effect_value": 200},
    {"item_id": "26", "name": "金币袋", "icon": "💰", "type": "consumable", "price": 50, "description": "获得100金贝", "effect_type": "gold", "effect_value": 100},
    {"item_id": "27", "name": "体力恢复剂", "icon": "⚡", "type": "consumable", "price": 80, "description": "恢复30点体力", "effect_type": "energy", "effect_value": 30},
    {"item_id": "28", "name": "MP恢复药", "icon": "💜", "type": "consumable", "price": 80, "description": "恢复30点MP", "effect_type": "mp", "effect_value": 30},
    {"item_id": "29", "name": "稀有矿石", "icon": "�ite", "type": "material", "price": 100, "description": "高级合成材料", "effect_type": None, "effect_value": 0},
    {"item_id": "31", "name": "双倍经验卡", "icon": "🎫", "type": "consumable", "price": 300, "description": "1小时经验翻倍", "effect_type": "xp_2x", "effect_value": 0},
    {"item_id": "33", "name": "珍珠", "icon": "📌", "type": "material", "price": 30, "description": "合成材料", "effect_type": None, "effect_value": 0},
    {"item_id": "35", "name": "贝壳碎片", "icon": "🐚", "type": "material", "price": 15, "description": "基础材料", "effect_type": None, "effect_value": 0},
    {"item_id": "37", "name": "海藻种子", "icon": "🌱", "type": "material", "price": 20, "description": "种植材料", "effect_type": None, "effect_value": 0},
    {"item_id": "38", "name": "小型体力药水", "icon": "🧪", "type": "consumable", "price": 30, "description": "恢复20点体力", "effect_type": "energy", "effect_value": 20},
    {"item_id": "39", "name": "中型体力药水", "icon": "🧪", "type": "consumable", "price": 60, "description": "恢复40点体力", "effect_type": "energy", "effect_value": 40},
    {"item_id": "40", "name": "钳力精华", "icon": "💎", "type": "material", "price": 80, "description": "钳力强化材料", "effect_type": None, "effect_value": 0},
    {"item_id": "41", "name": "甲壳碎片", "icon": "🛡️", "type": "material", "price": 80, "description": "甲壳强化材料", "effect_type": None, "effect_value": 0},
    {"item_id": "42", "name": "游速鱼鳞", "icon": "🌊", "type": "material", "price": 80, "description": "游速强化材料", "effect_type": None, "effect_value": 0},
    {"item_id": "43", "name": "智慧灵液", "icon": "💧", "type": "material", "price": 80, "description": "智慧强化材料", "effect_type": None, "effect_value": 0},
    {"item_id": "44", "name": "混合精华", "icon": "⚗️", "type": "material", "price": 100, "description": "全能强化材料", "effect_type": None, "effect_value": 0},
    {"item_id": "45", "name": "稀有贝壳", "icon": "🪸", "type": "material", "price": 120, "description": "稀有材料", "effect_type": None, "effect_value": 0},
    {"item_id": "46", "name": "深海珍珠", "icon": "💠", "type": "material", "price": 150, "description": "高级材料", "effect_type": None, "effect_value": 0},
    {"item_id": "47", "name": "龙虾钳", "icon": "🦞", "type": "material", "price": 60, "description": "食材/材料", "effect_type": None, "effect_value": 0},
    {"item_id": "48", "name": "海胆刺", "icon": "🦔", "type": "material", "price": 60, "description": "武器材料", "effect_type": None, "effect_value": 0},
    {"item_id": "49", "name": "海马尾", "icon": "🐴", "type": "material", "price": 50, "description": "合成材料", "effect_type": None, "effect_value": 0},
    {"item_id": "50", "name": "珊瑚枝", "icon": "🪸", "type": "material", "price": 40, "description": "装饰/合成材料", "effect_type": None, "effect_value": 0},
    {"item_id": "51", "name": "海星干", "icon": "⭐", "type": "material", "price": 30, "description": "食材材料", "effect_type": None, "effect_value": 0},
    {"item_id": "52", "name": "海螺壳", "icon": "🐚", "type": "material", "price": 25, "description": "基础材料", "effect_type": None, "effect_value": 0},
    {"item_id": "53", "name": "鲨鱼牙", "icon": "🦈", "type": "material", "price": 70, "description": "武器材料", "effect_type": None, "effect_value": 0},
    {"item_id": "54", "name": "水母触须", "icon": "🪼", "type": "material", "price": 65, "description": "防具材料", "effect_type": None, "effect_value": 0},
    {"item_id": "55", "name": "章鱼墨汁", "icon": "🐙", "type": "material", "price": 55, "description": "道具材料", "effect_type": None, "effect_value": 0},
    {"item_id": "56", "name": "鲸鱼肉", "icon": "🐋", "type": "material", "price": 90, "description": "食材材料", "effect_type": None, "effect_value": 0},
    {"item_id": "57", "name": "海龟壳", "icon": "🐢", "type": "material", "price": 85, "description": "防具材料", "effect_type": None, "effect_value": 0},
    {"item_id": "58", "name": "蝠鳐翼", "icon": "🦅", "type": "material", "price": 75, "description": "饰品材料", "effect_type": None, "effect_value": 0},
    {"item_id": "59", "name": "宝箱钥匙", "icon": "🗝️", "type": "consumable", "price": 200, "description": "打开宝箱", "effect_type": None, "effect_value": 0},
    {"item_id": "60", "name": "幸运草", "icon": "🍀", "type": "material", "price": 100, "description": "幸运道具材料", "effect_type": None, "effect_value": 0},
    {"item_id": "61", "name": "龙涎香", "icon": "💎", "type": "material", "price": 200, "description": "传说级材料", "effect_type": None, "effect_value": 0},
    {"item_id": "62", "name": "千年珍珠", "icon": "💠", "type": "material", "price": 500, "description": "神话级材料", "effect_type": None, "effect_value": 0},
    {"item_id": "70", "name": "免战牌", "icon": "🛡️", "type": "consumable", "price": 200, "description": "保护30分钟", "effect_type": "peace", "effect_value": 30},
    {"item_id": "79", "name": "传说贝壳", "icon": "🪸", "type": "material", "price": 300, "description": "传说级合成材料", "effect_type": None, "effect_value": 0},
    {"item_id": "80", "name": "神话精华", "icon": "✨", "type": "material", "price": 1000, "description": "神话级强化材料", "effect_type": None, "effect_value": 0},
    {"item_id": "88", "name": "荣耀之证", "icon": "🏆", "type": "material", "price": 5000, "description": "荣耀奖励材料", "effect_type": None, "effect_value": 0},
    # 系统商品 (TEXT keys)
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

def restore():
    with get_db() as conn:
        with get_cursor(conn) as cur:
            count = 0
            for item in RESTORE_ITEMS:
                # 先删除旧的（按item_id）
                cur.execute("DELETE FROM items WHERE item_id = %s", (item["item_id"],))
                # 插入新数据（同时设置id和item_id）
                id_val = int(item["item_id"]) if item["item_id"].isdigit() else None
                cur.execute("""
                    INSERT INTO items (item_id, name, icon, type, price, description, effect_type, effect_value)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    item["item_id"], item["name"], item["icon"], item["type"],
                    item["price"], item["description"],
                    item["effect_type"], item["effect_value"]
                ))
                count += 1
            conn.commit()
            print(f"Restored {count} items")

if __name__ == "__main__":
    restore()
