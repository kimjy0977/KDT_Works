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


RG_STAT = {"검사": 0, "빠진값 발견": 0, "재생성": 0, "재생성 후 채움": 0}


def missing_numbers(results, text):
    """★역방향 가드레일 — 「조회 결과에 있는데 답변이 «안 쓴» 값」을 낸다.

    14_reverse_guardrail.py 에서 «모범 답안»으로 오탐을 재고 좁힌 규칙을 그대로 쓴다.
    오탐 24/25 → 3/25 까지 줄인 것이 그 파일이고, 여기서는 «쓰기»만 한다.
    """
    import importlib.util as _u
    global _RG
    try:
        _RG
    except NameError:
        _sp = _u.spec_from_file_location("_rg", "14_reverse_guardrail.py")
        _m = _u.module_from_spec(_sp)
        _argv, sys.argv = sys.argv, ["x"]
        _sp.loader.exec_module(_m)
        sys.argv = _argv
        _RG = _m
    want = _RG.extract(results, "linked", text)
    return sorted(n for n in want if not _RG.in_answer(n, text))


def run_two_stage(pick_llm, write_llm, question, route, max_turns=MAX_TOOL_TURNS,
                  guide=PICK_GUIDE, reverse_guard=False):
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

    sys_prompt = build_answer_prompt(question, route, used or None)
    try:
        text = write_llm.invoke(
            [("system", sys_prompt), ("human", question)]).content
    except Exception as exc:
        return "", used, type(exc).__name__

    # ★역방향 가드레일 — 빠진 값이 있으면 «그 값을 찍어» 한 번만 다시 쓰게 한다.
    #   차단이 아니라 «재생성 1회»인 이유: 모범 답안으로 재도 오탐이 3/25 남는다.
    #   차단하면 그 3건에서 «맞는 답»을 막는다.
    if reverse_guard and used:
        RG_STAT["검사"] += 1
        miss = missing_numbers(used, text)
        if miss:
            RG_STAT["빠진값 발견"] += 1
            hint = ("%s[다시 쓰기] 조회 결과의 다음 값이 답변에 빠졌습니다: %s%s"
                    "이 값들이 «이 문의에 해당하는» 값이면 숫자를 그대로 넣어 다시 쓰십시오."
                    "%s해당하지 않는 값이면 넣지 마십시오 — 넣으면 틀린 안내가 됩니다."
                    % (chr(10), ", ".join(miss), chr(10), chr(10)))
            try:
                text2 = write_llm.invoke(
                    [("system", sys_prompt + hint), ("human", question)]).content
                if text2.strip():
                    RG_STAT["재생성"] += 1
                    if not missing_numbers(used, text2):
                        RG_STAT["재생성 후 채움"] += 1
                    text = text2
            except Exception:                       # noqa: BLE001
                pass                                # 재생성 실패면 1차 답변을 쓴다
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
    ap.add_argument("--search-v2", action="store_true",
                    help="★엔티티 링킹 개선판을 쓴다(12강 한계 ① · 13_search_v2.py)")
    ap.add_argument("--rules-v2", action="store_true",
                    help="★답변 규칙 v2 — must 누락 15건을 읽고 고친 것(prompts_answer_v2.py)")
    ap.add_argument("--reverse-guard", action="store_true",
                    help="★역방향 가드레일 — 빠진 값이 있으면 재생성 1회(14_reverse_guardrail.py)")
    ap.add_argument("--tool-turns", type=int, default=None,
                    help="★도구 호출 상한(기본 3). 신서연님 회고: 3→5 로 올리니 효과가 있었다")
    args = ap.parse_args()

    ensure_data()

    if args.rules_v2:
        # ★원본 prompts.py 는 «한 줄도» 고치지 않는다. 런타임에만 갈아 끼운다.
        #   context.build_answer_prompt 가 «함수 안»에서 import 하므로 이 대입이 닿는다.
        #   7b 측정(측정/21)의 must 누락 15건을 문장으로 읽어 셋으로 갈랐다:
        #     A 조회하고도 "○○원" 자리표시   B "확인해 보겠습니다"로 미룸
        #     C 같은 뜻 다른 말("품절"을 "재고 없음"으로)
        import prompts
        from prompts_answer_v2 import ANSWER_RULES_V2
        prompts.ANSWER_RULES = ANSWER_RULES_V2
        print("   ★답변 규칙을 v2 로 교체했다 (규칙 7·8·9 추가)")

    if args.search_v2:
        # ★원본 tools.py 는 «고치지 않고», 도구 목록에서 이 함수만 바꿔 끼운다.
        #   12강 한계 ①: search_product 가 토큰 «겹침»으로만 찾아
        #   「요일팬티 세트」와 「브라·팬티 세트」가 동점이 된다.
        #   13_search_v2.py 실측: 정확히 특정 15/18 → 16/18, 애매 1 → 0
        import importlib.util as _u
        _sp = _u.spec_from_file_location("_s2", "13_search_v2.py")
        _m = _u.module_from_spec(_sp)
        _argv, sys.argv = sys.argv, ["x"]
        _sp.loader.exec_module(_m)
        sys.argv = _argv
        _fn = _m.search_v2
        _fn.__name__ = "search_product"        # ★도구 «이름»은 그대로여야 한다
        _fn.__doc__ = TOOLS["search_product"].__doc__
        TOOLS["search_product"] = _fn
        globals()["LC_TOOLS"] = [tool(f) for f in TOOLS.values()]
        print("   ★search_product 를 v2(가중 점수)로 교체했다")

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
                guide=PICK_GUIDE_ASK if args.ask_first else PICK_GUIDE,
                reverse_guard=args.reverse_guard,
                max_turns=args.tool_turns or MAX_TOOL_TURNS)
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
    # ★답변 «전문»을 남긴다 — 로그는 223자에서 잘린다.
    #   재현율(빠진 값을 «실제로» 잡는가)을 나중에 재려면 전문이 있어야 한다.
    #   1차 측정에서 이걸 안 남겨 「효과 0」의 원인을 바로 못 갈랐다.
    import pathlib
    _csv = pathlib.Path("측정") / ("답변전문_%s_%s.csv" % (
        args.model.replace(":", ""), "rg" if args.reverse_guard else "base"))
    res.to_csv(_csv, index=False, encoding="utf-8-sig")
    print()
    print("   답변 전문 → %s" % _csv)

    if args.reverse_guard:
        print()
        print("[★역방향 가드레일 발동 내역]")
        for k, v in RG_STAT.items():
            print("   %-14s %d" % (k, v))
        print("   ※ «검사» 는 도구 결과가 있었던 건수다. 도구를 안 부르면 검사 자체가 없다.")

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
