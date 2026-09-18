# -*- coding: utf-8 -*-
"""★7강 베이스라인 — basic RAG(BM25)는 이 질문에 답할 수 있는가.

노드가 시키는 것: *"BM25 로 베이스라인을 잡고, 정답을 담은 문서를 후보 안에
데려왔는지를 재서 «어디서 무너지는지» 읽는다."*

⛔그래프를 만들기 «전»에 이 숫자를 남긴다. 나중에 비교할 기준선이다.
  노드5 에서 배운 것 — 기준선 없이 잰 점수는 못 믿는다.

재는 것 = **Recall@k** (정답 문서가 후보 k 개 안에 들어왔나)
  ⚠ 「답이 맞았나」가 아니다. 그건 LLM 이 필요하다.
    여기서는 **찾아오기라도 했는가**만 본다 — 못 찾으면 답할 방법이 없다.

    python 01_baseline.py
    python 01_baseline.py --k 10
"""
import argparse
import collections
import glob
import io
import json
import os
import re
import sys

# 윈도우 콘솔 기본이 cp949 라 한글·특수기호에서 터진다. 출력만 UTF-8 로 고정한다.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "data", "cinephile_kb_80", "docs")
GOLD = os.path.join(HERE, "data", "cinephile_goldenset.json")

# 문서 제목과 삼중항 엔티티는 «표기»가 다르다.
#   문서   1987_(2017년_영화) · CJ엔터테인먼트
#   삼중항 1987               · CJ 엔터테인먼트
# ⇒ 9강 「정규화」가 다루는 문제를 여기서 미리 만난다.
_PAREN = re.compile(r"\([^)]*\)")


def norm(s):
    """밑줄·괄호·공백을 걷어낸 비교용 키."""
    s = s.replace("_", " ")
    s = _PAREN.sub(" ", s)
    return re.sub(r"\s+", "", s).lower()


def tokenize(text):
    """한국어라 형태소 분석이 맞지만, 베이스라인은 «기준선»이므로 단순하게 간다.

    ★일부러 소박하게 둔다 — 여기를 잘 만들면 「벽」이 낮아 보여서
      GraphRAG 가 얼마나 넘는지를 못 잰다.
    """
    return re.findall(r"[가-힣]+|[A-Za-z]+|\d+", text or "")


def load_docs():
    docs = []
    for p in sorted(glob.glob(os.path.join(DOCS, "*.md"))):
        title = os.path.basename(p)[:-3]
        body = io.open(p, encoding="utf-8").read()
        docs.append({"title": title, "key": norm(title), "body": body})
    return docs


def gold_docs_for(item, keyset):
    """이 문항의 «정답 문서» — 삼중항의 주어·목적어 중 실제 문서인 것.

    장르·테마·지역(미스터리·가난·조선)은 문서가 아니다. 세지 않는다.
    """
    want = set()
    for t in item.get("reference_contexts") or []:
        for e in (t[0], t[2]):
            k = norm(e)
            if k in keyset:
                want.add(k)
    return want


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()

    from rank_bm25 import BM25Okapi

    docs = load_docs()
    keyset = {d["key"] for d in docs}
    bm25 = BM25Okapi([tokenize(d["title"].replace("_", " ") + " " + d["body"]) for d in docs])

    gold = json.load(io.open(GOLD, encoding="utf-8"))
    items = gold["items"]

    rows, by_kind = [], collections.defaultdict(lambda: [0, 0])
    no_gold = 0
    for it in items:
        want = gold_docs_for(it, keyset)
        scores = bm25.get_scores(tokenize(it["user_input"]))
        top = sorted(range(len(docs)), key=lambda i: -scores[i])[: args.k]
        got = {docs[i]["key"] for i in top}

        if not want:                       # 전역 질문은 reference_contexts 가 빈 배열
            no_gold += 1
            rows.append((it["id"], it["kind"], None, None, [docs[i]["title"] for i in top[:3]]))
            continue

        hit = want & got
        recall = len(hit) / len(want)
        by_kind[it["kind"]][0] += recall
        by_kind[it["kind"]][1] += 1
        rows.append((it["id"], it["kind"], recall, len(want),
                     [docs[i]["title"] for i in top[:3]]))

    print("=" * 66)
    print("7강 베이스라인 — BM25 Recall@%d  (문서 %d건 · 문항 %d건)"
          % (args.k, len(docs), len(items)))
    print("=" * 66)
    for rid, kind, rec, nwant, top3 in rows:
        mark = "  --  " if rec is None else ("%5.0f%%" % (rec * 100))
        note = "(전역 — 정답 문서 없음)" if rec is None else "정답문서 %d개" % nwant
        print("%-8s %-4s %s  %s" % (rid, kind, mark, note))
        print("         top3: %s" % " · ".join(t[:22] for t in top3))

    print("-" * 66)
    tot_r = sum(v[0] for v in by_kind.values())
    tot_n = sum(v[1] for v in by_kind.values())
    for kind in ("단순", "추천", "전역"):
        if kind in by_kind:
            s, n = by_kind[kind]
            print("  %-4s %2d문항  평균 Recall@%d = %5.1f%%" % (kind, n, args.k, s / n * 100))
    if no_gold:
        print("  전역  %2d문항  — 정답 «문서»가 없어 이 지표로는 못 잰다" % no_gold)
    print("-" * 66)
    print("  ★전체 %d문항 평균 Recall@%d = %.1f%%" % (tot_n, args.k, tot_r / tot_n * 100))
    print("=" * 66)
    print()
    print("⚠ 이 숫자는 «찾아왔는가»일 뿐 «답했는가»가 아니다.")
    print("  그리고 전역 질문 %d건은 이 잣대로 못 잰다 — 11강 커뮤니티 요약이 그래서 필요하다." % no_gold)


if __name__ == "__main__":
    main()
