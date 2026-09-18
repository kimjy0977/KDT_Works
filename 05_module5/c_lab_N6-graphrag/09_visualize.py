# -*- coding: utf-8 -*-
"""★4강 누락 메우기 — 그래프를 «그림»으로 본다 + 노드에 «타입»을 붙인다.

4강이 두 가지를 시켰는데 내가 건너뛰었다.

  ① 시각화   *"시각화는 예쁘게 만드는 작업이 아니라 «디버깅 도구»입니다.
              추출이 잘못되면 통계보다 «그림에서 먼저» 티가 납니다."*
  ② 타입     *"「《기생충》의 감독은?」이라는 질문에 «송강호»가 후보로 올라왔을 때,
              타입이 있으면 걸러낼 수 있기 때문입니다."*

타입은 `manifest.json` 의 `by_type` 에 이미 있다 — Film 33 · Person 28 ·
Organization 11 · Award 8. 손으로 적지 않고 «읽어 온다».

    python 09_visualize.py
    python 09_visualize.py --seed 봉준호 --hops 2
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
MANIFEST = os.path.join(HERE, "data", "cinephile_kb_80", "manifest.json")
GRAPH = os.path.join(HERE, "graph", "graph.json")
FONT = os.path.join(HERE, "data", "fonts", "NanumGothic-Regular.ttf")
OUTDIR = os.path.join(HERE, "graph", "figs")

_PAREN = re.compile(r"\([^)]*\)")
COLOR = {"Film": "#E57373", "Person": "#64B5F6", "Organization": "#81C784",
         "Award": "#FFD54F", "?": "#BDBDBD"}


def key(s):
    s = (s or "").replace("_", " ")
    s = _PAREN.sub(" ", s)
    return re.sub(r"\s+", "", s).lower()


def load_types():
    """★manifest 에서 «읽어 온다». 손으로 적으면 자라는 목록을 놓친다."""
    m = json.load(io.open(MANIFEST, encoding="utf-8"))
    types = {}
    for d in m["docs"]:
        types[key(d["title"])] = d.get("type", "?")
    return types, m.get("by_type", {})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", default="기생충")
    ap.add_argument("--hops", type=int, default=2)
    ap.add_argument("--maxnodes", type=int, default=45)
    args = ap.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    import networkx as nx

    # ★한글 폰트 — 1차 시도에서 «전부 깨졌다». addfont + get_name() 만으로는
    #   rcParams 가 DejaVu Sans 를 계속 썼다(Glyph missing 경고 수백 줄).
    #   ⇒ 그릴 때 fontproperties 를 «직접» 넘긴다. 이게 확실하다.
    FP = None
    if os.path.exists(FONT):
        font_manager.fontManager.addfont(FONT)
        FP = font_manager.FontProperties(fname=FONT)
        plt.rcParams["font.family"] = FP.get_name()
        plt.rcParams["font.sans-serif"] = [FP.get_name(), "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    os.makedirs(OUTDIR, exist_ok=True)
    types, by_type = load_types()
    g = json.load(io.open(GRAPH, encoding="utf-8"))
    triples = g["triples"]

    print("=" * 70)
    print("4강 누락 — 시각화 + 노드 타입")
    print("=" * 70)
    print("manifest 의 타입 분포: %s" % by_type)

    # ── ② 타입을 그래프에 «붙인다» ────────────────────────
    ents = {t["s"] for t in triples} | {t["o"] for t in triples}
    typed = {e: types.get(key(e), "?") for e in ents}
    c = collections.Counter(typed.values())
    print("그래프 엔티티 %s개 중 타입이 붙은 것: %s"
          % (format(len(ents), ","), format(len(ents) - c["?"], ",")))
    for k, v in c.most_common():
        print("  %-14s %5d" % (k, v))
    print()
    print("★타입이 없는 것이 %s개 — 배역·장르·수상명 등 «문서가 없는» 엔티티다."
          % format(c["?"], ","))
    print("  4강이 말한 「타입으로 걸러낸다」를 하려면 이쪽도 분류해야 한다.")

    out = {"typed": typed, "by_type_manifest": by_type,
           "counts": dict(c)}
    io.open(os.path.join(HERE, "graph", "node_types.json"), "w",
            encoding="utf-8", newline="").write(
        json.dumps(out, ensure_ascii=False, indent=1))

    # ── ① 그림 — 씨앗에서 N홉 ────────────────────────────
    G = nx.Graph()
    for t in triples:
        G.add_edge(t["s"], t["o"], r=t["r"])

    seedk = key(args.seed)
    seeds = [n for n in G.nodes if key(n) == seedk] or \
            [n for n in G.nodes if seedk in key(n)]
    if not seeds:
        print("⚠ 씨앗을 못 찾음: %s" % args.seed)
        return
    seed = seeds[0]

    sub = {seed}
    frontier = {seed}
    for _ in range(args.hops):
        nxt = set()
        for n in frontier:
            nxt |= set(G.neighbors(n))
        sub |= nxt
        frontier = nxt
        if len(sub) > args.maxnodes * 4:
            break
    deg = dict(G.degree())
    sub = sorted(sub, key=lambda n: -(deg.get(n, 0)))[: args.maxnodes]
    if seed not in sub:
        sub.append(seed)
    H = G.subgraph(sub)

    pos = nx.spring_layout(H, k=0.9, seed=42, iterations=80)
    plt.figure(figsize=(14, 10))
    nx.draw_networkx_edges(H, pos, alpha=0.25, width=1.0)
    for tp in ("Film", "Person", "Organization", "Award", "?"):
        ns = [n for n in H.nodes if typed.get(n, "?") == tp]
        if not ns:
            continue
        nx.draw_networkx_nodes(H, pos, nodelist=ns, node_color=COLOR[tp],
                               node_size=[220 + 26 * deg.get(n, 1) for n in ns],
                               label="%s (%d)" % (tp, len(ns)), alpha=0.92)
    nx.draw_networkx_nodes(H, pos, nodelist=[seed], node_color="none",
                           edgecolors="#D32F2F", linewidths=3,
                           node_size=[300 + 26 * deg.get(seed, 1)])
    nx.draw_networkx_labels(H, pos, font_size=8, font_family=(FP.get_name() if FP else None),
                            labels={n: (n[:14]) for n in H.nodes})
    plt.legend(loc="upper left", fontsize=9, prop=FP)
    plt.title("「%s」 에서 %d홉 · 노드 %d개 (빨간 테두리 = 씨앗)"
              % (seed, args.hops, H.number_of_nodes()), fontsize=13, fontproperties=FP)
    plt.axis("off")
    plt.tight_layout()
    fn = os.path.join(OUTDIR, "graph_%s_%dhop.png"
                      % (re.sub(r"[^가-힣A-Za-z0-9]", "", seed)[:20], args.hops))
    plt.savefig(fn, dpi=130)
    plt.close()
    print()
    print("그림: %s  (노드 %d · 엣지 %d)"
          % (os.path.relpath(fn, HERE).replace(os.sep, "/"),
             H.number_of_nodes(), H.number_of_edges()))

    # ── ★디버깅 도구로 써 본다 — 타입이 이상한 엣지 ────────
    print()
    print("-" * 70)
    print("★그림이 아니라 «타입»으로 잡은 이상한 관계 (4강이 말한 그 용도)")
    print("-" * 70)
    bad = []
    for t in triples:
        ts, to = typed.get(t["s"], "?"), typed.get(t["o"], "?")
        if t["r"] == "DIRECTED" and ts == "Film":
            bad.append(("DIRECTED 의 주어가 Film", t))
        elif t["r"] == "ACTED_IN" and to == "Person":
            bad.append(("ACTED_IN 의 목적어가 Person", t))
    if bad:
        cb = collections.Counter(x[0] for x in bad)
        for k, v in cb.items():
            print("  %-28s %3d건" % (k, v))
        for lab, t in bad[:6]:
            print("    (%s, %s, %s)  ←%s" % (t["s"], t["r"], t["o"], t.get("origin", "")))
    else:
        print("  없음")
    print("=" * 70)


if __name__ == "__main__":
    main()
