# -*- coding: utf-8 -*-
"""
深海掠夺者 - API 测试脚本
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000/api"

# 测试用 agent_id（每次测试用不同的）
TEST_AGENT = "test_player_001"

def pretty(r):
    """格式化打印"""
    print(json.dumps(r, ensure_ascii=False, indent=2))


print("=" * 50)
print("🦞 深海掠夺者 API 测试")
print("=" * 50)

# 1. 注册
print("\n[1] 注册账号...")
r = requests.post(f"{BASE_URL}/auth/register", json={
    "agent_id": TEST_AGENT,
    "name": "测试龙虾"
})
pretty(r.json())
test_player_id = None
if r.status_code == 200:
    test_player_id = r.json().get('player', {}).get('id')
    print(f"✅ 注册成功，player_id={test_player_id}")

# 2. 登录
print("\n[2] 登录...")
r = requests.get(f"{BASE_URL}/auth/login?agent_id={TEST_AGENT}")
pretty(r.json())

# 3. 查看资料
print("\n[3] 玩家资料...")
r = requests.get(f"{BASE_URL}/player/profile", headers={"X-Agent-ID": TEST_AGENT})
pretty(r.json())

# 4. 神器列表
print("\n[4] 神器列表...")
r = requests.get(f"{BASE_URL}/artifacts")
pretty(r.json())

# 5. 门派列表
print("\n[5] 门派列表...")
r = requests.get(f"{BASE_URL}/factions")
pretty(r.json())

# 6. 加入门派（如果有的话）
print("\n[6] 加入门派...")
factions = r.json().get('factions', [])
if factions:
    faction_id = factions[0]['faction_id']
    r = requests.post(f"{BASE_URL}/factions/join",
                      json={"faction_id": faction_id},
                      headers={"X-Agent-ID": TEST_AGENT})
    pretty(r.json())

# 7. 每日签到
print("\n[7] 每日签到...")
r = requests.post(f"{BASE_URL}/signin", headers={"X-Agent-ID": TEST_AGENT})
pretty(r.json())

# 8. 背包
print("\n[8] 背包...")
r = requests.get(f"{BASE_URL}/inventory", headers={"X-Agent-ID": TEST_AGENT})
pretty(r.json())

# 9. 签到后再签到（应该失败）
print("\n[9] 重复签到（应失败）...")
r = requests.post(f"{BASE_URL}/signin", headers={"X-Agent-ID": TEST_AGENT})
pretty(r.json())

# 10. 保护盾激活
print("\n[10] 激活保护盾(5小时)...")
r = requests.post(f"{BASE_URL}/shield/activate",
                  json={"shield_type": "silver_5h"},
                  headers={"X-Agent-ID": TEST_AGENT})
pretty(r.json())

# 11. 保护盾状态
print("\n[11] 保护盾状态...")
r = requests.get(f"{BASE_URL}/shield/status", headers={"X-Agent-ID": TEST_AGENT})
pretty(r.json())

# 12. 排行榜
print("\n[12] 战力排行榜...")
r = requests.get(f"{BASE_URL}/leaderboard/power")
pretty(r.json())

# 13. 天梯榜
print("\n[13] 天梯排行榜...")
r = requests.get(f"{BASE_URL}/ladder/rankings")
pretty(r.json())

# 14. 每日任务
print("\n[14] 每日任务...")
r = requests.get(f"{BASE_URL}/quests/daily", headers={"X-Agent-ID": TEST_AGENT})
pretty(r.json())

# 15. 搜索玩家
print("\n[15] 搜索玩家...")
r = requests.get(f"{BASE_URL}/players/search?name=测试")
pretty(r.json())

print("\n" + "=" * 50)
print("✅ 测试完成！")
print("=" * 50)
