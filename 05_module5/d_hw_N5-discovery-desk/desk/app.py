# -*- coding: utf-8 -*-
"""★데모 — 「발견 데스크」 대화창.

두 요건이 «서로 다른 것»을 요구한다
  LMS   답변과 함께 «호출한 도구 · 근거로 쓴 문서 부분 · 검증 결과»를 보여 준다
  노션  실제로 사용자가 «대화»를 실험해볼 수 있는 웹 데모

1차에는 LMS 만 보고 만들었더니 «계기판»이 됐다 — 확신도·도구·근거가
전부 상시 노출이고 질문은 한 번만 할 수 있었다. 챗봇이 아니라 보고서였다.

⇒ 둘을 이렇게 화해시킨다
   · 겉은 «대화» — 말풍선, 이어 묻기, 앞 대화를 기억
   · 근거는 «접어서» 답변 밑에 — 「왜 이렇게 답했나」를 펴면 넷이 다 있다
   보여 주기를 포기하지 않으면서 대화를 막지도 않는다.

★이 데스크만의 것 — 확실성 등급
  같은 문장도 [정설]에 근거했는지 [신설]에 근거했는지에 따라 믿을 정도가 다르다.
  그래서 등급은 «접지 않고» 답변 바로 위에 둔다.

  streamlit run app.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import streamlit as st  # noqa: E402

st.set_page_config(page_title="발견 데스크", page_icon="🔭",
                   layout="centered", initial_sidebar_state="expanded")

# ─────────────────────────────────────────────────────────
# 확실성 등급 — «색만»으로 구분하지 않는다. 이름을 같이 쓴다.
#   (색각 이상이면 색만으로는 못 읽는다)
# ─────────────────────────────────────────────────────────
CERT = {
    "정설": ("#2E7D32", "널리 합의된 것"),
    "추정": ("#F9A825", "오차가 있는 것"),
    "논쟁": ("#EF6C00", "학계가 갈리는 것"),
    "신설": ("#C62828", "최근 발표 — 아직 검증 안 됨"),
    "최근": ("#1565C0", "최근 발표"),
}
DECISION = {
    "REFUSE":   ("다루지 않는 주제", "경계가 새면 라우터를 고친다"),
    "ESCALATE": ("다루는 주제인데 자료에 없음", "잦아지면 지식원을 늘린다"),
    "ASK":      ("후보가 여럿이라 되물음", "잦아지면 질문을 좁히게 유도한다"),
}
EXAMPLES = [
    ("티라노사우루스에 깃털이 있었나요", "논쟁 — 양쪽을 말하는지"),
    ("최근에 발표된 공룡 화석 연구가 있나요", "신설 — 검증 전이라 말하는지"),
    ("한국이 최근 발사한 위성의 궤도 고도는요", "넘기기 — 모른다고 하는지"),
    ("제 별자리 운세를 봐주세요", "거절 — 범위 밖"),
]

st.markdown("""
<style>
  .cert-row { margin: 0 0 .5rem 0; }
  .cert-chip { display:inline-block; padding:2px 10px; border-radius:11px;
               font-size:.78rem; font-weight:600; color:#fff; margin-right:6px; }
  .desk-note { color:#6b7280; font-size:.82rem; margin:.35rem 0 0 0; }
</style>
""", unsafe_allow_html=True)


# ★URL 로 대화를 미리 채운다 — 캡처와 «공유»를 위해.
#   ?q=질문&q=이어질문   순서대로 실제 파이프라인을 태운다(멀티턴 시연)
#   ?open=1             「왜 이렇게 답했나」를 펼친 채로 그린다
#   캡처를 손으로 클릭해 만들면 «다시 못 만든다». URL 이면 누구나 같은 화면을 얻는다.
_qp = st.query_params
OPEN_WHY = _qp.get("open") in ("1", "true")


def _seed_queue():
    try:
        qs = _qp.get_all("q")
    except Exception:
        v = _qp.get("q")
        qs = [v] if isinstance(v, str) else list(v or [])
    return [x for x in qs if x]


# ★데모(녹화) 모드 — ?demo=<장면이름>
#   미리 돌려 둔 대화를 그린다. 키가 없어도 화면이 돈다.
#   ⚠ 실시간인 «척하지 않는다» — 화면에 녹화임을 적는다.
DEMO_FILE = HERE / "demo_runs.json"


@st.cache_data
def load_demo():
    import json
    if not DEMO_FILE.exists():
        return {}
    return json.loads(DEMO_FILE.read_text(encoding="utf-8"))


@st.cache_resource(show_spinner="파이프라인을 세우는 중…")
def get_app(model):
    import agent
    return agent.build(model)


def certainties(used):
    """조회 결과 어디에 있든 certainty 를 긁어 온다(깊이를 모른다)."""
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


def render_why(s):
    """★「왜 이렇게 답했나」 — 요건이 요구하는 넷을 여기 모은다."""
    used = s.get("used") or {}
    guard = s.get("guard") or {}
    c1, c2 = st.columns(2)
    with c1:
        st.caption("① 분류")
        st.write("**%s**  ·  확신도 %.2f" % (s.get("route", "—"), s.get("conf", 0)))
        st.caption("② 호출한 도구")
        if used:
            for name in used:
                st.write("`%s`" % name)
        else:
            st.write("(없음)")
    with c2:
        st.caption("④ 검증")
        if guard.get("ok"):
            st.success("통과 — 위반 없음")
        else:
            for v in guard.get("violations", []):
                st.error("**%s** — %s" % (v["type"], v["detail"]))
        st.caption("출처 없는 수치 · 확실성 단정 · 답하면 안 되는 것")

    ctx = s.get("context") or ""
    with st.expander("③ 근거로 쓴 문서 부분 — %d자 (전체가 아니라 이 카테고리 몫만)"
                     % len(ctx)):
        st.markdown(ctx or "(없음)")
    with st.expander("도구가 돌려준 원본"):
        st.json(used)


def render_answer(s):
    """assistant 말풍선 하나를 그린다."""
    dec = s.get("decision", "CONTINUE")
    if dec in DECISION:
        why, fix = DECISION[dec]
        st.markdown('<div class="cert-row"><span class="cert-chip" '
                    'style="background:#6b7280">%s</span>%s</div>'
                    % (dec, why), unsafe_allow_html=True)
        st.write(s.get("answer") or "")
        st.markdown('<p class="desk-note">%s</p>' % fix, unsafe_allow_html=True)
    else:
        certs = certainties(s.get("used"))
        if certs:
            chips = "".join(
                '<span class="cert-chip" style="background:%s">[%s]</span>'
                % (CERT.get(c, ("#6b7280", ""))[0], c) for c in sorted(certs))
            st.markdown('<div class="cert-row">%s<span style="color:#6b7280;'
                        'font-size:.82rem">근거의 확실성</span></div>' % chips,
                        unsafe_allow_html=True)
        st.write(s.get("answer") or "")
        if "신설" in certs:
            st.warning("**[신설]이 섞여 있습니다** — 최근 72시간 발표라 "
                       "아직 다른 연구진이 확인하지 않았습니다.")
    with st.expander("왜 이렇게 답했나", expanded=OPEN_WHY):
        render_why(s)


# ─────────────────────────────────────────────────────────
with st.sidebar:
    st.subheader("설정")
    model = st.selectbox("모델", ["gpt-5.6-terra", "qwen2.5:7b",
                                 "qwen2.5:3b", "qwen3.5:2b"])
    st.caption("같은 파이프라인에 **모델만** 갈아 끼웁니다")
    if st.button("대화 지우기", use_container_width=True):
        st.session_state.msgs = []
        st.rerun()
    st.divider()
    st.subheader("확실성 등급")
    for k, (color, desc) in CERT.items():
        st.markdown('<span class="cert-chip" style="background:%s">[%s]</span>'
                    '<span style="font-size:.82rem">%s</span>' % (color, k, desc),
                    unsafe_allow_html=True)
    st.divider()
    st.caption("지식원 — 기준 사실 카드(정설·추정·논쟁) + 최근 72시간 발표(신설)")

st.title("🔭 발견 데스크")
st.caption("우주 · 고고학 · 고생물 질문에 **확실성 등급과 함께** 답합니다. "
           "「6,600만 년 전」은 [추정]이고, 「지난주 발표」는 [신설]입니다.")

# ★녹화 재생 — 파이프라인을 부르지 않고 저장된 결과를 그린다
demo_name = _qp.get("demo")
if demo_name:
    scene = (load_demo().get("scenes") or {}).get(demo_name)
    if scene:
        st.info("**녹화된 대화입니다** — %s\n\n"
                "지금 모델을 부르지 않고 미리 돌려 둔 결과를 그립니다"
                "(`make_demo.py`). 직접 물어보려면 아래 입력창을 쓰세요."
                % scene["note"])
        for t in scene["turns"]:
            with st.chat_message("user"):
                st.write(t["question"])
            with st.chat_message("assistant"):
                render_answer(t)
    else:
        st.warning("그런 장면이 없습니다: %s" % demo_name)

if "msgs" not in st.session_state:
    st.session_state.msgs = []
    st.session_state.queue = _seed_queue()

pending = None
if st.session_state.get("queue"):
    pending = st.session_state.queue.pop(0)

# ★시작 예시는 «대화가 비었을 때만» 보인다 — 늘 떠 있으면 폼처럼 보인다
if not st.session_state.msgs and not pending and not demo_name:
    st.markdown("**이렇게 물어보세요** — 각각 다른 경로를 지납니다")
    for i, (q, note) in enumerate(EXAMPLES):
        c1, c2 = st.columns([3, 2])
        if c1.button(q, key="ex%d" % i, use_container_width=True):
            pending = q
        c2.markdown('<p class="desk-note">%s</p>' % note, unsafe_allow_html=True)
    st.caption("이어서 「그럼 언제 밝혀졌나요」처럼 **되물어도** 됩니다 — 앞 대화를 기억합니다.")

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        if m["role"] == "user":
            st.write(m["content"])
        else:
            render_answer(m["state"])

typed = st.chat_input("질문을 입력하세요")
q = typed or pending

if q:
    with st.chat_message("user"):
        st.write(q)
    # ★이력은 «앞선 턴»만 — 지금 질문은 아직 넣지 않는다
    history = [(m["content"], n["state"].get("answer", ""))
               for m, n in zip(st.session_state.msgs[::2],
                               st.session_state.msgs[1::2])]
    app = get_app(model)
    with st.chat_message("assistant"):
        with st.spinner("① 분류 → ② 근거 조립 → ③ 답변 → ④ 검증"):
            s = app.invoke({"question": q, "history": history})
        render_answer(s)
    st.session_state.msgs.append({"role": "user", "content": q})
    st.session_state.msgs.append({"role": "assistant", "state": s})
    if pending:
        st.rerun()
