// 도구 6종 — 브라우저와 Node 양쪽에서 그대로 돈다 (빌드 단계 없음).
//
// 설계 원칙 네 가지
//   ① 스키마를 «먼저» 적고 구현이 그것을 따른다. 모델에 주는 설명도 여기 한 곳에만 있다.
//   ② 실패는 예외로 던지지 않고 {ok:false, reason} 으로 «돌려준다» — 루프가 관찰하고 판단해야 하니까.
//   ③ 쓰기 도구는 하나뿐이고, 런타임이 승인 상태를 검사한다. 모델의 선의에 기대지 않는다.
//   ④ 외부 호출은 전부 공개 API·키 불필요. 호출 간격을 둔다(남의 서버다).

const UA = 'KDT-MQ4-CURATOR/1.0 (https://github.com/kimjy0977/KDT_Works; kjuyoung77@gmail.com)';

// ★Wikidata Query Service 는 설명이 붙은 User-Agent 가 없으면 «403»을 준다 (실측 2026-09-09).
//   브라우저에서는 User-Agent 가 금지 헤더라 설정해도 무시되지만, 브라우저 자신의 UA 로 통과한다.
//   Node 에서는 직접 넣어야 한다 — 안 넣으면 폴백 도구가 통째로 죽는다.
const IS_NODE = typeof window === 'undefined';
function headers() {
  const h = { Accept: 'application/json', 'Api-User-Agent': UA };
  if (IS_NODE) h['User-Agent'] = UA;
  return h;
}

// ── 예의: 같은 호스트에 연달아 때리지 않는다.
const lastCall = new Map();
async function polite(host, ms = 250) {
  const prev = lastCall.get(host) || 0;
  const wait = prev + ms - Date.now();
  if (wait > 0) await new Promise((r) => setTimeout(r, wait));
  lastCall.set(host, Date.now());
}

// ── 재시도: 429/5xx 만 지수 백오프 2회. 404·빈결과는 «재시도해도 같다» — 즉시 돌려준다.
async function fetchJSON(url, { timeoutMs = 20000, retries = 2 } = {}) {
  const host = new URL(url).host;
  for (let attempt = 0; ; attempt++) {
    await polite(host);
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), timeoutMs);
    try {
      const res = await fetch(url, { signal: ctl.signal, headers: headers() });
      clearTimeout(timer);
      if (res.status === 429 || res.status >= 500) {
        if (attempt < retries) {
          await new Promise((r) => setTimeout(r, 600 * 2 ** attempt));
          continue;
        }
        return { ok: false, reason: `http_${res.status}`, detail: '재시도 소진' };
      }
      if (!res.ok) return { ok: false, reason: `http_${res.status}` };
      return { ok: true, data: await res.json() };
    } catch (e) {
      clearTimeout(timer);
      const reason = e.name === 'AbortError' ? 'timeout' : 'network';
      if (attempt < retries && reason === 'network') {
        await new Promise((r) => setTimeout(r, 600 * 2 ** attempt));
        continue;
      }
      return { ok: false, reason, detail: String(e.message || e) };
    }
  }
}

// ── Wikidata 클레임에서 값 하나 꺼내기 (구조가 깊어서 따로 뺀다)
function claimValues(claims, pid) {
  const arr = claims?.[pid];
  if (!Array.isArray(arr)) return [];
  return arr
    .map((c) => c.mainsnak?.datavalue?.value)
    .filter(Boolean)
    .map((v) => (typeof v === 'object' ? (v.id ?? v.time ?? v.text ?? v.amount ?? null) : v))
    .filter((v) => v !== null);
}

// ═══════════════════════════════════════════════════════════════
// 도구 정의
// ═══════════════════════════════════════════════════════════════

export const TOOLS = [
  {
    name: 'wd_search',
    // 설명은 «언제 쓰는가»를 먼저 말한다. 무엇을 하는지만 적으면 모델이 순서를 틀린다.
    description:
      '작품을 Wikidata에서 찾는 첫 수단. mode 두 가지가 «완전히 다르게» 동작하니 골라 써야 한다. ' +
      'mode="fulltext"(기본): 전문 검색이라 제목에 작가 이름을 «함께» 넣으면 정답이 위로 올라온다. ' +
      '동명이작이 많은 신화 주제에서 특히 유리하다. ' +
      'mode="label": 라벨 접두 일치라 «제목만» 정확히 넣어야 한다. 작가 이름을 덧붙이면 오히려 0건이 된다(실측). ' +
      '결과가 비면 제목을 바꿔(괄호 제거, 부제 절단, 괄호 안쪽만) 다시 부르는 것이 정상적인 사용법이다. ' +
      '실측상 원제를 그대로 label 로 넣으면 30%만 맞고, 변형을 함께 시도하면 60%까지 오른다. ' +
      '두세 번 변형해도 비면 wd_sparql 폴백으로 넘어간다.',
    input: {
      type: 'object',
      required: ['query'],
      properties: {
        query: { type: 'string', maxLength: 200, description: '검색할 제목. 영문 원제가 한국어보다 훨씬 잘 맞는다' },
        mode: { type: 'string', enum: ['fulltext', 'label'], default: 'fulltext' },
        artist: { type: 'string', description: 'fulltext 일 때만 쓰인다. 넣으면 동명이작을 갈라 준다' },
        lang: { type: 'string', enum: ['en', 'ko'], default: 'en' },
        limit: { type: 'integer', minimum: 1, maximum: 5, default: 5 },
      },
    },
    output: '{ ok, results: [{qid, label, description}], empty }',
    writes: false,
    async run({ query, mode = 'fulltext', artist, lang = 'en', limit = 5 }) {
      if (!query || !query.trim()) return { ok: false, reason: 'empty_query' };
      const n = Math.min(5, Math.max(1, limit));
      const q = query.trim();
      let u, pluck;
      if (mode === 'label') {
        // 라벨 접두 일치. 빠르지만 «제목만» 받는다.
        u = 'https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&origin=*' +
            `&search=${encodeURIComponent(q)}&language=${lang}&uselang=${lang}&limit=${n}`;
        pluck = (d) => (d.search || []).map((s) => ({
          qid: s.id, label: s.label || s.match?.text || '', description: s.description || '',
        }));
      } else {
        // 전문 검색(CirrusSearch). generator+entityterms 로 «한 번의 호출»에 라벨·설명까지 받는다.
        const term = artist ? `${q} ${artist}` : q;
        u = 'https://www.wikidata.org/w/api.php?action=query&format=json&origin=*' +
            `&generator=search&gsrsearch=${encodeURIComponent(term)}&gsrlimit=${n}` +
            '&prop=entityterms&wbetterms=label%7Cdescription&uselang=en';
        pluck = (d) => Object.values(d.query?.pages || {})
          .sort((a, b) => (a.index ?? 99) - (b.index ?? 99))
          .map((p) => ({
            qid: p.title,
            label: (p.entityterms?.label || [''])[0],
            description: (p.entityterms?.description || [''])[0],
          }))
          .filter((x) => /^Q[0-9]+$/.test(x.qid));
      }
      const r = await fetchJSON(u);
      if (!r.ok) return r;
      const results = pluck(r.data);
      // 빈 결과는 «실패»가 아니라 «관찰»이다. 루프가 다음 변형을 고르게 사실만 돌려준다.
      return { ok: true, mode, results, empty: results.length === 0 };
    },
  },

  {
    name: 'wd_entity',
    description:
      '동정이 끝난 뒤 그 작품의 사실을 캔다. Q번호를 주면 제작자·제작연도·재료·소장처·사조·묘사대상과 ' +
      'Commons 대표 이미지 파일명, 저작권 상태를 돌려준다. wd_search 로 Q번호를 얻기 전에는 부를 수 없다.',
    input: {
      type: 'object',
      required: ['qid'],
      properties: {
        qid: { type: 'string', pattern: '^Q[0-9]+$' },
        lang: { type: 'string', enum: ['ko', 'en'], default: 'ko' },
      },
    },
    output: '{ ok, entity: {qid,label,description,instanceOf,creator,inception,material,location,collection,movement,depicts,commonsFile,copyrightStatus} }',
    writes: false,
    async run({ qid, lang = 'ko' }) {
      if (!/^Q[0-9]+$/.test(qid || '')) return { ok: false, reason: 'bad_qid', detail: qid };
      const u =
        'https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&origin=*' +
        `&ids=${qid}&props=labels%7Cdescriptions%7Cclaims&languages=${lang}%7Cen`;
      const r = await fetchJSON(u);
      if (!r.ok) return r;
      const e = r.data.entities?.[qid];
      if (!e || e.missing !== undefined) return { ok: false, reason: 'not_found', detail: qid };
      const c = e.claims || {};
      const pick = (o) => o?.[lang]?.value || o?.en?.value || '';
      // 참조된 Q번호들의 «이름»을 한 번에 받아 온다 (Q번호만 있으면 모델이 읽을 수 없다)
      const refs = [
        ...claimValues(c, 'P170'), ...claimValues(c, 'P186'), ...claimValues(c, 'P276'),
        ...claimValues(c, 'P195'), ...claimValues(c, 'P135'), ...claimValues(c, 'P180'),
        ...claimValues(c, 'P31'), ...claimValues(c, 'P6216'),
      ].filter((v) => /^Q[0-9]+$/.test(v)).slice(0, 40);
      const names = {};
      if (refs.length) {
        const lu =
          'https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&origin=*' +
          `&ids=${[...new Set(refs)].join('%7C')}&props=labels&languages=${lang}%7Cen`;
        const lr = await fetchJSON(lu);
        if (lr.ok) {
          for (const [k, v] of Object.entries(lr.data.entities || {})) {
            names[k] = v.labels?.[lang]?.value || v.labels?.en?.value || k;
          }
        }
      }
      const nm = (arr) => arr.map((v) => names[v] || v);
      return {
        ok: true,
        entity: {
          qid,
          label: pick(e.labels),
          description: pick(e.descriptions),
          instanceOf: nm(claimValues(c, 'P31')),
          creator: nm(claimValues(c, 'P170')),
          inception: claimValues(c, 'P571').map((t) => String(t).replace(/^\+/, '').slice(0, 10)),
          material: nm(claimValues(c, 'P186')),
          location: nm(claimValues(c, 'P276')),
          collection: nm(claimValues(c, 'P195')),
          movement: nm(claimValues(c, 'P135')),
          depicts: nm(claimValues(c, 'P180')),
          commonsFile: claimValues(c, 'P18')[0] || null,
          copyrightStatus: nm(claimValues(c, 'P6216')),
        },
      };
    },
  },

  {
    name: 'wd_sparql',
    description:
      '제목 검색이 «모두» 실패했을 때만 쓰는 마지막 수단. 작가의 Q번호를 주면 그 작가의 작품 목록을 받아 ' +
      '제목을 눈으로 대조할 수 있다. 제목 검색을 시도하지 않고 먼저 부르지 말 것. ' +
      '작가 Q번호는 wd_search 에 작가 이름을 넣어 얻는다.',
    input: {
      type: 'object',
      required: ['artistQid'],
      properties: {
        artistQid: { type: 'string', pattern: '^Q[0-9]+$' },
        limit: { type: 'integer', minimum: 1, maximum: 30, default: 20 },
      },
    },
    output: '{ ok, works: [{qid, label, inception}] }',
    writes: false,
    // 자유 SPARQL 을 받지 않는다 — 템플릿만 채운다. 권한 최소화.
    async run({ artistQid, limit = 20 }) {
      if (!/^Q[0-9]+$/.test(artistQid || '')) return { ok: false, reason: 'bad_qid', detail: artistQid };
      const n = Math.min(30, Math.max(1, limit));
      const q = `SELECT ?w ?wLabel ?inception WHERE {
  ?w wdt:P170 wd:${artistQid} .
  OPTIONAL { ?w wdt:P571 ?inception }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "ko,en". }
} LIMIT ${n}`;
      const u = `https://query.wikidata.org/sparql?format=json&query=${encodeURIComponent(q)}`;
      const r = await fetchJSON(u, { timeoutMs: 20000, retries: 1 });
      if (!r.ok) return r;
      const works = (r.data.results?.bindings || []).map((b) => ({
        qid: (b.w?.value || '').split('/').pop(),
        label: b.wLabel?.value || '',
        inception: (b.inception?.value || '').slice(0, 10),
      }));
      return { ok: true, works, empty: works.length === 0 };
    },
  },

  {
    name: 'commons_file',
    description:
      '이미지의 라이선스를 확인한다. 등재 전에 «반드시» 한 번 부른다. ' +
      'wd_entity 가 돌려준 commonsFile 을 title 로 넣거나, 없으면 search 로 찾는다. ' +
      '결과가 없거나 라이선스를 읽지 못하면 판정은 «불명»이고, 그때는 등재를 진행하지 않는다.',
    input: {
      type: 'object',
      properties: {
        title: { type: 'string', description: 'Commons 파일명. "File:" 접두사는 있어도 없어도 된다' },
        search: { type: 'string', description: 'title 을 모를 때 쓰는 검색어' },
      },
    },
    output: '{ ok, file: {title,imageUrl,license,licenseUrl,author,verdict} }  verdict ∈ pd|cc|restricted|unknown',
    writes: false,
    async run({ title, search }) {
      let t = title;
      if (!t && search) {
        const su =
          'https://commons.wikimedia.org/w/api.php?action=query&format=json&origin=*' +
          `&list=search&srnamespace=6&srlimit=1&srsearch=${encodeURIComponent(search)}`;
        const sr = await fetchJSON(su);
        if (!sr.ok) return sr;
        t = sr.data.query?.search?.[0]?.title;
      }
      if (!t) return { ok: true, file: null, verdict: 'unknown', reason: 'no_file' };
      if (!/^File:/i.test(t)) t = 'File:' + t;
      const u =
        'https://commons.wikimedia.org/w/api.php?action=query&format=json&origin=*' +
        `&titles=${encodeURIComponent(t)}&prop=imageinfo&iiprop=url%7Cextmetadata`;
      const r = await fetchJSON(u);
      if (!r.ok) return r;
      const pages = r.data.query?.pages || {};
      const page = Object.values(pages)[0];
      if (!page || page.missing !== undefined) {
        return { ok: true, file: null, verdict: 'unknown', reason: 'missing' };
      }
      const info = page.imageinfo?.[0] || {};
      const em = info.extmetadata || {};
      const strip = (s) => String(s || '').replace(/<[^>]*>/g, '').trim();
      const license = strip(em.LicenseShortName?.value);
      const low = license.toLowerCase();
      // 판정은 «보수적으로». 확실할 때만 통과시킨다.
      let verdict = 'unknown';
      if (/public domain|^pd|cc0/.test(low)) verdict = 'pd';
      else if (/^cc[ -]by/.test(low)) verdict = 'cc';
      else if (license) verdict = 'restricted';
      return {
        ok: true,
        file: {
          title: page.title,
          imageUrl: info.url || null,
          license: license || null,
          licenseUrl: strip(em.LicenseUrl?.value) || null,
          author: strip(em.Artist?.value) || null,
          verdict,
        },
        verdict,
      };
    },
  },

  {
    name: 'archive_search',
    description:
      '내 아카이브(982점) 안을 찾는다. 두 가지 목적으로 쓴다 — ①이 작품이 «이미 등재돼 있는지» 확인 ' +
      '②등장인물·사조가 같은 기존 작품을 찾아 연결 후보로 삼기. 등재 직전에 ①을 반드시 한 번 한다. ' +
      '⚠ q 에는 «사람이 읽는 말»을 넣는다 — 작품 제목(원제 또는 한국어)이나 등장인물 이름. ' +
      'Q번호(예: Q3545179)나 URL 을 넣으면 아카이브에는 그런 문자열이 없으므로 «반드시 0건»이 나온다.',
    input: {
      type: 'object',
      required: ['q'],
      properties: {
        q: { type: 'string', maxLength: 120 },
        topK: { type: 'integer', minimum: 1, maximum: 8, default: 5 },
      },
    },
    output: '{ ok, hits: [{slug,title,origTitle,artist,era,people,url,score}] }',
    writes: false,
    async run({ q, topK = 5 }, ctx) {
      const index = ctx?.archive;
      if (!Array.isArray(index)) return { ok: false, reason: 'index_not_loaded' };
      const norm = (s) => String(s || '').toLowerCase().replace(/[^a-z0-9가-힣]+/g, ' ').trim();
      const terms = norm(q).split(' ').filter((t) => t.length > 1);
      if (!terms.length) return { ok: true, hits: [] };
      const scored = [];
      for (const it of index) {
        const hay = norm([it.title, it.origTitle, it.artist, it.era, (it.people || []).join(' ')].join(' '));
        let s = 0;
        for (const t of terms) if (hay.includes(t)) s += t.length;
        // 제목이 통째로 들어맞으면 크게 가산 — 중복 등재 판정이 이 신호에 달려 있다
        if (norm(it.origTitle).includes(norm(q)) || norm(it.title).includes(norm(q))) s += 40;
        if (s > 0) scored.push({ ...it, score: s });
      }
      scored.sort((a, b) => b.score - a.score);
      return {
        ok: true,
        hits: scored.slice(0, Math.min(8, topK)).map((h) => ({
          slug: h.slug, title: h.title, origTitle: h.origTitle, artist: h.artist,
          era: h.era, people: h.people, url: h.url, score: h.score,
        })),
      };
    },
  },

  {
    name: 'emit_record',
    description:
      '등재 레코드를 확정한다. 이것이 이 워크플로의 «결과물»이다. ' +
      '★사람이 승인하기 전에는 호출해도 거부된다. 모든 사실을 모으고 라이선스를 확인한 뒤 마지막에 한 번만 부른다.',
    input: {
      type: 'object',
      required: ['title', 'origTitle', 'artist'],
      properties: {
        title: { type: 'string', description: '한국어 제목' },
        origTitle: { type: 'string' },
        artist: { type: 'string' },
        inception: { type: 'string' },
        material: { type: 'string' },
        collection: { type: 'string' },
        era: { type: 'string' },
        people: { type: 'array', items: { type: 'string' } },
        license: { type: 'string' },
        imageUrl: { type: 'string' },
        sources: { type: 'array', items: { type: 'string' }, description: '각 사실의 근거 URL' },
        sections: {
          type: 'object',
          description: '한국어 해설 4단 초안',
          properties: {
            meta: { type: 'string' }, description: { type: 'string' },
            myth: { type: 'string' }, insight: { type: 'string' },
          },
        },
      },
    },
    output: '{ ok, record }',
    writes: true,   // ★런타임이 이 표시를 보고 승인 게이트를 건다
    async run(args, ctx) {
      // 게이트는 «여기»가 아니라 실행기에 있다. 여기서도 한 번 더 막는다 — 방어를 두 겹으로.
      if (!ctx?.approved) {
        return { ok: false, reason: 'not_approved', detail: '사람 승인 전에는 등재할 수 없습니다' };
      }
      for (const k of ['title', 'origTitle', 'artist']) {
        if (!args?.[k]) return { ok: false, reason: 'schema', detail: `필수 필드 누락: ${k}` };
      }
      return { ok: true, record: { ...args, emittedAt: new Date().toISOString() } };
    },
  },
];

export const TOOL_MAP = Object.fromEntries(TOOLS.map((t) => [t.name, t]));

/** 모델에 넘길 도구 목록 (실행 함수는 빼고 스키마·설명만). */
export function toolSpecs() {
  return TOOLS.map(({ name, description, input }) => ({ name, description, input_schema: input }));
}

/** 도구 하나를 실행하고 «항상» {ok,...}와 소요시간을 돌려준다. 예외를 밖으로 던지지 않는다. */
export async function callTool(name, args, ctx) {
  const t0 = Date.now();
  const tool = TOOL_MAP[name];
  if (!tool) return { ok: false, reason: 'unknown_tool', detail: name, ms: 0 };
  if (tool.writes && !ctx?.approved) {
    return { ok: false, reason: 'not_approved', detail: `${name} 은 승인 뒤에만 호출됩니다`, ms: Date.now() - t0 };
  }
  try {
    const out = await tool.run(args || {}, ctx || {});
    return { ...out, ms: Date.now() - t0 };
  } catch (e) {
    return { ok: false, reason: 'tool_threw', detail: String(e?.message || e), ms: Date.now() - t0 };
  }
}
