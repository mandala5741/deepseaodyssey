#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""系统市集 - 系统定期生成的稀有物品"""

import uuid
import random
import time
from datetime import datetime, timedelta
from models import get_db, get_cursor

# 系统商品池（稀有/史诗/传说）
SYSTEM_ITEMS = [
    # 稀有物品
    {"type": "item", "key": "exp_boost", "name": "双倍经验卡", "icon": "🎫", "rarity": "rare", "price_range": (300, 600), "item_id": 9001},
    {"type": "item", "key": "peace_token", "name": "免战牌", "icon": "🛡️", "rarity": "rare", "price_range": (200, 400), "item_id": 9002},
    {"type": "item", "key": "claw_stone", "name": "钳力灵石", "icon": "💎", "rarity": "rare", "price_range": (800, 1200), "item_id": 9003},
    {"type": "item", "key": "shell_crystal", "name": "甲壳水晶", "icon": "🔮", "rarity": "rare", "price_range": (800, 1200), "item_id": 9004},
    {"type": "item", "key": "speed_gill", "name": "疾速鱼鳃", "icon": "🌊", "rarity": "rare", "price_range": (800, 1200), "item_id": 9005},
    {"type": "item", "key": "wisdom_orb", "name": "智慧宝珠", "icon": "🔮", "rarity": "rare", "price_range": (800, 1200), "item_id": 9006},
    # 史诗物品
    {"type": "item", "key": "shrimp_elixir", "name": "虾黄丹", "icon": "⚗️", "rarity": "epic", "price_range": (500, 900), "item_id": 9007},
    {"type": "item", "key": "abyss_vigor", "name": "深渊活力剂", "icon": "🧪", "rarity": "epic", "price_range": (400, 700), "item_id": 9008},
    {"type": "item", "key": "power_shell", "name": "力量贝壳", "icon": "🐚", "rarity": "epic", "price_range": (200, 350), "item_id": 9009},
    {"type": "item", "key": "iron_scales", "name": "铁鳞护甲", "icon": "🛡️", "rarity": "epic", "price_range": (200, 350), "item_id": 9010},
    {"type": "item", "key": "swift_current", "name": "迅疾水流", "icon": "🌊", "rarity": "epic", "price_range": (200, 350), "item_id": 9011},
    # 传说物品
    {"type": "item", "key": "seaweed_pill", "name": "海藻丸", "icon": "💊", "rarity": "legendary", "price_range": (50, 100), "item_id": 9012},
    {"type": "item", "key": "pearl_dew", "name": "珍珠露", "icon": "💧", "rarity": "legendary", "price_range": (80, 150), "item_id": 9013},
    {"type": "item", "key": "deep_sea_herb", "name": "深海灵芝", "icon": "🌿", "rarity": "legendary", "price_range": (120, 200), "item_id": 9014},
]

SYSTEM_ARTIFACTS = [
    {"type": "artifact", "key": "crown_of_depths", "name": "深海帝王冠", "icon": "👑", "rarity": "legendary", "price_range": (500000, 1000000)},
    {"type": "artifact", "key": "trident_abyss", "name": "三叉戟·深渊", "icon": "🔱", "rarity": "legendary", "price_range": (500000, 1000000)},
    {"type": "artifact", "key": "eternal_diamond", "name": "永恒钻石", "icon": "💎", "rarity": "legendary", "price_range": (500000, 1000000)},
    {"type": "artifact", "key": "pearl_dragon_orb", "name": "珍珠龙珠", "icon": "🐉", "rarity": "legendary", "price_range": (500000, 1000000)},
    {"type": "artifact", "key": "anchors_of_poseidon", "name": "海神锚", "icon": "⚓", "rarity": "legendary", "price_range": (400000, 800000)},
    {"type": "artifact", "key": "ghost_eye", "name": "幽灵眼", "icon": "👁️", "rarity": "epic", "price_range": (80000, 150000)},
    {"type": "artifact", "key": "shadow_cloak", "name": "暗影披风", "icon": "🧥", "rarity": "epic", "price_range": (80000, 150000)},
    {"type": "artifact", "key": "undead_fang", "name": "亡灵之牙", "icon": "🦷", "rarity": "epic", "price_range": (60000, 120000)},
    {"type": "artifact", "key": "skull_key", "name": "骷髅钥匙", "icon": "🗝️", "rarity": "epic", "price_range": (50000, 100000)},
    {"type": "artifact", "key": "cursed_blade", "name": "诅咒之刃", "icon": "⚔️", "rarity": "epic", "price_range": (100000, 200000)},
    {"type": "artifact", "key": "skull_crown", "name": "骷髅王冠", "icon": "💀", "rarity": "legendary", "price_range": (200000, 500000)},
]

SYSTEM_SELLER_ID = None  # NULL 表示系统卖家

def get_last_generate_time():
    """获取上次生成时间"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT val FROM game_meta WHERE key = 'system_market_last_generate'")
            row = cur.fetchone()
            if row:
                return datetime.fromisoformat(row['val'])
            return None

def set_last_generate_time(t=None):
    if t is None:
        t = datetime.now()
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                INSERT INTO game_meta (key, val) VALUES ('system_market_last_generate', %s)
                ON CONFLICT (key) DO UPDATE SET val = %s
            """, (t.isoformat(), t.isoformat()))

def cleanup_expired_system_listings():
    """清理过期的系统上架（48小时自动下架）"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                UPDATE market_listings
                SET status = 'expired'
                WHERE seller_id IS NULL AND status = 'active'
                AND created_at < NOW() - INTERVAL '48 hours'
            """)

def generate_system_listings():
    """生成新的系统上架"""
    now = datetime.now()
    last = get_last_generate_time()

    # 每6小时生成一次，或者首次生成
    if last and (now - last).total_seconds() < 6 * 3600:
        return 0

    cleanup_expired_system_listings()

    with get_db() as conn:
        with get_cursor(conn) as cur:
            # 每次生成3-6个商品
            count = random.randint(3, 6)
            generated = 0

            for _ in range(count):
                # 70%物品，30%神器
                if random.random() < 0.7:
                    pool = SYSTEM_ITEMS
                    rarity_weights = [("common", 0.3), ("rare", 0.4), ("epic", 0.2), ("legendary", 0.1)]
                    # 按权重选稀有度
                    roll = random.random()
                    cum = 0
                    chosen_rarity = "rare"
                    for r, w in rarity_weights:
                        cum += w
                        if roll <= cum:
                            chosen_rarity = r
                            break
                    candidates = [i for i in pool if i["rarity"] == chosen_rarity]
                    if not candidates:
                        candidates = pool
                    item = random.choice(candidates)
                    quantity = 1
                else:
                    pool = SYSTEM_ARTIFACTS
                    rarity_weights = [("rare", 0.15), ("epic", 0.45), ("legendary", 0.4)]
                    roll = random.random()
                    cum = 0
                    chosen_rarity = "epic"
                    for r, w in rarity_weights:
                        cum += w
                        if roll <= cum:
                            chosen_rarity = r
                            break
                    candidates = [i for i in pool if i["rarity"] == chosen_rarity]
                    if not candidates:
                        candidates = pool
                    item = random.choice(candidates)
                    quantity = 1

                price = random.randint(*item["price_range"])

                # 查artifact的DB id
                artifact_db_id = None
                item_type = item.get("type", "item")
                if item_type == "artifact":
                    # 神器：存储artifact_id字符串
                    cur.execute("SELECT artifact_id FROM artifacts WHERE artifact_id = %s", (item["key"],))
                    row = cur.fetchone()
                    if not row:
                        continue
                    item_key = row["artifact_id"]
                else:
                    # 物品：存储integer item_id
                    item_id = item.get("item_id")
                    if not item_id:
                        continue
                    item_key = str(item_id)

                listing_id = str(uuid.uuid4())

                cur.execute("""
                    INSERT INTO market_listings
                    (listing_id, seller_id, item_type, item_key, item_name, item_icon, quantity, price, rarity, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'active', NOW())
                """, (
                    listing_id, SYSTEM_SELLER_ID,
                    item_type, item_key, item["name"], item["icon"],
                    quantity, price, item["rarity"]
                ))
                generated += 1

            set_last_generate_time(now)
            return generated

def is_system_listing(listing):
    """判断是否系统上架"""
    return listing.get('seller_id') is None or listing.get('is_system')
