# -*- coding: utf-8 -*-
"""★9강 — 지식 그래프 정규화, 그리고 위키 분류로 보강.

노드가 시키는 것: *"흩어진 표기를 «정규화»하고 위키 분류 규칙으로 보강하며,
어느 사실이 어디서 왔는지 «origin»으로 남깁니다."*

정규화가 왜 필요한가 — 추출 직후 고유 엔티티가 1,876개다. 문서는 80건인데.
  「기생충」 · 「기생충 (영화)」 · 「기생충_(영화)」 가 «따로 논다».
  따로 놀면 이어 붙지 않고, 이어 붙지 않으면 멀티홉이 안 된다.

★두 가지를 한다
  ① 정규화  표기가 다른 같은 것을 하나로 («문서 제목»을 대표로 삼는다)
  ② 보강    위키 「분류:」 줄에서 장르·수상을 규칙으로 뽑아 더한다 (LLM 없이 · 공짜)

★그리고 «잰다» — 골든셋 정답 삼중항 39개 중 몇 개가 그래프에 있는가.
  없으면 그 문항은 «모델이 아무리 잘해도» 못 푼다. 색인 단계의 실패다.

    python 04_normalize.py
"""
import collections
import io
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "data", "cinephile_kb_80", "docs")
GOLD = os.path.join(HERE, "data", "cinephile_goldenset.json")
SRC = os.path.join(HERE, "graph", "triples.json")
OUT = os.path.join(HERE, "graph", "graph.json")

_PAREN = re.compile(r"\([^)]*\)")


def key(s):
    """비교용 키 — 밑줄·괄호·공백·대소문자를 지운다.

    「기생충_(영화)」 「기생충 (영화)」 「기생충」 이 모두 같은 키가 된다.
    """
    s = (s or "").replace("_", " ")
    s = _PAREN.sub(" ", s)
    return re.sub(r"\s+", "", s).lower()


def load_titles():
    """문서 제목 = 정규화의 «대표 이름». 문서가 있는 것이 기준이다."""
    titles = {}
    for fn in sorted(os.listdir(DOCS)):
        if not fn.endswith(".md"):
            continue
        raw = fn[:-3]
        disp = raw.replace("_", " ")
        titles[key(raw)] = disp
    return titles


def wiki_categories(name):
    """문서의 「분류:」 줄. LLM 없이 규칙으로 읽는다 — 공짜다."""
    p = os.path.join(DOCS, name + ".md")
    if not os.path.exists(p):
        return []
    for ln in io.open(p, encoding="utf-8").read().splitlines()[:8]:
        if ln.startswith("분류:"):
            return [c.strip() for c in ln[3:].split(",") if c.strip()]
    return []


# 분류 문자열 → (관계, 목적어) 규칙. ★열거가 아니라 «패턴»으로 잡는다.
CAT_RULES = [
    (re.compile(r"^(.+?) 수상작$"),      "WON_AWARD"),
    (re.compile(r"^(.+?) 수상자\(작\)$"), "WON_AWARD"),
    (re.compile(r"^대한민국의 (.+?) 영화$"), "HAS_GENRE"),
    (re.compile(r"^(.+?)를 배경으로 한 영화$"), "SET_IN"),
    (re.compile(r"^(.+?)을 배경으로 한 영화$"), "SET_IN"),
    (re.compile(r"^(.+?)를 소재로 한 영화$"), "HAS_THEME"),
    (re.compile(r"^(.+?)을 소재로 한 영화$"), "HAS_THEME"),
]


def main():
    src = json.load(io.open(SRC, encoding="utf-8"))
    titles = load_titles()
    tri = src["triples"]

    # ── ① 정규화 ───────────────────────────────────────────
    before_ents = {t["s"] for t in tri} | {t["o"] for t in tri}
    canon = {}
    for t in tri:
        for side in ("s", "o"):
            k = key(t[side])
            if k in titles:
                canon[t[side]] = titles[k]          # 문서가 있으면 그 제목으로
            else:
                canon.setdefault(t[side], t[side].replace("_", " ").strip())
    for t in tri:
        t["s"] = canon[t["s"]]
        t["o"] = canon[t["o"]]
    # ★정규화 «순효과»를 여기서 잡아 둔다 — 아래 분류 보강이 엔티티를 «더하므로»
    #   나중에 재면 두 효과가 섞여 정규화가 한 일이 안 보인다.
    norm_ents = {t["s"] for t in tri} | {t["o"] for t in tri}

    # ── ② 위키 분류로 보강 (LLM 없이) ─────────────────────
    added = 0
    for name in [os.path.basename(p)[:-3] for p in
                 sorted(os.listdir(DOCS)) if p.endswith(".md")]:
        subj = titles.get(key(name), name.replace("_", " "))
        for cat in wiki_categories(name):
            for pat, rel in CAT_RULES:
                m = pat.match(cat)
                if m:
                    obj = m.group(1).strip()
                    tri.append({"s": subj, "r": rel, "o": obj,
                                "origin": name + " (분류)"})
                    added += 1
                    break

    # ── 중복 제거 ────────────────────────────────────────
    seen, uniq = set(), []
    for t in tri:
        sig = (t["s"], t["r"], t["o"])
        if sig in seen:
            continue
        seen.add(sig)
        uniq.append(t)

    after_ents = {t["s"] for t in uniq} | {t["o"] for t in uniq}
    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps({"n_triples": len(uniq), "n_entities": len(after_ents),
                    "triples": uniq}, ensure_ascii=False, indent=1))

    print("=" * 70)
    print("9강 정규화 + 분류 보강")
    print("=" * 70)
    print("삼중항  %s → %s  (분류로 +%d · 중복 제거 후)"
          % (format(len(src["triples"]), ","), format(len(uniq), ","), added))
    print()
    print("엔티티 — 두 단계를 «갈라서» 본다")
    print("  ① 정규화만  %s → %s  (%s개 합쳐짐 · %.1f%% 감소)"
          % (format(len(before_ents), ","), format(len(norm_ents), ","),
             format(len(before_ents) - len(norm_ents), ","),
             (1 - len(norm_ents) / len(before_ents)) * 100))
    print("  ② 분류 보강 %s → %s  (+%s · 장르·배경 같은 «새 엔티티»가 들어온다)"
          % (format(len(norm_ents), ","), format(len(after_ents), ","),
             format(len(after_ents) - len(norm_ents), ",")))
    print("  ⇒ 합치면 %s개 — 늘어 보이지만 «줄인 일»과 «더한 일»이 섞인 값이다"
          % format(len(after_ents), ","))
    c = collections.Counter(t["r"] for t in uniq)
    print()
    for r, n in c.most_common():
        print("  %-28s %4d" % (r, n))

    # ── ★잰다: 골든셋 정답 삼중항이 그래프에 있는가 ──────
    gold = json.load(io.open(GOLD, encoding="utf-8"))
    gkeys = {(key(t["s"]), t["r"], key(t["o"])) for t in uniq}
    print()
    print("-" * 70)
    print("★색인 커버리지 — 골든셋 정답 삼중항이 그래프에 있는가")
    print("-" * 70)
    tot_hit = tot_n = 0
    miss_rows = []
    for it in gold["items"]:
        want = it.get("reference_contexts") or []
        if not want:
            print("  %-8s %-4s  —  (전역 질문 · 정답 삼중항 없음)" % (it["id"], it["kind"]))
            continue
        hit = [w for w in want if (key(w[0]), w[1], key(w[2])) in gkeys]
        tot_hit += len(hit)
        tot_n += len(want)
        mark = "✅" if len(hit) == len(want) else ("⚠" if hit else "❌")
        print("  %-8s %-4s %s %d/%d" % (it["id"], it["kind"], mark, len(hit), len(want)))
        for w in want:
            if (key(w[0]), w[1], key(w[2])) not in gkeys:
                miss_rows.append((it["id"], w))
    print("-" * 70)
    print("  ★정답 삼중항 %d개 중 %d개 있음 = %.1f%%"
          % (tot_n, tot_hit, tot_hit / tot_n * 100))
    if miss_rows:
        print()
        print("  없는 것 (이 문항들은 «색인» 단계에서 이미 못 푼다):")
        for rid, w in miss_rows[:12]:
            print("    %-8s (%s, %s, %s)" % (rid, w[0], w[1], w[2]))
        if len(miss_rows) > 12:
            print("    … 외 %d개" % (len(miss_rows) - 12))
    print("=" * 70)
    print("저장: graph/graph.json")


if __name__ == "__main__":
    main()
