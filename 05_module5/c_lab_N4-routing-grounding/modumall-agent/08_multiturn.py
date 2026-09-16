# -*- coding: utf-8 -*-
"""★12강 「더 해보기」 1 — 멀티턴 상태 관리. (키 불필요 · Ollama)

11강이 «일부러 미뤄 둔» 제약을 푼다:
  「정답셋은 34개 대화 112턴짜리인데, 오늘 채점에는 각 대화의 첫 턴 34건만 씁니다.
   뒤쪽 턴은 앞 턴의 맥락을 알아야 이해됩니다. … 문맥을 어떻게 넘길지는 «설계 선택지»가
   여럿이고, 그 선택이 점수를 지배해 버립니다.」

12강이 한계로 적은 것:
  「멀티턴 상태 관리가 «단순»합니다. 고객 발화를 «이어 붙여» 넘기는 방식이라,
   대화가 길어지면 앞 맥락이 희석됩니다.
   **메시지 목록을 «역할까지 살려» 넘기는 것이 정석**이고, 체크포인터에 그 자리를 마련해 두었습니다.」

⇒ 그래서 **문맥 전달 3방식을 같은 자로 잰다.** 「정석이 정말 나은가」를 숫자로 본다.

    none     현재 턴만          ← 기준선. 후속 턴은 맥락 없이 답해야 한다
    concat   고객 발화 이어 붙이기  ← 12강이 「단순하다」고 한 그 방식
    ★msgs    메시지 목록 (role 유지) ← 12강이 「정석」이라 한 방식 · checkpointer

  ★채점 대상도 34 → 56 턴으로 넓힌다(첫 턴 34 + 후속 22).
    후속 턴을 따로 집계해야 «맥락 전달이 실제로 듣는지»가 보인다.

  python 08_multiturn.py --mode msgs
  python 08_multiturn.py --mode all      # 세 방식을 차례로
"""
import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from langchain.tools import tool
from langchain_ollama import ChatOllama
from langgraph.errors import GraphRecursionError
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from config import BASE, MAX_TOOL_TURNS, ensure_data
from context import build_answer_prompt
from evaluate import AUTO_ACTIONS, score_turn
from tools import TOOLS

sys.stdout.reconfigure(encoding="utf-8")

LC_TOOLS = [tool(fn) for fn in TOOLS.values()]
ASK_PAT = r"\?|주시겠|알려주|말씀해"

# 2단계 분리 — 7,227자 프롬프트에서 2B 모델이 도구 호출을 잃는다(03_ollama_answer.py 실측)
PICK_GUIDE = """\
너는 쇼핑몰 상담 시스템의 조회 담당이다. 조회가 «꼭 필요할 때만» 도구를 부른다.
답변 문장은 쓰지 않는다.

★먼저 판단한다 — 고객이 «어느 상품·어느 주문»인지 «대화 전체»에서 특정할 수 있는가?
- 특정할 수 없으면 **아무 도구도 부르지 않는다.**
- 특정할 수 있으면: 상품명이면 search_product 로 ID 를 찾고 필요한 조회를 잇는다.
  주문번호(O-0000)가 보이면 그 번호로 주문·반품을 조회한다.
★앞 턴에서 고객이 말한 상품·주문번호도 «지금 아는 것»으로 친다.
"""


def load_multiturn():
    """★expect 가 붙은 턴을 «전부» 뽑는다 — 앞선 대화도 함께 들고 온다."""
    g = json.loads((BASE / "answer_goldenset_multiturn.json").read_text(encoding="utf-8"))
    out = []
    for c in g["conversations"]:
        route = c["route"].split("→")[-1].strip()
        hist = []                      # [(role, text)] — 지금까지의 대화
        idx = 0
        for t in c["turns"]:
            if t["role"] == "customer":
                hist.append(("human", t["text"]))
                continue
            if t.get("expect") and t["expect"]["action"] in AUTO_ACTIONS:
                q = next((x for r, x in reversed(hist) if r == "human"), "")
                out.append({"conv_id": c["conv_id"], "route": route, "question": q,
                            "history": list(hist), "expect": t["expect"],
                            "turn_idx": idx, "is_first": idx == 0})
                idx += 1
            if t.get("text"):
                hist.append(("ai", t["text"]))
    return out


def build_context(case, mode):
    """★문맥을 어떻게 넘기는가 — 세 방식. 11강이 「선택이 점수를 지배한다」고 한 자리."""
    if mode == "none":
        return [("human", case["question"])]
    if mode == "concat":
        # 12강이 「단순하다」고 한 방식 — 고객 발화만 이어 붙인다
        says = [x for r, x in case["history"] if r == "human"]
        return [("human", " / ".join(says))]
    # ★msgs — 역할을 살려 그대로 넘긴다(12강의 «정석»)
    return list(case["history"]) or [("human", case["question"])]


def make_picker(model):
    kw = dict(model=model, temperature=0, num_predict=700)
    if model.startswith("qwen3"):
        kw["reasoning"] = False
    llm = ChatOllama(**kw).bind_tools(LC_TOOLS)
    g = StateGraph(dict)
    # 간단한 루프 대신 직접 돌린다 — 상태를 우리가 들고 있기 때문이다
    return llm


def run_case(picker, writer, case, mode, max_turns=MAX_TOOL_TURNS):
    msgs = [("system", PICK_GUIDE)] + build_context(case, mode)
    used = {}
    try:
        for _ in range(max_turns):
            r = picker.invoke(msgs)
            calls = getattr(r, "tool_calls", []) or []
            if not calls:
                break
            msgs.append(r)
            for c in calls:
                fn = TOOLS.get(c["name"])
                if not fn:
                    continue
                try:
                    out = fn(**c["args"])
                except Exception as exc:
                    out = {"error": str(exc)[:80]}
                used[c["name"]] = out
                from langchain_core.messages import ToolMessage
                msgs.append(ToolMessage(content=json.dumps(out, ensure_ascii=False),
                                        tool_call_id=c["id"], name=c["name"]))
    except Exception as exc:
        return "", {}, type(exc).__name__

    ctx = build_context(case, mode)
    try:
        text = writer.invoke(
            [("system", build_answer_prompt(case["question"], case["route"], used or None))]
            + ctx).content
    except Exception as exc:
        return "", used, type(exc).__name__
    return text, used, ""


def judge(text, results):
    if results.get("get_order_status", {}).get("is_external_channel"):
        return "OUT_OF_SCOPE"
    if not results and re.search(ASK_PAT, text):
        return "ASK"
    return "ANSWER"


def evaluate(cases, model, mode, workers=3):
    kw = dict(model=model, temperature=0, num_predict=700)
    if model.startswith("qwen3"):
        kw["reasoning"] = False
    picker = ChatOllama(**kw).bind_tools(LC_TOOLS)
    writer = ChatOllama(**kw)

    t0 = time.perf_counter()

    def one(c):
        text, used, err = run_case(picker, writer, c, mode)
        act = judge(text, used)
        ok, fails = score_turn(c["expect"], text, list(used), act)
        return {"conv": c["conv_id"], "turn": c["turn_idx"], "첫턴": c["is_first"],
                "기대": c["expect"]["action"], "실제": act, "ok": ok, "err": err,
                "fails": "; ".join(fails), "tools": ",".join(used), "answer": text}

    with ThreadPoolExecutor(max_workers=workers) as ex:
        rows = list(ex.map(one, cases))
    secs = time.perf_counter() - t0
    res = pd.DataFrame(rows)

    first = res[res["첫턴"]]
    later = res[~res["첫턴"]]
    print()
    print("── 문맥 전달 = %s ──  %.0f초" % (mode, secs))
    print("   전체   %2d/%2d (%4.1f%%)   ★호출 실패 %d건"
          % (res["ok"].sum(), len(res), 100 * res["ok"].mean(), (res["err"] != "").sum()))
    print("   첫 턴  %2d/%2d (%4.1f%%)   ← 맥락이 필요 없는 턴"
          % (first["ok"].sum(), len(first), 100 * first["ok"].mean()))
    print("   ★후속  %2d/%2d (%4.1f%%)   ← 여기가 맥락 전달의 «진짜» 시험대"
          % (later["ok"].sum(), len(later), 100 * later["ok"].mean()))
    kinds = [f.split(":")[0] for s in res.loc[~res["ok"], "fails"] for f in s.split("; ") if f]
    if kinds:
        print("   실패 유형: %s" % pd.Series(kinds).value_counts().to_dict())
    return {"mode": mode, "all": res["ok"].mean(), "first": first["ok"].mean(),
            "later": later["ok"].mean(), "n": len(res), "n_later": len(later), "res": res}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="멀티턴 상태 관리 (12강 더해보기 1)")
    ap.add_argument("--model", default="qwen3.5:2b")
    ap.add_argument("--mode", choices=["none", "concat", "msgs", "all"], default="all")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    ensure_data()
    cases = load_multiturn()
    if args.limit:
        cases = cases[:args.limit]
    n_first = sum(1 for c in cases if c["is_first"])
    print("=== 멀티턴 채점 — 11강이 미뤄 둔 제약을 푼다 ===")
    print("   채점 대상 %d턴 (첫 턴 %d · ★후속 %d)" % (len(cases), n_first, len(cases) - n_first))
    print("   ※ 11강은 첫 턴 34건만 썼다. 후속 턴이 «맥락 전달»의 시험대다.")

    modes = ["none", "concat", "msgs"] if args.mode == "all" else [args.mode]
    outs = [evaluate(cases, args.model, m, args.workers) for m in modes]

    print()
    print("══ 요약 ══")
    print("   %-8s %10s %10s %10s" % ("문맥전달", "전체", "첫 턴", "★후속턴"))
    for o in outs:
        print("   %-8s %9.1f%% %9.1f%% %9.1f%%"
              % (o["mode"], 100 * o["all"], 100 * o["first"], 100 * o["later"]))
    if len(outs) > 1:
        base = outs[0]["later"]
        print()
        print("   ⇒ 후속 턴 기준, 맥락을 넘기면 %+.1f%%p (concat) · %+.1f%%p (msgs)"
              % (100 * (outs[1]["later"] - base), 100 * (outs[-1]["later"] - base)))
        print("     12강: 「메시지 목록을 «역할까지 살려» 넘기는 것이 정석」 — 숫자로 확인한다.")
