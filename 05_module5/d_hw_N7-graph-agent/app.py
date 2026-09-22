# -*- coding: utf-8 -*-
"""웹 데모 (요건 ⑥) — 답변 + ★탄 경로 + 근거 삼중항 + 출처 문서

  streamlit run app.py

★요건이 요구한 넷을 «한 화면»에 다 보인다.
  답변 / 탄 경로 / 근거 삼중항 / 출처 문서
★거절도 보여 준다 — 「모른다」고 답하는 것이 이 시스템의 기능이다.
"""
import io
import json
import os

import streamlit as st

import agent as A

HERE = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(page_title="영화 딜레마 그래프", page_icon="🎬",
                   layout="wide")


@st.cache_resource
def boot():
    G = A.load_graph()
    reach, n_films = A.hub_reach(G)
    return G, reach, n_films, A.build()


@st.cache_data
def gold():
    p = os.path.join(HERE, "data", "goldenset.json")
    return json.load(io.open(p, encoding="utf-8"))["items"]


G, reach, n_films, app = boot()

st.title("🎬 영화 딜레마 그래프 에이전트")
st.caption("영화가 던지는 **물음**과 그 물음이 세우는 **가치의 대립**으로 "
           "「같은 딜레마를 다룬 다른 영화」를 찾습니다. "
           "답은 **그래프의 근거만으로** 만들고, 근거가 없으면 **모른다고 답합니다.**")

with st.sidebar:
    st.subheader("그래프")
    kinds = {}
    for _, d in G.nodes(data=True):
        k = d.get("kind", "?")
        kinds[k] = kinds.get(k, 0) + 1
    for k in ("Film", "Question", "Value"):
        st.metric(k, kinds.get(k, 0))
    st.caption("엣지 %d개" % G.number_of_edges())

    st.divider()
    st.subheader("설정")
    hop = st.slider("최대 홉", 1, 6, A.CFG["hops"]["max"],
                    help="4홉이면 「같은 가치 대립을 다룬 다른 영화」까지 닿습니다")

    st.divider()
    st.caption("**허브 회피** — 코퍼스의 %d%% 를 넘는 영화에 닿는 가치는 "
               "허브로 봅니다. 이 코퍼스에서는 최대가 11%% 라 "
               "거의 발동하지 않습니다(실측)." % (A.CFG["hub"]["degree_pct"] or 0))

examples = [it["user_input"] for it in gold()][:14]
kinds = {it["user_input"]: it["kind"] for it in gold()}

# ★streamlit 은 위젯이 렌더된 뒤 value= 변경을 «무시»한다.
#   그래서 selectbox 를 골라도 text_input 이 안 바뀌었다 (버그였다).
#   key + session_state 로 «직접» 갱신해야 한다.
st.session_state.setdefault("q", "")
st.session_state.setdefault("_pick", "(직접 입력)")


def _on_pick():
    p = st.session_state["_sel"]
    st.session_state["_pick"] = p
    st.session_state["q"] = "" if p == "(직접 입력)" else p


st.selectbox("평가셋에서 고르기 (14문항 · 1홉/2홉/4홉/★거절)",
             ["(직접 입력)"] + examples, key="_sel",
             format_func=lambda x: x if x == "(직접 입력)"
             else "[%s] %s" % (kinds.get(x, "?"), x[:56]),
             on_change=_on_pick)
st.text_input("질문", key="q",
              placeholder="예) 영화 «1987»과 같은 가치 대립을 다루는 다른 영화는?")
q = st.session_state["q"]

if st.button("물어보기", type="primary") and q.strip():
    with st.spinner("그래프를 걷는 중…"):
        res = A.ask(app, G, reach, n_films, q.strip(), hop)

    refused = "근거를 찾지 못" in (res["answer"] or "")
    (st.warning if refused else st.success)(res["answer"])
    if refused:
        st.caption("★근거가 없어 **거절**했습니다 — 지어내지 않는 것이 이 시스템의 기능입니다.")

    c1, c2, c3 = st.columns(3)
    c1.metric("탄 경로", len(res["paths"]))
    c2.metric("근거 삼중항", len(res["evidence"]))
    c3.metric("걸린 시간", "%.2fs" % res["sec"])

    st.subheader("★탄 경로")
    if not res["paths"]:
        st.caption("경로 없음")
    for i, p in enumerate(res["paths"][:10], 1):
        st.markdown("**%d.** %s" % (
            i, "  →  ".join("`%s` ─*%s*─ `%s`" % (s, r, o) for s, r, o in p)))
    if len(res["paths"]) > 10:
        st.caption("… 외 %d개" % (len(res["paths"]) - 10))

    st.subheader("근거 삼중항")
    if res["evidence"]:
        st.dataframe(
            [{"주어": t[0], "관계": t[1], "목적어": t[2]} for t in res["evidence"]],
            use_container_width=True, hide_index=True)
    else:
        st.caption("없음")

    st.subheader("출처 문서")
    st.write(" · ".join(res["sources"]) if res["sources"] else "없음")

    with st.expander("State 흐름 (LangGraph)"):
        st.code(" → ".join(t["node"] for t in res["trace"]))
        st.json(res["trace"])
