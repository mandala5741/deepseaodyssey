#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""商店系统"""

from items import ITEMS

class Shop:
    def __init__(self, game):
        self.game = game
    
    def open_shop(self):
        """打开商店"""
        player = self.game.player
        
        print(f"""
🏪 深海商店
═══════════════════════════════════════
你的金贝: {player.gold}
═══════════════════════════════════════""")
        
        categories = {
            "恢复类": ["seaweed_pill", "pearl_dew", "deep_sea_herb", "coral_essence", 
                      "energy_potion", "shrimp_elixir", "abyss_vigor"],
            "战斗增益": ["power_shell", "iron_scales", "swift_current"],
            "永久增益": ["claw_stone", "shell_crystal", "speed_gill", "wisdom_orb"],
            "特殊道具": ["exp_boost", "peace_token"]
        }
        
        for cat, items in categories.items():
            print(f"\n【{cat}】")
            for item_id in items:
                item = ITEMS.get(item_id, {})
                print(f"  {item.get('name', item_id)} - {item.get('price', 0)}金贝")
                print(f"    {item.get('description', '')}")
        
        print("\n输入物品名称购买，输入'q'退出")
        
        while True:
            choice = input("\n> ").strip()
            if choice.lower() == 'q':
                break
            
            # 查找物品
            for item_id, item in ITEMS.items():
                if choice in item["name"] or choice == item_id:
                    self.buy_item(item_id, item)
                    break
            else:
                print("没有找到这个物品")
    
    def buy_item(self, item_id, item):
        """购买物品"""
        player = self.game.player
        price = item.get("price", 0)
        
        if player.gold < price:
            print(f"金贝不足！需要 {price} 金贝，你只有 {player.gold} 金贝")
            return
        
        # 检查限购
        if item.get("max_stack"):
            owned = player.inventory.get(item_id, {}).get("quantity", 0)
            if owned >= item["max_stack"]:
                print(f"这个物品已经达到购买上限了！")
                return
        
        player.gold -= price
        player.add_item(item_id, 1)
        
        print(f"✅ 购买了 {item['name']}！")
        
        # 永久道具立即生效
        if item.get("type") == "permanent":
            player.use_item(item_id)
