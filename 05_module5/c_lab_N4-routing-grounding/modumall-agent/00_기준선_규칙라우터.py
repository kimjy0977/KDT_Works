# -*- coding: utf-8 -*-
"""★키 없이 잴 수 있는 «바닥»을 먼저 잰다 — 규칙 라우터로 ① 지표.

왜 이걸 먼저 하나
  4강이 규칙 노드를 꽂고 6강이 LLM 으로 «갈아 끼운다». 그러면 물어야 할 것은
  「LLM 이 몇 점인가」가 아니라 **「LLM 이 규칙보다 얼마나 나은가」** 다.
  규칙 쪽은 모델을 안 부르므로 **API 키 없이 지금 잴 수 있다.**

  evaluate.py 는 LLM 라우터만 잰다. 이 파일은 그 «비교 대상»을 만든다.
  원본 파일은 건드리지 않는다.

  python 00_기준선_규칙라우터.py
"""
import sys

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from config import BASE, LABELS4, ROUTES, ensure_data
from router import build, rule_classify

sys.stdout.reconfigure(encoding="utf-8")


def load(split):
    inq = pd.read_csv(BASE / "customer_inquiries.csv")
    ans = pd.read_csv(BASE / "routing_answers.csv")
    g = inq.merge(ans, on="qa_id")
    return g[g["split"] == split].reset_index(drop=True)


def measure(df, title):
    """규칙 라우터를 통과시키고 점수를 낸다. — «무엇을 몇 건» 쟀는지 먼저 찍는다."""
    graph = build(rule_classify)
    pred = [graph.invoke({"question": q})["route"] for q in df["question"]]
    y = df["route"].tolist()

    f1 = f1_score(y, pred, labels=LABELS4, average="macro", zero_division=0)
    acc = accuracy_score(y, pred)
    print()
    print("== %s ==" % title)
    print("   대상 %d건 · 정확도 %.3f · macro F1 %.3f  (macro F1 은 OTHER 를 안 센다)"
          % (len(df), acc, f1))
    print()
    print(classification_report(y, pred, labels=LABELS4, digits=3, zero_division=0))
    print("[혼동 행렬] 행=정답, 열=예측")
    print(pd.DataFrame(confusion_matrix(y, pred, labels=ROUTES),
                       index=ROUTES, columns=ROUTES).to_string())

    miss = [(q, a, p) for q, a, p in zip(df["question"], y, pred) if a != p]
    print()
    print("[오분류 %d건 / %d건]" % (len(miss), len(df)))
    pairs = {}
    for _, a, p in miss:
        pairs[(a, p)] = pairs.get((a, p), 0) + 1
    for (a, p), n in sorted(pairs.items(), key=lambda kv: -kv[1]):
        print("   %-14s → %-14s %2d건" % (a, p, n))
    print()
    print("[오분류 전문]")
    for q, a, p in miss:
        print("   [%s → %s]  %s" % (a, p, q[:60]))
    return {"n": len(df), "acc": acc, "f1": f1, "miss": len(miss)}


if __name__ == "__main__":
    ensure_data()
    out = {"eval": measure(load("eval"), "① 의도 분류 — 규칙 라우터 · 평가셋")}

    hard = pd.read_csv(BASE / "hard_cases.csv")
    print()
    print("[hard_cases.csv 열]", list(hard.columns), "· %d행" % len(hard))

    print()
    print("== 요약 ==")
    for k, v in out.items():
        print("   %-6s n=%d  정확도 %.3f · macro F1 %.3f · 오분류 %d"
              % (k, v["n"], v["acc"], v["f1"], v["miss"]))
    print()
    print("   ⇒ 이 숫자가 «LLM 을 쓰지 않았을 때의 바닥»이다.")
    print("     퍼실 제시 LLM 기준선 0.94 / macro F1 0.945 와 비교하면")
    print("     «LLM 이 벌어 준 몫»이 나온다.")
