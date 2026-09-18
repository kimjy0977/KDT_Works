# -*- coding: utf-8 -*-
"""★10~11강 — 완성된 그래프 살펴보기 · 커뮤니티 탐지 → 전역 보고서.

10강: 그래프가 «어떻게 생겼는지» 숫자로 본다.
11강: *"커뮤니티를 찾아 「이 자료 전체에 어떤 집단이 있는가」 같은 전역 질문에
      답할 요약을 «미리» 만들어 둡니다."*

★왜 «미리» 만드나 — 전역 질문은 문서 몇 개를 찾아서 답할 수 있는 게 아니다.
  전체를 봐야 한다. 질문이 올 때마다 2,103개 삼중항을 LLM 에 넣을 수는 없다.
  ⇒ 색인 시점에 요약해 둔다. GraphRAG 원논문의 아이디어가 이것이다.

★전역-15 는 LLM 이 «필요 없다» — 감독-영화-배우 삼자를 조인해서 세면 나온다.
  BM25 로는 절대 못 하는 일이고, 그래프에서는 집계 한 번이다.

    python 05_community.py
    python 05_community.py --no-llm     # 요약 생성 없이 구조만
"""
import argparse
import collections
import io
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "graph", "graph.json")
OUT = os.path.join(HERE, "graph", "communities.json")
PAIRS = os.path.join(HERE, "graph", "director_actor_pairs.json")

SUM_SYS = """너는 지식 그래프의 한 «집단»을 설명하는 요약가다.

주어진 것은 그 집단에 속한 인물·작품과 그들 사이의 관계다.
아래를 3~5문장으로 적는다.

- 이 집단을 한 마디로 무엇이라 부를 수 있는가 (예: 「봉준호를 중심으로 한 …」)
- 중심 인물과 대표 작품
- 두드러진 장르·주제·수상 경향

규칙
- 주어진 관계에 «있는 것»만 쓴다. 아는 것을 보태지 않는다.
- 숫자를 지어내지 않는다."""


def build_graph(triples):
    import networkx as nx
    G = nx.Graph()
    for t in triples:
        s, o, r = t["s"], t["o"], t["r"]
        G.add_node(s)
        G.add_node(o)
        if G.has_edge(s, o):
            G[s][o]["rels"].add(r)
            G[s][o]["weight"] += 1
        else:
            G.add_edge(s, o, rels={r}, weight=1)
    return G


def director_actor_pairs(triples, top=15):
    """★전역-15 — 감독-영화-배우 삼자 조인. LLM 없이 «집계»로 푼다."""
    directed = collections.defaultdict(set)   # 영화 -> 감독들
    acted = collections.defaultdict(set)      # 영화 -> 배우들
    for t in triples:
        if t["r"] == "DIRECTED":
            directed[t["o"]].add(t["s"])
        elif t["r"] == "ACTED_IN":
            acted[t["o"]].add(t["s"])
    pair = collections.Counter()
    films = collections.defaultdict(set)
    for film in set(directed) & set(acted):
        for d in directed[film]:
            for a in acted[film]:
                # ★자기 자신은 «조합»이 아니다. 「봉준호–봉준호 4편」이 나왔었다.
                #   원인은 추출 쪽 — 「한국영화아카데미」 문서의 «졸업생 필모그래피»
                #   (봉준호 : 플란다스의 개, 살인의 추억 …) 를 ACTED_IN 으로 읽었다.
                #   ⚠02_extract_probe 에 넣은 「배우: 배역 역 목록도 출연」 규칙의 부작용이다.
                #     기생충에서 12개를 살린 그 한 줄이 여기서는 7개를 잘못 만들었다.
                if d == a:
                    continue
                pair[(d, a)] += 1
                films[(d, a)].add(film)
    rows = [{"director": d, "actor": a, "n": n, "films": sorted(films[(d, a)])}
            for (d, a), n in pair.most_common() if n >= 2]
    return rows[:top]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--model", default=os.environ.get("SUMMARY_MODEL", "gpt-4.1-mini"))
    ap.add_argument("--minsize", type=int, default=6, help="이보다 작은 커뮤니티는 요약하지 않는다")
    args = ap.parse_args()

    g = json.load(io.open(SRC, encoding="utf-8"))
    triples = g["triples"]
    G = build_graph(triples)

    # ── 10강: 그래프를 «본다» ───────────────────────────
    import networkx as nx
    deg = dict(G.degree())
    top_deg = sorted(deg.items(), key=lambda x: -x[1])[:12]
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    print("=" * 70)
    print("10강 완성된 그래프")
    print("=" * 70)
    print("노드 %s · 엣지 %s · 삼중항 %s"
          % (format(G.number_of_nodes(), ","), format(G.number_of_edges(), ","),
             format(len(triples), ",")))
    print("연결 요소 %d개 · 가장 큰 덩어리에 %s개 (%.1f%%)"
          % (len(comps), format(len(comps[0]), ","),
             len(comps[0]) / G.number_of_nodes() * 100))
    print()
    print("차수 상위 (허브):")
    for n, d in top_deg:
        print("  %-28s %3d" % (n[:28], d))

    # ── ★전역-15: 감독-배우 반복 조합 ──────────────────
    pairs = director_actor_pairs(triples)
    io.open(PAIRS, "w", encoding="utf-8", newline="").write(
        json.dumps(pairs, ensure_ascii=False, indent=1))
    print()
    print("-" * 70)
    print("★전역-15 감독–배우 반복 조합 (LLM 없이 «집계»로 뽑았다)")
    print("-" * 70)
    for r in pairs[:15]:
        print("  %-10s – %-10s %d편  %s"
              % (r["director"][:10], r["actor"][:10], r["n"],
                 " · ".join(f[:14] for f in r["films"][:4])))

    # ── 11강: 커뮤니티 ─────────────────────────────────
    import community as community_louvain
    part = community_louvain.best_partition(G, random_state=42)
    groups = collections.defaultdict(list)
    for node, cid in part.items():
        groups[cid].append(node)
    sizes = sorted(((cid, len(ns)) for cid, ns in groups.items()), key=lambda x: -x[1])
    print()
    print("-" * 70)
    print("11강 커뮤니티 탐지 (Louvain) — %d개 · 모듈러리티 %.3f"
          % (len(groups), community_louvain.modularity(part, G)))
    print("-" * 70)
    for cid, n in sizes[:10]:
        head = sorted(groups[cid], key=lambda x: -deg[x])[:5]
        print("  #%-3d %3d개  %s" % (cid, n, " · ".join(h[:16] for h in head)))

    big = [cid for cid, n in sizes if n >= args.minsize]
    print()
    print("  요약 대상: %d개 (크기 %d 이상)" % (len(big), args.minsize))

    out = {"n_communities": len(groups),
           "modularity": community_louvain.modularity(part, G),
           "communities": []}

    if args.no_llm:
        for cid in big:
            out["communities"].append({"id": cid, "size": len(groups[cid]),
                                       "members": sorted(groups[cid], key=lambda x: -deg[x])[:40]})
    else:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(HERE, ".env"))
        from openai import OpenAI
        client = OpenAI()
        tin = tout = 0
        print()
        for i, cid in enumerate(big, 1):
            members = set(groups[cid])
            facts = ["(%s, %s, %s)" % (t["s"], t["r"], t["o"])
                     for t in triples if t["s"] in members and t["o"] in members]
            body = "\n".join(facts[:200])
            r = client.chat.completions.create(
                model=args.model,
                messages=[{"role": "system", "content": SUM_SYS},
                          {"role": "user", "content": body}],
                temperature=0)
            tin += r.usage.prompt_tokens
            tout += r.usage.completion_tokens
            summ = r.choices[0].message.content.strip()
            out["communities"].append({
                "id": cid, "size": len(groups[cid]), "n_facts": len(facts),
                "members": sorted(groups[cid], key=lambda x: -deg[x])[:40],
                "summary": summ})
            print("  [%d/%d] #%-3d %3d개 · 사실 %3d개 → 요약 %d자"
                  % (i, len(big), cid, len(groups[cid]), len(facts), len(summ)))
        print()
        print("  요약 토큰: 입력 %s · 출력 %s" % (format(tin, ","), format(tout, ",")))

    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(out, ensure_ascii=False, indent=1))
    print("=" * 70)
    print("저장: graph/communities.json · graph/director_actor_pairs.json")


if __name__ == "__main__":
    main()
