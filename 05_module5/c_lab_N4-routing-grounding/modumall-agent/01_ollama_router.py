# -*- coding: utf-8 -*-
"""★키 없이 4강 → 6강 「갈아 끼우기」를 재현한다 — LLM 자리에 로컬 Ollama.

왜 이렇게 하나
  6강의 요지는 「LLM 이 몇 점인가」가 아니라 **「규칙보다 얼마나 나은가」** 다.
  그 비교는 «어느 모델이든» 성립한다. OpenAI 키가 없으면 그 자리에 Ollama 를 꽂는다.
  2강이 LangGraph 의 장점으로 든 「특정 모델에 얽매이지 않는 유연함」을 실제로 쓰는 것이다.

  ⚠ 절대 점수는 퍼실 기준선(0.94 / macro F1 0.945)과 «비교할 수 없다» — 모델이 다르다.
     비교할 수 있는 것은 **같은 모델 안에서의 전후**다.

  python 01_ollama_router.py                 # 기본 지침
  python 01_ollama_router.py --limit 20      # 20건만 (흐름 확인)
  python 01_ollama_router.py --fewshot       # ★fewshot 예시를 붙여서 (시도 #5)
  python 01_ollama_router.py --model qwen2.5:3b
"""
import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Literal

import pandas as pd
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from config import BASE, LABELS4, ROUTES, ensure_data
from prompts import ROUTE_GUIDE

sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_MODEL = "qwen3.5:2b"      # tools·thinking 지원 (2026-08-28 로컬)


class RouteDecision(BaseModel):
    """고객 문의 한 건에 대한 라우팅 판단 결과."""

    route: Literal["ORDER_PLACE", "PRODUCT_INFO", "SHIPPING",
                   "RETURN_REFUND", "OTHER"] = Field(
        description="문의를 배정할 라우트. 5개 값 중 하나만 사용한다.")
    confidence: float = Field(ge=0.0, le=1.0, description="판단의 확신도.")
    reason: str = Field(description="그 라우트로 판단한 근거를 한 문장으로.")


def load(split):
    inq = pd.read_csv(BASE / "customer_inquiries.csv")
    ans = pd.read_csv(BASE / "routing_answers.csv")
    g = inq.merge(ans, on="qa_id")
    return g[g["split"] == split].reset_index(drop=True)


def build_fewshot_block(n_per_route=2, hard=False):
    """★예시는 «fewshot» split 에서만 뽑는다 — eval 을 쓰면 점수가 거짓이 된다(6강 경고).

    hard=True 면 ★«경계 문항»을 우선 고른다.
      6강 더해보기 1: 「예시를 «쉬운 문항»으로 고를 때와 «경계 문항»으로 고를 때
                      차이가 크다」
      ⇒ 무엇이 «경계»인가? — **규칙 라우터가 «틀리는» 문항**이다.
        규칙은 어휘만 본다. 규칙이 틀렸다는 것은 «어휘로는 안 되는» 문항이라는 뜻이고,
        그게 정확히 LLM 이 배워야 할 자리다.
      ⚠ 이 선별에 eval 은 «한 건도» 쓰지 않는다. fewshot 40건 안에서만 고른다.
    """
    fs = load("fewshot")
    if hard:
        from router import build, rule_classify
        g = build(rule_classify)
        fs = fs.copy()
        fs["rule_pred"] = [g.invoke({"question": q})["route"] for q in fs["question"]]
        fs["is_hard"] = fs["rule_pred"] != fs["route"]      # 규칙이 틀린 것 = 경계
    picked = []
    for r in ROUTES:
        sub = fs[fs["route"] == r]
        if hard:
            sub = pd.concat([sub[sub["is_hard"]], sub[~sub["is_hard"]]])   # 경계 먼저
        for _, row in sub.head(n_per_route).iterrows():
            picked.append('문의: "%s" -> %s' % (row["question"], r))
    if not picked:
        return ""
    tag = "경계 사례 위주" if hard else "실제 상담 기록"
    head = "%s%s[판단 예시 — %s]%s" % (chr(10), chr(10), tag, chr(10))
    return head + chr(10).join(picked)


def make_classifier(model, guide):
    """분류 노드 — Ollama 판. 구조화 출력이 실패하면 «세지 않고 표시»한다."""
    # ★reasoning=False — qwen3 계열은 thinking 토큰을 먼저 쓴다.
    #   끄지 않으면 출력 예산이 거기서 다 소진돼 «빈 응답»이 오고,
    #   그것이 OutputParserException 으로 나타난다(20/20 실패를 이렇게 겪었다).
    kw = dict(model=model, temperature=0, num_predict=400)
    if model.startswith("qwen3"):
        kw["reasoning"] = False
    llm = ChatOllama(**kw)
    chain = llm.with_structured_output(RouteDecision)

    def classify(question):
        try:
            d = chain.invoke([("system", guide),
                              ("human", "고객 문의: %s" % question)])
            return d.route, d.confidence, ""
        except Exception as exc:
            # ★실패를 «OTHER» 로 뭉뚱그리지 않는다 — 그러면 모델 탓인지 파싱 탓인지 못 가른다
            return "_PARSE_FAIL", 0.0, type(exc).__name__

    return classify


def run(df, classify, title, workers=4):
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        out = list(ex.map(classify, df["question"].tolist()))
    secs = time.perf_counter() - t0

    pred = [o[0] for o in out]
    fails = [(q, o[2]) for q, o in zip(df["question"], out) if o[0] == "_PARSE_FAIL"]
    y = df["route"].tolist()

    print()
    print("== %s ==" % title)
    print("   대상 %d건 · %.1f초 (건당 %.2f초)" % (len(df), secs, secs / max(1, len(df))))
    print("   ★구조화 출력 실패 %d건 — 이건 «분류 오류»가 아니라 «형식 오류»다" % len(fails))
    if fails:
        from collections import Counter
        for k, v in Counter(f[1] for f in fails).most_common(3):
            print("       %-28s %d건" % (k, v))

    ok = [(a, p) for a, p in zip(y, pred) if p != "_PARSE_FAIL"]
    if not ok:
        print("   ⛔ 전부 실패 — 점수를 낼 수 없다")
        return None
    ya, pa = [a for a, _ in ok], [p for _, p in ok]
    f1 = f1_score(ya, pa, labels=LABELS4, average="macro", zero_division=0)
    acc = accuracy_score(ya, pa)
    print("   ⇒ 채점 %d건 · 정확도 %.3f · macro F1 %.3f" % (len(ok), acc, f1))
    print()
    print(classification_report(ya, pa, labels=LABELS4, digits=3, zero_division=0))
    print("[혼동 행렬] 행=정답, 열=예측")
    print(pd.DataFrame(confusion_matrix(ya, pa, labels=ROUTES),
                       index=ROUTES, columns=ROUTES).to_string())

    miss = [(q, a, p) for q, a, p in zip(df["question"], y, pred) if a != p and p != "_PARSE_FAIL"]
    print()
    print("[오분류 %d건] — 여기를 읽는 것이 개선의 출발점이다" % len(miss))
    pairs = {}
    for _, a, p in miss:
        pairs[(a, p)] = pairs.get((a, p), 0) + 1
    for (a, p), n in sorted(pairs.items(), key=lambda kv: -kv[1]):
        print("   %-14s → %-14s %2d건" % (a, p, n))
    print()
    for q, a, p in miss[:15]:
        print("   [%s → %s]  %s" % (a, p, q[:56]))
    return {"n": len(ok), "acc": acc, "f1": f1, "fail": len(fails), "secs": secs}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Ollama 라우터로 ① 지표를 잰다")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--limit", type=int, default=None, help="앞 N건만")
    ap.add_argument("--fewshot", action="store_true", help="fewshot 예시를 지침에 붙인다")
    ap.add_argument("--hard-fewshot", action="store_true",
                    help="★예시를 «경계 문항»으로 고른다(6강 더해보기 1)")
    ap.add_argument("--n-shot", type=int, default=2, help="라우트당 예시 개수")
    ap.add_argument("--workers", type=int, default=4, help="동시 호출 (로컬은 낮게)")
    ap.add_argument("--outscope", action="store_true", help="★범위 밖 33건도 같이 잰다")
    ap.add_argument("--guide", choices=["v1", "v2", "v3", "v4"], default="v1",
                    help="v2 = SHIPPING 정의를 강화한 판(시도 #2)")
    args = ap.parse_args()

    ensure_data()
    if args.guide == "v2":
        from prompts_v2 import ROUTE_GUIDE_V2 as BASE_GUIDE
    elif args.guide == "v3":
        from prompts_v3 import ROUTE_GUIDE_V3 as BASE_GUIDE
    elif args.guide == "v4":
        from prompts_v4 import ROUTE_GUIDE_V4 as BASE_GUIDE
    else:
        BASE_GUIDE = ROUTE_GUIDE
    want_fs = args.fewshot or args.hard_fewshot
    guide = BASE_GUIDE + (build_fewshot_block(args.n_shot, args.hard_fewshot)
                          if want_fs else "")
    tag = "%s%s" % (args.guide,
                    (" + hard-fewshot x%d" % args.n_shot) if args.hard_fewshot
                    else ((" + fewshot x%d" % args.n_shot) if args.fewshot else ""))
    print("모델 %s · 지침 %s (%d자)" % (args.model, tag, len(guide)))

    ev = load("eval")
    if args.limit:
        ev = ev.head(args.limit)
    clf = make_classifier(args.model, guide)
    res = run(ev, clf, "① 의도 분류 — Ollama 라우터 · 평가셋")

    if args.outscope:
        # ★한쪽만 재면 속는다 — eval 에는 OTHER 정답이 «0건»이라
        #   OTHER 를 덜 쓰게만 만들어도 점수가 오른다
        osc = load("outscope")
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            o = list(ex.map(clf, osc["question"].tolist()))
        hit = sum(1 for x in o if x[0] == "OTHER")
        print()
        print("== ★범위 밖(outscope) %d건 ==" % len(osc))
        print("   OTHER 로 제대로 보낸 것 %d건 (%.1f%%)" % (hit, 100 * hit / len(osc)))
        print("   ⇒ eval 점수만 보면 이 값이 떨어지는 걸 «못 본다»")

    print()
    print("══ 요약 ══")
    if res:
        print("   Ollama(%s·%s)  정확도 %.3f · macro F1 %.3f  [형식실패 %d]"
              % (args.model, tag, res["acc"], res["f1"], res["fail"]))
    print("   규칙 라우터(기준)        정확도 0.583 · macro F1 0.677")
    print("   퍼실 제시(gpt-5.6-luna)  정확도 0.940 · macro F1 0.945  ← ⚠모델이 달라 직접 비교 불가")
