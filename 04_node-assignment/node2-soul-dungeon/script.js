const cv = document.getElementById('game');
const ctx = cv.getContext('2d');
const W = 480, H = 480;
ctx.imageSmoothingEnabled = false;

const WALL = 30;
const AREA = { x0: WALL, y0: WALL, x1: W - WALL, y1: H - WALL };
const DOORW = 66;

const keys = {};
const mouse = { x: W / 2, y: H / 2, down: false };

const BODY = ['#5aa9ff', '#ff6b6b', '#63d471', '#ffd76a', '#c77dff'];
const HATS = 4;
const MT = {
  0: { hp: 3, sp: 0.55, r: 10, shoot: true, fr: 1300, bs: 2.5, contact: false, name: '임프' },
  1: { hp: 6, sp: 0.4, r: 12, shoot: false, contact: true, name: '슬라임' },
  2: { hp: 2, sp: 1.15, r: 8, shoot: true, fr: 850, bs: 3.3, contact: false, name: '파리' },
  3: { hp: 10, sp: 0.28, r: 15, shoot: true, fr: 1500, bs: 2.2, contact: true, name: '골렘' }
};

let state = 'home', confirming = false;
let rooms = [], cur = 4, gold = 0, flash = 0;
let pbullets = [], mbullets = [], particles = [], popups = [];
const player = { x: W / 2, y: H - 90, r: 8, hp: 10, maxhp: 10, inv: 0, cd: 0, blink: 0, ci: 0, hat: 0, wcount: 1, wcd: 180 };

const PORTAL = { x: W / 2, y: 74, col: '#8b3bd6' };
const WARDROBE = { x: 78, y: 96 };
const TAILOR = { x: 404, y: 150, col: '#c77dff', name: '의류상인' };
const NPCS = [
  { x: 150, y: 384, col: '#c9a24a', name: '상인', line: '좋은 무기 있어요!' },
  { x: 330, y: 384, col: '#7a8291', name: '대장장이', line: '칼 갈아드립니다' }
];
const BTN_R = { x: W / 2 - 92, y: 244, w: 184, h: 40 };
const BTN_H = { x: W / 2 - 92, y: 296, w: 184, h: 40 };

function dist(a, b) { return Math.hypot(a.x - b.x, a.y - b.y); }
function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }
function inCanvas(b) { return b.x > -12 && b.x < W + 12 && b.y > -12 && b.y < H + 12; }
function hash(gx, gy) { let h = (gx * 374761393 + gy * 668265263) >>> 0; h = ((h ^ (h >> 13)) * 1274126177) >>> 0; return h >>> 0; }
function R() { return rooms[cur]; }
function rc(i) { return [(i / 3) | 0, i % 3]; }
function doorExists(i, s) { const [r, c] = rc(i); return s === 'N' ? r > 0 : s === 'S' ? r < 2 : s === 'W' ? c > 0 : c < 2; }
function locked() { const rm = R(); return (rm.type === 'combat' || rm.type === 'horde') && !rm.cleared; }
function openSide(s) { return doorExists(cur, s) && !locked(); }
function popup(x, y, t, c) { popups.push({ x, y, t, c, life: 900 }); }

function genDungeon() {
  rooms = [];
  for (let i = 0; i < 9; i++) rooms.push({ type: null, monsters: [], items: [], cleared: false, visited: false });
  rooms[4].type = 'start'; rooms[4].cleared = true;
  const pool = ['combat', 'combat', 'combat', 'combat', 'horde', 'potion', 'weapon', 'gold'];
  for (let k = pool.length - 1; k > 0; k--) { const j = Math.floor(Math.random() * (k + 1));[pool[k], pool[j]] = [pool[j], pool[k]]; }
  let pi = 0;
  for (let i = 0; i < 9; i++) { if (i === 4) continue; rooms[i].type = pool[pi++]; if (rooms[i].type !== 'combat' && rooms[i].type !== 'horde') rooms[i].cleared = true; }
  gold = 0; player.hp = player.maxhp; player.wcount = 1; player.wcd = 180;
  enterRoom(4, W / 2, H / 2);
  state = 'play';
}
function spawnMon(rm, n) {
  const pool = rm.type === 'horde' ? [2, 2, 0, 2, 0, 3] : [0, 1, 2, 0, 1];
  for (let k = 0; k < n; k++) {
    const t = pool[Math.floor(Math.random() * pool.length)], tm = MT[t];
    rm.monsters.push({ x: AREA.x0 + 40 + Math.random() * (AREA.x1 - AREA.x0 - 80), y: AREA.y0 + 40 + Math.random() * (AREA.y1 - AREA.y0 - 130), r: tm.r, hp: tm.hp, t, cd: 400 + Math.random() * 900, hurt: 0 });
  }
}
function enterRoom(i, px, py) {
  cur = i; const rm = rooms[i];
  player.x = px; player.y = py; player.inv = Math.max(player.inv, 350);
  pbullets = []; mbullets = []; particles = [];
  if (!rm.visited) {
    rm.visited = true;
    if (rm.type === 'combat') spawnMon(rm, 2 + Math.floor(Math.random() * 2));
    else if (rm.type === 'horde') spawnMon(rm, 6);
    else if (rm.type === 'potion') rm.items.push({ x: W / 2, y: H / 2, kind: 'potion' });
    else if (rm.type === 'weapon') rm.items.push({ x: W / 2, y: H / 2, kind: 'weapon' });
    else if (rm.type === 'gold') for (let k = 0; k < 6; k++) rm.items.push({ x: AREA.x0 + 70 + Math.random() * (AREA.x1 - AREA.x0 - 140), y: AREA.y0 + 70 + Math.random() * (AREA.y1 - AREA.y0 - 140), kind: 'gold' });
  }
}
function goHome() { state = 'home'; confirming = false; player.x = W / 2; player.y = H - 90; player.blink = 0; player.inv = 0; player.hp = player.maxhp; }
function checkClear() { for (const rm of rooms) if ((rm.type === 'combat' || rm.type === 'horde') && !rm.cleared) return false; return true; }
function hurtPlayer() { if (player.inv > 0) return; player.hp--; player.inv = 430; player.blink = 430; flash = 160; burst(player.x, player.y, '#ffd76a'); }

window.addEventListener('keydown', e => {
  const k = e.key.toLowerCase(), was = keys[k];
  keys[k] = true;
  if (['arrowup', 'arrowdown', 'arrowleft', 'arrowright', ' '].includes(k)) e.preventDefault();
  if (k === 'enter') { if (state === 'home') { confirming = false; genDungeon(); } else if (state === 'clear' || state === 'over') goHome(); }
  if (k === 'escape') { if (state === 'play') state = 'pause'; else if (state === 'pause') state = 'play'; else if (state === 'home' && confirming) confirming = false; }
  if (k === ' ' && !was && state === 'home' && !confirming) {
    if (dist(player, WARDROBE) < 40) { player.ci = (player.ci + 1) % BODY.length; popup(WARDROBE.x, WARDROBE.y - 30, '색 변경', '#ffd76a'); }
    else if (dist(player, TAILOR) < 44) { player.hat = (player.hat + 1) % HATS; popup(TAILOR.x, TAILOR.y - 30, '모자 변경', '#ffd76a'); }
    else if (dist(player, PORTAL) < 46) { confirming = true; }
    else { const n = NPCS.find(nn => dist(player, nn) < 46); if (n) popup(n.x, n.y - 30, n.line, '#f4eede'); }
  }
});
window.addEventListener('keyup', e => { keys[e.key.toLowerCase()] = false; });
function toGame(ev) { const r = cv.getBoundingClientRect(); mouse.x = (ev.clientX - r.left) / r.width * W; mouse.y = (ev.clientY - r.top) / r.height * H; }
cv.addEventListener('mousemove', toGame);
cv.addEventListener('mousedown', ev => {
  toGame(ev);
  if (state === 'home' && confirming) { if (hit(BTN_R)) { confirming = false; genDungeon(); } else if (hit(BTN_H)) confirming = false; return; }
  if (state === 'pause') { if (hit(BTN_R)) state = 'play'; else if (hit(BTN_H)) goHome(); return; }
  if (state === 'clear' || state === 'over') { goHome(); return; }
  if (state === 'play') mouse.down = true;
});
window.addEventListener('mouseup', () => { mouse.down = false; });
function hit(b) { return mouse.x >= b.x && mouse.x <= b.x + b.w && mouse.y >= b.y && mouse.y <= b.y + b.h; }

function movePlayer(dt, home) {
  let dx = 0, dy = 0;
  if (keys['a'] || keys['arrowleft']) dx--;
  if (keys['d'] || keys['arrowright']) dx++;
  if (keys['w'] || keys['arrowup']) dy--;
  if (keys['s'] || keys['arrowdown']) dy++;
  if (dx || dy) { const l = Math.hypot(dx, dy), sp = 2.7 * dt / 16; player.x += dx / l * sp; player.y += dy / l * sp; }
  const cx = W / 2, cy = H / 2;
  const n = !home && openSide('N') && Math.abs(player.x - cx) < DOORW / 2 - 2;
  const s = !home && openSide('S') && Math.abs(player.x - cx) < DOORW / 2 - 2;
  const w = !home && openSide('W') && Math.abs(player.y - cy) < DOORW / 2 - 2;
  const e = !home && openSide('E') && Math.abs(player.y - cy) < DOORW / 2 - 2;
  player.x = clamp(player.x, w ? AREA.x0 - 26 : AREA.x0 + player.r, e ? AREA.x1 + 26 : AREA.x1 - player.r);
  player.y = clamp(player.y, n ? AREA.y0 - 26 : AREA.y0 + player.r, s ? AREA.y1 + 26 : AREA.y1 - player.r);
}
function tryTransition() {
  if (locked()) return;
  const cx = W / 2, cy = H / 2, m = DOORW / 2;
  if (openSide('N') && player.y < AREA.y0 - 6 && Math.abs(player.x - cx) < m) enterRoom(cur - 3, cx, AREA.y1 - 26);
  else if (openSide('S') && player.y > AREA.y1 + 6 && Math.abs(player.x - cx) < m) enterRoom(cur + 3, cx, AREA.y0 + 26);
  else if (openSide('W') && player.x < AREA.x0 - 6 && Math.abs(player.y - cy) < m) enterRoom(cur - 1, AREA.x1 - 26, cy);
  else if (openSide('E') && player.x > AREA.x1 + 6 && Math.abs(player.y - cy) < m) enterRoom(cur + 1, AREA.x0 + 26, cy);
}
function shoot() {
  const a = Math.atan2(mouse.y - player.y, mouse.x - player.x), n = player.wcount;
  for (let i = 0; i < n; i++) { const off = (i - (n - 1) / 2) * 0.16; pbullets.push({ x: player.x, y: player.y, vx: Math.cos(a + off) * 6.6, vy: Math.sin(a + off) * 6.6, r: 3 }); }
}
function burst(x, y, c) { for (let i = 0; i < 8; i++) { const a = Math.random() * 6.28, s = 1 + Math.random() * 2.5; particles.push({ x, y, vx: Math.cos(a) * s, vy: Math.sin(a) * s, life: 300, c }); } }

function update(dt) {
  flash = Math.max(0, flash - dt);
  for (const p of particles) { p.x += p.vx * dt / 16; p.y += p.vy * dt / 16; p.life -= dt; }
  particles = particles.filter(p => p.life > 0);
  for (const p of popups) { p.y -= 0.3 * dt / 16; p.life -= dt; }
  popups = popups.filter(p => p.life > 0);

  if (state === 'home') {
    if (!confirming) movePlayer(dt, true);
    return;
  }
  if (state !== 'play') return;
  const rm = R();
  player.inv = Math.max(0, player.inv - dt); player.cd -= dt; if (player.blink > 0) player.blink -= dt;
  movePlayer(dt, false); tryTransition();
  if (mouse.down && player.cd <= 0) { shoot(); player.cd = player.wcd; }
  for (const b of pbullets) { b.x += b.vx * dt / 16; b.y += b.vy * dt / 16; }
  for (const b of mbullets) { b.x += b.vx * dt / 16; b.y += b.vy * dt / 16; }

  for (const m of rm.monsters) {
    const tm = MT[m.t]; if (m.hurt > 0) m.hurt -= dt;
    const d = dist(player, m) || 1;
    if (tm.contact) {
      m.x += (player.x - m.x) / d * tm.sp * dt / 16; m.y += (player.y - m.y) / d * tm.sp * dt / 16;
      if (d < player.r + m.r) hurtPlayer();
    } else if (d > 100) { m.x += (player.x - m.x) / d * tm.sp * dt / 16; m.y += (player.y - m.y) / d * tm.sp * dt / 16; }
    if (tm.shoot) { m.cd -= dt; if (m.cd <= 0) { m.cd = tm.fr + Math.random() * 400; const a = Math.atan2(player.y - m.y, player.x - m.x); mbullets.push({ x: m.x, y: m.y, vx: Math.cos(a) * tm.bs, vy: Math.sin(a) * tm.bs, r: 4 }); } }
    m.x = clamp(m.x, AREA.x0 + m.r, AREA.x1 - m.r); m.y = clamp(m.y, AREA.y0 + m.r, AREA.y1 - m.r);
  }
  pbullets = pbullets.filter(b => {
    for (const m of rm.monsters) if (dist(b, m) < m.r + b.r) {
      m.hp--; m.hurt = 120;
      if (m.hp <= 0) { m.dead = true; burst(m.x, m.y, MT[m.t].contact ? '#63d471' : '#ff5b7a'); if (Math.random() < 0.35) rm.items.push({ x: m.x, y: m.y, kind: 'gold' }); }
      return false;
    }
    return inCanvas(b);
  });
  rm.monsters = rm.monsters.filter(m => !m.dead);
  mbullets = mbullets.filter(b => { if (player.inv <= 0 && dist(b, player) < player.r + b.r) { hurtPlayer(); return false; } return inCanvas(b); });

  rm.items = rm.items.filter(it => {
    if (dist(player, it) < 15) {
      if (it.kind === 'potion') { player.hp = Math.min(player.maxhp, player.hp + 4); popup(player.x, player.y - 14, '+HP', '#ff4b6a'); }
      else if (it.kind === 'weapon') { if (player.wcount < 3) player.wcount++; else player.wcd = Math.max(90, player.wcd - 30); popup(player.x, player.y - 14, '무기 강화!', '#5aa9ff'); }
      else { gold += 10; popup(player.x, player.y - 14, '+10', '#ffd76a'); }
      return false;
    }
    return true;
  });

  if ((rm.type === 'combat' || rm.type === 'horde') && rm.monsters.length === 0 && !rm.cleared) {
    rm.cleared = true; popup(W / 2, 60, '방 클리어!', '#63d471');
    if (checkClear()) state = 'clear';
  }
  if (player.hp <= 0) state = 'over';
}

function px(x, y, s, c) { ctx.fillStyle = c; ctx.fillRect(Math.round(x), Math.round(y), s, s); }
function label(x, y, t, c, sz) { ctx.fillStyle = c || '#d7cfff'; ctx.font = (sz || 11) + 'px monospace'; ctx.textAlign = 'center'; ctx.fillText(t, x, y); ctx.textAlign = 'left'; }
function drawFloor(base, alt, grout, deco) {
  const T = 24;
  for (let gy = AREA.y0; gy < AREA.y1; gy += T) for (let gx = AREA.x0; gx < AREA.x1; gx += T) {
    const h = hash(gx, gy); ctx.fillStyle = (h & 1) ? base : alt;
    ctx.fillRect(gx, gy, Math.min(T, AREA.x1 - gx), Math.min(T, AREA.y1 - gy));
    ctx.fillStyle = grout; ctx.fillRect(gx, gy, Math.min(T, AREA.x1 - gx), 1); ctx.fillRect(gx, gy, 1, Math.min(T, AREA.y1 - gy));
    const d = h % 19;
    if (d === 0) { px(gx + 5 + (h >> 4) % 10, gy + 6 + (h >> 8) % 9, 2, grout); px(gx + 8 + (h >> 5) % 8, gy + 10 + (h >> 9) % 7, 2, grout); }
    else if (d === 1) px(gx + 9 + (h >> 5) % 6, gy + 8 + (h >> 9) % 8, 3, deco);
  }
}
function drawWalls() {
  const bands = [[0, 0, W, WALL], [0, H - WALL, W, WALL], [0, 0, WALL, H], [W - WALL, 0, WALL, H]];
  ctx.fillStyle = '#241c38'; for (const [x, y, w, h] of bands) ctx.fillRect(x, y, w, h);
  const bw = 30, bh = 15;
  for (const [x, y, w, h] of bands) for (let by = y; by < y + h; by += bh) { const off = (((by / bh) | 0) % 2) ? bw / 2 : 0; for (let bx = x + off - bw; bx < x + w; bx += bw) { ctx.fillStyle = ((bx + by) & 16) ? '#4a3d6b' : '#453960'; ctx.fillRect(bx + 1, by + 1, bw - 2, bh - 2); } }
}
function drawDoors() {
  const sides = [['N', W / 2 - DOORW / 2, 0, DOORW, WALL], ['S', W / 2 - DOORW / 2, H - WALL, DOORW, WALL], ['W', 0, H / 2 - DOORW / 2, WALL, DOORW], ['E', W - WALL, H / 2 - DOORW / 2, WALL, DOORW]];
  for (const [s, x, y, w, h] of sides) {
    if (!doorExists(cur, s)) continue;
    if (locked()) { ctx.fillStyle = '#2a2138'; ctx.fillRect(x, y, w, h); ctx.fillStyle = '#c04040'; if (s === 'N' || s === 'S') ctx.fillRect(x + 4, y + h / 2 - 2, w - 8, 4); else ctx.fillRect(x + w / 2 - 2, y + 4, 4, h - 8); }
    else { ctx.fillStyle = '#151021'; ctx.fillRect(x, y, w, h); ctx.fillStyle = '#ffd76a'; if (s === 'N') ctx.fillRect(x, WALL - 3, w, 3); if (s === 'S') ctx.fillRect(x, H - WALL, w, 3); if (s === 'W') ctx.fillRect(WALL - 3, y, 3, h); if (s === 'E') ctx.fillRect(W - WALL, y, 3, h); }
  }
}
function torch(x, y) { px(x - 2, y, 4, '#5a3a22'); const f = Math.floor(Date.now() / 140) % 2; px(x - 2, y - 6 - f, 4, '#ff8a3c'); px(x - 1, y - 9 - f, 2, '#ffd76a'); }
function ring(x, y, col) { const t = Date.now() / 300, pr = 15 + Math.sin(t) * 2.5; for (let i = 0; i < 3; i++) { ctx.strokeStyle = [col, '#5aa9ff', '#ffd76a'][i]; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x, y, pr - i * 4, 0, 6.28); ctx.stroke(); } }

function drawHat(x, y) {
  if (player.hat === 1) { px(x - 6, y - 14, 2, '#c0392b'); px(x + 4, y - 14, 2, '#c0392b'); px(x - 6, y - 16, 2, '#e05a44'); px(x + 4, y - 16, 2, '#e05a44'); }
  else if (player.hat === 2) { px(x - 6, y - 13, 12, '#2f6e4a'); px(x - 6, y - 15, 12, '#3f9e5f'); }
  else if (player.hat === 3) { px(x - 5, y - 13, 10, '#ffd76a'); px(x - 5, y - 16, 2, '#ffd76a'); px(x - 1, y - 17, 2, '#ffe89a'); px(x + 3, y - 16, 2, '#ffd76a'); }
}
function drawPlayer() {
  if (state === 'play' && player.blink > 0 && Math.floor(player.blink / 80) % 2 === 0) return;
  const x = player.x, y = player.y, c = BODY[player.ci];
  px(x - 5, y - 10, 10, '#3a2f52'); px(x - 4, y - 9, 8, '#5b6b8a');
  px(x - 4, y - 5, 8, '#ffe0b8'); px(x - 4, y - 4, 2, '#12101a'); px(x + 2, y - 4, 2, '#12101a');
  px(x - 5, y, 10, c); px(x - 5, y, 2, '#ffffff33');
  px(x - 4, y + 6, 3, '#2a2138'); px(x + 1, y + 6, 3, '#2a2138');
  drawHat(x, y);
  const a = Math.atan2(mouse.y - y, mouse.x - x);
  px(x + Math.cos(a) * 9 - 1.5, y + Math.sin(a) * 9 - 1.5, 5, '#cfd3e0'); px(x + Math.cos(a) * 12 - 1, y + Math.sin(a) * 12 - 1, 3, '#8890a5');
}
function drawMonster(m) {
  const x = m.x, y = m.y, hurt = m.hurt > 0, t = m.t;
  if (t === 0) { const c = hurt ? '#fff' : '#8b3bd6'; px(x - 7, y - 7, 14, c); px(x - 8, y - 4, 3, c); px(x + 6, y - 4, 3, c); px(x - 5, y - 4, 4, '#fff'); px(x + 2, y - 4, 4, '#fff'); px(x - 4, y - 3, 2, '#12101a'); px(x + 3, y - 3, 2, '#12101a'); px(x - 4, y + 4, 3, '#5a2d82'); px(x + 2, y + 4, 3, '#5a2d82'); }
  else if (t === 1) { const c = hurt ? '#fff' : '#2f9e5f'; px(x - 8, y - 5, 16, c); px(x - 6, y - 9, 12, c); px(x - 4, y - 3, 3, '#fff'); px(x + 2, y - 3, 3, '#fff'); px(x - 3, y - 2, 2, '#12101a'); px(x + 3, y - 2, 2, '#12101a'); px(x - 4, y + 5, 8, '#1d6e42'); }
  else if (t === 2) { const c = hurt ? '#fff' : '#ff6b6b'; px(x - 5, y - 5, 10, c); px(x - 8, y - 6, 3, '#ffb0b0'); px(x + 5, y - 6, 3, '#ffb0b0'); px(x - 3, y - 3, 2, '#12101a'); px(x + 1, y - 3, 2, '#12101a'); }
  else { const c = hurt ? '#fff' : '#7a6a4a'; px(x - 9, y - 9, 18, c); px(x - 9, y - 9, 18, hurt ? '#fff' : '#8a7a58'); px(x - 6, y - 5, 4, '#ffd76a'); px(x + 2, y - 5, 4, '#ffd76a'); px(x - 5, y - 4, 2, '#12101a'); px(x + 3, y - 4, 2, '#12101a'); px(x - 7, y + 5, 5, '#5a4d34'); px(x + 2, y + 5, 5, '#5a4d34'); }
}
function drawItem(it) {
  const x = it.x, y = it.y, b = Math.sin(Date.now() / 300) * 2;
  if (it.kind === 'potion') { px(x - 4, y - 6 + b, 8, '#ff4b6a'); px(x - 3, y - 8 + b, 6, '#7a8291'); px(x - 2, y - 4 + b, 4, '#ff8aa0'); }
  else if (it.kind === 'weapon') { px(x - 1, y - 8 + b, 3, '#cfd3e0'); px(x - 4, y + 2 + b, 9, '#8a6236'); px(x - 1, y - 8 + b, 3, '#fff'); }
  else { px(x - 4, y - 4 + b, 8, '#ffd76a'); px(x - 3, y - 3 + b, 2, '#fff5c0'); px(x - 4, y - 4 + b, 8, '#e0b84a'); px(x - 3, y - 3 + b, 4, '#ffe89a'); }
}
function drawNPC(n) {
  px(n.x - 5, n.y - 12, 10, '#3a2f52'); px(n.x - 4, n.y - 8, 8, '#ffe0b8'); px(n.x - 4, n.y - 3, 8, n.col); px(n.x - 4, n.y + 3, 3, '#2a2138'); px(n.x + 1, n.y + 3, 3, '#2a2138');
  label(n.x, n.y + 20, n.name, '#9d97b8');
  if (dist(player, n) < 46) label(n.x, n.y - 20, 'SPACE', '#ffd76a', 10);
}
function drawWardrobe() {
  px(WARDROBE.x - 12, WARDROBE.y - 16, 24, '#6b4a2a'); px(WARDROBE.x - 10, WARDROBE.y - 14, 20, '#8a6236'); px(WARDROBE.x - 1, WARDROBE.y - 14, 2, '#4a2f18');
  px(WARDROBE.x - 22, WARDROBE.y - 4, 6, BODY[player.ci]);
  label(WARDROBE.x, WARDROBE.y + 22, '옷장(색)', '#9d97b8');
  if (dist(player, WARDROBE) < 40) label(WARDROBE.x, WARDROBE.y - 26, 'SPACE: 색', '#ffd76a');
}
function drawFurniture() {
  px(300, 300, 18, '#6b4a2a'); px(302, 302, 14, '#8a6236'); px(305, 300, 8, '#5a3a22'); px(322, 302, 14, '#6b4a2a'); px(324, 304, 10, '#8a6236');
  px(160, 250, 16, '#2f6e4a'); px(163, 245, 4, '#3f9e5f'); px(169, 244, 4, '#3f9e5f'); px(166, 248, 4, '#4fbf6f');
  torch(WALL + 8, 190); torch(W - WALL - 8, 190); torch(WALL + 8, 340); torch(W - WALL - 8, 340);
}
function drawMinimap() {
  const s = 16, ox = W - WALL - s * 3 - 6, oy = WALL + 6;
  ctx.fillStyle = 'rgba(10,8,18,0.62)'; ctx.fillRect(ox - 4, oy - 4, s * 3 + 8, s * 3 + 12); label(ox + s * 1.5, oy - 6, 'MAP', '#9d97b8', 10);
  for (let i = 0; i < 9; i++) {
    const rm = rooms[i], mx = ox + (i % 3) * s, my = oy + ((i / 3 | 0)) * s;
    let col = '#221c31'; if (rm.visited) col = rm.cleared ? '#3b6d55' : '#7a3b3b'; if (i === cur) col = '#ffd76a';
    ctx.fillStyle = col; ctx.fillRect(mx + 1, my + 1, s - 2, s - 2); ctx.strokeStyle = '#4a3d6b'; ctx.lineWidth = 1; ctx.strokeRect(mx + 1, my + 1, s - 2, s - 2);
    if (rm.visited && i !== cur) { const mk = { potion: '#63d471', weapon: '#5aa9ff', gold: '#ffd76a' }[rm.type]; if (mk) px(mx + s / 2 - 1.5, my + s / 2 - 1.5, 4, mk); }
  }
}
function drawHUD() {
  for (let i = 0; i < player.maxhp; i++) px(8 + i * 12, 9, 9, i < player.hp ? '#ff4b6a' : '#3a2f52');
  ctx.fillStyle = '#ffd76a'; ctx.font = '12px monospace'; ctx.textAlign = 'left'; ctx.fillText('◆ ' + gold, 10, 36);
  ctx.fillStyle = '#5aa9ff'; ctx.fillText('WPN ×' + player.wcount, 76, 36);
}
function drawBtn(b, t) { ctx.fillStyle = hit(b) ? '#3a3358' : '#2a2340'; ctx.fillRect(b.x, b.y, b.w, b.h); ctx.strokeStyle = '#6b5a9a'; ctx.lineWidth = 2; ctx.strokeRect(b.x, b.y, b.w, b.h); label(b.x + b.w / 2, b.y + b.h / 2 + 5, t, '#e8e6f0', 15); }
function overlay(a) { ctx.fillStyle = 'rgba(10,8,18,' + a + ')'; ctx.fillRect(0, 0, W, H); }
function center(lines) { for (const [t, y, s, c] of lines) label(W / 2, y, t, c, s); }
function drawPop() { for (const p of popups) label(p.x, p.y, p.t, p.c, 12); }

function render() {
  ctx.fillStyle = '#151021'; ctx.fillRect(0, 0, W, H);
  if (state === 'home') {
    drawFloor('#3a3348', '#352f43', '#241c38', '#4a4258');
    ctx.fillStyle = '#6b3a4a'; ctx.fillRect(196, 210, 88, 66); ctx.fillStyle = '#7a4657'; ctx.fillRect(200, 214, 80, 58);
    drawWalls(); drawFurniture(); drawWardrobe();
    for (const n of NPCS) drawNPC(n);
    drawNPC({ x: TAILOR.x, y: TAILOR.y, col: TAILOR.col, name: '의류상인' });
    ring(PORTAL.x, PORTAL.y, PORTAL.col); label(PORTAL.x, PORTAL.y + 26, '던전', '#ffd76a');
    if (dist(player, PORTAL) < 46 && !confirming) label(PORTAL.x, PORTAL.y - 24, 'SPACE: 입장', '#ffd76a', 10);
    drawPlayer(); drawPop();
    ctx.fillStyle = '#ffd76a'; ctx.font = '20px monospace'; ctx.textAlign = 'center'; ctx.fillText('◈ 홈 ◈', W / 2, 52); ctx.textAlign = 'left';
    label(W / 2, H - 12, 'SPACE로 상호작용 · 옷장=색 · 의류상인=모자', '#9d97b8', 10);
    if (confirming) { overlay(0.72); center([['던전으로 들어갈까요?', 214, 20, '#ffd76a']]); drawBtn(BTN_R, '예 (Enter)'); drawBtn(BTN_H, '아니오 (ESC)'); }
    return;
  }
  const rm = R();
  const theme = { combat: ['#2e2742', '#2a2340', '#171226', '#3a3352'], horde: ['#3a2230', '#331e2a', '#1a0f16', '#4a2d3a'], potion: ['#233a30', '#1f342a', '#12261c', '#2f5040'], weapon: ['#233246', '#1f2c3e', '#121e2c', '#2f4460'], gold: ['#3a3322', '#332e1e', '#1a1610', '#4a4228'], start: ['#2e2742', '#2a2340', '#171226', '#3a3352'] }[rm.type];
  drawFloor(theme[0], theme[1], theme[2], theme[3]);
  drawWalls(); drawDoors();
  for (const it of rm.items) drawItem(it);
  drawParticlesAndBullets(rm);
  drawPlayer(); drawMinimap(); drawHUD(); drawPop();
  if (flash > 0) { ctx.fillStyle = 'rgba(255,60,80,' + (flash / 500) + ')'; ctx.fillRect(0, 0, W, H); }
  const tn = { start: '시작 방', combat: '전투 방', horde: '몬스터 소굴', potion: '포션 방', weapon: '무기 방', gold: '보물 방' }[rm.type];
  label(W / 2, WALL + 14, tn, locked() ? '#ff8a8a' : '#9d97b8', 11);
  if (locked()) label(W / 2, WALL + 30, '몬스터를 처치하면 문이 열립니다', '#ff8a8a', 10);
  if (state === 'pause') { overlay(0.8); center([['일시정지', 200, 24, '#ffd76a']]); drawBtn(BTN_R, '계속하기'); drawBtn(BTN_H, '홈으로 (포기)'); label(W / 2, 360, 'ESC: 계속', '#9d97b8', 10); }
  if (state === 'clear') { overlay(0.78); center([['★ STAGE CLEAR ★', 200, 26, '#ffd76a'], ['모든 전투 방을 정복했습니다 · ◆' + gold, 240, 13, '#d7cfff'], ['Enter : 홈으로', 290, 14, '#9d97b8']]); }
  if (state === 'over') { overlay(0.78); center([['GAME OVER', 200, 30, '#ff4b6a'], ['◆' + gold + ' 획득', 240, 13, '#d7cfff'], ['Enter : 홈으로', 290, 14, '#9d97b8']]); }
}
function drawParticlesAndBullets(rm) {
  for (const p of particles) px(p.x - 1, p.y - 1, 3, p.c);
  for (const b of pbullets) { px(b.x - 2, b.y - 2, 5, '#ffe15a'); px(b.x - 1, b.y - 1, 3, '#fff'); }
  for (const b of mbullets) { px(b.x - 2, b.y - 2, 5, '#ff5bce'); px(b.x - 1, b.y - 1, 3, '#ffd0ee'); }
  for (const m of rm.monsters) drawMonster(m);
}

let last = performance.now();
function loop(now) { const dt = Math.min(40, now - last); last = now; update(dt); render(); requestAnimationFrame(loop); }
requestAnimationFrame(loop);
