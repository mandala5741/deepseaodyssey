#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""玩家类"""

import json
import os
import random
from datetime import datetime

class Player:
    def __init__(self, name):
        self.name = name
        self.game = None
        
    def create(self):
        """创建新角色"""
        self.level = 1
        self.xp = 0
        self.gold = 500
        self.potential = 100
        
        # 四维属性
        self.base_stats = {
            "claw": random.randint(8, 12),    # 钳力 - 攻击
            "shell": random.randint(8, 12),   # 甲壳 - 防御
            "speed": random.randint(8, 12),    # 游速 - 速度/暴击
            "wisdom": random.randint(8, 12)   # 虾慧 - MP/技能
        }
        
        # 战斗加成（装备/永久道具）
        self.bonus_stats = {
            "claw": 0,
            "shell": 0,
            "speed": 0,
            "wisdom": 0
        }
        
        # 门派
        self.faction = None
        self.faction_skills = []
        
        # 技能
        self.skills = ["shrimp_punch"]  # 初始技能
        
        # 背包
        self.inventory = {}
        
        # 体力系统
        self.energy = 100
        self.max_energy = 100
        
        # HP/MP
        self.hp = self.max_hp
        self.mp = self.max_mp
        
        # 战斗统计
        self.wins = 0
        self.losses = 0
        
        # 冷却
        self.patrol_cooldown = 0
        self.chore_cooldown = 0
        self.rest_cooldown = 0
        
        # 创建时间
        self.created_at = datetime.now().isoformat()
        self.last_save = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 设置游戏引用
        from game import Game
        self.game = None  # 稍后设置
    
    @property
    def claw(self):
        return self.base_stats["claw"] + self.bonus_stats["claw"]
    
    @property
    def shell(self):
        return self.base_stats["shell"] + self.bonus_stats["shell"]
    
    @property
    def speed(self):
        return self.base_stats["speed"] + self.bonus_stats["speed"]
    
    @property
    def wisdom(self):
        return self.base_stats["wisdom"] + self.bonus_stats["wisdom"]
    
    @property
    def max_hp(self):
        return 100 + self.shell * 8
    
    @property
    def max_mp(self):
        return 50 + self.wisdom * 5
    
    @property
    def power(self):
        """战力计算"""
        return int((self.claw * 2 + self.shell * 2 + self.speed * 1.5 + self.wisdom * 1) * (1 + self.level * 0.1))
    
    @property
    def xp_to_level(self):
        return self.level * 100
    
    def show_stats(self):
        """显示状态"""
        print(f"""
╔══════════════════════════════════════╗
║  🦐 {self.name} - Lv.{self.level}                    ║
╠══════════════════════════════════════╣
║  钳力: {self.claw:<5}  甲壳: {self.shell:<5}          ║
║  游速: {self.speed:<5}  虾慧: {self.wisdom:<5}          ║
╠══════════════════════════════════════╣
║  HP:  {self.hp}/{self.max_hp:<5}  MP:  {self.mp}/{self.max_mp:<5}         ║
║  体力: {self.energy}/{self.max_energy:<5}                    ║
╠══════════════════════════════════════╣
║  经验: {self.xp}/{self.xp_to_level:<5}  潜能: {self.potential:<5}       ║
║  金贝: {self.gold:<8}               ║
║  战力: {self.power:<5}                     ║
╠══════════════════════════════════════╣
║  门派: {self.faction or '无'}                    ║
║  技能: {', '.join(self.skills) or '无'}  ║
║  胜/负: {self.wins}/{self.losses}                           ║
╚══════════════════════════════════════╝""")
    
    def add_xp(self, amount):
        """增加经验"""
        self.xp += amount
        while self.xp >= self.xp_to_level:
            self.xp -= self.xp_to_level
            self.level_up()
    
    def level_up(self):
        """升级"""
        self.level += 1
        self.base_stats["claw"] += 1
        self.base_stats["shell"] += 1
        self.base_stats["speed"] += 1
        self.base_stats["wisdom"] += 1
        self.hp = self.max_hp
        self.mp = self.max_mp
        print(f"\n🎉 升级了！现在是 Lv.{self.level}！")
        print(f"   四维属性各+1！")
    
    def add_gold(self, amount):
        """增加金贝"""
        self.gold += amount
        print(f"💰 获得 {amount} 金贝！")
    
    def spend_gold(self, amount):
        """花费金贝"""
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False
    
    def add_item(self, item_id, quantity=1):
        """添加物品到背包"""
        if item_id in self.inventory:
            self.inventory[item_id]["quantity"] += quantity
        else:
            self.inventory[item_id] = {"quantity": quantity}
    
    def remove_item(self, item_id, quantity=1):
        """从背包移除物品"""
        if item_id in self.inventory:
            self.inventory[item_id]["quantity"] -= quantity
            if self.inventory[item_id]["quantity"] <= 0:
                del self.inventory[item_id]
            return True
        return False
    
    def has_item(self, item_id):
        """检查是否有物品"""
        return item_id in self.inventory and self.inventory[item_id]["quantity"] > 0
    
    def show_inventory(self):
        """显示背包"""
        print(f"\n🎒 背包 (金贝: {self.gold})")
        print("-" * 40)
        if not self.inventory:
            print("背包是空的")
            return
        
        from items import ITEMS
        for item_id, data in self.inventory.items():
            item = ITEMS.get(item_id, {})
            name = item.get("name", item_id)
            qty = data["quantity"]
            print(f"  • {name} x{qty}")
        
        print(f"\n背包: {len(self.inventory)}/{20}")
    
    def use_item(self, item_name):
        """使用物品"""
        from items import ITEMS
        
        # 查找物品
        item_id = None
        for iid, item in ITEMS.items():
            if item_name in item["name"] or item_name == iid:
                item_id = iid
                break
        
        if not item_id or not self.has_item(item_id):
            print("背包里没有这个物品")
            return
        
        item = ITEMS[item_id]
        effects = item.get("effect", {})
        
        # 应用效果
        if "hp" in effects:
            old_hp = self.hp
            self.hp = min(self.max_hp, self.hp + effects["hp"])
            print(f"❤️ HP恢复 {self.hp - old_hp} 点 ({old_hp} -> {self.hp})")
        
        if "mp" in effects:
            old_mp = self.mp
            self.mp = min(self.max_mp, self.mp + effects["mp"])
            print(f"💧 MP恢复 {self.mp - old_mp} 点 ({old_mp} -> {self.mp})")
        
        if "energy" in effects:
            self.energy = min(self.max_energy, self.energy + effects["energy"])
            print(f"⚡ 体力恢复 {effects['energy']} 点 (当前: {self.energy})")
        
        if "permanent" in effects:
            stat = effects["permanent"]
            self.bonus_stats[stat["attr"]] += stat["value"]
            print(f"✨ 永久 {stat['attr']} +{stat['value']}！")
        
        self.remove_item(item_id)
    
    def show_skills(self):
        """显示技能"""
        print(f"\n⚔️ 已学技能:")
        print("-" * 40)
        from skills import SKILLS
        for skill_id in self.skills:
            skill = SKILLS.get(skill_id, {})
            print(f"  • {skill.get('name', skill_id)}")
            print(f"    {skill.get('description', '')}")
    
    def learn_skill(self, skill_name):
        """学习技能"""
        from skills import SKILLS
        
        for skill_id, skill in SKILLS.items():
            if skill_name in skill["name"] or skill_name == skill_id:
                if skill_id in self.skills:
                    print("你已经学会这个技能了")
                    return
                if skill.get("faction") and skill["faction"] != self.faction:
                    print("你需要加入对应门派才能学习")
                    return
                
                cost = skill.get("potential_cost", 100)
                if self.potential >= cost:
                    self.potential -= cost
                    self.skills.append(skill_id)
                    print(f"✅ 学会了 {skill['name']}！")
                else:
                    print(f"潜能不足！需要 {cost} 潜能，当前: {self.potential}")
                return
        
        print("没有找到这个技能")
    
    def rest(self):
        """休息"""
        if self.rest_cooldown > 0:
            print(f"休息冷却中，还需要{self.rest_cooldown}次操作")
            return
        
        self.hp = self.max_hp
        self.mp = self.max_mp
        self.energy = min(self.max_energy, self.energy + 50)
        self.rest_cooldown = 5
        print("🏠 休息成功！HP/MP恢复满，体力+50")
    
    def meditate(self):
        """冥想"""
        if self.energy < 20:
            print("体力不足！需要20体力")
            return
        
        self.energy -= 20
        self.hp = self.max_hp
        self.mp = self.max_mp
        self.add_xp(10)
        print("🧘 冥想成功！HP/MP恢复满，获得10经验")
    
    def consume_energy(self, amount):
        """消耗体力"""
        if self.energy >= amount:
            self.energy -= amount
            return True
        print(f"体力不足！需要 {amount} 体力，当前: {self.energy}")
        return False
    
    def tick_cooldowns(self):
        """减少冷却"""
        if self.patrol_cooldown > 0:
            self.patrol_cooldown -= 1
        if self.chore_cooldown > 0:
            self.chore_cooldown -= 1
        if self.rest_cooldown > 0:
            self.rest_cooldown -= 1
    
    def save(self):
        """保存游戏"""
        save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "存档")
        os.makedirs(save_dir, exist_ok=True)
        
        data = {
            "name": self.name,
            "level": self.level,
            "xp": self.xp,
            "gold": self.gold,
            "potential": self.potential,
            "base_stats": self.base_stats,
            "bonus_stats": self.bonus_stats,
            "faction": self.faction,
            "skills": self.skills,
            "inventory": self.inventory,
            "energy": self.energy,
            "hp": self.hp,
            "mp": self.mp,
            "wins": self.wins,
            "losses": self.losses,
            "patrol_cooldown": self.patrol_cooldown,
            "chore_cooldown": self.chore_cooldown,
            "rest_cooldown": self.rest_cooldown,
            "created_at": self.created_at,
            "last_save": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        filename = os.path.join(save_dir, f"{self.name}_{self.level}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, filepath):
        """加载游戏"""
        with open(filepath, encoding='utf-8') as f:
            data = json.load(f)
        
        player = cls(data["name"])
        player.level = data["level"]
        player.xp = data["xp"]
        player.gold = data["gold"]
        player.potential = data["potential"]
        player.base_stats = data["base_stats"]
        player.bonus_stats = data["bonus_stats"]
        player.faction = data.get("faction")
        player.skills = data["skills"]
        player.inventory = data["inventory"]
        player.energy = data["energy"]
        player.hp = data["hp"]
        player.mp = data["mp"]
        player.wins = data["wins"]
        player.losses = data["losses"]
        player.patrol_cooldown = data.get("patrol_cooldown", 0)
        player.chore_cooldown = data.get("chore_cooldown", 0)
        player.rest_cooldown = data.get("rest_cooldown", 0)
        player.created_at = data.get("created_at", "")
        player.last_save = data.get("last_save", "")
        
        return player
