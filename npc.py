#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NPC系统"""

import random

NPCS = {
    "路虾甲": {
        "name": "路虾甲",
        "dialogues": [
            "我什么也不知道，知道我也不说！",
            "隔壁那虾说他是铁钳派的，结果被螃蟹追着跑",
            "听说幻影派的虾跑得特别快，我都追不上",
            "平安海沟最近不太平啊..."
        ]
    },
    "虾婆婆": {
        "name": "虾婆婆",
        "dialogues": [
            "年轻虾就是精力旺盛啊",
            "我这把老骨头，见识过的虾多了去了",
            "有什么需要帮忙的尽管说，婆婆这里随时欢迎你",
            "做人要知道感恩，做虾也一样"
        ]
    },
    "虾村长": {
        "name": "虾村长",
        "dialogues": [
            "年轻虾要多做任务，别整天游手好闲",
            "要想成为一代虾王，就必须勤加修炼",
            "我们平安海沟虽然偏僻，但也算是一片净土",
            "听说深海里还有更强大的存在..."
        ]
    }
}

class NPCManager:
    def __init__(self, game):
        self.game = game
    
    def talk(self):
        """与NPC对话"""
        player = self.game.player
        
        print("\n选择要对话的NPC:")
        for name in NPCS.keys():
            print(f"  • {name}")
        
        choice = input("> ").strip()
        
        npc = NPCS.get(choice)
        if not npc:
            print("没有这个NPC")
            return
        
        dialogue = random.choice(npc["dialogues"])
        print(f"\n💬 {npc['name']}: 「{dialogue}」")
        
        # 对话恢复少量体力
        player.energy = min(player.max_energy, player.energy + 15)
        print(f"⚡ 与{npc['name']}交谈后，精力充沛！体力+15")
