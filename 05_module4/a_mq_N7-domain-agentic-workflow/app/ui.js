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
  syncUrl(b.dataset.tab);
});
const goTab = (name) => document.querySelector(`.tabs button[data-tab="${name}"]`).click();

/* ★딥링크 — 탭·실행이 «주소»를 가진다.
   전에는 어느 탭을 보고 있든 URL 이 하나였다. 링크로 「트레이스 화면」을
   보낼 수 없었고, 새로고침하면 늘 첫 탭으로 돌아갔다.
   (UX 지침 deep-linking · state-preservation · back-behavior)
     ?tab=trace   탭 지정
     ?run=3       저장된 데모 실행 3번을 «불러온 채로» 연다 */
const TABS = ['run', 'trace', 'approve', 'result', 'eval', 'about'];
function syncUrl(tab) {
  const u = new URL(location.href);
  if (tab === 'run') u.searchParams.delete('tab');
  else u.searchParams.set('tab', tab);
  history.replaceState(null, '', u);
}

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
  // ★실행 헤더 — 칩이 아니라 «타일». 무엇을 봐야 하는지가 먼저 눈에 들어와야 한다.
  const STATUS_KO = { done: '등재됨', awaiting_approval: '승인 대기', stopped: '중단',
    failed: '실패', running: '실행 중' };
  const tiles = [
    ['상태', STATUS_KO[run.status] || run.status, run.status === 'done' ? 'ok'
      : run.status === 'failed' ? 'bad' : run.status === 'awaiting_approval' ? 'warn' : ''],
    ['스텝', s.steps, ''],
    ['도구 호출', s.toolCalls, ''],
    ['소요', (s.wallMs / 1000).toFixed(1) + '초', ''],
    ['토큰 in / out', s.usage.in + ' / ' + s.usage.out, ''],
    ['비용', s.costUsd ? '$' + s.costUsd.toFixed(4) : '$0 (로컬)', ''],
  ];
  $('#runMeta').innerHTML =
    `<div class="runhead">
      <div class="rh-t"><b>${esc(run.input.title)}</b>${run.input.artist
        ? `<span class="hint"> / ${esc(run.input.artist)}</span>` : ''}
        <span class="hint"> · ${esc(run.backend)} · ${esc(run.model)}</span></div>
      <div class="stats">${tiles.map(([k, v, cls]) =>
        `<div class="stat ${cls}"><span class="sk">${k}</span><span class="sv">${esc(String(v))}</span></div>`
      ).join('')}</div>
    </div>`;

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

  // ★워터폴 — 「무엇이 총합에서 큰가」(위 막대)와 «다른 것»을 본다: 「**언제** 무슨 일이 있었나」.
  //   에이전트 트레이스 뷰어의 정석(LangSmith·Jaeger·DevTools Network)을 따랐다.
  //   모델이 오래 생각하고 도구가 짧게 도는 패턴이 «반복»되는지, 한 군데서만 튀는지가 보인다.
  const t0 = run.startedAt || (run.steps[0] && run.steps[0].at) || 0;
  const last = run.steps[run.steps.length - 1] || {};
  const span = Math.max(1, ((last.at || t0) + (last.modelMs || 0) + (last.toolMs || 0)) - t0);
  const wf = $('#waterfall');
  if (wf) {
    wf.innerHTML = run.steps.map((st, i) => {
      const off = Math.max(0, (st.at || t0) - t0);
      const m = st.modelMs || 0, tl = st.toolMs || 0;
      const name = st.kind === 'act' ? (st.action && st.action.tool) || 'act'
        : st.kind === 'parse_fail' ? '형식 오류' : st.kind;
      const bad = st.kind === 'parse_fail' || (st.observation && st.observation.ok === false);
      return `<div class="wf-row">
        <span class="wf-n">${i + 1}</span>
        <span class="wf-name${bad ? ' bad' : ''}">${esc(name)}</span>
        <span class="wf-track">
          <span class="wf-bar model" style="left:${(off / span) * 100}%;width:${Math.max(0.6, (m / span) * 100)}%"
            title="모델 ${(m / 1000).toFixed(1)}s"></span>
          <span class="wf-bar tool${bad ? ' bad' : ''}" style="left:${((off + m) / span) * 100}%;width:${Math.max(0.6, (tl / span) * 100)}%"
            title="도구 ${tl}ms"></span>
        </span>
        <span class="wf-ms">${((m + tl) / 1000).toFixed(1)}s</span>
      </div>`;
    }).join('') +
      `<div class="wf-legend"><span><i class="model"></i>모델이 생각한 시간</span>
       <span><i class="tool"></i>도구가 돈 시간</span>
       <span class="hint">가로축 = 실행 시작부터 ${(span / 1000).toFixed(1)}초</span></div>`;
  }

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
  card.appendChild(el('p', 'note',
    '★승인하면 <b>등재 레코드 JSON 이 확정</b>됩니다. ' +
    '<b>공개 아카이브에 자동으로 써 넣지 않습니다</b> — ④ 결과 탭에서 내려받아 넣는 것은 사람이 합니다.'));
  const act = el('div', 'actions');
  const approve = el('button', 'primary', g.blocked ? '등재 (차단됨)' : '승인하고 레코드 확정');
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
  if (!run || !run.record) {
    box.innerHTML = '<div class="card"><p class="note">아직 확정된 결과물이 없습니다.</p></div>';
    return;
  }
  const r = run.record;
  const isExhibition = Array.isArray(r.sections);

  // ★사람이 읽는 것을 «먼저». JSON 은 접어서 아래로.
  //   PRD 의 2차 유저(소규모 아카이브·전시 기획자)는 개발자가 아닐 수 있다.
  //   화면 맨 위의 중괄호 덩어리는 그 사람에게 「이게 뭐지」로 끝난다.
  const FIELD_LABELS = [
    ['title', '한국어 제목'], ['origTitle', '원제'], ['artist', '작가'],
    ['inception', '제작 시기'], ['material', '매체'], ['collection', '소장처'],
    ['era', '사조'], ['people', '등장인물'], ['license', '라이선스'],
  ];
  const SEC_LABELS = { meta: '기본정보', description: '작품 해설', myth: '신화 배경', insight: '감상 포인트' };

  if (!isExhibition) {
    // ── ① 등재할 내용 — 표로
    const head = el('div', 'card');
    head.innerHTML = `<h2>등재할 내용 <span class="badge ok">사람이 승인함</span></h2>
      <p class="warn">★<b>여기까지가 이 서비스의 몫입니다.</b>
        이 내용은 <b>공개 아카이브에 «자동으로 들어가지 않습니다».</b>
        아래에서 내려받아 아카이브에 넣는 것은 <b>사람</b>이 합니다.<br>
        <span class="note">지금 이 레코드는 <b>브라우저에만</b>(localStorage · 최근 20건) 있습니다.
        서버도 데이터베이스도 없습니다.</span></p>
      <div class="tw"><table><tbody>` +
      FIELD_LABELS.map(([k, lab]) => {
        const v = Array.isArray(r[k]) ? r[k].join(', ') : (r[k] || '');
        return `<tr><th style="width:120px">${lab}</th><td>${v ? esc(v)
          : '<span class="note">비어 있습니다 — 자료에서 확정하지 못했습니다</span>'}</td></tr>`;
      }).join('') + `</tbody></table></div>`;
    box.appendChild(head);

    // ── ② 해설 4단 — 사람이 읽는 본문
    if (r.sections && !Array.isArray(r.sections)) {
      const s2 = el('div', 'card');
      s2.innerHTML = '<h2>해설 초안 <span class="hint">그대로 쓰지 말고 «확인한 사실»로 다듬어 쓰세요</span></h2>' +
        Object.entries(r.sections).map(([k, v]) =>
          `<h3>${esc(SEC_LABELS[k] || k)}</h3><p>${esc(v)}</p>`).join('');
      box.appendChild(s2);
    }

    // ── ③ 근거 · 이미지
    if ((r.sources && r.sources.length) || r.imageUrl) {
      const s3 = el('div', 'card');
      s3.innerHTML = '<h2>근거 <span class="hint">각 사실이 어디서 왔는가</span></h2>' +
        ((r.sources && r.sources.length)
          ? '<ul class="links">' + r.sources.map((u) =>
              `<li><a href="${esc(u)}" target="_blank" rel="noopener">${esc(u)}</a></li>`).join('') + '</ul>'
          : '<p class="note">근거 링크가 없습니다.</p>') +
        (r.imageUrl ? `<h3>이미지</h3>
          <img src="${esc(r.imageUrl)}" alt="" style="max-width:100%;max-height:280px;border-radius:8px">
          <p class="note" style="word-break:break-all">${esc(r.imageUrl)}</p>` : '');
      box.appendChild(s3);
    }
  }

  // ── ④ 내려받기 — «누구에게 쓸모 있는지»를 적는다
  const dl = el('div', 'card');
  dl.innerHTML = `<h2>가져가기 <span class="hint">쓰는 곳에 맞는 형식을 고르세요</span></h2>
    <div class="tw"><table><tbody>
      <tr><th style="width:120px">Markdown</th><td><b>사람이 읽고 붙여 넣는 용</b> —
        노션·워드·블로그에 그대로 붙습니다. <b>JSON 을 몰라도 됩니다.</b></td></tr>
      <tr><th>JSON</th><td>아카이브·스프레드시트에 <b>기계로 넣을 때</b>. 필드 이름이 그대로 살아 있습니다.</td></tr>
      <tr><th>복사</th><td>파일을 만들지 않고 <b>클립보드로</b> 바로.</td></tr>
    </tbody></table></div>`;
  const acts = el('div', 'actions');

  const toMarkdown = () => {
    if (isExhibition) {
      const bySlug = Object.fromEntries(archive.map((x) => [x.slug, x]));
      return `# ${r.title || '전시'}\n\n${r.statement || ''}\n\n` +
        (r.sections || []).map((sec) => `## ${sec.name}\n\n${sec.wallText || ''}\n\n` +
          (sec.works || []).map((slug) => {
            const w = bySlug[slug];
            return `- ${w ? `${w.title} — ${w.artist || ''} (${w.era || ''})` : slug}`;
          }).join('\n')).join('\n\n') + '\n';
    }
    let m = `# ${r.title || ''}${r.origTitle ? ` (${r.origTitle})` : ''}\n\n`;
    m += FIELD_LABELS.filter(([k]) => k !== 'title' && k !== 'origTitle')
      .map(([k, lab]) => `- **${lab}**: ${Array.isArray(r[k]) ? r[k].join(', ') : (r[k] || '—')}`).join('\n');
    if (r.sections && !Array.isArray(r.sections)) {
      m += '\n\n' + Object.entries(r.sections)
        .map(([k, v]) => `## ${SEC_LABELS[k] || k}\n\n${v}`).join('\n\n');
    }
    if (r.sources && r.sources.length) {
      m += '\n\n## 근거\n\n' + r.sources.map((u) => `- ${u}`).join('\n');
    }
    if (r.imageUrl) m += `\n\n## 이미지\n\n${r.imageUrl}`;
    m += `\n\n---\n\n*확정 ${r.emittedAt || ''} · CURATOR 가 만든 초안입니다. 사실은 위 근거로 확인하세요.*\n`;
    return m;
  };

  const save = (text, ext, mime) => {
    const name = `record-${String(r.origTitle || r.title || 'work').replace(/\W+/g, '-').slice(0, 40)}.${ext}`;
    const blob = new Blob([text], { type: mime });
    const u = URL.createObjectURL(blob);
    const a2 = document.createElement('a');
    a2.href = u; a2.download = name;
    document.body.appendChild(a2); a2.click(); a2.remove(); URL.revokeObjectURL(u);
  };

  const bMd = el('button', 'primary', 'Markdown 내려받기');
  bMd.onclick = () => save(toMarkdown(), 'md', 'text/markdown;charset=utf-8');
  const bJson = el('button', 'ghost', 'JSON 내려받기');
  bJson.onclick = () => save(JSON.stringify(r, null, 1), 'json', 'application/json');
  const bCopy = el('button', 'ghost', '클립보드에 복사');
  bCopy.onclick = async () => {
    try {
      await navigator.clipboard.writeText(toMarkdown());
      bCopy.textContent = '복사됨 ✓';
      setTimeout(() => { bCopy.textContent = '클립보드에 복사'; }, 1800);
    } catch (e) {
      // ★실패를 «성공한 척» 하지 않는다. 브라우저가 막을 수 있다.
      bCopy.textContent = '복사 실패 — 내려받기를 쓰세요';
      setTimeout(() => { bCopy.textContent = '클립보드에 복사'; }, 2600);
    }
  };
  acts.append(bMd, bJson, bCopy);
  dl.appendChild(acts);
  box.appendChild(dl);

  // ── ⑤ 전시 결과 (큐레이션) — 걸린 그대로
  if (isExhibition) {
    const bySlug = Object.fromEntries(archive.map((x) => [x.slug, x]));
    const s = el('div', 'card');
    s.innerHTML = `<h2>${esc(r.title)} <span class="hint">${r.workCount}점 · ${r.sections.length}구획</span></h2>` +
      (r.statement ? `<p>${esc(r.statement)}</p>` : '') +
      r.sections.map((sec) => `<h3>${esc(sec.name)}</h3>` +
        (sec.wallText ? `<p class="note">${esc(sec.wallText)}</p>` : '') +
        '<div class="tw"><table><tbody>' + (sec.works || []).map((slug) => {
          const w = bySlug[slug];
          return `<tr><td>${w ? `<a href="${esc(w.url)}" target="_blank" rel="noopener">${esc(w.title)}</a>` : esc(slug)}</td>
            <td>${esc((w && w.artist) || '')}</td><td>${esc((w && w.mythKo) || '')}</td><td>${esc((w && w.era) || '')}</td></tr>`;
        }).join('') + '</tbody></table></div>').join('');
    box.appendChild(s);
  }

  // ── ⑥ 원본 JSON — «접어서» 아래로. 필요한 사람만 편다.
  const raw = el('details', 'card');
  raw.innerHTML = `<summary><b>원본 JSON</b> <span class="hint">기계가 읽는 형태 — 개발자·채점자용</span></summary>
    <pre>${esc(JSON.stringify(r, null, 1))}</pre>`;
  box.appendChild(raw);
}

function renderHistory() {
  // ★사이드바에 «상주»하는 목록이다. 표가 아니라 리스트.
  //   전에는 ①실행 탭 «맨 아래»에 표로 있었다 — 다른 실행으로 옮기려면
  //   탭을 되돌아가 스크롤해야 했다. 목록↔상세가 한 화면에 있어야 도구다.
  const runs = loadRuns();
  const box = $('#history');
  const rows = [...demoRuns.map((r) => ({ ...r, _demo: true })), ...runs];
  $('#historyCard').hidden = rows.length === 0;
  if (!rows.length) { box.innerHTML = ''; return; }

  // ★클래스 이름이 «충돌»했다. 실측 2026-09-10 —
  //   <span class="dot warn"> 가 «경고 상자»용 `.warn`(padding:14px 18px)을 먹어
  //   7px 점이 «큰 갈색 타원»이 됐다. 제네릭 이름은 반드시 부딪힌다.
  //   ⇒ 상태 점은 s- 접두를 붙인다.
  const DOT = { done: 's-ok', awaiting_approval: 's-warn', failed: 's-bad', stopped: '' };
  const KO = { done: '등재됨', awaiting_approval: '승인 대기', failed: '실패',
    stopped: '중단', running: '실행 중' };

  box.innerHTML = '<div class="runlist"></div>';
  const list = box.querySelector('.runlist');
  for (const r of rows.slice(0, 24)) {
    const s2 = summary(r);
    const b = el('button', 'runitem' + (current && current.runId === r.runId ? ' on' : ''));
    b.innerHTML =
      `<span class="t">${esc(r.input.title)}</span>` +
      `<span class="dot ${r.gate && r.gate.blocked ? 's-bad' : (DOT[r.status] || '')}"></span>` +
      `<span class="m"><span>${KO[r.status] || esc(r.status)}</span>` +
      `<span>${r._demo ? '데모' : esc(r.backend)}</span>` +
      `<span>${s2.steps}스텝 · ${(s2.wallMs / 1000).toFixed(0)}초</span></span>`;
    b.title = `${r.input.title} — ${KO[r.status] || r.status}`;
    b.onclick = () => {
      if (r._demo) { replay(r); return; }
      current = r; renderTrace(r); renderApprove(r); renderResult(r); renderHistory(); goTab('trace');
    };
    list.appendChild(b);
  }
}

// ★평가는 «한 번만» 부른다 — 탭을 오갈 때마다 다시 가져오지 않는다.
//   실사고 2026-09-10: renderHistory 를 다시 쓰면서 loadEval 과 «이 줄»이
//   같이 지워졌다. loadEval 만 되살렸더니 이번엔 evalLoaded 가 없어서
//   평가 탭이 「불러오는 중…」에서 멈춰 있었다. 화면 캡처가 그걸 잡았다.
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
  const pct = (o) => (o && o.pct != null) ? o.pct + '%' : '-';
  const acc = (s, k) => (s.fieldAcc && s.fieldAcc[k]) ? s.fieldAcc[k].pct : null;

  // ★「좋아 보이는데 아무것도 못 맞힌」 세팅을 «화면이» 짚어 준다.
  //   사람이 표를 훑고 스스로 알아채길 기대하면 안 된다 — 나부터 못 알아챘다.
  const trap = S.filter((s) => acc(s, 'artist') === 0 && s.reachedApproval.pct >= 70);

  let h = '';

  if (trap.length) {
    h += `<div class="card" style="border-color:var(--warn)">
      <h2>★이 표를 읽는 법 <span class="hint">단일 지표로 고르면 «정확히 반대로» 고릅니다</span></h2>
      ${trap.map((s) => `<p class="warn"><b>${esc(s.setting.label)}</b> 는
        승인도달 <b>${s.reachedApproval.pct}%</b> · 환각 <b>${s.hallucinated.pct}%</b> ·
        <b>${(s.perf.wallMs / 1000).toFixed(0)}초</b> 로 <b>셋 다 1등</b>처럼 보입니다.
        그런데 <b>필드 정확도 ${acc(s, 'artist')}% · 게이트 통과 ${s.passedGate.pct}%</b> 입니다 —
        <b>아무것도 못 맞히면서 통과만 잘 받았습니다.</b>
        ${s.n}건 중 <b>${s.n - s.passedGate.n}건</b>을 게이트가 막았습니다.</p>`).join('')}
      <p class="note">⇒ 뒤집어 보면 <b>게이트가 «일한다»는 증거</b>이기도 합니다.
        모델이 무엇을 내든 근거 없는 것은 등재로 넘어가지 않습니다.</p></div>`;
  }

  // ── 세팅별 — ★필드 정확도를 «같은 표에» 둔다. 다른 표로 미루면 함정이 안 보인다
  h += `<div class="card"><h2>세팅별 비교 <span class="hint">한 번에 하나씩만 바꿨습니다</span></h2>
    <div class="tw"><table><thead><tr><th>세팅</th><th class="num">n</th><th class="num">승인도달</th>
    <th class="num">게이트통과</th><th class="num">중복탐지</th><th class="num">환각</th>
    <th class="num">★작가 정확</th><th class="num">평균스텝</th><th class="num">평균초</th></tr></thead><tbody>` +
    S.map((s) => {
      const a = acc(s, 'artist');
      const bad = a === 0;
      return `<tr${bad ? ' class="blocked"' : ''}><td>${esc(s.setting.label)}
        ${bad ? '<span class="badge warn">못 맞힘</span>' : ''}</td>
        <td class="num">${s.n}</td>
        <td class="num">${s.reachedApproval.pct}%</td><td class="num">${s.passedGate.pct}%</td>
        <td class="num">${s.duplicateFound.pct}%</td><td class="num">${s.hallucinated.pct}%</td>
        <td class="num"><b>${a == null ? '-' : a + '%'}</b></td>
        <td class="num">${s.perf.steps}</td><td class="num">${(s.perf.wallMs / 1000).toFixed(0)}</td></tr>`;
    }).join('') + `</tbody></table></div>
    <p class="note">「승인도달」은 <b>사람 앞까지 갔다</b>는 뜻이지 <b>맞았다</b>는 뜻이 아닙니다.
      맞았는지는 <b>작가 정확</b> 열이 말합니다.</p></div>`;

  // ── ★자료의 천장별 — 있는데 화면에 없었다
  const withSplit = S.filter((s) => s.split);
  if (withSplit.length) {
    h += `<div class="card"><h2>★자료의 천장별
      <span class="hint">섞어 놓고 한 숫자로 말하면 «양쪽 다» 오해가 됩니다</span></h2>
      <p class="note">공개 데이터가 <b>충분한 것(strong)</b> · <b>부족한 것(weak)</b> ·
        <b>아예 없는 것(none)</b> 으로 나눠 쟀습니다.
        «에이전트의 한계»와 «자료의 한계»를 가르려면 이렇게 재야 합니다.</p>
      <div class="tw"><table><thead><tr><th>세팅</th><th>구간</th><th class="num">n</th>
      <th class="num">승인도달</th><th class="num">작가 정확</th><th class="num">중복탐지</th></tr></thead><tbody>` +
      withSplit.map((s) => ['strong', 'weak', 'none'].map((k) => {
        const v = s.split[k]; if (!v) return '';
        return `<tr><td>${esc(s.setting.name)}</td><td><b>${k}</b></td><td class="num">${v.n}</td>
          <td class="num">${v.reachedApprovalPct}%</td><td class="num">${v.artistPct}%</td>
          <td class="num">${v.dupPct}%</td></tr>`;
      }).join('')).join('') + `</tbody></table></div></div>`;
  }

  // ── ★신화별 — 이것도 있는데 화면에 없었다
  const withMyth = S.filter((s) => s.byMyth && Object.keys(s.byMyth).length);
  if (withMyth.length) {
    const base = withMyth[0];
    const keys = Object.keys(base.byMyth);
    h += `<div class="card"><h2>신화별 <span class="hint">
      ${esc(base.setting.label)} 기준 — 어느 문화권이 «자료가 얇은가»</span></h2>
      <div class="tw"><table><thead><tr><th>신화</th><th class="num">n</th>
      <th class="num">승인도달</th><th class="num">작가 정확</th></tr></thead><tbody>` +
      keys.map((k) => {
        const v = base.byMyth[k];
        return `<tr><td>${esc(k)}</td><td class="num">${v.n}</td>
          <td class="num">${v.approval}/${v.n}</td>
          <td class="num">${v.artist}/${v.artistN}</td></tr>`;
      }).join('') + `</tbody></table></div>
      <p class="note">그리스로마 밖(북유럽·이집트·메소포타미아·힌두·중국)은
        <b>Wikidata·Commons 자체가 얇습니다.</b> 낮은 숫자가 곧 «에이전트가 못했다»는 뜻은 아닙니다.</p></div>`;
  }

  // ── 필드 정확도 전체
  h += `<div class="card"><h2>필드 정확도 <span class="hint">아카이브 982점이 정답지입니다</span></h2>
    <div class="tw"><table><thead><tr><th>세팅</th>${f.map((x) => `<th class="num">${x}</th>`).join('')}</tr></thead><tbody>` +
    S.map((s) => `<tr><td>${esc(s.setting.name)}</td>${f.map((k) =>
      `<td class="num">${s.fieldAcc[k] ? s.fieldAcc[k].pct + '%' : '-'}</td>`).join('')}</tr>`).join('') +
    `</tbody></table></div>
    <p class="note">★<b>채점기가 틀려 있었습니다.</b> 소장처 정답지가 괄호에서 잘리고, 매체 어순·BCE 부호·
      「미상」 처리가 어긋나 있었습니다. 고친 뒤 material 이 8%→28% 로 올랐습니다 —
      <b>고치기 전 숫자로 결론을 냈다면 틀린 결론이 났습니다.</b></p></div>`;

  // ── 실패 분류
  h += `<div class="card"><h2>실패 분류 <span class="hint">무엇 때문에 못 갔는가</span></h2>
    <div class="tw"><table><thead><tr><th>세팅</th><th>유형</th></tr></thead><tbody>` +
    S.map((s) => `<tr><td>${esc(s.setting.name)}</td><td>${Object.entries(s.failures).map(([k, v]) =>
      `${esc(k)} ×${v}`).join(' · ') || '없음'}</td></tr>`).join('') +
    `</tbody></table></div>
    <p class="note">자세한 분석 — <a href="EVALUATION.md">EVALUATION.md</a> ·
      원본 트레이스 <a href="results/">results/</a> (채점 규칙을 고쳐도 <b>재실행 없이 다시 집계</b>됩니다)</p></div>`;

  return h;
}

function renderToolDocs() {
  // ★개수를 «센다». 손으로 적으면 반드시 어긋난다 —
  //   실제로 화면에 「도구 6종」이라 적혀 있었는데 8종이었다(2026-09-10 발견).
  const writes = TOOLS.filter((t) => t.writes).length;
  const head = $('#toolHead');
  if (head) head.innerHTML = `도구 ${TOOLS.length}종
    <span class="hint">읽기 ${TOOLS.length - writes} · <b>쓰기 ${writes}</b> — 쓰기는 승인 뒤에만 부를 수 있습니다</span>`;
  $('#toolDocs').innerHTML = '<div class="toolgrid">' + TOOLS.map((t) =>
    `<div class="tool-card${t.writes ? ' w' : ''}">
      <div class="tc-h"><code>${esc(t.name)}</code>
        ${t.writes ? '<span class="badge bad">쓰기 · 승인 필요</span>'
                   : '<span class="badge ok">읽기</span>'}</div>
      <p class="note">${esc(t.description)}</p>
      <details><summary>입력 스키마 / 출력</summary><pre>${esc(JSON.stringify(t.input, null, 1))}

→ ${esc(t.output)}</pre></details>
    </div>`).join('') + '</div>';
}

// ── 부팅
(async function boot() {
  renderModes(); renderModeCfg(); renderToolDocs();
  $('#btnRun').onclick = start;

  archive = await fetch('data/works-index.json').then((r) => r.json()).catch(() => []);
  renderWorkflows(); renderInputs();
  demoRuns = await fetch('results/demo-runs.json').then((r) => r.ok ? r.json() : []).catch(() => []);
  renderModeCfg(); renderHistory();

  // ★주소가 가리키는 곳으로 — 링크·새로고침·캡처가 «같은 화면»을 연다
  const q = new URLSearchParams(location.search);
  const n = parseInt(q.get('run') || '', 10);
  if (n >= 1 && demoRuns[n - 1]) await replay(demoRuns[n - 1]);
  const t = q.get('tab');
  if (t && TABS.includes(t)) goTab(t);
})();
