# -*- coding: utf-8 -*-
"""웹 데모 — 배정 도면.

  streamlit run app.py
  ?q=질문&axis=문화권&auto=1

★요건: 「보고서와 함께 절마다 누가 무엇을 읽고 무엇을 썼는지를 보여 줍니다.
       숫자만 보여 주는 화면은 이 프로젝트의 요점을 놓칩니다.」

★구조 — DESIGN.md 「측량 도면」
  탭도 사이드바 지표판도 없다. 한 화면이 위에서 아래로 이어진다.
      머리      질문과 규모가 «한 문단»에
      ★도면     문서 42건 → 조사관 4명. 겹침·몰림·버림이 «보인다»
      판독      도면에서 읽어야 할 것을 «문장»으로 (⛔스탯 배너 줄 대신)
      절 원고   카드가 아니라 «본문 조판». 근거에 강조색
      격리 단면 코디가 본 글자 ÷ 팀이 읽은 글자

  ⛔번호 단계(①②③) 없음 — ★도면이 과정 자체다
  ⛔동일 카드 반복 없음 — 블록마다 모양이 다르다
"""
import base64
import io
import json
import os
import re
import time

import streamlit as st

import graph as agent
import compare
import mapviz
import ui
from metrics import 지표사전, 절판정

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(io.open(os.path.join(HERE, "config.json"), encoding="utf-8"))
QS = json.load(io.open(os.path.join(HERE, "data/questions.json"),
                       encoding="utf-8"))

st.set_page_config(page_title="딥리서처 · 세계 신화", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(ui.css(), unsafe_allow_html=True)

_qp = st.query_params
if not st.session_state.get("_from_url") and (_qp.get("q") or _qp.get("auto")):
    if _qp.get("q"):
        st.session_state["_url_q"] = _qp["q"]
    if _qp.get("axis"):
        st.session_state["_url_axis"] = _qp["axis"]
    st.session_state["_auto"] = _qp.get("auto") in ("1", "true", "yes")
    st.session_state["_from_url"] = True

C = ui.C
H = lambda s: st.markdown(s, unsafe_allow_html=True)      # noqa: E731


def esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def 강조(t):
    """근거(«…»)에 강조색. ★유채색을 여기에만 쓴다."""
    return re.sub("«([^»\n]{1,40})»", '<span class="q">«\\1»</span>', esc(t))


def 괘선(제목, 설명="", 캡션="", 번호=None):
    """★번호를 받으면 붙인다 — 머리의 사용법과 «눈으로 이어지게»."""
    H('<div class="rule">%s<h2>%s%s</h2>%s</div>'
      % ('<div class="cap">%s</div>' % esc(캡션) if 캡션 else "",
         ('<span style="font-family:IBM Plex Mono,monospace;color:%s;'
          'margin-right:10px">%d</span>' % (C["mark"], 번호)) if 번호 else "",
         esc(제목),
         '<div class="sub">%s</div>' % 설명 if 설명 else ""))


# ══ 머리 — ⛔가운데 정렬·배지 없음. 수치를 «문장 안»에 ═══════════════
co = CFG["_코퍼스"]
_hero = os.path.join(HERE, "docs/hero.jpg")
_hm = {}
if os.path.exists(os.path.join(HERE, "docs/hero.json")):
    _hm = json.load(io.open(os.path.join(HERE, "docs/hero.json"),
                            encoding="utf-8"))
if os.path.exists(_hero):
    # ★그림을 data URI 로 박는다 — Streamlit 은 로컬 파일을 <img> 로 못 준다
    _b64 = base64.b64encode(open(_hero, "rb").read()).decode()
    H('<div class="plate">'
      '<img src="data:image/jpeg;base64,%s" alt="사자의 서 — 후네페르 파피루스. '
      '고대 이집트의 심판 장면">'
      '<div class="scrim"></div><div class="on">'
      '<h1>딥리서처 · 세계 신화</h1>'
      '<div class="sub">한 번에 못 읽는 분량을 <b>넷이 나눠 읽고 한 편으로 '
      '합치는</b> 시스템입니다. 코퍼스는 위키백과 <b>%d건 %s자</b>로 모델의 창 '
      '128k 토큰의 <b>%s</b>라, 전부 넣는 길이 아예 없습니다.</div></div>'
      '<div class="src">%s<br>퍼블릭 도메인 · 위키미디어 공용</div></div>'
      % (_b64, co["문서"], format(co["글자"], ","), co["창대비"].split()[0],
         esc(_hm.get("파일", "").replace("File:", "").replace(".jpg", ""))))
else:
    H('<div class="hd"><h1>딥리서처 · 세계 신화</h1>'
      '<div class="meta">한 번에 못 읽는 분량을 <b>넷이 나눠 읽고 한 편으로 '
      '합치는</b> 시스템입니다. 코퍼스 <span class="num">%d</span>건 '
      '<span class="num">%s</span>자 = 창의 <b>%s</b>.</div></div>'
      % (co["문서"], format(co["글자"], ","), co["창대비"].split()[0]))

# ★표제 도면 — ⛔장식 이미지가 아니라 «코퍼스 그 자체».
#   막대 하나가 실제 문서이고 길이가 실제 글자 수다.
H('<div class="hero">%s</div>' % mapviz.표제(agent.DOCS, agent.설정["절수"]))

# ★사용법 — 처음 온 사람은 아래 칸들이 «왜» 있는지 모른다
H('<div class="how">'
  '<div class="s"><div class="n">1</div><div>'
  '<div class="t">질문을 고른다</div>'
  '<div class="d">한 건으로 답이 나오는 질문은 나눌 이유가 없습니다. '
  '고르면 아래 네 칸이 «이 질문이 나눌 만한지»를 검사합니다.</div>'
  '<div class="go">↓ 아래 <b style="color:%s">1</b> 질문</div></div></div>'
  '<div class="s"><div class="n">2</div><div>'
  '<div class="t">축과 규모를 정한다</div>'
  '<div class="d">절을 <b>무엇을 기준으로</b> 나눌지가 첫 결정입니다. '
  '장치를 꺼 보면 무엇이 먼저 무너지는지 보입니다.</div>'
  '<div class="go">↓ 아래 <b style="color:%s">2</b> 절을 나누는 축 · 규모와 장치'
  '</div></div></div>'
  '<div class="s"><div class="n">3</div><div>'
  '<div class="t">도면을 읽는다</div>'
  '<div class="d">겹친 선은 중복, 몰린 선은 편중, 흐린 선은 읽고 안 쓴 것입니다. '
  '두 번 돌리면 회차를 <b>나란히</b> 견줄 수 있습니다.</div>'
  '<div class="go">↓ <b style="color:%s">조사</b>를 누른 뒤 '
  '<b style="color:%s">3</b> 배정 도면</div></div></div>'
  '</div>' % (C["mark"], C["mark"], C["mark"], C["mark"]))

# ══ 조작부 — ⛔접어 두지 않는다. 핵심 조작이 «보여야» 한다 ═══════
예시 = [QS["주질문"]["text"]] + [q["text"] for q in QS["보조질문"]]
_uq = st.session_state.get("_url_q")

H('<div class="bar"><div class="no">1</div>'
  '<div class="lbl">질문</div>'
  '<div class="hint">무엇을 조사할지 고릅니다. 직접 적어도 됩니다. '
  '고르면 아래에 <b>이 질문이 나눌 만한지</b>가 네 칸으로 검사됩니다.</div></div>')
c1, c2 = st.columns([5, 1])
with c1:
    고른질문 = st.selectbox("질문", 예시 + ["직접 입력"],
                        index=예시.index(_uq) if _uq in 예시 else 0,
                        label_visibility="collapsed")
    q = (st.text_input("질문", "", placeholder="물어볼 것을 적으세요",
                       label_visibility="collapsed")
         if 고른질문 == "직접 입력" else 고른질문)
with c2:
    돌린다 = st.button("조사", type="primary", use_container_width=True)

# ── 이 질문이 왜 나눌 만한가 — ★네 조건을 «칸»으로 ────────────────
_docs, _links = co["문서"], co["내부링크"]
_조건 = [("한 질문에 여러 자료가 필요한가", "네 축이 각각 여러 문화권을 요구"),
       ("자료 전체가 모델 창에 안 들어가는가", "%s자 = 창의 %s"
        % (format(co["글자"], ","), co["창대비"].split()[0])),
       ("자료끼리 서로 가리키는가", "내부 링크 %d개" % _links),
       ("산출물이 장문인가", "네 절 + 머리말·맺음말")]
H('<div class="chk">' + "".join(
    '<div class="c"><div class="q">%s</div><div class="a">%s</div></div>'
    % (a, b) for a, b in _조건) + '</div>')
H('<div class="note">요건이 요구한 「주제 고르기」 4조건입니다. '
  '나눌 필요 <b>없는</b> 질문도 적어 뒀습니다 — %s. '
  '이런 건 혼자가 더 싸게 이깁니다.</div>'
  % " · ".join("«%s»" % x["text"]
               for x in QS["⛔나눌 필요 없음 — 대조용 반례"]))

# ── ★축 — 이 프로젝트의 핵심 조작. 맨 앞에 둔다 ──────────────────
H('<div class="bar"><div class="no">2</div>'
  '<div class="lbl">절을 나누는 축</div>'
  '<div class="hint">목차의 축이 곧 분업이고, 분업이 곧 결과물의 모양입니다. '
  '코디에게 <b>이 축으로 나눠라</b>를 직접 말합니다.</div></div>')
a1, a2 = st.columns([1.1, 2])
with a1:
    _축들 = ["주제", "문화권", "직접 입력"]
    축이름 = st.radio("축", _축들, horizontal=True, label_visibility="collapsed",
                   index=1 if str(st.session_state.get("_url_axis", ""))
                   .startswith("문화권") else 0)
with a2:
    if 축이름 == "직접 입력":
        _nm = st.text_input("축 이름", "", placeholder="예: 시대 / 전파 경로 / 학설",
                            label_visibility="collapsed")
        _ex = st.text_input("절 예시", "",
                            placeholder="쉼표로 — 예: 청동기, 철기, 고전기, 중세",
                            label_visibility="collapsed")
        축지시 = {"이름": _nm, "예": _ex} if _nm and _ex else None
        if not 축지시:
            st.caption("★축 이름과 절 예시를 둘 다 적어야 코디에게 전달됩니다. "
                       "비우면 코디가 스스로 정합니다.")
    else:
        축지시 = CFG["_축지시"][축이름]
        # ⚠st.caption 은 마크다운을 쓰는데 «축 이름»에 ** 를 붙이면
        #   이름 자체에 별이 섞여 보였다. ★내용이 강조 문법과 겹치면 안 쓴다.
        st.caption("코디에게 보낼 지시 — 「%s 를 기준으로 절을 나누세요. "
                   "예: %s」" % (축지시["이름"], 축지시["예"]))

# ── 설정 — ⛔접지 않는다. 지금 값이 «보여야» 한다 ─────────────────
H('<div class="bar"><div class="no">2</div>'
  '<div class="lbl">규모와 장치</div>'
  '<div class="hint">몇 명이 몇 건씩 읽을지, 그리고 네 장치를 켤지 끌지. '
  '<b>끄고 다시 돌리면</b> 그 장치가 실제로 값을 하는지 보입니다 — '
  '다만 잡음이 커서 한 번으로는 판단할 수 없습니다.</div></div>')
b1, b2, b3 = st.columns([1, 1, 1.6])
with b1:
    절수 = st.slider("절수 — 몇 명이 나눠 맡나", 2, 6, agent.설정["절수"])
with b2:
    예산 = st.slider("깊이 — 한 명이 몇 건 읽나", 1, 6, agent.설정["예산"])
with b3:
    H('<div class="mini">장치 끄기 — 끄면 <b>무엇이 먼저 무너지는지</b> 보세요</div>')
    d1, d2 = st.columns(2)
    with d1:
        배정 = st.checkbox("배정", agent.설정["배정"],
                         help="코디가 시작 문서를 정해 준다. 끄면 편중·읽고안쓴이 뛸 것")
        역할 = st.checkbox("역할", agent.설정["역할"],
                         help="담당 이름을 준다. 끄면 절이 비슷해질 것")
    with d2:
        구역 = st.checkbox("구역", agent.설정["구역"],
                         help="남의 구역을 알려 준다. 끄면 중복률이 먼저 뛸 것")
        재위임 = st.checkbox("재위임", agent.설정["재위임"],
                          help="부족한 절만 다시. 끄면 근거율이 내려갈 것")

_끈것 = [n for n, v in (("배정", 배정), ("구역", 구역), ("역할", 역할),
                     ("재위임", 재위임)) if not v]
H('<div class="sum">읽기 총량 <b class="num">%d건</b> '
  '= 절수 <span class="num">%d</span> × 깊이 <span class="num">%d</span>. '
  '대조군도 같은 값을 받습니다. 장치는 <b>%s</b>. 축은 <b>%s</b>. '
  '1회 약 <span class="num">$%.3f</span> · <span class="num">%d</span>초쯤.</div>'
  % (절수 * 예산, 절수, 예산,
     "전부 켬" if not _끈것 else " · ".join("%s 끔" % x for x in _끈것),
     (축지시["이름"] if 축지시 else "코디가 정함"),
     0.003 * 절수 * 예산 / 12 * 4, 5 * 절수))

if 돌린다 or st.session_state.pop("_auto", False):
    agent.설정.update({"절수": 절수, "예산": 예산, "배정": 배정,
                      "구역": 구역, "역할": 역할, "재위임": 재위임})
    # ★축 — 역할 «명단»만 바꿔서는 축이 안 바뀐다(실측). 프롬프트도 바꾼다.
    agent.ROSTER = (agent.ROSTER_ALT if 축이름 == "문화권"
                    else CFG["_역할명단"]["★주제 축(A) — 기본"])
    agent.설정.pop("축지시", None)
    if 축지시:
        agent.설정["축지시"] = 축지시
    # ★C — 과정을 보인다. spinner 하나로 20초는 «어디쯤인지» 모른다.
    with st.status("조사 중", expanded=True) as 상태:
        st.write("기획 — 카드 %d건을 보고 목차를 짭니다" % len(agent.DOCS))
        t0 = time.time()
        st.write("배치 — 조사관 %d명을 동시에 파견합니다 "
                 "(각자 %d건씩 · 총 %d건)" % (절수, 예산, 절수 * 예산))
        _st = agent.run(q, quiet=True)
        st.write("종합 — %d절을 이어 붙였습니다 (%d자)"
                 % (len(_st["sections"]), len(_st["report"])))
        상태.update(label="조사 끝 · %.1f초" % (time.time() - t0),
                  state="complete", expanded=False)
    _st["sec"] = round(time.time() - t0, 1)
    _st["설정"] = dict(agent.설정)
    _st["축"] = (축지시["이름"] if 축지시 else "코디가 정함")
    # ★A — 회차를 «쌓는다». 전에는 한 칸이라 다시 돌리면 앞이 덮였다.
    st.session_state.setdefault("회차", []).append(_st)
    st.session_state["st"] = _st
    st.session_state["sec"] = _st["sec"]
    # ★기록 — 데모 실행이 아무 데도 안 남던 것을 고친다
    keep = {k: v for k, v in _st.items() if k != "_배차"}
    keep["ts"] = time.strftime("%Y%m%d-%H%M%S")
    keep["from"] = "app"
    io.open(os.path.join(HERE, "output/runs.jsonl"), "a",
            encoding="utf-8", newline="").write(
        json.dumps(keep, ensure_ascii=False, default=str) + "\n")

회차 = st.session_state.get("회차", [])
S = st.session_state.get("st")
if not S:
    괘선("아직 도면이 비어 있습니다",
       "질문을 고르고 <b>조사</b>를 누르면 문서 %d건이 조사관에게 어떻게 "
       "나뉘는지가 이 자리에 그려집니다. 선이 겹치면 중복이고, 한 문서로 "
       "몰리면 편중이고, 흐린 선은 읽고 쓰지 않은 것입니다.<br><br>"
       "미리 적어 둡니다 — 같은 설정을 12번 돌려 잰 잡음이 "
       "<b class='num'>15.0%%p</b>이고 장치를 바꾼 조건들의 차이는 "
       "<b class='num'>11.7%%p</b>입니다. <b>잡음이 차이보다 큽니다.</b> "
       "한 번 돌린 숫자로 판단하지 마세요." % co["문서"])
    st.stop()

m = S["metrics"]

# ══ ★A 회차 — 쌓아 두고 «둘을 골라» 견준다 ═══════════════════════
if len(회차) > 1:
    괘선("돌린 회차 %d번" % len(회차),
       "이 프로젝트의 결론은 전부 「A 대 B」입니다 — 팀 대 혼자, 장치 켬 대 끔, "
       "축 주제 대 문화권. 그래서 회차를 <b>덮지 않고 쌓습니다</b>. "
       "둘을 고르면 아래에 차이가 나옵니다.")
    요약들 = [compare.요약(x) for x in 회차]
    st.table([{"#": i + 1, "설정": r["라벨"], "축": r["축"],
               "근거율": "%.1f%%" % (r["근거율"] * 100),
               "편중": "%.1f%%" % (r["편중"] * 100),
               "중복률": "%.1f%%" % (r["중복률"] * 100),
               "읽은 문서": r["읽은문서수"], "경보": r["경보"],
               "초": r["초"]} for i, r in enumerate(요약들)])
    cA, cB = st.columns(2)
    with cA:
        iA = st.selectbox("견줄 회차 A", range(1, len(회차) + 1),
                          index=max(0, len(회차) - 2),
                          format_func=lambda i: "%d · %s" % (i, 요약들[i - 1]["라벨"]))
    with cB:
        iB = st.selectbox("견줄 회차 B", range(1, len(회차) + 1),
                          index=len(회차) - 1,
                          format_func=lambda i: "%d · %s" % (i, 요약들[i - 1]["라벨"]))
    if iA != iB:
        행, 잡음폭 = compare.견줌표(요약들[iA - 1], 요약들[iB - 1], C)
        H('<div class="cut">' + "".join(
            '<div class="row"><span class="k">%s</span>'
            '<span class="v num">%.1f%%</span>'
            '<span class="n">→</span><span class="v num">%.1f%%</span>'
            '<span class="n">차이 <b class="num">%+.1f%%p</b> · %s</span></div>'
            % (k, a * 100, b * 100, d * 100, 판)
            for k, a, b, d, 판 in 행) + '</div>')
        if 잡음폭:
            st.caption("같은 설정을 여러 번 돌렸을 때의 흩어짐이 "
                       "%.1f%%p 입니다. 그보다 작은 차이는 «장치 때문»이라고 "
                       "말할 수 없습니다." % (잡음폭 * 100))
    S = 회차[iB - 1]
    m = S["metrics"]

last = {}
for s_ in sorted(S["sections"], key=lambda x: x.get("바퀴", 0)):
    old = last.get(s_["절"])
    if old is None or len(s_["인용"]) >= len(old["인용"]):
        last[s_["절"]] = s_
secs = sorted(last.values(), key=lambda x: x["번호"])
판정 = {s["절"]: 절판정(s, agent.DOCS) for s in secs}
실인용맵 = {k: v["실인용"] for k, v in 판정.items()}

# ══ 경보 — ⛔왼쪽 컬러 보더 아님. 바탕으로 ════════════════════════
벌 = []
for k, v in 지표사전.items():
    if "경보" not in v["종류"]:
        continue
    x = m.get(k)
    n = len(x) if isinstance(x, list) else (x or 0)
    if n:
        벌.append("<li><b>%s %s</b> — %s</li>" % (k, n, v["한 줄"]))
if 벌:
    H('<div class="alarm"><div class="h">0이어야 하는 값이 0이 아닙니다</div>'
      '<ul>%s</ul></div>' % "".join(벌))
else:
    H('<div class="clear">경보 없음 — 허위 인용 · 표기 흔들림 · '
      '인용 0곳 절 · 꺾쇠 안 닫힘이 모두 0입니다.</div>')

# ══ ★도면 ═══════════════════════════════════════════════════════
괘선("배정 도면",
   "왼쪽은 코퍼스이고 막대 길이가 글자 수입니다. 오른쪽은 조사관이고 "
   "<b>선 모양</b>으로 갈립니다. 가운데 선이 «누가 무엇을 읽었나»입니다. "
   "겹친 선은 <b>중복</b>, 몰린 선은 <b>편중</b>, 흐린 선은 <b>읽고 안 쓴</b> 것입니다.",
   "문서 %d건 → 조사관 %d명" % (len(agent.DOCS), len(secs)), 번호=3)
H(mapviz.도면(agent.DOCS, secs, 실인용맵,
              격리=(m["팀이읽은글자"], m["코디가본글자"])))

# ══ 판독 — ⛔스탯 배너 줄 대신 «문장» ═════════════════════════════
괘선("도면에서 읽히는 것",
   "숫자를 그대로 두면 못 읽습니다. 무엇이 어디서 보이는지 적습니다.")

# ★B — 잡음 띠. 근거율만 띄우면 사람은 그 값을 믿는다.
_범위 = compare.잡음범위()
if _범위:
    _svg, _안 = compare.띠(m["근거율"], _범위, C=C)
    H('<div style="display:flex;gap:20px;align-items:center;'
      'margin:10px 0 4px;flex-wrap:wrap">%s'
      '<div style="font-size:13px;line-height:1.8;max-width:62ch;color:%s">'
      '이번 근거율은 <b class="num" style="color:%s">%.1f%%</b> 입니다. '
      '회색 띠는 <b>같은 설정</b>을 <span class="num">%d</span>번 돌렸을 때 '
      '나온 범위(<span class="num">%.1f</span>~<span class="num">%.1f</span>%%)입니다.'
      '<br><b>%s</b></div></div>'
      % (_svg, C["ink60"], C["mark"], m["근거율"] * 100, _범위["n"],
         _범위["최소"] * 100, _범위["최대"] * 100,
         ("바늘이 띠 «안»에 있습니다 — 이 값만으로는 아무것도 못 읽습니다. "
          "장치를 바꿔 여러 번 돌려야 합니다."
          if _안 else
          "바늘이 띠를 «벗어났습니다» — 잡음으로 설명되지 않는 값입니다.")))
H('<ul class="read">%s</ul>' % "".join(
    "<li>%s<span class='why'>%s</span></li>" % (a, b)
    for a, b in mapviz.판독(agent.DOCS, secs, 실인용맵, m)))

with st.expander("계기판 전체 — 지표마다 어느 장치를 보는 신호인가"):
    st.table([{"지표": k,
               "값": ("%d건" % len(m[k])) if isinstance(m.get(k), list)
               else (("%.1f%%" % (m[k] * 100)) if isinstance(m.get(k), float)
                     else m.get(k)),
               "종류": v["종류"].replace("★", ""), "어느 장치": v["장치"],
               "한 줄": v["한 줄"]}
              for k, v in 지표사전.items() if k in m])
    st.caption("버린 지표 셋 — 가독성 점수 · 문체 일관성 · 인용 밀도 분산. "
               "셋 다 잴 수는 있었지만 어느 장치를 보는지 한 줄로 못 적어서 "
               "버렸습니다. 요건이 「설명이 한 줄로 안 되는 지표는 버립니다」라고 "
               "했습니다.")

# ══ 절 원고 — ⛔카드 아님. 본문 조판 ══════════════════════════════
괘선("절마다 무엇을 썼나",
   "왼쪽이 조사관이 쓴 원고이고, 오른쪽은 그가 읽은 문서입니다. "
   "강조된 것이 원고에 붙은 근거입니다.")
지시맵 = {t.get("절"): t.get("지시", "") for t in S.get("toc", [])}
for i, sec in enumerate(secs):
    j = 판정[sec["절"]]
    쓴것 = set(j["실인용"])
    docs = "".join(
        '<div class="d%s"><span class="mk">%s</span>'
        '<span class="n">%s</span><span class="sz">%s</span></div>'
        % (" used" if d in 쓴것 else "", "●" if d in 쓴것 else "",
           esc(d), format(len(agent.DOCS.get(d, "")), ","))
        for d in sec["읽음"])
    경 = ""
    if j["진짜허위"]:
        경 += ("<div class='alarm' style='margin-top:10px'>"
              "<div class='h'>안 읽은 문서를 인용했습니다</div>%s</div>"
              % esc(", ".join(j["진짜허위"])))
    if j["흔들림"]:
        경 += ("<div class='alarm' style='margin-top:10px'>"
              "<div class='h'>표기가 흔들렸습니다</div>%s — 환각이 아니라 "
              "오타이고, 내용은 그 문서에서 왔습니다.</div>"
              % esc(" · ".join("%s → %s" % x for x in j["흔들림"])))
    H('<div class="sec"><div class="top">'
      '<span class="idx">%02d</span><span class="ttl">%s</span>'
      '<span class="who">%s · %s</span></div>'
      '<div class="body"><div><div class="draft">%s</div>%s</div>'
      '<div class="aside"><div class="t">배정받은 일</div>'
      '<div style="margin-bottom:12px;line-height:1.7">%s</div>'
      '<div class="t">읽은 문서 %d건 · ● 은 인용까지 한 것</div>%s'
      '<div style="margin-top:10px;color:%s">자기신고 — %s</div>'
      '</div></div></div>'
      % (i + 1, esc(sec["절"]), esc(sec["역할"]),
         ui.DASH_이름[i % 4], 강조(sec["원고"]), 경,
         esc(지시맵.get(sec["절"], "(없음)")), len(sec["읽음"]), docs,
         C["ink60"] if sec["충분"] else C["mark"],
         "충분하다" if sec["충분"] else "부족: " + esc(sec["부족"])))
    with st.expander("이 조사관이 본 원문 메모 — 코디에게 올라가지 않습니다"):
        st.caption("컨텍스트 격리. 원문은 여기서 끝나고 위로는 원고만 "
                   "올라갑니다. 이 메모를 코디네이터는 본 적이 없습니다.")
        for mm in sec["메모"]:
            st.text(mm[:1400])

# ══ 격리 단면 ════════════════════════════════════════════════════
괘선("격리 단면",
   "요건이 「코디네이터가 본 글자 수와 서브에이전트가 본 글자 수를 <b>따로</b> "
   "센다」고 했습니다. 비율만 두면 무엇이 움직였는지 못 봅니다 — 격리율이 "
   "오르는 것은 원고가 길어진 것일 수도, 덜 읽은 것일 수도 있습니다.")
H('<div class="cut">'
  '<div class="row"><span class="k">코디네이터가 본 글자</span>'
  '<span class="v num">%s</span><span class="n">절 원고만 받는다</span></div>'
  '<div class="row"><span class="k">팀이 읽은 글자</span>'
  '<span class="v num">%s</span>'
  '<span class="n">조사관 안에서 끝난다 · 위로 안 올라간다</span></div>'
  '<div class="row"><span class="k">격리율</span>'
  '<span class="v num" style="color:%s">%.1f%%</span>'
  '<span class="n">한 자릿수여야 한다</span></div></div>'
  % (format(m["코디가본글자"], ","), format(m["팀이읽은글자"], ","),
     C["mark"], m["격리율"] * 100))

# ══ 파이프라인 기록 ═══════════════════════════════════════════════
괘선("파이프라인이 한 일",
   "라우팅은 코드 짤 때, GraphRAG 는 인덱싱할 때 구조가 굳습니다. "
   "이 구조는 <b>질문이 온 뒤</b>에 굳습니다 — 목차·인원·배정이 질문마다 "
   "다릅니다.")
for l in S.get("log", []):
    st.text(l)
u = S["usage"]
H('<div style="font-size:12.5px;color:%s;line-height:1.9;margin-top:10px">'
  '종료 사유 <b>%s</b> · <span class="num">%d</span>바퀴. '
  '「빈 칸 없음」과 「바퀴 소진」은 완전히 다른 사건이라 상태에 남깁니다.<br>'
  '호출 <span class="num">%d</span>회 · 입력 <span class="num">%s</span> · '
  '출력 <span class="num">%s</span> 토큰 · <span class="num">%.1f</span>초 · '
  '약 <span class="num">$%.4f</span></div>'
  % (C["ink60"], esc(S["종료"]), S["wheel"], u["calls"],
     format(u["in"], ","), format(u["out"], ","),
     st.session_state.get("sec", 0),
     u["in"] / 1e6 * 0.15 + u["out"] / 1e6 * 0.60))

with st.expander("목차 — 코디네이터가 질문이 온 뒤 정한 것"):
    st.json(S.get("toc", []))
