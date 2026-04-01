// 共享 JavaScript 函数
const API_BASE = '/api';

function getAuthHeader() {
  const token = localStorage.getItem('auth_token');
  const agentId = localStorage.getItem('agent_id');
  if (!token || !agentId) {
    console.warn('Auth missing - token:', token, 'agentId:', agentId);
    setTimeout(() => { location.href = '/login.html'; }, 100);
    return {};
  }
  return { 'Authorization': `Bearer ${agentId}` };
}

function showToast(msg, type = 'success') {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.className = `toast ${type} show`;
  setTimeout(() => toast.classList.remove('show'), 3000);
}

function formatTime(seconds) {
  if (!seconds || seconds <= 0) return '0秒';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}小时${m}分`;
  if (m > 0) return `${m}分${s}秒`;
  return `${s}秒`;
}

function getItemEmoji(itemId) {
  if (!itemId) return '📦';
  const id = String(itemId).toLowerCase();
  const map = {
    // HP恢复
    'seaweed_pill': '🌿',
    'health_potion': '❤️',
    'hp_potion': '❤️',
    'pearl_dew': '💧',
    // MP恢复
    'mp_potion': '🔮',
    'magic_pill': '🔮',
    // 体力恢复
    'energy_potion': '💚',
    'stamina_pill': '⚡',
    // 金贝
    'gold_bag': '💰',
    'gold_coin': '🪙',
    // 经验
    'xp_book': '📖',
    'exp_scroll': '📜',
    // 装备 - 武器
    'iron_sword': '⚔️',
    'steel_sword': '🗡️',
    'dragon_sword': '🐉',
    'crystal_staff': '🔮',
    // 装备 - 防具
    'leather_armor': '🛡️',
    'iron_armor': '🛡️',
    'dragon_armor': '🐉',
    'speed_boots': '👟',
    'lucky_charm': '🍀',
    'power_shell': '🐚',
    'shield_token': '🛡️',
    // 永久属性
    'perm_claw': '🦀',
    'perm_shell': '🦞',
    'perm_speed': '🐟',
    'perm_wisdom': '🧠',
    'perm_luck': '🍀',
    // 任务道具
    'task_item': '📦',
    'gift_box': '🎁',
    // 其他
    'gem': '💎',
    'crystal': '💠',
    'ore': '�ite',
    'fish': '🐟',
    'shell': '🐚',
  };
  // 匹配前缀
  for (const [key, emoji] of Object.entries(map)) {
    if (id.includes(key)) return emoji;
  }
  return '📦';
}

// ==================== 全局通知横幅 ====================
var _announcementTimer = null;

function showAnnouncement(msg, icon) {
  var existing = document.getElementById('announcement-banner');
  if (existing) existing.remove();
  if (_announcementTimer) clearTimeout(_announcementTimer);

  var banner = document.createElement('div');
  banner.id = 'announcement-banner';
  banner.innerHTML = '<span style="font-size:20px;margin-right:8px">' + (icon || '📢') + '</span><span>' + msg + '</span>';
  banner.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:9999;background:linear-gradient(135deg,rgba(255,100,0,0.95),rgba(200,50,0,0.95));color:#fff;padding:14px 20px;text-align:center;font-size:15px;font-weight:bold;box-shadow:0 4px 20px rgba(0,0,0,0.5);animation:slideDown 0.3s ease-out;cursor:pointer;';
  banner.onclick = function() { banner.remove(); };
  document.body.appendChild(banner);

  // Slide down animation
  var style = document.createElement('style');
  style.textContent = '@keyframes slideDown{from{transform:translateY(-100%)}to{transform:translateY(0)}}';
  document.head.appendChild(style);

  _announcementTimer = setTimeout(function() {
    if (banner.parentNode) {
      banner.style.transition = 'opacity 0.5s';
      banner.style.opacity = '0';
      setTimeout(function() { if (banner.parentNode) banner.remove(); }, 500);
    }
  }, 8000);
}

async function checkAnnouncements() {
  try {
    var res = await fetch(API_BASE + '/announcements/latest', { headers: getAuthHeader() });
    var data = await res.json();
    if (data.success && data.announcement) {
      var ann = data.announcement;
      // Only show if within 30 seconds
      var created = new Date(ann.created_at).getTime();
      if (Date.now() - created < 30000) {
        showAnnouncement(ann.message || ann.chat || ann.content, ann.icon);
      }
    }
  } catch(e) {}
}
