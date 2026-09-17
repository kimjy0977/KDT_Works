# -*- coding: utf-8 -*-
"""★데모 — 「발견 데스크」 대화창.

두 요건이 «서로 다른 것»을 요구한다
  LMS   답변과 함께 «호출한 도구 · 근거로 쓴 문서 부분 · 검증 결과»를 보여 준다
  노션  실제로 사용자가 «대화»를 실험해볼 수 있는 웹 데모

1차에는 LMS 만 보고 만들었더니 «계기판»이 됐다. 2차에서 말풍선 대화로 바꿨다.
이 3차는 «레퍼런스를 실제로 보고» 다시 짠 것이다.

★Perplexity 를 열어 «같은 질문»을 넣어 봤다 (2026-09-18)
  Perplexity  「공룡은 약 6,600만 년 전 … 멸종했습니다」 [출처 칩]
  우리        「★비조류 공룡은 약 6,600만 년 전 …」      [정설]
  ⇒ Perplexity 는 «어디서 왔나»(출처)를 문장 뒤에 단다.
    우리는 같은 자리에 «얼마나 믿을 수 있나»(확실성)를 단다.
    그리고 Perplexity 는 「비조류」를 안 붙였다 — 조류는 살아남았는데.

★베낀 것 (검증된 대화 UI 문법)
  · 단계 + «시간» 표시 (「조사 완료 1초」) — 우리는 20~60초라 더 필요하다
  · 질문은 오른쪽, 답변은 왼쪽
  · 핵심 수치 굵게 · 답변 아래 접이식 근거
  · 「후속 질문하기」 — «이어 물어도 된다»는 신호

★우리만 살린 것
  1 확실성을 «말풍선 자체»에 입힌다 (왼쪽 컬러 바 + 칩)
  2 넘기기 3갈래를 시각적으로 구분 (REFUSE·ESCALATE·ASK 는 고치는 법이 다르다)
  3 근거를 «파이프라인 순서»로 (①→②→③→④)
  4 ★지식원 패널 — 무엇을 아는지 «등급별로» 보여준다
  5 ★「지금 들어온 발표」 — 최근 72시간 기사에서 시작 질문을 만든다.
    고정 예시는 «어제도 오늘도 같은 화면»이라 죽은 데모가 된다.

  streamlit run app.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import streamlit as st  # noqa: E402

st.set_page_config(page_title="발견 데스크", page_icon="🔭",
                   layout="centered", initial_sidebar_state="expanded")

# ─────────────────────────────────────────────────────────
# 디자인 토큰 — 색은 «등급이 무엇인가»를 말한다. 장식이 아니다.
#   ⚠ 색«만»으로 구분하지 않는다 — 이름을 늘 같이 쓴다(색각 이상 대응).
# ─────────────────────────────────────────────────────────
CERT = {
    "정설": ("#1B5E20", "#E8F5E9", "널리 합의된 것"),
    "추정": ("#E65100", "#FFF3E0", "오차가 있는 것"),
    "논쟁": ("#BF360C", "#FBE9E7", "학계가 갈리는 것"),
    "신설": ("#B71C1C", "#FFEBEE", "최근 발표 — 아직 검증 안 됨"),
    "최근": ("#0D47A1", "#E3F2FD", "최근 발표"),
}
# ★넘기기 3갈래 — «고치는 방법»이 서로 달라서 화면에서도 갈라야 한다
DECISION = {
    "REFUSE":   ("#455A64", "#ECEFF1", "다루지 않는 주제",
                 "경계가 새면 라우터를 고친다"),
    "ESCALATE": ("#6A1B9A", "#F3E5F5", "다루는 주제인데 자료에 없음",
                 "잦아지면 지식원을 늘린다"),
    "ASK":      ("#00695C", "#E0F2F1", "후보가 여럿이라 되물음",
                 "잦아지면 질문을 좁히게 유도한다"),
}
ROUTE_KO = {"SPACE": "우주", "ARCHAEO": "고고학", "PALEO": "고생물",
            "CONCEPT": "개념·용어", "OTHER": "범위 밖"}

st.markdown("""
<style>
  .block-container { max-width: 780px; padding-top: 2.2rem; }
  .chip { display:inline-block; padding:2px 9px; border-radius:10px;
          font-size:.74rem; font-weight:700; color:#fff; margin-right:5px;
          letter-spacing:-.2px; }
  .cert-wrap { border-left:4px solid var(--c); padding:.55rem .85rem;
               background:var(--bg); border-radius:0 8px 8px 0; margin:.2rem 0 .5rem 0; }
  .note { color:#6b7280; font-size:.8rem; margin:.3rem 0 0 0; line-height:1.5; }
  .srcrow { font-size:.8rem; color:#374151; padding:.3rem 0;
            border-bottom:1px solid #f0f0f0; }
  .srcrow b { color:#111; }
  .step { font-size:.82rem; color:#374151; padding:.15rem 0; }
  .step .n { display:inline-block; width:1.35rem; color:#9ca3af; font-weight:700; }
  .tl { border-left:2px solid #e5e7eb; margin-left:.45rem; padding-left:.9rem; }
</style>
""", unsafe_allow_html=True)

_qp = st.query_params
OPEN_WHY = _qp.get("open") in ("1", "true")
DEMO_FILE = HERE / "demo_runs.json"


def _seed_queue():
    try:
        qs = _qp.get_all("q")
    except Exception:
        v = _qp.get("q")
        qs = [v] if isinstance(v, str) else list(v or [])
    return [x for x in qs if x]


@st.cache_data
def load_demo():
    if not DEMO_FILE.exists():
        return {}
    return json.loads(DEMO_FILE.read_text(encoding="utf-8"))


@st.cache_data
def load_sources():
    """★지식원이 «무엇을 담고 있나» — 등급별 구성과 최근 발표.

    Perplexity 는 「출처 10」을 보여준다. 우리는 그 자리에
    «등급별 구성»을 보여준다 — 이 데스크가 무엇을 아는지가 한눈에 들어온다.
    """
    facts = json.loads((HERE / "facts_base.json").read_text(encoding="utf-8"))["facts"]
    kb = json.loads((HERE / "store/knowledge.json").read_text(encoding="utf-8"))
    arts = kb["articles"]
    grade, route = {}, {}
    for f in facts:
        grade[f["certainty"]] = grade.get(f["certainty"], 0) + 1
        route[f["route"]] = route.get(f["route"], 0) + 1
    srcs = {}
    for a in arts:
        srcs[a.get("source", "?")] = srcs.get(a.get("source", "?"), 0) + 1
    recent = {}
    for a in arts:
        recent.setdefault(a["route"], []).append(a)
    return dict(facts=facts, grade=grade, route=route, arts=arts,
                srcs=srcs, recent=recent)


@st.cache_resource(show_spinner=False)
def get_app(model):
    import agent
    return agent.build(model)


def certainties(used):
    found = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "certainty" and isinstance(v, str):
                    found.add(v)
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(used or {})
    return found


def chip(text, color):
    return '<span class="chip" style="background:%s">%s</span>' % (color, text)


def render_why(s):
    """★근거를 «파이프라인 순서»로 — ①→②→③→④.

    2차에는 2열 그리드였는데 «흐름»이 안 보였다.
    요건이 요구하는 넷이 여기 다 있다.
    """
    used = s.get("used") or {}
    guard = s.get("guard") or {}
    ctx = s.get("context") or ""
    rt = s.get("route", "—")

    st.markdown('<div class="tl">', unsafe_allow_html=True)
    st.markdown('<p class="step"><span class="n">①</span>분류 &nbsp; '
                '<b>%s</b> (%s) · 확신도 %.2f</p>'
                % (rt, ROUTE_KO.get(rt, rt), s.get("conf", 0)),
                unsafe_allow_html=True)
    tools = ", ".join("<code>%s</code>" % t for t in used) if used else "(없음)"
    st.markdown('<p class="step"><span class="n">②</span>조회 &nbsp; %s</p>'
                % tools, unsafe_allow_html=True)
    st.markdown('<p class="step"><span class="n">③</span>근거 &nbsp; '
                '이 카테고리 몫 <b>%d자</b> <span style="color:#9ca3af">'
                '(문서 전체가 아니라)</span></p>' % len(ctx), unsafe_allow_html=True)
    ok = guard.get("ok")
    vtxt = ("통과 — 위반 없음" if ok else
            " · ".join(v["type"] for v in guard.get("violations", [])))
    st.markdown('<p class="step"><span class="n">④</span>검증 &nbsp; '
                '<b style="color:%s">%s</b></p>'
                % ("#1B5E20" if ok else "#B71C1C", vtxt), unsafe_allow_html=True)
    unchecked = guard.get("unchecked_nums") or []
    if unchecked:
        st.markdown('<p class="note">※ 판정하지 못한 수치: %s — 지식원이 영어라 '
                    '한국어 환산값은 문자열로 대조할 수 없습니다</p>'
                    % ", ".join(unchecked), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("근거로 쓴 문서 부분 (%d자)" % len(ctx)):
        st.markdown(ctx or "(없음)")
    with st.expander("도구가 돌려준 원본"):
        st.json(used)


def render_answer(s):
    # ★걸린 시간을 «말풍선 안»에 둔다 — 밖에 두면 rerun 뒤 사라진다(실측).
    #   Perplexity 의 「조사 완료 1초」에서 가져온 것인데, 우리는 20~60초라
    #   «얼마나 걸렸는지»가 더 중요하다.
    if s.get("_sec"):
        st.markdown('<p class="note">조사 완료 %.1f초</p>' % s["_sec"],
                    unsafe_allow_html=True)
    dec = s.get("decision", "CONTINUE")
    if dec in DECISION:
        c, bg, why, fix = DECISION[dec]
        st.markdown('<div class="cert-wrap" style="--c:%s;--bg:%s">%s'
                    '<span style="color:#374151;font-size:.83rem">%s</span></div>'
                    % (c, bg, chip(dec, c), why), unsafe_allow_html=True)
        st.write(s.get("answer") or "")
        st.markdown('<p class="note">※ %s</p>' % fix, unsafe_allow_html=True)
    else:
        certs = sorted(certainties(s.get("used")))
        if certs:
            c0, bg0, _ = CERT.get(certs[0], ("#6b7280", "#f3f4f6", ""))
            chips = "".join(chip("[%s]" % x, CERT.get(x, ("#6b7280",))[0])
                            for x in certs)
            st.markdown('<div class="cert-wrap" style="--c:%s;--bg:%s">%s'
                        '<span style="color:#374151;font-size:.83rem">'
                        '근거의 확실성</span></div>' % (c0, bg0, chips),
                        unsafe_allow_html=True)
        st.write(s.get("answer") or "")
        if "신설" in certs:
            st.markdown('<p class="note">🔴 <b>[신설]이 섞여 있습니다</b> — '
                        '최근 72시간 발표라 아직 다른 연구진이 확인하지 '
                        '않았습니다.</p>', unsafe_allow_html=True)
    with st.expander("왜 이렇게 답했나", expanded=OPEN_WHY):
        render_why(s)


# ─────────────────────────────────────────────────────────
S = load_sources()

with st.sidebar:
    st.subheader("설정")
    model = st.selectbox("모델", ["gpt-5.6-terra", "qwen2.5:7b",
                                 "qwen2.5:3b", "qwen3.5:2b"],
                         label_visibility="collapsed")
    st.caption("같은 파이프라인에 **모델만** 갈아 끼웁니다")
    if st.button("대화 지우기", use_container_width=True):
        st.session_state.msgs = []
        st.rerun()

    st.divider()
    # ★지식원 — 「무엇을 아는가」를 등급별로. Perplexity 의 「출처 N」 자리다.
    st.subheader("지식원")
    st.markdown("**기준 사실 카드 %d장**" % len(S["facts"]))
    st.markdown(" ".join(chip("[%s] %d" % (k, S["grade"][k]), CERT[k][0])
                         for k in ("정설", "추정", "논쟁") if k in S["grade"]),
                unsafe_allow_html=True)
    st.markdown('<p class="note">%s</p>'
                % " · ".join("%s %d" % (ROUTE_KO.get(k, k), v)
                             for k, v in sorted(S["route"].items())),
                unsafe_allow_html=True)
    with st.expander("무엇을 아는지 보기"):
        for f in S["facts"]:
            st.markdown('<div class="srcrow">%s <b>%s</b> '
                        '<span style="color:#9ca3af">%s</span></div>'
                        % (chip(f["certainty"], CERT[f["certainty"]][0]),
                           f["topic"], ROUTE_KO.get(f["route"], f["route"])),
                        unsafe_allow_html=True)

    st.markdown("**최근 발표 %d건**" % len(S["arts"]))
    st.markdown('<p class="note">72시간 이내 · 소스 %d곳 · 전부 [신설]</p>'
                % len(S["srcs"]), unsafe_allow_html=True)
    with st.expander("들어온 목록 보기"):
        for a in S["arts"][:40]:
            st.markdown('<div class="srcrow"><b>%s</b><br>'
                        '<span style="color:#9ca3af">%s · %s</span></div>'
                        % (a["title"][:70], a.get("source", "?"),
                           (a.get("published") or "")[:10]),
                        unsafe_allow_html=True)

    st.divider()
    st.subheader("확실성 등급")
    for k, (c, bg, desc) in CERT.items():
        st.markdown('%s<span style="font-size:.8rem">%s</span>'
                    % (chip("[%s]" % k, c), desc), unsafe_allow_html=True)

st.title("🔭 발견 데스크")
st.caption("우주 · 고고학 · 고생물 질문에 **확실성 등급과 함께** 답합니다. "
           "「6,600만 년 전」은 [추정]이고, 「지난주 발표」는 [신설]입니다.")

if "msgs" not in st.session_state:
    st.session_state.msgs = []
    st.session_state.queue = _seed_queue()

demo_name = _qp.get("demo")
if demo_name:
    scene = (load_demo().get("scenes") or {}).get(demo_name)
    if scene:
        st.info("**녹화된 대화입니다** — %s\n\n지금 모델을 부르지 않고 "
                "미리 돌려 둔 결과를 그립니다(`make_demo.py`)." % scene["note"])
        for t in scene["turns"]:
            with st.chat_message("user"):
                st.write(t["question"])
            with st.chat_message("assistant"):
                render_answer(t)

pending = None
if st.session_state.get("queue"):
    pending = st.session_state.queue.pop(0)

# ★시작 화면 — 대화가 비었을 때만. 고정 예시 넷은 «어제도 오늘도 같은 화면»이라
#   죽은 데모가 된다. 최근 72시간 발표에서 «지금 들어온 것»을 함께 보인다.
if not st.session_state.msgs and not pending and not demo_name:
    st.markdown("##### 이렇게 물어보세요 — 각각 다른 경로를 지납니다")
    EX = [("티라노사우루스에 깃털이 있었나요", "논쟁 — 양쪽을 말하는지"),
          ("방사성 탄소 연대측정이 뭔가요", "정설 — 한계까지 말하는지"),
          ("한국이 최근 발사한 위성의 궤도 고도는요", "넘기기 — 모른다고 하는지"),
          ("제 별자리 운세를 봐주세요", "거절 — 범위 밖")]
    for i, (q, note) in enumerate(EX):
        c1, c2 = st.columns([3, 2])
        if c1.button(q, key="ex%d" % i, use_container_width=True):
            pending = q
        c2.markdown('<p class="note">%s</p>' % note, unsafe_allow_html=True)

    st.markdown("##### 지금 들어온 발표 — 이걸 물으면 **[신설]** 경로를 지납니다")
    for r in ("SPACE", "ARCHAEO", "PALEO"):
        arts = S["recent"].get(r) or []
        if not arts:
            continue
        a = arts[0]
        c1, c2 = st.columns([3, 2])
        qr = "최근에 발표된 %s 연구가 있나요" % ROUTE_KO.get(r, r)
        if c1.button(qr, key="rc%s" % r, use_container_width=True):
            pending = qr
        c2.markdown('<p class="note">%s… <br><span style="color:#b91c1c">%s</span></p>'
                    % (a["title"][:44], a.get("source", "")),
                    unsafe_allow_html=True)
    st.caption("이어서 「그럼 언제 밝혀졌나요」처럼 **되물어도** 됩니다 — 앞 대화를 기억합니다.")

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        if m["role"] == "user":
            st.write(m["content"])
        else:
            render_answer(m["state"])

typed = st.chat_input("질문을 입력하세요 — 이어서 되물어도 됩니다")
q = typed or pending

if q:
    with st.chat_message("user"):
        st.write(q)
    history = [(m["content"], n["state"].get("answer", ""))
               for m, n in zip(st.session_state.msgs[::2],
                               st.session_state.msgs[1::2])]
    app = get_app(model)
    with st.chat_message("assistant"):
        # ★단계 + «시간» — Perplexity 의 「조사 완료 1초」에서 가져왔다.
        #   우리는 20~60초가 걸려서 «더» 필요하다. 빈 화면은 고장처럼 보인다.
        import time
        t0 = time.perf_counter()
        with st.spinner("① 분류 → ② 근거 조립 → ③ 답변 → ④ 검증 … "
                        "모델을 부르는 중입니다"):
            s = app.invoke({"question": q, "history": history})
        s["_sec"] = time.perf_counter() - t0
        render_answer(s)
    st.session_state.msgs.append({"role": "user", "content": q})
    st.session_state.msgs.append({"role": "assistant", "state": s})
    if pending:
        st.rerun()
