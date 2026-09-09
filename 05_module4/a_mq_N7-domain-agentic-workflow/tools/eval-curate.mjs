// 큐레이션 워크플로 평가.
//
// ★전시 구성에는 «정답»이 없다. 그래서 정확도를 재지 않는다.
//   대신 «객관적으로 잴 수 있는 것»만 잰다:
//     ① 지어낸 slug 비율   — 아카이브에 없는 작품을 넣었는가 (게이트가 잡은 것)
//     ② 완주율             — 승인 지점까지 갔는가
//     ③ 분산               — 신화가 몇 개 섞였는가 (한 신화만 쓰면 «전시»가 아니다)
//     ④ 효율               — 스텝·도구·시간
//   주제 적합성과 동선의 설득력은 «사람이 봐야 한다». 여기서 재는 척하지 않는다.
//
//   node tools/eval-curate.mjs [--model qwen3.5:2b]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { newRun, runToApproval, summary, LIMITS } from '../app/agent.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');
const archive = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'works-index.json'), 'utf8'));
const bySlug = Object.fromEntries(archive.map((x) => [x.slug, x]));

const model = process.argv.includes('--model') ? process.argv[process.argv.indexOf('--model') + 1] : 'qwen3.5:2b';

// 주제는 «내 도메인의 실제 업무 시나리오»다 — 실제로 기획해 볼 만한 것들.
const TOPICS = [
  '변신 — 모습이 바뀌는 순간',
  '물과 바다의 신들',
  '죽음과 저승으로 가는 길',
  '영웅의 시련',
  '사랑과 그 대가',
  '창조와 세계의 시작',
];

const cfg = { backend: 'ollama', model, numCtx: 16384, workflow: 'curate', limits: { ...LIMITS, maxSteps: 10 } };
const rows = [];
const runs = [];

console.log(`■ 큐레이션 평가 · ${model} · 주제 ${TOPICS.length}개\n${'─'.repeat(74)}`);
for (let i = 0; i < TOPICS.length; i++) {
  const t = TOPICS[i];
  const run = newRun({ title: t, backend: 'ollama', model, workflow: 'curate' });
  await runToApproval(run, cfg, { archive });
  const d = run.finish?.draft || {};
  const secs = Array.isArray(d.sections) ? d.sections : [];
  const slugs = secs.flatMap((s) => s.works || []);
  const unknown = slugs.filter((s) => !bySlug[s]);
  const myths = new Set(slugs.map((s) => bySlug[s]?.mythKo).filter(Boolean));
  const s = summary(run);
  rows.push({
    topic: t, status: run.status,
    reachedApproval: run.status === 'awaiting_approval',
    gateBlocked: !!run.gate?.blocked, gateWhy: run.gate?.why || [],
    works: slugs.length, unknown: unknown.length, unknownSlugs: unknown.slice(0, 5),
    sections: secs.length, myths: myths.size, mythList: [...myths],
    stopReason: run.stopReason?.reason || null, perf: s,
  });
  runs.push({ topic: t, steps: run.steps, status: run.status, gate: run.gate, finish: run.finish, stopReason: run.stopReason });
  const ok = run.status === 'awaiting_approval' ? (run.gate?.blocked ? '△' : 'O') : '✗';
  console.log(`${String(i + 1).padStart(2)}/${TOPICS.length} ${ok} ${t.padEnd(24)} ` +
    `${String(Math.round(s.wallMs / 1000)).padStart(3)}s 스텝${s.steps} 도구${s.toolCalls} ` +
    `작품${String(slugs.length).padStart(2)} 지어냄${String(unknown.length).padStart(2)} 신화${myths.size} ` +
    `${run.gate?.blocked ? '차단:' + (run.gate.why[0] || '').slice(0, 26) : run.stopReason?.reason || ''}`);
}

const n = rows.length;
const pct = (x) => Math.round((x * 100) / n);
const totalWorks = rows.reduce((a, r) => a + r.works, 0);
const totalUnknown = rows.reduce((a, r) => a + r.unknown, 0);
const agg = {
  n, model,
  reachedApprovalPct: pct(rows.filter((r) => r.reachedApproval).length),
  passedGatePct: pct(rows.filter((r) => r.reachedApproval && !r.gateBlocked).length),
  totalWorks, totalUnknown,
  unknownRatePct: totalWorks ? Math.round((totalUnknown * 100) / totalWorks) : 0,
  runsWithUnknown: rows.filter((r) => r.unknown > 0).length,
  avgWorks: Math.round(totalWorks / n),
  avgMyths: (rows.reduce((a, r) => a + r.myths, 0) / n).toFixed(1),
  avgSteps: Math.round(rows.reduce((a, r) => a + r.perf.steps, 0) / n),
  avgSec: Math.round(rows.reduce((a, r) => a + r.perf.wallMs, 0) / n / 1000),
};
fs.mkdirSync(path.join(ROOT, 'results'), { recursive: true });
fs.writeFileSync(path.join(ROOT, 'results', 'curate.json'),
  JSON.stringify({ aggregate: agg, rows, runs }, null, 1), 'utf8');

console.log('─'.repeat(74));
console.log(`승인 도달 ${agg.reachedApprovalPct}% · 게이트 통과 ${agg.passedGatePct}%`);
console.log(`★지어낸 slug ${totalUnknown}/${totalWorks} = ${agg.unknownRatePct}% · 하나라도 지어낸 실행 ${agg.runsWithUnknown}/${n}`);
console.log(`평균 작품 ${agg.avgWorks}점 · 신화 ${agg.avgMyths}개 · 스텝 ${agg.avgSteps} · ${agg.avgSec}초`);
console.log('\n※ 주제 적합성과 동선의 설득력은 여기서 재지 않는다 — 사람이 봐야 한다.');
console.log('→ results/curate.json');
