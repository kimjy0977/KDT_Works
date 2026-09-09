// 평가 — 아카이브 40점을 «정답지와 대조»해 숫자로 잰다.
//
//   node tools/eval.mjs <세팅이름> [--n 40] [--model qwen3.5:2b] [--out results/xxx.json]
//   node tools/eval.mjs --list
//
// ★이 과제의 가장 큰 자산: 아카이브 982점이 그대로 «정답지»다.
//   그래서 정확도를 «느낌»이 아니라 «숫자»로 잰다.
//   에이전트에게는 원제와 작가만 주고, 나머지 필드를 스스로 복원하게 한 뒤 정답과 맞춰 본다.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { newRun, runToApproval, summary, LIMITS } from '../app/agent.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');
const archive = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'works-index.json'), 'utf8'));
const evalset = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'evalset.json'), 'utf8'));

// ── 세팅. «한 번에 하나씩만» 바꾼다 — 안 그러면 무엇이 효과였는지 못 가른다.
export const SETTINGS = {
  base: { label: '① 기준 (fulltext · 보정 없음)', autoRepair: false, model: 'qwen3.5:2b' },
  repair: { label: '② + autoRepair (중복확인 자동보정)', autoRepair: true, model: 'qwen3.5:2b' },
  smaller: { label: '③ 모델 교체 — llama3.2:1b', autoRepair: true, model: 'llama3.2:1b' },
  other3b: { label: '④ 모델 교체 — qwen2.5:3b', autoRepair: true, model: 'qwen2.5:3b' },
  tight: { label: '⑤ 예산 절반 (스텝 6 · 90초)', autoRepair: true, model: 'qwen3.5:2b', limits: { maxSteps: 6, wallClockMs: 90000 } },
};

// ── 채점기.
//
// ★2026-09-09 — 첫 판을 돌린 뒤 «채점기 자신»의 결함 넷을 찾아 고쳤다.
//   고치기 전 숫자로 보고했다면 «에이전트가 나쁘다»는 틀린 결론이 나왔을 것이다.
//     ① 소장처 정답지가 깨져 있었다 (괄호 안 마침표에서 잘림) → build-index.py 에서 수정
//     ② 매체 「유채, 캔버스」 vs 「캔버스에 유채」 가 «불일치»로 세어졌다 → 토큰 집합 비교로
//     ③ 「기원전 1200년」의 부호를 안 봤다 → BCE 를 음수로
//     ④ 「미상」·「정보없음」을 정답으로 세어 «맞힐 수 없는 문제»를 오답으로 세었다 → 채점 대상 외
//   ⑤ era 는 고치지 않고 «따로» 보고한다 — 아래 eraEq 주석 참조.
const NO_ANSWER = /^(미상|불명|정보없음|알 수 없|없음|unknown|n\/a|-)$/i;
const norm = (s) => String(s ?? '').toLowerCase().replace(/[\s()·,．.'"「」<>]+/g, '');
const isBlank = (v) => !v || NO_ANSWER.test(String(v).trim());

function looseEq(got, want) {
  if (isBlank(want)) return null;    // 정답이 없으면 채점하지 않는다 (null = 대상 외)
  if (isBlank(got)) return false;
  const g = norm(got), w = norm(want);
  if (!g) return false;
  return g.includes(w) || w.includes(g);
}

/** 낱말 집합으로 견준다 — 「유채, 캔버스」와 「캔버스에 유채」는 같은 말이다. */
function tokenEq(got, want) {
  if (isBlank(want)) return null;
  if (isBlank(got)) return false;
  if (looseEq(got, want) === true) return true;
  const tok = (s) => new Set(String(s).toLowerCase()
    .split(/[^a-z0-9가-힣]+/).filter((t) => t.length > 1)
    .map((t) => t.replace(/(에|의|으로|로|과|와|에서)$/, '')).filter((t) => t.length > 1));
  const a = tok(got), b = tok(want);
  if (!a.size || !b.size) return false;
  let hit = 0;
  for (const t of b) if (a.has(t)) hit++;
  return hit / b.size >= 0.5;        // 정답 낱말의 절반 이상이 답에 있으면 맞은 것으로 본다
}

/** 기관 이름만 견준다 — 「메트로폴리탄 미술관 (MET)」과 「메트로폴리탄 미술관, 뉴욕, 미국」은 같은 곳이다. */
function placeEq(got, want) {
  if (isBlank(want)) return null;
  if (isBlank(got)) return false;
  const head = (s) => String(s).split(/[,(]/)[0].trim();
  return looseEq(head(got), head(want)) === true || tokenEq(got, want) === true;
}

/** 연도. ★「기원전 1200년」을 음수로 읽는다 — 안 그러면 BCE 유물이 전부 오답이 된다. */
function yearEq(got, want) {
  const yr = (v) => {
    const s = String(v ?? '');
    const m = s.match(/\d{1,4}/);
    if (!m) return null;
    const bce = /기원전|bce|b\.c/i.test(s) ? -1 : 1;
    return bce * +m[0];
  };
  const wy = yr(want);
  if (isBlank(want) || wy === null) return null;
  const gy = yr(got);
  if (isBlank(got) || gy === null) return false;
  // 오래된 유물일수록 연대 폭이 넓다 — 허용 오차를 «연대에 비례»시킨다
  const tol = Math.abs(wy) > 1000 && wy < 0 ? 200 : Math.abs(wy) < 1400 ? 50 : 5;
  return Math.abs(gy - wy) <= tol;
}

/**
 * ★era 는 «고치지 않고 따로 본다».
 * 내 아카이브의 era 는 「르네상스 1400년~1600년」·「상·주 기원전 1600년~기원전 256년」처럼
 * «시대 이름 + 연대 범위» 를 묶은 값이고, Wikidata 의 P135 는 «미술 사조» 하나다.
 * 둘은 «같은 것을 가리키는 다른 분류 체계»라 일치를 요구하는 것 자체가 틀렸다.
 * 그래서 연대 범위를 떼고 «이름 부분»만 견주되, 이 지표는 보고서에서 «참고»로만 쓴다.
 */
function eraEq(got, want) {
  if (isBlank(want)) return null;
  if (isBlank(got)) return false;
  const name = (s) => String(s).replace(/기원전|년|경|~|—|–|-|\d+/g, '').replace(/\s+/g, ' ').trim();
  return looseEq(name(got), name(want));
}
function peopleHit(got, want) {
  if (!want || !want.length) return null;
  if (!Array.isArray(got) || !got.length) return false;
  return want.some((w) => got.some((g) => looseEq(g, w)));
}

/** 평가 세트 40점은 모두 «이미 등재된» 작품이다. 트레이스의 어느 archive_search 든 잡았으면 성공. */
export function foundDuplicate(run) {
  if (run.finish?.duplicateOf) return true;
  for (const s of run.steps) {
    if (s.kind !== 'act' || s.action.tool !== 'archive_search') continue;
    if (s.observation?.hits?.some((h) => h.score >= 40)) return true;
  }
  return false;
}

/** 검색이 «돌려준 적 없는» Q번호를 모델이 썼다면 그건 지어낸 것이다. */
export function hallucinatedQid(run) {
  const seen = new Set();
  for (const s of run.steps) {
    if (s.kind !== 'act') continue;
    for (const r of s.observation?.results || []) seen.add(r.qid);
    for (const w of s.observation?.works || []) seen.add(w.qid);
  }
  for (const s of run.steps) {
    if (s.kind !== 'act') continue;
    const q = s.action.args?.qid || s.action.args?.artistQid;
    if (q && /^Q[0-9]+$/.test(q) && !seen.has(q)) return q;
  }
  return null;
}

export function grade(item, run) {
  const t = item.truth;
  const d = run.finish?.draft || {};
  // 동정 정확도 — 뽑아 온 «작가»가 정답 작가와 맞는가로 판정한다.
  //   Wikidata Q번호와 아카이브 slug 사이에 대응표가 없으므로 이것이 가장 강한 대리 지표다.
  //   ⚠«작가 일치»는 «작품 일치»보다 약한 기준이다. 보고서에 그대로 적는다.
  const identified = run.status === 'awaiting_approval' && !!run.finish?.identified;
  return {
    id: item.id,
    status: run.status,
    reachedApproval: run.status === 'awaiting_approval',
    gateBlocked: !!run.gate?.blocked,
    gateWhy: run.gate?.why || [],
    identified,
    fields: {
      artist: looseEq(d.artist, t.artist),
      era: eraEq(d.era, t.era),                    // ⚠분류 체계가 달라 «참고»용
      inception: yearEq(d.inception, t.inception),
      material: tokenEq(d.material, t.material),
      collection: placeEq(d.collection, t.collection),
      people: peopleHit(d.people, t.people),
      origTitle: looseEq(d.origTitle, t.origTitle),
    },
    duplicateFound: foundDuplicate(run),   // 40점 전부 «이미 등재된» 작품이므로 참이어야 옳다
    hallucinatedQid: hallucinatedQid(run),
    findable: item.findable || 'unknown',  // probe-coverage.mjs 가 잰 «천장»
    myth: t.mythKo,
    license: d.license || null,
    sectionsFilled: Object.values(d.sections || {}).filter((v) => String(v || '').trim().length > 20).length,
    repairs: run.repairs || 0,
    failureKind: classify(run),
    perf: summary(run),
  };
}

/** 실패를 «유형»으로 가른다. 루브릭이 요구하는 실패 분류가 이것이다. */
export function classify(run) {
  // ⚠순서가 뜻을 바꾼다. 환각을 «맨 앞»에 두었더니 승인까지 간 실행도 실패로 뭉뚱그려졌다.
  //   failureKind 는 «어떻게 끝났나»만 말한다. 환각은 별도 플래그(hallucinatedQid)로 따로 센다.
  if (run.status === 'awaiting_approval') return run.gate?.blocked ? 'gate_blocked' : null;
  if (run.status === 'done') return null;
  if (run.status === 'failed' && run.stopReason?.reason === 'parse_fail') return 'format_broken';
  if (run.status === 'failed') return 'backend_error:' + run.stopReason?.reason;
  if (run.stopReason?.reason === 'repeat_loop') return 'useless_repetition';
  if (run.stopReason?.reason === 'budget') return 'budget_exhausted';
  if (run.stopReason?.reason === 'rejected_by_human') return 'rejected';
  if (run.stopReason?.reason === 'license_unknown') return 'gave_up_license';
  if (run.stopReason?.reason === 'not_found') return 'gave_up_not_found';
  return 'other:' + (run.stopReason?.reason || run.status);
}

function pct(n, d) { return d ? Math.round((n * 100) / d) : 0; }

export function aggregate(rows, setting) {
  const n = rows.length;
  const fieldNames = ['origTitle', 'artist', 'era', 'inception', 'material', 'collection', 'people'];
  const fieldAcc = {};
  for (const f of fieldNames) {
    const scored = rows.map((r) => r.fields[f]).filter((v) => v !== null && v !== undefined);
    fieldAcc[f] = { n: scored.length, hit: scored.filter(Boolean).length, pct: pct(scored.filter(Boolean).length, scored.length) };
  }
  const fails = {};
  for (const r of rows) if (r.failureKind) fails[r.failureKind] = (fails[r.failureKind] || 0) + 1;

  // ★«자료의 한계»와 «에이전트의 한계»를 가른다.
  //   findable=strong 인 10점이 에이전트가 실제로 잘할 수 있는 구간이고,
  //   none 인 7점은 아무리 잘해도 못 찾는 구간이다. 섞어 놓고 한 숫자로 말하면 둘 다 오해가 된다.
  const split = {};
  for (const k of ['strong', 'weak', 'none']) {
    const g = rows.filter((r) => r.findable === k);
    if (!g.length) continue;
    const artistScored = g.map((r) => r.fields.artist).filter((v) => v !== null);
    split[k] = {
      n: g.length,
      reachedApprovalPct: pct(g.filter((r) => r.reachedApproval).length, g.length),
      artistPct: pct(artistScored.filter(Boolean).length, artistScored.length),
      dupPct: pct(g.filter((r) => r.duplicateFound).length, g.length),
    };
  }
  const byMyth = {};
  for (const r of rows) {
    const m = r.myth || '?';
    byMyth[m] ??= { n: 0, approval: 0, artist: 0, artistN: 0 };
    byMyth[m].n++;
    if (r.reachedApproval) byMyth[m].approval++;
    if (r.fields.artist !== null) { byMyth[m].artistN++; if (r.fields.artist) byMyth[m].artist++; }
  }
  const perf = rows.map((r) => r.perf);
  const avg = (f) => Math.round(perf.reduce((a, p) => a + f(p), 0) / Math.max(1, perf.length));
  return {
    setting,
    n,
    reachedApproval: { n: rows.filter((r) => r.reachedApproval).length, pct: pct(rows.filter((r) => r.reachedApproval).length, n) },
    passedGate: { n: rows.filter((r) => r.reachedApproval && !r.gateBlocked).length, pct: pct(rows.filter((r) => r.reachedApproval && !r.gateBlocked).length, n) },
    duplicateFound: { n: rows.filter((r) => r.duplicateFound).length, pct: pct(rows.filter((r) => r.duplicateFound).length, n) },
    hallucinated: { n: rows.filter((r) => r.hallucinatedQid).length, pct: pct(rows.filter((r) => r.hallucinatedQid).length, n) },
    fieldAcc,
    split,
    byMyth,
    failures: fails,
    perf: { steps: avg((p) => p.steps), toolCalls: avg((p) => p.toolCalls), wallMs: avg((p) => p.wallMs), tokensIn: avg((p) => p.usage.in), tokensOut: avg((p) => p.usage.out) },
  };
}

/** --n 이 전체보다 작으면 «앞에서 자르지» 않고 고르게 뽑는다. 앞쪽만 보면 신화가 편중된다. */
function spread(list, n) {
  if (n >= list.length) return list;
  const step = list.length / n;
  return Array.from({ length: n }, (_, i) => list[Math.floor(i * step)]);
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes('--list') || !args.length) {
    console.log('세팅:');
    for (const [k, v] of Object.entries(SETTINGS)) console.log(`  ${k.padEnd(9)} ${v.label}`);
    console.log('\n사용: node tools/eval.mjs <세팅> [--n 40] [--out results/x.json]');
    return;
  }
  const name = args[0];
  const S = SETTINGS[name];
  if (!S) { console.error(`모르는 세팅: ${name}`); process.exit(1); }
  const n = +((args[args.indexOf('--n') + 1]) || 0) || evalset.length;
  const outArg = args.indexOf('--out') >= 0 ? args[args.indexOf('--out') + 1] : `results/${name}.json`;
  const items = spread(evalset, n);

  console.log(`■ ${S.label}\n  모델 ${S.model} · ${items.length}점 · autoRepair=${!!S.autoRepair}`);
  console.log('─'.repeat(72));
  const cfg = {
    backend: 'ollama', model: S.model, numCtx: 16384,
    autoRepair: !!S.autoRepair,
    limits: { ...LIMITS, ...(S.limits || {}) },
  };

  const rows = [];
  const runs = [];
  for (let i = 0; i < items.length; i++) {
    const it = items[i];
    const run = newRun({ title: it.input.title, artist: it.input.artist, backend: 'ollama', model: S.model });
    await runToApproval(run, cfg, { archive });
    const g = grade(it, run);
    rows.push(g);
    runs.push({ id: it.id, steps: run.steps, status: run.status, gate: run.gate,
                stopReason: run.stopReason, finish: run.finish,
                usage: run.usage, startedAt: run.startedAt, model: S.model, repairs: run.repairs || 0 });
    const ok = g.reachedApproval ? (g.gateBlocked ? '△' : 'O') : '✗';
    const hits = Object.entries(g.fields).filter(([, v]) => v === true).map(([k]) => k[0]).join('');
    console.log(`${String(i + 1).padStart(3)}/${items.length} ${ok} ${it.id.padEnd(22)} ${String(Math.round(g.perf.wallMs / 1000)).padStart(3)}s ` +
      `스텝${g.perf.steps} 도구${g.perf.toolCalls} 필드[${hits.padEnd(7)}] ${g.failureKind || ''}`);
  }

  const agg = aggregate(rows, { name, ...S });
  const outPath = path.join(ROOT, outArg);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, JSON.stringify({ setting: { name, ...S }, aggregate: agg, rows, runs }, null, 1), 'utf8');

  console.log('─'.repeat(72));
  console.log(`승인 도달 ${agg.reachedApproval.n}/${agg.n} (${agg.reachedApproval.pct}%) · 게이트 통과 ${agg.passedGate.n} (${agg.passedGate.pct}%) · 중복 탐지 ${agg.duplicateFound.pct}%`);
  console.log('필드 정확도: ' + Object.entries(agg.fieldAcc).map(([k, v]) => `${k} ${v.pct}%(${v.hit}/${v.n})`).join(' · '));
  console.log('실패 분류: ' + (Object.entries(agg.failures).map(([k, v]) => `${k}=${v}`).join(' · ') || '없음'));
  console.log('환각 Q번호: ' + agg.hallucinated.n + '건 (' + agg.hallucinated.pct + '%)');
  console.log('★자료 천장별 — strong=Wikidata에 있고 작가까지 확인된 것, none=아예 없는 것');
  for (const [k, v] of Object.entries(agg.split)) {
    console.log(`   ${k.padEnd(7)} ${String(v.n).padStart(2)}점  승인도달 ${String(v.reachedApprovalPct).padStart(3)}% · 작가정확 ${String(v.artistPct).padStart(3)}% · 중복탐지 ${v.dupPct}%`);
  }
  console.log('신화별:');
  for (const [m, v] of Object.entries(agg.byMyth).sort((x, y) => y[1].n - x[1].n)) {
    console.log(`   ${m.padEnd(8)} ${String(v.n).padStart(2)}점  승인도달 ${pct(v.approval, v.n)}% · 작가정확 ${pct(v.artist, v.artistN)}%`);
  }
  console.log(`평균: 스텝 ${agg.perf.steps} · 도구 ${agg.perf.toolCalls} · ${(agg.perf.wallMs / 1000).toFixed(1)}초 · 토큰 in ${agg.perf.tokensIn}/out ${agg.perf.tokensOut}`);
  console.log(`→ ${outArg}`);
}

if (import.meta.url === `file://${process.argv[1].replace(/\\/g, '/')}` ||
    process.argv[1].endsWith('eval.mjs')) {
  await main();
}
