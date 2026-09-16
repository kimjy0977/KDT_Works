# -*- coding: utf-8 -*-
"""★12강 「더 해보기」 4 — 데모 화면. 라우트·도구·가드레일을 «함께» 보여준다.

12강이 시킨 것:
  「FastAPI + Streamlit 으로 상담 화면을 만들어 **라우트·호출된 도구·가드레일 결과를
   함께 보여주고**, README 에 설계 근거(어떤 정책 조항이 어떤 코드가 되었는지)를 표로 정리합니다.
   ⇒ '무엇을 만들었습니다'가 아니라 '**왜 그렇게 만들었습니다**'를 설명하는 문서가 완성됩니다.」

★왜 「함께 보여주는가」가 핵심인가
  답변 문장만 보면 **틀린 답도 자연스럽다.** 1강이 말한 그대로다 —
  「무료배송 기준이 40,000원입니다」는 완벽하게 자연스럽게 나온다.
  ⇒ 그래서 이 화면은 답변 «옆에» 항상 셋을 같이 띄운다:
     ① 어느 라우트로 갔나  ② 어떤 도구를 «실제로» 불렀나  ③ 가드레일이 뭘 말하나
  ⇒ **근거 없이 나온 답을 «눈으로» 가려낼 수 있게 하는 것**이 이 화면의 목적이다.

  ⚠ FastAPI 는 두지 않았다 — 서버를 하나 더 띄우면 «어디서 틀렸나»를 두 곳에서 찾게 된다.
    Streamlit 이 파이썬을 그대로 부르므로 한 프로세스로 충분하다.

  실행:  .venv/Scripts/streamlit run 11_demo_app.py
"""
import json
import sys
import time

import streamlit as st

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))

st.set_page_config(page_title="모두몰 상담 에이전트", layout="wide")
st.title("모두몰 고객응대 에이전트 — 근거를 «함께» 본다")
st.caption("답변만 보면 틀린 답도 자연스럽다. 라우트·도구·가드레일을 옆에 둔다.")

with st.sidebar:
    st.header("설정")
    model = st.selectbox("모델", ["qwen3.5:2b", "qwen2.5:3b"], index=0)
    guide_v = st.selectbox("라우팅 지침", ["v1 (원본)", "v4 (SHIPPING 강화)"], index=1)
    use_fewshot = st.checkbox("few-shot 예시 붙이기", value=True)
    st.divider()
    st.caption("★키 없이 로컬 Ollama 로 돈다. 퍼실 기준선(0.94/56%)과 "
               "절대 비교는 성립하지 않는다 — 모델이 다르다.")
    st.caption("측정 결과: macro F1 0.556 → **0.816** (v4+fewshot)")


@st.cache_resource(show_spinner=False)
def boot(model_name):
    from langchain.tools import tool
    from langchain_ollama import ChatOllama
    from tools import TOOLS
    kw = dict(model=model_name, temperature=0, num_predict=700)
    if model_name.startswith("qwen3"):
        kw["reasoning"] = False
    lc = [tool(f) for f in TOOLS.values()]
    return ChatOllama(**kw).bind_tools(lc), ChatOllama(**kw), TOOLS


def build_guide(v, fewshot):
    import pandas as pd
    from config import BASE
    from prompts import ROUTE_GUIDE
    if v.startswith("v4"):
        from prompts_v4 import ROUTE_GUIDE_V4 as G
    else:
        G = ROUTE_GUIDE
    if not fewshot:
        return G
    inq = pd.read_csv(BASE / "customer_inquiries.csv")
    ans = pd.read_csv(BASE / "routing_answers.csv")
    fs = inq.merge(ans, on="qa_id")
    fs = fs[fs["split"] == "fewshot"]
    lines = []
    for r in ["ORDER_PLACE", "PRODUCT_INFO", "SHIPPING", "RETURN_REFUND", "OTHER"]:
        for _, row in fs[fs["route"] == r].head(2).iterrows():
            lines.append('문의: "%s" -> %s' % (row["question"], r))
    return G + "\n\n[판단 예시]\n" + "\n".join(lines)


EXAMPLES = [
    "캔버스화 배송비 얼마예요?",
    "혹시 배송비가 얼마인가요?",            # ★상품 미특정 → 되물어야 한다
    "환불 언제 되나요? O-1009 주문이요.",   # ★외부 채널 주문
    "홍대점 오늘 몇 시까지 하나요?",          # ★범위 밖
]
c1, c2 = st.columns([3, 1])
with c2:
    st.caption("예시")
    for e in EXAMPLES:
        if st.button(e, use_container_width=True, key=e):
            st.session_state["q"] = e
with c1:
    q = st.text_input("고객 문의", value=st.session_state.get("q", EXAMPLES[0]))
    go = st.button("보내기", type="primary")

if go and q.strip():
    from typing import Literal

    from langchain_core.messages import ToolMessage
    from pydantic import BaseModel, Field

    from context import build_answer_prompt
    from guardrail import guardrail

    picker, writer, TOOLS = boot(model)

    class RouteDecision(BaseModel):
        route: Literal["ORDER_PLACE", "PRODUCT_INFO", "SHIPPING",
                       "RETURN_REFUND", "OTHER"]
        confidence: float = Field(ge=0.0, le=1.0)
        reason: str

    t0 = time.perf_counter()
    # ① 분류
    with st.spinner("① 분류…"):
        try:
            d = writer.with_structured_output(RouteDecision).invoke(
                [("system", build_guide(guide_v, use_fewshot)),
                 ("human", "고객 문의: %s" % q)])
            route, conf, reason = d.route, d.confidence, d.reason
            route_err = ""
        except Exception as exc:
            route, conf, reason, route_err = "OTHER", 0.0, "", type(exc).__name__

    # ② 조회 — 2단계 분리(7,227자 프롬프트에서 도구 호출이 사라지는 문제 때문)
    PICK = ("너는 조회 담당이다. 조회가 꼭 필요할 때만 도구를 부른다. 답변은 쓰지 않는다.\n"
            "★어느 상품·어느 주문인지 특정할 수 없으면 아무 도구도 부르지 않는다.")
    used = {}
    with st.spinner("② 조회…"):
        msgs = [("system", PICK), ("human", q)]
        for _ in range(3):
            r = picker.invoke(msgs)
            calls = getattr(r, "tool_calls", []) or []
            if not calls:
                break
            msgs.append(r)
            for c in calls:
                fn = TOOLS.get(c["name"])
                out = fn(**c["args"]) if fn else {"error": "unknown"}
                used[c["name"]] = out
                msgs.append(ToolMessage(content=json.dumps(out, ensure_ascii=False),
                                        tool_call_id=c["id"], name=c["name"]))

    # ③ 답변
    with st.spinner("③ 답변…"):
        text = writer.invoke([("system", build_answer_prompt(q, route, used or None)),
                              ("human", q)]).content
    gr = guardrail(text, used)
    secs = time.perf_counter() - t0

    st.divider()
    a, b, c = st.columns(3)
    a.metric("① 라우트", route, "conf %.2f" % conf)
    b.metric("② 부른 도구", "%d개" % len(used), ", ".join(used) if used else "없음")
    c.metric("③ 가드레일", "통과" if gr["ok"] else "위반",
             "-" if gr["ok"] else gr["violations"][0]["type"])

    st.subheader("답변")
    if gr["ok"]:
        st.success(text)
    else:
        st.error(text)
        for v in gr["violations"]:
            st.warning("**%s** — %s" % (v["type"], v["detail"]))
        st.caption("★10강: 자연스러움으로는 이 오류를 잡을 수 없다. "
                   "출처 역추적이라는 «기계적» 검사만이 잡는다.")

    with st.expander("근거 펼쳐 보기", expanded=not gr["ok"]):
        st.caption("판단 근거 (reason)"); st.write(reason or "—")
        if route_err:
            st.caption("★분류 실패: %s — 이건 «오답»이 아니라 «형식 오류»다" % route_err)
        st.caption("조회 결과 — ★답변의 숫자는 여기 있는 것만 써야 한다")
        st.json(used if used else {"(조회 없음)": "상품·주문을 특정할 수 없으면 되묻는 것이 맞다"})
        st.caption("가드레일 상세")
        st.json({"답변 속 숫자": gr["numbers_in_answer"], "조회에서 온 숫자": gr["from_tools"]})
        st.caption("%.1f초" % secs)
