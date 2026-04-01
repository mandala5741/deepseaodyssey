#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""市集系统 - 玩家之间交易物品和神器"""

import uuid
from models import get_db, get_cursor

def get_market_listings(item_type=None, rarity=None, limit=50):
    """获取市集上架列表"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            sql = """
                SELECT ml.listing_id, ml.id, ml.seller_id, ml.item_type, ml.item_key, ml.item_name,
                       ml.item_icon, ml.quantity, ml.price, ml.rarity, ml.created_at,
                       CASE WHEN ml.seller_id IS NULL THEN '系统' ELSE p.name END as seller_name,
                       CASE WHEN ml.seller_id IS NULL THEN 0 ELSE p.level END as seller_level
                FROM market_listings ml
                LEFT JOIN players p ON ml.seller_id = p.id
                WHERE ml.status = 'active'
            """
            params = []
            if item_type:
                sql += " AND ml.item_type = %s"
                params.append(item_type)
            if rarity:
                sql += " AND ml.rarity = %s"
                params.append(rarity)
            sql += " ORDER BY ml.created_at DESC LIMIT %s"
            params.append(limit)
            cur.execute(sql, params)
            return cur.fetchall()

def get_my_listings(player_id):
    """获取我的上架列表"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT listing_id, id, item_type, item_key, item_name, item_icon, quantity, price, rarity, created_at, status
                FROM market_listings
                WHERE seller_id = %s
                ORDER BY created_at DESC
            """, (player_id,))
            return cur.fetchall()

def list_item_for_sale(player_id, item_type, item_key, quantity, price, item_name, item_icon, rarity=None):
    """上架物品"""
    if price < 1:
        return {"success": False, "reason": "价格不能低于1金贝"}

    with get_db() as conn:
        with get_cursor(conn) as cur:
            if item_type == 'item':
                # 从背包扣除物品
                cur.execute("""
                    SELECT id, quantity FROM inventory
                    WHERE player_id = %s AND item_id = %s AND quantity >= %s
                    FOR UPDATE
                """, (player_id, item_key, quantity))
                row = cur.fetchone()
                if not row:
                    return {"success": False, "reason": "背包物品不足"}
                
                slot_id = row['id']
                cur.execute("""
                    UPDATE inventory SET quantity = quantity - %s
                    WHERE id = %s
                """, (quantity, slot_id))
                # 如果数量归零则删除记录
                cur.execute("DELETE FROM inventory WHERE id = %s AND quantity <= 0", (slot_id,))

            elif item_type == 'artifact':
                # 检查玩家是否拥有这个神器（可能在 player_artifacts 或 player_auction_artifacts）
                found_in_pa = False
                found_in_auction = False
                pa_record_id = None
                auction_record_id = None

                # 方式1：从 faction_artifacts 查找（player_artifacts 表）
                cur.execute("SELECT id FROM faction_artifacts WHERE artifact_key = %s", (item_key,))
                fa_row = cur.fetchone()
                if fa_row:
                    cur.execute("""
                        SELECT id FROM player_artifacts
                        WHERE player_id = %s AND artifact_id = %s
                    """, (player_id, fa_row['id']))
                    pa_row = cur.fetchone()
                    if pa_row:
                        found_in_pa = True
                        pa_record_id = pa_row['id']

                # 方式2：从 artifacts 表查找（player_auction_artifacts 表）
                if not found_in_pa:
                    cur.execute("SELECT id FROM artifacts WHERE artifact_id = %s", (item_key,))
                    art_row = cur.fetchone()
                    if art_row:
                        cur.execute("""
                            SELECT id FROM player_auction_artifacts
                            WHERE player_id = %s AND artifact_db_id = %s
                        """, (player_id, art_row['id']))
                        auction_row = cur.fetchone()
                        if auction_row:
                            found_in_auction = True
                            auction_record_id = auction_row['id']

                if not found_in_pa and not found_in_auction:
                    return {"success": False, "reason": "你没有这个神器"}

                # 从相应表中删除
                if found_in_pa:
                    cur.execute("DELETE FROM player_artifacts WHERE id = %s", (pa_record_id,))
                elif found_in_auction:
                    cur.execute("DELETE FROM player_auction_artifacts WHERE id = %s", (auction_record_id,))

            elif item_type == 'equipment':
                # 检查玩家是否拥有这件装备
                cur.execute("""
                    SELECT id FROM equipment_pieces
                    WHERE player_id = %s AND equipment_id = %s
                """, (player_id, int(item_key)))
                row = cur.fetchone()
                if not row:
                    return {"success": False, "reason": "你没有这件装备"}

                # 从背包装备中删除
                cur.execute("DELETE FROM equipment_pieces WHERE player_id = %s AND equipment_id = %s",
                          (player_id, int(item_key)))

            # 创建上架记录
            listing_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO market_listings
                (listing_id, seller_id, item_type, item_key, item_name, item_icon, quantity, price, rarity, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'active', NOW())
            """, (listing_id, player_id, item_type, item_key, item_name, item_icon, quantity, price, rarity))

            return {"success": True, "listing_id": listing_id, "message": f"成功上架 {item_name} x{quantity}"}

def buy_from_market(player_id, listing_id):
    """从市集购买物品"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            # 获取上架记录
            cur.execute("""
                SELECT id, seller_id, item_type, item_key, item_name, item_icon, quantity, price, rarity
                FROM market_listings
                WHERE listing_id = %s AND status = 'active'
                FOR UPDATE
            """, (listing_id,))
            listing = cur.fetchone()
            if not listing:
                return {"success": False, "reason": "该商品不存在或已下架"}

            if listing['seller_id'] == player_id:
                return {"success": False, "reason": "不能购买自己上架的物品"}

            # 扣除购买者金贝
            cur.execute("SELECT gold FROM players WHERE id = %s FOR UPDATE", (player_id,))
            buyer = cur.fetchone()
            if not buyer or buyer['gold'] < listing['price']:
                return {"success": False, "reason": "金贝不足"}

            cur.execute("UPDATE players SET gold = gold - %s WHERE id = %s", (listing['price'], player_id))

            # 系统上架不需要给卖家转金贝
            fee = 0
            if listing['seller_id'] is not None:
                # 玩家上架：95%金贝通过邮件发给卖家（扣除5%手续费）
                fee = int(listing['price'] * 0.05)
                seller_gold = listing['price'] - fee
                msg_id_seller = str(uuid.uuid4())
                import json as json_mod
                cur.execute("""
                    INSERT INTO player_messages (message_id, sender_id, receiver_id, message_type, content, status, attachments, created_at)
                    VALUES (%s, NULL, %s, 'market_sale', %s, 'unclaimed', %s, NOW())
                """, (
                    msg_id_seller,
                    listing['seller_id'],
                    f"🏧 市集售出：{listing['item_name']} x{listing['quantity']}\n💰 售价 {listing['price']} 金贝\n✅ 到账 {seller_gold} 金贝（已扣除5%手续费）",
                    json_mod.dumps([{'type': 'gold', 'quantity': seller_gold}])
                ))

            # 标记为已售
            cur.execute("""
                UPDATE market_listings SET status = 'sold' WHERE listing_id = %s
            """, (listing_id,))

            # 发货到买家邮件
            attachments = [{
                "type": listing['item_type'],
                "id": listing['item_key'],
                "name": listing['item_name'],
                "icon": listing['item_icon'],
                "quantity": listing['quantity']
            }]
            if listing['item_type'] == 'artifact':
                attachments[0]['rarity'] = listing['rarity']

            seller_note = "（系统物品，无手续费）" if listing['seller_id'] == 0 else f"（手续费5%）"
            msg_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO player_messages (message_id, sender_id, receiver_id, message_type, content, status, attachments, created_at)
                VALUES (%s, NULL, %s, 'market_purchase', %s, 'unclaimed', %s, NOW())
            """, (
                msg_id,
                player_id,
                f"🎁 市集购买：{listing['item_name']} x{listing['quantity']}\n💰 花费 {listing['price']} 金贝 {seller_note}\n请提取附件",
                __import__('json').dumps(attachments)
            ))

            return {
                "success": True,
                "message": f"购买成功！{listing['item_name']} x{listing['quantity']} 已发送到邮件",
                "cost": listing['price'],
                "fee": fee
            }

def cancel_listing(player_id, listing_id):
    """取消上架"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT id, item_type, item_key, item_name, item_icon, quantity, rarity
                FROM market_listings
                WHERE listing_id = %s AND seller_id = %s AND status = 'active'
                FOR UPDATE
            """, (listing_id, player_id))
            listing = cur.fetchone()
            if not listing:
                return {"success": False, "reason": "上架记录不存在或无法取消"}

            # 归还物品给玩家
            if listing['item_type'] == 'item':
                cur.execute("""
                    INSERT INTO inventory (player_id, item_id, quantity, is_bound)
                    VALUES (%s, %s, %s, FALSE)
                    ON CONFLICT (player_id, item_id) DO UPDATE SET quantity = inventory.quantity + %s
                """, (player_id, listing['item_key'], listing['quantity'], listing['quantity']))
            elif listing['item_type'] == 'artifact':
                # 尝试添加到 player_artifacts (via faction_artifacts)
                cur.execute("SELECT id FROM faction_artifacts WHERE artifact_key = %s", (listing['item_key'],))
                fa_row = cur.fetchone()
                if fa_row:
                    cur.execute("""
                        INSERT INTO player_artifacts (player_id, artifact_id, obtained_at)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT DO NOTHING
                    """, (player_id, fa_row['id']))
                # 同时尝试添加到 player_auction_artifacts (via artifacts)
                cur.execute("SELECT id FROM artifacts WHERE artifact_id = %s", (listing['item_key'],))
                art_row = cur.fetchone()
                if art_row:
                    cur.execute("""
                        INSERT INTO player_auction_artifacts (player_id, artifact_db_id, obtained_at)
                        VALUES (%s, %s, NOW())
                        ON CONFLICT DO NOTHING
                    """, (player_id, art_row['id']))

            # 标记为已取消
            cur.execute("UPDATE market_listings SET status = 'cancelled' WHERE listing_id = %s", (listing_id,))

            return {"success": True, "message": f"已取消上架 {listing['item_name']}"}

def delete_listing_record(player_id, listing_id):
    """删除已结束的上架记录（只能删除自己的、非active的）"""
    with get_db() as conn:
        with get_cursor(conn) as cur:
            cur.execute("""
                SELECT id, status, item_name FROM market_listings
                WHERE listing_id = %s AND seller_id = %s AND status != 'active'
                FOR UPDATE
            """, (listing_id, player_id))
            row = cur.fetchone()
            if not row:
                return {"success": False, "reason": "记录不存在或无法删除"}
            cur.execute("DELETE FROM market_listings WHERE listing_id = %s", (listing_id,))
            return {"success": True, "message": f"已删除记录：{row['item_name']}"}
