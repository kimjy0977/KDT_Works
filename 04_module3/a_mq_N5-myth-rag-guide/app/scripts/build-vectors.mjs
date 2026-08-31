/* 청크 → 768차원 벡터스토어 (모듈3 노드5 메인 퀘스트 · 4강)
 *
 * chunks.json 의 각 청크를 embeddinggemma-300m 으로 임베딩해
 * app/public/myth-docs-{신화}.json 샤드와 myth-docs-index.json 을 만든다.
 * 스키마는 참조 구현과 동일하게 유지한다:
 *   { id, text, url, section, vector[768] }
 *
 * ★ 왜 이 모델·이 방식이어야 하나
 *   질의 임베딩은 브라우저(app/src/rag.ts)가 만든다. 자료 벡터를 다른 모델이나
 *   다른 풀링으로 만들면 두 벡터가 같은 공간에 있지 않게 되어, 코사인 점수는
 *   비교할 자리를 잃는다. 그래서 여기서도 rag.ts 와 똑같이 한다:
 *     같은 모델 파일(model_no_gather_q4) · mean pooling · L2 정규화
 *
 * 실행:  cd app && npm run build:vectors
 *   --verify 를 붙이면 브라우저 embed() 와의 일치를 확인할 문장 벡터도 함께 낸다.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { AutoTokenizer, AutoModel } from "@huggingface/transformers";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, "..", "..");                 // 과제 폴더
const IN = path.join(ROOT, "data", "chunks.json");        // 수집기가 만든 정본
const OUT = path.join(HERE, "..", "public", "myth-docs.json");

const MODEL_ID = "onnx-community/embeddinggemma-300m-ONNX";
const MODEL_FILE = "model_no_gather";      // transformers.js 가 뒤에 _q4 를 붙여 model_no_gather_q4.onnx 가 된다
const DTYPE = "q4";                        // rag.ts 가 브라우저에서 쓰는 바로 그 파일
const DIM = 768;

/** rag.ts 의 embed() 와 같은 계산 — mean pooling 뒤 L2 정규화 */
function meanPoolL2(hidden, mask, seq, hid) {
  const acc = new Float64Array(hid);
  let cnt = 0;
  for (let s = 0; s < seq; s++) {
    const w = Number(mask[s]);
    cnt += w;
    if (!w) continue;
    for (let h = 0; h < hid; h++) acc[h] += Number(hidden[s * hid + h]);
  }
  let norm = 0;
  for (let h = 0; h < hid; h++) {
    acc[h] /= cnt;
    norm += acc[h] * acc[h];
  }
  norm = Math.sqrt(norm);
  const vec = new Array(hid);
  for (let h = 0; h < hid; h++) vec[h] = acc[h] / norm;
  return vec;
}

async function main() {
  const chunks = JSON.parse(fs.readFileSync(IN, "utf8"));
  console.log(`청크 ${chunks.length}개 읽음`);

  console.log(`모델 준비 — ${MODEL_ID} (${MODEL_FILE})`);
  const tokenizer = await AutoTokenizer.from_pretrained(MODEL_ID);
  const model = await AutoModel.from_pretrained(MODEL_ID, {
    dtype: DTYPE,
    model_file_name: MODEL_FILE,
    use_external_data_format: true,   // 가중치가 .onnx_data 로 분리돼 있다
  });

  async function embed(text) {
    const enc = await tokenizer(text);
    const out = await model({ input_ids: enc.input_ids, attention_mask: enc.attention_mask });
    const hs = out.last_hidden_state;
    const [, seq, hid] = hs.dims;
    if (hid !== DIM) throw new Error(`차원이 ${hid} 다 — ${DIM} 이어야 한다`);
    return meanPoolL2(hs.data, enc.attention_mask.data, seq, hid);
  }

  const docs = [];
  for (let i = 0; i < chunks.length; i++) {
    const c = chunks[i];
    if (!c.url) { console.log(`  건너뜀(url 없음): ${c.id}`); continue; }
    const vector = await embed(c.text);
    docs.push({
      id: c.id,
      text: c.text,
      url: c.url,
      section: c.section,
      vector: vector.map((v) => Math.round(v * 1e6) / 1e6),   // 참조 구현과 같은 6자리
    });
    if ((i + 1) % 10 === 0 || i === chunks.length - 1) {
      console.log(`  ${i + 1}/${chunks.length}`);
    }
  }

  fs.mkdirSync(path.dirname(OUT), { recursive: true });

  /* 신화별로 쪼개 저장한다 — myth-docs-greek.json 처럼.
   *
   * 왜. 아카이브 982점을 전부 담으면 한 파일이 20MB를 넘는다. 방문자는 그리스·로마만
   * 물으려 왔어도 여섯 신화를 다 받아야 한다. 그래서 신화를 파일 경계로 삼고,
   * 앱은 기본으로 그리스·로마만 받은 뒤 나머지는 **누를 때** 받는다.
   *
   * 스키마는 그대로다(id·text·url·section·vector). 파일이 나뉠 뿐이라
   * 검색·프롬프트 파이프라인은 건드리지 않는다. */
  const byMyth = new Map();
  for (const d of docs) {
    const code = d.id.split("-")[0];          // greek-xxxx#meta → greek
    if (!byMyth.has(code)) byMyth.set(code, []);
    byMyth.get(code).push(d);
  }

  const manifest = [];
  for (const [code, list] of [...byMyth].sort((a, b) => b[1].length - a[1].length)) {
    const p = path.join(path.dirname(OUT), `myth-docs-${code}.json`);
    fs.writeFileSync(p, JSON.stringify(list), "utf8");
    const bytes = fs.statSync(p).size;
    manifest.push({ myth: code, chunks: list.length,
                    works: new Set(list.map((d) => d.url)).size, bytes });
    console.log(`  ${code.padEnd(8)} ${String(list.length).padStart(5)}청크  ${(bytes / 1e6).toFixed(2)}MB`);
  }
  /* ── starter 샤드 ────────────────────────────────────────────────────
   * 왜. 신화별로 쪼갰는데도 그리스·로마 혼자 아카이브의 절반(469점)이라
   * 샤드 하나가 9.79MB다. 그런데 그걸 **페이지를 여는 순간** 받는다(App.tsx).
   * 첫 방문자가 질문을 하기도 전에 10MB를 기다린다.
   *
   * 그래서 «화면에 실제로 보이는 작품»만 담은 작은 샤드를 따로 만든다.
   * 정본은 app/src/works.ts — 화면이 싣는 목록 그대로다. 화면에 보이는 것은
   * 무조건 답할 수 있고, 나머지는 뒤에서 받는 동안 채워진다.
   *
   * 스키마는 그대로다(id·text·url·section·vector). 파일이 하나 더 생길 뿐이라
   * 검색·프롬프트 파이프라인은 건드리지 않는다. */
  const worksTs = fs.readFileSync(path.join(HERE, "..", "src", "works.ts"), "utf8");
  const shown = new Set([...worksTs.matchAll(/slug:\s*"([a-z]+-[a-z0-9]+)"/g)].map((m) => m[1]));
  const starter = docs.filter((d) => shown.has(d.id.split("#")[0]));
  const missing = [...shown].filter((sl) => !docs.some((d) => d.id.startsWith(sl + "#")));
  const sp = path.join(path.dirname(OUT), "myth-docs-starter.json");
  fs.writeFileSync(sp, JSON.stringify(starter), "utf8");
  const sbytes = fs.statSync(sp).size;
  console.log(`  starter  ${String(starter.length).padStart(5)}청크  ${(sbytes / 1e6).toFixed(2)}MB  (화면 ${shown.size}점)`);
  if (missing.length) console.log(`  ⚠ works.ts 에 있는데 말뭉치에 없는 슬러그 ${missing.length}개: ${missing.join(", ")}`);

  fs.writeFileSync(path.join(path.dirname(OUT), "myth-docs-index.json"),
    JSON.stringify({ built: docs.length, shards: manifest,
                     starter: { chunks: starter.length, works: shown.size, bytes: sbytes } }), "utf8");

  // 예전 이름의 통합본도 남긴다 — 이전 링크·도구가 깨지지 않게
  /* ⛔ 통합본(myth-docs.json)은 더 이상 만들지 않는다.
     샤딩으로 바꾼 뒤 앱은 myth-docs-index.json 과 myth-docs-{myth}.json 만 읽는다(rag.ts).
     그런데 통합본을 계속 만들어 커밋·배포까지 하고 있었다 — 22MB짜리 죽은 파일이
     재생성할 때마다 새 blob 으로 히스토리에 쌓였다(2026-08-31 확인, 이미 3판본).
     되살릴 일이 생기면 샤드를 합치면 된다. */
  console.log(`저장 — 샤드 ${manifest.length}개 · 청크 ${docs.length}개 (통합본은 만들지 않는다)`);

  // 브라우저 embed() 와 같은 공간인지 확인할 기준 문장.
  // 브라우저 콘솔에서 embed("<문장>") 을 돌려 이 벡터와 코사인을 재면 1에 가까워야 한다.
  if (process.argv.includes("--verify")) {
    const probe = "페르세포네를 납치하는 하데스";
    const v = await embed(probe);
    fs.writeFileSync(path.join(ROOT, "data", "embed-probe.json"),
      JSON.stringify({ model: MODEL_ID, file: MODEL_FILE + "_" + DTYPE, text: probe, vector: v }), "utf8");
    console.log("기준 문장 벡터 저장 — data/embed-probe.json");
  }
}

main().catch((e) => { console.error(e); process.exit(1); });
