// 데모 모드가 재생할 트레이스를 «실제 실행 기록에서» 굽는다.
//
// 왜 필요한가 — 배포 요건이 「다른 사람이 링크만으로 접속해 워크플로를 실행해 볼 수 있어야」다.
// 그런데 실제 실행에는 로컬 Ollama 나 API 키가 필요하다. 채점자에게 그걸 요구할 수 없다.
// 그래서 «실제로 돌았던» 실행을 그대로 재생한다. 지어낸 화면이 아니라 진짜 기록이다.
//
// ⛔불리한 실행을 골라 빼지 않는다 — 성공·게이트차단·실패를 «모두» 넣는다.
//
//   node tools/bake-demo.mjs
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');
const evalset = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'evalset.json'), 'utf8'));
const byId = Object.fromEntries(evalset.map((x) => [x.id, x]));

const SRC = ['repair', 'base', 'other3b'];
const pool = [];
for (const name of SRC) {
  const p = path.join(ROOT, 'results', `${name}.json`);
  if (!fs.existsSync(p)) continue;
  const d = JSON.parse(fs.readFileSync(p, 'utf8'));
  for (const r of d.runs) pool.push({ ...r, _setting: name, _model: d.setting.model });
}
if (!pool.length) { console.error('결과 파일이 없습니다. 먼저 tools/eval.mjs 를 돌리세요.'); process.exit(1); }

// 세 갈래를 «골고루» — 잘 된 것만 보여 주면 데모가 광고가 된다.
const pick = (fn, n) => pool.filter(fn).slice(0, n);
const chosen = [
  ...pick((r) => r.status === 'awaiting_approval' && !r.gate?.blocked, 3),   // 통과
  ...pick((r) => r.status === 'awaiting_approval' && r.gate?.blocked, 2),    // 게이트가 막은 것
  ...pick((r) => r.status === 'stopped' && r.stopReason?.reason === 'repeat_loop', 1),
  ...pick((r) => r.status === 'stopped' && r.stopReason?.reason === 'budget', 1),
  ...pick((r) => r.status === 'failed', 1),
];
const seen = new Set();
const runs = [];
for (const r of chosen) {
  const key = r.id + r._setting;
  if (seen.has(key)) continue;
  seen.add(key);
  const it = byId[r.id];
  runs.push({
    runId: `demo-${r._setting}-${r.id}`,
    input: it.input,
    backend: 'demo', model: r._model,
    startedAt: r.steps[0]?.at ? r.steps[0].at - 500 : 0,
    phase: r.status === 'awaiting_approval' ? 'approval' : 'identify',
    steps: r.steps, toolCalls: r.steps.filter((s) => s.kind === 'act').length,
    parseFails: r.steps.filter((s) => s.kind === 'parse_fail').length,
    usage: r.steps.reduce((a, s) => ({ in: a.in + (s.tokens?.in || 0), out: a.out + (s.tokens?.out || 0) }), { in: 0, out: 0 }),
    status: r.status, finish: r.finish, gate: r.gate, stopReason: r.stopReason,
    approved: false, record: null,
    _note: `${r._setting} 세팅 · ${r._model} · 실제 실행 기록`,
  });
}

const outP = path.join(ROOT, 'results', 'demo-runs.json');
fs.writeFileSync(outP, JSON.stringify(runs, null, 1), 'utf8');
console.log(`데모 트레이스 ${runs.length}건 · ${(fs.statSync(outP).size / 1024).toFixed(0)} KB`);
for (const r of runs) {
  console.log(`  ${r.status.padEnd(18)} ${(r.gate?.blocked ? '게이트차단' : r.stopReason?.reason || '').padEnd(12)} ${r.input.title.slice(0, 44)}`);
}
console.log('\n갈래별로 골고루 담았습니다 — 잘 된 것만 넣으면 데모가 광고가 됩니다.');
