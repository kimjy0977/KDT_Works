# -*- coding: utf-8 -*-
"""웹 데모 — ★「누가 · 무엇을 읽고 · 무엇을 썼나」를 보여 준다.

  streamlit run app.py

★요건이 못 박은 것
  「보고서와 함께 절마다 누가 무엇을 읽고 무엇을 썼는지를 보여 줍니다.
   ★숫자만 보여 주는 화면은 이 프로젝트의 요점을 놓칩니다.」

  ⇒ 그래서 이 화면의 «주인공»은 계기판이 아니라 **절별 추적**이다.
    계기판은 접어 두고, 절을 펼치면 그 조사관이
      ① 무엇을 배정받았고 ② 무엇을 읽었고 ③ 무엇을 메모했고
      ④ 무엇을 썼고 ⑤ 어디를 인용했는지
    가 «원문 메모까지» 나온다.

★격리를 «보이게» 하는 것이 이 화면의 두 번째 일이다.
  원문은 조사관 안에서 끝나고 코디는 원고만 본다 — 말로는 와닿지 않는다.
  그래서 「코디가 본 글자 / 팀이 읽은 글자」를 원시값으로 나란히 둔다.
"""
import io
import json
import os
import time

import streamlit as st

import graph as agent
from metrics import 지표사전

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(io.open(os.path.join(HERE, "config.json"), encoding="utf-8"))
QS = json.load(io.open(os.path.join(HERE, "data/questions.json"),
                       encoding="utf-8"))

st.set_page_config(page_title="딥리서처 — 세계 신화", layout="wide")

# ── ★URL 파라미터 — «사이드바보다 먼저» 읽는다 ──────────────────
#   나중에 읽으면 위젯이 기본값으로 이미 만들어진 뒤라 ★조용히 무시된다.
#   노드7 에서 hop 파라미터가 문서에만 있고 코드가 안 읽던 자리다.
#   ?q=질문&axis=문화권&auto=1
_qp = st.query_params
if not st.session_state.get("_from_url") and (_qp.get("q") or _qp.get("auto")):
    if _qp.get("q"):
        st.session_state["_url_q"] = _qp["q"]
    if _qp.get("axis"):
        st.session_state["_url_axis"] = _qp["axis"]
    st.session_state["_auto"] = _qp.get("auto") in ("1", "true", "yes")
    st.session_state["_from_url"] = True



# ────────────────────────────────────────────────────────────────
def 계기판(m):
    """★신호와 경보를 «갈라» 보여 준다 — 섞으면 무엇이 급한지 모른다."""
    경보 = [k for k, v in 지표사전.items() if "경보" in v["종류"]]
    c = st.columns(4)
    for i, k in enumerate(("근거율", "편중", "중복률", "격리율")):
        c[i].metric(k, "%.1f%%" % (m[k] * 100), help=지표사전[k]["한 줄"])

    벌 = []
    for k in 경보:
        v = m.get(k)
        n = len(v) if isinstance(v, list) else v
        if n:
            벌.append("**%s %s** — %s" % (k, n, 지표사전[k]["한 줄"]))
    if 벌:
        st.error("🚨 경보 — 0이어야 하는 값이 0이 아닙니다\n\n" + "\n\n".join(벌))
    else:
        st.success("🚨 경보 0 — 허위 인용 · 표기 흔들림 · 인용 0곳 절 모두 0")

    with st.expander("계기판 전체 — ★지표마다 «어느 장치»를 보는 신호인가"):
        st.table([{"지표": k, "값": _보기(m.get(k)), "종류": v["종류"],
                   "어느 장치": v["장치"], "한 줄 설명": v["한 줄"]}
                  for k, v in 지표사전.items()])
        st.caption("⛔ 설명이 한 줄로 안 되는 지표는 버렸습니다 — "
                   "가독성 점수 · 문체 일관성 · 인용 밀도 분산 "
                   "(셋 다 «잴 수는» 있었지만 «어느 장치»를 보는지 말할 수 없었습니다)")


def _보기(v):
    if isinstance(v, list):
        return "%d건" % len(v)
    if isinstance(v, float):
        return "%.1f%%" % (v * 100) if v <= 1 else "%.2f" % v
    return v


def 절추적(sec, toc):
    """★이 화면의 주인공 — 누가 · 무엇을 읽고 · 무엇을 썼나."""
    지시 = ""
    for t in toc:
        if t.get("절") == sec["절"]:
            지시 = t.get("지시", "")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("**① 누가** — `%s`" % sec["역할"])
        st.markdown("**② 배정받은 일**")
        st.caption(지시 or "(없음)")
        st.markdown("**③ 무엇을 읽었나** — %d건" % len(sec["읽음"]))
        for d in sec["읽음"]:
            쓴것 = "✅" if d in sec["인용"] else "⬜"
            st.markdown("- %s «%s»  `%s자`"
                        % (쓴것, d, format(len(agent.DOCS.get(d, "")), ",")))
        st.caption("✅ = 인용까지 한 문서 · ⬜ = 읽고 안 쓴 문서")
    with c2:
        st.markdown("**④ 무엇을 썼나** — %d자" % len(sec["원고"]))
        st.write(sec["원고"])
        st.markdown("**⑤ 어디를 인용했나** — %d곳" % len(sec["인용"]))
        st.code(" / ".join("«%s»" % x for x in sec["인용"]) or "(없음)")
        if sec["허위인용"]:
            st.error("🚨 안 읽은 문서 인용: %s" % sec["허위인용"])
        st.markdown("**자기신고** — %s"
                    % ("충분하다" if sec["충분"] else "★부족: " + sec["부족"]))

    with st.expander("★조사관이 «본» 원문 메모 — 이것은 코디에게 올라가지 않는다"):
        st.caption("컨텍스트 격리 — 원문은 여기서 끝나고, 위로는 ④ 원고만 올라갑니다. "
                   "이 메모를 코디네이터는 «본 적이 없습니다».")
        for mm in sec["메모"]:
            st.text(mm[:1200])


# ────────────────────────────────────────────────────────────────
st.title("딥리서처 — 코디네이터 + 서브에이전트")
st.caption("모듈5 노드9 [실습 프로젝트] · 김주영 · 코퍼스: %s %d건 %s자"
           % (CFG["_코퍼스"]["이름"], CFG["_코퍼스"]["문서"],
              format(CFG["_코퍼스"]["글자"], ",")))

with st.sidebar:
    st.header("설정")
    st.caption("값의 출처는 `config.json` 하나입니다.")
    절수 = st.slider("절수 (폭)", 2, 6, agent.설정["절수"])
    예산 = st.slider("절당 읽기 예산 (깊이)", 1, 6, agent.설정["예산"])
    st.divider()
    st.markdown("**장치 끄기** — 끄면 무엇이 무너지는지 보세요")
    배정 = st.checkbox("배정 — 코디가 시작문서를 정해 준다", agent.설정["배정"])
    구역 = st.checkbox("구역 — 남의 구역을 알려 준다", agent.설정["구역"])
    역할 = st.checkbox("역할 — 「우주 발생 담당」 같은 이름", agent.설정["역할"])
    재위임 = st.checkbox("재위임 — 부족하다는 절만 다시", agent.설정["재위임"])
    st.divider()
    _축목록 = ["주제 (창조·홍수·저승·영웅)", "문화권 (메소포타미아·그리스·…)"]
    _i = 1 if str(st.session_state.get("_url_axis", "")).startswith("문화권") else 0
    축 = st.radio("★절을 나누는 축", _축목록, index=_i)
    st.caption("★목차의 축이 곧 분업이고, 분업이 곧 결과물의 모양입니다. "
               "바꿔 돌려 보면 같은 질문에 «다른 보고서»가 나옵니다.")
    st.divider()
    st.caption("1회 실행 ≈ $0.012 · 약 20초")

예시 = [QS["주질문"]["text"]] + [q["text"] for q in QS["보조질문"]]
_uq = st.session_state.get("_url_q")
_qi = 예시.index(_uq) if _uq in 예시 else 0
고른질문 = st.selectbox("질문", 예시 + ["(직접 입력)"], index=_qi)
q = st.text_input("직접 입력", "") if 고른질문 == "(직접 입력)" else 고른질문

with st.expander("★이 질문이 «왜 나눌 만한가» — 요건이 요구한 근거"):
    if 고른질문 == QS["주질문"]["text"]:
        for l in QS["주질문"]["왜 나눌 만한가"]:
            st.markdown(l or "&nbsp;")
        st.info("⛔**나눌 필요 «없는» 질문도 적어 뒀습니다** — "
                + " · ".join(x["text"] for x in QS["⛔나눌 필요 없음 — 대조용 반례"]))
    else:
        st.caption("`data/questions.json` 을 보세요.")

_auto = st.session_state.pop("_auto", False)
if st.button("돌리기", type="primary") or _auto:
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
    st.info("질문을 고르고 **돌리기**를 누르세요. "
            "⬅ 왼쪽에서 장치를 끄거나 «축»을 바꿔 가며 견줘 보세요.")
    st.stop()

m = S["metrics"]
계기판(m)

tab1, tab2, tab3 = st.tabs(["★절별 추적 — 누가 뭘 읽고 뭘 썼나",
                            "완성된 보고서", "파이프라인이 한 일"])

with tab1:
    st.caption("★이 탭이 이 데모의 요점입니다. "
               "숫자만 보면 «분업이 실제로 무엇을 했는지»가 안 보입니다.")
    # 바퀴가 여럿이면 마지막 것만 (review 의 채택 규칙과 같다)
    last = {}
    for s_ in sorted(S["sections"], key=lambda x: x.get("바퀴", 0)):
        old = last.get(s_["절"])
        if old is None or len(s_["인용"]) >= len(old["인용"]):
            last[s_["절"]] = s_
    for 절, sec in last.items():
        with st.expander("**%s**  —  `%s` · 읽음 %d · 인용 %d · %d자"
                         % (절, sec["역할"], len(sec["읽음"]),
                            len(sec["인용"]), len(sec["원고"])),
                         expanded=(sec["번호"] == 0)):
            절추적(sec, S.get("toc", []))

    st.divider()
    c = st.columns(3)
    c[0].metric("코디가 «본» 글자", format(m["코디가본글자"], ","))
    c[1].metric("팀이 «읽은» 글자", format(m["팀이읽은글자"], ","))
    c[2].metric("★격리율", "%.1f%%" % (m["격리율"] * 100),
                help="원문은 조사관 안에서 끝납니다. 코디는 원고만 봅니다.")
    st.caption("★비율만 보면 «무엇이 움직였나»를 못 봅니다 — "
               "격리율이 오르는 것은 원고가 길어진 것일 수도, 덜 읽은 것일 수도 있습니다. "
               "그래서 원시값을 나란히 둡니다.")

with tab2:
    st.markdown(S["report"])
    st.download_button("보고서 내려받기", S["report"],
                       file_name="report.md", mime="text/markdown")

with tab3:
    for l in S.get("log", []):
        st.text(l)
    st.caption("종료 사유: **%s** · %d바퀴" % (S["종료"], S["wheel"]))
    u = S["usage"]
    st.caption("호출 %d회 · 입력 %s · 출력 %s 토큰 · %.1f초 · 약 $%.4f"
               % (u["calls"], format(u["in"], ","), format(u["out"], ","),
                  st.session_state.get("sec", 0),
                  u["in"] / 1e6 * 0.15 + u["out"] / 1e6 * 0.60))
    with st.expander("목차 — 코디네이터가 «질문이 온 뒤» 정한 것"):
        st.json(S.get("toc", []))
