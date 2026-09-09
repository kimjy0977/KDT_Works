// 저장된 실행 기록에서 «다시» 집계한다.
//
// 왜 재집계인가 — 평가를 돌리는 도중에 실패 분류 규칙을 고쳤다(환각이 다른 유형을 덮어써서).
// 세팅마다 다른 규칙으로 매긴 숫자를 나란히 놓으면 비교가 성립하지 않는다.
// 모든 세팅의 «원본 트레이스»가 남아 있으므로, 같은 코드로 전부 다시 매긴다.
// 앞으로 채점 규칙을 고칠 때도 실행을 다시 돌리지 않고 여기만 돌리면 된다.
//
//   node tools/report.mjs        → results/summary.json + EVALUATION.md 표
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { grade, aggregate, SETTINGS } from './eval.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');
const evalset = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'evalset.json'), 'utf8'));
const byId = Object.fromEntries(evalset.map((x) => [x.id, x]));

const order = ['base', 'repair', 'other3b', 'smaller', 'tight'];
const out = [];
for (const name of order) {
  const p = path.join(ROOT, 'results', `${name}.json`);
  if (!fs.existsSync(p)) { console.log(`  (없음) ${name}.json — 건너뜀`); continue; }
  const d = JSON.parse(fs.readFileSync(p, 'utf8'));
  // ★rows 를 그대로 쓰지 않는다. runs(원본 트레이스)에서 «다시» 채점한다.
  const rows = d.runs.map((r) => grade(byId[r.id], r));
  const agg = aggregate(rows, d.setting);
  out.push(agg);
  fs.writeFileSync(p, JSON.stringify({ ...d, aggregate: agg, rows }, null, 1), 'utf8');
  console.log(`  ${name.padEnd(9)} ${rows.length}점 재집계`);
}

fs.writeFileSync(path.join(ROOT, 'results', 'summary.json'),
  JSON.stringify({ generatedFrom: order.filter((n) => fs.existsSync(path.join(ROOT, 'results', `${n}.json`))), settings: out }, null, 1), 'utf8');

// ── 사람이 읽을 표. EVALUATION.md 에 그대로 붙일 수 있게 마크다운으로 뽑는다.
const L = [];
const p2 = (x) => String(x).padStart(3);
L.push('### 세팅별 비교\n');
L.push('| 세팅 | n | 승인 도달 | 게이트 통과 | 중복 탐지 | 환각 Q번호 | 평균 스텝 | 평균 도구 | 평균 초 |');
L.push('|---|---:|---:|---:|---:|---:|---:|---:|---:|');
for (const s of out) {
  L.push(`| ${s.setting.label} | ${s.n} | ${s.reachedApproval.pct}% | ${s.passedGate.pct}% | ` +
    `${s.duplicateFound.pct}% | ${s.hallucinated.pct}% | ${s.perf.steps} | ${s.perf.toolCalls} | ${(s.perf.wallMs / 1000).toFixed(0)} |`);
}
const F = ['origTitle', 'artist', 'era', 'inception', 'material', 'collection', 'people'];
L.push('\n### 필드 정확도 — 아카이브 982점이 정답지\n');
L.push('| 세팅 | ' + F.join(' | ') + ' |');
L.push('|---|' + F.map(() => '---:').join('|') + '|');
for (const s of out) {
  L.push(`| ${s.setting.name} | ` + F.map((k) => s.fieldAcc[k] ? `${s.fieldAcc[k].pct}% (${s.fieldAcc[k].hit}/${s.fieldAcc[k].n})` : '-').join(' | ') + ' |');
}
L.push('\n### ★자료의 천장별 — 섞어 놓고 한 숫자로 말하면 둘 다 오해가 된다\n');
L.push('| 세팅 | 구간 | n | 승인 도달 | 작가 정확 | 중복 탐지 |');
L.push('|---|---|---:|---:|---:|---:|');
for (const s of out) {
  for (const [k, v] of Object.entries(s.split)) {
    L.push(`| ${s.setting.name} | ${k} | ${v.n} | ${v.reachedApprovalPct}% | ${v.artistPct}% | ${v.dupPct}% |`);
  }
}
L.push('\n### 실패 분류\n');
L.push('| 세팅 | 유형 |');
L.push('|---|---|');
for (const s of out) {
  L.push(`| ${s.setting.name} | ` + (Object.entries(s.failures).map(([k, v]) => `\`${k}\` ×${v}`).join(' · ') || '없음') + ' |');
}
fs.writeFileSync(path.join(ROOT, 'results', 'tables.md'), L.join('\n') + '\n', 'utf8');

console.log('\n' + L.join('\n'));
console.log('\n→ results/summary.json · results/tables.md');
