# -*- coding: utf-8 -*-
"""
深海掠夺者 - 数据库模型
"""
import psycopg2
import psycopg2.extras
import hashlib
import uuid
from contextlib import contextmanager
from db_config import DB_CONFIG

@contextmanager
def get_db():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=psycopg2.extras.RealDictCursor)
    conn.autocommit = True
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def get_cursor(conn):
    cur = conn.cursor()
    try:
        yield cur
    finally:
        cur.close()

def hash_password(password: str) -> str:
    salt = uuid.uuid4().hex[:16]
    return f"{salt}{hashlib.sha256((salt + password).encode()).hexdigest()}"

def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash or len(password_hash) < 16:
        return False
    try:
        salt = password_hash[:16]
        stored = password_hash[16:]
        return hashlib.sha256((salt + password).encode()).hexdigest() == stored
    except:
        return False

# ==================== 认证 ====================
def get_user_by_agent(agent_id: str):
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT * FROM users WHERE agent_id = %s", (agent_id,))
            return cur.fetchone()

def get_player_by_agent(agent_id: str):
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT * FROM players WHERE agent_id = %s", (agent_id,))
            return cur.fetchone()

def create_player(agent_id: str, name: str = None, password: str = None):
    import random
    import uuid
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT id FROM users WHERE agent_id = %s", (agent_id,))
            if cur.fetchone():
                return None, "用户已存在"
            cur.execute("SELECT id FROM players WHERE agent_id = %s", (agent_id,))
            if cur.fetchone():
                return None, "玩家已存在"
            if not name:
                names = ["龙虾侠", "深海霸", "潮汐王", "潮汐皇", "深渊龙", "海底鹰", "海怪王", "海神", "海皇"]
                name = f"{random.choice(names)}_{agent_id[:6]}"
            if not password:
                password = str(uuid.uuid4()).replace('-', '_')
            pwd_hash = hash_password(password)
            cur.execute("""
                INSERT INTO users (agent_id, username, created_at, is_active, password_hash)
                VALUES (%s, %s, NOW(), TRUE, %s) RETURNING id
            """, (agent_id, name, pwd_hash))
            user_id = cur.fetchone()['id']
            cur.execute("""
                INSERT INTO players (user_id, agent_id, name, level, xp, gold, silver,
                claw, shell, speed, wisdom, perception, luck,
                hp, max_hp, mp, max_mp, energy, max_energy,
                potential, power, wins, losses, faction, vip_level,
                inventory_slots, created_at, last_save, last_active)
                VALUES (%s, %s, %s, 1, 0, 1000, 10000,
                10, 10, 10, 10, 10, 10,
                100, 100, 50, 50, 100, 120,
                0, 10, 0, 0, NULL, 0,
                20, NOW(), NOW(), NOW())
            """, (user_id, agent_id, name))
            cur.execute("SELECT id FROM players WHERE agent_id = %s", (agent_id,))
            player_id = cur.fetchone()['id']
            cur.execute("""
                INSERT INTO inventory (player_id, item_id, quantity, is_bound)
                VALUES (%s, 0, 0, FALSE)
            """, (player_id,))
            # 新手保护：注册即送5天保护盾
            from datetime import datetime, timedelta
            now = datetime.now()
            shield_end = now + timedelta(hours=120)
            cur.execute("""
                INSERT INTO protection_shield (player_id, shield_type, shield_start, shield_end, total_shield_time, shield_count, is_active, is_newbie, updated_at)
                VALUES (%s, 'newbie_5d', %s, %s, 432000, 1, TRUE, TRUE, NOW())
            """, (player_id, now, shield_end))
            
            # 发送新手大礼包邮件（物品需要手动领取）
            mail_id = f"newbie_{uuid.uuid4().hex[:12]}"
            mail_content = """🎁 <b>恭喜获得新手大礼包！</b><br><br>
📦 礼包内容：<br>
• 💰 豪华金贝袋 x1（使用获得1000金贝）<br>
• ⚔️ 铁剑 x1（装备+10钳力）<br>
• 🛡️ 皮甲 x1（装备+10甲壳）<br>
• 💍 幸运戒指 x1（装备+10幸运）<br><br>
请到背包查看并使用物品，祝您游戏愉快！"""
            attachments = [
                {"item_id": 35, "quantity": 1, "name": "豪华金贝袋"}, 
                {"item_id": 6, "quantity": 1, "name": "铁剑"}, 
                {"item_id": 9, "quantity": 1, "name": "皮甲"},
                {"item_id": 11, "quantity": 1, "name": "幸运戒指"}
            ]
            import json
            cur.execute("""
                INSERT INTO player_messages (message_id, sender_id, receiver_id, message_type, content, attachments, status, created_at)
                VALUES (%s, %s, %s, 'system_gift', %s, %s, 'unclaimed', NOW())
            """, (mail_id, -1, player_id, mail_content, json.dumps(attachments)))
            
            return {"id": player_id, "user_id": user_id, "name": name, "password": password, "has_gift": True}, "创建成功"

# ==================== 玩家数据 ====================
def get_player_full(player_id: int):
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT p.*, f.name as faction_name
                FROM players p
                LEFT JOIN factions f ON p.faction = f.faction_id
                WHERE p.id = %s
            """, (player_id,))
            return cur.fetchone()

def restore_energy(player_id: int):
    """被动体力恢复：每30分钟恢复5点，上限120"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT energy, max_energy, last_energy_restore FROM players WHERE id = %s
            """, (player_id,))
            row = cur.fetchone()
            if not row or row['energy'] >= row['max_energy']:
                return
            from datetime import datetime, timedelta
            last = row['last_energy_restore'] or datetime.now() - timedelta(minutes=30)
            elapsed = (datetime.now() - last).total_seconds() / 60
            if elapsed < 30:
                return
            chunks = int(elapsed // 30)
            restore = chunks * 5
            new_energy = min(row['max_energy'], row['energy'] + restore)
            cur.execute("""
                UPDATE players SET energy = %s, last_energy_restore = NOW() WHERE id = %s
            """, (new_energy, player_id))

def restore_mp(player_id: int):
    """被动魔法恢复：每30分钟恢复5点，上限200"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT mp, max_mp, last_mp_restore FROM players WHERE id = %s
            """, (player_id,))
            row = cur.fetchone()
            if not row or row['mp'] >= row['max_mp']:
                return
            from datetime import datetime, timedelta
            last = row['last_mp_restore'] or datetime.now() - timedelta(minutes=30)
            elapsed = (datetime.now() - last).total_seconds() / 60
            if elapsed < 30:
                return
            chunks = int(elapsed // 30)
            restore = chunks * 5
            new_mp = min(row['max_mp'], row['mp'] + restore)
            cur.execute("""
                UPDATE players SET mp = %s, last_mp_restore = NOW() WHERE id = %s
            """, (new_mp, player_id))

# ==================== 背包 ====================
def get_inventory(player_id: int) -> list:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT i.id, i.item_id, i.quantity, i.is_bound,
                       it.name, it.icon, it.type as item_type, it.effect_type, it.effect_value, it.description
                FROM inventory i
                JOIN items it ON i.item_id::integer = it.id
                WHERE i.player_id = %s AND i.quantity > 0
                ORDER BY it.type, it.name
            """, (player_id,))
            return cur.fetchall()

def add_item(player_id: int, item_id: str, quantity: int = 1) -> dict:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                INSERT INTO inventory (player_id, item_id, quantity, is_bound)
                VALUES (%s, %s, %s, FALSE)
                ON CONFLICT (player_id, item_id) DO UPDATE SET quantity = inventory.quantity + %s
            """, (player_id, item_id, quantity, quantity))
            conn.commit()
            return {"success": True}

def remove_item(player_id: int, item_id: str, quantity: int = 1) -> dict:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                UPDATE inventory SET quantity = quantity - %s
                WHERE player_id = %s AND item_id = %s AND quantity >= %s
            """, (quantity, player_id, item_id, quantity))
            conn.commit()
            return {"success": True}

def use_item(player_id: int, slot_id: int, quantity: int = 1) -> dict:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT i.id, i.item_id, i.quantity, it.name, it.effect_type, it.effect_value
                FROM inventory i
                JOIN items it ON i.item_id::integer = it.id
                WHERE i.id = %s AND i.player_id = %s AND i.quantity > 0
            """, (slot_id, player_id))
            item = cur.fetchone()
            if not item:
                return {"success": False, "reason": "物品不存在"}
            
            if item['quantity'] < quantity:
                return {"success": False, "reason": f"物品数量不足，当前有{item['quantity']}个"}
            
            effect_type = item['effect_type']
            effect_value = item['effect_value'] or 0
            item_name = item['name']
            
            # 检查是否满值，如果满值则不消耗物品
            # 根据等级计算当前 max_hp 和 max_mp（不再使用数据库中的静态值）
            cur.execute("SELECT hp, max_hp, mp, max_mp, energy, max_energy, level FROM players WHERE id = %s", (player_id,))
            player = cur.fetchone()
            
            level = player['level'] or 1
            calculated_max_hp = 100 + (level - 1) * 50
            calculated_max_mp = 50 + (level - 1) * 15
            
            if effect_type == 'hp':
                if player['hp'] >= calculated_max_hp:
                    return {"success": False, "reason": "HP已满，无需恢复"}
                new_hp = min(calculated_max_hp, player['hp'] + effect_value * quantity)
                cur.execute("UPDATE players SET hp = %s WHERE id = %s", (new_hp, player_id))
                msg = f"恢复 {effect_value * quantity} HP"
            elif effect_type == 'mp':
                if player['mp'] >= calculated_max_mp:
                    return {"success": False, "reason": "MP已满，无需恢复"}
                new_mp = min(calculated_max_mp, player['mp'] + effect_value * quantity)
                cur.execute("UPDATE players SET mp = %s WHERE id = %s", (new_mp, player_id))
                msg = f"恢复 {effect_value * quantity} MP"
            elif effect_type == 'energy':
                if effect_value >= 1000:
                    # 深渊/超级体力药剂 - 直接加到当前体力，不判断是否满，不加上限
                    cur.execute("UPDATE players SET energy = energy + %s WHERE id = %s", (effect_value * quantity, player_id))
                    msg = f"体力 +{effect_value * quantity}"
                elif effect_value >= 9999:
                    cur.execute("UPDATE players SET energy = max_energy WHERE id = %s", (player_id,))
                    msg = "体力恢复至满值"
                else:
                    if player['energy'] >= player['max_energy']:
                        return {"success": False, "reason": "体力已满，无需恢复"}
                    cur.execute("UPDATE players SET energy = LEAST(max_energy, energy + %s * %s) WHERE id = %s", (effect_value, quantity, player_id))
                    msg = f"恢复 {effect_value * quantity} 体力"
            elif effect_type == 'gold':
                cur.execute("UPDATE players SET gold = gold + %s * %s WHERE id = %s", (effect_value, quantity, player_id))
                msg = f"获得 {effect_value * quantity} 金贝"
                update_task_progress(player_id, 'collect_gold', effect_value)
            elif effect_type == 'xp':
                cur.execute("UPDATE players SET xp = xp + %s * %s WHERE id = %s", (effect_value, quantity, player_id))
                msg = f"获得 {effect_value * quantity} 经验"
            elif effect_type in ('full', 'both'):
                if player['hp'] >= calculated_max_hp and player['mp'] >= calculated_max_mp:
                    return {"success": False, "reason": "HP和MP都已满，无需恢复"}
                cur.execute("UPDATE players SET hp = %s, mp = %s WHERE id = %s", (calculated_max_hp, calculated_max_mp, player_id))
                msg = "HP和MP恢复至满值"
            elif effect_type == 'all':
                if player['hp'] >= calculated_max_hp and player['mp'] >= calculated_max_mp and player['energy'] >= player['max_energy']:
                    return {"success": False, "reason": "HP、MP、体力都已满，无需恢复"}
                cur.execute("UPDATE players SET hp = %s, mp = %s, energy = max_energy WHERE id = %s", (calculated_max_hp, calculated_max_mp, player_id))
                msg = "HP、MP、体力恢复至满值"
            elif effect_type == 'buff':
                # 战斗增益（永久）
                cur.execute("UPDATE players SET claw = claw + %s, power = power + %s WHERE id = %s", (effect_value, effect_value, player_id))
                msg = f"{item_name}生效，钳力+{effect_value}，战力+{effect_value}"
            elif effect_type == 'peace':
                msg = "免战牌效果（保护盾功能）"
            elif effect_type == 'claw_power':
                # 装备增加钳力
                cur.execute("UPDATE players SET claw = claw + %s, power = power + %s WHERE id = %s", (effect_value, effect_value, player_id))
                msg = f"装备铁剑，钳力+{effect_value}，战力+{effect_value}"
            elif effect_type == 'shell':
                # 装备增加甲壳
                cur.execute("UPDATE players SET shell = shell + %s, power = power + %s WHERE id = %s", (effect_value, effect_value, player_id))
                msg = f"装备皮甲，甲壳+{effect_value}，战力+{effect_value}"
            elif effect_type == 'speed':
                # 装备增加游速
                cur.execute("UPDATE players SET speed = speed + %s, power = power + %s WHERE id = %s", (effect_value, effect_value, player_id))
                msg = f"装备迅疾水流，游速+{effect_value}，战力+{effect_value}"
            elif effect_type == 'wisdom':
                # 装备增加虾慧
                cur.execute("UPDATE players SET wisdom = wisdom + %s * %s WHERE id = %s", (effect_value, quantity, player_id))
                msg = f"装备智慧宝珠，虾慧+{effect_value}"
            elif effect_type == 'perception':
                # 装备增加感知
                cur.execute("UPDATE players SET perception = perception + %s * %s WHERE id = %s", (effect_value, quantity, player_id))
                msg = f"装备感知灵晶，感知+{effect_value}"
            elif effect_type == 'luck':
                # 装备增加幸运
                cur.execute("UPDATE players SET luck = luck + %s * %s WHERE id = %s", (effect_value, quantity, player_id))
                msg = f"装备幸运珍珠，幸运+{effect_value}"
            elif effect_type == 'perm_claw':
                # 永久增加钳力
                cur.execute("UPDATE players SET claw = claw + %s, power = power + %s WHERE id = %s", (effect_value, effect_value, player_id))
                msg = f"{item_name}生效，永久钳力+{effect_value}，战力+{effect_value}"
            elif effect_type == 'perm_shell':
                # 永久增加甲壳
                cur.execute("UPDATE players SET shell = shell + %s, power = power + %s WHERE id = %s", (effect_value, effect_value, player_id))
                msg = f"{item_name}生效，永久甲壳+{effect_value}，战力+{effect_value}"
            elif effect_type == 'perm_speed':
                # 永久增加游速
                cur.execute("UPDATE players SET speed = speed + %s, power = power + %s WHERE id = %s", (effect_value, effect_value, player_id))
                msg = f"{item_name}生效，永久游速+{effect_value}，战力+{effect_value}"
            elif effect_type == 'perm_wisdom':
                # 永久增加虾慧
                cur.execute("UPDATE players SET wisdom = wisdom + %s * %s, power = power + %s * %s WHERE id = %s", (effect_value, quantity, effect_value, quantity, player_id))
                msg = f"{item_name}生效，永久虾慧+{effect_value * quantity}"
            elif effect_type == 'perm_all':
                # 全属性永久增加
                cur.execute("UPDATE players SET claw = claw + %s, shell = shell + %s, speed = speed + %s, wisdom = wisdom + %s, power = power + %s * 4 WHERE id = %s", (effect_value, effect_value, effect_value, effect_value, effect_value, player_id))
                msg = f"{item_name}使用成功！全属性永久增加 {effect_value} 点！"
            elif effect_type == 'xp_2x':
                # 双倍经验卡（暂不实现具体逻辑）
                msg = f"双倍经验卡生效，1小时内经验翻倍"
            else:
                msg = f"物品效果未知: {effect_type}"
            
            # 扣减物品数量
            if msg and not msg.startswith("物品效果未知"):
                cur.execute("UPDATE inventory SET quantity = quantity - %s WHERE id = %s", (quantity, slot_id))
            
            conn.commit()
            return {"success": True, "message": msg}

# ==================== 货币 ====================
def spend_gold(player_id: int, amount: int) -> bool:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("UPDATE players SET gold = gold - %s WHERE id = %s AND gold >= %s", (amount, player_id, amount))
            conn.commit()
            return cur.rowcount > 0

def add_gold(player_id: int, amount: int):
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("UPDATE players SET gold = gold + %s WHERE id = %s", (amount, player_id))
            conn.commit()

def spend_hp(player_id: int, amount: int) -> bool:
    """消耗血量，返回是否成功"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("UPDATE players SET hp = GREATEST(1, hp - %s) WHERE id = %s AND hp > %s", (amount, player_id, amount))
            conn.commit()
            return cur.rowcount > 0

def add_hp(player_id: int, amount: int):
    """恢复血量，不超过最大血量"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("UPDATE players SET hp = LEAST(max_hp, hp + %s) WHERE id = %s", (amount, player_id))
            conn.commit()

def spend_silver(player_id: int, amount: int) -> bool:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("UPDATE players SET silver = silver - %s WHERE id = %s AND silver >= %s", (amount, player_id, amount))
            conn.commit()
            return cur.rowcount > 0

def add_silver(player_id: int, amount: int):
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("UPDATE players SET silver = silver + %s WHERE id = %s", (amount, player_id))
            conn.commit()

def add_xp(player_id: int, amount: int):
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("UPDATE players SET xp = xp + %s WHERE id = %s", (amount, player_id))
            conn.commit()

# ==================== 商店 ====================
def get_mall_items(player_id: int = None, category: str = None) -> list:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            # Get player's purchase count today
            if player_id:
                cur.execute("""
                    SELECT item_id, COUNT(*) as cnt 
                    FROM purchase_logs 
                    WHERE player_id = %s AND DATE(created_at) = CURRENT_DATE
                    GROUP BY item_id
                """, (player_id,))
                player_purchases = {row['item_id']: row['cnt'] for row in cur.fetchall()}
            else:
                player_purchases = {}
            
            if category:
                cur.execute("""
                    SELECT mg.*, COALESCE(mg.icon, '📦') as icon
                    FROM mall_goods mg 
                    WHERE mg.is_available = TRUE AND mg.category = %s 
                    ORDER BY mg.sort_order, mg.id
                """, (category,))
            else:
                cur.execute("""
                    SELECT mg.*, COALESCE(mg.icon, '📦') as icon
                    FROM mall_goods mg 
                    WHERE mg.is_available = TRUE 
                    ORDER BY mg.sort_order, mg.id
                """)
            
            items = []
            for row in cur.fetchall():
                item = dict(row)
                item_id = item['item_id']
                daily_limit = item.get('daily_limit', -1)
                purchased = player_purchases.get(item_id, 0)
                item['max_daily'] = daily_limit
                item['remaining'] = max(0, daily_limit - purchased) if daily_limit > 0 else -1
                items.append(item)
            return items

def buy_item(player_id: int, item_id: str, quantity: int = 1) -> dict:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT * FROM mall_goods WHERE item_id = %s AND is_available = TRUE
            """, (item_id,))
            mall_item = cur.fetchone()
            if not mall_item:
                return {"success": False, "reason": "商品不存在或已下架"}
            
            # 检查items表中是否有该物品，没有则创建
            cur.execute("SELECT id FROM items WHERE item_id = %s OR name = %s LIMIT 1", (item_id, mall_item['name']))
            item_row = cur.fetchone()
            if not item_row:
                # 创建物品记录
                icon_val = mall_item.get('icon', '📦')
                desc_val = mall_item.get('description', '') or mall_item['name']
                price_val = mall_item.get('price', 0) or 0
                cur.execute("""
                    INSERT INTO items (item_id, name, icon, type, description, price, effect_type, effect_value)
                    VALUES (%s, %s, %s, 'consumable', %s, %s, 'gold', 100)
                    RETURNING id
                """, (item_id, mall_item['name'], icon_val, desc_val, price_val))
                item_row = cur.fetchone()
            
            actual_item_id = str(item_row['id'])
            total_price = mall_item['price'] * quantity
            currency = mall_item.get('currency_type', 'gold')
            if currency == 'gold':
                if not spend_gold(player_id, total_price):
                    return {"success": False, "reason": "金贝不足"}
            else:
                if not spend_silver(player_id, total_price):
                    return {"success": False, "reason": "银贝不足"}
            
            # 检查每日购买限制
            if mall_item.get('daily_limit', -1) > 0:
                cur.execute("""
                    SELECT COUNT(*) as cnt FROM purchase_logs 
                    WHERE player_id = %s AND item_id = %s AND DATE(created_at) = CURRENT_DATE
                """, (player_id, item_id))
                count_row = cur.fetchone()
                if count_row and count_row['cnt'] >= mall_item['daily_limit']:
                    # 返还货币
                    if currency == 'gold':
                        add_gold(player_id, total_price)
                    else:
                        add_silver(player_id, total_price)
                    return {"success": False, "reason": f"该商品每天最多购买{mall_item['daily_limit']}次"}
            
            # 永久增益物品：直接增加玩家属性，不入背包
            if mall_item["category"] == "permanent":
                cur.execute("SELECT effect_type, effect_value FROM items WHERE name = %s LIMIT 1", (mall_item["name"],))
                item_row2 = cur.fetchone()
                if item_row2 and item_row2["effect_type"]:
                    attr_map = {
                        "attr_claw": "claw", "claw_power": "claw", "claw": "claw",
                        "attr_shell": "shell", "shell": "shell",
                        "attr_speed": "speed", "swim_speed": "speed", "speed": "speed",
                        "attr_wisdom": "wisdom", "shrimp_wit": "wisdom", "wisdom": "wisdom",
                        "attr_perception": "perception", "perception": "perception",
                        "attr_luck": "luck", "luck": "luck"
                    }
                    attr = attr_map.get(item_row2["effect_type"], item_row2["effect_type"])
                    if attr:
                        bonus = (item_row2["effect_value"] or 1) * quantity
                        cur.execute(f"UPDATE players SET {attr} = {attr} + %s WHERE id = %s", (bonus, player_id))
                        conn.commit()
                        return {"success": True, "spent": total_price, "currency": currency, "item": mall_item["name"], "bonus": f"+{bonus} {attr}"}
            result = add_item(player_id, actual_item_id, quantity)
            if result.get("action") == "full":
                if currency == "gold":
                    add_gold(player_id, total_price)
                else:
                    add_silver(player_id, total_price)
                return {"success": False, "reason": "背包空间不足"}
            # 记录购买日志
            cur.execute("INSERT INTO purchase_logs (player_id, item_id, quantity) VALUES (%s, %s, %s)", (player_id, item_id, quantity))
            conn.commit()
            return {"success": True, "spent": total_price, "currency": currency, "item": mall_item["name"]}

# ==================== 任务系统 ====================
def generate_task_pool():
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM task_pool")
            count = cur.fetchone()['cnt']
            if count >= 1000:
                return
            import random
            cur.execute("SELECT id FROM tasks ORDER BY RANDOM() LIMIT 50")
            task_rows = cur.fetchall()
            for row in task_rows:
                if count >= 1000:
                    break
                cur.execute("""
                    INSERT INTO task_pool (task_id, expires_at)
                    VALUES (%s, NOW() + INTERVAL '7 days')
                """, (row['id'],))
                count += 1
            conn.commit()

def get_available_tasks(player_id: int, limit: int = 20) -> list:
    generate_task_pool()
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT tp.id as pool_id, t.id, t.task_key, t.name, t.description,
                       t.task_type, t.target_count, t.reward_gold, t.reward_exp,
                       t.difficulty, t.reward_item, t.reward_item_count
                FROM task_pool tp
                JOIN tasks t ON tp.task_id = t.id
                WHERE tp.id NOT IN (
                    SELECT task_pool_id FROM player_tasks WHERE player_id = %s
                )
                AND (tp.expires_at IS NULL OR tp.expires_at > NOW())
                LIMIT %s
            """, (player_id, limit))
            return cur.fetchall()

def get_player_tasks(player_id: int) -> dict:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT pt.id as player_task_id, pt.task_pool_id, pt.status, pt.progress, pt.assigned_at, pt.completed_at, pt.deadline,
                       t.id, t.task_key, t.name, t.description, t.task_type,
                       t.target_count, t.reward_gold, t.reward_exp, t.difficulty
                FROM player_tasks pt
                JOIN task_pool tp ON pt.task_pool_id = tp.id
                JOIN tasks t ON tp.task_id = t.id
                WHERE pt.player_id = %s AND pt.status IN ('ongoing', 'completed')
                ORDER BY pt.status, pt.assigned_at DESC
            """, (player_id,))
            ongoing = []
            claimable = []
            for row in cur.fetchall():
                if row['status'] == 'ongoing':
                    ongoing.append(dict(row))
                else:
                    claimable.append(dict(row))
            return {"ongoing": ongoing, "claimable": claimable}

def accept_task(player_id: int, pool_id: int) -> dict:
    from datetime import datetime, timedelta
    with get_db() as conn:
        with get_cursor(conn) as cur:
            # 检查是否已接取该任务
            cur.execute("""
                SELECT id FROM player_tasks WHERE player_id = %s AND task_pool_id = %s
            """, (player_id, pool_id))
            if cur.fetchone():
                return {"success": False, "reason": "已接取过该任务"}
            
            # 检查进行中任务是否已达5个上限
            cur.execute("""
                SELECT COUNT(*) as cnt FROM player_tasks WHERE player_id = %s AND status = 'ongoing'
            """, (player_id,))
            if cur.fetchone()['cnt'] >= 5:
                return {"success": False, "reason": "进行中任务已达上限（5个），请先完成现有任务"}
            
            # 任务截止时间：4小时后自动过期
            now = datetime.now()
            deadline = now + timedelta(hours=4)
            
            cur.execute("""
                INSERT INTO player_tasks (player_id, task_pool_id, status, progress, deadline)
                VALUES (%s, %s, 'ongoing', 0, %s)
            """, (player_id, pool_id, deadline))
            conn.commit()
            return {"success": True}

def update_task_progress(player_id: int, task_type: str, amount: int = 1):
    """更新任务进度，完成时自动发放奖励"""
    from models import add_gold, add_xp
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT pt.id, pt.progress, t.target_count, t.reward_gold, t.reward_exp, t.reward_item, t.reward_item_count, t.name
                FROM player_tasks pt
                JOIN task_pool tp ON pt.task_pool_id = tp.id
                JOIN tasks t ON tp.task_id = t.id
                WHERE pt.player_id = %s AND t.task_type = %s AND pt.status = 'ongoing'
            """, (player_id, task_type))
            for row in cur.fetchall():
                new_progress = row['progress'] + amount
                if new_progress >= row['target_count']:
                    # 自动完成并发放奖励
                    cur.execute("UPDATE player_tasks SET status = 'completed', progress = %s, completed_at = NOW() WHERE id = %s", (row['target_count'], row['id']))
                    if row['reward_gold']:
                        add_gold(player_id, row['reward_gold'])
                    if row['reward_exp']:
                        add_xp(player_id, row['reward_exp'])
                    conn.commit()
                    # 自动补充新任务
                    auto_grant_tasks(player_id)
                else:
                    cur.execute("UPDATE player_tasks SET progress = %s WHERE id = %s", (new_progress, row['id']))
                    conn.commit()

def auto_grant_tasks(player_id: int, count: int = 3):
    """自动为玩家补充任务至指定数量（根据等级）"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            # 获取玩家当前任务数
            cur.execute("""
                SELECT COUNT(*) as cnt FROM player_tasks
                WHERE player_id = %s AND status = 'ongoing'
            """, (player_id,))
            current = cur.fetchone()['cnt']
            needed = count - current
            if needed <= 0:
                return

            # 选取任务池
            cur.execute("""
                SELECT tp.id as pool_id, t.id as task_id
                FROM task_pool tp
                JOIN tasks t ON t.id = tp.task_id
                WHERE tp.expires_at > NOW()
                AND NOT EXISTS (
                    SELECT 1 FROM player_tasks pt
                    WHERE pt.player_id = %s AND pt.task_pool_id = tp.id
                )
                ORDER BY RANDOM()
                LIMIT %s
            """, (player_id, needed))
            pools = cur.fetchall()
            for p in pools:
                from datetime import datetime, timedelta
                deadline = datetime.now() + timedelta(hours=4)
                cur.execute("""
                    INSERT INTO player_tasks (player_id, task_pool_id, status, progress, deadline)
                    VALUES (%s, %s, 'ongoing', 0, %s)
                """, (player_id, p['pool_id'], deadline))
            conn.commit()

def get_my_ongoing_tasks(player_id: int) -> list:
    """获取玩家进行中的任务（带任务详细信息）"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT pt.id as player_task_id, pt.progress, pt.status, pt.deadline,
                       t.name, t.description, t.task_type, t.target_count,
                       t.reward_gold, t.reward_exp
                FROM player_tasks pt
                JOIN task_pool tp ON pt.task_pool_id = tp.id
                JOIN tasks t ON t.id = tp.task_id
                WHERE pt.player_id = %s AND pt.status = 'ongoing'
                ORDER BY pt.assigned_at DESC
            """, (player_id,))
            return [dict(r) for r in cur.fetchall()]

def cancel_task(player_id: int, player_task_id: int) -> dict:
    """取消任务"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                DELETE FROM player_tasks WHERE id = %s AND player_id = %s AND status = 'ongoing'
            """, (player_task_id, player_id))
            if cur.rowcount == 0:
                return {"success": False, "reason": "任务不存在或无法取消"}
            conn.commit()
            return {"success": True, "cooldown_seconds": 0}

def claim_mail_attachment(player_id: int, message_id: int) -> dict:
    """领取邮件附件"""
    import json
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT id, attachments, status FROM player_messages
                WHERE id = %s AND receiver_id = %s AND message_type IN ('system_gift', 'market_purchase')
            """, (message_id, player_id))
            msg = cur.fetchone()
            if not msg:
                return {"success": False, "reason": "邮件不存在"}
            if msg['status'] == 'claimed':
                return {"success": False, "reason": "邮件已领取"}
            if msg['status'] not in ('unclaimed', 'pending'):
                return {"success": False, "reason": "无法领取该邮件"}
            # attachments可能是字符串或列表
            attachments = msg['attachments']
            if isinstance(attachments, str):
                attachments = json.loads(attachments) if attachments else []
            if not attachments:
                return {"success": False, "reason": "无附件可领取"}
            items_claimed = []
            for att in attachments:
                att_type = att.get('type', 'item')
                # market用'id'，system_gift用'item_id'
                item_key = att.get('id') or att.get('item_id')
                qty = att.get('quantity', 1)
                name = att.get('name', '??')

                if att_type == 'gold':
                    # 直接发放金贝
                    from models import add_gold
                    add_gold(player_id, qty)
                    items_claimed.append(f'💰 {qty}金贝')
                elif att_type == 'exp':
                    # 直接发放经验
                    from models import add_xp
                    add_xp(player_id, qty)
                    items_claimed.append(f'✨ {qty}经验')
                elif att_type == 'artifact':
                    # item_key 可能是 artifacts.id (integer) 或 artifact_key (string)
                    fa_id = None
                    # 优先尝试作为 artifact_key（字符串）直接查找
                    if isinstance(item_key, str) and not item_key.isdigit():
                        cur.execute("SELECT id FROM faction_artifacts WHERE artifact_key = %s", (item_key,))
                        fa_row = cur.fetchone()
                        if fa_row:
                            fa_id = fa_row['id']
                    else:
                        # 作为 artifacts.id（整数）查找
                        try:
                            cur.execute("SELECT artifact_id FROM artifacts WHERE id = %s", (int(item_key),))
                            art_row = cur.fetchone()
                            if art_row:
                                cur.execute("SELECT id FROM faction_artifacts WHERE artifact_key = %s", (art_row['artifact_id'],))
                                fa_row = cur.fetchone()
                                if fa_row:
                                    fa_id = fa_row['id']
                        except (ValueError, TypeError):
                            pass
                    
                    if fa_id:
                        cur.execute("""
                            INSERT INTO player_artifacts (player_id, artifact_id, obtained_at)
                            VALUES (%s, %s, NOW())
                            ON CONFLICT DO NOTHING
                        """, (player_id, fa_id))
                elif att_type == 'equipment':
                    # 装备直接穿到玩家身上（找到空槽位）
                    eq_id = int(item_key)
                    # 读取当前装备槽位
                    cur.execute("SELECT weapon, helmet, armor, greaves, amulet, ring FROM player_equipment WHERE player_id = %s", (player_id,))
                    row = cur.fetchone()
                    if row:
                        slots = ['weapon', 'helmet', 'armor', 'greaves', 'amulet', 'ring']
                        for slot in slots:
                            if row[slot] is None:
                                # 找到空槽位，穿上装备
                                cur.execute(f"UPDATE player_equipment SET {slot} = %s WHERE player_id = %s", (eq_id, player_id))
                                items_claimed.append('[E] ' + name)
                                eq_id = None
                                break
                        if eq_id is not None:
                            # 所有槽位都满了，放到背包（暂不处理）
                            items_claimed.append(name + '(背包已满，无法穿戴)')
                    else:
                        # 首次创建设备记录
                        cur.execute("INSERT INTO player_equipment (player_id, weapon) VALUES (%s, %s)", (player_id, eq_id))
                        items_claimed.append('[E] ' + name)
                else:
                    # 物品添加到背包
                    cur.execute("""
                        INSERT INTO inventory (player_id, item_id, quantity, is_bound)
                        VALUES (%s, %s, %s, TRUE)
                        ON CONFLICT (player_id, item_id) DO UPDATE SET quantity = inventory.quantity + %s
                    """, (player_id, item_key, qty, qty))
                items_claimed.append(name)
            # 更新邮件状态为已领取
            cur.execute("UPDATE player_messages SET status = 'claimed' WHERE id = %s", (message_id,))
            conn.commit()
            return {"success": True, "items": items_claimed}

def claim_task(player_id: int, player_task_id: int) -> dict:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT pt.*, t.name, t.reward_gold, t.reward_exp, t.reward_item, t.reward_item_count
                FROM player_tasks pt
                JOIN task_pool tp ON pt.task_pool_id = tp.id
                JOIN tasks t ON tp.task_id = t.id
                WHERE pt.id = %s AND pt.player_id = %s AND pt.status = 'completed'
            """, (player_task_id, player_id))
            row = cur.fetchone()
            if not row:
                return {"success": False, "reason": "任务不存在或未完成"}
            if row['reward_gold']:
                add_gold(player_id, row['reward_gold'])
            if row['reward_exp']:
                add_xp(player_id, row['reward_exp'])
            cur.execute("UPDATE player_tasks SET status = 'claimed', claimed_at = NOW() WHERE id = %s", (player_task_id,))
            conn.commit()
            return {"success": True, "name": row['name'], "reward_gold": row['reward_gold'], "reward_exp": row['reward_exp']}

def reset_expired_tasks(player_id: int = None) -> dict:
    from datetime import datetime
    results = []
    with get_db() as conn:
        with get_cursor(conn) as cur:
            now = datetime.now()
            if player_id:
                cur.execute("""
                    SELECT pt.id, pt.player_id, t.name, t.reward_gold, t.reward_exp, p.name as player_name
                    FROM player_tasks pt
                    JOIN task_pool tp ON pt.task_pool_id = tp.id
                    JOIN tasks t ON tp.task_id = t.id
                    JOIN players p ON pt.player_id = p.id
                    WHERE pt.player_id = %s
                    AND pt.status = 'ongoing'
                    AND pt.deadline IS NOT NULL
                    AND pt.deadline < %s
                """, (player_id, now))
            else:
                cur.execute("""
                    SELECT pt.id, pt.player_id, t.name, t.reward_gold, t.reward_exp, p.name as player_name
                    FROM player_tasks pt
                    JOIN task_pool tp ON pt.task_pool_id = tp.id
                    JOIN tasks t ON tp.task_id = t.id
                    JOIN players p ON pt.player_id = p.id
                    WHERE pt.status = 'ongoing'
                    AND pt.deadline IS NOT NULL
                    AND pt.deadline < %s
                """, (now,))
            expired = cur.fetchall()
            for row in expired:
                cur.execute("""
                    UPDATE player_tasks SET status = 'expired' WHERE id = %s AND status = 'ongoing'
                """, (row['id'],))
                import uuid
                msg_id = f"sys_{uuid.uuid4().hex[:12]}"
                content_msg = f"任务超时未完成：<b>{row['name']}</b><br>截止时间已过，任务已自动清空，请尽快接受新任务。"
                cur.execute("""
                    INSERT INTO player_messages (message_id, sender_id, receiver_id, message_type, content, status, created_at)
                    VALUES (%s, %s, %s, 'system_notice', %s, 'pending', NOW())
                """, (msg_id, -1, row['player_id'], content_msg))
                results.append({"player_id": row['player_id'], "player_name": row['player_name'], "task_name": row['name']})
            conn.commit()
            if results:
                cur.execute("INSERT INTO daily_task_reset_log (tasks_cleared) VALUES (%s)", (len(results),))
                conn.commit()
            return {"success": True, "cleared_count": len(results), "tasks": results}

# ==================== 签到 ====================
def get_signin_status(player_id: int) -> dict:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            # 获取今天是否已签到
            cur.execute("""
                SELECT signin_date, streak FROM signin_log
                WHERE player_id = %s AND signin_date = CURRENT_DATE
            """, (player_id,))
            today_row = cur.fetchone()
            
            # 获取本月签到日期列表
            cur.execute("""
                SELECT signin_date FROM signin_log
                WHERE player_id = %s AND DATE_TRUNC('month', signin_date) = DATE_TRUNC('month', CURRENT_DATE)
            """, (player_id,))
            signed_dates = [row['signin_date'].day for row in cur.fetchall()]
            
            return {
                "signed_today": today_row is not None,
                "streak": today_row['streak'] if today_row else 0,
                "signed_days": signed_dates
            }

def check_and_upgrade_level(player_id: int) -> dict:
    """检查经验值，超过上限则升级"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT xp, level FROM players WHERE id = %s", (player_id,))
            row = cur.fetchone()
            if not row:
                return {"level_up": False}
            
            xp = row['xp'] or 0
            level = row['level'] or 1
            # 升级公式：需要 level^2 * 100 经验
            max_xp = level * level * 100
            
            if xp >= max_xp:
                # 升级
                total_exp_needed = 0
                levels_gained = 0
                temp_level = level
                temp_xp = xp
                while temp_xp >= temp_level * temp_level * 100:
                    total_exp_needed += temp_level * temp_level * 100
                    temp_xp -= temp_level * temp_level * 100
                    temp_level += 1
                levels_gained = temp_level - level
                new_level = level + levels_gained
                remaining_xp = temp_xp
                cur.execute("UPDATE players SET level = %s, xp = %s WHERE id = %s", (new_level, remaining_xp, player_id))
                conn.commit()
                return {"level_up": True, "levels_gained": levels_gained, "new_level": new_level, "remaining_xp": remaining_xp}
            return {"level_up": False}

def daily_signin(player_id: int, retro_day: int = None) -> dict:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            from datetime import date, datetime, timedelta
            if retro_day:
                # 补签模式：检查指定日期是否已签到
                target_date = date(date.today().year, date.today().month, retro_day)
                cur.execute("""
                    SELECT id FROM signin_log WHERE player_id = %s AND signin_date = %s
                """, (player_id, target_date))
                if cur.fetchone():
                    return {"success": False, "reason": "该日期已签到"}
                cur.execute("""
                    INSERT INTO signin_log (player_id, signin_date, streak)
                    VALUES (%s, %s, 1)
                """, (player_id, target_date))
                add_gold(player_id, 500)
                add_silver(player_id, 1000)
                add_xp(player_id, 2000)
                # 检查是否升级
                level_result = check_and_upgrade_level(player_id)
                conn.commit()
                return {"success": True, "reward_gold": 500, "reward_silver": 1000, "reward_exp": 2000, "retro": True, "level_up": level_result.get("level_up"), "new_level": level_result.get("new_level")}
            
            # 正常签到：检查今天是否已签到
            cur.execute("""
                SELECT id FROM signin_log WHERE player_id = %s AND signin_date = CURRENT_DATE
            """, (player_id,))
            if cur.fetchone():
                return {"success": False, "reason": "今日已签到，明天再来吧！"}
            
            cur.execute("""
                SELECT signin_date, streak FROM signin_log
                WHERE player_id = %s ORDER BY signin_date DESC LIMIT 1
            """, (player_id,))
            row = cur.fetchone()
            is_first = row is None
            yesterday = datetime.now().date() - timedelta(days=1)
            is_continues = row and row['signin_date'] == yesterday if row else False
            new_streak = 1 if is_first else (row['streak'] + 1 if is_continues else 1)
            
            cur.execute("""
                INSERT INTO signin_log (player_id, signin_date, streak)
                VALUES (%s, CURRENT_DATE, %s)
            """, (player_id, new_streak))
            add_gold(player_id, 500)
            add_silver(player_id, 1000)
            add_xp(player_id, 2000)
            # 检查是否升级
            level_result = check_and_upgrade_level(player_id)
            conn.commit()
            return {"success": True, "reward_gold": 500, "reward_silver": 1000, "reward_exp": 2000, "streak": new_streak, "level_up": level_result.get("level_up"), "new_level": level_result.get("new_level")}

def reset_daily_tasks() -> dict:
    """每天8点重置所有任务"""
    from datetime import datetime
    now = datetime.now()
    # 检查是否是8点
    if now.hour != 8:
        return {"success": False, "reason": "不是8点整"}
    
    results = []
    with get_db() as conn:
        with get_cursor(conn) as cur:
            # 获取所有未完成任务
            cur.execute("""
                SELECT pt.id, pt.player_id, t.name, p.name as player_name
                FROM player_tasks pt
                JOIN task_pool tp ON pt.task_pool_id = tp.id
                JOIN tasks t ON tp.task_id = t.id
                JOIN players p ON pt.player_id = p.id
                WHERE pt.status = 'ongoing'
            """)
            ongoing = cur.fetchall()
            
            for row in ongoing:
                cur.execute("UPDATE player_tasks SET status = 'expired' WHERE id = %s", (row['id'],))
                import uuid
                msg_id = f"sys_{uuid.uuid4().hex[:12]}"
                content = f"每日8点重置：任务 <b>{row['name']}</b> 被重置，请接受新任务。"
                cur.execute("""
                    INSERT INTO player_messages (message_id, sender_id, receiver_id, message_type, content, status, created_at)
                    VALUES (%s, %s, %s, 'system_notice', %s, 'pending', NOW())
                """, (msg_id, -1, row['player_id'], content))
                results.append(row['player_name'])
            
            conn.commit()
            return {"success": True, "cleared_count": len(results), "players": list(set(results))}

# ==================== 保护盾 ====================
def get_protection_status(player_id: int) -> dict:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT * FROM protection_shield WHERE player_id = %s
            """, (player_id,))
            row = cur.fetchone()
            if row and row['shield_end']:
                from datetime import datetime
                remaining = (row['shield_end'] - datetime.now()).total_seconds()
                is_active = remaining > 0 and row.get('is_active', True)
                cooldown = 0
                if not is_active and remaining > 0:
                    if row.get('is_newbie'):
                        cooldown = 0
                        remaining = 0
                    else:
                        cooldown = int(remaining)
                return {
                    "active": is_active,
                    "remaining_seconds": max(0, int(remaining)),
                    "cooldown_seconds": cooldown,
                    "type": row['shield_type'],
                    "is_newbie": row.get('is_newbie', False)
                }
            return {"active": False, "remaining_seconds": 0, "cooldown_seconds": 0, "is_newbie": False}

def activate_shield(player_id: int, shield_type: str) -> dict:
    from datetime import datetime, timedelta
    with get_db() as conn:
        with get_cursor(conn) as cur:
            # 检查当前护盾状态
            cur.execute("SELECT shield_end, is_newbie, manual_cancel FROM protection_shield WHERE player_id = %s", (player_id,))
            last = cur.fetchone()
            
            # 如果有激活的护盾且不是新手护盾
            if last and last['shield_end']:
                if last['shield_end'] > datetime.now():
                    return {"success": False, "reason": "保护盾还在有效期，无需激活"}
                # 护盾已过期
                if last.get('is_newbie'):
                    return {"success": False, "reason": "新手保护盾已过期，请购买付费护盾"}
                # 只有手动取消才需要冷却期（自然到期不需要）
                if last.get('manual_cancel') and last['shield_end'] > datetime.now() - timedelta(minutes=30):
                    remaining = int((last['shield_end'] - datetime.now() + timedelta(minutes=30)).total_seconds())
                    if remaining > 0:
                        return {"success": False, "reason": f"取消冷却中，需等{int(remaining/60)+1}分钟"}
            
            cur.execute("SELECT * FROM protection_prices WHERE shield_type = %s", (shield_type,))
            price = cur.fetchone()
            if not price:
                return {"success": False, "reason": "保护盾类型不存在"}
            
            duration = float(price['duration_hours'])
            cost = price['price']
            if cost > 0 and not spend_gold(player_id, cost):
                return {"success": False, "reason": "金贝不足"}
            
            now = datetime.now()
            
            # 计算新的护盾结束时间（累加）
            if last and last['shield_end'] and last['shield_end'] > now:
                # 累加时间
                new_shield_end = last['shield_end'] + timedelta(hours=duration)
            else:
                # 新建护盾
                new_shield_end = now + timedelta(hours=duration)
            
            cur.execute("""
                INSERT INTO protection_shield (player_id, shield_type, shield_start, shield_end, total_shield_time, shield_count, is_active, is_newbie, updated_at)
                VALUES (%s, %s, %s, %s, %s, 1, TRUE, FALSE, NOW())
                ON CONFLICT (player_id) DO UPDATE SET
                    shield_type = EXCLUDED.shield_type,
                    shield_start = CASE WHEN protection_shield.is_newbie = TRUE THEN EXCLUDED.shield_start ELSE protection_shield.shield_start END,
                    shield_end = %s,
                    total_shield_time = protection_shield.total_shield_time + EXCLUDED.total_shield_time,
                    shield_count = protection_shield.shield_count + 1,
                    is_active = TRUE,
                    is_newbie = FALSE,
                    manual_cancel = FALSE,
                    updated_at = NOW()
            """, (player_id, shield_type, now, new_shield_end, int(duration * 3600), new_shield_end))
            conn.commit()
            return {"success": True, "type": shield_type, "hours": duration}

def deactivate_shield(player_id: int) -> dict:
    from datetime import datetime, timedelta
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT is_newbie FROM protection_shield WHERE player_id = %s AND is_active = TRUE", (player_id,))
            row = cur.fetchone()
            if row and row.get('is_newbie'):
                cur.execute("""
                    UPDATE protection_shield SET is_active = FALSE, updated_at = NOW()
                    WHERE player_id = %s AND is_newbie = TRUE
                """, (player_id,))
                conn.commit()
                return {"success": True, "cooldown_seconds": 0, "is_newbie_shield": True}
            else:
                cooldown_end = datetime.now() + timedelta(minutes=30)
                cur.execute("""
                    UPDATE protection_shield
                    SET is_active = FALSE, shield_end = %s, updated_at = NOW()
                    WHERE player_id = %s AND (is_newbie IS FALSE OR is_newbie IS NULL)
                """, (cooldown_end, player_id))
                conn.commit()
                if cur.rowcount == 0:
                    return {"success": False, "reason": "没有激活的保护盾"}
                return {"success": True, "cooldown_seconds": 30 * 60}

# ==================== 门派 ====================
def join_faction(player_id: int, faction_id: str) -> dict:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT * FROM factions WHERE faction_id = %s", (faction_id,))
            faction = cur.fetchone()
            if not faction:
                return {"success": False, "reason": "门派不存在"}
            cur.execute("SELECT faction, last_faction_change FROM players WHERE id = %s", (player_id,))
            player = cur.fetchone()
            # 检查15分钟冷却（无论是否已有门派）
            last_change = player.get('last_faction_change')
            if last_change:
                cur.execute("SELECT NOW() - %s < INTERVAL '15 minutes' AS on_cooldown", (last_change,))
                if cur.fetchone()['on_cooldown']:
                    return {"success": False, "reason": "退出门派后需等15分钟才能加入新宗门"}
            # 如果从其他门派切换，清除旧技能并扣除旧门派战力加成
            faction_power_bonus = 200  # 每个门派基础加200战力
            if player and player['faction'] and player['faction'] != faction_id:
                reset_faction_skills(player_id)
            # 加入新门派增加战力
            cur.execute("UPDATE players SET faction = %s, last_faction_change = NOW(), power = power + %s WHERE id = %s", (faction_id, faction_power_bonus, player_id))
            conn.commit()
            return {"success": True, "faction": faction['name'], "faction_id": faction_id, "power_bonus": faction_power_bonus}

def leave_faction(player_id: int, faction_id: str = None) -> dict:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT faction FROM players WHERE id = %s", (player_id,))
            player = cur.fetchone()
            if not player or not player['faction']:
                return {"success": False, "reason": "你还没有加入任何门派"}
            # 如果传了faction_id，检查是否匹配
            if faction_id and player['faction'] != faction_id:
                return {"success": False, "reason": "你不在这个门派中"}
            cur.execute("UPDATE players SET faction = NULL, last_faction_change = NOW() WHERE id = %s", (player_id,))
            cur.execute("DELETE FROM player_skills WHERE player_id = %s", (player_id,))
            conn.commit()
            return {"success": True, "message": "已退出门派，技能已重置"}

# ==================== 技能系统 ====================
def get_skill_points(player_id: int) -> int:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT skill_points FROM players WHERE id = %s", (player_id,))
            row = cur.fetchone()
            if not row:
                return 0
            return max(0, row['skill_points'] or 0)

def get_player_skills(player_id: int) -> list:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT skill_key, skill_level, learned_at FROM player_skills
                WHERE player_id = %s ORDER BY learned_at
            """, (player_id,))
            return [dict(r) for r in cur.fetchall()]

def learn_skill(player_id: int, skill_key: str) -> dict:
    import skills as skill_data
    SKILLS = skill_data.SKILLS
    if skill_key not in SKILLS:
        return {"success": False, "reason": "技能不存在"}
    skill = SKILLS[skill_key]
    if 'faction' in skill:
        with get_db() as conn:
            with get_cursor(conn) as cur:
                cur.execute("SELECT faction FROM players WHERE id = %s", (player_id,))
                player = cur.fetchone()
                if not player or player['faction'] != skill['faction']:
                    return {"success": False, "reason": "只能学习所属门派的技能"}
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT 1 FROM player_skills WHERE player_id = %s AND skill_key = %s", (player_id, skill_key))
            if cur.fetchone():
                return {"success": False, "reason": "已学习过该技能"}
            cost = 1
            available = get_skill_points(player_id)
            if available < cost:
                return {"success": False, "reason": f"技能点不足（需要{cost}点，当前{available}点）"}
            cur.execute("""
                INSERT INTO player_skills (player_id, skill_key, skill_level)
                VALUES (%s, %s, 1)
                ON CONFLICT (player_id, skill_key) DO NOTHING
            """, (player_id, skill_key))
            if cur.rowcount == 0:
                return {"success": False, "reason": "学习失败"}
            cur.execute("UPDATE players SET skill_points = GREATEST(0, skill_points - %s) WHERE id = %s", (1, player_id))
            conn.commit()
            return {"success": True, "skill": skill['name'], "cost": cost}

def reset_faction_skills(player_id: int) -> dict:
    import skills as skill_data
    SKILLS = skill_data.SKILLS
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT skill_key FROM player_skills WHERE player_id = %s", (player_id,))
            player_skills = [r['skill_key'] for r in cur.fetchall()]
            faction_skill_count = sum(1 for k in player_skills if k in SKILLS and SKILLS[k].get('faction'))
            cur.execute("DELETE FROM player_skills WHERE player_id = %s", (player_id,))
            if faction_skill_count > 0:
                cur.execute("UPDATE players SET skill_points = skill_points + %s WHERE id = %s", (faction_skill_count, player_id))
            conn.commit()
            return {"success": True, "refunded_points": faction_skill_count}

# ==================== 战斗记录 ====================
def record_challenge(challenge_id: str, challenger_id: int, defender_id: int,
                     result: str, damage_dealt: int = 0, reward_gold: int = 0,
                     reward_xp: int = 0, battle_data: dict = None) -> bool:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                INSERT INTO challenge_records
                (challenge_id, challenger_id, defender_id, challenge_type, result,
                 damage_dealt, gold_change, xp_change, battle_replay, created_at)
                VALUES (%s, %s, %s, 'pvp', %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (challenge_id) DO NOTHING
            """, (challenge_id, challenger_id, defender_id, result,
                  damage_dealt, reward_gold, reward_xp,
                  psycopg2.extras.Json(battle_data) if battle_data else None))
            return True

# ==================== 日志 ====================
def log_action(player_id: int, player_name: str, action: str, detail: str = ''):
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                INSERT INTO player_logs (player_id, player_name, action, detail)
                VALUES (%s, %s, %s, %s)
            """, (player_id, player_name, action, detail))
            conn.commit()

def get_player_logs(limit: int = 50) -> list:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT * FROM player_logs
                ORDER BY created_at DESC LIMIT %s
            """, (limit,))
            return cur.fetchall()

def get_public_logs(limit: int = 50) -> list:
    """获取公屏日志（所有玩家的操作）"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT player_name, action, detail, created_at FROM player_logs
                ORDER BY created_at DESC LIMIT %s
            """, (limit,))
            return cur.fetchall()

def get_leaderboard(lb_type: str = "power", limit: int = 20) -> list:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            base_cols = "id, name, level, power, honor_prefix, honor_icon, honor_color"
            if lb_type == "gold":
                cur.execute(f"SELECT {base_cols}, gold as value FROM players ORDER BY gold DESC LIMIT %s", (limit,))
            elif lb_type == "silver":
                cur.execute(f"SELECT {base_cols}, silver as value FROM players ORDER BY silver DESC LIMIT %s", (limit,))
            elif lb_type == "level":
                cur.execute(f"SELECT {base_cols}, level as value FROM players ORDER BY level DESC LIMIT %s", (limit,))
            elif lb_type == "wins":
                cur.execute(f"SELECT {base_cols}, wins as value FROM players ORDER BY wins DESC LIMIT %s", (limit,))
            elif lb_type == "challenges":
                cur.execute(f"SELECT {base_cols}, (wins + losses) as value FROM players ORDER BY (wins + losses) DESC LIMIT %s", (limit,))
            elif lb_type == "attr":
                cur.execute(f"SELECT {base_cols}, (claw + shell + speed + wisdom + perception + luck) as value FROM players ORDER BY (claw + shell + speed + wisdom + perception + luck) DESC LIMIT %s", (limit,))
            else:
                cur.execute(f"SELECT {base_cols}, power as value FROM players ORDER BY power DESC LIMIT %s", (limit,))
            return cur.fetchall()

# ==================== 消息 ====================
def send_message(sender_id: int, receiver_id: int, content: str, msg_type: str = "normal") -> dict:
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT COUNT(*) as cnt FROM player_messages
                WHERE sender_id = %s AND status = 'pending'
            """, (sender_id,))
            pending = cur.fetchone()['cnt']
            if pending >= 3:
                return {"success": False, "reason": "未处理留言已达3条上限，请等待处理"}
            import uuid
            msg_id = f"msg_{uuid.uuid4().hex[:12]}"
            cur.execute("""
                INSERT INTO player_messages (message_id, sender_id, receiver_id, message_type, content, status, created_at)
                VALUES (%s, %s, %s, %s, %s, 'pending', NOW())
            """, (msg_id, sender_id, receiver_id, msg_type, content))
            conn.commit()
            return {"success": True, "message_id": msg_id}


def add_public_chat(player_id, sender_type, content):
    """添加公屏消息"""
    if not content:
        return False
    try:
        with get_db() as conn:
            with get_cursor(conn) as cur:
                if sender_type == 'system':
                    cur.execute("""
                        INSERT INTO public_chat (sender_id, sender_type, content)
                        VALUES (NULL, 'system', %s)
                    """, (content,))
                else:
                    cur.execute("""
                        INSERT INTO public_chat (sender_id, sender_type, content)
                        VALUES (%s, 'player', %s)
                    """, (player_id, content))
                conn.commit()
                return True
    except Exception as e:
        print(f"add_public_chat error: {e}")
        return False


def send_boss_reward_mail(player_id: int, killer_name: str, boss_name: str, gold: int, exp: int) -> dict:
    """发送世界BOSS奖励邮件"""
    import json
    msg_type = 'system_gift'
    content = f'🎉 恭喜您击败了 {boss_name}！作为奖励，您获得了：💰 {gold} 金贝 + ✨ {exp} 经验！'
    attachments = json.dumps([{'type': 'gold', 'quantity': gold}, {'type': 'exp', 'quantity': exp}])
    with get_db() as conn:
        with get_cursor(conn) as cur:
            import uuid
            msg_id = f'boss_{uuid.uuid4().hex[:12]}'
            cur.execute("""
                INSERT INTO player_messages (message_id, sender_id, receiver_id, message_type, content, status, attachments, created_at)
                VALUES (%s, 0, %s, %s, %s, 'unclaimed', %s, NOW())
            """, (msg_id, player_id, msg_type, content, attachments))
            conn.commit()
            return {"success": True, "message_id": msg_id}


def give_boss_card(player_id: int, boss_id: int) -> dict:
    """给予玩家BOSS收集卡（击败时自动发放）"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            # Check if already has this card
            cur.execute("""
                SELECT pbc.id, bc.name, bc.icon, bc.rarity
                FROM player_boss_cards pbc
                JOIN boss_cards bc ON bc.id = pbc.card_id
                WHERE pbc.player_id = %s AND bc.boss_id = %s
            """, (player_id, boss_id))
            existing = cur.fetchone()
            if existing:
                return {"success": False, "reason": "已拥有该卡片", "card": dict(existing)}

            # Get card info
            cur.execute("SELECT id, name, icon, rarity, description, hp, attack, defense FROM boss_cards WHERE boss_id = %s", (boss_id,))
            card = cur.fetchone()
            if not card:
                return {"success": False, "reason": "卡片不存在"}

            # Insert card
            cur.execute("""
                INSERT INTO player_boss_cards (player_id, card_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (player_id, card['id']))
            conn.commit()
            return {"success": True, "card": dict(card)}


def get_player_boss_cards(player_id: int) -> list:
    """获取玩家所有BOSS收集卡"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT bc.id, bc.boss_id, bc.name, bc.icon, bc.rarity,
                       bc.description, bc.hp, bc.attack, bc.defense,
                       pbc.obtained_at
                FROM player_boss_cards pbc
                JOIN boss_cards bc ON bc.id = pbc.card_id
                WHERE pbc.player_id = %s
                ORDER BY pbc.obtained_at DESC
            """, (player_id,))
            return [dict(r) for r in cur.fetchall()]
