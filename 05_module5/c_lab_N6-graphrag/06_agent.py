# -*- coding: utf-8 -*-
"""★12~13강 — LangGraph 로 GraphRAG 에이전트. 질문 유형에 따라 «세 갈래».

노드가 시키는 것: *"라우터와 탐색을 조립해 LangGraph 로 질문 유형에 따라
세 갈래로 경로를 가릅니다."*

세 갈래 (노드 설명의 «지역·경로·전역»)
  local   엔티티 하나의 «이웃»만 본다            — 「기생충의 감독은?」
  path    두 엔티티를 «잇는 길»을 걷는다 (2홉)   — 「기생충 배우의 다른 작품」
  global  «커뮤니티 요약»을 본다                 — 「이 자료에 어떤 집단이 있나」

★라우팅 기준은 «모델의 확신»이 아니라 질문 유형이다.
  그리고 근거가 비면 답하지 않는다 — 노드5 에서 세운 규칙을 그대로 가져왔다.

    python 06_agent.py --q "영화 《기생충》의 감독은 누구인가?"
    python 06_agent.py --demo
"""
import argparse
import collections
import io
import json
import os
import re
import sys
from typing import TypedDict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
GRAPH = os.path.join(HERE, "graph", "graph.json")
COMM = os.path.join(HERE, "graph", "communities.json")
PAIRS = os.path.join(HERE, "graph", "director_actor_pairs.json")

_PAREN = re.compile(r"\([^)]*\)")


def key(s):
    s = (s or "").replace("_", " ")
    s = _PAREN.sub(" ", s)
    return re.sub(r"\s+", "", s).lower()


# ──────────────────────────── 지식 ────────────────────────────
class KB:
    def __init__(self):
        g = json.load(io.open(GRAPH, encoding="utf-8"))
        self.triples = g["triples"]
        self.by_s = collections.defaultdict(list)
        self.by_o = collections.defaultdict(list)
        self.names = {}
        for t in self.triples:
            self.by_s[key(t["s"])].append(t)
            self.by_o[key(t["o"])].append(t)
            self.names.setdefault(key(t["s"]), t["s"])
            self.names.setdefault(key(t["o"]), t["o"])
        self.comm = json.load(io.open(COMM, encoding="utf-8"))
        self.pairs = json.load(io.open(PAIRS, encoding="utf-8"))

    def find_entities(self, q):
        """질문에서 그래프에 «있는» 엔티티를 찾는다. 긴 이름부터 본다."""
        qk = key(q)
        hits = [(n, k) for k, n in self.names.items() if len(k) >= 2 and k in qk]
        hits.sort(key=lambda x: -len(x[1]))
        out, used = [], ""
        for name, k in hits:
            if k in used:            # 「기생충」이 「기생충 영화」에 먹히는 것을 막는다
                continue
            out.append(name)
            used += k
            if len(out) >= 4:
                break
        return out

    def neighbors(self, name):
        k = key(name)
        return self.by_s.get(k, []) + self.by_o.get(k, [])

    def two_hop(self, name, limit=80):
        """★멀티홉 — 이웃의 이웃. 「기생충 ←ACTED_IN— 배우 —ACTED_IN→ 다른 영화」."""
        k = key(name)
        first = self.neighbors(name)
        mids = {key(t["s"]) for t in first} | {key(t["o"]) for t in first}
        mids.discard(k)
        out = list(first)
        # ★sorted 가 «반드시» 필요하다 — list(set) 은 실행마다 순서가 달라진다.
        #   실제로 같은 질의를 3번 돌려 해시가 3번 다 달랐다.
        #   그래서 추천-07 이 회차마다 67% → 0% 로 «뒤집혔다».
        #   답변 규칙을 고쳐서 깨진 줄 알았는데 원인은 여기였다.
        #   ⇒ 재현되지 않는 파이프라인에서는 «무엇을 고쳤는지»도 말할 수 없다.
        for m in sorted(mids)[:30]:
            for t in self.by_s.get(m, []) + self.by_o.get(m, []):
                if key(t["s"]) != k and key(t["o"]) != k:
                    out.append(t)
        return out[:limit]


# ──────────────────────────── 상태 ────────────────────────────
class S(TypedDict, total=False):
    q: str
    route: str
    entities: list
    facts: list
    context: str
    answer: str


ROUTE_SYS = """질문을 세 갈래 중 하나로 고른다. 다른 말은 하지 않는다.

local   한 대상의 «속성»을 묻는다 — 감독이 누구, 배급사가 어디, 무슨 상을 받았나
path    A 를 거쳐 B 로 «건너가야» 답이 나온다 — 「X에 나온 배우의 다른 작품」,
        「X와 같은 상을 받은 다른 영화」처럼 한 번 더 타고 가는 추천
global  자료 «전체»를 봐야 한다 — 「어떤 집단들이 있나」, 「반복되는 조합은」

local / path / global 중 하나만 출력한다."""

ANS_SYS = """너는 한국 영화 안내원이다. 아래 [근거]에 «있는 것»만으로 답한다.

- 근거에 없으면 «없다»고 말한다. 아는 것을 보태지 않는다.
- ★추천을 물으면 «여러 사람·여러 작품»을 든다. 한 사람으로 줄이지 않는다.
  「A에 출연한 배우의 다른 작품」이면 근거에 있는 배우를 «가능한 한 많이» 훑고,
  각 배우마다 다른 작품을 함께 적는다. 목록으로 적어도 좋다.
- ★전체를 묻는 질문이면 근거에 나온 «집단·조합을 빠짐없이» 훑는다.
- 근거가 많으면 길어져도 된다. 빠뜨리는 것보다 낫다.

[근거]
{ctx}"""


def build(model="gpt-4.1-mini"):
    from langgraph.graph import StateGraph, START, END
    from dotenv import load_dotenv
    load_dotenv(os.path.join(HERE, ".env"))
    from openai import OpenAI
    client = OpenAI()
    kb = KB()

    def route(s: S) -> S:
        r = client.chat.completions.create(
            model=model, temperature=0,
            messages=[{"role": "system", "content": ROUTE_SYS},
                      {"role": "user", "content": s["q"]}])
        v = r.choices[0].message.content.strip().lower()
        v = v if v in ("local", "path", "global") else "local"
        return {"route": v, "entities": kb.find_entities(s["q"])}

    def local(s: S) -> S:
        facts = []
        for e in s["entities"]:
            facts += kb.neighbors(e)
        return {"facts": facts[:60]}

    def path(s: S) -> S:
        facts = []
        for e in s["entities"]:
            facts += kb.two_hop(e)
        return {"facts": facts[:120]}

    def glob(s: S) -> S:
        """전역 — 커뮤니티 요약과 «미리 집계해 둔» 감독-배우 쌍을 준다."""
        lines = []
        for c in kb.comm["communities"][:12]:
            head = " · ".join(c["members"][:6])
            lines.append("[집단 #%d · %d명] %s\n%s" % (c["id"], c["size"], head,
                                                    c.get("summary", "")))
        lines.append("[반복 협업 조합]")
        for p in kb.pairs[:12]:
            lines.append("  %s – %s : %d편 (%s)"
                         % (p["director"], p["actor"], p["n"], ", ".join(p["films"][:4])))
        return {"facts": [], "context": "\n\n".join(lines)}

    def compose(s: S) -> S:
        ctx = s.get("context")
        if ctx is None:
            seen, lines = set(), []
            for t in s.get("facts") or []:
                sig = (t["s"], t["r"], t["o"])
                if sig in seen:
                    continue
                seen.add(sig)
                lines.append("(%s, %s, %s)" % sig)
            ctx = "\n".join(lines)
        if not ctx.strip():
            return {"context": "", "answer": "자료에서 근거를 찾지 못했습니다."}
        r = client.chat.completions.create(
            model=model, temperature=0,
            messages=[{"role": "system", "content": ANS_SYS.format(ctx=ctx)},
                      {"role": "user", "content": s["q"]}])
        return {"context": ctx, "answer": r.choices[0].message.content.strip()}

    g = StateGraph(S)
    for n, f in [("route", route), ("local", local), ("path", path),
                 ("global", glob), ("compose", compose)]:
        g.add_node(n, f)
    g.add_edge(START, "route")
    g.add_conditional_edges("route", lambda s: s["route"],
                            {"local": "local", "path": "path", "global": "global"})
    for n in ("local", "path", "global"):
        g.add_edge(n, "compose")
    g.add_edge("compose", END)
    return g.compile()


DEMO = [
    "영화 《기생충》의 감독은 누구인가?",
    "영화 《기생충》에 출연한 배우의 다른 작품을 추천해줘.",
    "한국 영화계에서 반복적으로 함께 작업하는 감독과 배우 조합에는 어떤 것이 있는가?",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--q")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--model", default="gpt-4.1-mini")
    args = ap.parse_args()

    app = build(args.model)
    qs = DEMO if args.demo or not args.q else [args.q]
    for q in qs:
        s = app.invoke({"q": q})
        print("=" * 70)
        print("Q. %s" % q)
        print("   경로: %s · 엔티티: %s · 근거 %d줄"
              % (s["route"], " / ".join(s.get("entities") or []) or "-",
                 len((s.get("context") or "").splitlines())))
        print("-" * 70)
        print(s["answer"])
        print()


if __name__ == "__main__":
    main()
