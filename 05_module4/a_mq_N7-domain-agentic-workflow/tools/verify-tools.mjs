// 도구 6종을 «실제로» 두드린다. 루프를 짜기 전에 여기서 막힌 것을 다 찾는다.
//   node tools/verify-tools.mjs
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { TOOLS, callTool } from '../app/tools.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const archive = JSON.parse(fs.readFileSync(path.join(HERE, '..', 'data', 'works-index.json'), 'utf8'));

let pass = 0, fail = 0;
const FAILS = [];
async function check(label, fn) {
  try {
    const msg = await fn();
    console.log(`  ok   ${label}${msg ? ' — ' + msg : ''}`);
    pass++;
  } catch (e) {
    console.log(`  FAIL ${label} — ${e.message}`);
    FAILS.push(`${label}: ${e.message}`);
    fail++;
  }
}
const must = (cond, msg) => { if (!cond) throw new Error(msg); };

console.log('■ 0. 스키마 자체 점검');
await check('도구 6종 등록', () => {
  must(TOOLS.length === 6, `${TOOLS.length}종`);
  return TOOLS.map((t) => t.name).join(', ');
});
await check('모든 도구가 name·description·input·output 을 갖춤', () => {
  for (const t of TOOLS) {
    must(t.name && t.description && t.input && t.output, `${t.name} 필드 누락`);
    must(t.description.length > 60, `${t.name} 설명이 너무 짧다(${t.description.length}자) — 모델이 언제 쓸지 모른다`);
    must(t.input.type === 'object', `${t.name} input.type`);
  }
  return '6/6';
});
await check('쓰기 도구는 «하나»뿐 (권한 최소화)', () => {
  const w = TOOLS.filter((t) => t.writes).map((t) => t.name);
  must(w.length === 1 && w[0] === 'emit_record', `쓰기 도구: ${w.join(',') || '없음'}`);
  return 'emit_record 만';
});

console.log('\n■ 1. wd_search — 실제 호출');
await check('label 모드 · 원제 그대로 → 0건 (질의 재작성이 필요한 바로 그 상황)', async () => {
  const r = await callTool('wd_search', { query: 'Mercury (Flying Mercury)', mode: 'label' }, {});
  must(r.ok, r.reason);
  must(r.empty, `0건이어야 하는데 ${r.results.length}건`);
  return '0건 — 빈 결과는 «예외»가 아니라 «관찰»로 돌아온다';
});
await check('label 모드 · 괄호 안쪽으로 재질의 → 찾는다', async () => {
  const r = await callTool('wd_search', { query: 'Flying Mercury', mode: 'label' }, {});
  must(r.ok && r.results.length, '결과 없음');
  return `${r.results[0].qid} ${r.results[0].label}`;
});
await check('빈 질의는 «호출 전에» 거부', async () => {
  const r = await callTool('wd_search', { query: '   ' }, {});
  must(!r.ok && r.reason === 'empty_query', JSON.stringify(r));
  return 'empty_query';
});

console.log('\n■ 1-B. 두 mode 는 «반대로» 동작한다 — 도구 설명이 사실인지 검사');
await check('label: 작가명을 덧붙이면 오히려 0건', async () => {
  const r = await callTool('wd_search', { query: 'Rape of the Sabine Women Giambologna', mode: 'label' }, {});
  must(r.ok, r.reason);
  must(r.empty, `0건이어야 하는데 ${r.results.length}건`);
  return '0건 — 라벨 접두 일치라 그렇다';
});
await check('fulltext: 같은 작가명으로 정답을 «1위»에 올린다', async () => {
  const r = await callTool('wd_search', { query: 'Rape of the Sabine Women', artist: 'Giambologna' }, {});
  must(r.ok && r.results.length, '결과 없음');
  const top = r.results[0];
  must(/Giambologna/i.test(top.description), `1위 설명에 작가가 없다: ${top.description}`);
  return `1위 ${top.qid} ${top.label} | ${top.description.slice(0, 44)}`;
});
await check('fulltext 는 한 번의 호출로 라벨까지 받는다 (추가 왕복 없음)', async () => {
  const r = await callTool('wd_search', { query: 'Birth of Venus', artist: 'Botticelli' }, {});
  must(r.ok && r.results.length, '결과 없음');
  must(r.results.some((x) => x.label), '라벨이 비어 있다');
  return `${r.results.length}건 · ${r.ms}ms`;
});

console.log('\n■ 2. wd_entity — 구조화 사실');
await check('잘못된 qid 를 거부 (되돌림 신호)', async () => {
  const r = await callTool('wd_entity', { qid: 'not-a-qid' }, {});
  must(!r.ok && r.reason === 'bad_qid', JSON.stringify(r));
  return 'bad_qid';
});
await check('존재하지 않는 qid → not_found', async () => {
  const r = await callTool('wd_entity', { qid: 'Q999999999' }, {});
  must(!r.ok && (r.reason === 'not_found' || r.reason?.startsWith('http')), JSON.stringify(r).slice(0, 90));
  return r.reason;
});
await check('알려진 작품의 사실을 캔다 (사비니 여인의 납치)', async () => {
  const s = await callTool('wd_search', { query: 'Rape of the Sabine Women Giambologna' }, {});
  must(s.ok && s.results.length, '검색 실패');
  const r = await callTool('wd_entity', { qid: s.results[0].qid }, {});
  must(r.ok, r.reason);
  const e = r.entity;
  must(e.label, '라벨 없음');
  return `${e.label} | 작가 ${e.creator.join(',') || '-'} | ${e.inception.join(',') || '-'} | 재료 ${e.material.join(',') || '-'} | Q번호가 «이름»으로 바뀌었나: ${e.creator.every((c) => !/^Q\d+$/.test(c)) ? '예' : '아니오'}`;
});

console.log('\n■ 3. wd_sparql — 작가 스코프 폴백');
await check('템플릿 고정 — 자유 SPARQL 을 받지 않는다', () => {
  const t = TOOLS.find((x) => x.name === 'wd_sparql');
  must(!('query' in t.input.properties), '자유 query 파라미터가 열려 있다');
  return 'artistQid 만 받음';
});
await check('Giambologna(Q220136) 작품 목록', async () => {
  const r = await callTool('wd_sparql', { artistQid: 'Q220136', limit: 8 }, {});
  must(r.ok, r.reason);
  must(r.works.length > 0, '결과 0건');
  return `${r.works.length}건 · ${r.ms}ms · 예: ${r.works.slice(0, 3).map((w) => w.label).join(' / ')}`;
});

console.log('\n■ 4. commons_file — 라이선스 판정');
await check('없는 파일 → verdict=unknown (등재 보류 신호)', async () => {
  const r = await callTool('commons_file', { title: 'File:이런파일은없다-kdt-mq4.jpg' }, {});
  must(r.ok && r.verdict === 'unknown', JSON.stringify(r).slice(0, 120));
  return 'unknown';
});
await check('실제 PD 작품 → verdict 판정', async () => {
  const r = await callTool('commons_file', { search: 'Botticelli Birth of Venus' }, {});
  must(r.ok, r.reason);
  must(r.file, '파일 없음');
  return `${r.file.title.slice(0, 48)} | license=${r.file.license} → verdict=${r.verdict}`;
});

console.log('\n■ 5. archive_search — 로컬 색인');
await check('색인 미로드 시 명확히 실패', async () => {
  const r = await callTool('archive_search', { q: '헤르메스' }, {});
  must(!r.ok && r.reason === 'index_not_loaded', JSON.stringify(r));
  return 'index_not_loaded';
});
await check('중복 등재 탐지 — 이미 있는 작품을 찾아낸다', async () => {
  const r = await callTool('archive_search', { q: 'Flying Mercury', topK: 3 }, { archive });
  must(r.ok && r.hits.length, '결과 없음');
  const top = r.hits[0];
  must(/Mercur/i.test(top.origTitle || ''), `엉뚱한 1위: ${top.origTitle}`);
  return `1위 ${top.title} (${top.origTitle}) score=${top.score}`;
});
await check('인물로 연결 후보 찾기', async () => {
  const r = await callTool('archive_search', { q: '헤르메스', topK: 5 }, { archive });
  must(r.ok && r.hits.length >= 2, `${r.hits.length}건`);
  return `${r.hits.length}건 · ${r.hits.slice(0, 3).map((h) => h.title).join(' / ')}`;
});

console.log('\n■ 6. emit_record — ★승인 게이트');
await check('승인 «없이» 호출하면 거부된다', async () => {
  const r = await callTool('emit_record', { title: 'ㄱ', origTitle: 'a', artist: 'b' }, { approved: false });
  must(!r.ok && r.reason === 'not_approved', JSON.stringify(r));
  return 'not_approved — 런타임이 막음';
});
await check('승인해도 스키마 미달이면 거부', async () => {
  const r = await callTool('emit_record', { title: 'ㄱ' }, { approved: true });
  must(!r.ok && r.reason === 'schema', JSON.stringify(r));
  return r.detail;
});
await check('승인 + 스키마 충족 → 통과', async () => {
  const r = await callTool('emit_record',
    { title: '나는 메르쿠리우스', origTitle: 'Flying Mercury', artist: '잠볼로냐' }, { approved: true });
  must(r.ok && r.record.emittedAt, JSON.stringify(r));
  return '레코드 생성';
});

console.log('\n■ 7. 실패가 예외로 «새어 나가지» 않는가');
await check('없는 도구 이름', async () => {
  const r = await callTool('nope', {}, {});
  must(!r.ok && r.reason === 'unknown_tool', JSON.stringify(r));
  return 'unknown_tool';
});
await check('인자가 아예 없어도 던지지 않는다', async () => {
  for (const t of TOOLS) {
    const r = await callTool(t.name, undefined, { archive, approved: false });
    must(typeof r.ok === 'boolean', `${t.name} 이 {ok} 를 안 돌려줌`);
  }
  return '6/6 모두 {ok} 반환';
});

console.log('\n' + '='.repeat(56));
console.log(`통과 ${pass} · 실패 ${fail}`);
for (const f of FAILS) console.log('  ✗ ' + f);
process.exit(fail ? 1 : 0);
