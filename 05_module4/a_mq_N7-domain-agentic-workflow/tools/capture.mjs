/* capture.mjs — CURATOR 화면을 «전체 페이지»로 찍는다.
 *
 * ★왜 필요한가
 *   제출 요건이 「저장소 URL — 실제 결과물 «캡처본» 포함」이다.
 *   그런데 이 폴더엔 이미지가 한 장도 없었다(2026-09-10 실측).
 *   손으로 찍으면 ①빠뜨리고 ②화면 크기가 제각각이고 ③다시 찍기 어렵다.
 *   ⇒ 기계로 찍는다. 화면을 고치면 다시 돌리면 된다.
 *
 * ★왜 chrome --screenshot 이 아니라 CDP 인가
 *   --screenshot 은 «창 크기»만큼만 찍는다. 페이지가 길면 잘린다.
 *   CDP 의 captureBeyondViewport:true 는 «문서 전체»를 찍는다.
 *   그리고 승인 버튼을 «누른 뒤»의 결과 화면은 클릭 없이는 못 만든다.
 *
 * 쓰는 법:  node tools/capture.mjs [베이스URL]
 *           (기본 http://127.0.0.1:8898)
 */
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = join(ROOT, 'docs', 'screens');
const BASE = process.argv[2] || 'http://127.0.0.1:8898';
const PORT = 9333;

const CHROMES = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
];
const CHROME = CHROMES.find((p) => existsSync(p));
if (!CHROME) { console.error('크롬을 못 찾았습니다'); process.exit(1); }

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* ★찍을 화면 — «무엇을 보여 주려는가»로 골랐다.
   act 가 있으면 찍기 «전에» 그 JS 를 돌린다(승인 누르기 등). */
const SHOTS = [
  { f: '01-실행.png', u: '/', w: 1440,
    t: '실행 — 무엇을 하는 서비스인지, 어떻게 도는지, 어디서 멈추는지' },
  { f: '02-트레이스.png', u: '/?run=3&tab=trace', w: 1440,
    t: '트레이스 — 어느 도구를 왜 불렀고 무엇이 돌아왔나 (단계별 소요·워터폴)' },
  { f: '03-승인.png', u: '/?run=3&tab=approve', w: 1440,
    t: '사람 승인 — 되돌리기 어려운 작업 «앞»에서 멈춘 화면' },
  { f: '04-결과.png', u: '/?run=3&tab=approve', w: 1440,
    t: '결과 — 승인 뒤 확정된 등재 레코드 (사람이 읽는 것 먼저)',
    act: `(() => {
      const b = document.querySelector('#approve button.primary');
      if (!b) return 'no-button';
      if (b.disabled) return 'disabled:' + b.textContent.trim();
      b.click(); return 'clicked:' + b.textContent.trim();
    })()` },
  { f: '05-평가.png', u: '/?tab=eval', w: 1440,
    t: '평가 — 40문항 × 5세팅. 잘 된 것보다 «어디를 믿으면 안 되는지»' },
  { f: '06-문서.png', u: '/?tab=about', w: 1440,
    t: '문서 — 도구 8종의 입출력 스키마와 권한' },
];

let msgId = 0;
function rpc(ws, method, params = {}) {
  const id = ++msgId;
  return new Promise((res, rej) => {
    const to = setTimeout(() => rej(new Error(method + ' 시간초과')), 45000);
    const on = (ev) => {
      const m = JSON.parse(ev.data);
      if (m.id !== id) return;
      clearTimeout(to); ws.removeEventListener('message', on);
      m.error ? rej(new Error(method + ': ' + m.error.message)) : res(m.result);
    };
    ws.addEventListener('message', on);
    ws.send(JSON.stringify({ id, method, params }));
  });
}

(async () => {
  mkdirSync(OUT, { recursive: true });
  const prof = join(process.env.TEMP || '.', 'curator-capture-profile');

  const chrome = spawn(CHROME, [
    '--headless=new', '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
    '--force-device-scale-factor=1', '--disable-lcd-text',
    `--user-data-dir=${prof}`, `--remote-debugging-port=${PORT}`,
    'about:blank',
  ], { stdio: 'ignore' });

  // 디버깅 포트가 열릴 때까지 «기다린다» — 잠자기로 때우지 않는다
  let ver = null;
  for (let i = 0; i < 60 && !ver; i++) {
    try { ver = await fetch(`http://127.0.0.1:${PORT}/json/version`).then((r) => r.json()); }
    catch { await sleep(250); }
  }
  if (!ver) { chrome.kill(); console.error('크롬 디버깅 포트가 안 열렸습니다'); process.exit(1); }
  console.log('='.repeat(62));
  console.log('CURATOR 화면 캡처 —', ver.Browser);
  console.log('베이스', BASE, '· 저장', 'docs/screens/');
  console.log('='.repeat(62));

  const manifest = [];
  let noisy = 0;
  for (const s of SHOTS) {
    const tgt = await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: 'PUT' })
      .then((r) => r.json());
    const ws = new WebSocket(tgt.webSocketDebuggerUrl);
    await new Promise((r) => ws.addEventListener('open', r, { once: true }));

    /* ★페이지가 «조용한지» 듣는다.
       정적 검사는 내가 생각한 패턴만 본다. 실제로 열어 보는 것이 완전하다. */
    const problems = [];
    ws.addEventListener('message', (ev) => {
      const m = JSON.parse(ev.data);
      if (m.method === 'Runtime.exceptionThrown') {
        const d = m.params.exceptionDetails;
        problems.push('예외 ' + (d.exception?.description || d.text || '').split('\n')[0]);
      } else if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') {
        problems.push('console.error ' + m.params.args.map((a) => a.value ?? a.description).join(' '));
      } else if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error') {
        problems.push('로그 ' + m.params.entry.text);
      }
    });

    await rpc(ws, 'Page.enable');
    await rpc(ws, 'Runtime.enable');
    await rpc(ws, 'Log.enable');
    await rpc(ws, 'Emulation.setDeviceMetricsOverride',
      { width: s.w, height: 1000, deviceScaleFactor: 1, mobile: false });
    await rpc(ws, 'Page.navigate', { url: BASE + s.u });
    // load 이벤트 + 폰트·fetch 가 앉을 시간
    await new Promise((r) => {
      const on = (ev) => { if (JSON.parse(ev.data).method === 'Page.loadEventFired') {
        ws.removeEventListener('message', on); r(); } };
      ws.addEventListener('message', on); setTimeout(r, 15000);
    });
    await sleep(2200);

    let note = '';
    if (s.act) {
      const r = await rpc(ws, 'Runtime.evaluate', { expression: s.act, returnByValue: true });
      note = String(r.result?.value ?? '');
      await sleep(1800);
    }

    const shot = await rpc(ws, 'Page.captureScreenshot',
      { format: 'png', captureBeyondViewport: true, optimizeForSpeed: false });
    const buf = Buffer.from(shot.data, 'base64');
    writeFileSync(join(OUT, s.f), buf);
    const dim = `${buf.readUInt32BE(16)}×${buf.readUInt32BE(20)}`;
    const quiet = problems.length === 0;
    if (!quiet) noisy += problems.length;
    console.log(`  ${quiet ? '✅' : '❌'} ${s.f.padEnd(18)} ${dim.padEnd(11)} ` +
      `${String(Math.round(buf.length / 1024)).padStart(4)} KB` + (note ? `  [${note}]` : ''));
    for (const p of [...new Set(problems)]) console.log(`       ★${p}`);
    manifest.push({ file: s.f, title: s.t, url: s.u, size: dim, clean: quiet });

    ws.close();
    await fetch(`http://127.0.0.1:${PORT}/json/close/${tgt.id}`).catch(() => {});
  }

  writeFileSync(join(OUT, 'INDEX.json'), JSON.stringify(manifest, null, 2) + '\n');
  chrome.kill();
  console.log('\n' + '='.repeat(62));
  console.log(`${manifest.length}장 · docs/screens/INDEX.json 에 목록`);
  if (noisy) {
    console.log(`★콘솔에 ${noisy}건이 떴습니다 — 화면은 멀쩡해 보여도 «도는» 건 아닙니다.`);
    process.exit(1);
  }
  console.log('콘솔 조용함 — 여는 동안 예외·에러 0건');
  process.exit(0);
})();
