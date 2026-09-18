# -*- coding: utf-8 -*-
"""★누락 메우기 — basic RAG 와 GraphRAG 를 «같은 잣대»로 비교한다.

노드 16강이 정리한 표에 이렇게 적혀 있다:
    평가   LLM-as-judge + RAGAS
           «단순은 basic 우세, 추천·전역은 GraphRAG 우세»

그런데 내 07_evaluate.py 는 GraphRAG 만 쟀다. 7강 BM25 는 «문서를 찾아왔는가»
(Recall@k) 였고 14강은 «답했는가»라 **잣대가 달라 나란히 놓을 수 없었다.**
스크립트 끝에 「잣대가 다르다」고 적어 두고 넘어갔는데, 그건 벽을 넘은 게 아니라
벽이 있다고 적어 둔 것이다.

⇒ 여기서 넘는다. **같은 15문항 · 같은 채점기**로 둘을 잰다.

  basic RAG   BM25 top-k 문서 «본문»을 그대로 LLM 에 넣고 답하게 한다
  GraphRAG    06_agent 의 세 갈래

  채점 ①  LLM-as-judge   기대 정답과 실제 답변을 대조해 0~1
  채점 ②  context recall 정답 삼중항이 «근거에» 들어왔는가 (RAGAS 스타일)

    python 08_compare.py
    python 08_compare.py --k 5 --repeat 2
"""
import argparse
import collections
import io
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
GOLD = os.path.join(HERE, "data", "cinephile_goldenset.json")
sys.path.insert(0, HERE)
from importlib import import_module            # noqa: E402
_bl = import_module("01_baseline")
_agent = import_module("06_agent")
key = _agent.key

BASIC_SYS = """너는 한국 영화 안내원이다. 아래 [문서]에 «있는 것»만으로 답한다.

- 문서에 없으면 «없다»고 말한다. 아는 것을 보태지 않는다.
- 추천을 물으면 문서에 있는 작품을 여러 개 든다.
- 근거가 많으면 길어져도 된다.

[문서]
{ctx}"""

JUDGE_SYS = """너는 채점자다. 「기대 정답」과 「실제 답변」을 대조해 점수를 매긴다.

★표현이 아니라 «사실»을 본다. 말투·순서·길이는 보지 않는다.
- 기대 정답이 든 «항목» 중 실제 답변이 담은 비율을 센다.
- 기대 정답에 「등」이 붙어 있으면 대표 항목 몇 개만 담아도 인정한다.
- 답변이 사실과 «다른 것»을 말하면 감점한다.

점수
  1.0  기대 정답의 핵심을 사실상 다 담았다
  0.7  대부분 담았으나 빠진 항목이 있다
  0.4  일부만 담았다
  0.0  못 담았거나 틀렸다"""

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "number"},
        "reason": {"type": "string"},
    },
    "required": ["score", "reason"],
    "additionalProperties": False,
}


def basic_rag(client, model, docs, bm25, q, k):
    """basic RAG — BM25 로 문서를 찾아 «본문»을 통째로 넣고 답하게 한다."""
    scores = bm25.get_scores(_bl.tokenize(q))
    top = sorted(range(len(docs)), key=lambda i: -scores[i])[:k]
    ctx = "\n\n".join("[%s]\n%s" % (docs[i]["title"].replace("_", " "),
                                    docs[i]["body"][:3000]) for i in top)
    r = client.chat.completions.create(
        model=model, temperature=0,
        messages=[{"role": "system", "content": BASIC_SYS.format(ctx=ctx)},
                  {"role": "user", "content": q}])
    return r.choices[0].message.content.strip(), ctx


def judge(client, model, q, ref, ans):
    r = client.chat.completions.create(
        model=model, temperature=0,
        messages=[{"role": "system", "content": JUDGE_SYS},
                  {"role": "user", "content":
                   "질문: %s\n\n기대 정답: %s\n\n실제 답변: %s" % (q, ref, ans)}],
        response_format={"type": "json_schema",
                         "json_schema": {"name": "j", "strict": True,
                                         "schema": JUDGE_SCHEMA}})
    return json.loads(r.choices[0].message.content)


def flat(s):
    """근거 대조용 정규화 — ★괄호를 «지우지 않는다».

    ⚠1차 측정에서 GraphRAG 의 context recall 이 25~33% 로 찍혔다. 버그였다.
      06_agent.key() 는 「기생충 (영화)」를 「기생충」으로 만들려고 괄호 안을 지우는데,
      GraphRAG 의 근거는 「(봉준호, DIRECTED, 기생충 (영화))」 형식이라
      **삼중항 전체가 괄호로 인식돼 통째로 사라졌다.**
        key('(봉준호, DIRECTED, 기생충 (영화))')  ->  ')'
      ⇒ basic 은 «원문»이라 멀쩡했고 graph 만 0 에 가깝게 나왔다.
        두 방식에 «다른 자»를 댄 셈이다.
    """
    return re.sub(r"[\s_]+", "", s or "").lower()


def ctx_recall(item, ctx):
    """RAGAS 스타일 — 정답 삼중항의 «주어·목적어»가 근거에 들어왔는가."""
    want = item.get("reference_contexts") or []
    if not want:
        return None
    ck = flat(ctx)
    hit = 0
    for t in want:
        if flat(t[0]) in ck and flat(t[2]) in ck:
            hit += 1
    return hit / len(want)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--model", default="gpt-4.1-mini")
    ap.add_argument("--judge-model", default="gpt-4.1-mini")
    args = ap.parse_args()

    from dotenv import load_dotenv
    load_dotenv(os.path.join(HERE, ".env"))
    from openai import OpenAI
    from rank_bm25 import BM25Okapi
    client = OpenAI()

    docs = _bl.load_docs()
    bm25 = BM25Okapi([_bl.tokenize(d["title"].replace("_", " ") + " " + d["body"])
                      for d in docs])
    app = _agent.build(args.model)
    gold = json.load(io.open(GOLD, encoding="utf-8"))

    print("=" * 78)
    print("★basic RAG vs GraphRAG — «같은» 15문항 · «같은» LLM-as-judge")
    print("   basic = BM25 top-%d 문서 본문 · graph = local/path/global" % args.k)
    print("=" * 78)

    agg = collections.defaultdict(lambda: collections.defaultdict(list))
    for it in gold["items"]:
        q, kind, ref = it["user_input"], it["kind"], it["reference"]

        b_ans, b_ctx = basic_rag(client, args.model, docs, bm25, q, args.k)
        s = app.invoke({"q": q})
        g_ans, g_ctx = s.get("answer") or "", s.get("context") or ""

        bj = judge(client, args.judge_model, q, ref, b_ans)
        gj = judge(client, args.judge_model, q, ref, g_ans)
        br, gr = ctx_recall(it, b_ctx), ctx_recall(it, g_ctx)

        agg[kind]["basic"].append(bj["score"])
        agg[kind]["graph"].append(gj["score"])
        if br is not None:
            agg[kind]["basic_cr"].append(br)
            agg[kind]["graph_cr"].append(gr)

        win = "basic" if bj["score"] > gj["score"] else (
            "graph" if gj["score"] > bj["score"] else "=")
        print("%-8s %-4s  basic %.1f  graph %.1f   %s%s"
              % (it["id"], kind, bj["score"], gj["score"],
                 {"basic": "← basic 우세", "graph": "← graph 우세", "=": "무승부"}[win],
                 ("   (ctx recall %.0f%% / %.0f%%)" % (br * 100, gr * 100))
                 if br is not None else ""))

    print("-" * 78)
    print("%-6s %10s %10s   %s" % ("", "basic", "graph", "차이"))
    tot_b = tot_g = 0.0
    tot_n = 0
    for kind in ("단순", "추천", "전역"):
        if kind not in agg:
            continue
        b = sum(agg[kind]["basic"]) / len(agg[kind]["basic"])
        g = sum(agg[kind]["graph"]) / len(agg[kind]["graph"])
        tot_b += sum(agg[kind]["basic"])
        tot_g += sum(agg[kind]["graph"])
        tot_n += len(agg[kind]["basic"])
        mark = "★graph +%.2f" % (g - b) if g > b else (
            "★basic +%.2f" % (b - g) if b > g else "=")
        print("%-6s %10.2f %10.2f   %s (%d문항)" % (kind, b, g, mark, len(agg[kind]["basic"])))
        if agg[kind]["basic_cr"]:
            bc = sum(agg[kind]["basic_cr"]) / len(agg[kind]["basic_cr"])
            gc = sum(agg[kind]["graph_cr"]) / len(agg[kind]["graph_cr"])
            print("%-6s %9.0f%% %9.0f%%   context recall" % ("", bc * 100, gc * 100))
    print("-" * 78)
    print("%-6s %10.2f %10.2f   (%d문항 전체)" % ("전체", tot_b / tot_n, tot_g / tot_n, tot_n))
    print("=" * 78)
    print()
    print("※ 노드 16강이 적은 결론: «단순은 basic 우세, 추천·전역은 GraphRAG 우세»")
    print("  위 표가 그 문장을 우리 데이터에서 재현했는지 본다.")


if __name__ == "__main__":
    main()
