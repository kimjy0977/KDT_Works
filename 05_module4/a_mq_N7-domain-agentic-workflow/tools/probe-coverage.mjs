// 평가 세트 40점이 «애초에 Wikidata 에 있기는 한가»를 한 번 실측한다.
//
// 왜 필요한가 — 파일럿에서 중국 작품 3점이 모두 0건이 나왔다. 그건 에이전트가 못한 게 아니라
// «자료에 없어서» 다. 이 둘을 갈라 재지 않으면 «에이전트 성능»이라는 숫자가 의미를 잃는다.
// 여기서 나온 findable 플래그로 평가를 두 갈래로 나눠 보고한다.
//
//   node tools/probe-coverage.mjs        → data/evalset.json 에 findable 을 써 넣는다
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { callTool } from '../app/tools.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const P = path.join(HERE, '..', 'data', 'evalset.json');
const evalset = JSON.parse(fs.readFileSync(P, 'utf8'));
const idx = JSON.parse(fs.readFileSync(path.join(HERE, '..', 'data', 'works-index.json'), 'utf8'));
const mythOf = Object.fromEntries(idx.map((x) => [x.slug, x.mythKo]));

// 사람이 «최선을 다해» 찾는 방식을 그대로 흉내 낸다. 이보다 잘 찾을 수는 없다고 볼 상한선.
async function probe(item) {
  const { title, artist } = item.input;
  const tried = [];
  const attempt = async (label, args) => {
    const r = await callTool('wd_search', args, {});
    tried.push({ label, args, n: r.ok ? r.results.length : -1, top: r.results?.[0] || null, reason: r.reason });
    return r.ok ? r.results : [];
  };
  // ① 전문검색 + 작가 (가장 강한 수단)
  let res = await attempt('fulltext+artist', { query: title, artist, mode: 'fulltext' });
  if (!res.length) res = await attempt('fulltext', { query: title, mode: 'fulltext' });
  for (const q of item.queries.slice(1)) {          // ② 질의 변형들
    if (res.length) break;
    res = await attempt(`variant:${q.slice(0, 28)}`, { query: q, mode: 'fulltext' });
  }
  // ③ «이게 정말 그 작품인가» — 후보의 제작자(P170)를 «한국어 라벨»로 받아 아카이브 작가와 맞춘다.
  //    ⚠처음엔 영문 description 에 작가 이름이 있는지로 봤는데, 아카이브 작가명이 한국어(「잠볼로냐」)라
  //      비교가 아예 성립하지 않아 전부 0 이 나왔다. 탐침 자신의 버그였다.
  let strong = null;
  for (const cand of res.slice(0, 3)) {
    const e = await callTool('wd_entity', { qid: cand.qid, lang: 'ko' }, {});
    if (!e.ok) continue;
    const creators = e.entity.creator || [];
    const hit = creators.some((c) => looseEq(c, artist));
    tried.push({ label: `verify:${cand.qid}`, creators, artist, hit });
    if (hit) { strong = { ...cand, creators }; break; }
  }
  return { any: res.length > 0, strong: !!strong, strongCand: strong, top: res[0] || null, tried };
}

const nrm = (s) => String(s ?? '').toLowerCase().replace(/[\s()·,．.'"「」]+/g, '');
function looseEq(a, b) {
  if (!a || !b) return false;
  const x = nrm(a), y = nrm(b);
  return !!x && !!y && (x.includes(y) || y.includes(x));
}

const out = [];
let anyN = 0, strongN = 0;
for (let i = 0; i < evalset.length; i++) {
  const it = evalset[i];
  const p = await probe(it);
  it.findable = p.strong ? 'strong' : p.any ? 'weak' : 'none';
  it.probeTop = p.top ? { qid: p.top.qid, label: p.top.label, description: p.top.description } : null;
  it.probeStrong = p.strongCand ? { qid: p.strongCand.qid, label: p.strongCand.label, creators: p.strongCand.creators } : null;
  if (p.any) anyN++;
  if (p.strong) strongN++;
  out.push({ id: it.id, myth: mythOf[it.id], findable: it.findable, top: p.top?.label || '' });
  console.log(`${String(i + 1).padStart(3)}/${evalset.length} ${it.findable.padEnd(6)} ${(mythOf[it.id] || '').padEnd(6)} ${it.input.title.slice(0, 40).padEnd(42)} ${(p.strongCand?.label || p.top?.label || '').slice(0, 34)}`);
}

fs.writeFileSync(P, JSON.stringify(evalset, null, 1), 'utf8');

console.log('\n' + '─'.repeat(70));
console.log(`무엇이든 나옴 ${anyN}/${evalset.length} (${Math.round(anyN * 100 / evalset.length)}%) · 작가까지 맞는 강한 후보 ${strongN} (${Math.round(strongN * 100 / evalset.length)}%)`);
const byMyth = {};
for (const r of out) {
  byMyth[r.myth] ??= { n: 0, strong: 0, weak: 0, none: 0 };
  byMyth[r.myth].n++;
  byMyth[r.myth][r.findable]++;
}
console.log('\n신화별 — 이 숫자가 «에이전트가 아무리 잘해도 넘을 수 없는 천장»이다');
for (const [m, v] of Object.entries(byMyth).sort((a, b) => b[1].n - a[1].n)) {
  console.log(`  ${m.padEnd(8)} ${String(v.n).padStart(2)}점  strong ${v.strong} · weak ${v.weak} · none ${v.none}`);
}
