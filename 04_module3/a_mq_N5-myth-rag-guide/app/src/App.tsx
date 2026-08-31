import { useState, useRef, useEffect, type CSSProperties } from "react";
import { retrieve, buildPrompt, loadCorpus, loadIndex, loadMyth, loadedMyths, DEFAULT_MYTH,
         onEmbedProgress, peekModelCache, type Retrieved, type ShardInfo } from "./rag";
import { chatStream, pingOllama, judgeWithOllama, type ChatMsg } from "./ollama";
import { geminiStream, judgeTurn } from "./gemini";
import type { JudgeResult } from "./judge";
import { WORKS, THUMB, MYTHS, CORPUS } from "./works";
import { Thumb } from "./Thumb";
import "./App.css";

interface Turn {
  role: "user" | "assistant";
  content: string;
  sources?: Retrieved[];
  question?: string;
  judge?: JudgeResult;
  judgeBy?: "qwen3.5:2b" | "gemini-3.5-flash";
  judgeError?: boolean;
  feedback?: "up" | "down";
}

type Phase = "idle" | "embed" | "search" | "stream" | "error-ollama";

/* 평가용 훅 — 주소에 ?evalhook=1 이 있을 때만 검색과 프롬프트 조립을 밖으로 연다.
 *
 * 왜 필요한가. 실험 2바퀴에서 같은 세팅을 다시 돌렸더니 문항 점수가 평균 48.4점
 * 움직였다. 원인은 답변 생성이 매번 다시 뽑기 때문인데, 브라우저로 재면 검색까지
 * 매번 다시 돈다. 그러면 «프롬프트를 바꾼 효과»와 «뽑기 운»을 가를 수 없다.
 * 그래서 검색 결과를 한 번만 뽑아 고정해 두고, 생성만 통제 조건에서 비교한다.
 *
 * 파이프라인은 건드리지 않는다 — 읽기만 내보낸다(9강의 변경 금지 조건). */
if (typeof window !== "undefined" && window.location.search.includes("evalhook=1")) {
  (window as unknown as { __rag?: unknown }).__rag = { retrieve, buildPrompt, loadCorpus };
}

/** ★실험 변수 — 근거로 넘길 청크 수 (8강: 한 번에 하나만 바꾼다)
 *  세팅 A = 15 (참조 구현 기본값) · 세팅 B = 6
 *
 *  ⚠️ 이 값은 순수한 한 축이 아니다. rag.ts 의 retrieve() 가
 *     벡터 = slice(0, min(10, k)) · BM25 = k - 벡터개수  로 배분하므로
 *     k=15 -> 벡터10 + BM25 5,  k=6 -> 벡터6 + BM25 0 이 된다.
 *     즉 k 를 줄이면 BM25 가 통째로 빠진다. 실험 해석 시 이 교란을 감안할 것.
 *  기록은 README.md 「실험」 절 참조. */
const TOP_K = 15;

// 파이프라인 단계 — 튜토리얼용 표시
const PHASE_LABEL: Record<Phase, string> = {
  idle: "",
  embed: "① 질문 임베딩 중 — 브라우저에서 질문을 벡터로 바꿉니다",
  search: "② 근거 검색 중 — 벡터 유사도와 BM25로 근거를 고릅니다",
  stream: "③ 답변 생성 중 — 찾은 근거를 붙여 모델이 답을 씁니다",
  "error-ollama": "연결 실패",
};

export default function App() {
  const [turns, setTurns] = useState<Turn[]>([
    {
      role: "assistant",
      content:
        "안녕하세요. MYTH GALLERY 안내 챗봇입니다. 그림 속 인물이 누구인지, 무슨 장면인지 물어보세요. 답은 작품 페이지에서 뽑은 근거로만 드립니다.",
    },
  ]);
  const [input, setInput] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [ollamaOk, setOllamaOk] = useState<boolean | null>(null);
  const [engine, setEngine] = useState<"local" | "gemini">("local");
  const [apiKey, setApiKey] = useState(() => localStorage.getItem("gemini_key") ?? "");
  const [showSource, setShowSource] = useState<Retrieved[] | null>(null);
  const [lastHits, setLastHits] = useState<Retrieved[] | null>(null);
  const [dlPct, setDlPct] = useState<number | null>(null);
  const [judgeBusy, setJudgeBusy] = useState(false);
  const [openSrc, setOpenSrc] = useState<Record<number, boolean>>({});
  const [hitsOpen, setHitsOpen] = useState(false);
  const [embedCached, setEmbedCached] = useState(false);
  const [shards, setShards] = useState<ShardInfo[] | null>(null);
  const [myths, setMyths] = useState<string[]>([]);        // 지금까지 받은 신화
  const [loadingMyth, setLoadingMyth] = useState<string | null>(null);
  const [dockOpen, setDockOpen] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  /** 정지 버튼으로 끊은 것인지 — 연결 실패와 구별하려고 따로 둔다 */
  const stoppedByUser = useRef(false);
  const modalRef = useRef<HTMLDivElement>(null);
  /** 모달을 연 버튼 — 닫을 때 포커스를 여기로 돌려준다 */
  const lastFocus = useRef<HTMLElement | null>(null);
  const inlineLogRef = useRef<HTMLDivElement>(null);
  const dockLogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    pingOllama().then(setOllamaOk);
    loadIndex().then(setShards).catch(() => undefined);
    // 기본은 그리스·로마만 받는다. 나머지는 방문자가 누를 때.
    loadMyth(DEFAULT_MYTH).then(() => setMyths(loadedMyths())).catch(() => undefined);
    peekModelCache().then(setEmbedCached); // 재방문이면 "캐시된 모델" 표시
    onEmbedProgress((p) => {
      if (p.cached) setEmbedCached(true);
      setDlPct(p.pct >= 100 ? null : p.pct);
    });
  }, []);

  // 답변이 길어질 때 대화 로그 '안에서만' 아래로 붙인다.
  // 예전에는 bottomRef.scrollIntoView()를 썼는데, 토큰이 올 때마다 페이지 전체가
  // 끌려 내려가 위쪽 작품 목록을 읽던 사람의 스크롤을 빼앗았다.
  useEffect(() => {
    for (const r of [inlineLogRef, dockLogRef]) {
      const el = r.current;
      if (el) el.scrollTop = el.scrollHeight;
    }
  }, [turns, phase, dockOpen]);

  /* 모달이 열리면 포커스를 안으로 넣고 배경 스크롤을 잠근다.
   * 안 하면 키보드 사용자는 Tab 을 페이지 처음부터 눌러 내려와야 하고,
   * 모달 뒤 페이지가 같이 스크롤돼 어디를 보고 있었는지 잃는다. */
  useEffect(() => {
    if (!showSource) return;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    modalRef.current?.focus();
    return () => {
      document.body.style.overflow = prevOverflow;
      lastFocus.current?.focus();   // 열었던 자리로 돌려준다
      lastFocus.current = null;
    };
  }, [showSource]);

  // Esc — 근거 모달이 열려 있으면 모달, 아니면 도크를 닫는다
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      if (showSource) setShowSource(null);
      else if (dockOpen) setDockOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [showSource, dockOpen]);

  async function ask() {
    const q = input.trim();
    if (!q || phase !== "idle") return;
    setInput("");
    stoppedByUser.current = false;
    setTurns((t) => [...t, { role: "user", content: q }]);

    let streamStarted = false;
    try {
      setPhase("embed");
      await new Promise((r) => setTimeout(r, 350)); // 임베딩 단계를 눈으로 볼 수 있게 짧게 표시
      setPhase("search");
      const hits = await retrieve(q, TOP_K);
      setDlPct(null);
      setLastHits(hits);
      setHitsOpen(false);
      await new Promise((r) => setTimeout(r, 450)); // 검색 결과를 눈으로 볼 수 있게 표시
      const prompt = buildPrompt(q, hits);
      const messages: ChatMsg[] = [
        {
          role: "system",
          content:
            "당신은 신화 명화 아카이브 'MYTH GALLERY'의 안내 도우미입니다. 주어진 자료에 근거한 내용만 답하고, 자료에 없는 정보는 '제가 가진 자료에는 없습니다'라고 답합니다. 근거 조각의 [ID]를 답에 표시합니다. 이 갤러리는 그리스·로마, 북유럽, 이집트, 메소포타미아, 힌두, 중국 여섯 신화만 다루며, 지금 실린 자료는 그리스·로마 작품입니다. 다루지 않는 신화나 작품을 물으면 넓혀서 답하지 말고 범위 밖임을 밝힙니다. 작품의 저작권·이용 가부·가격은 판정하지 않고 갤러리 담당자 문의를 안내합니다.",
        },
        { role: "user", content: prompt },
      ];

      const lastQ = q;
      setTurns((t) => [...t, { role: "assistant", content: "", sources: hits, question: lastQ }]);
      setPhase("stream");
      streamStarted = true;
      abortRef.current = new AbortController();
      let acc = "";
      const onPiece = (piece: string) => {
        acc += piece;
        setTurns((t) => {
          const copy = [...t];
          copy[copy.length - 1] = { ...copy[copy.length - 1], content: acc, sources: hits };
          return copy;
        });
      };
      if (engine === "gemini") {
        await geminiStream(
          [
            { role: "user", text: messages[0].content },
            { role: "user", text: messages[1].content },
          ],
          apiKey,
          onPiece,
          abortRef.current.signal,
        );
      } else {
        await chatStream(messages, onPiece, "qwen3.5:2b", abortRef.current.signal);
      }
      setPhase("idle");
      // ④ LLM-as-a-Judge — 답변에 쓴 엔진과 같은 모델이 판정한다
      //    로컬 → qwen 자기평가(API 키 불필요), gemini → gemini-3.5-flash
      setJudgeBusy(true);
      try {
        const src = hits.map((h) => `[${h.chunk.id}] ${h.chunk.text}`).join("\n");
        const by = engine === "gemini" && apiKey ? "gemini-3.5-flash" as const : "qwen3.5:2b" as const;
        const verdict =
          engine === "gemini" && apiKey
            ? await judgeTurn(lastQ, src, acc, apiKey)
            : await judgeWithOllama(lastQ, src, acc);
        setTurns((t) => {
          const copy = [...t];
          const li = copy.length - 1;
          copy[li] = { ...copy[li], judge: verdict, judgeBy: by };
          return copy;
        });
      } catch {
        // 판정 실패가 답변을 해치지 않게 배지만 단다
        setTurns((t) => {
          const copy = [...t];
          const li = copy.length - 1;
          copy[li] = { ...copy[li], judgeError: true };
          return copy;
        });
      } finally {
        setJudgeBusy(false);
      }
    } catch (e: unknown) {
      console.error("챗봇 파이프라인 오류:", e);
      setDlPct(null);
      const msg = e instanceof Error ? e.message : String(e);
      if (!streamStarted) {
        // 검색/임베딩 단계 오류 — 원인을 채팅창에 그대로 보여준다 (ollama와 무관)
        setTurns((t) => [
          ...t.filter((x) => x.content !== ""),
          { role: "assistant", content: `⚠ 답변을 만들지 못했습니다 — ${msg}` },
        ]);
        setPhase("idle");
        return;
      }
      // 사용자가 정지를 눌러 끊은 것은 연결 실패가 아니다.
      // 예전에는 여기서 ollama 미연결 배너까지 띄워 멀쩡한 연결을 끊긴 것처럼 보였다.
      // 6강 "스트리밍이 중단되어도 이미 받은 답변 청크를 지우지 않는다"에 따라
      // 받은 데까지는 그대로 두고 안내만 붙인다.
      if (stoppedByUser.current) {
        stoppedByUser.current = false;
        setTurns((t) => {
          const copy = [...t];
          const li = copy.length - 1;
          if (copy[li]?.role === "assistant") {
            copy[li] = {
              ...copy[li],
              content: (copy[li].content || "") + (copy[li].content ? "\n\n" : "") + "— 여기서 정지했습니다.",
            };
          }
          return copy;
        });
        setPhase("idle");
        return;
      }
      setPhase("error-ollama");
      setOllamaOk(false);
      setTurns((t) => [
        ...t.filter((x) => x.content !== ""),
        { role: "assistant", content: "⚠ 로컬 모델(ollama)에 연결하지 못했습니다 — 페이지 위 안내를 따라 ollama를 실행·설정한 뒤 다시 질문해 주세요." },
      ]);
      setPhase("idle");
    }
  }

  function stop() {
    stoppedByUser.current = true;
    abortRef.current?.abort();
    setPhase("idle");
  }

  function setFeedback(i: number, v: "up" | "down") {
    setTurns((t) => {
      const copy = [...t];
      copy[i] = { ...copy[i], feedback: copy[i].feedback === v ? undefined : v };
      return copy;
    });
    // 피드백은 로컬에만 기록 (제출 없음 — 데모)
    console.log("feedback", { turn: i, value: v });
  }

  const connBadge = (
    <span className={`conn ${ollamaOk === true ? "ok" : ollamaOk === false ? "bad" : ""}`}>
      {engine === "gemini"
        ? "Gemini API"
        : ollamaOk === true
          ? "ollama 연결됨"
          : ollamaOk === false
            ? "ollama 미연결"
            : "연결 확인 중…"}
    </span>
  );

  /** 대화 로그 + 입력칸. 인라인 섹션과 우측 도크가 같은 상태를 그대로 나눠 쓴다.
   *  컴포넌트로 빼지 않고 JSX를 돌려주는 함수로 둔 이유 — 렌더마다 새 컴포넌트가
   *  만들어지면 React가 입력칸을 다시 마운트해 타이핑 중 포커스가 날아간다. */
  const chatBody = (variant: "inline" | "dock") => (
    <>
      <div className="chat-log" ref={variant === "inline" ? inlineLogRef : dockLogRef}>
          {turns.map((t, i) => (
            <div key={i} className={`bubble ${t.role}`}>
              <div className="bubble-text">{t.content || (phase === "stream" && i === turns.length - 1 ? "…" : "")}</div>
              {t.role === "assistant" && t.question && (
                <div className="meta-row">
                  {t.judge ? (
                    <span className={`judge ${(t.judge.score ?? 0) >= 70 ? "ok" : "bad"}`}>
                      평가 {t.judge.score}점 (루브릭 평균) ·
                      {(t.judge.rubrics ?? []).map((r) => ` ${r.name} ${r.score}`).join(" ·")}
                      {t.judge.refusal ? " · 정당한 거부" : ""}
                      {t.judge.comment && <em> “{t.judge.comment}”</em>}
                      <span className="judge-by"> · 판정 {t.judgeBy === "gemini-3.5-flash" ? "gemini-3.5-flash" : "qwen3.5:2b 자기평가"}</span>
                    </span>
                  ) : t.judgeError ? (
                    <span className="judge fail">판정 실패 — 평가 모델이 결과를 만들지 못했습니다 (답변은 정상)</span>
                  ) : judgeBusy && i === turns.length - 1 ? (
                    <span className="judge">④ 판정 중… (LLM-as-a-Judge)</span>
                  ) : null}
                  <span className="feedback">
                    <button aria-label="좋아요" className={t.feedback === "up" ? "on" : ""} onClick={() => setFeedback(i, "up")}>👍</button>
                    <button aria-label="싫어요" className={t.feedback === "down" ? "on" : ""} onClick={() => setFeedback(i, "down")}>👎</button>
                  </span>
                </div>
              )}
              {t.sources && !(phase === "stream" && i === turns.length - 1) && (
                <div className="chips">
                  <button
                    className="chips-toggle"
                    onClick={() => setOpenSrc((m) => ({ ...m, [i]: !m[i] }))}
                  >
                    출처 {t.sources.length}개 {openSrc[i] ? "접기 ▴" : "펼쳐 보기 ▾"}
                  </button>
                  {t.sources[0].score < 0.55 && (
                    <span className="weak-badge">⚠ 최고 유사도 {(t.sources[0].score * 100).toFixed(1)}%</span>
                  )}
                  {openSrc[i] &&
                    t.sources.map((s) => (
                      <button
                        key={s.chunk.id}
                        className={`chip ${s.method === "bm25" ? "bm25" : "vec"}`}
                        onClick={(e) => {
                          lastFocus.current = e.currentTarget;
                          setShowSource(t.sources!);
                        }}
                      >
                        {s.chunk.id} · {s.chunk.section} · {s.method === "bm25" ? "BM25" : "벡터"} {(s.score * 100).toFixed(0)}%
                      </button>
                    ))}
                </div>
              )}
            </div>
          ))}
          {(phase === "embed" || phase === "search") && (
            <div className="phase-box">
              <span className="spinner" />
              <span>
                {phase === "embed" && embedCached
                  ? "① 질문 임베딩 중 — 캐시된 모델 사용 (다운로드 없음)"
                  : PHASE_LABEL[phase]}
                {dlPct !== null && (
                  <div className="dl-progress">
                    임베딩 모델을 내려받는 중 {dlPct}% — 첫 방문 1회(약 200MB), 이후 브라우저에 캐시됩니다
                  </div>
                )}
              </span>
            </div>
          )}
          {lastHits && phase === "stream" && (
            <div className="hits-box">
              <div className="hits-title">
                <button className="chips-toggle" onClick={() => setHitsOpen((o) => !o)}>
                  ② 검색된 근거 {lastHits.length}개 — 벡터 {lastHits.length - nBm} · BM25 {nBm}{" "}
                  {hitsOpen ? "접기 ▴" : "펼쳐 보기 ▾"}
                </button>
                {lastHits[0].score < 0.55 && (
                  <span className="weak-badge"> ⚠ 최고 유사도 {(lastHits[0].score * 100).toFixed(1)}% — 근거가 약합니다</span>
                )}
              </div>
              {hitsOpen &&
                lastHits.map((h) => (
                  <div key={h.chunk.id} className={`hit-row ${h.method === "bm25" ? "bm25" : "vec"}`}>
                    <span className="hit-id">{h.chunk.id}</span>
                    <span className="hit-sec">{h.chunk.section}</span>
                    <span className="hit-score" style={{ "--w": `${Math.round(h.score * 100)}%` } as CSSProperties}>
                      {h.method === "bm25" ? "BM25" : "벡터"} {(h.score * 100).toFixed(1)}%
                    </span>
                    <span className="hit-text">{h.chunk.text.slice(0, 80)}…</span>
                  </div>
                ))}
              {phase === "stream" && (
                <div className="hits-title" style={{ marginTop: hitsOpen ? ".6rem" : undefined }}>③ 이 근거로 답변을 만듭니다…</div>
              )}
            </div>
          )}
      </div>
      <div className="chat-input">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            // 한글 조합 중의 Enter는 글자를 확정하는 키다. isComposing을 보지 않으면
            // "프로세르피나" 를 확정하려고 누른 Enter가 그대로 질문 전송이 된다.
            if (e.key === "Enter" && !e.nativeEvent.isComposing) ask();
          }}
          placeholder="예: 사계절이 생긴 신화가 뭐야?"
          aria-label="작품에 대해 질문하기"
          disabled={phase !== "idle"}
        />
        {phase === "stream" ? (
          <button onClick={stop} className="stop-btn">정지</button>
        ) : (
          <button onClick={ask} disabled={phase !== "idle" || !input.trim()}>
            보내기
          </button>
        )}
      </div>
    </>
  );

  const nBm = lastHits ? lastHits.filter((h) => h.method === "bm25").length : 0;

  return (
    <div className="app">
      <header className="hero">
        <div className="hero-inner">
          <p className="hero-badge">여섯 신화 · 그림으로 읽는 신화 아카이브</p>
          <h1>MYTH <span className="accent">GALLERY</span></h1>
          <p className="hero-sub">
            그리스·로마, 북유럽, 이집트, 메소포타미아, 힌두, 중국 — 여섯 신화의 명화를 모은
            아카이브입니다. 그림 앞에서 &ldquo;이게 무슨 장면이지?&rdquo; 싶을 때 아래 챗봇에게 —
            로컬 모델이 작품 페이지에서 근거를 찾아 답합니다.
          </p>
          <a className="hero-cta" href="#chat">챗봇으로 물어보기 ↓</a>
        </div>
      </header>

      <a className="skip-link" href="#chat">본문(챗봇)으로 건너뛰기</a>

      {/* 9강: "이 순서가 README와 안내 페이지에서 같은 말로 보이는지 마지막으로 대조합니다."
          → README.md 「처음 열었을 때 순서」와 같은 문장을 쓴다. 조건부로 감싸지 않는다. */}
      <section className="steps" aria-label="처음 열었을 때 순서">
        <h2>처음 열었을 때 순서</h2>
        <ol>
          <li>배포 주소를 열고 이 챗봇이 <b>다루는 자료와 질문 범위</b>를 읽습니다</li>
          <li><b>Ollama</b>를 실행하고 <code>qwen3.5:2b</code>를 준비합니다</li>
          <li>첫 방문의 <b>임베딩 다운로드</b>를 기다립니다 <span className="fine">(약 200MB · 1회, 이후 캐시)</span></li>
          <li>안내된 질문과 <b>자료 밖 질문</b>을 각각 넣어 봅니다</li>
        </ol>
        <p className="steps-note">
          원격 주소에서 로컬 Ollama를 부르려면 <code>OLLAMA_ORIGINS</code> 허용이 필요합니다 — 아래 «왜 Ollama가 필요한가요?» 참고.
          Chrome·Edge를 권장합니다. Safari는 https 페이지에서 로컬 호출을 차단합니다.
        </p>
      </section>

      <div className="marquee" aria-hidden="true">
        <div className="marquee-track">
          {[0, 1].map((g) => (
            <div className="marquee-group" key={g}>
              {[0, 1, 2, 3, 4, 5].map((i) => (
                <span key={i}>FROM MYTH TO CANVAS <i>∞</i></span>
              ))}
            </div>
          ))}
        </div>
      </div>

      <main>
      <section className="engine">
        <div className="engine-row">
          <span>답변 엔진:</span>
          <label><input type="radio" checked={engine==="local"} onChange={()=>setEngine("local")} /> 로컬 ollama (qwen3.5:2b)</label>
          <label><input type="radio" checked={engine==="gemini"} onChange={()=>setEngine("gemini")} /> Gemini API</label>
        </div>
        {engine === "gemini" && (
          <div className="engine-row">
            <input
              type="password"
              placeholder="Gemini API 키 (브라우저에만 저장됩니다)"
              value={apiKey}
              onChange={(e) => { setApiKey(e.target.value); localStorage.setItem("gemini_key", e.target.value); }}
            />
          </div>
        )}
      </section>

      {ollamaOk === false && engine === "local" && (
        <div className="banner">
          <strong>로컬 모델(ollama)에 연결할 수 없습니다.</strong>
          <ol>
            <li>브라우저 확인 — Safari는 이 페이지(https)에서 로컬 ollama 호출을 차단하므로 Chrome·Edge를 사용하세요. Chrome에서 "로컬 네트워크" 접근 권한을 물으면 <strong>허용</strong>을 누릅니다.</li>
            <li><code>ollama serve</code> 실행 (또는 Ollama 앱 실행) · 모델 확인: <code>ollama pull qwen3.5:2b</code></li>
            <li>
              github.io에서 열었다면 CORS 허용 — 운영 체제별로 한 번만 설정하고 Ollama를 재시작합니다:
              <div className="os-guide">
                <div><strong>macOS</strong><code>launchctl setenv OLLAMA_ORIGINS "https://*.github.io"</code>입력 후 메뉴 막대의 Ollama 앱을 종료하고 다시 실행합니다.</div>
                <div><strong>Windows</strong>작업 표시줄에서 Ollama를 종료합니다. 설정에서 <code>환경 변수</code>를 검색해 <code>계정의 환경 변수 편집</code>을 열고 새 변수 <code>OLLAMA_ORIGINS</code>에 <code>https://*.github.io</code>를 넣은 뒤 Ollama를 다시 시작합니다.</div>
                <div><strong>Linux</strong><code>sudo systemctl edit ollama.service</code>를 열어 <code>[Service]</code> 아래에 <code>Environment="OLLAMA_ORIGINS=https://*.github.io"</code>를 추가하고 <code>sudo systemctl restart ollama</code>로 재시작합니다.</div>
              </div>
            </li>
          </ol>
          <button onClick={() => pingOllama().then(setOllamaOk)}>다시 확인</button>
        </div>
      )}

      <section className="info">
        <div className="card card-a">
          <h2>MYTH GALLERY란?</h2>
          <p>
            여섯 신화의 그림을 신화·작가·인물·사조로 엮어 보는 아카이브입니다. 이 챗봇이
            근거로 삼는 것은 그중 <b>{CORPUS.works}점</b>이고, 첫 방문에는
            <b>그리스·로마</b>만 받고 다른 신화는 <b>누를 때</b> 받습니다.
          </p>
        </div>
        <div className="card card-b">
          <h2>근거 원칙</h2>
          <p>
            모든 답변은 <b>실제로 열리는 작품 페이지</b>에서 뽑은 조각에 근거합니다. 자료에 없으면
            없다고 답합니다. 답변 아래 출처 칩을 누르면 근거 조각과 원문 주소가 나옵니다.
          </p>
        </div>
        <div className="card card-c">
          <h2>실행 구조</h2>
          <p>
            서버가 없습니다. 브라우저가 직접 로컬 ollama(qwen3.5:2b)를 호출하고, 질문 임베딩도
            브라우저에서 돕니다. Gemini API 키를 넣으면 Gemini가 답변을 만듭니다.
          </p>
        </div>
      </section>

      <section className="scope">
        <div className="scope-head">
          <h2>이 챗봇이 아는 작품 — {CORPUS.works}점</h2>
          <p>
            MYTH GALLERY 아카이브 <b>{CORPUS.archive}점</b> 가운데 <b>{CORPUS.works}점</b>을
            사실 단위 <b>{CORPUS.chunks.toLocaleString()}조각</b>으로 나눠 실어 두었습니다.
            아래는 그중 <b>맛보기 {WORKS.length}점</b>이고, <b>목록에 없어도 실린 작품이면 답합니다.</b>
            그림을 누르면 근거가 된 원문 페이지가 열립니다.
          </p>
        </div>
        <ul className="work-grid">
          {WORKS.map((w) => (
            <li key={w.slug}>
              <a href={w.url} target="_blank" rel="noreferrer">
                <Thumb src={THUMB(w.slug)} alt={w.title} />
                <div className="work-meta">
                  <strong>{w.title}</strong>
                  <span>{w.artist}</span>
                  <span className="work-era">{w.era}</span>
                  <span className="work-foot">
                    <span className="work-myth">{w.myth}</span>
                    <span className="work-chunks">근거 조각 {w.chunks}개</span>
                  </span>
                </div>
              </a>
            </li>
          ))}
        </ul>

        <div className="myth-scope">
          <h3>지금 브라우저에 받아 둔 신화</h3>
          <ul>
            {MYTHS.map((m) => {
              const sh = shards?.find((s) => s.myth === m.code);
              const on = myths.includes(m.code);
              const busy = loadingMyth === m.code;
              return (
                <li key={m.name} className={on ? "on" : "off"}>
                  <b>{m.name}</b>
                  <span>{m.works}점</span>
                  {on ? (
                    <em>불러옴</em>
                  ) : (
                    <button
                      className="myth-load"
                      disabled={busy || !sh}
                      onClick={async () => {
                        setLoadingMyth(m.code);
                        try {
                          await loadMyth(m.code);
                          setMyths(loadedMyths());
                        } finally {
                          setLoadingMyth(null);
                        }
                      }}
                    >
                      {busy ? "받는 중…" : sh ? `불러오기 (${(sh.bytes / 1e6).toFixed(1)}MB)` : "준비 안 됨"}
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
          <p className="fine">
벡터스토어를 <b>신화별 파일로 나눠</b> 두었습니다. 한 번에 다 받으면 첫 방문이 무거워지므로
            처음에는 <b>그리스·로마만</b> 받고, 다른 신화는 <b>위 버튼을 누를 때</b> 받습니다.
            아직 안 받은 신화를 물으면 지어내지 않고 <b>범위 밖이라고 알립니다</b> — 불러온 뒤 다시 물어보세요.
          </p>
        </div>
      </section>

      <section className="faq">
        <h2>먼저 읽어 주세요</h2>
        <div className="faq-grid">
          <div>
            <h3>무엇을 물어볼 수 있나요?</h3>
            <p>
              실린 {CORPUS.works}점의 <b>작가·제작연도·매체·소장처·사조</b>, 그림 속 <b>장면 설명</b>,
              바탕이 된 <b>신화 이야기</b>, <b>감상 포인트</b>를 물을 수 있습니다.
            </p>
            <p className="ex">
              &ldquo;프로세르피나의 납치는 누가 그렸어?&rdquo; · &ldquo;큐피드와 프시케 이야기가 뭐야?&rdquo;
            </p>
          </div>
          <div>
            <h3>왜 답하지 못하는 질문이 있나요?</h3>
            <p>
              이 챗봇은 <b>작품 페이지에서 뽑은 조각 안에서만</b> 답합니다. 시세·감정,
              저작권 가부, 수록되지 않은 신화, 이미지 생성은 다루지 않습니다.
            </p>
            <p className="ex">
              모르면 지어내지 않고 <b>&ldquo;가진 자료에는 없습니다&rdquo;</b>라고 답하는 것이 정상 동작입니다.
            </p>
          </div>
          <div>
            <h3>왜 Ollama가 필요한가요?</h3>
            <p>
              이 페이지에는 <b>서버가 없습니다.</b> 답을 만드는 모델은 <b>여러분 컴퓨터에서</b> 돕니다.
              그래서 Ollama가 실행 중이어야 하고, 이 주소에서 부를 수 있도록 <code>OLLAMA_ORIGINS</code> 허용이 필요합니다.
            </p>
            <p className="ex">
              첫 방문에는 질문을 벡터로 바꿀 <b>임베딩 모델 약 200MB</b>를 한 번 내려받습니다.
            </p>
          </div>
          <div>
            <h3>답을 어디까지 믿나요?</h3>
            <p>
              문장 안의 <code>[ID]</code>와 아래 <b>출처 칩</b>이 근거를 가리킵니다. 칩을 누르면
              실제 조각과 유사도가 보이고 원문으로 갈 수 있습니다.
            </p>
            <p className="ex">
              판정 배지는 같은 2B 모델이 매기므로 <b>독립 심사가 아닙니다.</b> 거친 신호로만 읽어 주세요.
            </p>
          </div>
        </div>
      </section>

      <section id="chat" className="chat">
        <h2>
          MYTH GALLERY 안내 챗봇
          {connBadge}
        </h2>
        {chatBody("inline")}
      </section>

      {/* 우측 도크 — 페이지를 읽으면서 물어볼 수 있게. 인라인 챗봇과 같은 대화를 공유한다. */}
      <div className={`dock ${dockOpen ? "open" : ""}`}>
        {dockOpen && (
          <div className="dock-panel" id="dock-panel" role="complementary" aria-label="MYTH GALLERY 안내 챗봇">
            <div className="dock-head">
              <b>안내 챗봇</b>
              {connBadge}
              <button className="dock-close" onClick={() => setDockOpen(false)} aria-label="챗봇 닫기">✕</button>
            </div>
            {chatBody("dock")}
          </div>
        )}
        <button
          className="dock-tab"
          onClick={() => setDockOpen((o) => !o)}
          aria-expanded={dockOpen}
          aria-controls="dock-panel"
        >
          {dockOpen ? "챗봇 접기 ▾" : "💬 챗봇에게 물어보기"}
        </button>
      </div>


      {showSource && (
        <div className="modal" onClick={() => setShowSource(null)}>
          <div
            className="modal-body"
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-title"
            ref={modalRef}
            tabIndex={-1}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 id="modal-title">근거 조각</h3>
            {showSource.map((s) => (
              <div key={s.chunk.id} className="source-item">
                <div className="source-meta">
                  {s.chunk.id} · {s.chunk.section} · {s.method === "bm25" ? "BM25" : "벡터 유사도"} {(s.score * 100).toFixed(0)}%
                </div>
                <p>{s.chunk.text}</p>
                <a href={s.chunk.url} target="_blank" rel="noreferrer">원문 보기 →</a>
              </div>
            ))}
            <button onClick={() => setShowSource(null)}>닫기</button>
          </div>
        </div>
      )}

      </main>

      <footer className="footer">
        <p>
          MYTH GALLERY 안내 챗봇 — 로컬 실행. 자료: MYTH GALLERY 공개 작품 페이지.
          모델: qwen3.5:2b (ollama) · 임베딩: embeddinggemma-300m (브라우저).
        </p>
      </footer>
    </div>
  );
}
