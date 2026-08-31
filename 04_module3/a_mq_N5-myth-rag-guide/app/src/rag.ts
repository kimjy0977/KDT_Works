// MYTH GALLERY 안내 챗봇 — RAG 유틸리티
// 임베딩: embeddinggemma-300m (model_no_gather_q4 변형 — 브라우저 WASM ORT 호환)
//   - transformers.js pipeline()은 q4/q8 기본 파일을 골라 GatherBlockQuantized
//     미지원으로 실패하므로, 토크나이저만 transformers.js로 쓰고
//     ORT 세션은 no_gather_q4 파일로 직접 만든다 (2026-08 헤드리스 검증).
// 검색: 신화별 샤드(myth-docs-{신화}.json)와 코사인 유사도 top-k. 목록은 myth-docs-index.json

import { AutoTokenizer, type PreTrainedTokenizer } from "@huggingface/transformers";

const MODEL_ID = "onnx-community/embeddinggemma-300m-ONNX";
const HF_ONNX = `https://huggingface.co/${MODEL_ID}/resolve/main/onnx`;
// transformers.js 4.2.0이 쓰는 것과 같은 onnxruntime-web 빌드 (검증된 조합)
const ORT_URL =
  "https://cdn.jsdelivr.net/npm/onnxruntime-web@1.26.0-dev.20260416-b7804b056c/dist/ort.webgpu.bundle.min.mjs";

interface OrtSession {
  run(feeds: Record<string, unknown>): Promise<Record<string, { dims: number[]; data: Float32Array }>>;
}

export interface DocChunk {
  id: string;
  text: string;
  url: string;
  section: string;
  vector: number[];
}

let session: OrtSession | null = null;
let tokenizer: PreTrainedTokenizer | null = null;
let ready: Promise<void> | null = null;

/** 임베딩 모델 내려받기 진행률 (첫 방문 1회, 이후 브라우저 캐시 — cached: 캐시 히트) */
export type EmbedProgress = { pct: number; file: string; cached?: boolean };
let progressCb: ((p: EmbedProgress) => void) | null = null;
export function onEmbedProgress(cb: (p: EmbedProgress) => void) {
  progressCb = cb;
}

/** 모델 캐시 보유 여부만 확인한다(다운로드 없음) — 첫 화면에서 "캐시된 모델" 표시용 */
export async function peekModelCache(): Promise<boolean> {
  try {
    const c = await caches.open(MODEL_CACHE);
    return (await c.match(`${HF_ONNX}/model_no_gather_q4.onnx_data`)) !== undefined;
  } catch {
    return false;
  }
}

// 모델 파일 캐시 — HF resolve URL은 요청마다 서명이 다른 CDN 주소로 리다이렉트되어
// HTTP 캐시가 히트하지 않는다. Cache Storage에 직접 보관해 재방문 시 재다운로드를 막는다.
const MODEL_CACHE = "myth-embed-v1";

async function fetchWithProgress(url: string, file: string): Promise<Uint8Array> {
  let cache: Cache | null = null;
  try {
    cache = await caches.open(MODEL_CACHE);
    const hit = await cache.match(url);
    if (hit) {
      progressCb?.({ pct: 100, file, cached: true });
      return new Uint8Array(await hit.arrayBuffer());
    }
  } catch {
    cache = null; // 캐시 API를 쓸 수 없는 환경 — 그냥 내려받는다
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error(`모델 파일 내려받기 실패 (${res.status}): ${file}`);
  const total = Number(res.headers.get("content-length") ?? 0);
  if (!res.body || !total) return new Uint8Array(await res.arrayBuffer());
  const reader = res.body.getReader();
  const chunks: Uint8Array[] = [];
  let got = 0;
  let lastPct = -1;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    got += value.length;
    const pct = Math.round((got / total) * 100);
    if (pct !== lastPct) {
      lastPct = pct;
      progressCb?.({ pct, file });
    }
  }
  const out = new Uint8Array(got);
  let offset = 0;
  for (const c of chunks) {
    out.set(c, offset);
    offset += c.length;
  }
  if (cache) await putWithRetry(cache, url, out);
  return out;
}

/** 캐시 저장 — Chrome이 간헐히 Unexpected internal error를 내는 경우가 있어 1회 재시도한다 */
async function putWithRetry(cache: Cache, url: string, body: Uint8Array<ArrayBuffer>): Promise<void> {
  for (let i = 0; i < 2; i++) {
    try {
      await cache.put(url, new Response(body));
      return;
    } catch (e) {
      console.warn(`임베딩 모델 캐시 저장 실패 (${i + 1}/2) — ${url}:`, e);
      await new Promise((r) => setTimeout(r, 400));
    }
  }
}

/** 토크나이저 + ORT 세션 준비 (첫 호출 시 모델 다운로드, 이후 Cache Storage 재사용) */
function ensureReady(): Promise<void> {
  if (session && tokenizer) return Promise.resolve();
  if (!ready) {
    ready = (async () => {
      // 디스크 여유가 부족할 때 브라우저가 이 사이트의 저장소를 임의로 비우지 않게 한다
      navigator.storage?.persist?.().catch(() => undefined);
      const ort = (await import(/* @vite-ignore */ ORT_URL)) as {
        InferenceSession: { create(
          buf: Uint8Array,
          opts: { executionProviders: string[]; externalData: { path: string; data: Uint8Array }[] },
        ): Promise<OrtSession> };
      };
      const core = await fetchWithProgress(`${HF_ONNX}/model_no_gather_q4.onnx`, "model_no_gather_q4.onnx");
      const data = await fetchWithProgress(`${HF_ONNX}/model_no_gather_q4.onnx_data`, "model_no_gather_q4.onnx_data");
      session = await ort.InferenceSession.create(core, {
        executionProviders: ["wasm"],
        externalData: [{ path: "model_no_gather_q4.onnx_data", data }],
      });
      tokenizer = await AutoTokenizer.from_pretrained(MODEL_ID);
    })().catch((e) => {
      ready = null; // 실패 시 다음 질문에서 재시도 가능
      throw e;
    });
  }
  return ready;
}

/** 문장 → 768차원 벡터 (mean pooling + L2 정규화 — 벡터스토어 생성 방식과 동일) */
export async function embed(text: string): Promise<number[]> {
  await ensureReady();
  const { input_ids, attention_mask } = await tokenizer!(text);
  const out = await session!.run({ input_ids, attention_mask });
  const hs = out.last_hidden_state;
  const [, seq, hid] = hs.dims;
  const am = attention_mask.data as ArrayLike<bigint> | ArrayLike<number>;
  const acc = new Float64Array(hid);
  let cnt = 0;
  for (let s = 0; s < seq; s++) {
    const w = Number(am[s]);
    cnt += w;
    if (!w) continue;
    for (let h = 0; h < hid; h++) acc[h] += hs.data[s * hid + h];
  }
  let norm = 0;
  for (let h = 0; h < hid; h++) {
    acc[h] /= cnt;
    norm += acc[h] * acc[h];
  }
  norm = Math.sqrt(norm);
  const vec = new Array<number>(hid);
  for (let h = 0; h < hid; h++) vec[h] = acc[h] / norm;
  return vec;
}

/* ── 신화별 벡터스토어 ────────────────────────────────────────────────
 * 아카이브 982점을 전부 담으면 한 파일이 20MB를 넘는다. 그리스·로마만 물으러 온
 * 방문자가 여섯 신화를 다 받아야 할 이유가 없다. 그래서 신화를 파일 경계로 삼고
 * (myth-docs-greek.json …), 기본은 그리스·로마만 받은 뒤 나머지는 **누를 때** 받는다.
 *
 * 스키마는 그대로다 — id·text·url·section·vector. 파일이 나뉠 뿐이라
 * 검색·프롬프트 파이프라인은 건드리지 않는다.                                   */

export const DEFAULT_MYTH = "greek";

export interface ShardInfo { myth: string; chunks: number; works: number; bytes: number }

let index: ShardInfo[] | null = null;
const loaded = new Map<string, DocChunk[]>();
const inflight = new Map<string, Promise<DocChunk[]>>();

/** 어떤 신화가 있고 얼마나 큰지 — 화면이 «몇 MB 더 받습니다»를 보여 줄 수 있게 */
export async function loadIndex(): Promise<ShardInfo[]> {
  if (index) return index;
  const res = await fetch(`${import.meta.env.BASE_URL}myth-docs-index.json`);
  if (!res.ok) throw new Error(`목록 로드 실패: ${res.status}`);
  index = ((await res.json()) as { shards: ShardInfo[] }).shards;
  return index;
}

/* starter — «화면에 보이는 작품»만 담은 작은 샤드.
 * greek 샤드가 9.79MB 라 페이지를 여는 순간 그걸 받으면 첫 방문이 10MB 다.
 * 그래서 starter 를 먼저 받아 바로 답할 수 있게 하고, 전체 샤드는 뒤에서 받는다.
 * 검색은 loadCorpus() 가 돌려주는 배열 위에서만 일어나므로 파이프라인은 그대로다. */
let starter: DocChunk[] | null = null;
let starterInflight: Promise<DocChunk[]> | null = null;

export async function loadStarter(): Promise<DocChunk[]> {
  if (starter) return starter;
  if (starterInflight) return starterInflight;
  starterInflight = (async () => {
    const res = await fetch(`${import.meta.env.BASE_URL}myth-docs-starter.json`);
    if (!res.ok) throw new Error(`맛보기 자료 로드 실패: ${res.status}`);
    starter = (await res.json()) as DocChunk[];
    starterInflight = null;
    return starter;
  })().catch((e) => { starterInflight = null; throw e; });
  return starterInflight;
}

/** 신화 하나를 받아 말뭉치에 더한다. 이미 있으면 그대로. */
export async function loadMyth(myth: string): Promise<DocChunk[]> {
  const have = loaded.get(myth);
  if (have) return have;
  const running = inflight.get(myth);
  if (running) return running;                 // 두 번 눌러도 한 번만 받는다
  const p = (async () => {
    const res = await fetch(`${import.meta.env.BASE_URL}myth-docs-${myth}.json`);
    if (!res.ok) throw new Error(`${myth} 자료 로드 실패: ${res.status}`);
    const docs = (await res.json()) as DocChunk[];
    loaded.set(myth, docs);
    inflight.delete(myth);
    return docs;
  })().catch((e) => { inflight.delete(myth); throw e; });
  inflight.set(myth, p);
  return p;
}

export function loadedMyths(): string[] {
  return [...loaded.keys()];
}

/** 지금까지 받은 신화를 합쳐 돌려준다 — 검색은 이 위에서만 일어난다 */
export async function loadCorpus(): Promise<DocChunk[]> {
  /* 아무것도 없으면 starter 라도 받는다. starter 마저 없으면 기본 신화를 받는다. */
  if (!loaded.size && !starter) {
    try { await loadStarter(); } catch { await loadMyth(DEFAULT_MYTH); }
  }
  const seen = new Set<string>();
  const all: DocChunk[] = [];
  /* 전체 샤드를 먼저 넣는다 — starter 는 그 부분집합이라 중복이 걸러진다 */
  for (const list of loaded.values())
    for (const d of list) if (!seen.has(d.id)) { seen.add(d.id); all.push(d); }
  if (starter)
    for (const d of starter) if (!seen.has(d.id)) { seen.add(d.id); all.push(d); }
  return all;
}

export interface Retrieved {
  chunk: DocChunk;
  score: number;
  method: "vector" | "bm25";
}

// 단어 검색용 불용어 — 조사·접속사·군더더기 표현 (2글자 이상만 걸러낸다)
const STOPWORDS = new Set([
  "에서", "에게", "한테", "부터", "까지", "처럼", "같이", "마다", "보다", "라는",
  "무엇", "언제", "어디", "누구", "어떤", "어떻게", "왜요", "인가요", "나요",
  "있는", "없는", "하는", "했던", "하는지", "인지", "니까", "이며", "하고",
  "주세요", "알려줘", "알려주세요", "가르쳐", "가르쳐줘", "말해줘", "해줘",
  "해주세요", "해주실", "그리고", "그래서", "하지만", "그런데", "근데", "the", "is", "what", "when", "where", "how", "about", "please", "tell",
]);

/** 질문에서 검색어 뽑기 — 소문자 통일, 1글자·불용어 제거 */
function queryTerms(q: string): string[] {
  return q
    .toLowerCase()
    .split(/[^가-힣a-z0-9]+/)
    .filter((t) => t.length >= 2 && !STOPWORDS.has(t));
}

// ── BM25 단어 검색 ────────────────────────────────────────────────────────
//  tf(빈도)·IDF(희귀도)·문서 길이 정규화를 갖춘 표준 단어 검색 점수(k1=1.5, b=0.75).
//  tf는 토큰 '포함' 관계로 세서 조사가 붙은 형태("페르세포네를")도 "페르세포네" 검색어에
//  적중시킨다. 말뭉치가 37조각이라 질문마다 그 자리에서 계산한다(별도 색인 없음).
const BM25_K1 = 1.5;
const BM25_B = 0.75;

/** BM25 원점수 — 문서별 점수(정규화 전). 점수 0 = 적중 없음 */
function bm25(docs: DocChunk[], terms: string[]): { chunk: DocChunk; score: number }[] {
  if (!terms.length) return [];
  const toks = docs.map((d) => queryTerms(d.text)); // 문서 토큰화도 질문과 같은 규칙
  const avgdl = toks.reduce((s, t) => s + t.length, 0) / docs.length;
  const df = new Map<string, number>(); // 검색어 → 그 검색어를 포함하는 문서 수
  for (const t of new Set(terms)) {
    df.set(t, toks.reduce((n, dt) => n + (dt.some((x) => x.includes(t)) ? 1 : 0), 0));
  }
  return docs.map((chunk, i) => {
    const dl = toks[i].length || 1;
    let score = 0;
    for (const [t, dfv] of df) {
      if (!dfv) continue;
      let tf = 0;
      for (const x of toks[i]) if (x.includes(t)) tf++;
      if (!tf) continue;
      const idf = Math.log((docs.length - dfv + 0.5) / (dfv + 0.5) + 1);
      score += (idf * tf * (BM25_K1 + 1)) / (tf + BM25_K1 * (1 - BM25_B + (BM25_B * dl) / avgdl));
    }
    return { chunk, score };
  });
}

/** 하이브리드 검색 — 벡터 유사도 상위 10개 + BM25 상위 5개(벡터 결과와 중복 제외).
 *  BM25가 5개를 못 채우면 벡터 순위 11위부터 보충해 항상 k개를 돌려준다.
 *  BM25 점수는 표시를 위해 이번 질문의 최상위가 1이 되게 정규화한다. */
export async function retrieve(question: string, k = 15): Promise<Retrieved[]> {
  const [docs, q] = await Promise.all([loadCorpus(), embed(question)]);
  const vec = docs
    .map((chunk) => {
      let dot = 0;
      const v = chunk.vector;
      for (let i = 0; i < v.length; i++) dot += v[i] * q[i];
      return { chunk, score: dot, method: "vector" as const };
    })
    .sort((a, b) => b.score - a.score);
  const topVec = vec.slice(0, Math.min(10, k));
  const picked = new Set(topVec.map((r) => r.chunk.id));
  const scored = bm25(docs, queryTerms(question))
    .filter((r) => r.score > 0 && !picked.has(r.chunk.id))
    .sort((a, b) => b.score - a.score)
    .slice(0, Math.max(0, k - topVec.length));
  const top = scored[0]?.score ?? 0;
  const lex = scored.map((r) => ({
    chunk: r.chunk,
    score: top > 0 ? r.score / top : 0,
    method: "bm25" as const,
  }));
  for (const r of lex) picked.add(r.chunk.id);
  const rest = vec.filter((r) => !picked.has(r.chunk.id)).slice(0, k - topVec.length - lex.length);
  return [...topVec, ...lex, ...rest];
}

/** RAG 시스템 지시 — 근거 원칙을 고정 */
export function buildPrompt(question: string, hits: Retrieved[]): string {
  const now = new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul",
    year: "numeric", month: "long", day: "numeric", weekday: "long",
    hour: "2-digit", minute: "2-digit", hour12: true,
  }).format(new Date());
  const context = hits
    .map((h) => `[${h.chunk.id} | ${h.chunk.section}] ${h.chunk.text}`)
    .join("\n\n");
  const best = hits[0]?.score ?? 0;
  const weakNote = best < 0.55
    ? "주의: 검색된 조각의 유사도가 낮습니다. 질문과 완전히 맞는 근거가 아닐 수 있으니, 근거에 있는 내용만 짧게 답하고 자료에 없는 부분은 없다고 말합니다."
    : "자료에 근거한 내용만 답하고, 자료에 없으면 없다고 말합니다.";
  return [
    "다음 자료는 신화 명화 아카이브 'MYTH GALLERY'의 공개 작품 페이지에서 뽑은 조각입니다.",
    weakNote,
    "근거가 된 조각의 [ID]를 답 안에서 표시합니다.",
    `현재 시각은 ${now}(한국 표준시 KST)입니다. '지금', '올해', '다음 주' 같은 상대 표현은 이 시각을 기준으로 해석합니다.`,
    "",
    "[자료]",
    context,
    "",
    "[질문]",
    question,
  ].join("\n");
}
