#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""任务系统"""

import random

class QuestSystem:
    def __init__(self, game):
        self.game = game
    
    def do_patrol(self):
        """巡逻任务"""
        player = self.game.player
        
        if player.patrol_cooldown > 0:
            print(f"巡逻冷却中，还需要{player.patrol_cooldown}次操作")
            return
        
        if player.energy < 20:
            print(f"体力不足！需要20体力，当前: {player.energy}")
            return
        
        player.energy -= 20
        player.patrol_cooldown = 3
        
        # 随机事件
        event = random.choice([
            "发现宝藏", "遇到海盗", "遭遇海怪", "平静无事"
        ])
        
        print(f"\n🗺️ 巡逻中... {event}")
        
        if event == "发现宝藏":
            gold = random.randint(100, 300)
            player.add_gold(gold)
            xp = random.randint(20, 40)
            player.add_xp(xp)
            print(f"💰 发现宝藏！获得 {gold} 金贝和 {xp} 经验！")
        
        elif event == "遇到海盗":
            # 触发战斗
            print("⚔️ 遇到海盗！")
            from combat import Combat
            combat = Combat(self.game)
            enemy = combat.generate_enemy(player.level)
            print(f"你遇到了 {enemy['name']}！")
            
            # 快速战斗
            while enemy["hp"] > 0 and player.hp > 0:
                damage = int(player.claw * 1.2)
                enemy["hp"] -= damage
                print(f"🦐 你对 {enemy['name']} 造成 {damage} 伤害！")
                
                if enemy["hp"] <= 0:
                    break
                
                enemy_damage = int(enemy["claw"] * 0.8)
                player.hp -= enemy_damage
                print(f"👾 {enemy['name']} 对你造成 {enemy_damage} 伤害！")
            
            if player.hp > 0:
                xp = enemy["level"] * 30
                gold = enemy["level"] * 20
                player.add_xp(xp)
                player.add_gold(gold)
                player.wins += 1
                print(f"🏆 战胜海盗！获得 {xp} 经验，{gold} 金贝！")
            else:
                gold_loss = min(player.gold, 30)
                player.gold -= gold_loss
                player.losses += 1
                player.hp = player.max_hp // 2
                print(f"💀 战败，损失 {gold_loss} 金贝")
        
        elif event == "遭遇海怪":
            print("⚔️ 遭遇海怪！")
            from combat import Combat
            combat = Combat(self.game)
            enemy = combat.generate_enemy(player.level + 2)
            print(f"你遇到了 {enemy['name']}！")
            
            # 快速战斗
            while enemy["hp"] > 0 and player.hp > 0:
                damage = int(player.claw * 1.5)
                enemy["hp"] -= damage
                print(f"🦐 你对 {enemy['name']} 造成 {damage} 伤害！")
                
                if enemy["hp"] <= 0:
                    break
                
                enemy_damage = int(enemy["claw"] * 1.2)
                player.hp -= enemy_damage
                print(f"👾 {enemy['name']} 对你造成 {enemy_damage} 伤害！")
            
            if player.hp > 0:
                xp = enemy["level"] * 50
                gold = enemy["level"] * 30
                player.add_xp(xp)
                player.add_gold(gold)
                player.wins += 1
                print(f"🏆 战胜海怪！获得 {xp} 经验，{gold} 金贝！")
            else:
                gold_loss = min(player.gold, 50)
                player.gold -= gold_loss
                player.losses += 1
                player.hp = player.max_hp // 2
                print(f"💀 战败，损失 {gold_loss} 金贝")
        
        else:
            xp = 20
            gold = 50
            player.add_xp(xp)
            player.add_gold(gold)
            print(f"🌊 平安无事！获得 {xp} 经验，{gold} 金贝")
        
        player.tick_cooldowns()
    
    def do_chore(self):
        """义工任务"""
        player = self.game.player
        
        if player.chore_cooldown > 0:
            print(f"义工冷却中，还需要{player.chore_cooldown}次操作")
            return
        
        if player.energy < 10:
            print(f"体力不足！需要10体力，当前: {player.energy}")
            return
        
        player.energy -= 10
        player.chore_cooldown = 2
        
        xp = 20
        gold = 50
        potential = 10
        
        player.add_xp(xp)
        player.add_gold(gold)
        player.potential += potential
        
        print(f"""
🤝 义工完成！帮助了海沟里的居民
   获得:
   • 经验 +{xp}
   • 金贝 +{gold}
   • 潜能 +{potential}
   • 道德 +2
""")
        
        player.tick_cooldowns()
