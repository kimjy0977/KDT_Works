# -*- coding: utf-8 -*-
"""★4강 「더 해보기」 2·1 — LLM 없이 어디까지 되나. (키 불필요 · 모델 호출 0회)

4강이 규칙 라우터를 먼저 만든 이유가 이거다 —
  「LLM 없이 얼마나 되는지를 알아야 LLM 이 정말 «필요한지» 판단할 수 있다.」

그런데 규칙 라우터는 «사람이 손으로 쓴 키워드»다. 그 사이에 한 칸이 더 있다:
**데이터에서 «학습한» 전통 ML.** 4강 더 해보기 2 가 시키는 것이 그것이다.

  ① bag-of-keywords   규칙을 «가중치»로 — 매치된 키워드 개수를 세어 최다 라우트
  ② TF-IDF + 로지스틱  fewshot 40 건으로 «학습»한다
  ⇒ 셋을 나란히 놓으면 **「LLM 이 벌어 준 몫」이 정확히 얼마인지** 말할 수 있다.

  ⚠ 학습에는 **fewshot 40건만** 쓴다. eval 120건을 쓰면 그 점수는 거짓이 된다(3강).
     ★그런데 40건은 라우트당 8건뿐이다 — 그 한계도 함께 본다.

  python 05_tfidf_baseline.py
"""
import re
import sys
from collections import Counter

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score

from config import BASE, LABELS4, ROUTES, ensure_data
from router import RULES

sys.stdout.reconfigure(encoding="utf-8")


def load(split):
    inq = pd.read_csv(BASE / "customer_inquiries.csv")
    ans = pd.read_csv(BASE / "routing_answers.csv")
    g = inq.merge(ans, on="qa_id")
    return g[g["split"] == split].reset_index(drop=True)


def score(y, pred, name, n_train=None):
    f1 = f1_score(y, pred, labels=LABELS4, average="macro", zero_division=0)
    acc = accuracy_score(y, pred)
    extra = " · 학습 %d건" % n_train if n_train else ""
    print("   %-22s 정확도 %.3f · macro F1 %.3f%s" % (name, acc, f1, extra))
    return acc, f1


# ─────────── ① bag-of-keywords — 규칙을 «가중치»로 ───────────
def bag_of_keywords(q):
    """매치된 키워드 «개수»를 세어 최다 라우트를 고른다(4강 더 해보기 1).

    원래 규칙은 «먼저 매치되는 것»을 채택한다 — 순서가 곧 우선순위였다.
    여기서는 순서를 없애고 «많이 걸린 쪽»을 고른다.
    """
    cnt = Counter()
    for pattern, route in RULES:
        hits = len(re.findall(pattern, q))
        if hits:
            cnt[route] += hits
    return cnt.most_common(1)[0][0] if cnt else "OTHER"


def rule_first_match(q):
    """원본 규칙 — 먼저 매치되는 것을 채택."""
    for pattern, route in RULES:
        if re.search(pattern, q):
            return route
    return "OTHER"


if __name__ == "__main__":
    ensure_data()
    ev = load("eval")
    fs = load("fewshot")
    osc = load("outscope")
    y = ev["route"].tolist()

    print("=== LLM 없이 어디까지 되나 — 모델 호출 0회 ===")
    print("    평가셋 %d건 · 학습용 fewshot %d건 · 범위밖 %d건" % (len(ev), len(fs), len(osc)))
    print()

    print("[① 손으로 쓴 규칙]")
    p_rule = [rule_first_match(q) for q in ev["question"]]
    score(y, p_rule, "먼저 매치되는 것")
    p_bag = [bag_of_keywords(q) for q in ev["question"]]
    score(y, p_bag, "★가중치(bag-of-kw)")
    print("   ⇒ 4강 예고: 「대부분 조금 오르지만 ORDER_PLACE/PRODUCT_INFO 혼동은 여전히 남는다」")
    print()

    # ─────────── ② TF-IDF + 로지스틱 — 데이터에서 «학습» ───────────
    print("[② TF-IDF + 로지스틱 회귀] — fewshot 40건으로 학습")
    # ★한국어는 공백 토큰만으로는 약하다. 문자 n-gram 을 함께 쓴다.
    for name, kw in [("단어 1~2gram", dict(ngram_range=(1, 2))),
                     ("★문자 2~4gram", dict(analyzer="char_wb", ngram_range=(2, 4)))]:
        vec = TfidfVectorizer(**kw)
        X = vec.fit_transform(fs["question"])
        clf = LogisticRegression(max_iter=2000, class_weight="balanced")
        clf.fit(X, fs["route"])
        p = clf.predict(vec.transform(ev["question"]))
        score(y, p, name, n_train=len(fs))
    print()

    # ★학습 데이터를 늘리면 — fewshot + outscope (eval 은 «절대» 넣지 않는다)
    tr = pd.concat([fs, osc], ignore_index=True)
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
    X = vec.fit_transform(tr["question"])
    clf = LogisticRegression(max_iter=2000, class_weight="balanced")
    clf.fit(X, tr["route"])
    p_best = clf.predict(vec.transform(ev["question"]))
    print("[③ 학습 데이터를 늘리면] — fewshot + outscope (★eval 은 넣지 않는다)")
    score(y, p_best, "문자 2~4gram", n_train=len(tr))
    po = clf.predict(vec.transform(osc["question"]))
    print("   범위 밖 %d건 중 OTHER 로 %d건 (%.1f%%)  ※학습에 썼으므로 참고용"
          % (len(osc), (po == "OTHER").sum(), 100 * (po == "OTHER").mean()))
    print()

    print(classification_report(y, p_best, labels=LABELS4, digits=3, zero_division=0))

    print("══ 한자리에 놓고 보면 ══")
    rows = [
        ("손으로 쓴 규칙", 0.583, 0.677, "84.8%", "모델 호출 0"),
        ("Ollama 2B 지침만", 0.542, 0.556, "78.8%", "120회 · 6.5분"),
        ("Ollama 2B v4+fewshot", 0.792, 0.816, "66.7%", "120회 · 7.5분"),
        ("gpt-5.6-luna (퍼실)", 0.940, 0.945, "?", "120회 · 수십 원"),
    ]
    print("   %-24s %8s %10s %10s  %s" % ("", "정확도", "macro F1", "범위밖", "비용"))
    for n, a, f, o, c in rows:
        print("   %-24s %8.3f %10.3f %10s  %s" % (n, a, f, o, c))
    print()
    print("   ⇒ 4강의 질문 「LLM 이 정말 필요한가」에 «숫자로» 답할 수 있게 된다.")
