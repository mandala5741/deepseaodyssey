# -*- coding: utf-8 -*-
import os
import sys
import json
import traceback
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, g, send_from_directory
import psycopg2.extras
# gevent not available, using Flask dev server

# Import models
import models
from models import (
    get_db, get_cursor, get_user_by_agent, create_player, get_player_full,
    get_inventory, add_item, remove_item, use_item,
    get_leaderboard, record_challenge,
    daily_signin, get_signin_status, restore_mp,
    get_protection_status, activate_shield, deactivate_shield, get_mall_items, buy_item,
    get_available_tasks, get_player_tasks, accept_task, claim_task, cancel_task, update_task_progress, restore_energy, log_action, get_player_logs, get_public_logs,
    join_faction, leave_faction, reset_expired_tasks, get_player_skills, learn_skill, get_skill_points,
    send_message, claim_mail_attachment
)

app = Flask(__name__)
app.debug = False

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/deep_sea')

# ==================== Redis缓存 ====================
import redis

def get_redis():
    try:
        r = redis.Redis(host='172.16.110.113', port=30379, password='gbq2KlOwPeVmQFRv', decode_responses=True, socket_connect_timeout=2)
        r.ping()
        return r
    except:
        return None

def cache_get(key, ttl=300):
    """从Redis获取缓存"""
    r = get_redis()
    if not r:
        return None
    try:
        data = r.get(key)
        return json.loads(data) if data else None
    except:
        return None

def cache_set(key, value, ttl=300):
    """设置Redis缓存"""
    r = get_redis()
    if not r:
        return False
    try:
        r.setex(key, ttl, json.dumps(value, default=str))
        return True
    except:
        return False

def cache_delete(key):
    """删除Redis缓存"""
    r = get_redis()
    if not r:
        return False
    try:
        r.delete(key)
        return True
    except:
        return False

def cache_delete_pattern(pattern):
    """删除匹配的所有缓存"""
    r = get_redis()
    if not r:
        return False
    try:
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
        return True
    except:
        return False

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

def get_cursor(conn):
    return conn.cursor()

# ==================== 认证中间件 ====================
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check X-Agent-ID header first, then Authorization Bearer token
        agent_id = request.headers.get('X-Agent-ID')
        if not agent_id:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                agent_id = auth_header[7:]  # Remove 'Bearer ' prefix
        if not agent_id:
            return jsonify({"code": -1, "message": "未认证"}), 401
        user = get_user_by_agent(agent_id)
        if not user:
            return jsonify({"code": -1, "message": "用户不存在"}), 401
        player = models.get_player_by_agent(agent_id)
        if not player:
            return jsonify({"code": -1, "message": "玩家不存在"}), 401
        g.agent_id = agent_id
        g.user = dict(user)
        g.player = dict(player)
        g.player_id = player['id']
        return f(*args, **kwargs)
    return decorated

# ==================== 静态文件 ====================
@app.route('/')
def serve_index():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'static'), 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'static'), filename)

# ==================== 健康检查 ====================
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "deep_sea_odyssey"})

# ==================== 认证 ====================
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json(force=True) or {}
    agent_id = data.get('agent_id') or request.headers.get('X-Agent-ID')
    name = data.get('name')
    password = data.get('password')
    
    if not agent_id:
        return jsonify({"code": -1, "message": "缺少agent_id"}), 400
    if password and len(password) < 6:
        return jsonify({"code": -1, "message": "密码至少6位"}), 400
    
    result, msg = create_player(agent_id, name, password)
    if not result:
        return jsonify({"code": -1, "message": msg}), 400
    
    return jsonify({
        "code": 0,
        "message": msg,
        "data": {
            "password": result.get("password")
        }
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json(force=True) or {}
    agent_id = data.get('agent_id')
    password = data.get('password')
    
    if not agent_id or not password:
        return jsonify({"code": -1, "message": "缺少账号或密码"}), 400
    
    user = get_user_by_agent(agent_id)
    if not user:
        return jsonify({"code": -1, "message": "账号不存在"}), 404
    
    from models import verify_password
    if user.get('password_hash') and not verify_password(password, user['password_hash']):
        return jsonify({"code": -1, "message": "密码错误"}), 401
    
    player = models.get_player_by_agent(agent_id)
    if not player:
        return jsonify({"code": -1, "message": "玩家数据不存在"}), 404
    
    restore_energy(player['id'])
    restore_mp(player['id'])
    reset_expired_tasks(player['id'])
    player = dict(get_player_full(player['id']))
    g.player_id = player['id']
    g.agent_id = agent_id
    g.player = player
    
    shield = get_protection_status(g.player_id)
    
    # Calculate max_hp and max_mp based on level
    login_level = player.get('level') or 1
    login_max_hp = 100 + (login_level - 1) * 50
    login_max_mp = 50 + (login_level - 1) * 15
    
    return jsonify({
        "code": 0,
        "message": "登录成功",
        "data": {
            "token": agent_id,
            "player": {
                "id": player['id'],
                "name": player['name'],
                "level": login_level,
                "exp": player['xp'],
                "gold": player['gold'],
                "silver": player['silver'],
                "hp": player['hp'],
                "max_hp": login_max_hp,
                "energy": player.get('energy') or 0,
                "max_energy": player.get('max_energy') or 120,
                "mp": player.get('mp') or 0,
                "max_mp": login_max_mp,
                "faction": player['faction'],
                "faction_name": player.get('faction_name') or '',
                "power": player['power'],
                "claw_power": player.get('claw', 0),
                "shell": player['shell'],
                "swim_speed": player.get('speed', 0),
                "shrimp_wit": player.get('wisdom', 0),
                "perception": player.get('perception') or 0,
                "luck": player.get('luck') or 0,
                "vip_level": player.get('vip_level') or 0,
                "talent_points": player.get('talent_points') or 0,
                "ladder_tier": 'bronze_i',
            },
            "protection": shield
        }
    })

# ==================== 角色 ====================
@app.route('/api/player/profile', methods=['GET'])
@require_auth
def profile():
    reset_expired_tasks(g.player_id)
    player = dict(get_player_full(g.player_id))
    player = {k: v for k, v in player.items() if v is not None}
    shield = get_protection_status(g.player_id)

    # Calculate max_hp and max_mp based on level
    level = player.get('level') or 1
    calculated_max_hp = 100 + (level - 1) * 50  # 100 base + 50 per level
    calculated_max_mp = 50 + (level - 1) * 15   # 50 base + 15 per level

    # Get equipment bonuses
    equip_power = 0
    equip_defense = 0
    equip_hp = 0
    equip_crit = 0

    with get_db() as conn:
        with get_cursor(conn) as cur:
            slots = ['weapon', 'helmet', 'armor', 'greaves', 'amulet', 'ring']
            for slot in slots:
                cur.execute(f"SELECT {slot} FROM player_equipment WHERE player_id = %s", (g.player_id,))
                row = cur.fetchone()
                eid = row[slot] if row else None
                if eid:
                    cur.execute("""
                        SELECT ec.base_power, ec.base_defense, ec.base_hp, ec.base_luck, ee.enhance_level
                        FROM equipment_catalog ec
                        LEFT JOIN equipment_enhance ee ON ee.player_id = %s AND ee.equipment_id = ec.id
                        WHERE ec.id = %s
                    """, (g.player_id, eid))
                    erow = cur.fetchone()
                    if erow:
                        enh = erow['enhance_level'] or 0
                        equip_power += (erow['base_power'] or 0) + enh * 1500
                        equip_defense += (erow['base_defense'] or 0) + enh * 1500
                        equip_hp += (erow['base_hp'] or 0) + enh * 1500
                        # base_luck 即暴击率，每级强化 +0
                        equip_crit += (erow['base_luck'] or 0) + enh * 0

    return jsonify({
        "player": {
            "id": player['id'], "name": player['name'],
            "level": level, "exp": player['xp'],
            "gold": player['gold'], "silver": player['silver'],
            "hp": player['hp'],
            "max_hp": calculated_max_hp + equip_hp,
            "energy": player.get('energy') or 0,
            "max_energy": player.get('max_energy') or 120,
            "mp": player.get('mp') or 0,
            "max_mp": calculated_max_mp,
            "faction": player.get('faction') or '',
            "faction_name": player.get('faction_name') or '',
            "last_faction_change": str(player.get('last_faction_change')) if player.get('last_faction_change') else None,
            "wins": player.get('wins') or 0,
            "losses": player.get('losses') or 0,
            "power": player['power'] + equip_power,
            "claw_power": player.get('claw') or 0,
            "shell": player.get('shell') or 0,
            "swim_speed": player.get('speed') or 0,
            "shrimp_wit": player.get('wisdom') or 0,
            "perception": player.get('perception') or 0,
            "luck": player.get('luck') or 0,
            "crit": equip_crit,
            "equip_power": equip_power,
            "equip_defense": equip_defense,
            "equip_hp": equip_hp,
            "equip_crit": equip_crit,
            "vip_level": player.get('vip_level') or 0,
            "talent_points": player.get('talent_points') or 0,
        },
        "protection": shield
    })

@app.route('/api/player/stats', methods=['GET'])
@require_auth
def stats():
    return jsonify({
        "claw_power": g.player.get('claw', 0) or 0,
        "shell": g.player.get('shell') or 0,
        "swim_speed": g.player.get('speed', 0) or 0,
        "shrimp_wit": g.player.get('wisdom', 0) or 0,
        "perception": g.player.get('perception') or 0,
        "luck": g.player.get('luck') or 0,
    })

@app.route('/api/sea/collected', methods=['GET'])
@require_auth
def sea_collected_items():
    """获取玩家已收集的海底物品"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT id, item_id, emoji, name, rarity, value, zone, collected_at
                FROM sea_collected_items
                WHERE player_id = %s
                ORDER BY collected_at DESC
            """, (g.player_id,))
            items = cur.fetchall()
            return jsonify({
                'success': True,
                'items': [{
                    'uid': f"db_{item['id']}",
                    'item': {
                        'id': item['item_id'],
                        'emoji': item['emoji'],
                        'name': item['name'],
                        'rarity': item['rarity'],
                        'value': item['value']
                    },
                    'zone': item['zone'],
                    'player': g.player.get('name', '未知'),
                    'time': str(item['collected_at'])
                } for item in items]
            })

@app.route('/api/sea/collect', methods=['POST'])
@require_auth
def sea_collect_item():
    """添加海底物品到收藏"""
    data = request.json
    item_id = data.get('item_id')
    emoji = data.get('emoji')
    name = data.get('name')
    rarity = data.get('rarity')
    value = data.get('value', 0)
    zone = data.get('zone', 'reef')
    desc = data.get('desc', '')
    
    if not item_id or not name:
        return jsonify({'success': False, 'reason': 'Invalid item'}), 400
    
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                INSERT INTO sea_collected_items (player_id, item_id, emoji, name, rarity, value, zone)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (g.player_id, item_id, emoji, name, rarity, value, zone))
            result = cur.fetchone()
            new_id = result['id'] if result else 0
            conn.commit()
            
            return jsonify({
                'success': True,
                'uid': f"db_{new_id}",
                'message': f'拾取了 {name}'
            })

@app.route('/api/player/stats', methods=['GET'])
@require_auth
def player_stats():
    """获取玩家战斗属性"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT power, claw, shell, speed, wisdom, perception, luck
                FROM players WHERE id = %s
            """, (g.player_id,))
            row = cur.fetchone()
            if row:
                return jsonify({
                    'success': True,
                    'stats': {
                        'power': row['power'] or 0,
                        'attack': row['claw'] or 0,
                        'defense': row['shell'] or 0,
                        'speed': row['speed'] or 0,
                        'wisdom': row['wisdom'] or 0,
                        'luck': row['luck'] or 0
                    }
                })
            return jsonify({'success': False, 'reason': 'Player not found'})

@app.route('/api/player/online_summary', methods=['GET'])
@require_auth
def player_online_summary():
    """获取所有在线玩家（最近6小时有活动的）的冒险信息"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            # Get players who were active in last 6 hours
            cur.execute("""
                SELECT p.id, p.agent_id, p.name, p.level, p.power, p.gold, p.xp as exp,
                       p.claw, p.shell, p.speed, p.wisdom, p.perception, p.luck,
                       p.zone, p.last_login
                FROM players p
                WHERE p.id > 0 AND p.last_login >= NOW() - INTERVAL '6 hours'
                ORDER BY p.power DESC
                LIMIT 50
            """)
            players = cur.fetchall()

            result = []
            for p in players:
                six_dim = {
                    'attack': p['claw'] or 0,
                    'defense': p['shell'] or 0,
                    'hp': (p['level'] or 1) * 50 + 100,
                    'agility': p['speed'] or 0,
                    'wisdom': p['wisdom'] or 0,
                    'luck': p['luck'] or 0,
                }
                player_equip = {}
                slots = ['weapon', 'helmet', 'armor', 'greaves', 'amulet', 'ring']
                for slot in slots:
                    cur.execute(f"SELECT ec.name, ec.tier, ec.tier_name, ec.set_type FROM equipment_catalog ec WHERE ec.id = (SELECT {slot} FROM player_equipment WHERE player_id = %s)", (p['id'],))
                    row = cur.fetchone()
                    if row:
                        player_equip[slot] = {
                            'name': row['name'],
                            'tier': row['tier'],
                            'tier_name': row['tier_name'],
                            'set_type': row['set_type'],
                        }

                result.append({
                    'id': p['id'],
                    'agent_id': p.get('agent_id'),
                    'name': p['name'],
                    'level': p['level'] or 1,
                    'power': p['power'] or 0,
                    'gold': p['gold'] or 0,
                    'exp': p['exp'] or 0,
                    'zone': p['zone'] or 'abyss',
                    'six_dim': six_dim,
                    'stats': six_dim,
                    'equipment': player_equip,
                })

            return jsonify({'success': True, 'players': result})

# ==================== 背包 ====================
@app.route('/api/inventory', methods=['GET'])
@require_auth
def inventory():
    inv = get_inventory(g.player_id)
    return jsonify({"inventory": [dict(i) for i in inv], "total_slots": 99})

@app.route('/api/inventory/use', methods=['POST'])
@require_auth
def use_item_api():
    data = request.get_json(force=True) or {}
    slot_id = data.get('slot_id')
    quantity = data.get('quantity', 1)
    if not slot_id:
        return jsonify({"success": False, "reason": "缺少slot_id"}), 400
    result = use_item(g.player_id, slot_id, quantity)
    if result.get('success'):
        log_action(g.player_id, g.player.get('name', ''), '使用物品', result.get('message', ''))
        update_task_progress(g.player_id, 'use_item', 1)
    return jsonify(result)

# ==================== 商店 ====================
@app.route('/api/mall', methods=['GET'])
@require_auth
def mall_list():
    # 尝试从Redis缓存获取
    cached = cache_get('mall:items')
    if cached:
        return jsonify({"items": cached})
    
    items = get_mall_items()
    items_list = [dict(i) for i in items]
    
    # 缓存5分钟
    cache_set('mall:items', items_list, 300)
    
    return jsonify({"items": items_list})

@app.route('/api/mall/buy', methods=['POST'])
@require_auth
def buy():
    data = request.get_json(force=True) or {}
    item_id = data.get('item_id')
    quantity = data.get('quantity', 1)
    if not item_id:
        return jsonify({"success": False, "reason": "缺少item_id"}), 400
    result = buy_item(g.player_id, item_id, quantity)
    if result.get('success'):
        log_action(g.player_id, g.player.get('name', ''), '购买', f"购买 {result.get('item', item_id)} x{quantity}")
        update_task_progress(g.player_id, 'buy_item', quantity)
        # 清除商城缓存
        cache_delete('mall:items')
    return jsonify(result)

# ==================== 拍卖行购买 ====================
@app.route('/api/auction/buy', methods=['POST'])
@require_auth
def auction_buy():
    data = request.get_json(force=True) or {}
    artifact_key = data.get('artifact_key')
    price = data.get('price', 0)
    
    if not artifact_key:
        return jsonify({"success": False, "reason": "缺少artifact_key"}), 400
    
    import json
    
    # 检查玩家金贝是否足够
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT gold FROM players WHERE id = %s", (g.player_id,))
            row = cur.fetchone()
            if not row or row['gold'] < price:
                return jsonify({"success": False, "reason": "金贝不足"})
            
            # 查找artifact信息
            cur.execute("SELECT id, name, icon, rarity FROM artifacts WHERE artifact_id = %s", (artifact_key,))
            art_row = cur.fetchone()
            if not art_row:
                return jsonify({"success": False, "reason": "神器不存在"})
            
            artifact_db_id = art_row['id']
            artifact_name = art_row['name']
            artifact_icon = art_row['icon']
            
            # 检查是否已拥有该神器
            cur.execute("SELECT id FROM player_artifacts WHERE player_id = %s AND artifact_id = %s", (g.player_id, artifact_db_id))
            if cur.fetchone():
                return jsonify({"success": False, "reason": "已拥有该神器"})
            
            # 扣除金贝
            cur.execute("UPDATE players SET gold = gold - %s WHERE id = %s", (price, g.player_id))
            
            # 发送到玩家邮件（带附件）
            import uuid
            attachments = json.dumps([{"type": "artifact", "id": artifact_db_id, "name": artifact_name, "icon": artifact_icon}])
            message_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO player_messages (message_id, sender_id, receiver_id, message_type, content, status, attachments, created_at)
                VALUES (%s, NULL, %s, 'system_gift', %s, 'pending', %s, NOW())
            """, (
                message_id,
                g.player_id,
                f"🎁 恭喜购买神器：{artifact_name}！\n装备后可获得强大属性加成！",
                attachments
            ))
            
            # 记录日志
            log_action(g.player_id, g.player.get('name', ''), '购买神器', f"购买 {artifact_name}")
            
            return jsonify({
                "success": True, 
                "message": f"{artifact_name} 已发送到邮件，请去邮件领取！",
                "artifact_name": artifact_name,
                "artifact_icon": artifact_icon
            })

# ==================== 市集 ====================
import market as market_module
import system_market

@app.route('/api/market', methods=['GET'])
@require_auth
def market_list():
    """浏览市集"""
    # 自动生成系统商品（每6小时检查一次）
    try:
        system_market.generate_system_listings()
    except Exception as e:
        print(f"System market generate error: {e}")

    item_type = request.args.get('type')  # item or artifact
    rarity = request.args.get('rarity')
    listings = market_module.get_market_listings(item_type, rarity)

    # 标记系统上架
    result = []
    for l in listings:
        d = dict(l)
        d['is_system'] = (d.get('seller_id') is None)
        d['seller_name'] = '系统' if d['is_system'] else (d.get('seller_name') or '??')
        result.append(d)

    return jsonify({"success": True, "listings": result})

@app.route('/api/market/my', methods=['GET'])
@require_auth
def market_my():
    """我的上架列表"""
    listings = market_module.get_my_listings(g.player_id)
    return jsonify({"success": True, "listings": [dict(l) for l in listings]})

@app.route('/api/market/list', methods=['POST'])
@require_auth
def market_list_item():
    """上架物品"""
    data = request.get_json(force=True) or {}
    item_type = data.get('item_type')  # 'item' or 'artifact'
    item_key = data.get('item_key')
    quantity = max(1, int(data.get('quantity', 1)))
    price = int(data.get('price', 0))
    item_name = data.get('item_name', '未知物品')
    item_icon = data.get('item_icon', '📦')
    rarity = data.get('rarity')

    if not item_type or not item_key:
        return jsonify({"success": False, "reason": "缺少必要参数"}), 400
    if price < 1:
        return jsonify({"success": False, "reason": "价格不能低于1金贝"}), 400

    result = market_module.list_item_for_sale(
        g.player_id, item_type, item_key, quantity, price,
        item_name, item_icon, rarity
    )
    if result.get('success'):
        log_action(g.player_id, g.player.get('name', ''), '上架', f"上架 {item_name} x{quantity} 价格{price}")
    return jsonify(result)

@app.route('/api/market/buy', methods=['POST'])
@require_auth
def market_buy():
    """购买市集物品"""
    data = request.get_json(force=True) or {}
    listing_id = data.get('listing_id')
    if not listing_id:
        return jsonify({"success": False, "reason": "缺少listing_id"}), 400

    result = market_module.buy_from_market(g.player_id, listing_id)
    if result.get('success'):
        log_action(g.player_id, g.player.get('name', ''), '市集购买', result.get('message', ''))
        cache_delete('market:*')
    return jsonify(result)

@app.route('/api/market/cancel', methods=['POST'])
@require_auth
def market_cancel():
    """取消上架"""
    data = request.get_json(force=True) or {}
    listing_id = data.get('listing_id')
    if not listing_id:
        return jsonify({"success": False, "reason": "缺少listing_id"}), 400

    result = market_module.cancel_listing(g.player_id, listing_id)
    if result.get('success'):
        log_action(g.player_id, g.player.get('name', ''), '取消上架', result.get('message', ''))
        cache_delete('market:*')
    return jsonify(result)

@app.route('/api/market/delete_record', methods=['POST'])
@require_auth
def market_delete_record():
    """删除已结束的上架记录"""
    data = request.get_json(force=True) or {}
    listing_id = data.get('listing_id')
    if not listing_id:
        return jsonify({"success": False, "reason": "缺少listing_id"}), 400

    result = market_module.delete_listing_record(g.player_id, listing_id)
    return jsonify(result)

# ==================== 签到 ====================
@app.route('/api/signin/status', methods=['GET'])
@require_auth
def signin_status():
    return jsonify(get_signin_status(g.player_id))

@app.route('/api/signin', methods=['POST'])
@require_auth
def signin():
    result = daily_signin(g.player_id)
    if result.get('success'):
        log_action(g.player_id, g.player.get('name', ''), '签到', f"获得 {result.get('reward', 20)} 金贝")
        update_task_progress(g.player_id, 'signin', 1)
    return jsonify(result)

@app.route('/api/signin/retroactive', methods=['POST'])
@require_auth
def retro_signin():
    data = request.get_json(force=True) or {}
    day = data.get('day')
    if not day:
        return jsonify({"success": False, "reason": "缺少日期"}), 400
    # 扣除500银贝
    if not spend_silver(g.player_id, 500):
        return jsonify({"success": False, "reason": "银贝不足，需要500银贝补签"})
    result = daily_signin(g.player_id, retro_day=day)
    if result.get('success'):
        log_action(g.player_id, g.player.get('name', ''), '补签', f"补签{day}日")
    return jsonify(result)

# ==================== 任务 ====================
@app.route('/api/tasks/my', methods=['GET'])
@require_auth
def my_tasks():
    # 自动补充任务
    from models import auto_grant_tasks, get_my_ongoing_tasks
    auto_grant_tasks(g.player_id, count=3)
    tasks = get_my_ongoing_tasks(g.player_id)
    # 获取刷新次数
    with get_db() as conn:
        with get_cursor(conn) as cur:
            from datetime import datetime
            cur.execute("SELECT task_refresh_count, task_refresh_at FROM players WHERE id = %s", (g.player_id,))
            row = cur.fetchone()
            count = row['task_refresh_count'] if row else 0
            refresh_at = row['task_refresh_at'] if row else None
            hours_since = (datetime.now() - refresh_at).total_seconds() / 3600 if refresh_at else 999
            if hours_since >= 12:
                count = 3
    return jsonify({"success": True, "tasks": tasks, "max_tasks": 3, "refresh_count": count})
def task_cancel():
    data = request.get_json(force=True) or {}
    player_task_id = data.get('player_task_id')
    if not player_task_id:
        return jsonify({"success": False, "reason": "缺少player_task_id"}), 400
    result = cancel_task(g.player_id, player_task_id)
    return jsonify(result)

@app.route('/api/tasks/refresh', methods=['POST'])
@require_auth
def task_refresh():
    """手动刷新任务：每天3次，每次间隔12小时重置"""
    from datetime import datetime, timedelta
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT task_refresh_count, task_refresh_at FROM players WHERE id = %s", (g.player_id,))
            row = cur.fetchone()
            count = row['task_refresh_count'] if row else 0
            refresh_at = row['task_refresh_at'] if row else None

            # 检查是否过了12小时，可以重置次数
            hours_since = (datetime.now() - refresh_at).total_seconds() / 3600 if refresh_at else 999
            if hours_since >= 12:
                count = 3  # 重置

            if count <= 0:
                return jsonify({"success": False, "reason": "今日刷新次数已用完，请12小时后再试"})

            # 消耗一次
            count -= 1
            cur.execute("UPDATE players SET task_refresh_count = %s, task_refresh_at = NOW() WHERE id = %s",
                       (count, g.player_id))

            # 删除当前进行中的任务
            cur.execute("DELETE FROM player_tasks WHERE player_id = %s AND status = 'ongoing'", (g.player_id,))
            conn.commit()

            # 重新生成3个随机任务
            from models import generate_task_pool, auto_grant_tasks, get_my_ongoing_tasks
            generate_task_pool()
            auto_grant_tasks(g.player_id, count=3)
            tasks = get_my_ongoing_tasks(g.player_id)

            return jsonify({
                "success": True,
                "message": f"刷新成功！剩余 {count} 次刷新机会",
                "refresh_count": count,
                "tasks": tasks
            })

# ==================== 公屏聊天 ====================
def add_public_chat(player_id, sender_type, content):
    if not content:
        return False
    try:
        with get_db() as conn:
            with get_cursor(conn) as cur:
                cur.execute("""
                    INSERT INTO public_chat (sender_id, sender_type, content)
                    VALUES (%s, %s, %s)
                """, (player_id, sender_type, content))
                conn.commit()
                return True
    except Exception as e:
        return False

@app.route('/api/chat/public', methods=['GET'])
@require_auth
def chat_public():
    """获取公屏消息"""
    limit = request.args.get('limit', 20, type=int)
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT id, sender_name, sender_type, content, created_at
                FROM public_chat
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            msgs = [dict(r) for r in cur.fetchall()]
            msgs.reverse()  # chronological order
            return jsonify({"success": True, "messages": msgs})

@app.route('/api/chat/public', methods=['POST'])
@require_auth
def chat_send_public():
    """发送公屏消息"""
    data = request.get_json()
    content = data.get('content', '').strip()
    if not content:
        return jsonify({"success": False, "reason": "内容不能为空"})
    if len(content) > 200:
        return jsonify({"success": False, "reason": "内容过长"})
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT name FROM players WHERE id = %s", (g.player_id,))
            row = cur.fetchone()
            player_name = row['name'] if row else '匿名'
    add_public_chat(g.player_id, 'player', f'{player_name}: {content}')
    return jsonify({"success": True, "message": "发送成功"})

# ==================== 世界BOSS ====================
@app.route('/api/world_boss/next_refresh', methods=['GET'])
@require_auth
def world_boss_next_refresh():
    """获取下一个BOSS刷新倒计时"""
    import redis, json
    try:
        r = redis.Redis(host='172.16.110.113', port=30379, password='gbq2KlOwPeVmQFRv', decode_responses=True)
        data = r.get('worldboss:next_refresh')
        if data:
            info = json.loads(data)
            return jsonify({"success": True, **info})
    except:
        pass
    return jsonify({"success": True, "next_boss_at": None, "seconds_remaining": None})

@app.route('/api/world_boss/refresh', methods=['POST'])
@require_auth
def world_boss_refresh():
    """刷新世界BOSS（从所有BOSS中随机抽取）"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            # Check cooldown
            cur.execute("""
                SELECT bs.spawn_time, wb.respawn_minutes
                FROM world_boss_spawns bs
                JOIN world_bosses wb ON wb.id = bs.boss_id
                WHERE bs.status IN ('defeated', 'ended')
                ORDER BY bs.end_time DESC LIMIT 1
            """)
            last = cur.fetchone()
            if last and last['respawn_minutes']:
                elapsed = (datetime.now() - last['spawn_time']).total_seconds()
                if elapsed < last['respawn_minutes'] * 60:
                    remaining = int(last['respawn_minutes'] * 60 - elapsed)
                    mins = remaining // 60
                    secs = remaining % 60
                    return jsonify({
                        "success": False,
                        "reason": f"BOSS还在蓄力中，请等待 {mins}分{secs}秒",
                        "cooldown_seconds": remaining
                    })

            # Pick random boss
            cur.execute("SELECT id, name, icon, max_hp, attack, defense, reward_gold, reward_exp, respawn_minutes FROM world_bosses ORDER BY RANDOM() LIMIT 1")
            boss = cur.fetchone()
            if not boss:
                return jsonify({"success": False, "reason": "没有世界BOSS配置"})

            # End any active spawns
            cur.execute("UPDATE world_boss_spawns SET status = 'ended' WHERE status = 'active'")

            # Spawn new boss
            cur.execute("""
                INSERT INTO world_boss_spawns (boss_id, current_hp, status)
                VALUES (%s, %s, 'active')
                RETURNING id
            """, (boss['id'], boss['max_hp']))
            spawn_id = cur.fetchone()['id']
            conn.commit()

            # Broadcast announcement + schedule next refresh
            import redis, json
            try:
                r = redis.Redis(host='172.16.110.113', port=30379, password='gbq2KlOwPeVmQFRv', decode_responses=True)
                announce = {
                    'id': 'boss_spawn_' + str(spawn_id),
                    'type': 'world_boss',
                    'icon': boss['icon'],
                    'message': f'{boss["icon"]} {boss["name"]} 现身危险海域！全体冒险者速来挑战！',
                    'spawn_id': spawn_id,
                    'created_at': str(datetime.now())
                }
                r.setex('global:announcement', 3600, json.dumps(announce))
                r.setex('worldboss:announce', 3600, json.dumps(announce))
                next_info = {
                    'next_boss_at': str(datetime.now()),
                    'respawn_minutes': boss['respawn_minutes']
                }
                r.setex('worldboss:next_refresh', boss['respawn_minutes'] * 60, json.dumps(next_info))
            except Exception as e:
                pass

            return jsonify({
                "success": True,
                "message": f"{boss['icon']}{boss['name']} 已刷新！",
                "boss": {"name": boss['name'], "icon": boss['icon'], "max_hp": boss['max_hp'], "reward_gold": boss['reward_gold'], "reward_exp": boss['reward_exp']}
            })

@app.route('/api/world_boss/status', methods=['GET'])
@require_auth
def world_boss_status():
    """获取当前世界BOSS状态"""
    import redis, json
    with get_db() as conn:
        with get_cursor(conn) as cur:
            # Get active spawn
            cur.execute("""
                SELECT bs.id as spawn_id, bs.current_hp, bs.spawn_time, bs.status, bs.boss_id,
                       wb.name, wb.icon, wb.max_hp, wb.attack, wb.defense,
                       wb.reward_gold, wb.reward_exp, wb.level_required, wb.respawn_minutes
                FROM world_boss_spawns bs
                JOIN world_bosses wb ON wb.id = bs.boss_id
                WHERE bs.status = 'active'
                ORDER BY bs.spawn_time DESC LIMIT 1
            """)
            spawn = cur.fetchone()

            # Next refresh countdown
            next_boss_at = None
            seconds_remaining = None
            try:
                r = redis.Redis(host='172.16.110.113', port=30379, password='gbq2KlOwPeVmQFRv', decode_responses=True)
                data = r.get('worldboss:next_refresh')
                if data:
                    info = json.loads(data)
                    next_boss_at = info.get('next_boss_at')
                    respawn_min = info.get('respawn_minutes', 30)
                    if next_boss_at:
                        from datetime import datetime
                        delta = datetime.now() - datetime.strptime(next_boss_at, '%Y-%m-%d %H:%M:%S.%f')
                        elapsed = delta.total_seconds()
                        remaining = max(0, respawn_min * 60 - elapsed)
                        if remaining > 0:
                            seconds_remaining = int(remaining)
            except:
                pass

            if not spawn:
                return jsonify({
                    "success": True,
                    "active": False,
                    "boss": None,
                    "ranking": [],
                    "next_boss_at": next_boss_at,
                    "seconds_remaining": seconds_remaining
                })

            # Get player damage ranking (top 10)
            cur.execute("""
                SELECT p.id, p.name, p.level, SUM(wba.damage) as total_damage
                FROM world_boss_attacks wba
                JOIN players p ON p.id = wba.player_id
                WHERE wba.spawn_id = %s
                GROUP BY p.id ORDER BY total_damage DESC LIMIT 10
            """, (spawn['spawn_id'],))
            ranking = [dict(r) for r in cur.fetchall()]

            # Get current player's damage
            cur.execute("""
                SELECT COALESCE(SUM(damage), 0) as my_damage
                FROM world_boss_attacks
                WHERE spawn_id = %s AND player_id = %s
            """, (spawn['spawn_id'], g.player_id))
            my_damage = cur.fetchone()['my_damage']

            return jsonify({
                "success": True,
                "active": True,
                "spawn_id": spawn['spawn_id'],
                "boss": {
                    "name": spawn['name'],
                    "icon": spawn['icon'],
                    "max_hp": spawn['max_hp'],
                    "current_hp": spawn['current_hp'],
                    "hp_percent": int(spawn['current_hp'] / spawn['max_hp'] * 100),
                    "attack": spawn['attack'],
                    "defense": spawn['defense'],
                    "reward_gold": spawn['reward_gold'],
                    "reward_exp": spawn['reward_exp'],
                    "spawn_time": str(spawn['spawn_time'])
                },
                "my_damage": my_damage,
                "can_claim": False,
                "ranking": ranking,
                "next_boss_at": next_boss_at,
                "seconds_remaining": seconds_remaining
            })

@app.route('/api/world_boss/attack', methods=['POST'])
@require_auth
def world_boss_attack():
    """攻击世界BOSS"""
    import random
    with get_db() as conn:
        with get_cursor(conn) as cur:
            # Get active spawn WITH full boss info
            cur.execute("""
                SELECT bs.id, bs.current_hp, bs.status, bs.boss_id,
                       wb.name, wb.icon, wb.max_hp, wb.attack, wb.defense,
                       wb.reward_gold, wb.reward_exp, wb.respawn_minutes
                FROM world_boss_spawns bs
                JOIN world_bosses wb ON wb.id = bs.boss_id
                WHERE bs.status = 'active'
                ORDER BY bs.spawn_time DESC LIMIT 1
            """)
            spawn = cur.fetchone()
            if not spawn:
                return jsonify({"success": False, "reason": "当前没有活动的世界BOSS"})
            if spawn['status'] != 'active':
                return jsonify({"success": False, "reason": "BOSS已被击败"})

            # Get player stats
            cur.execute("SELECT power, level, name, hp FROM players WHERE id = %s", (g.player_id,))
            p = cur.fetchone()
            if not p:
                return jsonify({"success": False, "reason": "玩家不存在"})

            # Add equipment power to damage
            equip_power = 0
            equip_defense = 0
            equip_hp = 0
            equip_crit = 0
            cur.execute("SELECT weapon, helmet, armor, greaves, amulet, ring FROM player_equipment WHERE player_id = %s", (g.player_id,))
            eq = cur.fetchone()
            if eq:
                for slot in ['weapon', 'helmet', 'armor', 'greaves', 'amulet', 'ring']:
                    eid = eq[slot]
                    if eid:
                        cur.execute("SELECT ec.base_power, ec.base_defense, ec.base_hp, ec.base_luck, ee.enhance_level FROM equipment_catalog ec LEFT JOIN equipment_enhance ee ON ee.player_id = %s AND ee.equipment_id = ec.id WHERE ec.id = %s", (g.player_id, eid))
                        erow = cur.fetchone()
                        if erow:
                            enh = erow['enhance_level'] or 0
                            equip_power += (erow['base_power'] or 0) + enh * 1500
                            equip_defense += (erow['base_defense'] or 0) + enh * 1500

            # Calculate damage
            total_power = (p['power'] or 100) + equip_power
            base_dmg = total_power * 100 + random.randint(1000, 5000)
            defense = spawn['defense']
            damage = max(1, int(base_dmg * (1 - defense / (defense + 500))))
            damage = min(damage, spawn['current_hp'])

            # Record individual attack
            cur.execute("""
                INSERT INTO world_boss_attacks (spawn_id, player_id, damage)
                VALUES (%s, %s, %s)
            """, (spawn['id'], g.player_id, damage))

            new_hp = max(0, spawn['current_hp'] - damage)
            announce = None

            if new_hp <= 0:
                # BOSS DEFEATED - distribute rewards to ALL participants
                cur.execute("""
                    UPDATE world_boss_spawns SET current_hp = 0, status = 'defeated', end_time = NOW()
                    WHERE id = %s
                """, (spawn['id'],))

                # Get total damage by all players (sorted by damage descending for proper ranking)
                cur.execute("""
                    SELECT player_id, SUM(damage) as total_damage
                    FROM world_boss_attacks
                    WHERE spawn_id = %s
                    GROUP BY player_id
                    ORDER BY total_damage DESC
                """, (spawn['id'],))
                participants = cur.fetchall()

                # Record kill history
                if participants:
                    killer_id = participants[0]['player_id']
                    cur.execute("SELECT name FROM players WHERE id = %s", (killer_id,))
                    killer_row = cur.fetchone()
                    killer_name = killer_row['name'] if killer_row else '未知'
                    cur.execute("""
                        SELECT wb.name, wb.icon, wb.level_required, wb.reward_exp
                        FROM world_bosses wb WHERE wb.id = %s
                    """, (spawn['boss_id'],))
                    boss_row = cur.fetchone()
                    bname = boss_row['name'] if boss_row else '未知BOSS'
                    bicon = boss_row['icon'] if boss_row else '👹'
                    cur.execute("SELECT NEXTVAL('boss_kill_serial')")
                    serial = cur.fetchone()['nextval']
                    cur.execute("""
                        INSERT INTO world_boss_kill_history (spawn_id, boss_id, boss_name, boss_icon, boss_level, killer_id, killer_name, kill_time, total_attackers, kill_serial)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s)
                        ON CONFLICT (spawn_id) DO NOTHING
                    """, (spawn['id'], spawn['boss_id'], bname, bicon, boss_row['level_required'] if boss_row else 1, killer_id, killer_name, len(participants), serial))

                total_damage = sum(r['total_damage'] for r in participants)
                reward_gold = spawn['reward_gold']
                reward_exp = spawn['reward_exp']

                # Send mail to each participant based on damage %
                for idx, r in enumerate(participants):
                    dmg_pct = r['total_damage'] / total_damage if total_damage > 0 else 0
                    # Top 3 get bonus, rest get proportional
                    rank = idx + 1
                    if rank == 1:
                        gold = int(reward_gold * 0.40)
                        exp = int(reward_exp * 0.40)
                    elif rank == 2:
                        gold = int(reward_gold * 0.25)
                        exp = int(reward_exp * 0.25)
                    elif rank == 3:
                        gold = int(reward_gold * 0.15)
                        exp = int(reward_exp * 0.15)
                    else:
                        gold = int(reward_gold * 0.20 * dmg_pct)
                        exp = int(reward_exp * 0.20 * dmg_pct)
                    gold = max(gold, 1)
                    exp = max(exp, 1)
                    # Get player name
                    cur.execute("SELECT name FROM players WHERE id = %s", (r['player_id'],))
                    pname = cur.fetchone()
                    pname = pname['name'] if pname else '冒险者'
                    try:
                        from models import send_boss_reward_mail
                        # Top 3 get cards
                        if rank <= 3:
                            from models import give_boss_card
                            card_result = give_boss_card(r['player_id'], spawn['boss_id'])
                            if card_result.get('success'):
                                send_boss_reward_mail(r['player_id'], pname, spawn['name'], gold, exp, rank)
                            else:
                                send_boss_reward_mail(r['player_id'], pname, spawn['name'], gold, exp, rank)
                        else:
                            send_boss_reward_mail(r['player_id'], pname, spawn['name'], gold, exp, 0)
                    except Exception as e:
                        print(f"Error distributing boss reward: {e}")

                # Mark all attacks as distributed (update attack_time to mark them processed)
                cur.execute("""
                    UPDATE world_boss_attacks SET attack_time = NOW()
                    WHERE spawn_id = %s AND attack_time IS NULL
                """, (spawn['id'],))

                conn.commit()

                player_name = p['name']
                announce = {
                    'id': f'boss_killed_{spawn["id"]}',
                    'type': 'boss_kill',
                    'icon': spawn['icon'],
                    'message': f'{spawn["icon"]} {spawn["name"]} 被 {player_name} 击杀！全服庆祝！',
                    'chat': f'{spawn["icon"]} 【首杀公告】{player_name} 击败了 {spawn["name"]}！所有参与者已发放奖励到邮箱！',
                    'boss_name': spawn['name'],
                    'killer': player_name,
                    'reward_gold': reward_gold,
                    'reward_exp': reward_exp,
                    'created_at': str(datetime.now())
                }

                # Redis broadcast + next refresh timer
                import redis, json
                try:
                    r2 = redis.Redis(host='172.16.110.113', port=30379, password='gbq2KlOwPeVmQFRv', decode_responses=True)
                    r2.setex('global:announcement', 3600, json.dumps(announce))
                    r2.setex('worldboss:killed:' + str(spawn['id']), 3600, json.dumps(announce))
                    next_info = {'next_boss_at': str(datetime.now()), 'respawn_minutes': spawn['respawn_minutes']}
                    r2.setex('worldboss:next_refresh', spawn['respawn_minutes'] * 60, json.dumps(next_info))
                    add_public_chat(None, 'system', announce['chat'])
                except:
                    pass

                boss_status = 'defeated'
            else:
                cur.execute("UPDATE world_boss_spawns SET current_hp = %s WHERE id = %s", (new_hp, spawn['id']))
                conn.commit()
                boss_status = 'active'

            # Boss counter-attack
            boss_dmg = max(10, (spawn['attack'] or 100) // 5)
            cur.execute("UPDATE players SET hp = GREATEST(1, hp - %s) WHERE id = %s", (boss_dmg, g.player_id))
            conn.commit()

            return jsonify({
                "success": True,
                "damage": damage,
                "boss_hp": new_hp,
                "boss_hp_percent": int(new_hp / spawn['max_hp'] * 100),
                "boss_status": boss_status,
                "counter_damage": boss_dmg,
                "announcement": announce
            })

@app.route('/api/boss_cards/my', methods=['GET'])
@require_auth
def my_boss_cards():
    """获取我的BOSS收集卡"""
    from models import get_player_boss_cards
    cards = get_player_boss_cards(g.player_id)
    return jsonify({"success": True, "cards": cards})

@app.route('/api/boss_cards/all', methods=['GET'])
@require_auth
def all_boss_cards():
    """获取所有BOSS卡片图鉴"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT id, boss_id, name, icon, rarity, description, hp, attack, defense FROM boss_cards ORDER BY id")
            all_cards = [dict(r) for r in cur.fetchall()]
            # Mark which ones player has
            cur.execute("SELECT card_id FROM player_boss_cards WHERE player_id = %s", (g.player_id,))
            owned = set(r['card_id'] for r in cur.fetchall())
            for c in all_cards:
                c['owned'] = c['id'] in owned
            # Get kill history for all cards (only show if current player killed it)
            for c in all_cards:
                cur.execute("""
                    SELECT killer_name, kill_time, total_attackers, kill_serial
                    FROM world_boss_kill_history
                    WHERE boss_id = %s AND killer_id = %s
                    ORDER BY kill_time ASC
                    LIMIT 1
                """, (c['boss_id'], g.player_id))
                kh = cur.fetchone()
                if kh:
                    c['killer_name'] = kh['killer_name']
                    c['kill_time'] = str(kh['kill_time'])
                    c['total_attackers'] = kh['total_attackers']
                    c['kill_serial'] = kh['kill_serial']
                else:
                    # Player hasn't killed this boss themselves
                    c['killer_name'] = None
                    c['kill_time'] = None
                    c['total_attackers'] = None
                    c['kill_serial'] = None
            return jsonify({"success": True, "cards": all_cards})

@app.route('/api/world_boss/claim', methods=['POST'])
@require_auth
def world_boss_claim():
    """领取世界BOSS奖励"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT bs.id, wb.reward_gold, wb.reward_exp
                FROM world_boss_spawns bs
                JOIN world_bosses wb ON wb.id = bs.boss_id
                WHERE bs.status = 'defeated'
                ORDER BY bs.spawn_time DESC LIMIT 1
            """)
            spawn = cur.fetchone()
            if not spawn:
                return jsonify({"success": False, "reason": "没有可领取的奖励"})
            
            # Check if player dealt damage
            cur.execute("""
                SELECT SUM(damage) as total FROM world_boss_attacks
                WHERE spawn_id = %s AND player_id = %s
            """, (spawn['id'], g.player_id))
            dmg = cur.fetchone()['total'] or 0
            if dmg <= 0:
                return jsonify({"success": False, "reason": "未对BOSS造成伤害，无法领取"})
            
            # Award gold and exp
            cur.execute("UPDATE players SET gold = gold + %s, exp = exp + %s WHERE id = %s",
                       (spawn['reward_gold'], spawn['reward_exp'], g.player_id))
            conn.commit()
            
            return jsonify({
                "success": True,
                "reward_gold": spawn['reward_gold'],
                "reward_exp": spawn['reward_exp'],
                "message": f"获得 {spawn['reward_gold']} 金贝 + {spawn['reward_exp']} 经验！"
            })

# ==================== 武道大会 ====================
@app.route('/api/arena/status', methods=['GET'])
@require_auth
def arena_status():
    """获取武道大会状态"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT id, name, icon, max_participants, entry_fee,
                       reward_gold, reward_exp, start_time, end_time, status, description
                FROM arena_tournaments
                WHERE status IN ('signup', 'ongoing', 'finished')
                ORDER BY start_time DESC LIMIT 1
            """)
            t = cur.fetchone()
            if not t:
                return jsonify({"success": True, "tournament": None, "my_status": None})
            
            # Count participants
            cur.execute("SELECT COUNT(*) as cnt FROM arena_participants WHERE tournament_id = %s", (t['id'],))
            count = cur.fetchone()['cnt']
            
            # Check if player joined
            cur.execute("""
                SELECT 1 FROM arena_participants
                WHERE tournament_id = %s AND player_id = %s
            """, (t['id'], g.player_id))
            joined = cur.fetchone() is not None
            
            # Get recent matches if ongoing
            matches = []
            if t['status'] == 'ongoing':
                cur.execute("""
                    SELECT am.*, p1.name as p1_name, p2.name as p2_name,
                           pw.name as winner_name
                    FROM arena_matches am
                    LEFT JOIN players p1 ON p1.id = am.player1_id
                    LEFT JOIN players p2 ON p2.id = am.player2_id
                    LEFT JOIN players pw ON pw.id = am.winner_id
                    WHERE am.tournament_id = %s
                    ORDER BY am.round DESC, am.match_num
                    LIMIT 20
                """, (t['id'],))
                matches = [dict(r) for r in cur.fetchall()]
            
            return jsonify({
                "success": True,
                "tournament": {
                    "id": t['id'],
                    "name": t['name'],
                    "icon": t['icon'],
                    "max_participants": t['max_participants'],
                    "current_participants": count,
                    "entry_fee": t['entry_fee'],
                    "reward_gold": t['reward_gold'],
                    "reward_exp": t['reward_exp'],
                    "start_time": str(t['start_time']),
                    "status": t['status'],
                    "description": t['description']
                },
                "joined": joined,
                "matches": matches
            })

@app.route('/api/arena/join', methods=['POST'])
@require_auth
def arena_join():
    """报名武道大会"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT id, status, entry_fee FROM arena_tournaments
                WHERE status = 'signup' ORDER BY start_time DESC LIMIT 1
            """)
            t = cur.fetchone()
            if not t:
                return jsonify({"success": False, "reason": "当前没有开放的武道大会"})
            
            # Check if already joined
            cur.execute("""
                SELECT 1 FROM arena_participants
                WHERE tournament_id = %s AND player_id = %s
            """, (t['id'], g.player_id))
            if cur.fetchone():
                return jsonify({"success": False, "reason": "已经报名过了"})
            
            # Check player gold
            if t['entry_fee'] > 0:
                cur.execute("SELECT gold FROM players WHERE id = %s", (g.player_id,))
                gold = cur.fetchone()['gold']
                if gold < t['entry_fee']:
                    return jsonify({"success": False, "reason": f"报名费 {t['entry_fee']} 金贝不足"})
                cur.execute("UPDATE players SET gold = gold - %s WHERE id = %s", (t['entry_fee'], g.player_id))
            
            cur.execute("""
                INSERT INTO arena_participants (tournament_id, player_id)
                VALUES (%s, %s)
            """, (t['id'], g.player_id))
            conn.commit()
            
            # If full, generate bracket and start
            cur.execute("SELECT COUNT(*) as cnt FROM arena_participants WHERE tournament_id = %s", (t['id'],))
            cnt = cur.fetchone()['cnt']
            
            if cnt >= t.get('max_participants', 8):
                # Start tournament - generate bracket
                cur.execute("UPDATE arena_tournaments SET status = 'ongoing' WHERE id = %s", (t['id'],))
                
                # Get all participants
                cur.execute("""
                    SELECT player_id FROM arena_participants
                    WHERE tournament_id = %s ORDER BY RANDOM()
                """, (t['id'],))
                players = [r['player_id'] for r in cur.fetchall()]
                
                # Create first round matches
                for i in range(0, len(players), 2):
                    if i + 1 < len(players):
                        cur.execute("""
                            INSERT INTO arena_matches (tournament_id, round, match_num, player1_id, player2_id, status)
                            VALUES (%s, 1, %s, %s, %s, 'pending')
                        """, (t['id'], i // 2 + 1, players[i], players[i + 1]))
                
                conn.commit()
            
            return jsonify({"success": True, "message": "报名成功！", "participants": cnt})

# ==================== 门派 ====================
@app.route('/api/factions', methods=['GET'])
@require_auth
def factions_list():
    # 获取玩家当前的宗门 (不缓存)
    player = get_player_full(g.player_id)
    my_faction = None
    if player and player.get('faction'):
        with get_db() as conn:
            with get_cursor(conn) as cur:
                cur.execute("SELECT faction_id, name, description, bonus_effect, guardian_beast, guardian_artifact, level, silver as funds FROM factions WHERE faction_id = %s", (player['faction'],))
                row = cur.fetchone()
                if row:
                    my_faction = dict(row)
    
    # 尝试从Redis缓存获取宗门列表
    cache_key = 'factions:list'
    cached = cache_get(cache_key)
    if cached:
        return jsonify({"success": True, "factions": cached, "my_faction": my_faction})
    
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT faction_id, name, description, bonus_effect, guardian_beast, guardian_artifact, level, silver as funds FROM factions ORDER BY id")
            factions = [dict(r) for r in cur.fetchall()]
    
    # 缓存10分钟
    cache_set(cache_key, factions, 600)
    
    return jsonify({"success": True, "factions": factions, "my_faction": my_faction})

@app.route('/api/factions/join', methods=['POST'])
@require_auth
def faction_join():
    data = request.get_json(force=True) or {}
    faction_id = data.get('faction_id')
    if not faction_id:
        return jsonify({"success": False, "reason": "缺少faction_id"}), 400
    result = join_faction(g.player_id, faction_id)
    if result.get('success'):
        log_action(g.player_id, g.player.get('name', ''), '加入门派', f"加入 {result.get('faction', '')}")
        update_task_progress(g.player_id, 'join_faction', 1)
    return jsonify(result)

@app.route('/api/factions/leave', methods=['POST'])
@require_auth
def faction_leave():
    data = request.get_json(force=True) or {}
    # faction_id 可以不传，默认退出现在所在的宗门
    result = leave_faction(g.player_id)
    if result.get('success'):
        log_action(g.player_id, g.player.get('name', ''), '退出门派', '退出宗门')
    return jsonify(result)

@app.route('/api/factions/donate', methods=['POST'])
@require_auth
def faction_donate():
    """银贝捐献升级宗门等级"""
    data = request.get_json(force=True) or {}
    silver_amount = int(data.get('silver', 0))

    if silver_amount <= 0:
        return jsonify({"success": False, "reason": "捐献数量必须大于0"})

    # 捐献档位
    donate_options = [100, 500, 1000, 5000]
    if silver_amount not in donate_options:
        return jsonify({"success": False, "reason": f"每次捐献数量必须是：{', '.join(str(x) + '银贝' for x in donate_options)}"})

    player = get_player_full(g.player_id)
    if not player or not player.get('faction'):
        return jsonify({"success": False, "reason": "请先加入宗门"})

    if player.get('silver', 0) < silver_amount:
        return jsonify({"success": False, "reason": f"银贝不足，当前拥有 {player.get('silver', 0)} 银贝"})

    faction_id = player['faction']

    with get_db() as conn:
        with get_cursor(conn) as cur:
            # 扣除银贝
            cur.execute("UPDATE players SET silver = silver - %s WHERE id = %s", (silver_amount, g.player_id))

            # 增加宗门资金和经验
            cur.execute("UPDATE factions SET silver = silver + %s WHERE faction_id = %s", (silver_amount, faction_id))

            # 获取当前宗门等级
            cur.execute("SELECT level, silver as funds FROM factions WHERE faction_id = %s", (faction_id,))
            faction = cur.fetchone()

            current_level = faction['level'] or 1
            current_funds = faction['funds'] or 0

            # 升级所需资金
            upgrade_needed = current_level * 10000
            old_level = current_level
            new_level = current_level

            # 检查是否可以升级
            while current_funds >= new_level * 10000:
                current_funds -= new_level * 10000
                new_level += 1
                # 宗门最高10级
                if new_level >= 10:
                    break

            if new_level > old_level:
                cur.execute("UPDATE factions SET level = %s, silver = %s WHERE faction_id = %s",
                           (new_level, current_funds, faction_id))
                upgrade_msg = f"宗门升级至 Lv.{new_level}！"
            else:
                upgrade_msg = f"本次捐献 {silver_amount} 银贝，离升级还需 {upgrade_needed - current_funds} 银贝"

            conn.commit()

            log_action(g.player_id, player.get('name', ''), '宗门捐献',
                      f"捐献 {silver_amount} 银贝 → {upgrade_msg}")

            # 返回更新后的宗门信息
            cur.execute("""
                SELECT f.level, f.silver as funds, f.bonus_effect,
                       p.name as player_name
                FROM factions f
                JOIN players p ON p.id = %s
                WHERE f.faction_id = %s
            """, (g.player_id, faction_id))
            info = cur.fetchone()

            return jsonify({
                "success": True,
                "message": upgrade_msg,
                "donated": silver_amount,
                "faction": {
                    "level": new_level,
                    "funds": current_funds if new_level > old_level else current_funds + silver_amount,
                    "bonus_effect": info['bonus_effect']
                }
            })

# ==================== 装备系统 ====================
@app.route('/api/equipment/my', methods=['GET'])
@require_auth
def equipment_my():
    """获取我的装备穿戴信息"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            slot_names = ['weapon', 'helmet', 'armor', 'greaves', 'amulet', 'ring']
            slot_display = {'weapon':'武器','helmet':'头盔','armor':'盔甲','greaves':'护胫骨','amulet':'护身符','ring':'戒指'}
            slots = {}

            # Compute total equip combat stats
            equip_power = 0
            equip_defense = 0
            equip_hp = 0
            equip_crit = 0
            equipped_items = {}

            cur.execute("SELECT weapon, helmet, armor, greaves, amulet, ring FROM player_equipment WHERE player_id = %s", (g.player_id,))
            eq = cur.fetchone()
            if eq:
                for slot in slot_names:
                    eid = eq[slot]
                    if eid:
                        cur.execute("""
                            SELECT ec.*, ee.enhance_level
                            FROM equipment_catalog ec
                            LEFT JOIN equipment_enhance ee ON ee.player_id = %s AND ee.equipment_id = ec.id
                            WHERE ec.id = %s
                        """, (g.player_id, eid))
                        item = cur.fetchone()
                        if item:
                            enh = item['enhance_level'] or 0
                            epower = (item['base_power'] or 0) + enh * 1500
                            edef = (item['base_defense'] or 0) + enh * 1500
                            ehp = (item['base_hp'] or 0) + enh * 1500
                            ecrit = (item['base_luck'] or 0) + enh * 0
                            equip_power += epower
                            equip_defense += edef
                            equip_hp += ehp
                            equip_crit += ecrit
                            slots[slot] = dict(item)
                            slots[slot]['_epower'] = epower
                            slots[slot]['_edef'] = edef
                            slots[slot]['_ehp'] = ehp
                            slots[slot]['_ecrit'] = ecrit
                    else:
                        slots[slot] = None
            else:
                for slot in slot_names:
                    slots[slot] = None

            # Get fragments
            cur.execute("SELECT wealth_fragments, prosperity_fragments FROM player_fragments WHERE player_id = %s", (g.player_id,))
            fr = cur.fetchone()
            fragments = {
                'wealth': fr['wealth_fragments'] if fr else 0,
                'prosperity': fr['prosperity_fragments'] if fr else 0
            }

            # Get player's owned equipment pieces
            cur.execute("""
                SELECT ec.id, ec.tier, ec.tier_name, ec.slot, ec.name, ec.set_type,
                       ee.enhance_level, ec.base_power, ec.base_defense, ec.base_hp, ec.base_luck,
                       ec.description
                FROM equipment_pieces ep
                JOIN equipment_catalog ec ON ec.id = ep.equipment_id
                LEFT JOIN equipment_enhance ee ON ee.player_id = ep.player_id AND ee.equipment_id = ep.equipment_id
                WHERE ep.player_id = %s
                ORDER BY ec.tier DESC, ec.slot
            """, (g.player_id,))
            owned = [dict(r) for r in cur.fetchall()]

            return jsonify({
                "success": True,
                "equipped": slots,
                "fragments": fragments,
                "owned": owned,
                "slot_display": slot_display,
                "combat": {
                    "power": equip_power,
                    "defense": equip_defense,
                    "hp": equip_hp,
                    "crit": equip_crit
                }
            })

@app.route('/api/equipment/wear', methods=['POST'])
@require_auth
def equipment_wear():
    """穿装备"""
    data = request.get_json(force=True) or {}
    slot = data.get('slot')  # weapon, helmet, armor, greaves, amulet, ring
    equipment_id = data.get('equipment_id')  # None means take off

    valid_slots = ['weapon', 'helmet', 'armor', 'greaves', 'amulet', 'ring']
    if slot not in valid_slots:
        return jsonify({"success": False, "reason": "无效的装备槽位"})

    player = get_player_full(g.player_id)
    if not player:
        return jsonify({"success": False, "reason": "玩家不存在"})

    with get_db() as conn:
        with get_cursor(conn) as cur:
            # Verify player owns this equipment
            if equipment_id:
                cur.execute("""
                    SELECT id FROM equipment_pieces WHERE player_id = %s AND equipment_id = %s
                """, (g.player_id, equipment_id))
                if not cur.fetchone():
                    return jsonify({"success": False, "reason": "没有这件装备"})

                # Verify slot matches
                cur.execute("SELECT slot FROM equipment_catalog WHERE id = %s", (equipment_id,))
                row = cur.fetchone()
                if not row or row['slot'] != slot:
                    return jsonify({"success": False, "reason": "装备槽位不匹配"})

            # Get or create player_equipment row
            cur.execute("SELECT * FROM player_equipment WHERE player_id = %s", (g.player_id,))
            if not cur.fetchone():
                cur.execute("INSERT INTO player_equipment (player_id) VALUES (%s)", (g.player_id,))
                conn.commit()

            # Update slot
            cur.execute(f"UPDATE player_equipment SET {slot} = %s WHERE player_id = %s",
                       (equipment_id, g.player_id))
            conn.commit()

            log_action(g.player_id, player.get('name', ''), '穿戴装备',
                      f"{slot} <- {equipment_id if equipment_id else '卸下'}")

            return jsonify({"success": True, "message": "穿戴成功" if equipment_id else "已卸下"})

@app.route('/api/equipment/enhance', methods=['POST'])
@require_auth
def equipment_enhance():
    """强化装备"""
    data = request.get_json(force=True) or {}
    equipment_id = data.get('equipment_id')
    cost_silver = 1000  # 强化一次1000银贝

    player = get_player_full(g.player_id)
    if not player:
        return jsonify({"success": False, "reason": "玩家不存在"})

    if player.get('silver', 0) < cost_silver:
        return jsonify({"success": False, "reason": f"银贝不足，需要{cost_silver}银贝"})

    with get_db() as conn:
        with get_cursor(conn) as cur:
            # Check current enhance level
            cur.execute("""
                SELECT enhance_level FROM equipment_enhance
                WHERE player_id = %s AND equipment_id = %s
            """, (g.player_id, equipment_id))
            row = cur.fetchone()
            current = row['enhance_level'] if row else 0

            if current >= 5:
                return jsonify({"success": False, "reason": "强化等级已达上限+5"})

            # Deduct silver
            cur.execute("UPDATE players SET silver = silver - %s WHERE id = %s",
                       (cost_silver, g.player_id))

            # Upsert enhance level
            new_level = current + 1
            cur.execute("""
                INSERT INTO equipment_enhance (player_id, equipment_id, enhance_level)
                VALUES (%s, %s, %s)
                ON CONFLICT (player_id, equipment_id) DO UPDATE SET enhance_level = %s
            """, (g.player_id, equipment_id, new_level, new_level))
            conn.commit()

            log_action(g.player_id, player.get('name', ''), '强化装备',
                      f"装备强化至+{new_level}")

            return jsonify({
                "success": True,
                "message": f"强化成功！+{new_level} ⚔️+1500 🛡️+1500 ❤️+1500",
                "new_level": new_level,
                "power_add": 1500,
                "defense_add": 1500,
                "hp_add": 1500,
                "crit_add": 0
            })

@app.route('/api/equipment/synthesize', methods=['POST'])
@require_auth
def equipment_synthesize():
    """合成装备（100碎片）"""
    data = request.get_json(force=True) or {}
    slot = data.get('slot')
    tier = data.get('tier', 1)  # which tier to synthesize (1-17)
    set_type = data.get('set_type', 'wealth')  # wealth or prosperity

    valid_slots = ['weapon', 'helmet', 'armor', 'greaves', 'amulet', 'ring']
    if slot not in valid_slots:
        return jsonify({"success": False, "reason": "无效的装备槽位"})

    player = get_player_full(g.player_id)

    frag_key = 'wealth_fragments' if set_type == 'wealth' else 'prosperity_fragments'

    with get_db() as conn:
        with get_cursor(conn) as cur:
            # Check fragments
            cur.execute(f"SELECT {frag_key} FROM player_fragments WHERE player_id = %s",
                       (g.player_id,))
            row = cur.fetchone()
            current_frag = row[frag_key] if row else 0

            if current_frag < 100:
                return jsonify({"success": False, "reason": f"碎片不足，需要100个，当前{current_frag}个"})

            # Deduct fragments
            cur.execute(f"UPDATE player_fragments SET {frag_key} = {frag_key} - 100 WHERE player_id = %s",
                       (g.player_id,))

            # Find equipment in catalog
            cur.execute("""
                SELECT id, name, tier, slot, tier_name, set_type,
                       base_power, base_defense, base_hp, base_luck
                FROM equipment_catalog
                WHERE tier = %s AND slot = %s AND set_type = %s
                LIMIT 1
            """, (tier, slot, set_type))
            catalog_item = cur.fetchone()

            if not catalog_item:
                return jsonify({"success": False, "reason": "合成配方不存在"})

            # Give equipment piece to player
            cur.execute("""
                INSERT INTO equipment_pieces (player_id, equipment_id)
                VALUES (%s, %s)
            """, (g.player_id, catalog_item['id']))
            conn.commit()

            log_action(g.player_id, player.get('name', ''), '合成装备',
                      f"合成获得 {catalog_item['name']}")

            return jsonify({
                "success": True,
                "message": f"合成成功！获得 {catalog_item['name']}",
                "equipment": dict(catalog_item)
            })

@app.route('/api/equipment/flash_sale', methods=['GET'])
@require_auth
def equipment_flash_sale():
    """限时抢购"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            # Check if there's an active flash sale
            cur.execute("""
                SELECT es.id, es.equipment_id, es.refresh_at, es.is_sold,
                       ec.tier, ec.tier_name, ec.slot, ec.name, ec.set_type,
                       ec.base_power, ec.base_defense, ec.base_hp, ec.base_luck, ec.description
                FROM equipment_flash_sale es
                JOIN equipment_catalog ec ON ec.id = es.equipment_id
                WHERE es.refresh_at > NOW() AND es.is_sold = FALSE
                LIMIT 6
            """, (g.player_id,))
            items = [dict(r) for r in cur.fetchall()]

            if not items:
                # Refresh flash sale - 6 random equipment
                cur.execute("DELETE FROM equipment_flash_sale")
                cur.execute("""
                    INSERT INTO equipment_flash_sale (equipment_id, refresh_at)
                    SELECT id, NOW() + INTERVAL '2 hours'
                    FROM equipment_catalog
                    ORDER BY RANDOM() LIMIT 6
                """)
                conn.commit()

                cur.execute("""
                    SELECT es.id, es.equipment_id, es.refresh_at,
                           ec.tier, ec.tier_name, ec.slot, ec.name, ec.set_type,
                           ec.base_power, ec.base_defense, ec.base_hp, ec.base_luck, ec.description
                    FROM equipment_flash_sale es
                    JOIN equipment_catalog ec ON ec.id = es.equipment_id
                    WHERE es.refresh_at > NOW()
                """)
                items = [dict(r) for r in cur.fetchall()]

            # Get player silver
            player = get_player_full(g.player_id)

            return jsonify({
                "success": True,
                "items": items,
                "player_silver": player.get('silver', 0) if player else 0,
                "slot_display": {'weapon':'武器','helmet':'头盔','armor':'盔甲','greaves':'护胫骨','amulet':'护身符','ring':'戒指'}
            })

@app.route('/api/equipment/flash_buy', methods=['POST'])
@require_auth
def equipment_flash_buy():
    """购买限时装备"""
    data = request.get_json(force=True) or {}
    flash_sale_id = data.get('flash_sale_id')
    cost = 100000  # 10万金贝

    player = get_player_full(g.player_id)
    if not player:
        return jsonify({"success": False, "reason": "玩家不存在"})

    if player.get('gold', 0) < cost:
        return jsonify({"success": False, "reason": f"金贝不足，需要{cost}金贝"})

    with get_db() as conn:
        with get_cursor(conn) as cur:
            # Check flash sale item
            cur.execute("""
                SELECT es.*, ec.name as equip_name
                FROM equipment_flash_sale es
                JOIN equipment_catalog ec ON ec.id = es.equipment_id
                WHERE es.id = %s AND es.is_sold = FALSE AND es.refresh_at > NOW()
            """, (flash_sale_id,))
            item = cur.fetchone()

            if not item:
                return jsonify({"success": False, "reason": "商品已售罄或已过期"})

            # Deduct gold
            cur.execute("UPDATE players SET gold = gold - %s WHERE id = %s",
                       (cost, g.player_id))

            # Mark as sold
            cur.execute("UPDATE equipment_flash_sale SET is_sold = TRUE WHERE id = %s",
                       (flash_sale_id,))

            # Give equipment piece via mail
            import uuid, json
            msg_id = f'equip_flash_{uuid.uuid4().hex[:12]}'
            content = f'⚡ 恭喜您通过限时抢购获得：【{item["equip_name"]}】一件！请前往角色-装备页穿戴！'
            attachments = json.dumps([{
                'type': 'equipment',
                'id': item['equipment_id'],
                'name': item['equip_name']
            }])
            cur.execute("""
                INSERT INTO player_messages (message_id, sender_id, receiver_id, message_type, content, status, attachments, created_at)
                VALUES (%s, NULL, %s, 'system_gift', %s, 'unclaimed', %s, NOW())
            """, (msg_id, g.player_id, content, attachments))
            conn.commit()

            log_action(g.player_id, player.get('name', ''), '限时抢购',
                      f"购买 {item['equip_name']}")

            return jsonify({
                "success": True,
                "message": f"购买成功！获得 {item['equip_name']}"
            })

# ==================== 深渊装备掉落 ====================
@app.route('/api/abyss/claim_reward', methods=['POST'])
@require_auth
def abyss_claim_reward():
    """深渊boss击败奖励：1件装备 + 5碎片"""
    data = request.get_json(force=True) or {}
    monster_level = data.get('monster_level', 1)  # 1-20

    player = get_player_full(g.player_id)
    if not player:
        return jsonify({"success": False, "reason": "玩家不存在"})

    # Determine tier based on monster level
    # monster_level 1-5 -> tier 1-3
    # monster_level 6-10 -> tier 4-7
    # monster_level 11-15 -> tier 8-12
    # monster_level 16-20 -> tier 13-17
    tier = min(17, max(1, (monster_level - 1) // 2 + 1))

    with get_db() as conn:
        with get_cursor(conn) as cur:
            # Give 5 fragments
            frag_type = 'prosperity_fragments' if monster_level >= 10 else 'wealth_fragments'
            cur.execute("""
                INSERT INTO player_fragments (player_id, wealth_fragments, prosperity_fragments)
                VALUES (%s, 0, 0)
                ON CONFLICT (player_id) DO UPDATE SET
                    wealth_fragments = player_fragments.wealth_fragments + CASE WHEN %s = 'wealth_fragments' THEN 5 ELSE 0 END,
                    prosperity_fragments = player_fragments.prosperity_fragments + CASE WHEN %s = 'prosperity_fragments' THEN 5 ELSE 0 END
            """, (g.player_id, frag_type, frag_type))

            # Give 1 random equipment of appropriate tier
            # Prefer the set type matching the monster level
            set_type = 'prosperity' if monster_level >= 10 else 'wealth'
            cur.execute("""
                SELECT id, name, tier, tier_name, slot, set_type,
                       base_power, base_defense, base_hp, base_luck
                FROM equipment_catalog
                WHERE tier = %s AND set_type = %s
                ORDER BY RANDOM()
                LIMIT 1
            """, (tier, set_type))
            equip = cur.fetchone()

            if not equip:
                # Fallback to any tier
                cur.execute("""
                    SELECT id, name, tier, tier_name, slot, set_type,
                           base_power, base_defense, base_hp, base_luck
                    FROM equipment_catalog
                    WHERE tier = %s
                    ORDER BY RANDOM()
                    LIMIT 1
                """, (tier,))
                equip = cur.fetchone()

            equipment_gained = None
            if equip:
                cur.execute("""
                    INSERT INTO equipment_pieces (player_id, equipment_id)
                    VALUES (%s, %s)
                """, (g.player_id, equip['id']))
                equipment_gained = dict(equip)

            conn.commit()

            log_action(g.player_id, player.get('name', ''), '深渊奖励',
                      f"击败深渊boss获得 {equipment_gained['name'] if equipment_gained else '无'} + 5碎片")

            return jsonify({
                "success": True,
                "message": f"获得 {equipment_gained['name'] if equipment_gained else '无'} + 5碎片",
                "fragment_type": frag_type.replace('_fragments', ''),
                "fragment_count": 5,
                "equipment": equipment_gained
            })

# ==================== 保护盾 ====================
@app.route('/api/shield/status', methods=['GET'])
@require_auth
def shield_status():
    return jsonify(get_protection_status(g.player_id))

@app.route('/api/shield/activate', methods=['POST'])
@require_auth
def shield_activate():
    data = request.get_json(force=True) or {}
    shield_type = data.get('shield_type', 'silver_5h')
    result = activate_shield(g.player_id, shield_type)
    return jsonify(result)

@app.route('/api/shield/deactivate', methods=['POST'])
@require_auth
def shield_deactivate():
    """取消保护盾（30分钟冷却）"""
    result = deactivate_shield(g.player_id)
    return jsonify(result)

# ==================== 消息 ====================
@app.route('/api/messages/inbox', methods=['GET'])
@require_auth
def inbox():
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT id, sender_id, receiver_id, message_type, content, attachments, status, is_favorite, created_at
                FROM player_messages WHERE receiver_id = %s ORDER BY created_at DESC LIMIT 50
            """, (g.player_id,))
            msgs = [dict(r) for r in cur.fetchall()]
            return jsonify({"success": True, "messages": msgs})

@app.route('/api/messages/outbox', methods=['GET'])
@require_auth
def outbox():
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT id, sender_id, receiver_id, message_type, content, is_favorite, created_at
                FROM player_messages WHERE sender_id = %s ORDER BY created_at DESC LIMIT 50
            """, (g.player_id,))
            msgs = [dict(r) for r in cur.fetchall()]
            return jsonify({"success": True, "messages": msgs})

@app.route('/api/messages/favorite', methods=['POST'])
@require_auth
def messages_favorite():
    data = request.get_json(force=True) or {}
    msg_id = data.get('message_id')
    if not msg_id:
        return jsonify({"success": False, "reason": "缺少message_id"}), 400
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                UPDATE player_messages SET is_favorite = NOT is_favorite
                WHERE id = %s AND receiver_id = %s RETURNING is_favorite
            """, (msg_id, g.player_id))
            row = cur.fetchone()
            conn.commit()
            if not row:
                return jsonify({"success": False, "reason": "邮件不存在"}), 404
            return jsonify({"success": True, "is_favorite": row['is_favorite']})

@app.route('/api/messages/claim', methods=['POST'])
@require_auth
def messages_claim():
    data = request.get_json(force=True) or {}
    msg_id = data.get('message_id')
    if not msg_id:
        return jsonify({"success": False, "reason": "缺少message_id"}), 400
    result = claim_mail_attachment(g.player_id, msg_id)
    return jsonify(result)

@app.route('/api/messages/delete', methods=['POST'])
@require_auth
def messages_delete():
    data = request.get_json(force=True) or {}
    delete_all = data.get('delete_all', False)
    
    with get_db() as conn:
        with get_cursor(conn) as cur:
            if delete_all:
                # 只删除已领取的邮件（非收藏）
                cur.execute("""
                    DELETE FROM player_messages
                    WHERE receiver_id = %s AND is_favorite = FALSE AND status = 'claimed'
                """, (g.player_id,))
            else:
                # 删除指定邮件
                # 支持单个 message_id 或批量 message_ids
                message_ids = data.get('message_ids', [])
                single_id = data.get('message_id')
                if single_id:
                    message_ids = [single_id]
                if not message_ids:
                    return jsonify({"success": False, "reason": "缺少message_ids"}), 400
                cur.execute("""
                    DELETE FROM player_messages
                    WHERE id IN %s AND receiver_id = %s AND is_favorite = FALSE
                """, (tuple(message_ids), g.player_id))
            deleted = cur.rowcount
            conn.commit()
            return jsonify({"success": True, "deleted": deleted})


# ==================== 技能 ====================
@app.route('/api/skills/my', methods=['GET'])
@require_auth
def my_skills():
    """获取已学技能"""
    skills = get_player_skills(g.player_id)
    available_points = get_skill_points(g.player_id)
    return jsonify({
        "success": True,
        "skills": skills,
        "available_points": available_points
    })

@app.route('/api/skills/available', methods=['GET'])
@require_auth
def available_skills():
    """获取可学习的技能（根据门派）"""
    import skills as skill_data
    SKILLS = skill_data.SKILLS
    player_faction = g.player.get('faction')
    
    available = []
    for key, skill in SKILLS.items():
        # 通用技能所有人都能学
        if 'faction' not in skill:
            available.append({
                "key": key,
                "name": skill['name'],
                "type": skill.get('type', 'attack'),
                "mp_cost": skill.get('mp_cost', 0),
                "description": skill.get('description', ''),
                "faction": None,
                "faction_name": "通用"
            })
        elif player_faction == skill['faction']:
            available.append({
                "key": key,
                "name": skill['name'],
                "type": skill.get('type', 'attack'),
                "mp_cost": skill.get('mp_cost', 0),
                "description": skill.get('description', ''),
                "faction": skill['faction'],
                "faction_name": player_faction
            })
    
    return jsonify({
        "success": True,
        "skills": available,
        "player_faction": player_faction
    })

@app.route('/api/skills/learn', methods=['POST'])
@require_auth
def api_learn_skill():
    """学习技能"""
    data = request.get_json(force=True) or {}
    skill_key = data.get('skill_key')
    if not skill_key:
        return jsonify({"success": False, "reason": "缺少skill_key"}), 400
    
    result = learn_skill(g.player_id, skill_key)
    return jsonify(result)

# ==================== 任务重置 ====================
@app.route('/api/tasks/reset', methods=['POST'])
@require_auth
def task_reset():
    result = reset_expired_tasks(g.player_id)
    return jsonify(result)

# ==================== 掠夺 ====================
@app.route('/api/plunder/do', methods=['POST'])
@require_auth
def plunder():
    """掠夺其他玩家（每次100金贝，自己最多掠夺3次）"""
    data = request.get_json(force=True) or {}
    victim_id = data.get('victim_id')
    if not victim_id:
        return jsonify({"success": False, "reason": "缺少victim_id"}), 400
    
    victim_id = int(victim_id)
    if victim_id == g.player_id:
        return jsonify({"success": False, "reason": "不能掠夺自己"})
    
    with get_db() as conn:
        with get_cursor(conn) as cur:
            # 检查掠夺者是否还有次数
            cur.execute("SELECT plunder_count FROM players WHERE id = %s", (g.player_id,))
            row = cur.fetchone()
            current_plunders = row['plunder_count'] if row else 0
            if current_plunders >= 3:
                return jsonify({"success": False, "reason": "你今天掠夺次数已用完（3次）"})
            
            # 检查目标玩家
            cur.execute("SELECT id, name, gold FROM players WHERE id = %s", (victim_id,))
            victim = cur.fetchone()
            if not victim:
                return jsonify({"success": False, "reason": "目标玩家不存在"})
            
            if victim['gold'] < 100:
                return jsonify({"success": False, "reason": "目标金贝不足100，无法掠夺"})
            
            # 检查是否已经掠夺过该目标
            cur.execute("SELECT 1 FROM plunder_log WHERE plunderer_id = %s AND victim_id = %s", (g.player_id, victim_id))
            if cur.fetchone():
                return jsonify({"success": False, "reason": "已经掠夺过该玩家，不能重复掠夺"})
            
            # 执行掠夺：目标-100，掠夺者+100
            cur.execute("UPDATE players SET gold = gold - 100 WHERE id = %s AND gold >= 100", (victim_id,))
            if cur.rowcount == 0:
                return jsonify({"success": False, "reason": "目标金贝不足，掠夺失败"})
            
            cur.execute("UPDATE players SET gold = gold + 100, plunder_count = plunder_count + 1 WHERE id = %s", (g.player_id,))
            
            # 记录掠夺
            cur.execute("""
                INSERT INTO plunder_log (plunderer_id, victim_id, gold_amount)
                VALUES (%s, %s, 100)
                ON CONFLICT (plunderer_id, victim_id) DO NOTHING
            """, (g.player_id, victim_id))
            
            conn.commit()
            
            log_action(g.player_id, g.player.get('name', ''), '掠夺', f"掠夺 {victim['name']} 获得100金贝")
            
            return jsonify({
                "success": True,
                "gold_plundered": 100,
                "remaining_plunders": 3 - current_plunders - 1,
                "victim_name": victim['name']
            })

@app.route('/api/plunder/status', methods=['GET'])
@require_auth
def plunder_status():
    """查看今日掠夺状态"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT plunder_count FROM players WHERE id = %s", (g.player_id,))
            row = cur.fetchone()
            count = row['plunder_count'] if row else 0
            return jsonify({
                "success": True,
                "used_plunders": count,
                "remaining_plunders": max(0, 3 - count),
                "can_plunder": count < 3
            })

# ==================== 邮件礼物 ====================
@app.route('/api/messages/claim', methods=['POST'])
@require_auth
def claim_gift():
    """领取邮件附件（新手礼包、神器等）"""
    data = request.get_json(force=True) or {}
    msg_id = data.get('message_id')
    app.logger.info(f"claim_gift: player_id={g.player_id}, msg_id={msg_id}")
    if not msg_id:
        return jsonify({"success": False, "reason": "缺少message_id"}), 400
    
    with get_db() as conn:
        with get_cursor(conn) as cur:
            app.logger.info(f"Query: msg_id={msg_id}, player_id={g.player_id}")
            cur.execute("""
                SELECT id, attachments, status FROM player_messages
                WHERE id = %s AND receiver_id = %s AND message_type = 'system_gift'
            """, (msg_id, g.player_id))
            msg = cur.fetchone()
            app.logger.info(f"msg result: {msg}")
            if not msg:
                return jsonify({"success": False, "reason": "邮件不存在或已领取"}), 404
            if msg['status'] == 'claimed':
                return jsonify({"success": False, "reason": "已领取过"}), 400
            
            attachments = msg['attachments']
            app.logger.info(f"attachments: {attachments}")
            if not attachments:
                return jsonify({"success": False, "reason": "无附件"}), 400
            
            import json
            items = json.loads(attachments) if isinstance(attachments, str) else attachments
            added_items = []
            claimed_artifacts = []
            
            for att in items:
                att_type = att.get('type', 'item')
                
                if att_type == 'artifact':
                    # 神器：直接添加到玩家神器
                    artifact_db_id = att.get('id')
                    artifact_name = att.get('name', '神器')

                    # 检查是否已拥有（两个表都要检查）
                    cur.execute("SELECT id FROM player_auction_artifacts WHERE player_id = %s AND artifact_db_id = %s", (g.player_id, artifact_db_id))
                    if cur.fetchone():
                        claimed_artifacts.append(f"{artifact_name}(已拥有)")
                        continue

                    # 添加到玩家拍卖行神器记录
                    cur.execute("""
                        INSERT INTO player_auction_artifacts (player_id, artifact_db_id, obtained_at)
                        VALUES (%s, %s, NOW())
                    """, (g.player_id, artifact_db_id))

                    # 同时添加到可上架神器列表（player_artifacts）
                    # 通过 artifact_db_id 找到 artifacts.artifact_key，再找 faction_artifacts.id
                    cur.execute("SELECT artifact_id FROM artifacts WHERE id = %s", (artifact_db_id,))
                    art_row = cur.fetchone()
                    if art_row:
                        fa_key = art_row['artifact_id']  # string key like 'skull_crown'
                        cur.execute("SELECT id FROM faction_artifacts WHERE artifact_key = %s", (fa_key,))
                        fa_row = cur.fetchone()
                        if fa_row:
                            cur.execute("""
                                INSERT INTO player_artifacts (player_id, artifact_id, obtained_at)
                                VALUES (%s, %s, NOW())
                                ON CONFLICT DO NOTHING
                            """, (g.player_id, fa_row['id']))

                    claimed_artifacts.append(artifact_name)
                elif att_type == 'equipment':
                    # 装备：添加到装备仓库
                    equipment_id = att.get('id')
                    equipment_name = att.get('name', '装备')
                    cur.execute("""
                        INSERT INTO equipment_pieces (player_id, equipment_id, acquired_at)
                        VALUES (%s, %s, NOW())
                    """, (g.player_id, equipment_id))
                    added_items.append(equipment_name)
                else:
                    # 普通物品：添加到背包
                    item_id = att.get('item_id')
                    qty = att.get('quantity', 1)
                    cur.execute("""
                        INSERT INTO inventory (player_id, item_id, quantity, is_bound)
                        VALUES (%s, %s, %s, TRUE)
                        ON CONFLICT (player_id, item_id) DO UPDATE SET quantity = inventory.quantity + %s
                    """, (g.player_id, item_id, qty, qty))
                    added_items.append(att.get('name', f'item_{item_id}'))
            
            cur.execute("""
                UPDATE player_messages SET status = 'claimed' WHERE id = %s
            """, (msg_id,))
            conn.commit()
            
            result_msg = []
            if claimed_artifacts:
                result_msg.append(f"神器：{', '.join(claimed_artifacts)}")
            if added_items:
                result_msg.append(f"物品：{', '.join(added_items)}")
            
            return jsonify({
                "success": True,
                "message": f"成功领取：{' '.join(result_msg)}" if result_msg else "领取完成",
                "items": added_items,
                "artifacts": claimed_artifacts
            })

# ==================== PVP ====================
@app.route('/api/players/search', methods=['GET'])
@require_auth
def search_players():
    name = request.args.get('name', '')
    if not name:
        return jsonify({"players": []})
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT id, name, level, power FROM players
                WHERE name LIKE %s AND id != %s LIMIT 10
            """, (f'%{name}%', g.player_id))
            return jsonify({"success": True, "players": [dict(r) for r in cur.fetchall()]})

@app.route('/api/pvp/challenge', methods=['POST'])
@require_auth
def pvp_challenge():
    data = request.get_json(force=True) or {}
    defender_id = data.get('defender_id')
    break_own_shield = data.get('break_shield', False)  # 是否破除自己护盾
    
    if not defender_id:
        return jsonify({"success": False, "reason": "缺少defender_id"}), 400
    
    restore_energy(g.player_id)
    restore_mp(g.player_id)
    player = dict(get_player_full(g.player_id))
    if (player.get('energy') or 0) < 10:
        return jsonify({"success": False, "reason": "体力不足10点，无法挑战"})
    
    shield = get_protection_status(defender_id)
    if shield.get('active'):
        return jsonify({"success": False, "reason": "对方正在保护盾中"})
    
    # 检查攻击者是否有保护盾
    attacker_shield = get_protection_status(g.player_id)
    if attacker_shield.get('active'):
        if attacker_shield.get('is_newbie'):
            # 新手保护盾：强制破除
            deactivate_shield(g.player_id)
            attacker_shield_broken = True
            shield_broken_type = '新手保护'
        elif break_own_shield:
            # 付费护盾：需要确认破除
            deactivate_shield(g.player_id)
            attacker_shield_broken = True
            shield_broken_type = attacker_shield.get('type', '付费保护')
        else:
            attacker_shield_broken = False
            shield_broken_type = None
            return jsonify({
                "success": False, 
                "reason": "你有激活的保护盾，挑战会破除它",
                "shield_active": True,
                "shield_type": attacker_shield.get('type', '保护'),
                "confirm_break": True
            })
    else:
        attacker_shield_broken = False
        shield_broken_type = None
    
    defender = dict(get_player_full(defender_id))
    # Add equipment power
    cur.execute("SELECT weapon, helmet, armor, greaves, amulet, ring FROM player_equipment WHERE player_id = %s", (g.player_id,))
    eq = cur.fetchone()
    equip_power = 0
    if eq:
        for slot in ['weapon', 'helmet', 'armor', 'greaves', 'amulet', 'ring']:
            eid = eq[slot]
            if eid:
                cur.execute("SELECT base_power, enhance_level FROM equipment_catalog ec LEFT JOIN equipment_enhance ee ON ee.player_id = %s AND ee.equipment_id = ec.id WHERE ec.id = %s", (g.player_id, eid))
                erow = cur.fetchone()
                if erow:
                    equip_power += (erow['base_power'] or 0) + (erow['enhance_level'] or 0) * 5
    my_power = (player.get('power') or 0) + equip_power
    opp_power = defender.get('power') or 0
    
    from models import record_challenge
    import random
    my_atk = my_power * random.uniform(0.8, 1.2)
    opp_def = opp_power * random.uniform(0.7, 1.0)
    damage = max(1, int(my_atk - opp_def))
    is_win = my_atk > opp_def
    
    xp_change = 10 if is_win else 5
    
    from models import add_gold, add_xp, add_hp, spend_hp
    if is_win:
        gold_change = max(10, int(opp_power * 0.05))
        add_gold(g.player_id, gold_change)
        add_xp(g.player_id, xp_change)
    else:
        gold_change = 0
        # 失败扣血量，不是扣金贝
        hp_loss = min(damage, player.get('hp', 100))
        spend_hp(g.player_id, hp_loss)
        add_xp(g.player_id, xp_change)
    
    # 扣体力10点
    with get_db() as conn:
        with get_cursor(conn) as cur:
            # 更新永久胜负记录
            if is_win:
                cur.execute("UPDATE players SET energy = GREATEST(0, energy - 10), wins = wins + 1, last_energy_restore = NOW() WHERE id = %s", (g.player_id,))
            else:
                cur.execute("UPDATE players SET energy = GREATEST(0, energy - 10), losses = losses + 1, last_energy_restore = NOW() WHERE id = %s", (g.player_id,))
    
    import uuid
    battle_id = record_challenge(f"pvp_{uuid.uuid4().hex[:12]}", g.player_id, defender_id, 'win' if is_win else 'lose',
        damage_dealt=damage, reward_gold=gold_change, reward_xp=xp_change)
    
    update_task_progress(g.player_id, 'pvp_win' if is_win else 'pvp_lose', 1)
    
    # 更新天梯积分
    with get_db() as conn:
        with get_cursor(conn) as cur:
            if is_win:
                ladder_gain = 25
                cur.execute("UPDATE players SET ladder_points = ladder_points + %s, ladder_wins = ladder_wins + 1 WHERE id = %s", (ladder_gain, g.player_id))
            else:
                ladder_loss = 15
                cur.execute("UPDATE players SET ladder_points = GREATEST(0, ladder_points - %s), ladder_losses = ladder_losses + 1 WHERE id = %s", (ladder_loss, g.player_id))
            
            # 更新段位
            cur.execute("""
                UPDATE players p SET ladder_tier = t.tier_id
                FROM ladder_tiers t
                WHERE p.id = %s AND p.ladder_points >= t.min_points AND p.ladder_points <= t.max_points
            """, (g.player_id,))
            conn.commit()
    
    # 发邮件通知被挑战者（无论胜负都要发送）
    my_name = player.get('name', '神秘掠夺者')
    def_name = defender.get('name', '神秘掠夺者')
    if is_win:
        mail_content = f"⚔️ 【挑战结果】你被 {my_name} 挑战！结果：<b style='color:#ff6b7a'>你败了</b>！<br>对手造成了 {damage} 点伤害，你损失了 {hp_loss} 点血量。"
    else:
        mail_content = f"⚔️ 【挑战结果】你被 {my_name} 挑战！结果：<b style='color:#7bed9f'>你守住了</b>！<br>对手造成了 {damage} 点伤害。"
    send_message(g.player_id, defender_id, mail_content, 'challenge_result')
    
    return jsonify({
        "success": True, "result": 'win' if is_win else 'lose',
        "battle_id": battle_id,
        "gold_change": gold_change, "xp_change": xp_change,
        "damage_dealt": damage,
        "hp_loss": hp_loss if not is_win else 0,
        "shield_broken": attacker_shield_broken,
        "shield_broken_type": shield_broken_type
    })

# ==================== 排行榜 ====================
@app.route('/api/leaderboard/<lb_type>', methods=['GET'])
def leaderboard(lb_type):
    # 尝试从Redis缓存获取
    cache_key = f'leaderboard:{lb_type}'
    cached = cache_get(cache_key)
    if cached:
        return jsonify({"success": True, "type": lb_type, "rankings": cached})
    
    rankings = get_leaderboard(lb_type, 50)
    rankings_list = [dict(r) for r in rankings]
    
    # 缓存1分钟（排行榜更新频繁）
    cache_set(cache_key, rankings_list, 60)
    
    return jsonify({"success": True, "type": lb_type, "rankings": rankings_list})

@app.route('/api/announcements/latest', methods=['GET'])
@require_auth
def announcements_latest():
    """获取最新公告"""
    import redis, json
    try:
        r = redis.Redis(host='172.16.110.113', port=30379, password='gbq2KlOwPeVmQFRv', decode_responses=True)
        data = r.get('global:announcement')
        if data:
            return jsonify({"success": True, "announcement": json.loads(data)})
    except:
        pass
    return jsonify({"success": True, "announcement": None})

@app.route('/api/announcements/broadcast', methods=['POST'])
@require_auth
def announcements_broadcast():
    """发布全局公告（仅管理员）"""
    data = request.get_json()
    msg = data.get('message', '')
    icon = data.get('icon', '📢')
    if not msg:
        return jsonify({"success": False, "reason": "消息不能为空"})
    import redis, json
    try:
        r = redis.Redis(host='172.16.110.113', port=30379, password='gbq2KlOwPeVmQFRv', decode_responses=True)
        announce = {'id': str(time.time()), 'message': msg, 'icon': icon, 'created_at': str(datetime.now())}
        r.setex('global:announcement', 3600, json.dumps(announce))
        return jsonify({"success": True, "message": "公告已发布"})
    except Exception as e:
        return jsonify({"success": False, "reason": str(e)})

@app.route('/api/player/<int:player_id>/info', methods=['GET'])
def player_info(player_id):
    """获取任意玩家详细信息（排行榜点击查看）"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT p.id, p.name, p.level, p.power, p.gold, p.honor_prefix, p.honor_icon, p.honor_color,
                       p.claw as claw_power, p.shell, p.speed as swim_speed, p.wisdom as shrimp_wit,
                       p.luck, p.perception, p.wins, p.losses, p.vip_level,
                       p.energy, p.max_energy, p.hp, p.max_hp, p.mp, p.max_mp,
                       g.name as faction_name
                FROM players p
                LEFT JOIN guild_members gm ON gm.player_id = p.id
                LEFT JOIN guilds g ON g.guild_id::text = gm.guild_id::text
                WHERE p.id = %s
            """, (player_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({"success": False, "reason": "玩家不存在"})
            return jsonify({"success": True, "player": dict(row)})

# ==================== 名誉系统 ====================
@app.route('/api/player/honor_titles', methods=['GET'])
@require_auth
def get_honor_titles():
    """获取所有可用名誉称号"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT id as honor_id, name, icon, prefix, color, tier, description FROM honor_titles ORDER BY tier")
            titles = [dict(r) for r in cur.fetchall()]
            return jsonify({"success": True, "titles": titles})

@app.route('/api/player/honor', methods=['GET'])
@require_auth
def get_player_honor():
    """获取当前玩家名誉称号"""
    player_id = g.player_id
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("SELECT honor_prefix, honor_icon, honor_color FROM players WHERE id = %s", (player_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({"success": False, "reason": "玩家不存在"})
            return jsonify({"success": True, "honor": {
                "prefix": row['honor_prefix'] or '',
                "icon": row['honor_icon'] or '',
                "color": row['honor_color'] or '#ffffff'
            }})

@app.route('/api/player/honor', methods=['POST'])
@require_auth
def set_player_honor():
    """设置玩家名誉称号"""
    player_id = g.player_id
    data = request.get_json()
    honor_id = data.get('honor_id')
    if not honor_id:
        return jsonify({"success": False, "reason": "请选择称号"})
    
    with get_db() as conn:
        with get_cursor(conn) as cur:
            # Get the honor title
            cur.execute("SELECT honor_id, name, icon, prefix, color FROM honor_titles WHERE id = %s", (honor_id,))
            title = cur.fetchone()
            if not title:
                return jsonify({"success": False, "reason": "称号不存在"})
            
            # Update player's honor fields
            cur.execute("""
                UPDATE players 
                SET honor_prefix = %s, honor_icon = %s, honor_color = %s
                WHERE id = %s
            """, (title['prefix'], title['icon'], title['color'], player_id))
            conn.commit()
            
            # Clear leaderboard cache
            cache_delete('leaderboard:power')
            cache_delete('leaderboard:level')
            cache_delete('leaderboard:gold')
            
            return jsonify({
                "success": True, 
                "message": f"名誉称号已设置为 {title['icon']}{title['prefix']}",
                "honor": {
                    "prefix": title['prefix'],
                    "icon": title['icon'],
                    "color": title['color']
                }
            })

# ==================== 天梯榜 ====================
@app.route('/api/leaderboard/ladder', methods=['GET'])
def ladder_ranking():
    """天梯排行榜"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT p.id, p.name, p.level, p.ladder_points, p.ladder_tier, p.ladder_wins, p.ladder_losses,
                       lt.tier_name, lt.tier_icon
                FROM players p
                LEFT JOIN ladder_tiers lt ON p.ladder_tier = lt.tier_id
                WHERE p.ladder_points > 0
                ORDER BY p.ladder_points DESC
                LIMIT 50
            """)
            rankings = [dict(r) for r in cur.fetchall()]
            return jsonify({"success": True, "type": "ladder", "rankings": rankings})

@app.route('/api/player/ladder', methods=['GET'])
@require_auth
def my_ladder():
    """我的天梯信息"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT p.ladder_points, p.ladder_tier, p.ladder_wins, p.ladder_losses,
                       lt.tier_name, lt.tier_icon, lt.min_points, lt.max_points
                FROM players p
                LEFT JOIN ladder_tiers lt ON p.ladder_tier = lt.tier_id
                WHERE p.id = %s
            """, (g.player_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({"success": False})
            return jsonify({
                "success": True,
                "ladder_points": row['ladder_points'],
                "ladder_tier": row['ladder_tier'],
                "tier_name": row['tier_name'],
                "tier_icon": row['tier_icon'],
                "wins": row['ladder_wins'],
                "losses": row['ladder_losses'],
                "progress": row['min_points'],
                "next_tier": row['max_points']
            })

# ==================== 物品数据 ====================
@app.route('/api/items', methods=['GET'])
def items_list():
    """获取所有物品数据（供前端使用）"""
    from items import ITEMS
    items_data = []
    for item_id, item in ITEMS.items():
        items_data.append({
            "id": item_id,
            "name": item.get("name", item_id),
            "icon": item.get("icon", "📦"),
            "type": item.get("type", "misc"),
            "price": item.get("price", 0),
            "description": item.get("description", ""),
            "rarity": item.get("rarity", "common")
        })
    return jsonify({"items": items_data})

# ==================== 神器榜 ====================
@app.route('/api/artifacts/ranking', methods=['GET'])
def artifact_ranking():
    """神器榜 - 查看所有神器归属"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT fa.id, fa.artifact_key, fa.artifact_name, fa.artifact_type,
                       fa.attr_bonus, fa.attr_value, fa.description, fa.rarity,
                       fa.obtained_by, fa.obtained_at,
                       f.name as faction_name, f.faction_id,
                       p.name as owner_name
                FROM faction_artifacts fa
                JOIN factions f ON fa.faction_id = f.faction_id
                LEFT JOIN players p ON fa.obtained_by = p.id
                ORDER BY f.id, fa.artifact_type
            """)
            artifacts = [dict(r) for r in cur.fetchall()]
            
            # Group by faction
            factions = {}
            for a in artifacts:
                fid = a['faction_id']
                if fid not in factions:
                    factions[fid] = {
                        'faction_id': fid,
                        'faction_name': a['faction_name'],
                        'beast': None,
                        'artifact': None
                    }
                if a['artifact_type'] == 'beast':
                    factions[fid]['beast'] = a
                else:
                    factions[fid]['artifact'] = a
            
            return jsonify({
                "success": True,
                "factions": list(factions.values())
            })

@app.route('/api/player/artifacts', methods=['GET'])
@require_auth
def player_artifacts():
    """玩家神器列表"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            # 从两个表获取神器：player_artifacts (faction原生) + player_auction_artifacts (拍卖购买)
            cur.execute("""
                SELECT 
                    fa.artifact_key,
                    fa.artifact_name as name,
                    fa.description,
                    fa.rarity,
                    fa.attr_bonus as main_attribute,
                    fa.attr_value as main_value,
                    fa.artifact_type::text as effect,
                    NULL::text as secondary_attribute,
                    NULL::integer as secondary_value,
                    NULL::text as special_effect,
                    pa.obtained_at,
                    art.icon
                FROM player_artifacts pa
                JOIN faction_artifacts fa ON pa.artifact_id = fa.id
                LEFT JOIN artifacts art ON art.artifact_id = fa.artifact_key
                WHERE pa.player_id = %s
                UNION ALL
                SELECT 
                    a.artifact_id as artifact_key,
                    a.name,
                    a.description,
                    a.rarity,
                    a.main_attribute,
                    a.main_value,
                    a.effect::text,
                    a.secondary_attribute,
                    a.secondary_value,
                    a.special_effect,
                    pa.obtained_at,
                    a.icon
                FROM player_auction_artifacts pa
                JOIN artifacts a ON pa.artifact_db_id = a.id
                WHERE pa.player_id = %s
                ORDER BY obtained_at DESC
            """, (g.player_id, g.player_id))
            artifacts = cur.fetchall()
            return jsonify({
                "success": True,
                "artifacts": [dict(r) for r in artifacts]
            })

@app.route('/api/artifacts/my', methods=['GET'])
@require_auth
def my_artifacts():
    """我的神器"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            # 从两个表获取神器：faction artifacts + auction artifacts
            cur.execute("""
                SELECT 
                    fa.artifact_key,
                    fa.artifact_name as name,
                    fa.description,
                    fa.rarity,
                    fa.attr_bonus as main_attribute,
                    fa.attr_value as main_value,
                    NULL as secondary_attribute,
                    NULL as secondary_value,
                    pa.obtained_at
                FROM player_artifacts pa
                JOIN faction_artifacts fa ON pa.artifact_id = fa.id
                WHERE pa.player_id = %s
                UNION ALL
                SELECT 
                    a.artifact_id as artifact_key,
                    a.name,
                    a.description,
                    a.rarity,
                    a.main_attribute,
                    a.main_value,
                    a.secondary_attribute,
                    a.secondary_value,
                    pa.obtained_at
                FROM player_auction_artifacts pa
                JOIN artifacts a ON pa.artifact_db_id = a.id
                WHERE pa.player_id = %s
                ORDER BY obtained_at DESC
            """, (g.player_id, g.player_id))
            artifacts = cur.fetchall()
            return jsonify({
                "success": True,
                "artifacts": [dict(r) for r in artifacts]
            })

# ==================== 日志 ====================
@app.route('/api/logs', methods=['GET'])
def logs():
    limit = request.args.get('limit', 50, type=int)
    rows = get_player_logs(min(limit, 50))
    return jsonify({"success": True, "logs": [dict(r) for r in rows]})

@app.route('/api/logs/public', methods=['GET'])
def public_logs():
    limit = request.args.get('limit', 50, type=int)
    cache_key = f'logs:public:{limit}'
    cached = cache_get(cache_key)
    if cached:
        return jsonify({"code": 0, "logs": cached})
    rows = get_public_logs(min(limit, 100))
    logs = []
    for r in rows:
        logs.append({
            "player_name": r['player_name'],
            "action": r['action'],
            "detail": r['detail'] or '',
            "created_at": r['created_at'].strftime('%H:%M:%S') if r['created_at'] else ''
        })
    return jsonify({"code": 0, "logs": logs})

# ==================== 错误处理 ====================
@app.errorhandler(Exception)
def handle_exception(e):
    traceback.print_exc()
    return jsonify({"error": str(e)}), 500

# ==================== 启动 ====================
if __name__ == '__main__':
    print("Starting Deep Sea Odyssey server on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
