# -*- coding: utf-8 -*-
"""★7강 「더 해보기」 1 + 10강 「더 해보기」 2 — 컨텍스트를 깎아 보고, 위반을 «집계»한다.

7강 더 해보기 1:
  「build_context 에 include_appendix 인자를 만들어 부록 A·B 를 넣은 컨텍스트와
   넣지 않은 컨텍스트로 같은 문의에 답해 비교합니다.」

★그런데 오늘 실측이 이 실험에 «다른 의미»를 준다 —
  7,227자 프롬프트에서 **도구 호출이 사라졌다**(tool_calls 0).
  ⇒ 이제 질문은 「부록을 넣을까 뺄까」가 아니라 **「어디까지 깎아야 도구를 부르나」**다.

10강 더 해보기 2:
  「위반 유형·질문·차단된 답변을 CSV 로 append 하고, 어떤 라우트에서 위반이 가장 많은지
   집계합니다. ⇒ 어느 라우트의 프롬프트를 먼저 고쳐야 하는지 «데이터로» 판단할 수 있습니다.」

  python 12_context_ablation.py            # 컨텍스트 길이 → 도구 호출 (모델 호출 少)
  python 12_context_ablation.py --guard    # 가드레일 위반 집계 (모델 호출 0)
"""
import argparse
import csv
import io
import json
import re
import sys
import time
from pathlib import Path

import pandas as pd

from config import BASE, ROUTES, ensure_data

sys.stdout.reconfigure(encoding="utf-8")
LOG = Path(__file__).parent / "측정"


def ctx_sizes():
    """라우트별 컨텍스트가 실제로 몇 자인지 — 7강이 «쪼갠» 결과를 잰다."""
    from context import build_answer_prompt
    raw = (BASE / "policy_modumall.md").read_text(encoding="utf-8")
    rows = []
    for r in ROUTES:
        p = build_answer_prompt("배송비 얼마예요?", r)
        rows.append({"route": r, "chars": len(p)})
    return raw, rows


def trim(prompt, keep):
    """★컨텍스트를 «앞에서부터» keep 자만 남긴다. 규칙 부분이 앞에 있으므로 뒤(매뉴얼)가 잘린다."""
    return prompt[:keep]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="컨텍스트 깎기 + 위반 집계")
    ap.add_argument("--guard", action="store_true", help="가드레일 위반 집계만(모델 호출 0)")
    ap.add_argument("--model", default="qwen3.5:2b")
    args = ap.parse_args()
    ensure_data()

    # ─────────── 10강 더해보기 2 — 위반을 «집계»한다 (모델 호출 0) ───────────
    if args.guard:
        from evaluate import AUTO_ACTIONS, load_cases
        from guardrail import guardrail
        print("=== 10강 더해보기 2 — 가드레일 위반 집계 ===")
        print("   「어느 라우트의 프롬프트를 «먼저» 고쳐야 하는지 데이터로 판단한다」")
        print()
        cases = [c for c in load_cases() if c["expect"]["action"] in AUTO_ACTIONS]
        rows = []
        for c in cases:
            # ★모범답안에 «조회 결과 없이» 걸어 본다 —
            #   걸리는 숫자가 곧 「그 라우트에서 조회가 꼭 필요한 값」이다
            g = guardrail(c["expect"]["reference"], {})
            for v in g["violations"]:
                rows.append({"route": c["route"], "conv": c["conv_id"],
                             "type": v["type"], "detail": v["detail"][:70],
                             "answer": c["expect"]["reference"][:60]})
        if not rows:
            print("   위반 0건")
            sys.exit(0)
        df = pd.DataFrame(rows)
        out = LOG / "17_가드레일위반_로그_20260916.csv"
        df.to_csv(out, index=False, encoding="utf-8-sig")
        print("   위반 %d건 · 로그 → %s" % (len(df), out.name))
        print()
        print("[★라우트별 — 어디를 먼저 고칠까]")
        print(df["route"].value_counts().to_string())
        print()
        print("[위반 유형별]")
        print(df["type"].value_counts().to_string())
        print()
        print("[상세]")
        for _, r in df.iterrows():
            print("   %-14s %-7s %s" % (r["route"], r["conv"], r["detail"]))
        print()
        print("   ⇒ ★SHIPPING 에 몰려 있다면 그 라우트의 컨텍스트에")
        print("     «조회해야 하는 값»이 가장 많다는 뜻이다 — 무료배송 기준액이 거기 있다.")
        print("   ⇒ 이건 «답변이 틀렸다»가 아니라 «그 숫자는 조회 없이 못 쓴다»는 지도다.")
        sys.exit(0)

    # ─────────── 7강 더해보기 1 — 컨텍스트를 깎으면 도구가 돌아오나 ───────────
    from langchain.tools import tool
    from langchain_ollama import ChatOllama

    from context import build_answer_prompt
    from tools import TOOLS

    raw, rows = ctx_sizes()
    print("=== 7강 더해보기 1 — 컨텍스트 길이와 «도구 호출» ===")
    print("   매뉴얼 전문 %d자 → 라우트별로 쪼갠 결과:" % len(raw))
    for r in rows:
        print("      %-14s %6d자" % (r["route"], r["chars"]))
    print()
    print("   ★7강은 「전문을 넣지 말고 쪼개라」고 했다. 쪼갠 게 위 숫자다.")
    print("     그런데 2B 모델은 이 길이에서도 «도구 호출을 잃는다».")
    print("     ⇒ 질문이 바뀐다: 「어디까지 깎아야 도구를 부르나」")
    print()

    kw = dict(model=args.model, temperature=0, num_predict=700)
    if args.model.startswith("qwen3"):
        kw["reasoning"] = False
    LC = [tool(f) for f in TOOLS.values()]
    llm = ChatOllama(**kw).bind_tools(LC)

    q = "캔버스화 배송비 얼마예요?"
    full = build_answer_prompt(q, "SHIPPING")
    print("=== 잘라 가며 «도구를 부르는 길이»를 찾는다 ===")
    print("   문의: %s" % q)
    print()
    print("   %8s %6s  %s" % ("길이", "초", "부른 도구"))
    for keep in [len(full), 4000, 2000, 1000, 500, 200, 80]:
        p = trim(full, keep)
        t0 = time.perf_counter()
        try:
            r = llm.invoke([("system", p), ("human", q)])
            tc = [c["name"] for c in (getattr(r, "tool_calls", []) or [])]
        except Exception as exc:
            tc = ["ERR:" + type(exc).__name__]
        mark = "  ★" if tc and not tc[0].startswith("ERR") else ""
        print("   %8d %5.1f초  %s%s" % (keep, time.perf_counter() - t0,
                                       ", ".join(tc) if tc else "(없음)", mark))
    print()
    print("   ⇒ ★도구를 부르기 시작하는 «경계»가 곧 이 모델의 컨텍스트 한계다.")
    print("     7강의 「쪼개라」는 조언은 옳지만, «얼마나» 쪼개야 하는지는 모델이 정한다.")
