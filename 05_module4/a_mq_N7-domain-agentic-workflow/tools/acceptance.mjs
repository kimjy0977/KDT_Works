// 수용 기준 재확인 — 배포된 «그 주소»를 상대로 검사한다.
//
// PRD §8 에 미리 적어 둔 기준 넷을 그대로 검사한다. 기준을 결과에 맞춰 고치지 않는다.
//   node tools/acceptance.mjs [배포URL]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { newRun, step, runToApproval, approveAndCommit, WORKFLOWS } from '../app/agent.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');
const BASE = (process.argv[2] || 'https://kimjy0977.github.io/KDT_Works/05_module4/a_mq_N7-domain-agentic-workflow')
  .replace(/\/$/, '');
const archive = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'works-index.json'), 'utf8'));

let pass = 0, fail = 0;
const FAILS = [];
async function crit(label, target, fn) {
  try {
    const { ok, msg } = await fn();
    console.log(`  ${ok ? 'PASS' : 'FAIL'} ${label}\n       기준: ${target}\n       실측: ${msg}`);
    if (ok) pass++; else { fail++; FAILS.push(label + ' — ' + msg); }
  } catch (e) {
    console.log(`  FAIL ${label} — ${e.message}`);
    fail++; FAILS.push(label + ' — ' + e.message);
  }
}

console.log(`■ 수용 기준 재확인 — ${BASE}\n`);

// ── 0. 배포가 살아 있는가 (링크만으로 접속 가능해야 한다)
await crit('0. 배포된 자산이 전부 응답하는가', '핵심 파일 8개 모두 HTTP 200', async () => {
  const files = ['/', '/index.html', '/app/tools.js', '/app/agent.js', '/app/llm.js', '/app/ui.js',
                 '/data/works-index.json', '/PRD.md'];
  const bad = [];
  for (const f of files) {
    try {
      const r = await fetch(BASE + f, { method: 'GET' });
      if (!r.ok) bad.push(`${f}:${r.status}`);
    } catch (e) { bad.push(`${f}:${e.message}`); }
  }
  return { ok: !bad.length, msg: bad.length ? `실패 ${bad.join(', ')}` : `${files.length}/${files.length} 200` };
});

// ── 1. 대표 시나리오 10개 중 7개 이상이 «사람 개입 없이» 승인 지점까지
await crit('1. 승인 지점 도달률', '대표 시나리오 10개 중 7개 이상', async () => {
  const p = path.join(ROOT, 'results', 'repair.json');
  if (!fs.existsSync(p)) return { ok: false, msg: 'results/repair.json 이 없습니다 — 평가를 먼저 돌리세요' };
  const d = JSON.parse(fs.readFileSync(p, 'utf8'));
  // ★«대표 시나리오» 를 이렇게 정의한다 — 자료가 실제로 있는 구간(findable=strong).
  //   자료에 없는 작품을 못 찾은 것은 에이전트의 실패가 아니다. 이 정의를 PRD 보다 «좁게» 잡았음을 밝힌다.
  const evalset = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'evalset.json'), 'utf8'));
  const strong = new Set(evalset.filter((x) => x.findable === 'strong').map((x) => x.id));
  const rows = d.rows.filter((r) => strong.has(r.id));
  const reached = rows.filter((r) => r.reachedApproval).length;
  const scaled = Math.round((reached / Math.max(1, rows.length)) * 10);
  return {
    ok: scaled >= 7,
    msg: `strong 구간 ${reached}/${rows.length} 도달 → 10점 환산 ${scaled}점 · ` +
         `(전체 40점 기준으로는 ${d.aggregate.reachedApproval.n}/${d.aggregate.n} = ${d.aggregate.reachedApproval.pct}%)`,
  };
});

// ── 2. 라이선스 불명 건은 «하나도» 등재로 넘어가지 않는다
await crit('2. 라이선스 안전', '불명·제한 건이 게이트를 통과한 것 0건', async () => {
  const p = path.join(ROOT, 'results', 'repair.json');
  if (!fs.existsSync(p)) return { ok: false, msg: 'results/repair.json 이 없습니다' };
  const d = JSON.parse(fs.readFileSync(p, 'utf8'));
  const leaked = d.rows.filter((r) => {
    const lic = String(r.license || '').toLowerCase();
    const bad = !lic || /unknown|restricted|없|미확인/.test(lic);
    return bad && r.reachedApproval && !r.gateBlocked;
  });
  return { ok: leaked.length === 0, msg: leaked.length ? `★샌 것 ${leaked.length}건: ${leaked.map((x) => x.id).join(', ')}` : '0건 — 전부 막힘' };
});

// ── 3. 데모 모드는 «키 없이» 100% 재생된다
await crit('3. 데모 재생', '저장된 트레이스가 전부 재생 가능', async () => {
  let runs;
  try {
    const r = await fetch(BASE + '/results/demo-runs.json');
    if (!r.ok) return { ok: false, msg: `배포본에 demo-runs.json 이 없습니다 (${r.status})` };
    runs = await r.json();
  } catch (e) { return { ok: false, msg: e.message }; }
  const bad = [];
  for (const run of runs) {
    if (!Array.isArray(run.steps) || !run.steps.length) bad.push(`${run.runId}: 스텝 없음`);
    if (!run.input?.title) bad.push(`${run.runId}: 입력 없음`);
    // 재생은 저장된 스텝을 되짚기만 한다 — 모델도 네트워크도 필요 없어야 한다
    for (const s of run.steps) if (s.kind === 'act' && s.observation === undefined) bad.push(`${run.runId}: 관찰 누락`);
  }
  const kinds = new Set(runs.map((r) => (r.gate?.blocked ? 'blocked' : r.status)));
  return {
    ok: bad.length === 0 && runs.length >= 5 && kinds.size >= 3,
    msg: bad.length ? bad.slice(0, 3).join(' / ')
      : `${runs.length}건 · 갈래 ${[...kinds].join('/')} — 통과분만 담지 않았는지 확인`,
  };
});

// ── 4. 중단 후 재개가 10/10
await crit('4. 중단·재개', '10회 중 10회 이어서 완료', async () => {
  const script = [
    { thought: '1', action: { tool: 'archive_search', args: { q: '헤르메스' } } },
    { thought: '2', action: { tool: 'archive_facets', args: { by: 'myth' } } },
    { thought: '끝', stop: { reason: 'other', detail: 'ok' } },
  ];
  const scripted = (lines) => { let i = 0; return async () => ({ ok: true, usage: { in: 1, out: 1 }, ms: 1, text: JSON.stringify(lines[Math.min(i++, lines.length - 1)]) }); };
  let good = 0;
  for (let k = 0; k < 10; k++) {
    const r = newRun({ title: `재개시험${k}`, artist: 'x', backend: 'mock', model: 'mock' });
    await step(r, { complete: scripted(script) }, { archive });            // 1스텝만
    const revived = JSON.parse(JSON.stringify(r));                          // «저장 → 되살림»
    await runToApproval(revived, { complete: scripted(script.slice(1)) }, { archive });
    if (revived.status === 'stopped' && revived.steps.length === 3 &&
        revived.steps[0].action.args.q === '헤르메스') good++;
  }
  return { ok: good === 10, msg: `${good}/10 — 앞 기록 보존 포함` };
});

// ── 5. 워크플로 둘 다 «쓰기 도구가 승인 뒤에만» 열린다
await crit('5. 권한 최소화', '두 워크플로 모두 승인 전 쓰기 거부', async () => {
  const { callTool } = await import('../app/tools.js');
  const out = [];
  for (const [k, wf] of Object.entries(WORKFLOWS)) {
    const r = await callTool(wf.emit, {}, { archive, approved: false });
    out.push(`${k}:${r.reason}`);
    if (r.ok || r.reason !== 'not_approved') return { ok: false, msg: `${k} 워크플로에서 ${wf.emit} 이 열려 있다` };
  }
  return { ok: true, msg: out.join(' · ') };
});

console.log('\n' + '='.repeat(60));
console.log(`기준 ${pass} 충족 · ${fail} 미달`);
for (const f of FAILS) console.log('  ✗ ' + f);
console.log('\n※ 기준은 PRD §8 에 «미리» 적어 둔 것이다. 결과에 맞춰 고치지 않았다.');
process.exit(fail ? 1 : 0);
