# -*- coding: utf-8 -*-
"""평가셋 만들기 (요건 ②) — 문항마다 기대정답·★기대경로·원문근거

  python make_goldenset.py

★어떻게 만드나 — «지어내지 않는다».
  그래프에서 «참인 경로»를 먼저 뽑고, 그 경로로만 답할 수 있는 질문을 붙인다.
  ⇒ 기대 경로가 «먼저» 있고 질문이 나중이다. 그래서 채점이 가능하다.

★홉 수별로 갈라 짓는다 — 루브릭 ③이 「평균이 아니라 홉 수별로」를 요구한다.
  1홉  Film ─ASKS→ Question              「이 영화는 무엇을 묻나」
  2홉  Film ─ASKS→ Q ─INVOKES_VALUE→ V   「이 영화가 세운 가치는」
  4홉  Film ─…→ V ←…─ Film'              ★「같은 대립을 다룬 다른 영화는」
  ★거절  코퍼스에 «없는» 것을 묻는다 — 지어내는지 본다 (루브릭 ②)
"""
import io
import json
import os
import random
import re

import networkx as nx

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
DATA = os.path.join(HERE, "data")


def load():
    G = nx.read_graphml(os.path.join(OUT, "graph.graphml"))
    st = json.load(io.open(os.path.join(OUT, "graph_stats.json"),
                           encoding="utf-8"))
    raw = json.load(io.open(os.path.join(OUT, "triples_raw.json"),
                            encoding="utf-8"))
    return G, st, raw


def evidence(raw, film, limit=160):
    """원문 근거 — 그 영화 문서의 첫 서술 문단을 쓴다."""
    p = os.path.join(DATA, "docs")
    for f in sorted(os.listdir(p)):
        t = io.open(os.path.join(p, f), encoding="utf-8",
                    errors="replace").read()
        if t.startswith("# %s" % film) or f[:-3].replace("_", " ").startswith(film):
            body = re.sub(r"^#.*$|^분류:.*$", "", t, flags=re.M).strip()
            body = re.sub(r"\s+", " ", body)
            return body[:limit] + ("…" if len(body) > limit else "")
    return ""



def _axis_peers(G, film, label, fallback):
    """★그 영화가 걸친 «모든 축»의 공유 영화 전부.

    ⚠처음엔 label 의 축 «하나»만 봤다. 그랬더니 에이전트가 «다른 축»으로
      맞힌 답(7번방의 선물 ↔ 기생충, 가족애 축)을 틀렸다고 찍었다.
      영화 하나가 여러 축에 걸치는 게 정상이므로 «전부» 후보로 둔다.
    """
    my_axes = set()
    for _, q, d in G.out_edges(film, data=True):
        if d.get("rel") != "ASKS":
            continue
        for _, v, dd in G.out_edges(q, data=True):
            if dd.get("rel") != "INVOKES_VALUE":
                continue
            for a in (G.nodes[v].get("axes") or "").split(";"):
                if a and a != "미분류":
                    my_axes.add(a)
    peers = set()
    for n, d in G.nodes(data=True):
        if d.get("kind") != "Value":
            continue
        axs = [a for a in (d.get("axes") or "").split(";") if a and a != "미분류"]
        if not (my_axes & set(axs)):
            continue
        for q, _ in G.in_edges(n):
            if G.nodes[q].get("kind") != "Question":
                continue
            for f, _ in G.in_edges(q):
                if G.nodes[f].get("kind") == "Film" and f != film:
                    peers.add(f)
    return sorted(peers) or list(fallback)
def main():
    G, st, raw = load()
    films = sorted(n for n, d in G.nodes(data=True) if d.get("kind") == "Film")
    items = []

    # ── 1홉 — 「이 영화는 무엇을 묻나」 ──────────────────────────────
    for film in ("1987 (2017년 영화)", "12인의 성난 사람들 (1957년 영화)",
                 "7번방의 선물"):
        qs = sorted(o for _, o, d in G.out_edges(film, data=True)
                    if d.get("rel") == "ASKS")
        if not qs:
            continue
        items.append({
            "id": "1홉-%02d" % (len([i for i in items if i["kind"] == "1홉"]) + 1)
                  if items else "1홉-01",
            "kind": "1홉",
            "user_input": "영화 《%s》는 어떤 물음을 던지나요?" % film,
            "reference": qs,           # ★물음이 여럿이다. 하나만 적으면 채점기가 틀린다
            "reference_contexts": [[film, "ASKS", q] for q in qs],
            "chain": "%s ─ASKS→ 물음 (1홉)" % film,
            "evidence": evidence(raw, film),
        })

    # ── 2홉 — 「이 영화가 세운 가치 대립」 ──────────────────────────
    two = []
    for film in films:
        for _, q, d in G.out_edges(film, data=True):
            if d.get("rel") != "ASKS":
                continue
            vals = sorted(o for _, o, dd in G.out_edges(q, data=True)
                          if dd.get("rel") == "INVOKES_VALUE")
            if len(vals) >= 2:
                two.append((film, q, vals))
    two.sort()                                    # ★sorted — 재현 가능하게
    # ★영화가 겹치지 않게 고른다 — 같은 영화로 두 문항을 만들면 다양성이 없다
    picked, seen_f = [], set()
    for film, q, vals in two:
        if film in seen_f:
            continue
        seen_f.add(film)
        picked.append((film, q, vals))
        if len(picked) >= 4:
            break
    for i, (film, q, vals) in enumerate(picked, 1):
        items.append({
            "id": "2홉-%02d" % i, "kind": "2홉",
            "user_input": "영화 《%s》가 세운 가치 대립은 무엇인가요?" % film,
            "reference": vals,          # ★그 물음이 불러낸 가치 «전부»
            "reference_contexts": [[film, "ASKS", q]]
                                  + [[q, "INVOKES_VALUE", v] for v in vals[:2]],
            "chain": "%s ─ASKS→ 물음 ─INVOKES_VALUE→ 가치 (2홉)" % film,
            "evidence": evidence(raw, film),
        })

    # ── 4홉 — ★「같은 대립을 다룬 다른 영화」 ────────────────────────
    for i, (label, group) in enumerate(
            sorted(st["bridges"].items(), key=lambda kv: -len(kv[1]))[:4], 1):
        if len(group) < 2:
            continue
        a, rest = group[0], group[1:]
        # ★기대 경로를 «실제 그래프 형식»으로 만든다 — 형식이 다르면 대조가 안 된다
        #   (노드6 실사고 — 두 방식에 «다른 자»를 대서 graph 쪽만 0 에 가깝게 나왔다)
        ctx = []
        for _, q_, d_ in G.out_edges(a, data=True):
            if d_.get("rel") != "ASKS":
                continue
            ctx.append([a, "ASKS", q_])
            for _, v_, dd_ in G.out_edges(q_, data=True):
                if dd_.get("rel") == "INVOKES_VALUE":
                    ctx.append([q_, "INVOKES_VALUE", v_])
        items.append({
            "id": "4홉-%02d" % i, "kind": "4홉",
            "user_input": "영화 《%s》와 «같은 가치 대립»을 다루는 다른 영화를 "
                          "추천하고, 어떤 대립을 공유하는지 말해 주세요." % a,
            "reference": _axis_peers(G, a, label, rest),
            # ★축·극을 공유하는 영화 «전부»를 후보로 둔다.
            #   bridges 는 정제 단계의 부산물이라 좁다 — 첫 평가에서
            #   에이전트가 「글래디에이터」를 냈고 그건 실제로 [소속] 축을 공유했다.
            #   추천 문항은 «여럿 중 하나»면 맞다.
            "reference_contexts": ctx[:12],
            "chain": "%s ─ASKS→ 물음 ─INVOKES_VALUE→ 가치 "
                     "←INVOKES_VALUE─ 물음' ←ASKS─ 다른 영화 (4홉)" % a,
            "evidence": "공유 축 %s · 해당 영화 %d편" % (label, len(group)),
            "axis": label,
        })

    # ── ★거절 — 코퍼스에 «없는» 것 (루브릭 ②) ──────────────────────
    absent = [
        ("영화 《라라랜드》는 어떤 가치 대립을 다루나요?",
         "《라라랜드》는 코퍼스에 없다. 모른다고 답해야 한다. "
         "★처음엔 《인셉션》으로 물었는데 코퍼스를 늘리면서 인셉션이 «들어와» "
         "문항이 낡았다 — 답할 수 있게 된 것을 거절하라고 물은 셈이다. "
         "코퍼스가 자라면 거절 문항도 다시 봐야 한다."),
        ("영화 《1987》의 총 제작비는 얼마인가요?",
         "제작비는 이 그래프의 스키마에 없다(노드는 Film·Question·Value뿐). "
         "모른다고 답해야 한다."),
        ("영화 《기생충》의 감독은 누구인가요?",
         "★DIRECTED 관계를 «뽑지 않기로» 했다(config.dropped_relations). "
         "답이 그래프에 없으므로 모른다고 답해야 한다."),
    ]
    for i, (q, why) in enumerate(absent, 1):
        items.append({
            "id": "거절-%02d" % i, "kind": "거절",
            "user_input": q,
            "reference": "__REFUSE__",
            "reference_contexts": [],
            "chain": "경로 없음 — ★근거가 없으면 지어내지 않고 거절해야 한다",
            "evidence": why,
        })

    # id 다시 매기기 (1홉 번호가 꼬이지 않게)
    seq = {}
    for it in items:
        seq[it["kind"]] = seq.get(it["kind"], 0) + 1
        it["id"] = "%s-%02d" % (it["kind"], seq[it["kind"]])

    gs = {
        "name": "cinema-dilemma-goldenset",
        "version": "1.0",
        "created": "2026-09-22",
        "source_corpus": "data/docs (위키백과 영화 %d건 · 채택 기준은 "
                         "fetch_docs.py 에 코드로 박아 두었다)" % st["n_docs"],
        "purpose": "영화가 던지는 물음과 가치 대립으로 «같은 딜레마를 다룬 영화»를 "
                   "찾는다. 스키마는 그 질문에 답할 최소한으로 줄였다 "
                   "(관계 3종 · 뺀 관계와 그 대가는 config.json 에 적었다).",
        "note": "★기대 경로를 «먼저» 그래프에서 뽑고 질문을 나중에 붙였다. "
                "그래서 채점이 가능하다. reference_contexts 는 실제 그래프의 엣지다.",
        "fields": {
            "kind": "홉 수 (1홉 / 2홉 / 4홉 / ★거절)",
            "user_input": "사용자 질문",
            "reference": "기대 정답. __REFUSE__ 면 «모른다»고 답해야 한다",
            "reference_contexts": "★기대 경로 — 타야 하는 삼중항",
            "chain": "경로를 사람이 읽을 수 있게 쓴 것",
            "evidence": "원문 근거",
        },
        "stats": {
            "n": len(items),
            "by_kind": {k: v for k, v in sorted(seq.items())},
        },
        "items": items,
    }
    os.makedirs(DATA, exist_ok=True)
    io.open(os.path.join(DATA, "goldenset.json"), "w",
            encoding="utf-8", newline="").write(
                json.dumps(gs, ensure_ascii=False, indent=1))

    print("=" * 72)
    print("평가셋 %d문항 — 요건 「10건 이상」 %s"
          % (len(items), "충족" if len(items) >= 10 else "★미달"))
    print("=" * 72)
    for k, n in sorted(seq.items()):
        print("  %-5s %d문항" % (k, n))
    print()
    for it in items:
        print("  [%s] %s" % (it["id"], it["user_input"][:54]))
        print("        기대: %s" % str(it["reference"])[:60])
    print("\n저장 · data/goldenset.json")


if __name__ == "__main__":
    main()
