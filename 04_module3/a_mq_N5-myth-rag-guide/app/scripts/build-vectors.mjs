/* 청크 → 768차원 벡터스토어 (모듈3 노드5 메인 퀘스트 · 4강)
 *
 * chunks.json 의 각 청크를 embeddinggemma-300m 으로 임베딩해
 * app/public/myth-docs.json 을 만든다. 스키마는 참조 구현과 동일하게 유지한다:
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
  fs.writeFileSync(OUT, JSON.stringify(docs), "utf8");
  console.log(`저장 — ${OUT} (${docs.length}개, ${(fs.statSync(OUT).size / 1e6).toFixed(2)}MB)`);

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
