# -*- coding: utf-8 -*-
"""★4강 「더 해보기」 3 — 규칙 라우터를 LLM 의 «폴백»으로 붙인다.

4강이 시킨 것:
  「API 호출이 실패하거나 응답이 형식에 맞지 않을 때 rule_router 를 대신 호출하는
   래퍼 함수를 만듭니다. try/except 와 타임아웃 처리를 함께 넣습니다.
   ⇒ 실서비스에서 LLM 장애 시에도 서비스가 «완전히 멈추지 않는» 구조를 경험할 수 있습니다.」

★그런데 오늘 실측이 이 설계에 근거를 하나 더 준다 —
  **규칙 라우터의 macro F1 이 0.677 로, Ollama 2B 지침만(0.556)보다 «높다».**
  폴백은 「없는 것보다 낫다」 수준이 아니라 **실제로 쓸 만한 바닥**이다.

★그리고 노드3 피어리뷰에서 배운 것을 여기에 가져온다 — `retry_worth_it()`
  **「이 실패는 «다시 해서 달라지는가»」**를 먼저 묻는다.
  · 연결 실패 · 타임아웃 · 모델 없음  → 다시 해도 같다. **바로 폴백.**
  · 형식 오류(파싱 실패) · 빈 응답    → 모델이 «다른 답»을 낼 수 있다. **한 번 재시도.**
  ⇒ 구분하지 않으면 «달라질 리 없는 실패»를 세 번 반복하고 세 배 기다린다.

  python 09_fallback.py              # 장애를 «실제로» 일으켜 확인
  python 09_fallback.py --eval       # 평가셋 120건으로 폴백 비율·점수
"""
import argparse
import re
import sys
import time
from typing import Literal

import pandas as pd
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from config import BASE, LABELS4, ensure_data
from prompts import ROUTE_GUIDE
from router import RULES

sys.stdout.reconfigure(encoding="utf-8")


class RouteDecision(BaseModel):
    route: Literal["ORDER_PLACE", "PRODUCT_INFO", "SHIPPING",
                   "RETURN_REFUND", "OTHER"] = Field(description="5개 중 하나.")
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


def rule_classify(q):
    """규칙 라우터 — 모델을 부르지 않는다. macro F1 0.677(실측)."""
    for pattern, route in RULES:
        if re.search(pattern, q):
            return route, 0.8, "키워드 규칙 매치"
    return "OTHER", 0.3, "매치되는 규칙 없음"


def retry_worth_it(exc):
    """★이 실패는 «다시 해서 달라지는가» — (재시도할까, 안 한다면 왜).

    노드3 피어리뷰에서 상대에게 배워 가져온 것.
    """
    name = type(exc).__name__
    text = ("%s %s" % (name, exc))[:200].lower()
    # ★"connection" 으로 찾다가 ConnectError 를 «놓쳤다» — connecterror 에는 connection 이 없다.
    #   실측: 연결 실패 3건이 「형식 오류」로 분류돼 쓸데없이 재시도했다.
    #   ⇒ 키를 «어간»으로 줄인다. 예외 «이름»과 «메시지»를 둘 다 본다.
    for key, why in (
        ("connect", "백엔드에 연결 못 함 — 다시 걸어도 같다"),
        ("timeout", "타임아웃 — 같은 조건이면 또 걸린다"),
        ("timed out", "타임아웃 — 같은 조건이면 또 걸린다"),
        ("not found", "모델을 못 찾음 — 다시 물어도 없다"),
        ("refused", "연결 거부 — 서버가 안 떠 있다"),
        ("unauthorized", "인증 실패 — 키 문제라 재시도로 안 풀린다"),
        ("apiconnection", "API 연결 실패"),
        ("404", "엔드포인트 없음"),
    ):
        if key in text:
            return False, why
    return True, ""        # 파싱 실패·빈 응답 등은 «다른 답»이 나올 수 있다


class Router:
    """LLM 우선 · 실패하면 규칙으로 — 그리고 «왜 폴백했는지»를 센다."""

    def __init__(self, model="qwen3.5:2b", timeout=20, guide=ROUTE_GUIDE):
        kw = dict(model=model, temperature=0, num_predict=400, timeout=timeout)
        if model.startswith("qwen3"):
            kw["reasoning"] = False
        self.chain = ChatOllama(**kw).with_structured_output(RouteDecision)
        self.guide = guide
        self.stat = {"llm": 0, "retry": 0, "fallback": 0}
        self.why = {}

    def __call__(self, q):
        for attempt in (1, 2):
            try:
                d = self.chain.invoke(
                    [("system", self.guide), ("human", "고객 문의: %s" % q)])
                self.stat["llm"] += 1
                return d.route, d.confidence, "llm"
            except Exception as exc:
                again, why = retry_worth_it(exc)
                if not again:
                    # ★다시 해도 달라지지 않는 실패 — 바로 폴백한다
                    self.stat["fallback"] += 1
                    self.why[why] = self.why.get(why, 0) + 1
                    r, c, _ = rule_classify(q)
                    return r, c, "rule"
                if attempt == 1:
                    self.stat["retry"] += 1
                    continue
                # 재시도해도 안 되면 폴백
                self.stat["fallback"] += 1
                k = "형식 오류 — 두 번 해도 안 됨(%s)" % type(exc).__name__
                self.why[k] = self.why.get(k, 0) + 1
                r, c, _ = rule_classify(q)
                return r, c, "rule"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="규칙 라우터를 LLM 폴백으로 (4강 더해보기 3)")
    ap.add_argument("--eval", action="store_true", help="평가셋 120건으로 잰다")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    ensure_data()

    print("=== ★① 장애를 «실제로» 일으켜 본다 — 백엔드를 없는 포트로 ===")
    tests = ["반품 배송비 얼마예요?", "이 슬리퍼 275로 주세요.", "홍대점 오늘 몇 시까지 하나요?"]
    broken = Router(model="qwen3.5:2b")
    broken.chain = ChatOllama(model="qwen3.5:2b", base_url="http://127.0.0.1:59999",
                              temperature=0, timeout=5,
                              reasoning=False).with_structured_output(RouteDecision)
    t0 = time.perf_counter()
    for q in tests:
        r, c, src = broken(q)
        print("   %-28s → %-14s (%s)" % (q[:26], r, src))
    secs = time.perf_counter() - t0
    print("   %.1f초 · 호출 %s" % (secs, broken.stat))
    print("   폴백 사유: %s" % (broken.why or "없음"))
    print()
    # ★결론을 «미리 써 두지» 않는다 — 실측과 어긋나도 화면엔 그대로 나온다.
    #   처음에 「재시도 0회로 바로 폴백했다」고 박아 두었다가, 실제로는 3회 재시도한 것을
    #   출력이 «가려 주었다». 그래서 여기서는 stat 을 «읽어» 문장을 만든다.
    if broken.stat["retry"] == 0:
        print("   ⇒ ★재시도 0회 — 연결 실패를 «다시 해도 같은 실패»로 바로 알아봤다.")
    else:
        print("   ⚠ 재시도 %d회 — retry_worth_it() 이 이 예외를 «못 알아봤다».")
        print("     달라질 리 없는 실패를 반복하고 그만큼 더 기다렸다는 뜻이다.")
    print("   ⇒ 그래도 서비스는 «멈추지 않았다» — 규칙 라우터가 %d건 모두 답을 냈다."
          % broken.stat["fallback"])
    print()

    print("=== ② 정상일 때는 LLM 을 쓴다 ===")
    ok = Router()
    for q in tests:
        r, c, src = ok(q)
        print("   %-28s → %-14s conf=%.2f (%s)" % (q[:26], r, c, src))
    print("   호출 %s" % ok.stat)
    print()

    if args.eval:
        from concurrent.futures import ThreadPoolExecutor
        from sklearn.metrics import accuracy_score, f1_score
        inq = pd.read_csv(BASE / "customer_inquiries.csv")
        ans = pd.read_csv(BASE / "routing_answers.csv")
        d = inq.merge(ans, on="qa_id")
        d = d[d["split"] == "eval"].reset_index(drop=True)
        rt = Router()
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            out = list(ex.map(rt, d["question"].tolist()))
        pred = [o[0] for o in out]
        src = [o[2] for o in out]
        print("=== ③ 평가셋 %d건 — 폴백이 실제로 얼마나 쓰이나 ===" % len(d))
        print("   %.0f초 · 호출 %s" % (time.perf_counter() - t0, rt.stat))
        print("   LLM 이 답한 것 %d건 · 규칙이 답한 것 %d건"
              % (src.count("llm"), src.count("rule")))
        print("   정확도 %.3f · macro F1 %.3f"
              % (accuracy_score(d["route"], pred),
                 f1_score(d["route"], pred, labels=LABELS4, average="macro", zero_division=0)))
        print()
        print("   ※ 비교 — 규칙만 0.583/0.677 · Ollama 지침만 0.542/0.556")
        print("     ★폴백 구조는 «둘 중 나은 쪽으로 수렴»하지 않는다. 그냥 «멈추지 않게» 할 뿐이다.")
        print("     품질을 올리려면 라우터 자체를 고쳐야 한다(v4+fewshot 0.792/0.816).")
