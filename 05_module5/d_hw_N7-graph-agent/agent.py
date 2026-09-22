# -*- coding: utf-8 -*-
"""멀티홉 에이전트 — 시작개체 → n홉 확장 → 근거만으로 답변 (요건 ④)

  python agent.py "영화 «1987»과 같은 딜레마를 다룬 영화는?"
  python agent.py --eval                # 골든셋 전체를 돌린다
  python agent.py --eval --repeat 3     # ★3회 돌려 «흔들림»을 본다

★LangGraph 로 짠다 — REPORT 가 State 흐름 다이어그램을 요구한다(요건 §REPORT ④).

State 흐름
  seed ─▶ expand ─▶ gather ─▶ decide ─┬─▶ answer
                       ▲              └─▶ refuse
                       └── widen (근거 0 이면 «한 번» 넓힌다)

★근거가 없으면 지어내지 않고 «거절»한다 (루브릭 ②).
★탄 경로를 전부 기록한다 — 답과 «함께» 낸다 (요건 ④).
"""
import argparse
import io
import json
import os
import re
import time
from typing import Any, Dict, List

import networkx as nx

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
CFG = json.load(io.open(os.path.join(HERE, "config.json"), encoding="utf-8"))

REFUSE = "근거를 찾지 못했습니다. 이 그래프에는 답할 수 있는 경로가 없습니다."


# ── 그래프 도우미 ────────────────────────────────────────────────────
def load_graph():
    return nx.read_graphml(os.path.join(OUT, "graph.graphml"))


def kind(G, n):
    return G.nodes[n].get("kind", "?")


def films(G):
    return sorted(n for n in G if kind(G, n) == "Film")


_AXIS_CACHE = {}


def _same_axis_values(G, v):
    """★그 Value 와 «같은 축·극»을 가진 Value 들 (자기 포함).

    normalize_graph.py 가 노드에 axes="소속/개인;인정/자기 자신" 을 박아 둔다.
    축·극이 하나라도 겹치면 «같은 자리»로 본다 — 이름이 달라도 같은 대립이다.
    ⚠「미분류」는 겹치는 것으로 보지 않는다. 미분류끼리 이으면 아무거나 닿는다.
    """
    if not _AXIS_CACHE:
        for n, d in G.nodes(data=True):
            if d.get("kind") != "Value":
                continue
            for a in (d.get("axes") or "").split(";"):
                if a and a != "미분류":
                    _AXIS_CACHE.setdefault(a, set()).add(n)
    out = {v}
    for a in (G.nodes[v].get("axes") or "").split(";"):
        if a and a != "미분류":
            out |= _AXIS_CACHE.get(a, set())
    return sorted(out)


def hub_reach(G):
    """★Value 마다 «닿는 영화 수»를 센다 — 허브 판정의 근거."""
    out = {}
    fs = films(G)
    for n in G:
        if kind(G, n) != "Value":
            continue
        s = set()
        for q, _ in G.in_edges(n):
            for f, _ in G.in_edges(q):
                if kind(G, f) == "Film":
                    s.add(f)
        out[n] = len(s)
    return out, len(fs)


# ── LangGraph State ─────────────────────────────────────────────────
class S(dict):
    """State — 노드 사이를 흐르는 것. dict 로 두어 직렬화가 쉽다."""


def node_seed(st: S) -> S:
    """①시작 개체 찾기 — 질문 안에서 영화·가치 이름을 «찾는다»."""
    G, q = st["_G"], st["question"]
    hit_f = [f for f in films(G) if _mentions(q, f)]
    hit_v = sorted((n for n in G if kind(G, n) == "Value" and _mentions(q, n)),
                   key=len, reverse=True)
    st["seeds"] = {"films": hit_f[:3], "values": hit_v[:3]}
    st["trace"] = st.get("trace", []) + [
        {"node": "seed", "found_films": hit_f[:3], "found_values": hit_v[:3]}]
    return st


def _mentions(q, name):
    """제목 표기가 흔들려도 잡는다 — 「1987 (2017년 영화)」 ↔ 「1987」."""
    base = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()
    if len(base) < 2:
        return False
    return base in q


def node_expand(st: S) -> S:
    """②n홉 확장 — 실제로 «탄 경로»를 전부 남긴다."""
    G = st["_G"]
    max_hop = st.get("max_hop") or CFG["hops"]["max"]
    cap = CFG["hops"]["max_nodes_per_hop"]
    paths, seen_v = [], {}

    for f in st["seeds"]["films"]:
        for _, q, d in G.out_edges(f, data=True):
            if d.get("rel") != "ASKS":
                continue
            if max_hop < 2:
                paths.append([(f, "ASKS", q)])
                continue
            for _, v, dd in G.out_edges(q, data=True):
                if dd.get("rel") != "INVOKES_VALUE":
                    continue
                leg = [(f, "ASKS", q), (q, "INVOKES_VALUE", v)]
                if max_hop < 3:
                    paths.append(leg)
                    continue
                seen_v.setdefault(v, []).append(leg)

    # ★3~4홉 — 같은 Value 에 닿는 «다른» 영화로 되돌아 간다
    if max_hop >= 3:
        reach, n_films = st["_reach"], st["_n_films"]
        pct = CFG["hub"]["degree_pct"] or 100
        for v, legs in sorted(seen_v.items()):                 # ★sorted
            is_hub = 100.0 * reach.get(v, 0) / max(1, n_films) > pct
            # ★Value «노드 이름»이 아니라 «축·극»으로 잇는다.
            #   루브릭 ② 의 「같은 개체를 합치는 기준」이 축·극이라고 했으니
            #   확장도 같은 잣대를 써야 한다. 이름으로 이으면 파편화 때문에
            #   「가족애」와 「가족 간의 사랑」이 다른 것이 된다.
            #   (첫 평가에서 4홉 0% — 골든셋은 축·극, 에이전트는 노드 이름을 썼다)
            sibs = _same_axis_values(G, v)
            back = []
            for v2 in sibs:
                for q2, _ in G.in_edges(v2):
                    if kind(G, q2) != "Question":
                        continue
                    for f2, _ in G.in_edges(q2):
                        if kind(G, f2) != "Film":
                            continue
                        if f2 in st["seeds"]["films"]:
                            continue
                        back.append((q2, f2))
            for leg in legs:
                for q2, f2 in sorted(back)[:cap]:              # ★sorted
                    paths.append(leg + [(v, "INVOKES_VALUE←", q2),
                                        (q2, "ASKS←", f2)])
                    if is_hub:
                        st.setdefault("hub_used", []).append(v)
            if not back:
                paths += legs

    st["paths"] = paths[:200]
    st["trace"] = st["trace"] + [
        {"node": "expand", "max_hop": max_hop, "n_paths": len(paths),
         "hub_used": sorted(set(st.get("hub_used", [])))}]
    return st


def node_gather(st: S) -> S:
    """③근거 수집 — 경로에 쓰인 삼중항과 출처 문서를 모은다."""
    G = st["_G"]
    tri, srcs = [], set()
    for p in st["paths"]:
        for s, r, o in p:
            tri.append([s, r.rstrip("←"), o])
            d = G.get_edge_data(s, o) or G.get_edge_data(o, s) or {}
            if d.get("origin"):
                srcs.add(d["origin"])
    uniq = []
    for t in tri:
        if t not in uniq:
            uniq.append(t)
    st["evidence"] = uniq[:60]
    st["sources"] = sorted(srcs)
    st["trace"] = st["trace"] + [
        {"node": "gather", "n_evidence": len(uniq), "n_sources": len(srcs)}]
    return st


def node_decide(st: S) -> S:
    """④판정 — 근거가 있나? ★없으면 넓히고, 그래도 없으면 거절."""
    need = CFG["refuse"]["min_evidence"]
    ok = len(st["evidence"]) >= need
    if not ok and not st.get("widened"):
        # ★넓힌 뒤 «반드시» 다시 판정한다 — 여기서 route 를 안 넣으면
        #   conditional_edges 가 KeyError 로 죽는다 (첫 --eval 에서 그랬다)
        st["widened"] = True
        st["max_hop"] = (st.get("max_hop") or CFG["hops"]["max"]) + 2
        st["trace"] = st["trace"] + [
            {"node": "decide", "verdict": "widen",
             "why": "근거 %d < %d — 한 번 넓힌다" % (len(st["evidence"]), need)}]
        st = node_gather(node_expand(node_seed(st)))
        ok = len(st["evidence"]) >= need
    st["route"] = "answer" if ok else "refuse"
    st["trace"] = st["trace"] + [
        {"node": "decide", "verdict": st["route"],
         "n_evidence": len(st["evidence"])}]
    return st


ANSWER_SYS = """너는 지식 그래프의 «근거만»으로 답하는 도우미다.

★규칙
- 아래 «근거 삼중항»에 없는 사실을 절대 쓰지 마라. 일반 지식을 섞지 마라.
- 근거로 답할 수 없으면 「근거를 찾지 못했습니다」라고만 답하라.
- 영화를 추천할 때는 «어떤 가치 대립을 공유하는지»를 함께 말하라.
- ★「가치 대립은?」을 물으면 근거의 «가치 이름»을 그대로 말하라.
  물음 문장을 되풀이하지 마라. (가치는 INVOKES_VALUE 의 목적어다)
- ★「어떤 물음을 던지나?」를 물으면 ASKS 의 목적어를 그대로 말하라.
- 3문장 안으로 답하라.
"""


def node_answer(st: S) -> S:
    from dotenv import load_dotenv
    from openai import OpenAI
    load_dotenv(os.path.join(HERE, ".env"))
    cl = OpenAI()
    ev = "\n".join("(%s, %s, %s)" % tuple(t) for t in st["evidence"][:40])
    r = cl.chat.completions.create(
        model=CFG["model"]["answer"], temperature=0,
        messages=[{"role": "system", "content": ANSWER_SYS},
                  {"role": "user",
                   "content": "질문: %s\n\n근거 삼중항:\n%s"
                              % (st["question"], ev)}])
    st["answer"] = (r.choices[0].message.content or "").strip()
    st["usage"] = {"in": r.usage.prompt_tokens, "out": r.usage.completion_tokens}
    st["trace"] = st["trace"] + [{"node": "answer", "model": CFG["model"]["answer"]}]
    return st


def node_refuse(st: S) -> S:
    st["answer"] = REFUSE
    st["usage"] = {"in": 0, "out": 0}
    st["trace"] = st["trace"] + [{"node": "refuse"}]
    return st


def build():
    """★LangGraph 조립 — REPORT 다이어그램이 이 구조를 그린다."""
    from langgraph.graph import END, StateGraph
    g = StateGraph(dict)
    g.add_node("seed", node_seed)
    g.add_node("expand", node_expand)
    g.add_node("gather", node_gather)
    g.add_node("decide", node_decide)
    g.add_node("answer", node_answer)
    g.add_node("refuse", node_refuse)
    g.set_entry_point("seed")
    g.add_edge("seed", "expand")
    g.add_edge("expand", "gather")
    g.add_edge("gather", "decide")
    g.add_conditional_edges("decide", lambda s: s["route"],
                            {"answer": "answer", "refuse": "refuse"})
    g.add_edge("answer", END)
    g.add_edge("refuse", END)
    return g.compile()


def ask(app, G, reach, n_films, question, max_hop=None):
    st = {"question": question, "_G": G, "_reach": reach, "_n_films": n_films}
    if max_hop:
        st["max_hop"] = max_hop
    t0 = time.time()
    out = app.invoke(st)
    out["sec"] = round(time.time() - t0, 2)
    for k in ("_G", "_reach", "_n_films"):
        out.pop(k, None)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="?")
    ap.add_argument("--eval", action="store_true")
    ap.add_argument("--repeat", type=int, default=1,
                    help="★N회 돌려 «문항별 통과 횟수»와 흔들림을 본다")
    ap.add_argument("--hop", type=int)
    args = ap.parse_args()

    G = load_graph()
    reach, n_films = hub_reach(G)
    app = build()

    if args.eval:
        gs = json.load(io.open(os.path.join(HERE, "data", "goldenset.json"),
                               encoding="utf-8"))
        runs = []
        for r in range(args.repeat):
            for it in gs["items"]:
                res = ask(app, G, reach, n_films, it["user_input"], args.hop)
                runs.append({"run": r + 1, "id": it["id"], "kind": it["kind"],
                             "question": it["user_input"],
                             "reference": it["reference"],
                             "reference_contexts": it["reference_contexts"],
                             "answer": res["answer"],
                             "evidence": res["evidence"],
                             "paths": [[list(t) for t in p]
                                       for p in res["paths"][:8]],
                             "sources": res["sources"],
                             "trace": res["trace"], "sec": res["sec"],
                             "usage": res.get("usage", {})})
                print("  [%s] %s  근거%d · %.1fs"
                      % (it["id"], "거절" if res["answer"] == REFUSE else "답변",
                         len(res["evidence"]), res["sec"]), flush=True)
        io.open(os.path.join(OUT, "runs.jsonl"), "w",
                encoding="utf-8", newline="").write(
                    "\n".join(json.dumps(x, ensure_ascii=False) for x in runs))
        print("\n%d회 × %d문항 = %d건 · 저장 output/runs.jsonl"
              % (args.repeat, len(gs["items"]), len(runs)))
        return

    if not args.question:
        ap.error("질문을 주거나 --eval 을 쓰세요")
    res = ask(app, G, reach, n_films, args.question, args.hop)
    print("=" * 72)
    print("Q %s" % args.question)
    print("=" * 72)
    print("\nA %s\n" % res["answer"])
    print("★탄 경로 (%d개 중 앞 3개)" % len(res["paths"]))
    for p in res["paths"][:3]:
        print("   " + "  →  ".join("%s ─%s─ %s" % t for t in p))
    print("\n★근거 삼중항 %d개 (앞 6개)" % len(res["evidence"]))
    for t in res["evidence"][:6]:
        print("   (%s, %s, %s)" % tuple(t))
    print("\n출처 문서 %d건: %s" % (len(res["sources"]),
                                " · ".join(res["sources"][:5])))
    print("\nState 흐름: %s  (%.2fs)"
          % (" → ".join(t["node"] for t in res["trace"]), res["sec"]))


if __name__ == "__main__":
    main()
