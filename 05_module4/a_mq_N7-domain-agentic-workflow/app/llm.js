// 모델 백엔드 — 네 갈래. 어느 쪽이든 같은 모양으로 돌려준다.
//
// ★왜 네이티브 tool-calling API 를 안 쓰나
//   ① 백엔드마다 스키마가 달라 «세팅을 바꿔 가며 비교»하는 이 과제의 평가가 불가능해진다.
//   ② 로컬 소형 모델은 tool-calling 지원이 들쭉날쭉하다. 무료로 돌 수 있는 길을 막고 싶지 않다.
//   ③ 트레이스에 «모델이 실제로 뱉은 문자열»이 그대로 남아 실패 원인을 볼 수 있다.
//   대신 JSON 한 덩어리를 뱉게 하고 우리가 판다. 대가는 파싱 실패를 우리가 처리해야 한다는 것.

export const BACKENDS = {
  demo: { label: '데모 재생 (키 불필요)', needsKey: false, needsLocal: false },
  ollama: { label: '로컬 Ollama (키 불필요)', needsKey: false, needsLocal: true },
  anthropic: { label: 'Anthropic API (내 키)', needsKey: true, needsLocal: false },
  openai: { label: 'OpenAI API (내 키)', needsKey: true, needsLocal: false },
};

// 백만 토큰당 USD. 값이 바뀌므로 «확인 날짜»를 함께 적는다 (2026-09-09 확인).
export const PRICES = {
  'claude-sonnet-5': { in: 3, out: 15 },
  'claude-haiku-4-5': { in: 1, out: 5 },
  'gpt-4o-mini': { in: 0.15, out: 0.6 },
  _default: { in: 0, out: 0 },
};

export function estimateCost(model, usage) {
  const p = PRICES[model] || PRICES._default;
  return ((usage.in || 0) * p.in + (usage.out || 0) * p.out) / 1e6;
}

/** 모델 응답에서 JSON 한 덩어리를 판다. 앞뒤 잡담과 코드펜스를 견딘다. */
export function extractJSON(text) {
  if (!text) return null;
  let t = String(text).trim();
  const fence = t.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fence) t = fence[1].trim();
  try { return JSON.parse(t); } catch { /* 아래로 */ }
  // 균형 잡힌 첫 { … } 를 찾는다. 문자열 안의 중괄호를 세지 않도록 인용부호를 추적한다.
  const s = t.indexOf('{');
  if (s < 0) return null;
  let depth = 0, inStr = false, esc = false;
  for (let i = s; i < t.length; i++) {
    const c = t[i];
    if (esc) { esc = false; continue; }
    if (c === '\\') { esc = true; continue; }
    if (c === '"') { inStr = !inStr; continue; }
    if (inStr) continue;
    if (c === '{') depth++;
    else if (c === '}' && --depth === 0) {
      try { return JSON.parse(t.slice(s, i + 1)); } catch { return null; }
    }
  }
  return null;
}

async function postJSON(url, body, { headers = {}, timeoutMs = 120000 } = {}) {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      method: 'POST',
      signal: ctl.signal,
      headers: { 'Content-Type': 'application/json', ...headers },
      body: JSON.stringify(body),
    });
    clearTimeout(timer);
    const text = await res.text();
    if (!res.ok) return { ok: false, reason: `http_${res.status}`, detail: text.slice(0, 400) };
    try { return { ok: true, data: JSON.parse(text) }; }
    catch { return { ok: false, reason: 'bad_json', detail: text.slice(0, 400) }; }
  } catch (e) {
    clearTimeout(timer);
    return { ok: false, reason: e.name === 'AbortError' ? 'timeout' : 'network', detail: String(e.message || e) };
  }
}

/**
 * 한 번 물어본다.
 * @returns {ok, text, usage:{in,out}, ms, raw} | {ok:false, reason, detail, ms}
 */
export async function complete(cfg, { system, messages }) {
  const t0 = Date.now();
  const done = (r) => ({ ...r, ms: Date.now() - t0 });

  if (cfg.backend === 'demo') {
    return done({ ok: false, reason: 'demo_backend', detail: '데모 모드는 저장된 트레이스를 재생합니다' });
  }

  if (cfg.backend === 'ollama') {
    const host = (cfg.host || 'http://localhost:11434').replace(/\/$/, '');
    const r = await postJSON(`${host}/api/chat`, {
      model: cfg.model,
      stream: false,
      format: 'json',            // 소형 모델이 형식을 흘리지 않게 강제한다
      // ★think 를 끄지 않으면 추론을 늘어놓느라 «한 스텝이 2분을 넘겨» 타임아웃한다 (실측 2026-09-09:
      //   켜면 120초 초과, 끄면 1.2초). 우리는 «생각»을 thought 필드로 이미 받고 있으므로 중복이다.
      think: false,
      options: { temperature: 0, num_ctx: cfg.numCtx || 8192 },
      messages: [{ role: 'system', content: system }, ...messages],
    }, { timeoutMs: cfg.timeoutMs || 180000 });   // 첫 호출엔 모델 로드 시간(~10초)이 얹힌다
    if (!r.ok) {
      // 여기서 흔한 실패는 «CORS» 다. 원인을 사람이 읽을 수 있게 바꿔 준다.
      if (r.reason === 'network') {
        return done({ ok: false, reason: 'ollama_unreachable',
          detail: 'Ollama 에 닿지 못했습니다. 실행 중인지, OLLAMA_ORIGINS 에 이 주소가 허용됐는지 확인하세요.' });
      }
      return done(r);
    }
    return done({
      ok: true,
      text: r.data.message?.content || '',
      usage: { in: r.data.prompt_eval_count || 0, out: r.data.eval_count || 0 },
      raw: { evalDurationMs: Math.round((r.data.eval_duration || 0) / 1e6) },
    });
  }

  if (cfg.backend === 'anthropic') {
    const r = await postJSON('https://api.anthropic.com/v1/messages', {
      model: cfg.model,
      max_tokens: cfg.maxTokens || 2000,
      temperature: 0,
      system,
      messages,
    }, {
      headers: {
        'x-api-key': cfg.apiKey,
        'anthropic-version': '2023-06-01',
        // 브라우저에서 직접 부르려면 이 헤더가 필요하다. 키는 브라우저 밖으로 나가지 않는다.
        'anthropic-dangerous-direct-browser-access': 'true',
      },
    });
    if (!r.ok) return done(r);
    return done({
      ok: true,
      text: (r.data.content || []).filter((c) => c.type === 'text').map((c) => c.text).join(''),
      usage: { in: r.data.usage?.input_tokens || 0, out: r.data.usage?.output_tokens || 0 },
    });
  }

  if (cfg.backend === 'openai') {
    const r = await postJSON('https://api.openai.com/v1/chat/completions', {
      model: cfg.model,
      temperature: 0,
      response_format: { type: 'json_object' },
      messages: [{ role: 'system', content: system }, ...messages],
    }, { headers: { Authorization: `Bearer ${cfg.apiKey}` } });
    if (!r.ok) return done(r);
    return done({
      ok: true,
      text: r.data.choices?.[0]?.message?.content || '',
      usage: { in: r.data.usage?.prompt_tokens || 0, out: r.data.usage?.completion_tokens || 0 },
    });
  }

  return done({ ok: false, reason: 'unknown_backend', detail: cfg.backend });
}
