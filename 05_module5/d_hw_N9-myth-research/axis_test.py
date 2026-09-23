# -*- coding: utf-8 -*-
"""★축 실험 재시도 — 「목차가 실제로 갈리는가」를 «목차 자체»로 잰다.

  python axis_test.py            3회씩
  python axis_test.py --runs 5

왜 따로 만드나
  ablation.py 는 근거율·편중 같은 «지표»를 잰다. 그런데 축 실험이 물어야 할 것은
  ★「목차가 달라졌나」다. 그건 지표가 아니라 «제목 문자열»이다.
  1차 실험이 실패한 것을 지표로는 못 봤고 ★보고서를 읽고서야 알았다(REPORT §6).
  ⇒ 이번에는 «목차를 직접 세어» 본다.

무엇을 재나
    목차 겹침    A 와 B 의 절 제목이 얼마나 같은가 (0 이면 완전히 다른 축)
    문서 겹침    두 축이 읽은 문서 집합이 얼마나 같은가
  ★겹침이 높으면 축이 «안 바뀐» 것이다.
"""
import argparse
import io
import json
import os
import re
import sys

import graph as agent

HERE = os.path.dirname(os.path.abspath(__file__))
QS = json.load(io.open(os.path.join(HERE, "data/questions.json"),
                       encoding="utf-8"))
Q4 = next(x["text"] for x in QS["보조질문"] if x["id"] == "Q4")
Q1 = QS["주질문"]["text"]

조건 = [
    ("명단만 · 주제", "주제", False),
    ("명단만 · 문화권", "문화권", False),
    ("★지시 · 주제", "주제", True),
    ("★지시 · 문화권", "문화권", True),
]


def _키(t):
    """제목에서 «뼈대»만 — 조사·수식어를 떼고 겹침을 본다."""
    return set(re.findall(r"[가-힣]{2,}", t))


def 겹침(A, B):
    a = set().union(*[_키(x) for x in A]) if A else set()
    b = set().union(*[_키(x) for x in B]) if B else set()
    return len(a & b) / max(1, len(a | b))


def 한번(축, 지시, q):
    base = list(agent.ROSTER)
    agent.설정.pop("축지시", None)
    agent.ROSTER = (agent._CFG["_역할명단"]["문화권 축(B) — 대조 실험용"]
                    if 축 == "문화권"
                    else agent._CFG["_역할명단"]["★주제 축(A) — 기본"])
    if 지시:
        agent.설정["축지시"] = agent._CFG["_축지시"][축]
    st = agent.run(q, quiet=True)
    agent.ROSTER = base
    agent.설정.pop("축지시", None)
    return ([t["절"] for t in st["toc"]],
            sorted({d for s in st["sections"] for d in s["읽음"]}),
            st["metrics"]["근거율"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--q1", action="store_true",
                    help="축을 «말하는» 주질문으로 (1차 실험 재현)")
    a = ap.parse_args()
    q = Q1 if a.q1 else Q4

    print("═══ 축 실험 재시도 ═══")
    print("  질문: %s" % q)
    print("  %s\n" % ("★주질문 — 축을 «말한다»(1차 재현)" if a.q1
                     else "★Q4 — 축을 «말하지 않는다»"))

    결과 = {}
    for 이름, 축, 지시 in 조건:
        toc_s, doc_s, g = [], [], []
        print("  ▶ %s" % 이름)
        for i in range(a.runs):
            t, d, r = 한번(축, 지시, q)
            toc_s.append(t)
            doc_s.append(d)
            g.append(r)
            print("     [%d/%d] %s" % (i + 1, a.runs, " / ".join(t)))
        결과[이름] = {"목차": toc_s, "문서": doc_s, "근거율": g}

    print("\n── ★목차가 갈렸나 (0 = 완전히 다름 · 1 = 같음) ──")
    쌍 = [("명단만 · 주제", "명단만 · 문화권", "1차 — 역할 명단만 바꿈"),
         ("★지시 · 주제", "★지시 · 문화권", "★2차 — 프롬프트로 지시")]
    for A, B, 설명 in 쌍:
        t = sum(겹침(x, y) for x, y in zip(결과[A]["목차"], 결과[B]["목차"])) / a.runs
        d = sum(len(set(x) & set(y)) / max(1, len(set(x) | set(y)))
                for x, y in zip(결과[A]["문서"], 결과[B]["문서"])) / a.runs
        print("  %-24s 목차 겹침 %.2f · 읽은 문서 겹침 %.2f  %s"
              % (설명, t, d,
                 "★축이 안 바뀌었다" if t > .5 else "축이 갈렸다"))

    io.open(os.path.join(HERE, "output/axis_test.json"), "w",
            encoding="utf-8", newline="").write(
        json.dumps({"질문": q, "회차": a.runs, "결과": 결과},
                   ensure_ascii=False, indent=1))
    print("\n  → output/axis_test.json")


if __name__ == "__main__":
    main()
