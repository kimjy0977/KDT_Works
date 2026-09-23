# -*- coding: utf-8 -*-
"""웹 데모 — ★「누가 · 무엇을 읽고 · 무엇을 썼나」

  streamlit run app.py
  ?q=질문&axis=문화권&auto=1    ← 링크로 «이 설정 그대로» 보낼 수 있다

★요건이 못 박은 것
  「보고서와 함께 절마다 누가 무엇을 읽고 무엇을 썼는지를 보여 줍니다.
   ★숫자만 보여 주는 화면은 이 프로젝트의 요점을 놓칩니다.」
  ⇒ 첫 탭이 계기판이 «아니라» 절별 추적인 이유.

★디자인 — 「성좌 필사본」 (토큰은 ui.py 한 곳에만 있다)
  절 하나 = 하늘 한 «구역». 조사관이 그 구역을 맡는다 — 은유가 아니라 실제 기능이다.
  읽은 문서는 «별»이고, 인용되면 ★금박으로 불이 켜진다.
  격리는 «지상/지하»로 그린다 — 원문은 아래에 잠기고 원고만 위로 올라온다.
"""
import io
import json
import os
import re
import time

import streamlit as st

import graph as agent
import ui
from metrics import 지표사전, 절판정

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(io.open(os.path.join(HERE, "config.json"), encoding="utf-8"))
QS = json.load(io.open(os.path.join(HERE, "data/questions.json"),
                       encoding="utf-8"))

st.set_page_config(page_title="딥리서처 — 세계 신화", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown(ui.css(), unsafe_allow_html=True)

# ── ★URL 파라미터 — «사이드바보다 먼저» 읽는다 ──────────────────────
#   나중에 읽으면 위젯이 기본값으로 이미 만들어진 뒤라 ★조용히 무시된다.
#   (노드7 에서 hop 파라미터가 문서에만 있고 코드가 안 읽던 자리)
_qp = st.query_params
if not st.session_state.get("_from_url") and (_qp.get("q") or _qp.get("auto")):
    if _qp.get("q"):
        st.session_state["_url_q"] = _qp["q"]
    if _qp.get("axis"):
        st.session_state["_url_axis"] = _qp["axis"]
    st.session_state["_auto"] = _qp.get("auto") in ("1", "true", "yes")
    st.session_state["_from_url"] = True

C, I = ui.C, ui.icon
H = lambda s: st.markdown(s, unsafe_allow_html=True)      # noqa: E731


def esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def 금박(t):
    """★인용에 금박을 입힌다 — «…» 를 찾아 강조한다."""
    return re.sub("«([^»\n]{1,40})»",
                  '<span class="q">«\\1»</span>', esc(t))


# ══ 머리 ══════════════════════════════════════════════════════════
co = CFG["_코퍼스"]
H('<div class="codex-head">'
  '<div class="eyebrow">%s Codex of Constellations</div>'
  '<div class="codex-title">딥리서처 &mdash; 세계 신화</div>'
  '<div class="codex-sub">코디네이터 한 명이 조사관 <b>넷</b>을 동시에 파견해 '
  '각자 한 절씩 써 옵니다. 원문은 조사관 안에서 끝나고 위로는 원고만 올라옵니다.<br>'
  '코퍼스 <b>%d건</b> · <b>%s자</b> &mdash; 모델의 창 128k 토큰의 '
  '<b>%s</b>라 <b>전부 넣는 길이 없습니다.</b></div></div>'
  % (I("star", 13, C["brass"]), co["문서"], format(co["글자"], ","),
     co["창대비"].split()[0]))

# ══ 사이드바 ══════════════════════════════════════════════════════
with st.sidebar:
    H('<div class="eyebrow">%s Settings</div>' % I("scale", 13, C["brass"]))
    st.caption("값의 출처는 `config.json` **하나**입니다.")
    절수 = st.slider("절수 — 폭", 2, 6, agent.설정["절수"])
    예산 = st.slider("절당 읽기 예산 — 깊이", 1, 6, agent.설정["예산"])
    st.caption("읽기 총량 **%d건** = 절수 × 예산. 대조군도 같은 값을 받습니다."
               % (절수 * 예산))

    st.divider()
    H('<div class="eyebrow">%s Ablation</div>' % I("send", 13, C["brass"]))
    st.caption("끄면 **무엇이 먼저 무너지는지** 보세요.")
    배정 = st.checkbox("배정 — 코디가 시작 문서를 정해 준다", agent.설정["배정"],
                     help="끄면 편중·읽고안쓴이 뛸 것")
    구역 = st.checkbox("구역 — 남의 구역을 알려 준다", agent.설정["구역"],
                     help="끄면 중복률이 먼저 뛸 것")
    역할 = st.checkbox("역할 — 「우주 발생 담당」 같은 이름", agent.설정["역할"],
                     help="끄면 절이 비슷해질 것")
    재위임 = st.checkbox("재위임 — 부족하다는 절만 다시", agent.설정["재위임"],
                      help="끄면 근거율이 내려갈 것")

    st.divider()
    H('<div class="eyebrow">%s Axis</div>' % I("book", 13, C["brass"]))
    _축목록 = ["주제 — 창조·홍수·저승·영웅", "문화권 — 메소포타미아·그리스·이집트·북유럽"]
    _i = 1 if str(st.session_state.get("_url_axis", "")).startswith("문화권") else 0
    축 = st.radio("절을 나누는 축", _축목록, index=_i)
    st.caption("**목차의 축이 곧 분업**이고, 분업이 곧 결과물의 모양입니다. "
               "⚠단 REPORT §6 에 적었듯 **역할만 바꿔서는 축이 안 바뀝니다** — "
               "목차를 정하는 건 역할이 아니라 «질문»이라서요. 직접 확인해 보세요.")

    st.divider()
    st.caption("1회 실행 ≈ **$0.012** · 약 20초 · gpt-4o-mini")

# ══ 질문 ══════════════════════════════════════════════════════════
예시 = [QS["주질문"]["text"]] + [q["text"] for q in QS["보조질문"]]
_uq = st.session_state.get("_url_q")
_qi = 예시.index(_uq) if _uq in 예시 else 0
H('<div class="eyebrow" style="margin-bottom:8px">%s Question</div>'
  % I("eye", 13, C["brass"]))
고른질문 = st.selectbox("질문", 예시 + ["(직접 입력)"], index=_qi,
                    label_visibility="collapsed")
q = (st.text_input("직접 입력", "", placeholder="물어볼 것을 적으세요")
     if 고른질문 == "(직접 입력)" else 고른질문)

with st.expander("이 질문이 **왜 나눌 만한가** — 요건이 요구한 근거"):
    if 고른질문 == QS["주질문"]["text"]:
        for l in QS["주질문"]["왜 나눌 만한가"]:
            st.markdown(l or "&nbsp;")
        st.info("**나눌 필요 «없는» 질문도 적어 뒀습니다** — "
                + " · ".join(x["text"]
                             for x in QS["⛔나눌 필요 없음 — 대조용 반례"])
                + "  → 이런 건 혼자가 더 싸게 이깁니다. "
                  "**그 경계를 아는 것**이 「언제 팀을 꾸리나」의 답입니다.")
    else:
        st.caption("`data/questions.json` 을 보세요.")

_auto = st.session_state.pop("_auto", False)
if st.button("조사 시작", type="primary") or _auto:
    agent.설정.update({"절수": 절수, "예산": 예산, "배정": 배정,
                      "구역": 구역, "역할": 역할, "재위임": 재위임})
    agent.ROSTER = (agent.ROSTER_ALT if 축.startswith("문화권")
                    else CFG["_역할명단"]["★주제 축(A) — 기본"])
    with st.spinner("코디네이터가 목차를 짜고 조사관 %d명을 파견합니다…" % 절수):
        t0 = time.time()
        st.session_state["st"] = agent.run(q, quiet=True)
        st.session_state["sec"] = round(time.time() - t0, 1)

S = st.session_state.get("st")
if not S:
    H('<div class="const" style="margin-top:24px">'
      '<div class="const-b" style="grid-template-columns:1fr">'
      '<div><div class="step">%s 아직 비어 있습니다</div>'
      '<p style="color:%s;font-size:14px;line-height:1.9;margin:0">'
      '질문을 고르고 <b style="color:%s">조사 시작</b>을 누르세요. '
      '왼쪽에서 장치를 끄거나 «축»을 바꿔 가며 견줘 보시면 '
      '<b>무엇이 실제로 값을 하는지</b>가 보입니다.<br><br>'
      '⚠ 미리 말씀드리면 — 같은 설정을 12번 돌려 잰 <b>잡음이 15.0%%p</b>이고, '
      '장치를 바꾼 조건들의 차이는 <b>11.7%%p</b>입니다. '
      '<b style="color:%s">잡음이 차이보다 큽니다.</b> '
      '한 번 돌린 숫자로 판단하지 마세요.</p></div></div></div>'
      % (I("star", 13, C["brass"]), C["dim"], C["brass"], C["seal"]))
    st.stop()

m = S["metrics"]

# ══ 계기판 — 신호와 경보를 «갈라» 보여 준다 ═════════════════════════
H('<div class="eyebrow" style="margin:28px 0 4px">%s Instruments</div>'
  % I("scale", 13, C["brass"]))

_g = [("근거율", "%.1f%%" % (m["근거율"] * 100), "gold"),
      ("편중", "%.1f%%" % (m["편중"] * 100), ""),
      ("중복률", "%.1f%%" % (m["중복률"] * 100), ""),
      ("격리율", "%.1f%%" % (m["격리율"] * 100), "gold")]
H('<div class="gauges">' + "".join(
    '<div class="g %s"><div class="k">%s %s</div><div class="v">%s</div>'
    '<div class="h">%s</div></div>'
    % (cl, I("star", 11, C["brass"] if cl else C["faint"]), k, v,
       지표사전[k]["한 줄"])
    for k, v, cl in _g) + '</div>')

경보 = [k for k, v in 지표사전.items() if "경보" in v["종류"]]
벌 = []
for k in 경보:
    v = m.get(k)
    n = len(v) if isinstance(v, list) else (v or 0)
    if n:
        벌.append("<li><b>%s %s</b> — %s</li>" % (k, n, 지표사전[k]["한 줄"]))
if 벌:
    H('<div class="seal"><div class="t">%s 경보 — 0이어야 하는 값이 0이 아닙니다'
      '</div><ul>%s</ul></div>' % (I("seal", 15, "#F0B5AE"), "".join(벌)))
else:
    H('<div class="pass">%s 경보 0 — 허위 인용 · 표기 흔들림 · 인용 0곳 절 · '
      '꺾쇠 안 닫힘 모두 0</div>' % I("check", 15, C["moss"]))

with st.expander("계기판 전체 — **지표마다 «어느 장치»를 보는 신호인가**"):
    st.table([{"지표": k,
               "값": ("%d건" % len(m[k])) if isinstance(m.get(k), list)
               else (("%.1f%%" % (m[k] * 100)) if isinstance(m.get(k), float)
                     else m.get(k)),
               "종류": v["종류"], "어느 장치": v["장치"], "한 줄": v["한 줄"]}
              for k, v in 지표사전.items() if k in m])
    st.caption("**버린 지표 셋** — 가독성 점수 · 문체 일관성 · 인용 밀도 분산. "
               "셋 다 «잴 수는» 있었지만 **어느 장치를 보는지 한 줄로 못 적어서** "
               "버렸습니다(요건: 「설명이 한 줄로 안 되는 지표는 버립니다」).")

# ══ 탭 ════════════════════════════════════════════════════════════
t1, t2, t3 = st.tabs(["절별 추적 — 누가 뭘 읽고 뭘 썼나",
                      "완성된 보고서", "파이프라인이 한 일"])

# ── 바퀴가 여럿이면 «인용이 줄지 않은» 쪽 (review 의 채택 규칙과 같다) ──
last = {}
for s_ in sorted(S["sections"], key=lambda x: x.get("바퀴", 0)):
    old = last.get(s_["절"])
    if old is None or len(s_["인용"]) >= len(old["인용"]):
        last[s_["절"]] = s_

with t1:
    st.caption("**이 탭이 이 데모의 요점입니다.** 요건이 "
               "「숫자만 보여 주는 화면은 이 프로젝트의 요점을 놓친다」고 "
               "못 박았습니다. 절 하나가 하늘 한 «구역»이고, "
               "읽은 문서가 «별»입니다 — **인용되면 금으로 불이 켜집니다.**")

    지시맵 = {t.get("절"): t.get("지시", "") for t in S.get("toc", [])}
    for n, (절, sec) in enumerate(last.items(), 1):
        # ★판정은 metrics.py 한 곳에서 — 화면과 계기판이 같은 말을 하게 한다.
        #   UI 를 만들다 드러났다: 절 카드는 「안 읽은 문서 인용」이라 하고
        #   계기판은 같은 사건을 「표기 흔들림」이라 했다.
        j = 절판정(sec, agent.DOCS)
        쓴것 = set(j["실인용"])
        docs = "".join(
            '<div class="doc%s">%s<span class="nm">%s</span>'
            '<span class="sz">%s자</span></div>'
            % (" lit" if d in 쓴것 else "",
               I("star", 13, C["brass"] if d in 쓴것 else C["faint"]),
               esc(d), format(len(agent.DOCS.get(d, "")), ","))
            for d in sec["읽음"])
        cites = "".join('<span class="cite">«%s»</span>' % esc(x)
                        for x in dict.fromkeys(j["실인용"])) or \
            '<span style="color:%s;font-size:12px">(없음)</span>' % C["faint"]
        벌2 = []
        if j["진짜허위"]:
            벌2.append("<li><b>안 읽은 문서를 인용</b> — %s</li>"
                       % esc(", ".join(j["진짜허위"])))
        if j["흔들림"]:
            벌2.append("<li><b>표기 흔들림</b> — %s "
                       "<span style=\'color:%s\'>(환각이 아니라 오타. "
                       "내용은 그 문서에서 왔다)</span></li>"
                       % (esc(" · ".join("%s → %s" % x for x in j["흔들림"])),
                          C["dim"]))
        허위 = ('<div class="seal" style="margin-top:10px"><div class="t">%s '
               '이 절의 경보</div><ul>%s</ul></div>'
               % (I("seal", 14, "#F0B5AE"), "".join(벌2))) if 벌2 else ""
        H('<div class="const">'
          '<div class="const-h"><div class="const-n">%d</div>'
          '<div class="const-t">%s</div><div class="const-r">%s</div></div>'
          '<div class="const-b">'
          '<div><div class="step"><span class="order">①</span> 배정받은 일</div>'
          '<p style="color:%s;font-size:12.5px;line-height:1.7;margin:0 0 18px">%s</p>'
          '<div class="step"><span class="order">②</span> 무엇을 읽었나 — %d건</div>'
          '%s'
          '<p style="color:%s;font-size:11px;margin:8px 0 0">'
          '금색 = 인용까지 한 문서 · 회색 = <b>읽고 안 쓴</b> 문서<br>★표기가 흔들린 인용도 «쓴 것»으로 셉니다 — 오타지 안 쓴 게 아닙니다</p></div>'
          '<div><div class="step"><span class="order">③</span> 무엇을 썼나 — %d자</div>'
          '<div class="draft">%s</div>'
          '<div class="step" style="margin:16px 0 6px">'
          '<span class="order">④</span> 어디를 인용했나 — %d곳</div>'
          '<div class="cites">%s</div>%s'
          '<p style="color:%s;font-size:11.5px;margin:14px 0 0">'
          '자기신고 — <b style="color:%s">%s</b></p>'
          '</div></div></div>'
          % (n, esc(절), esc(sec["역할"]),
             C["dim"], esc(지시맵.get(절, "(없음)")),
             len(sec["읽음"]), docs, C["faint"],
             len(sec["원고"]), 금박(sec["원고"]),
             len(sec["인용"]), cites, 허위,
             C["faint"], C["moss"] if sec["충분"] else C["seal"],
             "충분하다" if sec["충분"] else "부족: " + esc(sec["부족"])))

        with st.expander("이 조사관이 **본** 원문 메모 — 코디에게 올라가지 않습니다"):
            st.caption("**컨텍스트 격리** — 원문은 여기서 끝나고, 위로는 ③ 원고만 "
                       "올라갑니다. 이 메모를 코디네이터는 «본 적이 없습니다».")
            for mm in sec["메모"]:
                st.text(mm[:1400])

    # ── ★격리 — 지상/지하 ──
    H('<div class="eyebrow" style="margin:28px 0 8px">%s Stratigraphy</div>'
      % I("down", 13, C["brass"]))
    H('<div class="strata">'
      '<div class="above"><div class="lab">%s 지상 &mdash; 코디네이터가 «본» 글자</div>'
      '<div class="val">%s</div></div><div class="gap"></div>'
      '<div class="below"><div class="lab">%s 지하 &mdash; 팀이 «읽은» 글자 '
      '(코디는 본 적이 없다)</div><div class="val">%s</div></div></div>'
      '<p style="color:%s;font-size:12.5px;line-height:1.8;margin-top:10px">'
      '격리율 <b class="num" style="color:%s">%.1f%%</b> — '
      '★<b>비율만 보면 «무엇이 움직였나»를 못 봅니다.</b> 격리율이 오르는 것은 '
      '원고가 길어진 것일 수도, 덜 읽은 것일 수도 있습니다. 그래서 '
      '요건이 「따로 <b>센다</b>」고 했고, 원시값을 나란히 뒀습니다.</p>'
      % (I("up", 12, C["navy"]), format(m["코디가본글자"], ","),
         I("down", 12, C["brass"]), format(m["팀이읽은글자"], ","),
         C["dim"], C["brass"], m["격리율"] * 100))

with t2:
    st.markdown(S["report"])
    st.download_button("보고서 내려받기", S["report"],
                       file_name="report.md", mime="text/markdown")

with t3:
    H('<div class="eyebrow" style="margin-bottom:10px">%s Pipeline</div>'
      % I("send", 13, C["brass"]))
    NODES = [("plan", "기획", "카드를 보고 목차·역할·시작문서를 정한다"),
             ("send", "배치", "Send 로 팬아웃 — 조사관 N명 동시 파견"),
             ("read", "조사", "★노드 «안»에 루프. 읽고 → 고르고 → 원고"),
             ("check", "점검", "자기신고를 모아 빈 칸을 찾는다 · LLM 0회"),
             ("book", "종합", "절을 이어 붙이고 머리말·맺음말"),
             ("scale", "평가", "★정답표 없이 잰다")]
    H('<div class="gauges" style="grid-template-columns:repeat(auto-fit,minmax(190px,1fr))">'
      + "".join('<div class="g"><div class="k">%s <b style="color:%s">%d</b> %s</div>'
                '<div class="h" style="margin-top:4px">%s</div></div>'
                % (I(ic, 13, C["brass"]), C["brass"], i, nm, de)
                for i, (ic, nm, de) in enumerate(NODES, 1)) + '</div>')
    st.caption("재위임이 걸리면 **④ 점검 → ② 배치**로 돌아갑니다 "
               "(이중 종료 조건: 내용 기준 + 예산 기준).")

    st.divider()
    for l in S.get("log", []):
        st.text(l)
    u = S["usage"]
    H('<p style="color:%s;font-size:12.5px;line-height:1.9;margin-top:12px">'
      '종료 사유 <b style="color:%s">%s</b> · <span class="num">%d</span>바퀴 &mdash; '
      '★「빈 칸 없음」과 「바퀴 소진」은 완전히 다른 사건이라 상태에 남깁니다.<br>'
      '호출 <span class="num">%d</span>회 · 입력 <span class="num">%s</span> · '
      '출력 <span class="num">%s</span> 토큰 · <span class="num">%.1f</span>초 · '
      '약 <b class="num" style="color:%s">$%.4f</b></p>'
      % (C["dim"], C["brass"], esc(S["종료"]), S["wheel"], u["calls"],
         format(u["in"], ","), format(u["out"], ","),
         st.session_state.get("sec", 0), C["brass"],
         u["in"] / 1e6 * 0.15 + u["out"] / 1e6 * 0.60))

    with st.expander("목차 — 코디네이터가 **질문이 온 «뒤»** 정한 것"):
        st.caption("라우팅은 코드 짤 때, GraphRAG 는 인덱싱할 때 구조가 굳습니다. "
                   "이 구조는 **질문이 온 뒤**에 굳습니다 — 목차·인원·배정이 "
                   "질문마다 다릅니다.")
        st.json(S.get("toc", []))
