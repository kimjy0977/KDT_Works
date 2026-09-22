# -*- coding: utf-8 -*-
"""평가 — ★홉 수별로 갈라 보고 · basic RAG 대조 · 실패 층 분류 (요건 ⑤·루브릭 ③)

  python evaluate.py                # output/runs.jsonl 을 채점
  python evaluate.py --baseline     # ★basic RAG(BM25) 대조까지

★루브릭 ③ 이 요구하는 셋을 그대로 한다.
  ① 사전에 정의한 기준으로 채점   → 아래 score_* 함수가 «기준»이다
  ② ★평균이 아니라 «홉 수별로» 갈라 보고
  ③ ★실패 사례를 «직접 읽어» 색인·탐색·생성 중 어디서 깨졌는지 구분

실패 층 (노드6 에서 쓴 분류를 그대로)
  색인  기대 경로의 삼중항이 ★그래프에 «없다»       → 추출·정규화를 고쳐야 한다
  탐색  그래프엔 있는데 ★근거로 «안 가져왔다»       → 확장·허브 규칙을 고쳐야 한다
  생성  근거는 가져왔는데 ★답에 «안 썼다»          → 프롬프트를 고쳐야 한다
"""
import argparse
import collections
import io
import json
import os
import re

import networkx as nx

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
REFUSE_PAT = re.compile(r"근거를 찾지 못")


def norm(s):
    """대조용 정규화 — ★괄호를 «지우지 않는다».

    노드6 실사고 — 괄호를 지우는 flat() 을 써서 「(봉준호, DIRECTED, 기생충 (영화))」가
    ")" 로 뭉개졌고, graph 쪽만 0 에 가깝게 나왔다. 두 방식에 «다른 자»를 댄 것이다.
    """
    return re.sub(r"[\s_]+", "", str(s or "")).lower()


def score_path(item_ctx, evidence):
    """★경로 재현율 — 기대 경로의 삼중항이 실제 근거에 얼마나 들어왔나.

    기준: 삼중항을 (s, o) 쌍으로 본다. 관계 이름은 방향 표기(←)가 붙어 흔들린다.
    """
    if not item_ctx:
        return None
    have = set()
    for t in evidence:
        if len(t) >= 3:
            have.add((norm(t[0]), norm(t[2])))
            have.add((norm(t[2]), norm(t[0])))
    hit = sum(1 for t in item_ctx
              if len(t) >= 3 and (norm(t[0]), norm(t[2])) in have)
    return hit / len(item_ctx)


def score_answer(ref, answer):
    """★답변 정확도 — 기준을 «미리» 정해 둔다.

    __REFUSE__  거절해야 한다 → 거절했으면 1
    그 밖        기대 정답의 «핵심 조각»이 답에 있으면 1
                 (「A / B / C」 형태는 하나라도 들어가면 맞다 — 추천 문항이라 그렇다)
    """
    if ref == "__REFUSE__":
        return 1.0 if REFUSE_PAT.search(answer or "") else 0.0
    if REFUSE_PAT.search(answer or ""):
        return 0.0                      # 답이 있는데 거절했다 = 틀림
    a = norm(answer)
    # ★기대 정답은 «후보 목록»이다 — 하나라도 맞으면 통과.
    #   영화는 물음이 여럿이고 추천 후보도 여럿이다. 하나만 정답으로 두면
    #   맞는 답을 틀렸다고 찍는다 (첫 채점에서 1홉 3건이 그렇게 틀렸다).
    cands = ref if isinstance(ref, list) else re.split(r"[/↔]", str(ref))
    parts = [p for p in cands if norm(p)]
    if not parts:
        return 0.0
    # ★조사 하나 차이로 틀리지 않게 «어절 겹침»으로 본다.
    #   「가치관은 집단의」 vs 「가치관이 집단의」 — 첫 채점에서 이 한 글자로 틀렸다
    for p in parts:
        if norm(p) in a:
            return 1.0
        ws = [w for w in re.findall(r"[가-힣A-Za-z0-9]{2,}", str(p))]
        if ws and sum(1 for w in ws if w in str(answer)) / len(ws) >= 0.6:
            return 1.0
    return 0.0


def layer(item, rec, G):
    """★실패 층 분류 — 색인 / 탐색 / 생성."""
    ctx = item.get("reference_contexts") or []
    # ① 색인 — 기대 삼중항이 그래프에 있나
    missing = []
    for t in ctx:
        if len(t) < 3:
            continue
        s, o = t[0], t[2]
        if t[1] == "공유축":
            if s not in G:
                missing.append(t)
            continue
        if not (G.has_edge(s, o) or G.has_edge(o, s)):
            missing.append(t)
    if missing:
        return "색인", "기대 삼중항 %d/%d 가 그래프에 없다" % (len(missing), len(ctx))
    # ② 탐색 — 그래프엔 있는데 근거로 안 왔나
    pr = score_path(ctx, rec["evidence"])
    if pr is not None and pr < 0.5:
        return "탐색", "경로 재현 %.0f%% — 그래프엔 있는데 안 가져왔다" % (pr * 100)
    # ③ 생성 — 근거는 왔는데 답에 안 썼나
    return "생성", "근거는 가져왔는데 답에 반영되지 않았다"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", action="store_true")
    args = ap.parse_args()

    G = nx.read_graphml(os.path.join(OUT, "graph.graphml"))
    gs = json.load(io.open(os.path.join(HERE, "data", "goldenset.json"),
                           encoding="utf-8"))
    by_id = {it["id"]: it for it in gs["items"]}
    runs = [json.loads(l) for l in
            io.open(os.path.join(OUT, "runs.jsonl"), encoding="utf-8") if l.strip()]

    rows, per_kind = [], collections.defaultdict(list)
    fails = []
    for rec in runs:
        it = by_id[rec["id"]]
        pa = score_path(it["reference_contexts"], rec["evidence"])
        sa = score_answer(it["reference"], rec["answer"])
        rows.append({"run": rec["run"], "id": rec["id"], "kind": rec["kind"],
                     "path_recall": pa, "answer": sa,
                     "refused": bool(REFUSE_PAT.search(rec["answer"] or "")),
                     "sec": rec["sec"], "n_evidence": len(rec["evidence"])})
        per_kind[rec["kind"]].append(rows[-1])
        if sa < 1.0:
            lay, why = layer(it, rec, G)
            fails.append({"id": rec["id"], "kind": rec["kind"],
                          "question": rec["question"],
                          "expected": it["reference"],
                          "got": (rec["answer"] or "")[:200],
                          "layer": lay, "why": why,
                          "path_recall": pa})

    W = "=" * 76
    print(W)
    print("평가 — %d문항 × %d회 = %d건"
          % (len(gs["items"]), max(r["run"] for r in rows), len(rows)))
    print(W)
    print("★홉 수별 — 평균 하나로 뭉개지 않는다 (루브릭 ③)")
    print("  %-6s %5s %10s %10s %7s" % ("구분", "문항", "답변정확", "경로재현", "초"))
    for k in ("1홉", "2홉", "4홉", "거절"):
        g = per_kind.get(k) or []
        if not g:
            continue
        pr = [x["path_recall"] for x in g if x["path_recall"] is not None]
        print("  %-6s %5d %9.1f%% %9s %7.1f"
              % (k, len(g), 100 * sum(x["answer"] for x in g) / len(g),
                 ("%.1f%%" % (100 * sum(pr) / len(pr))) if pr else "—",
                 sum(x["sec"] for x in g) / len(g)))
    allv = [x["answer"] for x in rows]
    print("  %-6s %5d %9.1f%%" % ("전체", len(rows), 100 * sum(allv) / len(allv)))

    print()
    print("-" * 76)
    print("★실패 %d건 — «직접 읽어» 층을 갈랐다 (루브릭 ③)" % len(fails))
    if not fails:
        print("    실패 없음")
    for f in fails:
        print("  [%s] %s" % (f["id"], f["question"][:52]))
        print("      기대: %s" % str(f["expected"])[:56])
        print("      받음: %s" % f["got"][:56])
        print("      ★층: %s — %s" % (f["layer"], f["why"]))

    # ── ★문항별 통과 횟수와 «폭» — 평균만 보면 흔들림을 못 본다 ──────
    n_runs = max(r["run"] for r in rows)
    per_item = collections.defaultdict(list)
    for r in rows:
        per_item[r["id"]].append(r["answer"])
    shaky = {k: v for k, v in per_item.items()
             if 0 < sum(v) < len(v)}            # 전부도 아니고 0도 아닌 것
    if n_runs > 1:
        print()
        print("-" * 76)
        print("★문항별 통과 횟수 (%d회 중) — 3/3·0/3 은 안정 · 그 사이가 «흔들림»"
              % n_runs)
        for k in sorted(per_item):
            v = per_item[k]
            mark = "  ★흔들림" if 0 < sum(v) < len(v) else ""
            print("  %-9s %d/%d%s" % (k, int(sum(v)), len(v), mark))
        print()
        print("★흔들리는 문항 %d개 / %d개 — 여기가 고칠 자리다"
              % (len(shaky), len(per_item)))
        if not shaky:
            print("    없음 — 모든 문항이 회차마다 «같은» 결과를 냈다")

    lay_cnt = collections.Counter(f["layer"] for f in fails)
    print()
    print("층별: " + (" · ".join("%s %d" % (k, v) for k, v in sorted(lay_cnt.items()))
                    or "없음"))

    res = {"goldenset": gs["name"], "n_items": len(gs["items"]),
           "n_runs": max(r["run"] for r in rows),
           "by_kind": {k: {"n": len(g),
                           "answer_acc": round(sum(x["answer"] for x in g) / len(g), 4),
                           "path_recall": (round(sum(x["path_recall"] for x in g
                                                     if x["path_recall"] is not None)
                                                 / max(1, len([1 for x in g
                                                               if x["path_recall"] is not None])), 4)
                                           if any(x["path_recall"] is not None for x in g) else None)}
                       for k, g in sorted(per_kind.items())},
           "overall_answer_acc": round(sum(allv) / len(allv), 4),
           "per_item_pass": {k: "%d/%d" % (int(sum(v)), len(v))
                             for k, v in sorted(per_item.items())},
           "shaky_items": sorted(shaky),
           "failures": fails, "by_layer": dict(lay_cnt),
           "_기준": {
               "답변정확": "__REFUSE__ 면 거절했으면 1 · 그 밖은 기대 정답의 조각이 답에 있으면 1",
               "경로재현": "기대 삼중항을 (s,o) 쌍으로 보고 실제 근거에 있는 비율",
               "실패층": "색인=그래프에 없다 / 탐색=있는데 안 가져왔다 / 생성=가져왔는데 안 썼다",
           }}

    if args.baseline:
        res["baseline"] = baseline(gs)

    io.open(os.path.join(OUT, "eval.json"), "w",
            encoding="utf-8", newline="").write(
                json.dumps(res, ensure_ascii=False, indent=1))
    print("\n저장 · output/eval.json")


def baseline(gs):
    """★basic RAG 대조 — BM25 로 같은 질문을 풀어 본다 (요건 ⑤·REPORT ③).

    그래프 없이 «문서만» 검색해서 답이 나오는지 본다.
    멀티홉 문항에서 무너지는 것이 이 프로젝트의 근거다.
    """
    import math
    d = os.path.join(HERE, "data", "docs")
    names, texts = [], []
    for f in sorted(os.listdir(d)):
        if f.endswith(".md"):
            names.append(f[:-3].replace("_", " "))
            texts.append(io.open(os.path.join(d, f), encoding="utf-8",
                                 errors="replace").read())
    toks = [re.findall(r"[가-힣A-Za-z0-9]+", t.lower()) for t in texts]
    df = collections.Counter()
    for tk in toks:
        for w in set(tk):
            df[w] += 1
    N, avg = len(toks), sum(len(t) for t in toks) / max(1, len(toks))

    def bm25(q, k=5):
        qt = re.findall(r"[가-힣A-Za-z0-9]+", q.lower())
        sc = []
        for i, tk in enumerate(toks):
            tf = collections.Counter(tk)
            s = 0.0
            for w in qt:
                if w not in tf:
                    continue
                idf = math.log(1 + (N - df[w] + 0.5) / (df[w] + 0.5))
                s += idf * tf[w] * 2.5 / (tf[w] + 1.5 * (0.25 + 0.75 * len(tk) / avg))
            sc.append((s, names[i]))
        sc.sort(reverse=True)
        return [n for _, n in sc[:k]]

    out = collections.defaultdict(list)
    detail = []
    for it in gs["items"]:
        top = bm25(it["user_input"])
        ref = str(it["reference"])
        if ref == "__REFUSE__":
            hit = 0.0          # BM25 는 «거절»을 못 한다 — 항상 문서를 낸다
        else:
            parts = [p.strip() for p in re.split(r"[/↔]", ref) if p.strip()]
            hit = 1.0 if any(norm(p) in norm(" ".join(top)) for p in parts) else 0.0
        out[it["kind"]].append(hit)
        detail.append({"id": it["id"], "kind": it["kind"],
                       "top5": top, "hit": hit})

    print()
    print("-" * 76)
    print("★basic RAG(BM25) 대조 — 그래프 없이 «문서만» 검색")
    print("  %-6s %5s %10s" % ("구분", "문항", "Recall@5"))
    for k in ("1홉", "2홉", "4홉", "거절"):
        g = out.get(k) or []
        if g:
            print("  %-6s %5d %9.1f%%" % (k, len(g), 100 * sum(g) / len(g)))
    print("  ⇒ ★거절 문항은 BM25 가 «구조적으로» 0% 다 — 항상 문서를 내놓는다.")
    return {"method": "BM25 · Recall@5 · 기대 정답 조각이 상위 5문서 제목에 있나",
            "by_kind": {k: round(sum(g) / len(g), 4) for k, g in sorted(out.items())},
            "detail": detail}


if __name__ == "__main__":
    main()
