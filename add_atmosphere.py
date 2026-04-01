#!/usr/bin/env python3
"""Batch add atmospheric dynamic elements to sea area pages."""

import re

# Each page: (file, body_additions, css_additions, script_additions)
PAGES = {
    "pearl.html": {
        "theme": "💎 珍珠湾",
        "body_attrs": 'background: linear-gradient(180deg, #0a0520 0%, #1a0a35 30%, #2a1050 60%, #0a0520 100%);',
        "css": """
    .pearl-glow { position:fixed;top:0;left:0;right:0;bottom:0;background:radial-gradient(ellipse at 30% 40%,rgba(255,182,203,0.12) 0%,transparent 50%),radial-gradient(ellipse at 70% 60%,rgba(200,220,255,0.1) 0%,transparent 50%);pointer-events:none;z-index:1;animation:glowPulse 5s ease-in-out infinite; }
    @keyframes glowPulse { 0%,100%{opacity:0.6}50%{opacity:1} }
    .bubble-pearl { position:fixed;bottom:-60px;border-radius:50%;background:radial-gradient(circle at 30% 30%,rgba(255,255,255,0.5),rgba(200,180,255,0.2));animation:pearlRise linear infinite;pointer-events:none;z-index:2;box-shadow:inset -2px -2px 6px rgba(255,255,255,0.3); }
    @keyframes pearlRise { 0%{transform:translateY(0) translateX(0) scale(1);opacity:0.8}25%{transform:translateY(-25vh) translateX(8px)}50%{opacity:0.4;transform:translateY(-50vh) translateX(-4px)}75%{transform:translateY(-75vh) translateX(6px)}100%{transform:translateY(-110vh) translateX(0) scale(0.3);opacity:0} }
    .shell { position:fixed;font-size:28px;opacity:0.12;pointer-events:none;z-index:2;animation:shellBob ease-in-out infinite; }
    @keyframes shellBob { 0%,100%{transform:translateY(0) rotate(-8deg);opacity:0.12}50%{transform:translateY(-18px) rotate(8deg);opacity:0.2} }
    .starfish { position:fixed;font-size:24px;opacity:0.1;pointer-events:none;z-index:2;animation:starRotate ease-in-out infinite; }
    @keyframes starRotate { 0%,100%{transform:rotate(-10deg) scale(1)}50%{transform:rotate(10deg) scale(1.1)} }
    .pearl-sparkle { position:fixed;width:5px;height:5px;background:radial-gradient(circle,#fff,#ffd700);border-radius:50%;pointer-events:none;z-index:5;animation:pearlSparkle ease-in-out infinite;box-shadow:0 0 8px #ffd700,0 0 15px #fff; }
    @keyframes pearlSparkle { 0%,100%{opacity:0.1;transform:scale(0.6)}50%{opacity:1;transform:scale(1.4)} }
    .clamshell { position:fixed;font-size:40px;opacity:0.1;pointer-events:none;z-index:2;animation:clamshellOpen ease-in-out infinite; }
    @keyframes clamshellOpen { 0%,100%{transform:rotate(-5deg) scaleX(1)}50%{transform:rotate(5deg) scaleX(1.1)} }
    .vignette { position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:6;background:radial-gradient(ellipse at 50% 50%,transparent 45%,rgba(0,0,0,0.45) 100%); }
    .fog { position:fixed;top:0;left:0;right:0;bottom:0;background:radial-gradient(ellipse at 50% 100%,rgba(200,180,255,0.08) 0%,transparent 60%);pointer-events:none;z-index:2;animation:fogDrift 10s ease-in-out infinite; }
    @keyframes fogDrift { 0%,100%{opacity:0.5;transform:translateX(-2%)}50%{opacity:0.9;transform:translateX(2%)} }
""",
        "body_divs": """
  <div class="pearl-glow"></div>
  <div class="fog"></div>
  <div id="pearlBubbles"></div>
  <div id="pearlShells"></div>
  <div id="pearlStarfish"></div>
  <div id="pearlClamshells"></div>
  <div id="pearlSparkles"></div>
  <div class="vignette"></div>""",
        "script": """
    // Pearl atmosphere
    const pb = document.getElementById('pearlBubbles');
    for(let i=0;i<18;i++){const b=document.createElement('div');b.className='bubble-pearl';const s=Math.random()*25+8;b.style.width=b.style.height=s+'px';b.style.left=Math.random()*100+'%';b.style.animationDuration=(Math.random()*8+6)+'s';b.style.animationDelay=(Math.random()*6)+'s';pb.appendChild(b);}
    const ps = document.getElementById('pearlShells');
    ['🐚','🪸','🪸'].forEach((icon,i)=>{const s=document.createElement('div');s.className='shell';s.textContent=icon;s.style.left=(8+i*28)+'%';s.style.bottom=(10+Math.random()*20)+'%';s.style.animationDuration=(3+Math.random()*2)+'s';s.style.animationDelay=(i*1.2)+'s';ps.appendChild(s);});
    const pst = document.getElementById('pearlStarfish');
    ['⭐','🌟','✨'].forEach((icon,i)=>{const s=document.createElement('div');s.className='starfish';s.textContent=icon;s.style.left=(12+i*25)+'%';s.style.top=(15+i*18)+'%';s.style.animationDuration=(2.5+Math.random()*2)+'s';s.style.animationDelay=(i*0.8)+'s';pst.appendChild(s);});
    const pcs = document.getElementById('pearlClamshells');
    ['🦪','🐚'].forEach((icon,i)=>{const c=document.createElement('div');c.className='clamshell';c.textContent=icon;c.style.left=(15+i*35)+'%';c.style.bottom=(8+i*5)+'%';c.style.animationDuration=(4+Math.random()*2)+'s';c.style.animationDelay=(i*2)+'s';pcs.appendChild(c);});
    const psp = document.getElementById('pearlSparkles');
    for(let i=0;i<20;i++){const s=document.createElement('div');s.className='pearl-sparkle';s.style.left=Math.random()*100+'%';s.style.top=Math.random()*80+'%';s.style.animationDuration=(1.5+Math.random()*2.5)+'s';s.style.animationDelay=(Math.random()*4)+'s';psp.appendChild(s);}
""",
    },
    "volcano.html": {
        "theme": "🌋 火山海域",
        "css": """
    .lava-glow { position:fixed;top:0;left:0;right:0;bottom:0;background:radial-gradient(ellipse at 50% 100%,rgba(255,80,0,0.25) 0%,transparent 55%),radial-gradient(ellipse at 20% 100%,rgba(255,30,0,0.15) 0%,transparent 45%),radial-gradient(ellipse at 80% 100%,rgba(255,100,0,0.2) 0%,transparent 50%);pointer-events:none;z-index:1;animation:lavaPulse 3s ease-in-out infinite; }
    @keyframes lavaPulse { 0%,100%{opacity:0.7}50%{opacity:1} }
    .lava-bubble { position:fixed;font-size:20px;opacity:0;animation:lavaBubble linear infinite;pointer-events:none;z-index:3; }
    @keyframes lavaBubble { 0%{transform:translateY(0) scale(0.5);opacity:0}10%{opacity:0.8}80%{opacity:0.4}100%{transform:translateY(-60px) scale(1.2);opacity:0} }
    .ember { position:fixed;width:4px;height:4px;background:#ff6600;border-radius:50%;pointer-events:none;z-index:4;animation:emberFloat linear infinite;box-shadow:0 0 6px #ff4500; }
    @keyframes emberFloat { 0%{transform:translateY(0) translateX(0) scale(1);opacity:1}100%{transform:translateY(-80px) translateX(20px) scale(0);opacity:0} }
    .smoke-puff { position:fixed;font-size:24px;opacity:0;animation:smokePuff linear infinite;pointer-events:none;z-index:2; }
    @keyframes smokePuff { 0%{transform:translateY(0) scale(0.5);opacity:0}15%{opacity:0.3}85%{opacity:0.15}100%{transform:translateY(-100px) scale(1.5);opacity:0} }
    .rock { position:fixed;font-size:18px;opacity:0.12;pointer-events:none;z-index:3;animation:rockSlide ease-in-out infinite; }
    @keyframes rockSlide { 0%,100%{transform:translateY(0) rotate(-10deg)}50%{transform:translateY(-15px) rotate(10deg)} }
    .lava-flow { position:fixed;bottom:0;left:0;right:0;height:5px;background:linear-gradient(90deg,transparent,rgba(255,100,0,0.4),rgba(255,50,0,0.6),rgba(255,100,0,0.4),transparent);pointer-events:none;z-index:2;animation:lavaFlow 3s linear infinite; }
    @keyframes lavaFlow { 0%{transform:scaleX(0.3);opacity:0.3}50%{transform:scaleX(0.8);opacity:0.7}100%{transform:scaleX(0.3);opacity:0.3} }
    .heat-wave { position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:5;background:linear-gradient(180deg,rgba(255,100,0,0.03) 0%,transparent 30%);animation:heatWave 2s ease-in-out infinite alternate; }
    @keyframes heatWave { 0%{opacity:0.3}100%{opacity:0.7} }
    .vignette { position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:6;background:radial-gradient(ellipse at 50% 50%,transparent 40%,rgba(0,0,0,0.5) 100%); }
""",
        "body_divs": """
  <div class="lava-glow"></div>
  <div class="heat-wave"></div>
  <div class="lava-flow"></div>
  <div id="lavaBubbles"></div>
  <div id="emberContainer"></div>
  <div id="smokePuffs"></div>
  <div id="rockContainer"></div>
  <div class="vignette"></div>""",
        "script": """
    // Volcano atmosphere
    const lb = document.getElementById('lavaBubbles');
    const lavaIcons = ['💥','🔥','🌋','💥','🔥'];
    for(let i=0;i<6;i++){const b=document.createElement('div');b.className='lava-bubble';b.textContent=lavaIcons[i%lavaIcons.length];b.style.left=(5+i*16)+'%';b.style.bottom=(5+Math.random()*15)+'%';b.style.animationDuration=(2+Math.random()*2)+'s';b.style.animationDelay=(i*1.5)+'s';lb.appendChild(b);}
    const ec = document.getElementById('emberContainer');
    for(let i=0;i<20;i++){const e=document.createElement('div');e.className='ember';e.style.left=Math.random()*100+'%';e.style.bottom=(Math.random()*30)+'%';e.style.animationDuration=(1.5+Math.random()*2)+'s';e.style.animationDelay=(Math.random()*4)+'s';ec.appendChild(e);}
    const sp = document.getElementById('smokePuffs');
    ['☁️','🌫️','💨','☁️'].forEach((icon,i)=>{const s=document.createElement('div');s.className='smoke-puff';s.textContent=icon;s.style.left=(8+i*22)+'%';s.style.bottom=(10+i*3)+'%';s.style.animationDuration=(4+Math.random()*3)+'s';s.style.animationDelay=(i*2)+'s';sp.appendChild(s);});
    const rc = document.getElementById('rockContainer');
    ['🪨','🪨','🪨'].forEach((icon,i)=>{const r=document.createElement('div');r.className='rock';r.textContent=icon;r.style.left=(10+i*28)+'%';r.style.bottom=(5+i*4)+'%';r.style.animationDuration=(3+Math.random()*2)+'s';r.style.animationDelay=(i*1.5)+'s';rc.appendChild(r);});
""",
    },
    "ice.html": {
        "theme": "🧊 冰封海峡",
        "css": """
    .aurora { position:fixed;top:0;left:0;right:0;height:50%;background:linear-gradient(180deg,rgba(100,200,255,0.06) 0%,rgba(150,100,255,0.04) 50%,transparent 100%);pointer-events:none;z-index:1;animation:auroraShift 8s ease-in-out infinite; }
    @keyframes auroraShift { 0%,100%{opacity:0.5;transform:translateX(-3%)}50%{opacity:0.9;transform:translateX(3%)} }
    .snowflake { position:fixed;color:rgba(255,255,255,0.7);pointer-events:none;z-index:3;animation:snowFall linear infinite; }
    @keyframes snowFall { 0%{transform:translateY(-20px) rotate(0deg);opacity:0}10%{opacity:0.8}90%{opacity:0.6}100%{transform:translateY(100vh) rotate(360deg);opacity:0} }
    .ice-crystal { position:fixed;font-size:22px;opacity:0.12;pointer-events:none;z-index:2;animation:iceCrystalShimmer ease-in-out infinite; }
    @keyframes iceCrystalShimmer { 0%,100%{opacity:0.08;transform:scale(1) rotate(0deg)}50%{opacity:0.2;transform:scale(1.15) rotate(30deg)} }
    .frost-edge { position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:2;box-shadow:inset 0 0 80px rgba(173,216,230,0.08); }
    .blizzard { position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:4;opacity:0.05;background:repeating-linear-gradient(90deg,transparent,transparent 2px,rgba(255,255,255,0.3) 2px,rgba(255,255,255,0.3) 4px);animation:blizzardMove 0.5s linear infinite; }
    @keyframes blizzardMove { 0%{transform:translateX(0)}100%{transform:translateX(4px)} }
    .icicle { position:fixed;top:-10px;width:6px;background:linear-gradient(180deg,rgba(200,230,255,0.6),transparent);border-radius:0 0 50% 50%;pointer-events:none;z-index:3;animation:icicleDrip linear infinite; }
    @keyframes icicleDrip { 0%{transform:translateY(0);opacity:0.8}100%{transform:translateY(100vh);opacity:0} }
    .penguin { position:fixed;font-size:26px;opacity:0.1;pointer-events:none;z-index:3;animation:penguinWaddle ease-in-out infinite; }
    @keyframes penguinWaddle { 0%,100%{transform:translateY(0) rotate(-5deg)}50%{transform:translateY(-10px) rotate(5deg)} }
    .polar-bear { position:fixed;font-size:40px;opacity:0.08;pointer-events:none;z-index:2;animation:bearIdle ease-in-out infinite; }
    @keyframes bearIdle { 0%,100%{transform:translateX(0)}50%{transform:translateX(15px)} }
    .vignette { position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:6;background:radial-gradient(ellipse at 50% 50%,transparent 40%,rgba(0,30,60,0.5) 100%); }
""",
        "body_divs": """
  <div class="aurora"></div>
  <div class="frost-edge"></div>
  <div class="blizzard"></div>
  <div id="snowContainer"></div>
  <div id="iceCrystalContainer"></div>
  <div id="icicleContainer"></div>
  <div id="animalContainer"></div>
  <div class="vignette"></div>""",
        "script": """
    // Ice atmosphere
    const snowC = document.getElementById('snowContainer');
    for(let i=0;i<30;i++){const s=document.createElement('div');s.className='snowflake';s.textContent=['❄','❅','❆','✦','•'][i%5];s.style.left=Math.random()*100+'%';s.style.fontSize=(Math.random()*14+8)+'px';s.style.animationDuration=(Math.random()*8+6)+'s';s.style.animationDelay=(Math.random()*8)+'s';snowC.appendChild(s);}
    const iceC = document.getElementById('iceCrystalContainer');
    ['❄','❅','❆','🔹','🧊'].forEach((icon,i)=>{const c=document.createElement('div');c.className='ice-crystal';c.textContent=icon;c.style.left=(5+i*20)+'%';c.style.top=(10+i*12)+'%';c.style.animationDuration=(3+Math.random()*2)+'s';c.style.animationDelay=(i*0.7)+'s';iceC.appendChild(c);});
    const icc = document.getElementById('icicleContainer');
    for(let i=0;i<8;i++){const ic=document.createElement('div');ic.className='icicle';ic.style.left=(5+i*12)+'%';ic.style.height=(30+Math.random()*50)+'px';ic.style.animationDuration=(3+Math.random()*3)+'s';ic.style.animationDelay=(i*1.2)+'s';icc.appendChild(ic);}
    const ac = document.getElementById('animalContainer');
    ['🐧','🐻‍❄️','🦭'].forEach((icon,i)=>{const a=document.createElement('div');a.className=icon==='🐧'?'penguin':icon==='🐻‍❄️'?'polar-bear':'penguin';a.textContent=icon;a.style.left=(10+i*30)+'%';a.style.bottom=(5+i*3)+'%';a.style.animationDuration=(4+Math.random()*3)+'s';a.style.animationDelay=(i*2)+'s';ac.appendChild(a);});
""",
    },
    "ghost.html": {
        "theme": "👻 幽灵船队",
        "css": """
    .ghost-glow { position:fixed;top:0;left:0;right:0;bottom:0;background:radial-gradient(ellipse at 30% 30%,rgba(100,0,150,0.15) 0%,transparent 50%),radial-gradient(ellipse at 70% 70%,rgba(50,0,100,0.2) 0%,transparent 50%);pointer-events:none;z-index:1;animation:glowFlicker 5s ease-in-out infinite; }
    @keyframes glowFlicker { 0%,100%{opacity:0.6}30%{opacity:0.3}50%{opacity:0.9}70%{opacity:0.4} }
    .spirit { position:fixed;font-size:28px;opacity:0;animation:spiritRise linear infinite;pointer-events:none;z-index:4; }
    @keyframes spiritRise { 0%{transform:translateY(100vh) translateX(0) scale(0.8);opacity:0}15%{opacity:0.2}85%{opacity:0.15}100%{transform:translateY(-80px) translateX(30px) scale(1.2);opacity:0} }
    .will-o-wisp { position:fixed;width:6px;height:6px;background:radial-gradient(circle,rgba(150,255,100,0.9),rgba(0,200,100,0.3));border-radius:50%;pointer-events:none;z-index:5;animation:wispFloat ease-in-out infinite;box-shadow:0 0 10px #50ff80,0 0 20px rgba(80,255,128,0.5); }
    @keyframes wispFloat { 0%,100%{transform:translateY(0) translateX(0);opacity:0.3}50%{transform:translateY(-25px) translateX(15px);opacity:0.9} }
    .fog-layer { position:fixed;top:0;left:0;right:0;bottom:0;background:radial-gradient(ellipse at 50% 100%,rgba(80,0,120,0.2) 0%,transparent 60%);pointer-events:none;z-index:2;animation:fogDrift 10s ease-in-out infinite; }
    @keyframes fogDrift { 0%,100%{opacity:0.4;transform:translateX(-5%)}50%{opacity:0.7;transform:translateX(5%)} }
    .chain { position:fixed;font-size:22px;opacity:0.1;pointer-events:none;z-index:3;animation:chainRattle ease-in-out infinite; }
    @keyframes chainRattle { 0%,100%{transform:rotate(-10deg)}50%{transform:rotate(10deg)} }
    .ghost-ship { position:fixed;font-size:32px;opacity:0.1;pointer-events:none;z-index:3;animation:ghostShipDrift linear infinite;bottom:20%; }
    @keyframes ghostShipDrift { 0%{transform:translateX(-100px)}100%{transform:translateX(calc(100vw + 100px))} }
    .skull-wave { position:fixed;font-size:24px;opacity:0;animation:skullWave linear infinite;pointer-events:none;z-index:4; }
    @keyframes skullWave { 0%{transform:translateY(0);opacity:0}20%{opacity:0.1}80%{opacity:0.08}100%{transform:translateY(-60px);opacity:0} }
    .vignette { position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:6;background:radial-gradient(ellipse at 50% 50%,transparent 35%,rgba(0,0,0,0.6) 100%); }
""",
        "body_divs": """
  <div class="ghost-glow"></div>
  <div class="fog-layer"></div>
  <div id="spiritContainer"></div>
  <div id="wispContainer"></div>
  <div id="chainContainer"></div>
  <div id="ghostShipContainer"></div>
  <div id="skullWaveContainer"></div>
  <div class="vignette"></div>""",
        "script": """
    // Ghost atmosphere
    const spiritC = document.getElementById('spiritContainer');
    const spiritIcons = ['👻','💀','🕯️','🔥','👻','✨'];
    for(let i=0;i<7;i++){const s=document.createElement('div');s.className='spirit';s.textContent=spiritIcons[i%spiritIcons.length];s.style.left=(5+i*14)+'%';s.style.animationDuration=(15+i*3)+'s';s.style.animationDelay=(i*2.5)+'s';s.style.fontSize=(20+Math.random()*12)+'px';spiritC.appendChild(s);}
    const wispC = document.getElementById('wispContainer');
    for(let i=0;i<12;i++){const w=document.createElement('div');w.className='will-o-wisp';w.style.left=Math.random()*100+'%';w.style.top=(20+Math.random()*60)+'%';w.style.animationDuration=(3+Math.random()*3)+'s';w.style.animationDelay=(Math.random()*5)+'s';wispC.appendChild(w);}
    const chainC = document.getElementById('chainContainer');
    ['⛓️','🔗','⛓️'].forEach((icon,i)=>{const c=document.createElement('div');c.className='chain';c.textContent=icon;c.style.right=(8+i*25)+'%';c.style.bottom=(5+i*4)+'%';c.style.animationDuration=(2.5+Math.random()*2)+'s';c.style.animationDelay=(i*1.5)+'s';chainC.appendChild(c);});
    const gsC = document.getElementById('ghostShipContainer');
    ['🚢','🏴‍☠️','🚢'].forEach((icon,i)=>{const g=document.createElement('div');g.className='ghost-ship';g.textContent=icon;g.style.animationDuration=(60+i*20)+'s';g.style.animationDelay=(i*22)+'s';g.style.fontSize=(26+i*6)+'px';gsC.appendChild(g);});
    const swC = document.getElementById('skullWaveContainer');
    ['💀','☠️','💀','🦴'].forEach((icon,i)=>{const s=document.createElement('div');s.className='skull-wave';s.textContent=icon;s.style.left=(8+i*22)+'%';s.style.animationDuration=(6+Math.random()*3)+'s';s.style.animationDelay=(i*3)+'s';swC.appendChild(s);});
""",
    },
    "snow.html": {
        "theme": "❄️ 雪原商路",
        "css": """
    .sky-glow { position:fixed;top:0;left:0;right:0;bottom:0;background:linear-gradient(180deg,rgba(180,210,230,0.15) 0%,rgba(150,190,220,0.1) 50%,rgba(200,220,240,0.08) 100%);pointer-events:none;z-index:1; }
    .snow-particle { position:fixed;color:rgba(255,255,255,0.8);pointer-events:none;z-index:3;animation:snowFall linear infinite; }
    @keyframes snowFall { 0%{transform:translateY(-20px) translateX(0) rotate(0deg);opacity:0}10%{opacity:0.9}50%{transform:translateY(50vh) translateX(20px) rotate(180deg)}90%{opacity:0.5}100%{transform:translateY(100vh) translateX(-10px) rotate(360deg);opacity:0} }
    .sleigh { position:fixed;font-size:32px;opacity:0.15;pointer-events:none;z-index:3;animation:sleighRide linear infinite;bottom:25%; }
    @keyframes sleighRide { 0%{transform:translateX(-100px)}100%{transform:translateX(calc(100vw + 100px))} }
    .pine-tree { position:fixed;font-size:36px;opacity:0.12;pointer-events:none;z-index:2;animation:pineSway ease-in-out infinite; }
    @keyframes pineSway { 0%,100%{transform:rotate(-3deg)}50%{transform:rotate(3deg)} }
    .gift { position:fixed;font-size:22px;opacity:0.1;pointer-events:none;z-index:3;animation:giftBob ease-in-out infinite; }
    @keyframes giftBob { 0%,100%{transform:translateY(0) rotate(-5deg)}50%{transform:translateY(-12px) rotate(5deg)} }
    .reindeer { position:fixed;font-size:26px;opacity:0.1;pointer-events:none;z-index:3;animation:reindeerRun linear infinite;bottom:18%; }
    @keyframes reindeerRun { 0%{transform:translateX(-80px)}100%{transform:translateX(calc(100vw + 80px))} }
    .carrot { position:fixed;font-size:18px;opacity:0.1;pointer-events:none;z-index:3;animation:carrotBob ease-in-out infinite; }
    @keyframes carrotBob { 0%,100%{transform:rotate(-15deg)}50%{transform:rotate(15deg)} }
    .snow-ground { position:fixed;bottom:0;left:0;right:0;height:12%;background:linear-gradient(180deg,transparent,rgba(220,240,255,0.12) 50%,rgba(200,230,255,0.2));pointer-events:none;z-index:2; }
    .vignette { position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:6;background:radial-gradient(ellipse at 50% 50%,transparent 45%,rgba(100,140,180,0.3) 100%); }
""",
        "body_divs": """
  <div class="sky-glow"></div>
  <div class="snow-ground"></div>
  <div id="snowParticles"></div>
  <div id="sleighContainer"></div>
  <div id="pineContainer"></div>
  <div id="giftContainer"></div>
  <div id="reindeerContainer"></div>
  <div class="vignette"></div>""",
        "script": """
    // Snow atmosphere
    const sp = document.getElementById('snowParticles');
    for(let i=0;i<35;i++){const s=document.createElement('div');s.className='snow-particle';s.textContent=['❄','❅','❆','✦','❇'][i%5];s.style.left=Math.random()*100+'%';s.style.fontSize=(Math.random()*16+8)+'px';s.style.animationDuration=(Math.random()*10+7)+'s';s.style.animationDelay=(Math.random()*8)+'s';sp.appendChild(s);}
    const sleighC = document.getElementById('sleighContainer');
    ['🛷','🎁','🛷'].forEach((icon,i)=>{const s=document.createElement('div');s.className='sleigh';s.textContent=icon;s.style.animationDuration=(40+i*15)+'s';s.style.animationDelay=(i*18)+'s';s.style.fontSize=(26+i*4)+'px';sleighC.appendChild(s);});
    const pineC = document.getElementById('pineContainer');
    ['🌲','🎄','🌲','🎅','🌲'].forEach((icon,i)=>{const p=document.createElement('div');p.className='pine-tree';p.textContent=icon;p.style.left=(3+i*19)+'%';p.style.bottom=(2+i*2)+'%';p.style.fontSize=(30+Math.random()*16)+'px';p.style.animationDuration=(3+Math.random()*2)+'s';p.style.animationDelay=(i*0.6)+'s';pineC.appendChild(p);});
    const gc = document.getElementById('giftContainer');
    ['🎁','🎀','🎁'].forEach((icon,i)=>{const g=document.createElement('div');g.className='gift';g.textContent=icon;g.style.left=(10+i*28)+'%';g.style.bottom=(8+i*4)+'%';g.style.animationDuration=(2.5+Math.random()*2)+'s';g.style.animationDelay=(i*1.5)+'s';gc.appendChild(g);});
    const rc = document.getElementById('reindeerContainer');
    ['🦌','🦌'].forEach((icon,i)=>{const r=document.createElement('div');r.className='reindeer';r.textContent=icon;r.style.animationDuration=(50+i*20)+'s';r.style.animationDelay=(i*25)+'s';rc.appendChild(r);});
""",
    },
    "winter.html": {
        "theme": "🌨️ 凛冬将至",
        "css": """
    .storm-aura { position:fixed;top:0;left:0;right:0;bottom:0;background:radial-gradient(ellipse at 50% 0%,rgba(100,160,220,0.12) 0%,transparent 60%);pointer-events:none;z-index:1;animation:stormPulse 6s ease-in-out infinite; }
    @keyframes stormPulse { 0%,100%{opacity:0.5}50%{opacity:1} }
    .blizzard-h { position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:4;opacity:0.06;background:repeating-linear-gradient(100deg,transparent,transparent 3px,rgba(200,230,255,0.4) 3px,rgba(200,230,255,0.4) 5px);animation:blizzardHMove 0.3s linear infinite; }
    @keyframes blizzardHMove { 0%{transform:translateX(0) translateY(0)}100%{transform:translateX(5px) translateY(3px)} }
    .ice-shard { position:fixed;font-size:20px;opacity:0;animation:iceShardFall linear infinite;pointer-events:none;z-index:3;color:rgba(180,220,255,0.6); }
    @keyframes iceShardFall { 0%{transform:translateY(-30px) rotate(0deg);opacity:0}15%{opacity:0.7}85%{opacity:0.4}100%{transform:translateY(100vh) rotate(180deg);opacity:0} }
    .wind-gust { position:fixed;font-size:22px;opacity:0;animation:windGust ease-in-out infinite;pointer-events:none;z-index:4;color:rgba(180,210,255,0.4); }
    @keyframes windGust { 0%,100%{opacity:0;transform:translateX(-50px) scaleX(0.8)}50%{opacity:0.5;transform:translateX(50vw) scaleX(1.2)} }
    .aurora-borealis { position:fixed;top:0;left:0;right:0;height:40%;background:linear-gradient(180deg,rgba(80,200,150,0.05) 0%,rgba(100,150,255,0.06) 40%,rgba(150,100,200,0.04) 70%,transparent 100%);pointer-events:none;z-index:2;animation:auroraWave 10s ease-in-out infinite; }
    @keyframes auroraWave { 0%,100%{opacity:0.4;transform:translateX(-5%) skewX(-2deg)}50%{opacity:0.8;transform:translateX(5%) skewX(2deg)} }
    .frost-rune { position:fixed;font-size:18px;opacity:0;animation:frostRuneAppear ease-in-out infinite;pointer-events:none;z-index:3;color:rgba(150,210,255,0.5); }
    @keyframes frostRuneAppear { 0%,100%{opacity:0;transform:scale(0.5)}50%{opacity:0.4;transform:scale(1.2)} }
    .polar-bear-sil { position:fixed;font-size:45px;opacity:0.06;pointer-events:none;z-index:2;animation:bearRoam linear infinite; }
    @keyframes bearRoam { 0%{transform:translateX(-100px)}100%{transform:translateX(calc(100vw + 100px))} }
    .ice-floor { position:fixed;bottom:0;left:0;right:0;height:10%;background:linear-gradient(180deg,transparent,rgba(150,200,255,0.08) 50%,rgba(100,180,255,0.15));pointer-events:none;z-index:2; }
    .vignette { position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:6;background:radial-gradient(ellipse at 50% 50%,transparent 35%,rgba(0,10,30,0.6) 100%); }
""",
        "body_divs": """
  <div class="storm-aura"></div>
  <div class="aurora-borealis"></div>
  <div class="blizzard-h"></div>
  <div id="iceShardContainer"></div>
  <div id="windGustContainer"></div>
  <div id="frostRuneContainer"></div>
  <div id="polarBearContainer"></div>
  <div class="ice-floor"></div>
  <div class="vignette"></div>""",
        "script": """
    // Winter storm atmosphere
    const isc = document.getElementById('iceShardContainer');
    for(let i=0;i<20;i++){const s=document.createElement('div');s.className='ice-shard';s.textContent=['❄','❅','❆','🧊','🔹'][i%5];s.style.left=Math.random()*100+'%';s.style.fontSize=(Math.random()*14+10)+'px';s.style.animationDuration=(Math.random()*6+4)+'s';s.style.animationDelay=(Math.random()*6)+'s';isc.appendChild(s);}
    const wgc = document.getElementById('windGustContainer');
    ['💨','🌬️','💨'].forEach((icon,i)=>{const w=document.createElement('div');w.className='wind-gust';w.textContent=icon;w.style.top=(10+i*25)+'%';w.style.animationDuration=(4+Math.random()*3)+'s';w.style.animationDelay=(i*3)+'s';wgc.appendChild(w);});
    const frc = document.getElementById('frostRuneContainer');
    const runeIcons = ['✦','❄','✦','❄','✦','❄'];
    runeIcons.forEach((icon,i)=>{const r=document.createElement('div');r.className='frost-rune';r.textContent=icon;r.style.left=(8+i*15)+'%';r.style.top=(15+i*10)+'%';r.style.fontSize=(16+Math.random()*8)+'px';r.style.animationDuration=(4+Math.random()*3)+'s';r.style.animationDelay=(i*1.5)+'s';frc.appendChild(r);});
    const pbc = document.getElementById('polarBearContainer');
    ['🐻‍❄️','🐻‍❄️'].forEach((icon,i)=>{const b=document.createElement('div');b.className='polar-bear-sil';b.textContent=icon;b.style.animationDuration=(80+i*30)+'s';b.style.animationDelay=(i*40)+'s';pbc.appendChild(b);});
""",
    },
    "troll.html": {
        "theme": "🧌 巨魔领域",
        "css": """
    .forest-mist { position:fixed;top:0;left:0;right:0;bottom:0;background:radial-gradient(ellipse at 50% 100%,rgba(0,80,0,0.15) 0%,transparent 60%);pointer-events:none;z-index:1;animation:forestMist 8s ease-in-out infinite; }
    @keyframes forestMist { 0%,100%{opacity:0.5}50%{opacity:0.8} }
    .firefly { position:fixed;width:5px;height:5px;background:radial-gradient(circle,rgba(150,255,50,0.9),rgba(50,200,0,0.3));border-radius:50%;pointer-events:none;z-index:5;animation:fireflyGlow ease-in-out infinite;box-shadow:0 0 8px #80ff20,0 0 15px rgba(100,255,50,0.4); }
    @keyframes fireflyGlow { 0%,100%{opacity:0.2;transform:translate(0,0)}25%{opacity:0.9;transform:translate(10px,-15px)}50%{opacity:0.4;transform:translate(-5px,-25px)}75%{opacity:0.8;transform:translate(8px,-10px)} }
    .mushroom { position:fixed;font-size:24px;opacity:0.12;pointer-events:none;z-index:2;animation:mushroomPulse ease-in-out infinite; }
    @keyframes mushroomPulse { 0%,100%{transform:scale(1)}50%{transform:scale(1.08)} }
    .vine { position:fixed;font-size:28px;opacity:0.1;pointer-events:none;z-index:2;animation:vineSway ease-in-out infinite;transform-origin:top center; }
    @keyframes vineSway { 0%,100%{transform:rotate(-5deg)}50%{transform:rotate(5deg)} }
    .mushroom-glow { position:fixed;width:8px;height:8px;background:radial-gradient(circle,rgba(100,255,50,0.7),transparent);border-radius:50%;pointer-events:none;z-index:5;animation:mushroomGlowP ease-in-out infinite;box-shadow:0 0 10px rgba(80,200,0,0.5); }
    @keyframes mushroomGlowP { 0%,100%{opacity:0.3;transform:scale(0.8)}50%{opacity:0.8;transform:scale(1.3)} }
    .butterfly { position:fixed;font-size:20px;opacity:0.15;pointer-events:none;z-index:4;animation:butterflyFloat ease-in-out infinite; }
    @keyframes butterflyFloat { 0%,100%{transform:translateY(0) translateX(0) rotate(-5deg)}33%{transform:translateY(-20px) translateX(15px) rotate(5deg)}66%{transform:translateY(-10px) translateX(-10px) rotate(-3deg)} }
    .owl { position:fixed;font-size:26px;opacity:0.1;pointer-events:none;z-index:4;animation:owlBob ease-in-out infinite; }
    @keyframes owlBob { 0%,100%{transform:rotate(-8deg)}50%{transform:rotate(8deg)} }
    .frog { position:fixed;font-size:22px;opacity:0.1;pointer-events:none;z-index:4;animation:frogHop ease-in-out infinite; }
    @keyframes frogHop { 0%,100%{transform:translateY(0) scaleX(1)}50%{transform:translateY(-12px) scaleX(0.9)} }
    .vignette { position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:6;background:radial-gradient(ellipse at 50% 50%,transparent 40%,rgba(0,20,0,0.5) 100%); }
""",
        "body_divs": """
  <div class="forest-mist"></div>
  <div id="fireflyContainer"></div>
  <div id="mushroomContainer"></div>
  <div id="vineContainer"></div>
  <div id="butterflyContainer"></div>
  <div id="owlContainer"></div>
  <div id="frogContainer"></div>
  <div class="vignette"></div>""",
        "script": """
    // Troll forest atmosphere
    const ffc = document.getElementById('fireflyContainer');
    for(let i=0;i<20;i++){const f=document.createElement('div');f.className='firefly';f.style.left=Math.random()*100+'%';f.style.top=(20+Math.random()*60)+'%';f.style.animationDuration=(3+Math.random()*4)+'s';f.style.animationDelay=(Math.random()*6)+'s';ffc.appendChild(f);}
    const mc = document.getElementById('mushroomContainer');
    ['🍄','🍄','🪵','🍄','🌿'].forEach((icon,i)=>{const m=document.createElement('div');m.className='mushroom';m.textContent=icon;m.style.left=(5+i*18)+'%';m.style.bottom=(2+i*3)+'%';m.style.fontSize=(22+Math.random()*12)+'px';m.style.animationDuration=(2.5+Math.random()*2)+'s';m.style.animationDelay=(i*0.8)+'s';mc.appendChild(m);});
    const vc = document.getElementById('vineContainer');
    ['🌿','🌱','🪴','🌿','🌱'].forEach((icon,i)=>{const v=document.createElement('div');v.className='vine';v.textContent=icon;v.style.left=(8+i*18)+'%';v.style.top=(5+i*2)+'%';v.style.fontSize=(24+Math.random()*10)+'px';v.style.animationDuration=(3+Math.random()*2)+'s';v.style.animationDelay=(i*1.2)+'s';vc.appendChild(v);});
    const bc = document.getElementById('butterflyContainer');
    ['🦋','🦋','🦋','🐛'].forEach((icon,i)=>{const b=document.createElement('div');b.className='butterfly';b.textContent=icon;b.style.left=(10+i*22)+'%';b.style.top=(15+Math.random()*25)+'%';b.style.animationDuration=(6+Math.random()*4)+'s';b.style.animationDelay=(i*2.5)+'s';bc.appendChild(b);});
    const oc = document.getElementById('owlContainer');
    ['🦉','🦉'].forEach((icon,i)=>{const o=document.createElement('div');o.className='owl';o.textContent=icon;o.style.right=(10+i*25)+'%';o.style.top=(10+i*15)+'%';o.style.fontSize=(22+Math.random()*8)+'px';o.style.animationDuration=(4+Math.random()*3)+'s';o.style.animationDelay=(i*3)+'s';oc.appendChild(o);});
    const frc2 = document.getElementById('frogContainer');
    ['🐸','🐸'].forEach((icon,i)=>{const f=document.createElement('div');f.className='frog';f.textContent=icon;f.style.left=(15+i*30)+'%';f.style.bottom=(5+i*4)+'%';f.style.animationDuration=(2.5+Math.random()*2)+'s';f.style.animationDelay=(i*2)+'s';frc2.appendChild(f);});
""",
    },
    "abyss.html": {
        "theme": "🌀 深海漩涡",
        "css": """
    .vortex-aura { position:fixed;top:50%;left:50%;width:150vmax;height:150vmax;transform:translate(-50%,-50%);background:conic-gradient(from 0deg,transparent,rgba(80,0,150,0.08),rgba(120,0,200,0.1),rgba(60,0,120,0.06),transparent);pointer-events:none;z-index:1;animation:vortexSpin 20s linear infinite;border-radius:50%; }
    @keyframes vortexSpin { 0%{transform:translate(-50%,-50%) rotate(0deg)}100%{transform:translate(-50%,-50%) rotate(360deg)} }
    .void-bubble { position:fixed;border-radius:50%;background:radial-gradient(circle at 30% 30%,rgba(100,0,200,0.2),rgba(50,0,150,0.1));animation:voidBubble linear infinite;pointer-events:none;z-index:3;box-shadow:inset 0 0 10px rgba(100,0,200,0.2); }
    @keyframes voidBubble { 0%{transform:translateY(100vh) scale(0.5);opacity:0}20%{opacity:0.6}80%{opacity:0.3}100%{transform:translateY(-50px) scale(1.2);opacity:0} }
    .deep-creature { position:fixed;font-size:26px;opacity:0;animation:deepCreep linear infinite;pointer-events:none;z-index:4; }
    @keyframes deepCreep { 0%{transform:translateY(0) translateX(0);opacity:0}20%{opacity:0.1}50%{transform:translateY(-30vh) translateX(20px)}80%{opacity:0.08}100%{transform:translateY(-60vh) translateX(-10px);opacity:0} }
    .tentacle { position:fixed;font-size:30px;opacity:0.08;pointer-events:none;z-index:3;animation:tentacleWave ease-in-out infinite; }
    @keyframes tentacleWave { 0%,100%{transform:rotate(-15deg) scaleY(1)}50%{transform:rotate(15deg) scaleY(1.05)} }
    .abyss-light { position:fixed;width:4px;height:4px;background:rgba(150,0,255,0.8);border-radius:50%;pointer-events:none;z-index:5;animation:abyssLightPulse ease-in-out infinite;box-shadow:0 0 8px rgba(150,0,255,0.6); }
    @keyframes abyssLightPulse { 0%,100%{opacity:0.1;transform:scale(0.6)}50%{opacity:1;transform:scale(1.8)} }
    .pressure-wave { position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:2;background:radial-gradient(ellipse at 50% 50%,rgba(0,0,50,0.3) 0%,transparent 60%);animation:pressurePulse 4s ease-in-out infinite; }
    @keyframes pressurePulse { 0%,100%{transform:scale(1)}50%{transform:scale(1.05)} }
    .vignette { position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:6;background:radial-gradient(ellipse at 50% 50%,transparent 25%,rgba(0,0,0,0.7) 100%); }
""",
        "body_divs": """
  <div class="vortex-aura"></div>
  <div class="pressure-wave"></div>
  <div id="voidBubbleContainer"></div>
  <div id="deepCreatureContainer"></div>
  <div id="tentacleContainer"></div>
  <div id="abyssLightContainer"></div>
  <div class="vignette"></div>""",
        "script": """
    // Abyss atmosphere
    const vbc = document.getElementById('voidBubbleContainer');
    for(let i=0;i<15;i++){const b=document.createElement('div');b.className='void-bubble';const s=Math.random()*30+10;b.style.width=b.style.height=s+'px';b.style.left=Math.random()*100+'%';b.style.animationDuration=(6+Math.random()*6)+'s';b.style.animationDelay=(Math.random()*6)+'s';vbc.appendChild(b);}
    const dcc = document.getElementById('deepCreatureContainer');
    const dcIcons = ['🦑','🐙','🕳️','🦈','🦑','👁️'];
    for(let i=0;i<6;i++){const d=document.createElement('div');d.className='deep-creature';d.textContent=dcIcons[i%dcIcons.length];d.style.left=(10+i*15)+'%';d.style.bottom=(10+Math.random()*20)+'%';d.style.animationDuration=(12+i*3)+'s';d.style.animationDelay=(i*4)+'s';d.style.fontSize=(22+Math.random()*10)+'px';dcc.appendChild(d);}
    const tc = document.getElementById('tentacleContainer');
    ['🐙','🦑','🐙'].forEach((icon,i)=>{const t=document.createElement('div');t.className='tentacle';t.textContent=icon;t.style.left=(8+i*30)+'%';t.style.bottom=(2+i*3)+'%';t.style.fontSize=(28+Math.random()*10)+'px';t.style.animationDuration=(3+Math.random()*2)+'s';t.style.animationDelay=(i*1.5)+'s';tc.appendChild(t);});
    const alc = document.getElementById('abyssLightContainer');
    for(let i=0;i<18;i++){const l=document.createElement('div');l.className='abyss-light';l.style.left=Math.random()*100+'%';l.style.top=Math.random()*80+'%';l.style.animationDuration=(1.5+Math.random()*2.5)+'s';l.style.animationDelay=(Math.random()*4)+'s';alc.appendChild(l);}
""",
    },
    "deepabyss.html": {
        "theme": "🌊 海底深渊",
        "css": """
    .deep-darkness { position:fixed;top:0;left:0;right:0;bottom:0;background:radial-gradient(ellipse at 50% 50%,rgba(0,0,20,0.4) 0%,rgba(0,0,0,0.8) 100%);pointer-events:none;z-index:1; }
    .abyss-vortex { position:fixed;top:50%;left:50%;width:180vmax;height:180vmax;transform:translate(-50%,-50%);background:conic-gradient(from 0deg,transparent,rgba(0,0,80,0.2),rgba(0,0,50,0.15),rgba(0,0,100,0.1),transparent);pointer-events:none;z-index:2;animation:abyssVortexSpin 30s linear infinite;border-radius:50%; }
    @keyframes abyssVortexSpin { 0%{transform:translate(-50%,-50%) rotate(0deg)}100%{transform:translate(-50%,-50%) rotate(-360deg)} }
    .biolum { position:fixed;width:4px;height:4px;background:radial-gradient(circle,rgba(0,200,255,0.9),rgba(0,100,200,0.3));border-radius:50%;pointer-events:none;z-index:5;animation:biolumPulse ease-in-out infinite;box-shadow:0 0 8px rgba(0,200,255,0.7),0 0 15px rgba(0,150,255,0.4); }
    @keyframes biolumPulse { 0%,100%{opacity:0.15;transform:scale(0.7)}50%{opacity:1;transform:scale(1.6)} }
    .leviathan { position:fixed;font-size:50px;opacity:0;animation:leviathanGlide linear infinite;pointer-events:none;z-index:4; }
    @keyframes leviathanGlide { 0%{transform:translateX(-120px) translateY(0) rotate(-5deg);opacity:0}15%{opacity:0.1}85%{opacity:0.08}100%{transform:translateX(calc(100vw + 120px)) translateY(-50px) rotate(5deg);opacity:0} }
    .pressure-fish { position:fixed;font-size:22px;opacity:0;animation:pressureFish linear infinite;pointer-events:none;z-index:4; }
    @keyframes pressureFish { 0%{transform:translateY(0) translateX(0);opacity:0}20%{opacity:0.12}80%{opacity:0.1}100%{transform:translateY(-40px) translateX(15px);opacity:0} }
    .bone { position:fixed;font-size:18px;opacity:0.06;pointer-events:none;z-index:3;animation:boneDrift linear infinite; }
    @keyframes boneDrift { 0%{transform:translateY(100vh) rotate(0deg);opacity:0}20%{opacity:0.06}80%{opacity:0.05}100%{transform:translateY(-30px) rotate(180deg);opacity:0} }
    .vignette { position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:6;background:radial-gradient(ellipse at 50% 50%,transparent 15%,rgba(0,0,0,0.85) 100%); }
""",
        "body_divs": """
  <div class="deep-darkness"></div>
  <div class="abyss-vortex"></div>
  <div id="biolumContainer"></div>
  <div id="leviathanContainer"></div>
  <div id="pressureFishContainer"></div>
  <div id="boneContainer"></div>
  <div class="vignette"></div>""",
        "script": """
    // Deep abyss atmosphere
    const bioC = document.getElementById('biolumContainer');
    for(let i=0;i<25;i++){const b=document.createElement('div');b.className='biolum';b.style.left=Math.random()*100+'%';b.style.top=Math.random()*80+'%';b.style.animationDuration=(1.5+Math.random()*3)+'s';b.style.animationDelay=(Math.random()*5)+'s';bioC.appendChild(b);}
    const levC = document.getElementById('leviathanContainer');
    ['🐋','🦈','🦑'].forEach((icon,i)=>{const l=document.createElement('div');l.className='leviathan';l.textContent=icon;l.style.top=(15+i*25)+'%';l.style.animationDuration=(60+i*25)+'s';l.style.animationDelay=(i*30)+'s';l.style.fontSize=(40+i*15)+'px';levC.appendChild(l);});
    const pfc = document.getElementById('pressureFishContainer');
    const pfIcons = ['🐟','🦈','🐡','🦑','🐙','🐟'];
    for(let i=0;i<8;i++){const p=document.createElement('div');p.className='pressure-fish';p.textContent=pfIcons[i%pfIcons.length];p.style.left=(5+i*12)+'%';p.style.bottom=(10+Math.random()*25)+'%';p.style.animationDuration=(10+i*3)+'s';p.style.animationDelay=(i*3)+'s';p.style.fontSize=(16+Math.random()*10)+'px';pfc.appendChild(p);}
    const boneC = document.getElementById('boneContainer');
    ['🦴','💀','🦴'].forEach((icon,i)=>{const b=document.createElement('div');b.className='bone';b.textContent=icon;b.style.left=(10+i*28)+'%';b.style.fontSize=(16+Math.random()*8)+'px';b.style.animationDuration=(12+Math.random()*8)+'s';b.style.animationDelay=(i*4)+'s';boneC.appendChild(b);});
""",
    },
    "worldboss.html": {
        "theme": "👹 世界BOSS",
        "css": """
    .boss-aura { position:fixed;top:0;left:0;right:0;bottom:0;background:radial-gradient(ellipse at 50% 60%,rgba(200,0,0,0.15) 0%,transparent 55%),radial-gradient(ellipse at 30% 80%,rgba(150,0,0,0.1) 0%,transparent 45%),radial-gradient(ellipse at 70% 80%,rgba(180,0,0,0.12) 0%,transparent 50%);pointer-events:none;z-index:1;animation:bossAura 3s ease-in-out infinite; }
    @keyframes bossAura { 0%,100%{opacity:0.6}50%{opacity:1} }
    .boss-ember { position:fixed;width:5px;height:5px;background:#ff3300;border-radius:50%;pointer-events:none;z-index:4;animation:bossEmber linear infinite;box-shadow:0 0 8px #ff2200; }
    @keyframes bossEmber { 0%{transform:translateY(0) translateX(0);opacity:1}100%{transform:translateY(-100px) translateX(25px);opacity:0} }
    .boss-smoke { position:fixed;font-size:26px;opacity:0;animation:bossSmoke linear infinite;pointer-events:none;z-index:3; }
    @keyframes bossSmoke { 0%{transform:translateY(0) scale(0.5);opacity:0}20%{opacity:0.3}80%{opacity:0.15}100%{transform:translateY(-120px) scale(1.5);opacity:0} }
    .boss-rune { position:fixed;font-size:20px;opacity:0;animation:bossRune ease-in-out infinite;pointer-events:none;z-index:4;color:rgba(255,50,0,0.5); }
    @keyframes bossRune { 0%,100%{opacity:0;transform:scale(0.5) rotate(0deg)}50%{opacity:0.4;transform:scale(1.3) rotate(180deg)} }
    .boss-ground-glow { position:fixed;bottom:0;left:0;right:0;height:8px;background:linear-gradient(90deg,transparent,rgba(200,0,0,0.5),rgba(255,50,0,0.7),rgba(200,0,0,0.5),transparent);pointer-events:none;z-index:2;animation:groundGlow 2s linear infinite; }
    @keyframes groundGlow { 0%{transform:scaleX(0.2);opacity:0.3}50%{transform:scaleX(0.9);opacity:0.8}100%{transform:scaleX(0.2);opacity:0.3} }
    .boss-lightning { position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:5;opacity:0; }
    .boss-lightning.flash { animation:bossLightning 0.3s ease-out; }
    @keyframes bossLightning { 0%{opacity:0;background:transparent}10%{opacity:1;background:rgba(255,200,100,0.1)}20%{opacity:0.2}30%{opacity:0.8;background:rgba(255,200,100,0.15)}100%{opacity:0} }
    .vignette { position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:6;background:radial-gradient(ellipse at 50% 50%,transparent 35%,rgba(0,0,0,0.65) 100%); }
""",
        "body_divs": """
  <div class="boss-aura"></div>
  <div class="boss-ground-glow"></div>
  <div class="boss-lightning" id="bossLightning"></div>
  <div id="bossEmberContainer"></div>
  <div id="bossSmokeContainer"></div>
  <div id="bossRuneContainer"></div>
  <div class="vignette"></div>""",
        "script": """
    // World boss atmosphere
    const bec = document.getElementById('bossEmberContainer');
    for(let i=0;i<20;i++){const e=document.createElement('div');e.className='boss-ember';e.style.left=Math.random()*100+'%';e.style.bottom=(Math.random()*30)+'%';e.style.animationDuration=(1.5+Math.random()*2)+'s';e.style.animationDelay=(Math.random()*4)+'s';bec.appendChild(e);}
    const bsc = document.getElementById('bossSmokeContainer');
    ['☁️','💨','🌫️','🔥'].forEach((icon,i)=>{const s=document.createElement('div');s.className='boss-smoke';s.textContent=icon;s.style.left=(8+i*20)+'%';s.style.bottom=(5+i*2)+'%';s.style.animationDuration=(4+Math.random()*3)+'s';s.style.animationDelay=(i*2.5)+'s';bsc.appendChild(s);});
    const brc = document.getElementById('bossRuneContainer');
    const runeIcons = ['☠️','⚡','👹','🔥','💀','⚡'];
    runeIcons.forEach((icon,i)=>{const r=document.createElement('div');r.className='boss-rune';r.textContent=icon;r.style.left=(5+i*15)+'%';r.style.top=(8+i*12)+'%';r.style.fontSize=(18+Math.random()*10)+'px';r.style.animationDuration=(3+Math.random()*3)+'s';r.style.animationDelay=(i*1.5)+'s';brc.appendChild(r);});
    const blEl = document.getElementById('bossLightning');
    function triggerBossLightning(){blEl.classList.remove('flash');void blEl.offsetWidth;blEl.classList.add('flash');}
    setInterval(()=>{if(Math.random()<0.25) triggerBossLightning();},5000);
""",
    },
    "arena.html": {
        "theme": "⚔️ 武道大会",
        "css": """
    .arena-glow { position:fixed;top:0;left:0;right:0;bottom:0;background:radial-gradient(ellipse at 50% 50%,rgba(100,60,0,0.15) 0%,transparent 55%);pointer-events:none;z-index:1;animation:arenaGlow 4s ease-in-out infinite; }
    @keyframes arenaGlow { 0%,100%{opacity:0.5}50%{opacity:0.9} }
    .dust { position:fixed;width:3px;height:3px;background:rgba(200,160,80,0.5);border-radius:50%;pointer-events:none;z-index:4;animation:dustFloat linear infinite; }
    @keyframes dustFloat { 0%{transform:translateY(100vh) rotate(0deg);opacity:0}20%{opacity:0.5}80%{opacity:0.3}100%{transform:translateY(-20px) rotate(180deg);opacity:0} }
    .torch { position:fixed;font-size:24px;opacity:0.15;pointer-events:none;z-index:3;animation:torchFlicker ease-in-out infinite; }
    @keyframes torchFlicker { 0%,100%{opacity:0.1;transform:scale(1)}50%{opacity:0.2;transform:scale(1.1)} }
    .crowd-silhouette { position:fixed;font-size:20px;opacity:0.08;pointer-events:none;z-index:2;animation:crowdCheer ease-in-out infinite; }
    @keyframes crowdCheer { 0%,100%{transform:scaleY(1)}50%{transform:scaleY(1.15)} }
    .sword-gleam { position:fixed;width:4px;height:4px;background:radial-gradient(circle,#ffd700,#ffaa00);border-radius:50%;pointer-events:none;z-index:5;animation:swordGleam ease-in-out infinite;box-shadow:0 0 8px #ffd700; }
    @keyframes swordGleam { 0%,100%{opacity:0.1;transform:scale(0.5) rotate(0deg)}50%{opacity:1;transform:scale(1.5) rotate(180deg)} }
    .arena-floor { position:fixed;bottom:0;left:0;right:0;height:8%;background:linear-gradient(180deg,transparent,rgba(120,80,0,0.1) 50%,rgba(100,60,0,0.2));pointer-events:none;z-index:2; }
    .flag-arena { position:fixed;font-size:26px;opacity:0.12;pointer-events:none;z-index:3;animation:flagArenaWave ease-in-out infinite; }
    @keyframes flagArenaWave { 0%,100%{transform:rotate(-8deg) scaleX(1)}50%{transform:rotate(8deg) scaleX(0.95)} }
    .applause-wave { position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:5;opacity:0;background:radial-gradient(ellipse at 50% 100%,rgba(255,200,100,0.05) 0%,transparent 60%);animation:applauseWave 5s ease-in-out infinite; }
    @keyframes applauseWave { 0%,100%{opacity:0}30%{opacity:1}70%{opacity:0.5} }
    .vignette { position:fixed;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:6;background:radial-gradient(ellipse at 50% 50%,transparent 40%,rgba(0,0,0,0.5) 100%); }
""",
        "body_divs": """
  <div class="arena-glow"></div>
  <div class="arena-floor"></div>
  <div class="applause-wave"></div>
  <div id="dustContainer"></div>
  <div id="torchContainer"></div>
  <div id="crowdContainer"></div>
  <div id="swordGleamContainer"></div>
  <div id="flagArenaContainer"></div>
  <div class="vignette"></div>""",
        "script": """
    // Arena atmosphere
    const dc = document.getElementById('dustContainer');
    for(let i=0;i<15;i++){const d=document.createElement('div');d.className='dust';d.style.left=Math.random()*100+'%';d.style.animationDuration=(4+Math.random()*5)+'s';d.style.animationDelay=(Math.random()*4)+'s';dc.appendChild(d);}
    const tc = document.getElementById('torchContainer');
    ['🔥','🔥','🏮','🔥'].forEach((icon,i)=>{const t=document.createElement('div');t.className='torch';t.textContent=icon;t.style.left=(8+i*22)+'%';t.style.top=(10+i*5)+'%';t.style.fontSize=(20+Math.random()*8)+'px';t.style.animationDuration=(0.5+Math.random()*1)+'s';t.style.animationDelay=(i*0.5)+'s';tc.appendChild(t);});
    const cc = document.getElementById('crowdContainer');
    ['👥','👏','👥','👏'].forEach((icon,i)=>{const c=document.createElement('div');c.className='crowd-silhouette';c.textContent=icon;c.style.left=(5+i*22)+'%';c.style.bottom=(8+i*3)+'%';c.style.fontSize=(18+Math.random()*8)+'px';c.style.animationDuration=(1.5+Math.random()*2)+'s';c.style.animationDelay=(i*1)+'s';cc.appendChild(c);});
    const sgc = document.getElementById('swordGleamContainer');
    for(let i=0;i<12;i++){const s=document.createElement('div');s.className='sword-gleam';s.style.left=Math.random()*100+'%';s.style.top=Math.random()*70+'%';s.style.animationDuration=(1.5+Math.random()*2.5)+'s';s.style.animationDelay=(Math.random()*4)+'s';sgc.appendChild(s);}
    const fac = document.getElementById('flagArenaContainer');
    ['⚔️','🏴','⚔️'].forEach((icon,i)=>{const f=document.createElement('div');f.className='flag-arena';f.textContent=icon;f.style.left=(8+i*28)+'%';f.style.top=(5+i*4)+'%';f.style.fontSize=(22+Math.random()*6)+'px';f.style.animationDuration=(2+Math.random()*1.5)+'s';f.style.animationDelay=(i*1.2)+'s';fac.appendChild(f);});
""",
    },
}

def inject_atmosphere(html_content, page_name, info):
    """Inject atmosphere elements into a page."""
    # 1. Add CSS before </style>
    css_end = html_content.find('</style>')
    if css_end == -1:
        print(f"  WARNING: No </style> found in {page_name}")
        return html_content
    
    css_block = f"\n    /* Atmosphere: {info['theme']} */\n" + info['css']
    html_content = html_content[:css_end] + css_block + html_content[css_end:]
    
    # 2. Add body divs after <body
    body_start = html_content.find('<body')
    if body_start == -1:
        print(f"  WARNING: No <body> found in {page_name}")
        return html_content
    
    body_tag_end = html_content.find('>', body_start)
    html_content = html_content[:body_tag_end+1] + '\n  ' + info['body_divs'] + html_content[body_tag_end+1:]
    
    # 3. Add JS before </script> of last script tag
    last_script = html_content.rfind('</script>')
    if last_script == -1:
        print(f"  WARNING: No </script> found in {page_name}")
        return html_content
    
    script_block = '\n' + info['script']
    html_content = html_content[:last_script] + script_block + '\n' + html_content[last_script:]
    
    return html_content


def main():
    base = '/root/.openclaw/workspace/games/deep_sea_odyssey/static/'
    for fname, info in PAGES.items():
        fpath = base + fname
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Skip if already has atmosphere class (avoid double injection)
            if 'Atmosphere: ' + info['theme'] in content or 'atmosphere-added' in content:
                print(f"SKIP {fname} - already has atmosphere")
                continue
            
            new_content = inject_atmosphere(content, fname, info)
            
            # Add marker and write
            marker = f'<!-- atmosphere-added: {info["theme"]} -->'
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(marker + '\n' + new_content)
            
            print(f"OK   {fname} - {info['theme']}")
        except Exception as e:
            print(f"ERR  {fname}: {e}")

if __name__ == '__main__':
    main()
