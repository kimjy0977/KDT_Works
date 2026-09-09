// 루프의 «구조»를 모델 없이 검사한다.
//
// 왜 모델 없이 하나 — 모델을 쓰면 실패했을 때 «루프가 틀렸나 모델이 틀렸나»를 못 가른다.
// 여기서는 대본을 읽는 가짜 모델을 넣어 루프만 시험한다. 모델 시험은 verify-live.mjs 가 한다.
//
//   node tools/verify-loop.mjs
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { newRun, step, runToApproval, approveAndCommit, reject, summary, LIMITS } from '../app/agent.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const archive = JSON.parse(fs.readFileSync(path.join(HERE, '..', 'data', 'works-index.json'), 'utf8'));
const ctx = { archive };

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
const must = (c, m) => { if (!c) throw new Error(m); };

/** 대본을 순서대로 뱉는 가짜 모델. 대본이 끝나면 마지막 줄을 되풀이한다. */
function scripted(lines, { usage = { in: 100, out: 40 } } = {}) {
  let i = 0;
  return async () => {
    const text = typeof lines[Math.min(i, lines.length - 1)] === 'string'
      ? lines[Math.min(i, lines.length - 1)]
      : JSON.stringify(lines[Math.min(i, lines.length - 1)]);
    i++;
    return { ok: true, text, usage, ms: 5 };
  };
}

const GOOD_DRAFT = {
  title: '사비니 여인의 납치', origTitle: 'Rape of the Sabine Women', artist: '잠볼로냐',
  inception: '1579~1583', material: '대리암', collection: '로지아 데이 란치, 피렌체',
  era: '매너리즘', people: ['로물루스'], license: 'Public domain',
  imageUrl: 'https://upload.wikimedia.org/x.jpg',
  sources: ['https://www.wikidata.org/wiki/Q3545179'],
  sections: { meta: 'ㄱ', description: 'ㄴ', myth: 'ㄷ', insight: 'ㄹ' },
};

console.log('■ 1. 정상 경로 — 도구 호출 → 관찰 → 종료 → 승인 → 등재');
let happy;
await check('세 도구를 부르고 finish 로 끝난다', async () => {
  happy = newRun({ title: 'Rape of the Sabine Women', artist: 'Giambologna', backend: 'mock', model: 'mock' });
  const cfg = {
    complete: scripted([
      { thought: '전문 검색으로 동정', action: { tool: 'wd_search', args: { query: 'Rape of the Sabine Women', artist: 'Giambologna' } } },
      { thought: '사실을 캔다', action: { tool: 'wd_entity', args: { qid: 'Q3545179' } } },
      { thought: '라이선스 확인', action: { tool: 'commons_file', args: { search: 'Giambologna Rape of the Sabine Women' } } },
      { thought: '중복 확인', action: { tool: 'archive_search', args: { q: 'Rape of the Sabine Women' } } },
      { thought: '다 모았다', finish: { identified: true, qid: 'Q3545179', confidence: 'high', draft: GOOD_DRAFT, duplicateOf: null, notes: '' } },
    ]),
  };
  await runToApproval(happy, cfg, ctx);
  must(happy.status === 'awaiting_approval', `상태 ${happy.status}`);
  must(happy.toolCalls === 4, `도구 호출 ${happy.toolCalls}`);
  return `스텝 ${happy.steps.length} · 도구 ${happy.toolCalls} · 상태 ${happy.status}`;
});
await check('★승인 «전»에는 등재 도구가 거부된다', async () => {
  const { callTool } = await import('../app/tools.js');
  const r = await callTool('emit_record', GOOD_DRAFT, { ...ctx, approved: happy.approved });
  must(!r.ok && r.reason === 'not_approved', JSON.stringify(r));
  return 'not_approved';
});
await check('게이트가 통과 판정 (라이선스 PD · 중복확인 함)', () => {
  must(happy.gate && !happy.gate.blocked, JSON.stringify(happy.gate));
  return 'blocked=false';
});
await check('승인 + 사람 수정 → 등재된다', async () => {
  const out = await approveAndCommit(happy, { title: '사비니 여인의 납치(수정본)' }, ctx);
  must(out.ok, JSON.stringify(out));
  must(happy.status === 'done', happy.status);
  must(happy.record.title === '사비니 여인의 납치(수정본)', '사람 수정이 반영 안 됨');
  const c = happy.steps.at(-1);
  must(c.kind === 'commit' && c.editedFields.includes('title'), '수정 이력이 트레이스에 없음');
  return `등재됨 · 수정필드 ${c.editedFields.join(',')}`;
});
await check('요약이 병목을 보여 준다', () => {
  const s = summary(happy);
  must(s.toolCalls === 4 && s.steps >= 5, JSON.stringify(s));
  must(Object.keys(s.toolMs).length === 4, '도구별 소요시간이 없다');
  return `도구별 ms: ${Object.entries(s.toolMs).map(([k, v]) => `${k}=${v}`).join(' ')}`;
});

console.log('\n■ 2. ★안전 — 라이선스가 확인 안 되면 등재로 못 넘어간다');
await check('license=unknown 인데 finish 하면 게이트가 막는다', async () => {
  const r = newRun({ title: 'x', artist: 'y', backend: 'mock', model: 'mock' });
  const cfg = {
    complete: scripted([
      { thought: '중복 확인', action: { tool: 'archive_search', args: { q: 'Mercury' } } },
      { thought: '끝', finish: { identified: true, qid: 'Q1', confidence: 'low', draft: { ...GOOD_DRAFT, license: 'unknown' }, notes: '' } },
    ]),
  };
  await runToApproval(r, cfg, ctx);
  must(r.status === 'awaiting_approval', r.status);
  must(r.gate.blocked, '막지 않았다');
  must(r.gate.why.some((w) => w.includes('라이선스')), JSON.stringify(r.gate.why));
  return r.gate.why.join(' / ');
});
await check('중복 확인을 «건너뛰면» 게이트가 막는다', async () => {
  const r = newRun({ title: 'x', artist: 'y', backend: 'mock', model: 'mock' });
  const cfg = { complete: scripted([{ thought: '바로 끝', finish: { identified: true, draft: GOOD_DRAFT, notes: '' } }]) };
  await runToApproval(r, cfg, ctx);
  must(r.gate.blocked && r.gate.why.some((w) => w.includes('중복')), JSON.stringify(r.gate));
  return r.gate.why.join(' / ');
});
await check('모델이 스스로 stop 하면 그대로 멈춘다', async () => {
  const r = newRun({ title: 'x', artist: 'y', backend: 'mock', model: 'mock' });
  const cfg = { complete: scripted([{ thought: '못 찾음', stop: { reason: 'license_unknown', detail: '이미지가 없다' } }]) };
  await runToApproval(r, cfg, ctx);
  must(r.status === 'stopped' && r.stopReason.reason === 'license_unknown', JSON.stringify(r.stopReason));
  return r.stopReason.detail;
});
await check('★autoRepair — 모델이 중복확인을 건너뛰면 시스템이 대신 한다', async () => {
  const r = newRun({ title: 'Rape of the Sabine Women', artist: 'Giambologna', backend: 'mock', model: 'mock' });
  const cfg = { autoRepair: true, complete: scripted([{ thought: '바로 끝', finish: { identified: true, draft: GOOD_DRAFT, notes: '' } }]) };
  await runToApproval(r, cfg, ctx);
  must(r.repairs === 1, `보정 ${r.repairs}회`);
  must(!r.gate.blocked, `여전히 막힘: ${JSON.stringify(r.gate.why)}`);
  const rep = r.steps.find((s) => s.repaired);
  must(rep && rep.action.tool === 'archive_search', '보정 스텝이 트레이스에 없다');
  return `보정 1회 → 게이트 통과 · duplicateOf=${r.finish.duplicateOf}`;
});
await check('★autoRepair 여도 «라이선스»는 대신 판정하지 않는다', async () => {
  const r = newRun({ title: 'x', artist: 'y', backend: 'mock', model: 'mock' });
  const cfg = { autoRepair: true, complete: scripted([{ thought: '끝', finish: { identified: true, draft: { ...GOOD_DRAFT, license: 'unknown' }, notes: '' } }]) };
  await runToApproval(r, cfg, ctx);
  must(r.gate.blocked && r.gate.why.some((w) => w.includes('라이선스')), JSON.stringify(r.gate));
  return '라이선스는 여전히 막힘 — 조회가 아니라 판단이므로';
});
await check('사람이 거부할 수 있다', () => {
  const r = newRun({ title: 'x', artist: 'y', backend: 'mock', model: 'mock' });
  r.status = 'awaiting_approval';
  reject(r, '작가 동정이 틀렸다');
  must(r.status === 'stopped' && r.stopReason.reason === 'rejected_by_human', JSON.stringify(r.stopReason));
  return r.stopReason.detail;
});

console.log('\n■ 3. 종료 조건 — 무한 루프를 막는다');
/** 매번 «다른» 인자를 내는 가짜 모델 — 반복 탐지에 걸리지 않고 예산만 태운다. */
function wanderer(tool, key = 'q') {
  let i = 0;
  return async () => ({
    ok: true, usage: { in: 50, out: 20 }, ms: 2,
    text: JSON.stringify({ thought: `${++i}번째`, action: { tool, args: { [key]: `헤르메스${i}` } } }),
  });
}
await check('행동이 계속 달라도 maxSteps 에서 멈춘다', async () => {
  const r = newRun({ title: 'x', artist: 'y', backend: 'mock', model: 'mock' });
  await runToApproval(r, { limits: { ...LIMITS, maxSteps: 5 }, complete: wanderer('archive_search') }, ctx);
  must(r.status === 'stopped' && /최대 스텝/.test(r.stopReason.detail), JSON.stringify(r.stopReason));
  return r.stopReason.detail;
});
await check('maxToolCalls 로도 멈춘다', async () => {
  const r = newRun({ title: 'x', artist: 'y', backend: 'mock', model: 'mock' });
  await runToApproval(r, { limits: { ...LIMITS, maxSteps: 99, maxToolCalls: 3 }, complete: wanderer('archive_search') }, ctx);
  must(r.status === 'stopped' && /도구 호출/.test(r.stopReason.detail), JSON.stringify(r.stopReason));
  return `도구 ${r.toolCalls}회에서 정지`;
});
await check('★같은 호출 반복 — 먼저 «관찰로» 알려 주고, 계속하면 접는다', async () => {
  const r = newRun({ title: 'x', artist: 'y', backend: 'mock', model: 'mock' });
  const cfg = {
    limits: { ...LIMITS, maxSteps: 30, maxToolCalls: 30 },
    complete: scripted([{ thought: '또', action: { tool: 'archive_search', args: { q: '헤르메스' } } }]),
  };
  await runToApproval(r, cfg, ctx);
  must(r.status === 'stopped' && r.stopReason.reason === 'repeat_loop', JSON.stringify(r.stopReason));
  const nudge = r.steps.find((s) => s.observation?.reason === 'repeated_call');
  must(nudge, '중단 전에 «알려 주는» 스텝이 없다');
  must(r.toolCalls === 2, `실제 도구 호출이 ${r.toolCalls}회 — 반복분이 API 로 새어 나갔다`);
  return `2회 실호출 → 관찰로 경고 → ${r.stopReason.detail}`;
});
await check('벽시계로도 멈춘다', async () => {
  const r = newRun({ title: 'x', artist: 'y', backend: 'mock', model: 'mock' });
  r.startedAt = Date.now() - 999999;
  const cfg = { complete: scripted([{ thought: 'x', action: { tool: 'archive_search', args: { q: 'a' } } }]) };
  await runToApproval(r, cfg, ctx);
  must(/제한 시간/.test(r.stopReason.detail), JSON.stringify(r.stopReason));
  return r.stopReason.detail;
});

console.log('\n■ 4. 형식이 깨진 응답 — 두 번은 봐주고 세 번째에 접는다');
await check('JSON 아닌 응답을 2회까지 견딘다', async () => {
  const r = newRun({ title: 'x', artist: 'y', backend: 'mock', model: 'mock' });
  const cfg = { complete: scripted(['죄송합니다, 무엇을 도와드릴까요?']) };
  await runToApproval(r, cfg, ctx);
  must(r.status === 'failed' && r.stopReason.reason === 'parse_fail', JSON.stringify(r.stopReason));
  must(r.parseFails === 3, `parseFails=${r.parseFails}`);
  must(r.steps[0].raw.includes('죄송'), '원문이 트레이스에 안 남았다');
  return `3회째에 중단 · 원문 보존됨`;
});
await check('★finish 를 «도구»로 부른 응답을 받아 준다 (실측 실패 유형)', async () => {
  const r = newRun({ title: 'x', artist: 'y', backend: 'mock', model: 'mock' });
  const cfg = {
    complete: scripted([
      { thought: '중복 확인', action: { tool: 'archive_search', args: { q: 'Mercury' } } },
      // qwen3.5:2b 가 실제로 낸 모양 — 이걸 안 받아 주면 5회를 헛돈다
      { thought: '끝', action: { tool: 'finish', args: { identified: true, draft: GOOD_DRAFT, notes: '' } } },
    ]),
  };
  await runToApproval(r, cfg, ctx);
  must(r.status === 'awaiting_approval', `상태 ${r.status}`);
  must(r.finish?.draft?.origTitle === GOOD_DRAFT.origTitle, '초안이 유실됨');
  must(r.parseFails === 0, `parseFails=${r.parseFails}`);
  return 'action.tool=finish → finish 로 정규화됨';
});
await check('★action 과 finish 를 «둘 다» 내면 finish 가 이긴다 (실측 실패 유형)', async () => {
  const r = newRun({ title: 'x', artist: 'y', backend: 'mock', model: 'mock' });
  const cfg = {
    complete: scripted([
      { thought: '중복 확인', action: { tool: 'archive_search', args: { q: 'Mercury' } } },
      // 모델이 실제로 낸 모양 — 초안이 «다 들어 있는데» 버려지고 있었다
      { thought: '끝', action: { tool: 'archive_search', args: { q: '또' } }, finish: { identified: true, draft: GOOD_DRAFT, notes: '' } },
    ]),
  };
  await runToApproval(r, cfg, ctx);
  must(r.status === 'awaiting_approval', `상태 ${r.status}`);
  must(r.finish?.draft?.origTitle === GOOD_DRAFT.origTitle, '초안이 유실됨');
  must(r.toolCalls === 1, `도구 ${r.toolCalls}회 — finish 인데 도구를 또 불렀다`);
  return '초안 보존 · 도구 재호출 없음';
});
await check('action 을 빠뜨린 {tool,args} 도 받아 준다', async () => {
  const r = newRun({ title: 'x', artist: 'y', backend: 'mock', model: 'mock' });
  const cfg = {
    complete: scripted([
      { thought: 'x', tool: 'archive_search', args: { q: '헤르메스' } },
      { thought: '끝', stop: { reason: 'other', detail: 'ok' } },
    ]),
  };
  await runToApproval(r, cfg, ctx);
  must(r.toolCalls === 1 && r.parseFails === 0, `호출 ${r.toolCalls} / 파싱실패 ${r.parseFails}`);
  return '정규화됨';
});
await check('코드펜스로 감싼 JSON 은 판다', async () => {
  const r = newRun({ title: 'x', artist: 'y', backend: 'mock', model: 'mock' });
  const cfg = {
    complete: scripted([
      '여기 있습니다:\n```json\n{"thought":"검색","action":{"tool":"archive_search","args":{"q":"헤르메스"}}}\n```\n이상입니다.',
      { thought: '끝', stop: { reason: 'other', detail: '테스트' } },
    ]),
  };
  await runToApproval(r, cfg, ctx);
  must(r.toolCalls === 1, `도구 호출 ${r.toolCalls}`);
  must(r.parseFails === 0, `parseFails=${r.parseFails}`);
  return '잡담·코드펜스를 견딤';
});

console.log('\n■ 5. 도구가 실패해도 루프는 «관찰»하고 계속 간다');
await check('없는 qid → not_found 가 관찰로 들어오고 다음 행동을 한다', async () => {
  const r = newRun({ title: 'x', artist: 'y', backend: 'mock', model: 'mock' });
  const cfg = {
    complete: scripted([
      { thought: '틀린 qid 로 시도', action: { tool: 'wd_entity', args: { qid: 'Q999999999' } } },
      { thought: '다시 검색', action: { tool: 'archive_search', args: { q: '헤르메스' } } },
      { thought: '끝', stop: { reason: 'other', detail: 'ok' } },
    ]),
  };
  await runToApproval(r, cfg, ctx);
  const first = r.steps[0];
  must(first.observation.ok === false, '실패가 관찰로 안 들어옴');
  must(r.toolCalls === 2, `${r.toolCalls}회`);
  must(r.status === 'stopped' && r.stopReason.detail === 'ok', JSON.stringify(r.stopReason));
  return `1번째 관찰 reason=${first.observation.reason} → 계속 진행`;
});
await check('없는 도구 이름을 불러도 죽지 않는다', async () => {
  const r = newRun({ title: 'x', artist: 'y', backend: 'mock', model: 'mock' });
  const cfg = {
    complete: scripted([
      { thought: '?', action: { tool: 'google_search', args: {} } },
      { thought: '끝', stop: { reason: 'other', detail: 'ok' } },
    ]),
  };
  await runToApproval(r, cfg, ctx);
  must(r.steps[0].observation.reason === 'unknown_tool', JSON.stringify(r.steps[0].observation));
  return 'unknown_tool 로 관찰됨';
});

console.log('\n■ 6. 중단·재개 — 상태가 직렬화되고 이어진다');
await check('직렬화 → 역직렬화 후 이어서 진행된다', async () => {
  const r = newRun({ title: 'Flying Mercury', artist: 'Giambologna', backend: 'mock', model: 'mock' });
  const script = [
    { thought: '1', action: { tool: 'archive_search', args: { q: 'Mercury' } } },
    { thought: '2', action: { tool: 'archive_search', args: { q: '헤르메스' } } },
    { thought: '끝', finish: { identified: true, draft: GOOD_DRAFT, notes: '' } },
  ];
  // 한 스텝만 진행하고 «저장»한다
  await step(r, { complete: scripted(script) }, ctx);
  const saved = JSON.parse(JSON.stringify(r));
  must(saved.steps.length === 1, '스텝 1개여야 함');
  // 새 객체로 되살려 «남은 대본»으로 계속
  const revived = JSON.parse(JSON.stringify(saved));
  await runToApproval(revived, { complete: scripted(script.slice(1)) }, ctx);
  must(revived.status === 'awaiting_approval', revived.status);
  must(revived.steps.length === 3, `스텝 ${revived.steps.length}`);
  must(revived.steps[0].action.args.q === 'Mercury', '앞 스텝이 유실됨');
  return `1스텝에서 끊고 재개 → 총 ${revived.steps.length}스텝, 앞 기록 보존`;
});
await check('run 객체에 함수·순환참조가 없다 (저장 가능)', () => {
  const s = JSON.stringify(happy);
  must(s.length > 100, '직렬화 결과가 비었다');
  must(!/\[object|undefined/.test(s.slice(0, 4000)), '직렬화 이상');
  return `${(s.length / 1024).toFixed(1)} KB`;
});

console.log('\n■ 7. 모델에게 쓰기 도구를 «보여 주지도» 않는다');
await check('도구 카탈로그에 emit_record 가 없다', async () => {
  const r = newRun({ title: 'x', artist: 'y', backend: 'mock', model: 'mock' });
  let seen = '';
  const cfg = {
    complete: async (_c, { messages }) => {
      seen = messages[0].content;
      return { ok: true, text: JSON.stringify({ thought: 'x', stop: { reason: 'other', detail: 'ok' } }), usage: { in: 1, out: 1 }, ms: 1 };
    },
  };
  await runToApproval(r, cfg, ctx);
  must(!seen.includes('emit_record'), 'emit_record 가 카탈로그에 노출됨');
  must(seen.includes('wd_search') && seen.includes('archive_search'), '읽기 도구가 안 보임');
  return '읽기 5종만 노출';
});

console.log('\n■ 8. 두 번째 워크플로 — 큐레이션 (루프·승인·트레이스를 그대로 재사용)');
// ⚠myth 값은 'greek' 이 아니라 'greco-roman' 이다 — slug 접두로 고른다(시험 데이터가 조용히 비면 검사가 무의미해진다)
const realSlugs = archive.filter((x) => x.slug.startsWith('greek-')).slice(0, 9).map((x) => x.slug);
if (realSlugs.length !== 9) { console.error('시험 데이터 준비 실패: 표본 ' + realSlugs.length + '점'); process.exit(1); }
const EXH = {
  title: '변신 — 모습이 바뀌는 순간',
  statement: '신화에서 변신은 도피이자 처벌이며 구원이다.',
  sections: [
    { name: '1부 · 쫓김', wallText: 'ㄱ', works: realSlugs.slice(0, 3) },
    { name: '2부 · 굳어짐', wallText: 'ㄴ', works: realSlugs.slice(3, 6) },
    { name: '3부 · 다시 태어남', wallText: 'ㄷ', works: realSlugs.slice(6, 9) },
  ],
};
await check('큐레이션 워크플로가 «다른» 도구 목록을 본다', async () => {
  const r = newRun({ title: '변신', backend: 'mock', model: 'mock', workflow: 'curate' });
  let seen = '';
  const cfg = {
    workflow: 'curate',
    complete: async (_c, { messages, system }) => {
      seen = messages[0].content + '\n@@SYS@@' + system;
      return { ok: true, text: JSON.stringify({ thought: 'x', stop: { reason: 'other', detail: 'ok' } }), usage: { in: 1, out: 1 }, ms: 1 };
    },
  };
  await runToApproval(r, cfg, ctx);
  must(seen.includes('archive_facets'), '큐레이션 전용 도구가 안 보인다');
  must(!seen.includes('### wd_search'), '등재 전용 도구가 새어 나왔다');
  must(!seen.includes('emit_exhibition\n'), 'emit_exhibition 이 카탈로그에 노출됨');
  must(seen.includes('전시 기획자'), '큐레이션 시스템 프롬프트가 아니다');
  must(seen.includes('전시 주제:'), '작업 설명이 등재용 그대로다');
  return '도구 3종만 · 전용 프롬프트';
});
await check('★지어낸 slug 가 섞이면 게이트가 막는다', async () => {
  const r = newRun({ title: '변신', backend: 'mock', model: 'mock', workflow: 'curate' });
  const fake = JSON.parse(JSON.stringify(EXH));
  fake.sections[0].works[0] = 'greek-이건없는작품';
  const cfg = {
    workflow: 'curate',
    complete: scripted([
      { thought: '검색', action: { tool: 'archive_search', args: { q: '변신' } } },
      { thought: '끝', finish: { draft: fake, notes: '' } },
    ]),
  };
  await runToApproval(r, cfg, ctx);
  must(r.status === 'awaiting_approval', r.status);
  must(r.gate.blocked && r.gate.why.some((w) => w.includes('없는 작품')), JSON.stringify(r.gate));
  return r.gate.why[0];
});
await check('archive_search 를 한 번도 안 부르면 막는다', async () => {
  const r = newRun({ title: '변신', backend: 'mock', model: 'mock', workflow: 'curate' });
  const cfg = { workflow: 'curate', complete: scripted([{ thought: '바로 끝', finish: { draft: EXH, notes: '' } }]) };
  await runToApproval(r, cfg, ctx);
  must(r.gate.blocked && r.gate.why.some((w) => w.includes('archive_search')), JSON.stringify(r.gate));
  return r.gate.why.join(' / ');
});
await check('autoRepair 는 큐레이션에 «끼어들지 않는다»', async () => {
  const r = newRun({ title: '변신', backend: 'mock', model: 'mock', workflow: 'curate' });
  const cfg = { workflow: 'curate', autoRepair: true, complete: scripted([{ thought: '끝', finish: { draft: EXH, notes: '' } }]) };
  await runToApproval(r, cfg, ctx);
  must(!r.repairs, `보정이 ${r.repairs}회 일어남 — 큐레이션엔 중복확인 개념이 없다`);
  return '보정 0회 — 워크플로마다 다른 규칙';
});
await check('정상 경로 → 승인 → emit_exhibition 으로 확정된다', async () => {
  const r = newRun({ title: '변신', backend: 'mock', model: 'mock', workflow: 'curate' });
  const cfg = {
    workflow: 'curate',
    complete: scripted([
      { thought: '분포 확인', action: { tool: 'archive_facets', args: { by: 'myth' } } },
      { thought: '검색', action: { tool: 'archive_search', args: { q: '변신 다프네', topK: 8 } } },
      { thought: '끝', finish: { draft: EXH, notes: '' } },
    ]),
  };
  await runToApproval(r, cfg, ctx);
  must(!r.gate.blocked, JSON.stringify(r.gate));
  const out = await approveAndCommit(r, {}, ctx, cfg);
  must(out.ok, JSON.stringify(out));
  must(r.record.workCount === 9, `작품 ${r.record.workCount}점`);
  must(r.status === 'done', r.status);
  return `${r.record.workCount}점 · ${r.record.sections.length}구획 · emit_exhibition 으로 확정`;
});
await check('승인 «전»에는 emit_exhibition 이 거부된다', async () => {
  const { callTool } = await import('../app/tools.js');
  const out = await callTool('emit_exhibition', EXH, { ...ctx, approved: false });
  must(!out.ok && out.reason === 'not_approved', JSON.stringify(out));
  return 'not_approved';
});

console.log('\n' + '='.repeat(56));
console.log(`통과 ${pass} · 실패 ${fail}`);
for (const f of FAILS) console.log('  ✗ ' + f);
process.exit(fail ? 1 : 0);
