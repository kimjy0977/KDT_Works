// 에이전트 루프 — 계획 → 도구 호출 → 관찰 → 다음 행동.
//
// 이 파일이 지키는 네 가지
//   ① 상태가 «직렬화 가능»하다. 그래서 새로고침해도 이어진다.
//   ② 종료 조건이 «셋» 있다 (스텝·도구호출·벽시계). 하나라도 걸리면 멈춘다.
//   ③ 승인 게이트가 «루프 안»에 있다. 모델이 아무리 우겨도 승인 전에는 등재가 안 된다.
//   ④ 모든 스텝이 트레이스로 남는다 — 무엇을 왜 불렀고 무엇이 돌아왔는지.

import { callTool, toolSpecs } from './tools.js';
import { complete, extractJSON, estimateCost } from './llm.js';

export const LIMITS = { maxSteps: 12, maxToolCalls: 20, wallClockMs: 180000, maxParseFails: 2 };

export const PHASES = [
  { id: 'identify', label: '동정', hint: '이 작품이 Wikidata의 어느 엔티티인지 확정' },
  { id: 'facts', label: '사실 수집', hint: '제작연도·재료·소장처·사조·묘사대상' },
  { id: 'license', label: '라이선스', hint: '이미지 저작권 판정 — 불명이면 중단' },
  { id: 'dedupe', label: '아카이브 대조', hint: '중복 등재 여부와 연결 후보' },
  { id: 'draft', label: '해설 초안', hint: '한국어 4단 초안' },
  { id: 'approval', label: '사람 승인', hint: '★사람이 확인해야 넘어간다' },
  { id: 'commit', label: '등재', hint: 'emit_record' },
];

const SYSTEM = `당신은 신화 명화 아카이브의 «등재 담당»입니다.
작품 하나의 제목과 작가를 받아, 공개 데이터에서 사실을 캐고 라이선스를 판정하고
한국어 해설 초안까지 만들어 «사람의 승인 앞에» 갖다 놓는 것이 임무입니다.

## 반드시 지킬 것

1. **한 번에 «행동 하나»** 만 고릅니다. 결과를 본 뒤 다음을 정합니다.
2. **모르는 것을 지어내지 않습니다.** 자료에 없으면 해당 필드를 null 로 두고 notes 에 이유를 적습니다.
   미술 정보에서 그럴듯한 오답은 없느니만 못합니다.
3. **라이선스가 'unknown' 이거나 'restricted' 면 등재하지 않습니다.** stop 으로 끝내고 이유를 적습니다.
4. **finish 하기 전에 archive_search 로 중복 등재를 반드시 한 번 확인**합니다.
5. emit_record 는 부르지 않습니다. 사람이 승인하면 시스템이 부릅니다.

## 출력 형식 — JSON 객체 «하나»만. 설명·코드펜스 없이.

⚠ **finish 와 stop 은 «도구가 아닙니다».** {"action":{"tool":"finish",...}} 라고 쓰지 마세요.
아래 세 가지 «최상위 키» 중 정확히 하나만 씁니다: action · finish · stop.

도구를 하나 고를 때 (도구 이름은 위 목록에 있는 것만):
{"thought":"왜 이걸 하는지 한 문장","action":{"tool":"도구이름","args":{...}}}

충분히 모았을 때 (action 을 쓰지 말고 finish 를 «최상위»에):
{"thought":"...","finish":{
  "identified": true,
  "qid":"Q...",
  "confidence":"high|medium|low",
  "draft":{
    "title":"한국어 제목","origTitle":"원제","artist":"작가(한국어)",
    "inception":"제작 시기 또는 null","material":"매체 또는 null",
    "collection":"소장처 또는 null","era":"사조 또는 null","people":["등장인물"],
    "license":"판정 결과","imageUrl":"이미지 URL 또는 null",
    "sources":["근거 URL"],
    "sections":{"meta":"기본정보 한 문단","description":"작품 해설","myth":"신화 배경","insight":"감상 포인트"}
  },
  "duplicateOf": null,
  "notes":"확정하지 못한 것과 그 이유"
}}

진행할 수 없을 때:
{"thought":"...","stop":{"reason":"license_unknown|not_found|other","detail":"..."}}`;

const CURATE_SYSTEM = `당신은 신화 명화 아카이브의 «전시 기획자»입니다.
주제 한 줄을 받아, 아카이브 982점 중에서 작품을 골라 동선과 벽면 텍스트까지 갖춘
전시 구성 초안을 만들어 «사람의 승인 앞에» 갖다 놓는 것이 임무입니다.

## 반드시 지킬 것

1. **한 번에 «행동 하나»** 만 고릅니다. 결과를 본 뒤 다음을 정합니다.
2. **아카이브에 «있는» 작품만 고릅니다.** archive_search 가 실제로 돌려준 slug 만 씁니다.
   기억나는 명화를 적지 마세요 — 아카이브에 없으면 전시에 걸 수 없습니다.
3. **먼저 archive_facets 로 분포를 봅니다.** 어느 신화에 몇 점이 있는지 «추측하지 않고» 확인한 뒤
   주제에 맞는 검색어로 archive_search 를 부릅니다.
4. ★**archive_search 는 «3~5회면 충분»합니다.** 그 뒤에는 «더 찾지 말고» 지금까지 나온 후보에서 골라
   finish 하세요. **앞선 검색 결과는 이 대화에 그대로 남아 있습니다 — 다시 찾을 필요가 없습니다.**
   같은 결과가 또 나오면 «이미 충분히 모았다»는 뜻입니다.
   ⚠ 「신화 이름」(그리스로마 등)으로는 검색되지 않습니다. **주제어·인물·사건**으로 찾으세요.
5. **6~12점**을 고르고 **2~3구획**으로 나눕니다. 구획마다 벽면 텍스트를 씁니다.
   ⚠ **action 과 finish 를 «같이» 쓰지 마세요.** 끝낼 거면 finish «하나»만 냅니다.
6. emit_exhibition 은 부르지 않습니다. 사람이 승인하면 시스템이 부릅니다.

## 출력 형식 — JSON 객체 «하나»만. 설명·코드펜스 없이.

⚠ **finish 와 stop 은 «도구가 아닙니다».** 최상위 키는 action · finish · stop 중 하나입니다.

도구를 고를 때:
{"thought":"왜 이걸 하는지 한 문장","action":{"tool":"도구이름","args":{...}}}

충분히 모았을 때:
{"thought":"...","finish":{
  "draft":{
    "title":"전시 제목",
    "statement":"기획 의도 한 문단",
    "sections":[
      {"name":"구획 이름","wallText":"벽면 텍스트","works":["아카이브 slug", "..."]}
    ]
  },
  "notes":"주제에 맞는 작품을 충분히 찾지 못했다면 여기에 적습니다"
}}

진행할 수 없을 때:
{"thought":"...","stop":{"reason":"not_found|other","detail":"..."}}`;

/**
 * 워크플로 정의. 루프·상태·트레이스·승인은 «그대로» 쓰고 이것만 갈아 끼운다.
 * ★쓰기 도구는 워크플로마다 «하나»뿐이고, 어느 쪽도 모델에게 보여 주지 않는다.
 */
export const WORKFLOWS = {
  intake: {
    id: 'intake',
    label: '등재 — 작품 한 점을 아카이브에 올린다',
    system: null,          // 아래에서 SYSTEM 을 넣는다 (선언 순서 때문)
    tools: ['wd_search', 'wd_entity', 'wd_sparql', 'commons_file', 'archive_search'],
    emit: 'emit_record',
    inputs: [['title', '제목'], ['artist', '작가']],
    // 실측 — 등재는 4~5스텝이면 끝난다. 예산을 절반(6스텝·90초)으로 줄여도 결과가 «동일»했다.
    limits: { maxSteps: 8, maxToolCalls: 14, wallClockMs: 150000 },
    gate(run) {
      const lic = String(run.finish?.draft?.license || '').toLowerCase();
      const licenseOk = /pd|public domain|cc/.test(lic);
      const dedupeChecked = run.steps.some((s) => s.kind === 'act' && s.action.tool === 'archive_search');
      return {
        blocked: !licenseOk || !dedupeChecked,
        why: [
          !licenseOk ? '라이선스가 PD/CC 로 확인되지 않았습니다' : null,
          !dedupeChecked ? 'archive_search 로 중복 등재를 확인하지 않았습니다' : null,
        ].filter(Boolean),
      };
    },
  },
  curate: {
    id: 'curate',
    label: '큐레이션 — 주제 하나로 전시를 구성한다',
    system: CURATE_SYSTEM,
    tools: ['archive_facets', 'archive_search', 'wd_entity'],
    emit: 'emit_exhibition',
    inputs: [['title', '전시 주제']],
    // ★큐레이션은 «검색을 여러 번» 해야 한다 — 분포 확인 + 주제어 3~6회 + 마무리.
    //   등재와 같은 예산(10스텝)을 줬더니 «모으다가 예산이 끝나» 승인 도달 0% 가 나왔다.
    //   워크플로가 다르면 예산도 달라야 한다.
    limits: { maxSteps: 18, maxToolCalls: 24, wallClockMs: 300000 },
    gate(run, ctx) {
      const d = run.finish?.draft || {};
      const secs = Array.isArray(d.sections) ? d.sections : [];
      const slugs = secs.flatMap((s) => s.works || []);
      const known = new Set((ctx?.archive || []).map((x) => x.slug));
      // ★가장 중요한 검사 — 지어낸 작품이 섞였는가. 전시에 «없는 그림»이 걸리면 결과물이 아니다.
      const unknown = slugs.filter((s) => !known.has(s));
      const searched = run.steps.some((s) => s.kind === 'act' && s.action.tool === 'archive_search');
      return {
        blocked: unknown.length > 0 || slugs.length < 6 || !searched,
        why: [
          unknown.length ? `아카이브에 없는 작품이 ${unknown.length}점 섞였습니다: ${unknown.slice(0, 3).join(', ')}` : null,
          slugs.length < 6 ? `작품이 ${slugs.length}점뿐입니다 (최소 6점)` : null,
          !searched ? 'archive_search 를 한 번도 부르지 않았습니다' : null,
        ].filter(Boolean),
        stats: { works: slugs.length, sections: secs.length, unknown: unknown.length },
      };
    },
  },
};

WORKFLOWS.intake.system = SYSTEM;

export function workflowOf(run, cfg) {
  return WORKFLOWS[cfg?.workflow || run?.workflow || 'intake'] || WORKFLOWS.intake;
}

function toolCatalog(wf) {
  const allow = new Set(wf.tools);
  return toolSpecs()
    .filter((t) => allow.has(t.name))   // 쓰기 도구는 모델에게 «보여 주지도» 않는다
    .map((t) => `### ${t.name}\n${t.description}\n입력 스키마: ${JSON.stringify(t.input_schema)}`)
    .join('\n\n');
}

/** 도구 결과를 모델에 돌려줄 때 줄인다 — 컨텍스트가 터지면 루프가 조용히 망가진다. */
function summarize(name, out) {
  if (!out.ok) return { ok: false, reason: out.reason, detail: String(out.detail || '').slice(0, 200) };
  const c = { ok: true };
  if (name === 'wd_search') { c.results = out.results.slice(0, 5); c.empty = out.empty; }
  else if (name === 'wd_entity') c.entity = out.entity;
  else if (name === 'wd_sparql') { c.works = out.works.slice(0, 20); c.empty = out.empty; }
  else if (name === 'commons_file') { c.file = out.file; c.verdict = out.verdict; }
  else if (name === 'archive_search') {
    c.hits = out.hits.map((h) => ({ slug: h.slug, title: h.title, origTitle: h.origTitle, artist: h.artist, score: h.score }));
  } else if (name === 'archive_facets') { c.by = out.by; c.total = out.total; c.facets = out.facets; }
  else Object.assign(c, out);
  return c;
}

/**
 * 모델이 «거의 맞게» 낸 응답을 우리 형식으로 맞춘다.
 *
 * ★2026-09-09 실측 — qwen3.5:2b 는 finish 를 «도구»로 취급해
 *   {"action":{"tool":"finish","args":{...}}} 를 냈고, 파서가 안 받자 «5회 같은 응답을 반복»했다.
 *   모델의 해석이 부자연스럽지도 않다(도구 목록만 준 상태니까). 프롬프트도 고쳤지만,
 *   받아 주는 쪽이 너그러운 편이 훨씬 튼튼하다. 형식을 못 맞췄다고 일을 버리지 않는다.
 */
export function normalize(p) {
  if (!p || typeof p !== 'object') return p;
  // ★실측 2026-09-09 — 모델이 action 과 finish 를 «동시에» 내는 일이 있다.
  //   큐레이션 평가에서 draft(7점 선정·제목·기획의도)가 «다 들어 있는데» 버려졌다.
  //   둘 다 있으면 «끝내겠다»는 쪽이 더 강한 의사표시다. finish 를 택한다.
  if (p.finish && p.action) return { thought: p.thought, finish: p.finish };
  if (p.stop && p.action) return { thought: p.thought, stop: p.stop };
  const t = p.action?.tool;
  if (t === 'finish' || t === 'done' || t === 'complete') {
    return { thought: p.thought, finish: p.action.args || p.action.arguments || {} };
  }
  if (t === 'stop' || t === 'abort' || t === 'give_up') {
    const a = p.action.args || {};
    // ★detail 이 비면 «왜 멈췄는지»가 통째로 사라진다.
    //   실측 2026-09-10 — 평가 174건 중 15건이 reason='other', detail='' 로
    //   떨어져 「기타」로만 분류됐다. 무엇 때문에 멈췄는지 아무도 모른다.
    //   모델은 thought 를 같이 보낸다. 그걸 쓰면 «왜»가 남는다.
    return { thought: p.thought,
      stop: { reason: a.reason || 'other',
              detail: a.detail || p.thought || '(모델이 사유를 남기지 않음)' } };
  }
  // {"tool":"...","args":{...}} 처럼 action 을 빠뜨린 경우도 받아 준다
  if (!p.action && !p.finish && !p.stop && p.tool) {
    return { thought: p.thought, action: { tool: p.tool, args: p.args || p.arguments || {} } };
  }
  return p;
}

/** 같은 호출을 되풀이하는가. 되풀이는 «관찰로» 알려 준다 — 조용히 죽이지 않는다. */
function repeatCount(run, tool, args) {
  const key = tool + '|' + JSON.stringify(args || {});
  let n = 0;
  for (let i = run.steps.length - 1; i >= 0; i--) {
    const s = run.steps[i];
    if (s.kind !== 'act') continue;
    if (s.action.tool + '|' + JSON.stringify(s.action.args || {}) === key) n++;
    else break;
  }
  return n;
}

export function newRun({ title, artist, backend, model, workflow = 'intake' }) {
  return {
    runId: `run-${Date.now()}-${Math.floor(Math.random() * 1e4)}`,
    input: { title, artist },
    workflow,
    backend, model,
    startedAt: Date.now(),
    phase: 'identify',
    steps: [],            // 트레이스. 이게 곧 «관찰 가능성»이다.
    toolCalls: 0,
    parseFails: 0,
    usage: { in: 0, out: 0 },
    status: 'running',    // running | awaiting_approval | done | stopped | failed
    finish: null,
    approved: false,
    record: null,
  };
}

function budgetLeft(run, limits) {
  const elapsed = Date.now() - run.startedAt;
  if (run.steps.length >= limits.maxSteps) return { over: true, why: `최대 스텝 ${limits.maxSteps} 도달` };
  if (run.toolCalls >= limits.maxToolCalls) return { over: true, why: `최대 도구 호출 ${limits.maxToolCalls} 도달` };
  if (elapsed >= limits.wallClockMs) return { over: true, why: `제한 시간 ${limits.wallClockMs / 1000}초 초과` };
  return { over: false, elapsed };
}

/** 지금까지의 트레이스를 모델이 읽을 대화로 바꾼다. 상태에서 «파생»하므로 재개해도 같다. */
function buildMessages(run, wf) {
  const task = wf.id === 'curate'
    ? `## 이번 작업\n전시 주제: ${run.input.title}\n\n이 주제로 전시 구성 초안을 만들어 주세요. 행동을 하나 고르세요.`
    : `## 이번 작업\n제목: ${run.input.title}\n작가: ${run.input.artist || '(모름)'}\n\n이 작품의 등재 초안을 만들어 주세요. 행동을 하나 고르세요.`;
  const msgs = [{
    role: 'user',
    content: `## 쓸 수 있는 도구\n\n${toolCatalog(wf)}\n\n` + task,
  }];
  for (const s of run.steps) {
    if (s.kind !== 'act') continue;
    msgs.push({ role: 'assistant', content: JSON.stringify({ thought: s.thought, action: s.action }) });
    msgs.push({
      role: 'user',
      content: `도구 ${s.action.tool} 결과:\n${JSON.stringify(s.observation)}\n\n다음 행동을 고르세요.`,
    });
  }
  return msgs;
}

/**
 * 한 스텝 전진. 호출하는 쪽이 반복하므로 «중단·재개»가 자연스럽다.
 * @returns 갱신된 run
 */
export async function step(run, cfg, ctx, onEvent = () => {}) {
  if (run.status !== 'running') return run;
  const wf = workflowOf(run, cfg);

  const b = budgetLeft(run, { ...LIMITS, ...(wf.limits || {}), ...(cfg.limits || {}) });
  if (b.over) {
    run.status = 'stopped';
    run.stopReason = { reason: 'budget', detail: b.why };
    run.steps.push({ kind: 'stop', at: Date.now(), detail: b.why });
    onEvent(run);
    return run;
  }

  // ── ① 모델에 묻는다.
  //    cfg.complete 로 갈아끼울 수 있게 열어 둔다 — 데모 재생과 루프 시험이 여기로 들어온다.
  //    (모델을 안 부르고도 루프의 «구조»를 검사할 수 있어야 한다)
  const ask = cfg.complete || complete;
  const res = await ask(cfg, { system: wf.system, messages: buildMessages(run, wf) });
  if (!res.ok) {
    run.status = 'failed';
    run.stopReason = { reason: res.reason, detail: res.detail };
    run.steps.push({ kind: 'error', at: Date.now(), ms: res.ms, reason: res.reason, detail: res.detail });
    onEvent(run);
    return run;
  }
  run.usage.in += res.usage?.in || 0;
  run.usage.out += res.usage?.out || 0;

  // ── ② 판다. 실패는 «즉시 실패»가 아니라 «수리 요청»이다 — 두 번까지.
  const parsed = normalize(extractJSON(res.text));
  if (!parsed || (!parsed.action && !parsed.finish && !parsed.stop)) {
    run.parseFails++;
    run.steps.push({
      kind: 'parse_fail', at: Date.now(), ms: res.ms,
      raw: String(res.text || '').slice(0, 500),
      tokens: { in: res.usage?.in || 0, out: res.usage?.out || 0 },
    });
    if (run.parseFails > ({ ...LIMITS, ...(wf.limits || {}), ...(cfg.limits || {}) }).maxParseFails) {
      run.status = 'failed';
      run.stopReason = { reason: 'parse_fail', detail: `JSON 을 ${run.parseFails}회 못 냈습니다` };
    }
    onEvent(run);
    return run;
  }

  // ── ③ 끝내겠다고 한다
  if (parsed.finish) {
    // ★자동 보정 — 실측 2026-09-09: qwen3.5:2b 는 "finish 전에 archive_search 를 반드시" 라는
    //   지시를 «지키지 않고» 끝내려 했다. 소형 모델에서 흔한 일이다.
    //   중복 확인은 읽기 전용이고 8ms 짜리다. 사람을 부르기 전에 «시스템이» 한 번 해 준다.
    //   ⚠단, 라이선스 판정은 자동 보정하지 않는다 — 그건 판단이지 조회가 아니다.
    if (cfg.autoRepair && wf.id === 'intake' && !run.steps.some((s) => s.kind === 'act' && s.action.tool === 'archive_search')) {
      const q = parsed.finish.draft?.origTitle || parsed.finish.draft?.title || run.input.title;
      const obs = await callTool('archive_search', { q, topK: 5 }, { ...ctx, approved: false });
      run.toolCalls++;
      run.repairs = (run.repairs || 0) + 1;
      run.steps.push({
        kind: 'act', at: Date.now(), repaired: true,
        thought: '[시스템 보정] 모델이 중복 확인을 건너뛰어 대신 수행합니다',
        action: { tool: 'archive_search', args: { q, topK: 5 } },
        observation: summarize('archive_search', obs), toolMs: obs.ms,
      });
      // 이미 등재된 작품이면 사람에게 «중복»이라고 알려 준다
      const hit = obs.ok && obs.hits?.[0];
      if (hit && hit.score >= 40) parsed.finish.duplicateOf = hit.slug;
    }
    run.finish = parsed.finish;
    run.phase = 'approval';
    // ★루프가 «스스로» 안전 규칙을 다시 검사한다. 모델의 말을 믿지 않는다.
    //   무엇을 검사하는지는 워크플로가 정한다 — 등재는 «라이선스·중복», 큐레이션은 «지어낸 작품».
    run.gate = wf.gate(run, ctx);
    run.status = 'awaiting_approval';
    run.steps.push({
      kind: 'finish', at: Date.now(), ms: res.ms, thought: parsed.thought,
      finish: parsed.finish, gate: run.gate,
      tokens: { in: res.usage?.in || 0, out: res.usage?.out || 0 },
    });
    onEvent(run);
    return run;
  }

  // ── ④ 스스로 멈추겠다고 한다 (라이선스 불명 등)
  if (parsed.stop) {
    run.status = 'stopped';
    run.stopReason = parsed.stop;
    run.steps.push({
      kind: 'stop', at: Date.now(), ms: res.ms, thought: parsed.thought, detail: parsed.stop.detail,
      tokens: { in: res.usage?.in || 0, out: res.usage?.out || 0 },
    });
    onEvent(run);
    return run;
  }

  // ── ⑤ 도구를 부른다
  const { tool, args } = parsed.action || {};

  // ★같은 호출의 되풀이 — 조용히 돌게 두면 예산만 태운다.
  //   먼저 «관찰로» 알려 주고(모델이 스스로 빠져나올 기회), 그래도 계속하면 접는다.
  const rep = repeatCount(run, tool, args);
  if (rep >= 2) {
    const lim = { ...LIMITS, ...(wf.limits || {}), ...(cfg.limits || {}) };
    if (rep >= (lim.maxRepeat || 3)) {
      run.status = 'stopped';
      run.stopReason = { reason: 'repeat_loop', detail: `${tool} 을 같은 인자로 ${rep + 1}회 반복했습니다` };
      run.steps.push({ kind: 'stop', at: Date.now(), detail: run.stopReason.detail });
      onEvent(run);
      return run;
    }
    run.steps.push({
      kind: 'act', at: Date.now(), thought: parsed.thought, action: { tool, args },
      observation: { ok: false, reason: 'repeated_call',
        detail: `방금과 «똑같은» 호출입니다(${rep + 1}회째). 결과는 같습니다. 인자를 바꾸거나 다른 도구를 쓰거나 finish 로 끝내세요.` },
      toolMs: 0, modelMs: res.ms, tokens: { in: res.usage?.in || 0, out: res.usage?.out || 0 },
    });
    onEvent(run);
    return run;
  }

  const observation = await callTool(tool, args, { ...ctx, approved: run.approved });
  run.toolCalls++;
  if (tool === 'commons_file' && observation.ok) run.phase = 'dedupe';
  else if (tool === 'wd_entity' && observation.ok) run.phase = 'license';
  else if (tool === 'archive_search' && observation.ok) run.phase = 'draft';

  run.steps.push({
    kind: 'act', at: Date.now(),
    thought: parsed.thought, action: { tool, args },
    observation: summarize(tool, observation),
    toolMs: observation.ms, modelMs: res.ms,
    tokens: { in: res.usage?.in || 0, out: res.usage?.out || 0 },
  });
  onEvent(run);
  return run;
}

/** 승인 뒤에만 부를 수 있다. 여기가 «되돌리기 어려운 작업» 앞의 마지막 문이다. */
export async function approveAndCommit(run, edits, ctx, cfg) {
  if (run.status !== 'awaiting_approval') {
    return { ok: false, reason: 'not_ready', detail: `상태가 ${run.status} 입니다` };
  }
  const wf = workflowOf(run, cfg);
  run.approved = true;
  const draft = { ...(run.finish?.draft || {}), ...(edits || {}) };
  const out = await callTool(wf.emit, draft, { ...ctx, approved: true });
  if (!out.ok) { run.approved = false; return out; }
  run.record = out.record || out.exhibition;
  run.status = 'done';
  run.phase = 'commit';
  run.steps.push({ kind: 'commit', at: Date.now(), ms: out.ms, editedFields: Object.keys(edits || {}) });
  return out;
}

export function reject(run, why) {
  run.status = 'stopped';
  run.stopReason = { reason: 'rejected_by_human', detail: why || '사람이 거부했습니다' };
  run.steps.push({ kind: 'reject', at: Date.now(), detail: why });
  return run;
}

/** 실행 요약 — 어디가 병목인지 보려면 이게 필요하다. */
export function summary(run) {
  // ⚠저장본에서 되살린 run 은 일부 필드가 없을 수 있다 — 여기서 죽으면 재집계가 통째로 막힌다.
  if (!run || !Array.isArray(run.steps)) return { steps: 0, toolCalls: 0, usage: { in: 0, out: 0 }, toolMs: {}, costUsd: 0, wallMs: 0, modelMs: 0, toolMsTotal: 0 };
  const usage = run.usage || run.steps.reduce(
    (a, s) => ({ in: a.in + (s.tokens?.in || 0), out: a.out + (s.tokens?.out || 0) }), { in: 0, out: 0 });
  const startedAt = run.startedAt || run.steps[0]?.at || Date.now();
  const acts = run.steps.filter((s) => s.kind === 'act');
  const toolMs = {};
  for (const s of acts) toolMs[s.action.tool] = (toolMs[s.action.tool] || 0) + (s.toolMs || 0);
  const modelMs = run.steps.reduce((a, s) => a + (s.modelMs || s.ms || 0), 0);
  return {
    runId: run.runId,
    status: run.status,
    steps: run.steps.length,
    // 저장본에는 toolCalls 가 없을 수 있다 — 스텝에서 «세면» 된다
    toolCalls: run.toolCalls ?? acts.length,
    parseFails: run.parseFails,
    wallMs: (run.steps.at(-1)?.at || startedAt) - startedAt,
    modelMs,
    toolMsTotal: Object.values(toolMs).reduce((a, b) => a + b, 0),
    toolMs,
    usage,
    costUsd: estimateCost(run.model, usage),
  };
}

// ── 저장·재개. localStorage 가 없으면(Node) 메모리로 떨어진다.
const KEY = 'mq4.runs';
const mem = new Map();
const store = typeof localStorage === 'undefined' ? null : localStorage;

export function saveRun(run) {
  if (!store) { mem.set(run.runId, run); return; }
  try {
    const all = JSON.parse(store.getItem(KEY) || '{}');
    all[run.runId] = run;
    // 최근 20건만 남긴다 — 저장소가 꽉 차면 «조용히» 저장이 실패한다
    const ids = Object.keys(all).sort((a, b) => (all[b].startedAt || 0) - (all[a].startedAt || 0));
    for (const id of ids.slice(20)) delete all[id];
    store.setItem(KEY, JSON.stringify(all));
  } catch { /* 용량 초과 등 — 실행 자체를 막지는 않는다 */ }
}

export function loadRuns() {
  if (!store) return [...mem.values()];
  try {
    const all = JSON.parse(store.getItem(KEY) || '{}');
    return Object.values(all).sort((a, b) => (b.startedAt || 0) - (a.startedAt || 0));
  } catch { return []; }
}

export function loadRun(runId) {
  return loadRuns().find((r) => r.runId === runId) || null;
}

/** 끝까지 돌린다. 스텝마다 저장하므로 중간에 끊겨도 이어진다. */
export async function runToApproval(run, cfg, ctx, onEvent = () => {}) {
  while (run.status === 'running') {
    await step(run, cfg, ctx, onEvent);
    saveRun(run);
  }
  return run;
}
