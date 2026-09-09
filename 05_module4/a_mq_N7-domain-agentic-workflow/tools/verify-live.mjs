// 실제 모델로 한 바퀴 돌린다. 루프가 아니라 «모델»을 시험하는 자리다.
//   node tools/verify-live.mjs [model] [title] [artist]
//   기본: qwen3.5:2b / Rape of the Sabine Women / Giambologna
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { newRun, runToApproval, summary, LIMITS } from '../app/agent.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const archive = JSON.parse(fs.readFileSync(path.join(HERE, '..', 'data', 'works-index.json'), 'utf8'));

const model = process.argv[2] || 'qwen3.5:2b';
const title = process.argv[3] || 'Rape of the Sabine Women';
const artist = process.argv[4] || 'Giambologna';

console.log(`모델 ${model} · 입력 「${title}」 / ${artist}\n${'─'.repeat(64)}`);

const run = newRun({ title, artist, backend: 'ollama', model });
const cfg = { backend: 'ollama', model, numCtx: 16384, limits: { ...LIMITS, maxSteps: 10 } };

let n = 0;
await runToApproval(run, cfg, { archive }, (r) => {
  const s = r.steps[r.steps.length - 1];
  if (!s || r.steps.length === n) return;
  n = r.steps.length;
  const t = (s.thought || '').replace(/\s+/g, ' ').slice(0, 62);
  if (s.kind === 'act') {
    const o = s.observation;
    let got = o.ok ? '' : `실패(${o.reason})`;
    if (o.ok && o.results) got = `${o.results.length}건${o.empty ? ' 비었음' : ': ' + (o.results[0]?.label || '')}`;
    if (o.ok && o.entity) got = `${o.entity.label} · 작가 ${o.entity.creator?.join(',') || '-'}`;
    if (o.ok && o.verdict) got = `verdict=${o.verdict} (${o.file?.license || '-'})`;
    if (o.ok && o.hits) got = `${o.hits.length}건${o.hits[0] ? ': ' + o.hits[0].title : ''}`;
    if (o.ok && o.works) got = `${o.works.length}건`;
    console.log(`${String(n).padStart(2)} ${s.action.tool.padEnd(15)} ${String(s.toolMs).padStart(5)}ms  ${got}`);
    console.log(`   생각: ${t}`);
    console.log(`   인자: ${JSON.stringify(s.action.args).slice(0, 110)}`);
  } else if (s.kind === 'parse_fail') {
    console.log(`${String(n).padStart(2)} ✗ JSON 파싱 실패 — 모델이 뱉은 것: ${s.raw.replace(/\s+/g, ' ').slice(0, 100)}`);
  } else if (s.kind === 'finish') {
    console.log(`${String(n).padStart(2)} ■ finish — ${t}`);
  } else {
    console.log(`${String(n).padStart(2)} ■ ${s.kind} — ${s.detail || s.reason || ''}`);
  }
});

console.log('─'.repeat(64));
const s = summary(run);
console.log(`상태 ${run.status} · 스텝 ${s.steps} · 도구 ${s.toolCalls} · 파싱실패 ${s.parseFails}`);
console.log(`시간 ${(s.wallMs / 1000).toFixed(1)}초 (모델 ${(s.modelMs / 1000).toFixed(1)}s / 도구 ${(s.toolMsTotal / 1000).toFixed(1)}s)`);
console.log(`토큰 in ${s.usage.in} / out ${s.usage.out}`);

if (run.status === 'awaiting_approval') {
  const d = run.finish?.draft || {};
  console.log(`\n게이트: ${run.gate.blocked ? '막힘 — ' + run.gate.why.join(' / ') : '통과'}`);
  console.log('초안:');
  for (const k of ['title', 'origTitle', 'artist', 'inception', 'material', 'collection', 'era', 'license']) {
    console.log(`  ${k.padEnd(11)} ${JSON.stringify(d[k])}`);
  }
  console.log(`  people      ${JSON.stringify(d.people)}`);
  console.log(`  sections    ${Object.entries(d.sections || {}).map(([k, v]) => `${k}:${String(v).length}자`).join(' ')}`);
  console.log(`  notes       ${run.finish.notes || '-'}`);
} else if (run.stopReason) {
  console.log(`\n중단 사유: ${run.stopReason.reason} — ${run.stopReason.detail}`);
}
