# -*- coding: utf-8 -*-
"""★6강의 마지막 실습 — 어려운 케이스 72건 · 임계값 교환 관계. (키 불필요 · Ollama)

왜 따로 만드나
  `evaluate.py` 는 `hard_cases.csv` 를 **아예 쓰지 않는다.** 평가셋 120건만 잰다.
  그런데 6강은 이 72건으로 **「확신도가 신호 구실을 하는가」**를 확인하라고 한다.
  그게 확인되지 않으면 임계값 0.5 라는 값에 근거가 없다.

  ⚠ 그리고 `CONF_THRESHOLD` 는 **손잡이가 끊겨 있다** —
     `router.py:16` 이 config 에서 가져오고 `router.py:50` 이 같은 이름으로 덮어쓴다.
     그래서 여기서는 **판정을 직접 계산한다.** 원본 파일은 건드리지 않는다.

  ★6강이 강조한 것 — **임계값을 바꿀 때 모델을 다시 부르지 않는다.**
    분류는 이미 끝난 일이므로 받아 둔 결과를 재사용하고 판정만 다시 한다.
    「임계값 다섯 개를 보려고 600번 호출할 이유가 없다.」

  python 04_hard_cases.py                 # hard 72건
  python 04_hard_cases.py --guide v4 --fewshot
  python 04_hard_cases.py --eval          # 평가셋으로 자동화율 교환 관계
"""
import argparse
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from typing import Literal

import pandas as pd
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from config import BASE, ensure_data
from prompts import ROUTE_GUIDE

sys.stdout.reconfigure(encoding="utf-8")


class RouteDecision(BaseModel):
    route: Literal["ORDER_PLACE", "PRODUCT_INFO", "SHIPPING",
                   "RETURN_REFUND", "OTHER"] = Field(description="5개 값 중 하나.")
    confidence: float = Field(ge=0.0, le=1.0, description="애매하면 0.5 미만으로.")
    reason: str = Field(description="판단 근거 한 문장.")


def make_classifier(model, guide):
    kw = dict(model=model, temperature=0, num_predict=400)
    if model.startswith("qwen3"):
        kw["reasoning"] = False
    chain = ChatOllama(**kw).with_structured_output(RouteDecision)

    def f(q):
        try:
            d = chain.invoke([("system", guide), ("human", "고객 문의: %s" % q)])
            return d.route, d.confidence
        except Exception:
            return "_PARSE_FAIL", 0.0

    return f


def gate(route, conf, threshold):
    """router.py gate() 와 같은 판정 — 단, 임계값을 «인자로» 받는다."""
    if conf < threshold:
        return "ESCALATE"
    if route == "OTHER":
        return "OUT_OF_SCOPE"
    return "HANDLE"


def automation_report(states, gold, thresholds=(0.0, 0.3, 0.5, 0.7, 0.9)):
    """★모델을 다시 부르지 않는다 — 받아 둔 결과로 판정만 다시 한다."""
    print()
    print("[임계값 교환 관계] — 자동화율을 올리면 처리건 정확도가 떨어진다")
    print("   %6s %9s %14s %6s" % ("임계값", "자동화율", "처리건 정확도", "이관"))
    for th in thresholds:
        acts = [gate(r, c, th) for r, c in states]
        handled = [(r, g) for (r, c), g, a in zip(states, gold, acts) if a == "HANDLE"]
        auto = len(handled) / len(states)
        acc = (sum(1 for r, g in handled if r == g) / len(handled)) if handled else 0.0
        esc = sum(1 for a in acts if a == "ESCALATE")
        print("   %6.1f %8.1f%% %13.1f%% %6d" % (th, 100 * auto, 100 * acc, esc))
    print("   ⇒ 잘못된 환불 안내가 «금전 분쟁»이 되는 도메인이면 이관을 감수하는 쪽이 낫다(6강).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="어려운 케이스 72건 · 임계값 교환 관계")
    ap.add_argument("--model", default="qwen3.5:2b")
    ap.add_argument("--guide", choices=["v1", "v2", "v3", "v4"], default="v1")
    ap.add_argument("--fewshot", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--eval", action="store_true", help="평가셋 120건으로 교환 관계를 본다")
    args = ap.parse_args()

    ensure_data()
    if args.guide == "v2":
        from prompts_v2 import ROUTE_GUIDE_V2 as G
    elif args.guide == "v3":
        from prompts_v3 import ROUTE_GUIDE_V3 as G
    elif args.guide == "v4":
        from prompts_v4 import ROUTE_GUIDE_V4 as G
    else:
        G = ROUTE_GUIDE
    guide = G
    if args.fewshot:
        inq = pd.read_csv(BASE / "customer_inquiries.csv")
        ans = pd.read_csv(BASE / "routing_answers.csv")
        fs = inq.merge(ans, on="qa_id")
        fs = fs[fs["split"] == "fewshot"]
        lines = []
        for r in ["ORDER_PLACE", "PRODUCT_INFO", "SHIPPING", "RETURN_REFUND", "OTHER"]:
            for _, row in fs[fs["route"] == r].head(2).iterrows():
                lines.append('문의: "%s" -> %s' % (row["question"], r))
        guide = G + "\n\n[판단 예시 — 실제 상담 기록에서 뽑은 것]\n" + "\n".join(lines)

    tag = args.guide + (" + fewshot" if args.fewshot else "")
    clf = make_classifier(args.model, guide)
    print("모델 %s · 지침 %s (%d자)" % (args.model, tag, len(guide)))

    if args.eval:
        inq = pd.read_csv(BASE / "customer_inquiries.csv")
        ans = pd.read_csv(BASE / "routing_answers.csv")
        d = inq.merge(ans, on="qa_id")
        d = d[d["split"] == "eval"].reset_index(drop=True)
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            st = list(ex.map(clf, d["question"].tolist()))
        print("평가셋 %d건 · %.1f초" % (len(d), time.perf_counter() - t0))
        automation_report(st, d["route"].tolist())
        sys.exit(0)

    hard = pd.read_csv(BASE / "hard_cases.csv")
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        st = list(ex.map(clf, hard["question"].tolist()))
    secs = time.perf_counter() - t0

    hard["pred"] = [s[0] for s in st]
    hard["conf"] = [s[1] for s in st]
    hard["action"] = [gate(r, c, 0.5) for r, c in st]
    fails = (hard["pred"] == "_PARSE_FAIL").sum()

    print("어려운 케이스 %d건 · %.1f초 · ★형식 실패 %d건" % (len(hard), secs, fails))
    print()
    print("[유형별 분포]")
    print(hard["hard_type"].value_counts().to_string())
    print()
    print("[★유형별 확신도 평균] — 6강: 세 덩어리로 갈리는 것이 관찰의 핵심")
    print(hard.groupby("hard_type")["conf"].mean().round(2).sort_values().to_string())
    print()
    print("[유형별 처리]")
    print(pd.crosstab(hard["hard_type"], hard["action"]).to_string())
    print()

    # ★경계모호 — 6강이 「모델이 틀린 곳」으로 지목한 자리
    amb = hard[hard["hard_type"] == "경계모호"]
    if len(amb):
        esc = (amb["action"] == "ESCALATE").sum()
        print("★경계모호 %d건 — 정답은 «확신도를 낮춰 이관»" % len(amb))
        print("   실제 이관 %d건 (%.0f%%) · 확신도 평균 %.2f"
              % (esc, 100 * esc / len(amb), amb["conf"].mean()))
        print("   ⇒ 6강: 「헷갈려야 할 자리에서 헷갈리지 «않는» 것이라 더 위험하다」")
        print("      확신도는 모델이 «스스로 보고하는» 값이라 «틀린 확신»도 있다.")
    print()

    # ★기대 라우트와 맞았나 (route_expected · route_alt 둘 중 하나면 인정)
    hit = sum(1 for _, r in hard.iterrows()
              if r["pred"] in (r["route_expected"], r["route_alt"]))
    print("[기대/대안 라우트 중 하나와 일치] %d/%d (%.1f%%)"
          % (hit, len(hard), 100 * hit / len(hard)))
    print("   ※ hard_cases 는 «두 라우트에 모두 해당»하는 문항이 많아 둘 다 인정해 센다.")

    automation_report(list(zip(hard["pred"], hard["conf"])), hard["route_expected"].tolist())
