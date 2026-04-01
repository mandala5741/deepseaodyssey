#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""门派系统"""

FACTIONS = {
    "iron_claw": {
        "name": "铁钳派",
        "leader": "铁钳大师",
        "requirement": {"attr": "claw", "min": 8},
        "bonus": "暴击伤害 +20%",
        "description": "以力量著称，钳出如雷，刚猛无匹"
    },
    "mystic_shell": {
        "name": "玄甲派",
        "leader": "玄甲老祖",
        "requirement": {"attr": "shell", "min": 8},
        "bonus": "伤害减免 +15%",
        "description": "以防御见长，甲壳坚不可摧"
    },
    "phantom": {
        "name": "幻影派",
        "leader": "幻影真人",
        "requirement": {"attr": "speed", "min": 8},
        "bonus": "闪避率 +15%",
        "description": "身法诡异，来去如风，幻影无踪"
    },
    "wisdom_school": {
        "name": "智谋派",
        "leader": "虾圣",
        "requirement": {"attr": "wisdom", "min": 8},
        "bonus": "技能效果 +20%",
        "description": "以智取胜，运筹帷幄，决胜千里"
    }
}

class FactionSystem:
    def __init__(self, game):
        self.game = game
    
    def choose_faction(self):
        """选择门派"""
        player = self.game.player
        
        print("""
🏯 请选择加入的门派:
""")
        
        for fid, faction in FACTIONS.items():
            req = faction["requirement"]
            meets = player.base_stats.get(req["attr"], 0) >= req["min"]
            status = "✓" if meets else "✗"
            
            print(f"{status} {faction['name']}")
            print(f"  掌门: {faction['leader']}")
            print(f"  要求: {req['attr']} >= {req['min']}")
            print(f"  效果: {faction['bonus']}")
            print(f"  {faction['description']}")
            print()
        
        print("输入门派名称加入，或跳过")
        
        choice = input("> ").strip()
        
        for fid, faction in FACTIONS.items():
            if choice in faction["name"]:
                req = faction["requirement"]
                if player.base_stats.get(req["attr"], 0) >= req["min"]:
                    player.faction = fid
                    print(f"✅ 成功加入 {faction['name']}！")
                    return
                else:
                    print(f"属性不满足要求！需要 {req['attr']} >= {req['min']}")
                    return
        
        print("你暂时不加入任何门派，之后可以随时加入")
    
    def show_faction_info(self):
        """显示门派信息"""
        player = self.game.player
        
        if not player.faction:
            print("你还没有加入任何门派")
            return
        
        faction = FACTIONS[player.faction]
        print(f"""
🏯 {faction['name']}
═══════════════════════════════════════
掌门: {faction['leader']}
效果: {faction['bonus']}
描述: {faction['description']}
""")
