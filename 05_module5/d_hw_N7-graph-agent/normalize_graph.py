# -*- coding: utf-8 -*-
"""②정제·병합 → 지식 그래프 (요건 §필수구현 ③ 「정규화」)

  python normalize_graph.py

무엇을 하나
  ① ★두 가치가 붙은 이름을 쪼갠다 — 「진실과 정의」 → 「진실」 + 「정의 실현」
  ② ★가치를 «축·극»으로 합친다 — 이름이 아니라 축이 같으면 한 노드다
  ③ self-loop 를 버린다 (노드6 실사고 — 같은 것끼리 이어지면 경로가 헛돈다)
  ④ ★같은 축의 «같은 극»끼리 부딪친 것은 버린다 — 충돌이 아니다
  ⑤ 축이 «다른» 충돌은 버리지 않고 «가로지르는 충돌»로 따로 센다
  ⑥ graphml 로 내보낸다

★적용 전/후를 같은 잣대로 재서 찍는다. 숫자만 보지 말고 «다리»의 실물을 본다.
"""
import collections
import io
import json
import os
import re

import networkx as nx

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
CFG = json.load(io.open(os.path.join(HERE, "config.json"), encoding="utf-8"))


def load():
    v = json.load(io.open(os.path.join(HERE, "values.json"), encoding="utf-8"))
    raw = json.load(io.open(os.path.join(OUT, "triples_raw.json"),
                           encoding="utf-8"))
    return v, raw


def split_map(v):
    return v.get("_split", {})


def axes_of(name, v):
    return [tuple(a) for a in v["가치"].get(name, [])]


SPLIT_RE = re.compile(r"^(.{2,14}?)\s*(?:와|과)\s+(.{2,14})$")


def expand(name, v, tally=None):
    """★붙은 이름을 쪼갠다 — 「개인의 양심과 국가의 요구」는 가치 «둘»이다.

    ① 사전의 _split (LLM 이 쪼갠 것)
    ② ★규칙 — 「A와/과 B」. 양쪽이 «둘 다» 사전에 있을 때만 채택한다.
      LLM 이 split 을 28개 중 2개만 썼다. 규칙은 좁지만 정확하다
      (노드6 에서 배운 것 — 「규칙은 좁지만 정확하고, LLM 은 넓지만 흔들린다」).
      ⚠양쪽 다 사전에 있어야 한다는 조건이 «안전장치»다 —
        「용서와 화해」처럼 한쪽만 있으면 쪼개지 않는다. 억지로 쪼개면 뜻이 바뀐다.
    """
    sp = split_map(v).get(name)
    if sp:
        out = [s for s in sp if s in v["가치"]]
        if out:
            return out
    m = SPLIT_RE.match(name.strip())
    if m:
        a, b = m.group(1).strip(), m.group(2).strip()
        if a in v["가치"] and b in v["가치"]:
            if tally is not None:
                tally.append((name, a, b))
            return [a, b]
    return [name]


def canon_pair(a, b, v):
    """두 가치의 충돌을 «축·극»으로 정규화.

    ("축", (극1,극2))  같은 축의 다른 극  → 다리가 된다
    "같은극"           같은 축의 같은 극  → 충돌이 아니다
    "축다름"           축이 서로 다르다   → ★정규화 불가. 버리지 않는다
    "미분류"           한쪽이 사전에 없다
    """
    A, B = axes_of(a, v), axes_of(b, v)
    if not A or not B:
        return "미분류"
    same = False
    for ax_a, p_a in A:
        for ax_b, p_b in B:
            if ax_a == ax_b:
                if p_a != p_b:
                    return (ax_a, tuple(sorted([p_a, p_b])))
                same = True
    return "같은극" if same else "축다름"


def main():
    v, raw = load()
    T = raw["triples"]

    # ── 적용 «전» ────────────────────────────────────────────────────
    before = collections.defaultdict(set)
    for x in T:
        if x["r"] == "CONFLICTS_WITH":
            before[tuple(sorted([x["s"], x["o"]]))].add(x["origin"])
    before_multi = {k: s for k, s in before.items() if len(s) >= 2}

    # ── 정제 ─────────────────────────────────────────────────────────
    G = nx.DiGraph()
    bridges = collections.defaultdict(set)      # (축,극쌍) → 영화들
    cross, same_pole, unmapped, rule_split = [], [], [], []
    selfloop = 0
    q_of_film = collections.defaultdict(set)

    for x in T:
        s, o, r, org = x["s"], x["o"], x["r"], x["origin"]

        if r == "ASKS":
            G.add_node(org, kind="Film")
            G.add_node(o, kind="Question")
            G.add_edge(org, o, rel="ASKS", origin=org)
            q_of_film[org].add(o)

        elif r == "INVOKES_VALUE":
            for val in expand(o, v, rule_split):                     # ★쪼갠다
                if val == s:
                    selfloop += 1
                    continue
                G.add_node(s, kind="Question")
                ax = axes_of(val, v)
                G.add_node(val, kind="Value",
                           axes=";".join("%s/%s" % a for a in ax) or "미분류")
                G.add_edge(s, val, rel="INVOKES_VALUE", origin=org)

        elif r == "CONFLICTS_WITH":
            for a in expand(s, v, rule_split):
                for b in expand(o, v, rule_split):
                    if a == b:
                        selfloop += 1
                        continue
                    key = canon_pair(a, b, v)
                    if isinstance(key, tuple):
                        bridges[key].add(org)
                        G.add_node(a, kind="Value")
                        G.add_node(b, kind="Value")
                        G.add_edge(a, b, rel="CONFLICTS_WITH", origin=org,
                                   axis=key[0])
                        G.add_edge(b, a, rel="CONFLICTS_WITH", origin=org,
                                   axis=key[0])
                    elif key == "같은극":
                        same_pole.append((org, a, b))
                    elif key == "축다름":
                        cross.append((org, a, b))
                        # ★add_node 를 «먼저» 한다 — 엣지만 걸면 kind 없는 노드가 생긴다
                        #   (첫 실행에서 kind「?」 노드 27개가 이렇게 생겼다)
                        for n_ in (a, b):
                            ax_ = axes_of(n_, v)
                            G.add_node(n_, kind="Value",
                                       axes=";".join("%s/%s" % t_ for t_ in ax_)
                                            or "미분류")
                        G.add_edge(a, b, rel="CONFLICTS_WITH", origin=org,
                                   axis="가로지름")
                        G.add_edge(b, a, rel="CONFLICTS_WITH", origin=org,
                                   axis="가로지름")
                    else:
                        unmapped.append((org, a, b))

    after_multi = {k: s for k, s in bridges.items() if len(s) >= 2}

    W = "=" * 76
    print(W)
    print("정제 — 문서 %d건 · 삼중항 %d개" % (raw["n_docs"], len(T)))
    print(W)
    print("적용 전  충돌쌍 %4d개 중 «2편 이상» %d개"
          % (len(before), len(before_multi)))
    print("적용 후  축·극쌍 %3d개 중 «2편 이상» ★%d개"
          % (len(bridges), len(after_multi)))
    print()
    print("★다리 — 여러 영화가 «같은 대립»을 공유하는 자리")
    for (ax, poles), films in sorted(after_multi.items(),
                                     key=lambda kv: -len(kv[1]))[:10]:
        print("  [%s] %s ↔ %s   ★%d편" % (ax, poles[0], poles[1], len(films)))
        print("      %s" % " · ".join(sorted(films)[:6]))

    print()
    print("-" * 76)
    print("★축을 «가로지르는» 충돌 %d건 — 한 축으로는 못 담는다" % len(cross))
    for f, a, b in cross[:6]:
        print("    %-14s %s ↔ %s" % (f, a, b))
    print("⚠같은 극이라 «충돌 아님» %d건 · 사전에 없어 둔 것 %d건 · self-loop %d건"
          % (len(same_pole), len(unmapped), selfloop))
    uniq = sorted(set(rule_split))
    print("★규칙으로 쪼갠 이름 %d종 (「A와/과 B」 · 양쪽이 둘 다 사전에 있을 때만)" % len(uniq))
    for n_, a_, b_ in uniq[:8]:
        print("    %-26s → %s + %s" % (n_, a_, b_))

    print()
    print("그래프 — 노드 %d · 엣지 %d" % (G.number_of_nodes(), G.number_of_edges()))
    kinds = collections.Counter(d.get("kind", "?") for _, d in G.nodes(data=True))
    print("  " + " · ".join("%s %d" % (k, n) for k, n in sorted(kinds.items())))

    nx.write_graphml(G, os.path.join(OUT, "graph.graphml"))
    io.open(os.path.join(OUT, "graph_stats.json"), "w",
            encoding="utf-8", newline="").write(json.dumps({
                "n_docs": raw["n_docs"], "n_triples": len(T),
                "before": {"pairs": len(before), "multi": len(before_multi)},
                "after": {"pairs": len(bridges), "multi": len(after_multi)},
                "bridges": {"[%s] %s↔%s" % (ax, p[0], p[1]): sorted(f)
                            for (ax, p), f in sorted(
                                after_multi.items(), key=lambda kv: -len(kv[1]))},
                "cross_axis": [{"film": f, "a": a, "b": b} for f, a, b in cross],
                "same_pole_dropped": [{"film": f, "a": a, "b": b}
                                      for f, a, b in same_pole],
                "unmapped": [{"film": f, "a": a, "b": b} for f, a, b in unmapped],
                "selfloop_dropped": selfloop,
                "rule_split": [{"원래": n_, "쪼갠 것": [a_, b_]} for n_, a_, b_ in sorted(set(rule_split))],
                "nodes": G.number_of_nodes(), "edges": G.number_of_edges(),
                "node_kinds": dict(kinds),
            }, ensure_ascii=False, indent=1))
    print("저장 · output/graph.graphml · output/graph_stats.json")


if __name__ == "__main__":
    main()
