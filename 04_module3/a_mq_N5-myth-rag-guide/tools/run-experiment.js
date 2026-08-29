/* 모듈3 노드5 · 8강 실험 수집기 — 브라우저 콘솔(또는 자동화)에 붙여 실행한다.
 *
 * 왜 스크립트인가 — 1바퀴는 사람이 9문항을 손으로 넣고 화면을 읽어 적었다.
 * 그러면 세팅을 바꿔 다시 돌릴 때 조건이 미묘하게 달라진다(입력 순서·대기 시간).
 * 8강의 「고정 질문을 각 실행 행에서 같은 기준으로 본다」를 지키려면 실행도 고정해야 한다.
 *
 * 쓰는 법
 *   __EXP.start('A2')   // 실행 시작 (태그는 세팅 이름)
 *   __EXP.state()       // 진행 상황
 *   __EXP.json()        // 끝난 뒤 결과 JSON 문자열
 *
 * 결과 스키마는 tools/experiment-A.json 과 같다. 실패한 답도 그대로 남긴다.
 */
(() => {
  // ── 고정 질문 세트 (1바퀴와 동일 — 실험 도중 바꾸지 않는다) ────────────
  const QS = [
    { id: "Q1", kind: "정상", q: "사계절이 생긴 신화가 뭐야?" },
    { id: "Q2", kind: "정상", q: "프로세르피나의 납치는 누가 그렸어?" },
    { id: "Q3", kind: "정상", q: "헤라클레스가 켄타우로스를 죽인 이야기 알려줘" },
    { id: "Q4", kind: "경계", q: "루벤스 작품과 부셰 작품은 각각 어디에 소장돼 있어?" },
    { id: "Q5", kind: "경계", q: "아폴론이 나오는 그림이 몇 점이야?" },
    { id: "Q6", kind: "경계", q: "그 유명한 그림 보여줘" },
    { id: "Q7", kind: "무근거", q: "일본 신화 그림도 있어?" },
    { id: "Q8", kind: "무근거", q: "이 그림 지금 얼마야?" },
    { id: "Q9", kind: "무근거", q: "반 고흐의 별이 빛나는 밤 설명해줘" },
  ];

  /* 인용 판정 — 답변 본문에 청크 ID가 들어 있으면 인용으로 센다.
   * ⚠️ 1바퀴는 이 값을 사람이 눈으로 적었는데 Q5·Q6 이 누락됐다.
   *    둘 다 ID 를 적었지만 `**greek-…**` 처럼 굵게 감싸 대괄호가 없었다.
   *    지표가 답변이 아니라 표기 습관을 센 셈이라, 여기서는 ID 패턴만 본다. */
  const CITED_RE = /greek-[0-9a-f]{10}/;

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  /** 인라인 챗봇 영역 (도크가 열려 있어도 첫 번째가 인라인) */
  const chat = () => $("section.chat");

  function setInput(el, v) {
    const set = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
    set.call(el, v);
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }

  /** 판정 배지 텍스트 → 숫자. 화면에 보이는 값을 그대로 읽는다(별도 계산 없음). */
  function parseJudge(text) {
    if (!text) return null;
    const n = (re) => { const m = text.match(re); return m ? parseInt(m[1], 10) : null; };
    return {
      score: n(/평가\s*(\d+)\s*점/),
      grounded_s: n(/근거 충실성\s*(\d+)/),
      noHalluc_s: n(/환각 통제\s*(\d+)/),
      cited_s: n(/출처 표시\s*(\d+)/),
      refusal: /정당한 거부/.test(text),
      comment: (text.match(/[“"]([^”"]+)[”"]/) || [, ""])[1],
    };
  }

  async function askOne(item, timeoutMs = 240000) {
    /* ⚠️ DOM 참조를 캐시하지 않는다.
     * 처음엔 root 를 askOne 시작 때 한 번만 잡았는데, React 가 재렌더하며
     * 그 노드를 갈아끼우면 참조가 문서에서 떨어져 나간다. 그러면 폴링이
     * 영영 옛 스냅숏(인사말 1개)만 보게 되어 조건이 참이 되지 않는다.
     * 실제로 1회차에서 판정이 끝났는데도 수집기가 안 넘어갔다.
     * → 매 틱마다 다시 찾는다. */
    const before = $$(".bubble", chat()).length;
    setInput($(".chat-input input", chat()), item.q);
    await sleep(200);
    const btn = $$(".chat-input button", chat()).find((b) => !b.classList.contains("stop-btn"));
    if (!btn || btn.disabled) throw new Error(item.id + ": 보내기 불가");
    btn.click();

    const t0 = Date.now();
    let last = null;
    for (;;) {
      await sleep(1000);
      const bubbles = $$(".bubble", chat());          // ← 매번 다시 찾는다
      if (bubbles.length >= before + 2) {
        last = bubbles[bubbles.length - 1];
        const meta = $(".judge", last);
        const done = meta && !/판정 중/.test(meta.textContent);
        const failed = meta && /판정 실패/.test(meta.textContent);
        EXP.progress = { id: item.id, bubbles: bubbles.length, judged: !!meta,
                         sec: Math.round((Date.now() - t0) / 1000) };
        if (done || failed) break;
      } else {
        EXP.progress = { id: item.id, bubbles: bubbles.length, judged: false,
                         sec: Math.round((Date.now() - t0) / 1000) };
      }
      if (Date.now() - t0 > timeoutMs) break; // 시간 초과도 결과로 남긴다
    }

    const answer = last ? ($(".bubble-text", last)?.textContent || "").trim() : "";
    const judgeTxt = last ? ($(".judge", last)?.textContent || "") : "";
    // 근거 구성 — 출처 칩 토글 문구에서 개수, 칩에서 방법별 수
    let vector = null, bm25 = null, total = null;
    if (last) {
      const tg = $(".chips-toggle", last);
      const m = tg && tg.textContent.match(/출처\s*(\d+)\s*개/);
      if (m) total = parseInt(m[1], 10);
      if (tg && /펼쳐/.test(tg.textContent)) tg.click(); // 칩을 열어야 방법이 보인다
      await sleep(120);
      const chips = $$(".chip", last);
      if (chips.length) {
        bm25 = chips.filter((c) => c.classList.contains("bm25")).length;
        vector = chips.length - bm25;
      }
    }
    return {
      id: item.id, kind: item.kind, q: item.q, answer,
      hits: { total, vector, bm25 },
      judge: parseJudge(judgeTxt),
      cited: CITED_RE.test(answer),
      elapsed_s: Math.round((Date.now() - t0) / 1000),
    };
  }

  const EXP = {
    tag: null, rows: [], running: false, error: null, progress: null,
    async start(tag) {
      if (this.running) return "이미 실행 중";
      this.tag = tag; this.rows = []; this.running = true; this.error = null;
      try {
        for (const item of QS) {
          this.rows.push(await askOne(item));
        }
      } catch (e) {
        this.error = String(e && e.message ? e.message : e);
      }
      this.running = false;
      return "완료";
    },
    state() {
      return { tag: this.tag, running: this.running, done: this.rows.length, total: QS.length,
               error: this.error, last: this.rows.length ? this.rows[this.rows.length - 1].id : null,
               progress: this.progress || null };
    },
    json() { return JSON.stringify(this.rows, null, 1); },
  };
  window.__EXP = EXP;
  return "수집기 준비됨 — __EXP.start('태그')";
})();
