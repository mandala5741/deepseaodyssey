#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""战斗系统"""

import random

class Combat:
    def __init__(self, game):
        self.game = game
    
    def start_battle(self):
        """开始战斗"""
        player = self.game.player
        
        if player.energy < 30:
            print("体力不足！需要30体力进行战斗")
            return
        
        player.energy -= 30
        
        # 生成敌人
        enemy = self.generate_enemy(player.level)
        
        print(f"\n⚔️ 战斗开始！")
        print(f"你遇到了 {enemy['name']}！")
        print(f"敌人等级: Lv.{enemy['level']} | 战力: {enemy['power']}")
        print()
        
        # 战斗循环
        while enemy["hp"] > 0 and player.hp > 0:
            print(f"你的HP: {player.hp}/{player.max_hp} | 敌人HP: {enemy['hp']}/{enemy['max_hp']}")
            print("1. 普通攻击  2. 使用技能  3. 使用物品  4. 逃跑")
            
            choice = input("> ").strip()
            
            if choice == "1":
                self.player_attack(player, enemy)
            elif choice == "2":
                self.player_skill(player, enemy)
            elif choice == "3":
                self.use_item_in_combat(player)
            elif choice == "4":
                if random.random() < 0.5:
                    print("逃跑成功！")
                    return
                else:
                    print("逃跑失败！")
            else:
                print("无效选择")
            
            # 敌人回合
            if enemy["hp"] > 0:
                self.enemy_attack(enemy, player)
        
        # 战斗结束
        if player.hp <= 0:
            self.handle_defeat(player, enemy)
        else:
            self.handle_victory(player, enemy)
    
    def generate_enemy(self, player_level):
        """生成敌人"""
        level_range = max(1, player_level - 3)
        level = random.randint(level_range, player_level + 3)
        
        names = ["野生龙虾", "海沟蟹", "剧毒水母", "深海章鱼", "鲨鱼"]
        name = random.choice(names)
        
        # 基础属性
        claw = random.randint(5, 10) + level
        shell = random.randint(5, 10) + level
        speed = random.randint(5, 10) + level
        wisdom = random.randint(5, 10) + level
        
        power = int((claw * 2 + shell * 2 + speed * 1.5 + wisdom * 1) * (1 + level * 0.1))
        
        return {
            "name": name,
            "level": level,
            "claw": claw,
            "shell": shell,
            "speed": speed,
            "wisdom": wisdom,
            "hp": 100 + shell * 8,
            "max_hp": 100 + shell * 8,
            "power": power
        }
    
    def player_attack(self, player, enemy):
        """玩家攻击"""
        damage = int(player.claw * 1.0)
        is_crit = random.random() < (player.speed / 100)
        if is_crit:
            damage = int(damage * 1.5)
        
        enemy["hp"] = max(0, enemy["hp"] - damage)
        
        if is_crit:
            print(f"💥 暴击！你对 {enemy['name']} 造成了 {damage} 点伤害！")
        else:
            print(f"🦐 你对 {enemy['name']} 造成了 {damage} 点伤害！")
    
    def player_skill(self, player, enemy):
        """玩家使用技能"""
        from skills import SKILLS
        
        print("\n选择技能:")
        for i, skill_id in enumerate(player.skills, 1):
            skill = SKILLS.get(skill_id, {})
            print(f"{i}. {skill.get('name', skill_id)} (MP: {skill.get('mp_cost', 0)})")
        
        choice = input("> ").strip()
        try:
            idx = int(choice) - 1
            skill_id = player.skills[idx]
            skill = SKILLS.get(skill_id, {})
            
            mp_cost = skill.get("mp_cost", 0)
            if player.mp < mp_cost:
                print(f"MP不足！需要 {mp_cost} MP")
                return
            
            player.mp -= mp_cost
            
            if skill["type"] == "attack":
                damage = int(eval(skill.get("damage_formula", "player.claw")))
                if skill.get("always_crit"):
                    damage = int(damage * 1.5)
                    print(f"💥 暴击！")
                
                enemy["hp"] = max(0, enemy["hp"] - damage)
                print(f"⚔️ 你使用 {skill['name']} 对 {enemy['name']} 造成了 {damage} 点伤害！")
            
            elif skill["type"] == "defense":
                defense = skill.get("defense_bonus", 0)
                player.defense_buff = defense
                print(f"🛡️ 你使用 {skill['name']}，防御力提升 {defense*100}%！")
        
        except:
            print("无效选择")
    
    def enemy_attack(self, enemy, player):
        """敌人攻击"""
        damage = int(enemy["claw"] * 1.0)
        
        # 检查玩家防御
        defense = getattr(player, 'defense_buff', 0)
        if defense > 0:
            damage = int(damage * (1 - defense))
            player.defense_buff = 0
        
        player.hp = max(0, player.hp - damage)
        print(f"👾 {enemy['name']} 对你造成了 {damage} 点伤害！")
    
    def use_item_in_combat(self, player):
        """战斗中使用物品"""
        if not player.inventory:
            print("背包是空的")
            return
        
        from items import ITEMS
        print("\n选择物品:")
        for i, (item_id, data) in enumerate(player.inventory.items(), 1):
            item = ITEMS.get(item_id, {})
            print(f"{i}. {item.get('name', item_id)} x{data['quantity']}")
        
        choice = input("> ").strip()
        try:
            idx = int(choice) - 1
            item_id = list(player.inventory.keys())[idx]
            player.use_item(item_id)
        except:
            print("无效选择")
    
    def handle_victory(self, player, enemy):
        """胜利处理"""
        xp_reward = enemy["level"] * 20
        gold_reward = enemy["level"] * 10
        potential_reward = enemy["level"] * 5
        
        player.add_xp(xp_reward)
        player.add_gold(gold_reward)
        player.potential += potential_reward
        player.wins += 1
        
        print(f"""
🏆 战斗胜利！
   获得:
   • 经验 +{xp_reward}
   • 金贝 +{gold_reward}
   • 潜能 +{potential_reward}
""")
    
    def handle_defeat(self, player, enemy):
        """失败处理"""
        gold_loss = min(player.gold, 50)
        player.gold -= gold_loss
        player.losses += 1
        
        print(f"""
💀 战斗失败...
   损失: {gold_loss} 金贝
   可以在休息后重新挑战！
""")
