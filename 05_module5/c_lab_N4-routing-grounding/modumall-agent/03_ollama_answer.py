# -*- coding: utf-8 -*-
"""★② 1턴 답변 통과율을 «키 없이» 잰다 — 도구 호출까지 Ollama 로.

키가 필요한 자리는 생각보다 «작다»
  ② 지표에서 OpenAI 키를 요구하는 것은 **「모델이 답을 쓰는 단계」 하나뿐**이다.
  조회 도구 9개 · 매뉴얼 쪼개기 · 가드레일 · 채점기는 전부 **순수 코드**라 키 없이 돈다.
  그리고 `qwen3.5:2b` 는 **tools 를 지원**한다(Ollama capabilities).
  ⇒ 그 한 자리에 Ollama 를 꽂으면 ② 도 잴 수 있다.

  ⚠ 절대 점수는 퍼실 기준선 56%(18/32) 와 «비교할 수 없다» — 모델이 다르다.
     ①에서 한 것과 같다. 비교 가능한 것은 **같은 모델 안에서의 전후**다.

  ⛔ `answer.py` 는 모듈 최상위에서 `init_chat_model` 을 부르므로
     **import 만으로 키를 요구한다.** 그래서 그 파일을 건드리지 않고 여기서 다시 세운다.

  python 03_ollama_answer.py                  # 32건 전체
  python 03_ollama_answer.py --limit 6        # 흐름 확인
  python 03_ollama_answer.py --guardrail      # 가드레일도 함께 본다
"""
import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Annotated, TypedDict

import pandas as pd
from langchain.tools import tool
from langchain_ollama import ChatOllama
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from config import MAX_TOOL_TURNS, ensure_data
from context import build_answer_prompt
from evaluate import AUTO_ACTIONS, load_cases, score_turn
from guardrail import guardrail
from tools import TOOLS

sys.stdout.reconfigure(encoding="utf-8")

LC_TOOLS = [tool(fn) for fn in TOOLS.values()]
ASK_PAT = r"\?|주시겠|알려주|말씀해"


class ToolState(TypedDict, total=False):
    messages: Annotated[list, add_messages]


def build_app(model, num_predict=700):
    """answer.py 의 그래프를 «그대로» 세우되 모델만 Ollama 로 바꾼다."""
    kw = dict(model=model, temperature=0, num_predict=num_predict)
    if model.startswith("qwen3"):
        kw["reasoning"] = False        # ①에서 20/20 실패를 겪은 그 설정
    llm = ChatOllama(**kw).bind_tools(LC_TOOLS)

    def agent(state):
        return {"messages": [llm.invoke(state["messages"])]}

    g = StateGraph(ToolState)
    g.add_node("agent", agent)
    g.add_node("tools", ToolNode(LC_TOOLS))
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", tools_condition)
    g.add_edge("tools", "agent")
    return g.compile()


def answer_with_tools(app, question, route, max_turns=MAX_TOOL_TURNS):
    init = {"messages": [("system", build_answer_prompt(question, route)),
                         ("human", question)]}
    try:
        out = app.invoke(init, {"recursion_limit": 2 * max_turns + 1})
    except GraphRecursionError:
        return "정확한 확인을 위해 상담원에게 연결해 드리겠습니다.", {}, "RECURSION"
    except Exception as exc:
        # ★실패를 «오답»으로 뭉뚱그리지 않는다 — ①에서 이 설계가 값을 했다
        return "", {}, type(exc).__name__
    used = {}
    for m in out["messages"]:
        if getattr(m, "name", None) in TOOLS:
            try:
                used[m.name] = json.loads(m.content)
            except json.JSONDecodeError:
                used[m.name] = m.content
    return out["messages"][-1].content, used, ""


# ★2단계 분리 — 7,227자 프롬프트에서 2B 모델이 도구 호출을 «잃는다»(실측).
#   1단계: «짧은» 지침으로 도구만 고르게 한다
#   2단계: 조회 결과 + 매뉴얼로 답변을 쓰게 한다 (도구 없이)
#   ⇒ 이것이 8강 방식이다. 9강의 «모델이 스스로 조회» 는 큰 모델을 전제한다.
PICK_GUIDE = """너는 쇼핑몰 상담 시스템의 조회 담당이다. 고객 문의에 답하려면 어떤 값을 조회해야 하는지 판단해
필요한 도구를 «전부» 부른다. 답변 문장은 쓰지 않는다.

- 상품을 이름으로 말했으면 먼저 search_product 로 상품 ID 를 찾는다.
- 주문번호(O-0000)가 보이면 그 번호로 주문·반품 조회를 부른다.
- 배송비·무료배송이면 get_shipping_policy, 반품 규정이면 get_return_policy 를 부른다.
- 상품도 주문도 특정할 수 없으면 아무 도구도 부르지 않는다.
- ★애매하면 «더» 부른다. 덜 부르는 것보다 낫다.
"""

# ★시도 #6 — 위 지침의 마지막 줄이 ASK 8건을 «전멸»시켰다(0/8).
#   「애매하면 더 부른다」를 빼고 「특정 못 하면 부르지 마라」를 앞으로 올린다.
#   ⇒ 12강의 교환 관계를 «반대 방향»에서 확인하는 것이다:
#     「검색을 적극적으로 시키자 조회 성공률은 올랐지만,
#      되물어야 할 문의에 답해 버리는 건수도 함께 늘었다」
PICK_GUIDE_ASK = """너는 쇼핑몰 상담 시스템의 조회 담당이다. 조회가 «꼭 필요할 때만» 도구를 부른다.
답변 문장은 쓰지 않는다.

★먼저 판단한다 — 고객이 «어느 상품·어느 주문»인지 문장에서 특정할 수 있는가?
- 특정할 수 없으면 **아무 도구도 부르지 않는다.** 그게 정답이다.
  예) "배송비 얼마예요?" 처럼 상품명이 없는 문의 → 아무것도 부르지 않는다.
- 특정할 수 있을 때만 부른다:
  · 상품을 이름으로 말했으면 search_product 로 ID 를 찾고, 필요한 조회를 잇는다.
  · 주문번호(O-0000)가 보이면 그 번호로 주문·반품을 조회한다.

★부를지 말지 헷갈리면 «부르지 않는다». 되묻는 편이 틀린 값을 주는 것보다 낫다.
"""


def run_two_stage(pick_llm, write_llm, question, route, max_turns=MAX_TOOL_TURNS,
                  guide=PICK_GUIDE):
    """1단계 도구 선택(짧은 지침) → 2단계 답변 작성(매뉴얼 + 조회결과)."""
    g = StateGraph(ToolState)
    g.add_node("agent", lambda st: {"messages": [pick_llm.invoke(st["messages"])]})
    g.add_node("tools", ToolNode(LC_TOOLS))
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", tools_condition)
    g.add_edge("tools", "agent")
    picker = g.compile()

    try:
        out = picker.invoke({"messages": [("system", guide), ("human", question)]},
                            {"recursion_limit": 2 * max_turns + 1})
    except GraphRecursionError:
        out = None
    except Exception as exc:
        return "", {}, type(exc).__name__

    used = {}
    if out:
        for m in out["messages"]:
            if getattr(m, "name", None) in TOOLS:
                try:
                    used[m.name] = json.loads(m.content)
                except json.JSONDecodeError:
                    used[m.name] = m.content

    try:
        text = write_llm.invoke(
            [("system", build_answer_prompt(question, route, used or None)),
             ("human", question)]).content
    except Exception as exc:
        return "", used, type(exc).__name__
    return text, used, ""


def judge(text, results):
    """evaluate.py run_case() 의 판정 로직 그대로."""
    if results.get("get_order_status", {}).get("is_external_channel"):
        return "OUT_OF_SCOPE"
    if not results and re.search(ASK_PAT, text):
        return "ASK"
    return "ANSWER"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="② 1턴 답변 통과율 — Ollama 판")
    ap.add_argument("--model", default="qwen3.5:2b")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--guardrail", action="store_true", help="가드레일 결과도 집계")
    ap.add_argument("--two-stage", action="store_true",
                    help="★도구 선택과 답변 작성을 «분리»한다(8강 방식)")
    ap.add_argument("--ask-first", action="store_true",
                    help="★조회를 «덜» 적극적으로 — ASK 를 살리는 지침(시도 #6)")
    args = ap.parse_args()

    ensure_data()
    app = build_app(args.model)
    cases = [c for c in load_cases() if c["expect"]["action"] in AUTO_ACTIONS]
    if args.limit:
        cases = cases[:args.limit]

    print("모델 %s · 대상 %d건" % (args.model, len(cases)))
    print("⚠ 퍼실 기준선 56%(18/32) 는 gpt-5.6-terra 다. 절대 비교하지 않는다.")
    print()

    t0 = time.perf_counter()

    if args.two_stage:
        kw = dict(model=args.model, temperature=0, num_predict=700)
        if args.model.startswith("qwen3"):
            kw["reasoning"] = False
        _pick = ChatOllama(**kw).bind_tools(LC_TOOLS)
        _write = ChatOllama(**kw)

    def run(c):
        if args.two_stage:
            text, results, err = run_two_stage(
                _pick, _write, c["question"], c["route"],
                guide=PICK_GUIDE_ASK if args.ask_first else PICK_GUIDE)
        else:
            text, results, err = answer_with_tools(app, c["question"], c["route"])
        act = judge(text, results)
        ok, fails = score_turn(c["expect"], text, list(results), act)
        row = {"conv": c["conv_id"], "기대": c["expect"]["action"], "실제": act,
               "ok": ok, "err": err, "fails": "; ".join(fails), "answer": text,
               "tools": ",".join(results)}
        if args.guardrail:
            gr = guardrail(text, results)
            row["가드레일"] = "ok" if gr["ok"] else gr["violations"][0]["type"]
        return row

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        rows = list(ex.map(run, cases))
    secs = time.perf_counter() - t0

    res = pd.DataFrame(rows)
    errs = res[res["err"] != ""]
    print("== ② 1턴 답변 ==")
    print("   %.1f초 (건당 %.1f초)" % (secs, secs / len(res)))
    print("   ★호출 실패 %d건 — 이건 «오답»이 아니라 «실행 실패»다" % len(errs))
    if len(errs):
        print("      %s" % errs["err"].value_counts().to_dict())
    print("   ⇒ 통과 %d / %d  (%.1f%%)" % (res["ok"].sum(), len(res), 100 * res["ok"].mean()))
    print()
    print("[기대 행동별]")
    print(res.groupby("기대")["ok"].agg(["count", "sum", "mean"])
          .rename(columns={"count": "건수", "sum": "통과", "mean": "통과율"}).to_string())
    print()
    print("[행동 판정 혼동] 행=기대, 열=실제")
    print(pd.crosstab(res["기대"], res["실제"]).to_string())
    print()
    kinds = [f.split(":")[0] for s in res.loc[~res["ok"], "fails"] for f in s.split("; ") if f]
    print("[실패 유형] — ★tools 미호출이면 must 누락이 따라온다(11강). 원인은 tools 쪽이다")
    print(pd.Series(kinds).value_counts().to_string() if kinds else "  없음")
    if args.guardrail:
        print()
        print("[가드레일]")
        print(res["가드레일"].value_counts().to_string())
    print()
    print("[실패 사례]")
    for _, r in res[~res["ok"]].iterrows():
        print("  %s 기대=%-13s 실제=%-13s %s" % (r["conv"], r["기대"], r["실제"], r["fails"][:74]))
        print("      도구: %s" % (r["tools"] or "(없음)"))
        print("      답변: %s" % r["answer"][:88].replace("\n", " "))
