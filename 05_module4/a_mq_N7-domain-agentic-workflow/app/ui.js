// 화면. 다섯 탭 — 실행 · 트레이스 · 승인 · 결과 · 평가.
//
// 이 파일이 지키는 것
//   ① 승인 화면은 «필드마다 근거»를 같이 보여 준다. 값만 보여 주면 확인이 아니라 서명이 된다.
//   ② 게이트가 막혀 있으면 승인 버튼이 «눌리지 않는다». 화면에서도 한 겹 더 막는다.
//   ③ 트레이스는 요약하지 않는다 — 인자와 결과 원문을 접어서라도 남긴다.
import { TOOLS } from './tools.js';
import { newRun, runToApproval, approveAndCommit, reject, summary, saveRun, loadRuns, PHASES, LIMITS, WORKFLOWS } from './agent.js';
import { BACKENDS, estimateCost } from './llm.js';

const $ = (s) => document.querySelector(s);
const el = (t, c, h) => { const e = document.createElement(t); if (c) e.className = c; if (h != null) e.innerHTML = h; return e; };
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[m]));

let archive = [];
let demoRuns = [];
let current = null;
let mode = 'demo';
let wfId = 'intake';
const cfgState = { ollamaModel: 'qwen3.5:2b', ollamaHost: 'http://localhost:11434', apiKey: '', apiModel: '' };

// ── 탭
$('#tabs').addEventListener('click', (e) => {
  const b = e.target.closest('button'); if (!b) return;
  for (const x of document.querySelectorAll('.tabs button')) x.classList.toggle('on', x === b);
  for (const s of document.querySelectorAll('.tab')) s.classList.toggle('on', s.id === 'tab-' + b.dataset.tab);
  if (b.dataset.tab === 'eval') loadEval();
});
const goTab = (name) => document.querySelector(`.tabs button[data-tab="${name}"]`).click();

// ── 워크플로 선택
const SAMPLES = {
  intake: [
    ['Rape of the Sabine Women', 'Giambologna'],
    ['The Birth of Venus', '산드로 보티첼리'],
    ['Apollo and Daphne', '잔 로렌초 베르니니'],
    ['The Flaying of Marsyas', '티치아노'],
  ],
  curate: [
    ['변신 — 모습이 바뀌는 순간', ''],
    ['물과 바다의 신들', ''],
    ['죽음과 저승으로 가는 길', ''],
    ['영웅의 시련', ''],
  ],
};
function renderWorkflows() {
  const box = $('#workflows'); box.innerHTML = '';
  for (const [k, v] of Object.entries(WORKFLOWS)) {
    const b = el('button', 'mode' + (k === wfId ? ' on' : ''),
      `<b>${esc(v.label)}</b><span>도구 ${v.tools.length}종 · 결과물 <code>${esc(v.emit)}</code></span>`);
    b.onclick = () => { wfId = k; renderWorkflows(); renderInputs(); };
    box.appendChild(b);
  }
}
function renderInputs() {
  const curate = wfId === 'curate';
  $('#inputHead').textContent = curate ? '전시 주제' : '작품 입력';
  $('#lblArtist').hidden = curate;
  $('#rowRepair').hidden = curate;
  $('#hintTitle').textContent = curate
    ? '한 줄이면 됩니다. 아카이브 982점 안에서 골라 줍니다'
    : '원제(영문)가 한국어보다 훨씬 잘 맞습니다';
  $('#lblTitle').firstChild.textContent = curate ? '주제 ' : '제목 ';
  $('#inTitle').placeholder = curate ? '변신 — 모습이 바뀌는 순간' : 'Rape of the Sabine Women';
  $('#inTitle').value = ''; $('#inArtist').value = '';
  const box = $('#samples'); box.innerHTML = '';
  for (const [t, a] of SAMPLES[wfId]) {
    const b = el('button', '', esc(t));
    b.onclick = () => { $('#inTitle').value = t; $('#inArtist').value = a; };
    box.appendChild(b);
  }
}

// ── 모드 선택
function renderModes() {
  const box = $('#modes'); box.innerHTML = '';
  for (const [k, v] of Object.entries(BACKENDS)) {
    const b = el('button', 'mode' + (k === mode ? ' on' : ''),
      `<b>${esc(v.label)}</b><span>${k === 'demo' ? '저장된 실행을 그대로 재생합니다' :
        v.needsLocal ? '내 컴퓨터에서 돕니다. 데이터가 나가지 않습니다' : '키는 브라우저에만 저장됩니다'}</span>`);
    b.onclick = () => { mode = k; renderModes(); renderModeCfg(); };
    box.appendChild(b);
  }
}
function renderModeCfg() {
  const box = $('#modeCfg'); box.innerHTML = '';
  if (mode === 'demo') {
    box.innerHTML = `<p class="note">키도 설치도 필요 없습니다. 아래 «저장된 실행» 중 하나를 고르면
      실제로 돌았던 트레이스가 단계별로 재생됩니다. — 저장본 ${demoRuns.length}건</p>`;
    return;
  }
  if (mode === 'ollama') {
    box.innerHTML = `<div class="row">
      <label>모델 <input id="cfgModel" value="${esc(cfgState.ollamaModel)}"></label>
      <label>주소 <input id="cfgHost" value="${esc(cfgState.ollamaHost)}"></label></div>
      <p class="note">⚠ 배포된 페이지에서 로컬 Ollama 를 부르려면 CORS 허용이 필요합니다 —
      <code>OLLAMA_ORIGINS</code> 에 <code>https://*.github.io</code> 를 넣고 Ollama 를 다시 시작하세요.
      <br>⚠ <code>qwen3.5</code> 계열은 <code>think</code> 를 끄지 않으면 한 스텝이 2분을 넘깁니다 — 이 앱은 자동으로 끕니다.</p>`;
    $('#cfgModel').oninput = (e) => cfgState.ollamaModel = e.target.value;
    $('#cfgHost').oninput = (e) => cfgState.ollamaHost = e.target.value;
    return;
  }
  const def = mode === 'anthropic' ? 'claude-haiku-4-5' : 'gpt-4o-mini';
  box.innerHTML = `<div class="row">
    <label>모델 <input id="cfgModel" value="${esc(cfgState.apiModel || def)}"></label>
    <label>API 키 <input id="cfgKey" type="password" placeholder="브라우저에만 저장됩니다" value="${esc(cfgState.apiKey)}"></label></div>
    <p class="note">키는 <b>이 브라우저 메모리에만</b> 있습니다. 저장하지도, 어디로 보내지도 않습니다.
    새로고침하면 사라집니다. 호출은 브라우저에서 제공사로 «직접» 갑니다.</p>`;
  cfgState.apiModel = cfgState.apiModel || def;
  $('#cfgModel').oninput = (e) => cfgState.apiModel = e.target.value;
  $('#cfgKey').oninput = (e) => cfgState.apiKey = e.target.value;
}

// ── 실행
function backendCfg() {
  if (mode === 'ollama') return { backend: 'ollama', model: cfgState.ollamaModel, host: cfgState.ollamaHost, numCtx: 16384 };
  if (mode === 'demo') return { backend: 'demo', model: 'demo' };
  return { backend: mode, model: cfgState.apiModel, apiKey: cfgState.apiKey };
}

async function start() {
  const title = $('#inTitle').value.trim();
  const artist = $('#inArtist').value.trim();
  if (!title) { $('#runNote').textContent = '제목을 넣어 주세요.'; return; }
  if (mode === 'demo') { $('#runNote').textContent = '데모 모드에서는 아래 저장된 실행을 골라 재생하세요.'; return; }
  if (BACKENDS[mode].needsKey && !cfgState.apiKey) { $('#runNote').textContent = 'API 키를 넣어 주세요.'; return; }

  const c = backendCfg();
  current = newRun({ title, artist, backend: c.backend, model: c.model, workflow: wfId });
  $('#btnRun').disabled = true;
  $('#runNote').textContent = '실행 중…';
  goTab('trace');
  try {
    await runToApproval(current, { ...c, workflow: wfId, autoRepair: $('#optRepair').checked, limits: LIMITS }, { archive },
      (r) => { renderTrace(r); });
  } finally {
    $('#btnRun').disabled = false;
    $('#runNote').textContent = '';
    renderTrace(current); renderApprove(current); renderHistory();
    if (current.status === 'awaiting_approval') goTab('approve');
  }
}

// ── 데모 재생: 저장된 트레이스를 한 스텝씩 되살린다
async function replay(saved) {
  current = JSON.parse(JSON.stringify(saved));
  const all = current.steps;
  current.steps = [];
  current.status = 'running';
  goTab('trace');
  for (const s of all) {
    current.steps.push(s);
    renderTrace(current);
    await new Promise((r) => setTimeout(r, 420));
  }
  current.status = saved.status;
  renderTrace(current); renderApprove(current);
  if (current.status === 'awaiting_approval') goTab('approve');
}

// ── 트레이스
function renderTrace(run) {
  if (!run) return;
  const s = summary(run);
  $('#runMeta').innerHTML =
    `<span>${esc(run.input.title)}${run.input.artist ? ' / ' + esc(run.input.artist) : ''}</span>` +
    `<span>${esc(run.backend)} · ${esc(run.model)}</span>` +
    `<span>상태 ${esc(run.status)}</span><span>스텝 ${s.steps}</span><span>도구 ${s.toolCalls}</span>` +
    `<span>${(s.wallMs / 1000).toFixed(1)}초</span>` +
    `<span>토큰 in ${s.usage.in} / out ${s.usage.out}</span>` +
    `<span>비용 ${s.costUsd ? '$' + s.costUsd.toFixed(4) : '$0 (로컬)'}</span>`;

  const done = new Set(run.steps.filter((x) => x.kind === 'act').map((x) => ({
    wd_search: 'identify', wd_sparql: 'identify', wd_entity: 'facts',
    commons_file: 'license', archive_search: 'dedupe',
  }[x.action.tool])).filter(Boolean));
  if (run.finish) done.add('draft');
  if (run.status === 'done') { done.add('approval'); done.add('commit'); }
  $('#phases').innerHTML = PHASES.map((p) =>
    `<span class="ph ${done.has(p.id) ? 'done' : run.phase === p.id ? 'now' : ''}" title="${esc(p.hint)}">${esc(p.label)}</span>`).join('');

  // 병목 — 모델 시간과 도구 시간을 갈라 본다
  const rows = [['모델 호출', s.modelMs]];
  for (const [k, v] of Object.entries(s.toolMs)) rows.push([k, v]);
  const max = Math.max(1, ...rows.map((r) => r[1]));
  $('#bottleneck').innerHTML = rows.map(([k, v]) =>
    `<div class="bar"><span class="lab">${esc(k)}</span>
     <span class="fill" style="width:${Math.round((v / max) * 62)}%"></span>
     <span class="v">${(v / 1000).toFixed(1)}s</span></div>`).join('') +
    `<p class="note">모델이 ${Math.round(s.modelMs * 100 / Math.max(1, s.modelMs + s.toolMsTotal))}%,
     도구가 ${Math.round(s.toolMsTotal * 100 / Math.max(1, s.modelMs + s.toolMsTotal))}% 를 씁니다.</p>`;

  const box = $('#trace'); box.innerHTML = '';
  run.steps.forEach((st, i) => {
    if (st.kind === 'act') {
      const ok = st.observation?.ok;
      const d = el('div', 'step ' + (st.repaired ? 'sys' : ok ? 'ok' : 'bad'));
      d.innerHTML =
        `<div class="h"><span class="n">${i + 1}</span><span class="tool">${esc(st.action.tool)}</span>` +
        (st.repaired ? '<span class="badge warn">시스템 보정</span>' : '') +
        (ok ? '' : `<span class="badge bad">${esc(st.observation?.reason || '실패')}</span>`) +
        `<span class="ms">${st.toolMs}ms${st.modelMs ? ' (모델 ' + (st.modelMs / 1000).toFixed(1) + 's)' : ''}</span></div>` +
        `<div class="th">${esc(st.thought || '')}</div>` +
        `<pre>${esc(JSON.stringify(st.action.args))}</pre>` +
        `<details><summary>결과 원문</summary><pre>${esc(JSON.stringify(st.observation, null, 1))}</pre></details>`;
      box.appendChild(d);
    } else if (st.kind === 'parse_fail') {
      box.appendChild(el('div', 'step bad',
        `<div class="h"><span class="n">${i + 1}</span><span class="tool">형식 오류</span>
         <span class="badge bad">JSON 아님</span><span class="ms">${st.ms}ms</span></div>
         <div class="th">모델이 뱉은 원문을 그대로 남깁니다 — 무엇이 잘못됐는지 보려면 이게 필요합니다.</div>
         <pre>${esc(st.raw)}</pre>`));
    } else if (st.kind === 'finish') {
      box.appendChild(el('div', 'step ok',
        `<div class="h"><span class="n">${i + 1}</span><span class="tool">finish</span>
         ${st.gate?.blocked ? '<span class="badge bad">게이트 차단</span>' : '<span class="badge ok">게이트 통과</span>'}
         <span class="ms">${st.ms}ms</span></div><div class="th">${esc(st.thought || '')}</div>` +
        (st.gate?.blocked ? `<p class="warn">${st.gate.why.map(esc).join('<br>')}</p>` : '')));
    } else {
      box.appendChild(el('div', 'step ' + (st.kind === 'commit' ? 'ok' : 'bad'),
        `<div class="h"><span class="n">${i + 1}</span><span class="tool">${esc(st.kind)}</span></div>
         <div class="th">${esc(st.detail || st.thought || (st.editedFields ? '사람이 수정한 필드: ' + st.editedFields.join(', ') : ''))}</div>`));
    }
  });
}

// ── 승인
// ★2026-09-10 — 필드를 «묶었다».
//   14개가 아무 구분 없이 세로로 쌓여 있으면 «무엇을 확인해야 하는지»가 안 보인다.
//   확인하는 «성격»이 다르다 — 이 작품이 맞나 / 사실이 맞나 / 쓸 수 있나 / 글이 맞나.
//   '@' 로 시작하는 행은 «구분 머리»다. data-k 가 없으므로 값 수집에 섞이지 않는다.
const FIELDS = [
  ['@', '이 작품이 맞나', '틀리면 아래가 전부 틀린다'],
  ['title', '한국어 제목', 1], ['origTitle', '원제', 1], ['artist', '작가', 1],
  ['@', '작품 정보', '공개 데이터에서 캔 것'],
  ['inception', '제작 시기', 1], ['material', '매체', 1], ['collection', '소장처', 1],
  ['era', '사조', 1], ['people', '등장인물', 1],
  ['@', '쓸 수 있나', '불명이면 게이트가 막는다'],
  ['license', '라이선스', 1],
  ['@', '해설 초안', '모델이 쓴 글 — 사실은 위에서 확인한 것만'],
  ['sections.meta', '해설 · 기본정보', 2], ['sections.description', '해설 · 작품', 2],
  ['sections.myth', '해설 · 신화 배경', 2], ['sections.insight', '해설 · 감상 포인트', 2],
];
const get = (o, p) => p.split('.').reduce((a, k) => a?.[k], o);

function renderApprove(run) {
  const box = $('#approve'); box.innerHTML = '';
  if (!run || run.status !== 'awaiting_approval') {
    box.innerHTML = `<div class="card"><p class="note">${run
      ? '승인 대기 상태가 아닙니다 (현재: ' + esc(run.status) + ')' + (run.stopReason ? ' — ' + esc(run.stopReason.detail) : '')
      : '아직 실행한 것이 없습니다.'}</p></div>`;
    return;
  }
  const d = run.finish.draft || {};
  const g = run.gate || {};
  if ((run.workflow || 'intake') === 'curate') { renderApproveCurate(run, d, g, box); return; }

  const head = el('div', 'card');
  head.innerHTML = `<h2>사람 승인 <span class="hint">되돌리기 어려운 작업 앞의 마지막 문</span></h2>
    ${g.blocked ? `<p class="warn"><b>등재할 수 없습니다.</b><br>${g.why.map(esc).join('<br>')}</p>`
      : '<p><span class="badge ok">안전 검사 통과</span> 라이선스 확인 · 중복 확인을 모두 마쳤습니다.</p>'}
    ${run.finish.duplicateOf ? `<p class="warn"><b>이미 등재된 작품일 수 있습니다</b> — <code>${esc(run.finish.duplicateOf)}</code></p>` : ''}
    <p class="note">동정 신뢰도 <b>${esc(run.finish.confidence || '-')}</b>
      ${run.finish.qid ? ` · <a href="https://www.wikidata.org/wiki/${esc(run.finish.qid)}" target="_blank" rel="noopener">${esc(run.finish.qid)}</a>` : ''}
      ${run.finish.notes ? '<br>모델 메모: ' + esc(run.finish.notes) : ''}</p>`;
  box.appendChild(head);

  const card = el('div', 'card');
  card.innerHTML = '<h2>필드 확인 <span class="hint">값을 고칠 수 있습니다. 고친 것은 트레이스에 남습니다</span></h2>';
  for (const [key, label, kind] of FIELDS) {
    if (key === '@') {                       // ★구분 머리 — 값이 아니다
      card.appendChild(el('div', 'fgroup',
        `${esc(label)}<span>${esc(kind || '')}</span>`));
      continue;
    }
    const v = get(d, key);
    const row = el('div', 'field');
    const val = Array.isArray(v) ? v.join(', ') : (v ?? '');
    row.innerHTML = `<div class="k">${esc(label)}</div><div class="v">` +
      (kind === 2 ? `<textarea data-k="${key}">${esc(val)}</textarea>`
                  : `<input data-k="${key}" value="${esc(val)}">`) +
      (val ? '' : '<div class="src">비어 있습니다 — 자료에서 확정하지 못했습니다</div>') + '</div>';
    card.appendChild(row);
  }
  if (d.sources?.length) {
    const s = el('div', 'field');
    s.innerHTML = `<div class="k">근거</div><div class="v">${d.sources.map((u) =>
      `<div class="src"><a href="${esc(u)}" target="_blank" rel="noopener">${esc(u)}</a></div>`).join('')}</div>`;
    card.appendChild(s);
  }
  if (d.imageUrl) {
    const s = el('div', 'field');
    s.innerHTML = `<div class="k">이미지</div><div class="v"><img src="${esc(d.imageUrl)}" alt="" style="max-width:100%;max-height:230px;border-radius:7px">
      <div class="src">${esc(d.imageUrl)}</div></div>`;
    card.appendChild(s);
  }
  const act = el('div', 'actions');
  const approve = el('button', 'primary', g.blocked ? '등재 (차단됨)' : '승인하고 등재');
  approve.disabled = !!g.blocked;
  approve.onclick = async () => {
    const edits = {};
    for (const inp of card.querySelectorAll('[data-k]')) {
      const k = inp.dataset.k;
      const orig = get(d, k);
      let v = inp.value;
      if (k === 'people') v = v.split(',').map((x) => x.trim()).filter(Boolean);
      const same = Array.isArray(orig) ? orig.join(', ') === inp.value : String(orig ?? '') === inp.value;
      if (same) continue;
      if (k.startsWith('sections.')) { edits.sections = { ...(edits.sections || d.sections || {}), [k.slice(9)]: v }; }
      else edits[k] = v;
    }
    const out = await approveAndCommit(current, edits, { archive });
    if (!out.ok) { alert('등재 실패: ' + out.reason + ' — ' + (out.detail || '')); return; }
    saveRun(current); renderTrace(current); renderResult(current); renderApprove(current); renderHistory();
    goTab('result');
  };
  const rej = el('button', 'ghost', '거부');
  rej.onclick = () => {
    const why = prompt('거부 사유를 적어 주세요 (트레이스에 남습니다)') || '';
    reject(current, why); saveRun(current); renderTrace(current); renderApprove(current); renderHistory();
  };
  act.append(approve, rej);
  if (g.blocked) act.appendChild(el('span', 'note', '안전 검사를 통과하지 못해 승인 버튼이 잠겨 있습니다.'));
  card.appendChild(act);
  box.appendChild(card);
}

// ── 승인 · 큐레이션판
//    등재는 «필드»를 확인하고, 큐레이션은 «작품 목록»을 확인한다. 확인해야 할 것이 다르니 화면도 다르다.
function renderApproveCurate(run, d, g, box) {
  const bySlug = Object.fromEntries(archive.map((x) => [x.slug, x]));
  const head = el('div', 'card');
  head.innerHTML = `<h2>전시 구성 승인 <span class="hint">아카이브에 «있는» 작품만 걸 수 있습니다</span></h2>
    ${g.blocked ? `<p class="warn"><b>확정할 수 없습니다.</b><br>${(g.why || []).map(esc).join('<br>')}</p>`
      : `<p><span class="badge ok">안전 검사 통과</span> ${g.stats?.works ?? 0}점 · ${g.stats?.sections ?? 0}구획 ·
         <b>지어낸 작품 0점</b></p>`}
    ${run.finish.notes ? `<p class="note">모델 메모: ${esc(run.finish.notes)}</p>` : ''}`;
  box.appendChild(head);

  const card = el('div', 'card');
  card.innerHTML = `<h2>구성 확인 <span class="hint">체크를 풀면 그 작품은 «빠집니다»</span></h2>
    <div class="field"><div class="k">전시 제목</div><div class="v"><input id="exTitle" value="${esc(d.title || '')}"></div></div>
    <div class="field"><div class="k">기획 의도</div><div class="v"><textarea id="exStmt">${esc(d.statement || '')}</textarea></div></div>`;
  (d.sections || []).forEach((sec, i) => {
    const wrap = el('div', 'field');
    const items = (sec.works || []).map((slug) => {
      const w = bySlug[slug];
      return `<label class="chk"><input type="checkbox" data-sec="${i}" data-slug="${esc(slug)}" checked>
        <span>${w ? `${esc(w.title)} <span class="hint">· ${esc(w.artist)} · ${esc(w.mythKo)} · ${esc(w.era)}</span>
        <a href="${esc(w.url)}" target="_blank" rel="noopener">보기</a>`
        : `<span class="badge bad">아카이브에 없음</span> <code>${esc(slug)}</code>`}</span></label>`;
    }).join('');
    wrap.innerHTML = `<div class="k">구획 ${i + 1}</div><div class="v">
      <input data-secname="${i}" value="${esc(sec.name || '')}">
      <textarea data-sectext="${i}" style="margin-top:6px">${esc(sec.wallText || '')}</textarea>
      <div style="margin-top:7px">${items || '<span class="note">작품 없음</span>'}</div></div>`;
    card.appendChild(wrap);
  });

  const act = el('div', 'actions');
  const approve = el('button', 'primary', g.blocked ? '확정 (차단됨)' : '승인하고 확정');
  approve.disabled = !!g.blocked;
  approve.onclick = async () => {
    const secs = (d.sections || []).map((sec, i) => ({
      name: card.querySelector(`[data-secname="${i}"]`)?.value ?? sec.name,
      wallText: card.querySelector(`[data-sectext="${i}"]`)?.value ?? sec.wallText,
      works: [...card.querySelectorAll(`input[data-sec="${i}"]:checked`)].map((x) => x.dataset.slug),
    })).filter((sec) => sec.works.length);
    const edits = { title: $('#exTitle').value, statement: $('#exStmt').value, sections: secs };
    const out = await approveAndCommit(current, edits, { archive }, { workflow: 'curate' });
    if (!out.ok) { alert('확정 실패: ' + out.reason + ' — ' + (out.detail || '')); return; }
    saveRun(current); renderTrace(current); renderResult(current); renderApprove(current); renderHistory();
    goTab('result');
  };
  const rej = el('button', 'ghost', '거부');
  rej.onclick = () => {
    const why = prompt('거부 사유를 적어 주세요 (트레이스에 남습니다)') || '';
    reject(current, why); saveRun(current); renderTrace(current); renderApprove(current); renderHistory();
  };
  act.append(approve, rej);
  if (g.blocked) act.appendChild(el('span', 'note', '안전 검사를 통과하지 못해 승인 버튼이 잠겨 있습니다.'));
  card.appendChild(act);
  box.appendChild(card);
}

// ── 결과
function renderResult(run) {
  const box = $('#result'); box.innerHTML = '';
  if (!run?.record) {
    box.innerHTML = '<div class="card"><p class="note">아직 등재된 결과물이 없습니다.</p></div>';
    return;
  }
  const r = run.record;
  const c = el('div', 'card');
  c.innerHTML = `<h2>등재 레코드 <span class="badge ok">사람이 승인함</span></h2>
    <p class="note">에이전트가 «끝냈다»고 말하는 것과 결과물이 실제로 만들어진 것은 다릅니다. 아래가 실물입니다.</p>
    <pre>${esc(JSON.stringify(r, null, 1))}</pre>`;
  const a = el('div', 'actions');
  const dl = el('button', 'primary', 'JSON 내려받기');
  dl.onclick = () => {
    const blob = new Blob([JSON.stringify(r, null, 1)], { type: 'application/json' });
    const u = URL.createObjectURL(blob);
    const a2 = document.createElement('a');
    a2.href = u; a2.download = `record-${(r.origTitle || 'work').replace(/\W+/g, '-').slice(0, 40)}.json`;
    document.body.appendChild(a2); a2.click(); a2.remove(); URL.revokeObjectURL(u);
  };
  a.appendChild(dl);
  c.appendChild(a);
  box.appendChild(c);

  if (Array.isArray(r.sections)) {
    // 큐레이션 결과 — 전시를 «걸린 그대로» 보여 준다
    const bySlug = Object.fromEntries(archive.map((x) => [x.slug, x]));
    const s = el('div', 'card');
    s.innerHTML = `<h2>${esc(r.title)} <span class="hint">${r.workCount}점 · ${r.sections.length}구획</span></h2>` +
      (r.statement ? `<p>${esc(r.statement)}</p>` : '') +
      r.sections.map((sec) => `<h3>${esc(sec.name)}</h3>` +
        (sec.wallText ? `<p class="note">${esc(sec.wallText)}</p>` : '') +
        '<div class="tw"><table><tbody>' + (sec.works || []).map((slug) => {
          const w = bySlug[slug];
          return `<tr><td>${w ? `<a href="${esc(w.url)}" target="_blank" rel="noopener">${esc(w.title)}</a>` : esc(slug)}</td>
            <td>${esc(w?.artist || '')}</td><td>${esc(w?.mythKo || '')}</td><td>${esc(w?.era || '')}</td></tr>`;
        }).join('') + '</tbody></table></div>').join('');
    box.appendChild(s);
  } else if (r.sections) {
    const s = el('div', 'card');
    s.innerHTML = '<h2>해설 4단</h2>' + Object.entries(r.sections)
      .map(([k, v]) => `<h3>${esc({ meta: '기본정보', description: '작품 해설', myth: '신화 배경', insight: '감상 포인트' }[k] || k)}</h3><p>${esc(v)}</p>`).join('');
    box.appendChild(s);
  }
}

// ── 지난 실행
function renderHistory() {
  const runs = loadRuns();
  const box = $('#history');
  $('#historyCard').hidden = runs.length === 0 && demoRuns.length === 0;
  const rows = [...demoRuns.map((r) => ({ ...r, _demo: true })), ...runs];
  if (!rows.length) { box.innerHTML = ''; return; }
  box.innerHTML = '<div class="tw"><table><thead><tr><th>작품</th><th>모드</th><th>상태</th><th class="num">스텝</th><th class="num">초</th><th></th></tr></thead><tbody></tbody></table></div>';
  const tb = box.querySelector('tbody');
  for (const r of rows.slice(0, 24)) {
    const s = summary(r);
    const tr = el('tr', r.gate?.blocked ? 'blocked' : '');
    tr.innerHTML = `<td>${esc(r.input.title)}</td><td>${r._demo ? '데모' : esc(r.backend)}</td>
      <td>${esc(r.status)}</td><td class="num">${s.steps}</td><td class="num">${(s.wallMs / 1000).toFixed(0)}</td><td></td>`;
    const b = el('button', 'small', r._demo ? '재생' : '열기');
    b.onclick = () => { if (r._demo) replay(r); else { current = r; renderTrace(r); renderApprove(r); renderResult(r); goTab('trace'); } };
    tr.lastElementChild.appendChild(b);
    tb.appendChild(tr);
  }
}

// ── 평가 탭
let evalLoaded = false;
async function loadEval() {
  if (evalLoaded) return;
  evalLoaded = true;
  const box = $('#evalView');
  try {
    const r = await fetch('results/summary.json');
    if (!r.ok) throw new Error('아직 없음');
    const d = await r.json();
    box.innerHTML = renderEvalHTML(d);
  } catch {
    box.innerHTML = `<div class="card"><h2>평가</h2>
      <p class="note">평가 요약(<code>results/summary.json</code>)이 아직 생성되지 않았습니다.
      저장소의 <a href="EVALUATION.md">EVALUATION.md</a> 를 보세요.</p></div>`;
  }
}
function renderEvalHTML(d) {
  const S = d.settings || [];
  const f = ['origTitle', 'artist', 'era', 'inception', 'material', 'collection', 'people'];
  return `<div class="card"><h2>세팅별 비교 <span class="hint">한 번에 하나씩만 바꿨습니다</span></h2>
    <div class="tw"><table><thead><tr><th>세팅</th><th class="num">n</th><th class="num">승인도달</th>
    <th class="num">게이트통과</th><th class="num">중복탐지</th><th class="num">환각</th>
    <th class="num">평균스텝</th><th class="num">평균초</th></tr></thead><tbody>` +
    S.map((s) => `<tr><td>${esc(s.setting.label)}</td><td class="num">${s.n}</td>
      <td class="num">${s.reachedApproval.pct}%</td><td class="num">${s.passedGate.pct}%</td>
      <td class="num">${s.duplicateFound.pct}%</td><td class="num">${s.hallucinated.pct}%</td>
      <td class="num">${s.perf.steps}</td><td class="num">${(s.perf.wallMs / 1000).toFixed(0)}</td></tr>`).join('') +
    `</tbody></table></div></div>
    <div class="card"><h2>필드 정확도 <span class="hint">아카이브 982점이 정답지입니다</span></h2>
    <div class="tw"><table><thead><tr><th>세팅</th>${f.map((x) => `<th class="num">${x}</th>`).join('')}</tr></thead><tbody>` +
    S.map((s) => `<tr><td>${esc(s.setting.name)}</td>${f.map((k) =>
      `<td class="num">${s.fieldAcc[k] ? s.fieldAcc[k].pct + '%' : '-'}</td>`).join('')}</tr>`).join('') +
    `</tbody></table></div></div>
    <div class="card"><h2>실패 분류</h2><div class="tw"><table><thead><tr><th>세팅</th><th>유형</th></tr></thead><tbody>` +
    S.map((s) => `<tr><td>${esc(s.setting.name)}</td><td>${Object.entries(s.failures).map(([k, v]) => `${esc(k)} ×${v}`).join(' · ') || '없음'}</td></tr>`).join('') +
    `</tbody></table></div><p class="note">자세한 분석은 <a href="EVALUATION.md">EVALUATION.md</a>.</p></div>`;
}

// ── 도구 문서
function renderToolDocs() {
  $('#toolDocs').innerHTML = TOOLS.map((t) =>
    `<h3>${esc(t.name)} ${t.writes ? '<span class="badge bad">쓰기 · 승인 필요</span>' : '<span class="badge ok">읽기</span>'}</h3>
     <p class="note">${esc(t.description)}</p>
     <details><summary>입력 스키마 / 출력</summary><pre>${esc(JSON.stringify(t.input, null, 1))}\n\n→ ${esc(t.output)}</pre></details>`).join('');
}

// ── 부팅
(async function boot() {
  renderModes(); renderModeCfg(); renderToolDocs();
  $('#btnRun').onclick = start;

  archive = await fetch('data/works-index.json').then((r) => r.json()).catch(() => []);
  renderWorkflows(); renderInputs();
  demoRuns = await fetch('results/demo-runs.json').then((r) => r.ok ? r.json() : []).catch(() => []);
  renderModeCfg(); renderHistory();
})();
