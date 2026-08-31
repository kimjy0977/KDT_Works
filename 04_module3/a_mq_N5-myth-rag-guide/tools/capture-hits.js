/* eval-hits 재생성 — 브라우저에서 실행한다 (모듈3 노드5 · 실험 4바퀴 ①단계)
 *
 * 무엇을 하나
 *   고정 질문 13개를 앱의 실제 retrieve() 로 돌려 근거 15조각을 뽑아 고정한다.
 *   이렇게 한 번 뽑아 두면 모든 세팅이 **같은 근거**를 쓰므로,
 *   세팅 사이의 차이에서 «검색 뽑기 운»이 빠진다(3바퀴에서 이걸로 재현성 0.0점을 얻었다).
 *
 * ★반드시 지킬 것 — 6신화를 모두 불러온 뒤에 뽑는다.
 *   앱 기본은 그리스로마만 받는다. 그대로 뽑으면 후보가 469점뿐이라
 *   «982점으로 늘린 뒤의 검색»을 재는 것이 아니다. 3바퀴와 같은 조건이 되어 버린다.
 *   이 스크립트는 그래서 loadMyth 를 6종 다 돌린 뒤에 검색한다.
 *
 * 쓰는 법
 *   1) 로컬 서버를 띄운다      python -m http.server 8791   (배포 폴더에서)
 *   2) 수신기를 띄운다          python tools/recv-hits.py
 *   3) 브라우저에서 연다        http://localhost:8791/?evalhook=1
 *   4) 이 파일 내용을 콘솔에 붙여 실행한다
 *   5) tools/eval-hits.json 이 덮인다  → python tools/round4-precheck.py 로 확인
 */
(async () => {
  const QUESTIONS = [
    { id: "Q1",  kind: "정상",   q: "사계절이 생긴 신화가 뭐야?" },
    { id: "Q2",  kind: "정상",   q: "프로세르피나의 납치는 누가 그렸어?" },
    { id: "Q3",  kind: "정상",   q: "헤라클레스가 켄타우로스를 죽인 이야기 알려줘" },
    { id: "Q4",  kind: "경계",   q: "루벤스 작품과 부셰 작품은 각각 어디에 소장돼 있어?" },
    { id: "Q5",  kind: "경계",   q: "아폴론이 나오는 그림이 몇 점이야?" },
    { id: "Q6",  kind: "경계",   q: "그 유명한 그림 보여줘" },
    { id: "Q7",  kind: "무근거", q: "일본 신화 그림도 있어?" },
    { id: "Q8",  kind: "무근거", q: "이 그림 지금 얼마야?" },
    { id: "Q9",  kind: "무근거", q: "반 고흐의 별이 빛나는 밤 설명해줘" },
    { id: "Q10", kind: "정상",   q: "큐피드와 프시케는 누가 그렸고 어디 소장돼 있어?" },
    { id: "Q11", kind: "정상",   q: "아폴론과 다프네는 누가 그렸어?" },
    { id: "Q12", kind: "정상",   q: "오디세우스와 폴리페모스 그림은 어느 시대 작품이야?" },
    { id: "Q13", kind: "경계",   q: "비너스가 나오는 작품 있어?" },
  ];
  const MYTHS = ["greek", "norse", "egypt", "meso", "hindu", "chinese"];
  const K = 15;                       // 3바퀴와 같은 값 — 바꾸면 비교가 끊긴다

  const rag = window.__rag;
  if (!rag) { console.error("__rag 가 없다. 주소에 ?evalhook=1 을 붙여 다시 열어라."); return; }

  // ① 6신화를 전부 불러온다 — 이걸 빼먹으면 그리스로마만 후보가 된다
  console.log("신화 불러오는 중…");
  const mod = await import("./assets/" + [...document.scripts]
    .map(s => s.src.split("/").pop()).find(n => /^index-.*\.js$/.test(n)))
    .catch(() => null);
  // 앱이 내보낸 loadMyth 가 없으면 화면 버튼을 눌러 받는다
  for (const m of MYTHS) {
    const btn = [...document.querySelectorAll(".myth-load")]
      .find(b => b.closest("li")?.textContent?.includes(m) ||
                 b.getAttribute("data-code") === m);
    if (btn && !btn.disabled) { btn.click(); }
  }
  // 로드가 끝날 때까지 기다린다 (말뭉치 크기가 안 늘면 끝난 것)
  let prev = -1, same = 0;
  for (let i = 0; i < 240; i++) {
    const n = (await rag.loadCorpus()).length;
    if (n === prev) { if (++same >= 4) break; } else { same = 0; prev = n; }
    await new Promise(r => setTimeout(r, 500));
  }
  const corpus = await rag.loadCorpus();
  const myths = new Set(corpus.map(d => d.id.split("-")[0]));
  console.log(`말뭉치 ${corpus.length}청크 · 신화 ${[...myths].sort().join(", ")}`);
  if (myths.size < 6) {
    console.error(`❌ 신화가 ${myths.size}종뿐이다. 화면에서 나머지를 «불러오기» 한 뒤 다시 실행해라.`);
    return;
  }

  // ② 검색을 한 번씩만 돌려 고정한다
  const out = [];
  for (const it of QUESTIONS) {
    const hits = await rag.retrieve(it.q, K);
    out.push({
      id: it.id, kind: it.kind, q: it.q,
      hits: hits.map(h => ({
        id: h.chunk.id, section: h.chunk.section, url: h.chunk.url,
        text: h.chunk.text, score: h.score, method: h.method,
      })),
    });
    console.log(`  ${it.id} ${hits.length}조각 · 최고 ${hits[0]?.score?.toFixed(3)}`);
  }

  // ③ 로컬 수신기로 보낸다
  const res = await fetch("http://127.0.0.1:8899/eval-hits.json", {
    method: "POST", headers: { "content-type": "application/json" },
    body: JSON.stringify(out),
  }).catch(e => ({ ok: false, statusText: String(e) }));
  console.log(res.ok ? "✅ tools/eval-hits.json 저장됨" : "❌ 수신기 응답 없음 — recv-hits.py 를 띄웠나");
  window.__hits = out;      // 수신기가 없으면 여기서 직접 꺼내 쓴다
})();
