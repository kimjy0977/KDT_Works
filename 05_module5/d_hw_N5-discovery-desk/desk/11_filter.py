# -*- coding: utf-8 -*-
"""★수집한 기사에서 «주제 밖»을 거른다 — 그리고 «버린 것»을 보여준다.

왜 필요한가 — 실측으로 드러났다
  `Phys.org 고고학` 피드(https://phys.org/rss-feed/science-news/archaeology/)에
  이런 것이 섞여 나온다:
    「AI can be more comforting than a person」
    「How online platforms are misaligned with late-career workers」
  URL 은 고고학이 맞다. **피드 쪽이 일반 기사를 섞어 보낸다.**
  NASA 도 마찬가지 — 「Celebrates Restoration of Guam Station」은 홍보다.

  ★노드3 은 «선별» 단계(LLM 예선·본선)가 있었다. 나는 그걸 건너뛰었고,
    건너뛰고 나서야 **왜 있었는지** 알았다.

★어제 배운 것을 여기에 적용한다
  「가드레일은 «막는 것»보다 «안 막는 것»이 어렵다」
  필터도 같다. 좋은 기사를 버리면 지식원이 빈약해진다.
  ⇒ **버린 것을 «전부» 찍는다.** 그래야 과하게 버리는지 눈으로 본다.
  ⇒ 어제 역방향 가드레일에서 «재현율을 안 잰» 실수를 여기서 되풀이하지 않는다.

  python 11_filter.py            # 미리보기 — 무엇이 버려지는지만 본다
  python 11_filter.py --write    # store/knowledge.json 로 저장
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent

# ★라우트별 «주제어» — 제목이나 요약에 하나라도 있으면 통과
#   영어 기사이므로 영어로 쓴다. 한국어 기사가 섞이면 한국어도 더한다.
TOPIC = {
    "SPACE": ("planet", "star", "galaxy", "telescope", "orbit", "spacecraft", "asteroid",
              "comet", "moon", "mars", "jupiter", "saturn", "solar", "cosmic", "nebula",
              "astronom~", "meteor~", "lunar", "exoplanet", "black hole", "supernova",
              "space", "rover", "satellite", "universe", "milky way"),
    "ARCHAEO": ("archaeolog~", "excavat~", "ancient", "artifact", "artefact", "tomb", "ruin",
                "burial", "inscription", "pottery", "neolithic", "bronze age", "iron age",
                "roman", "egypt", "maya", "mesopotam~", "settlement", "shipwreck",
                "prehistor~", "cave art", "temple", "civilization", "civilisation",
                # ★1차 실측에서 «잘못 버린» 기사가 근거다:
                #   「Australian cave hid 25,000 years of ritual secrets」
                #   「Large estimated size of the Australian Indigenous population before…」
                #   「Long-term ecological stability in the Pleistocene central Levant」
                "cave", "ritual", "rock art", "indigenous", "heritage", "levant",
                "pleistocene", "holocene", "stone tool", "midden", "dwelling"),
    "PALEO": ("fossil", "dinosaur", "extinct~", "evolution", "specimen", "cretaceous",
              "jurassic", "triassic", "cambrian", "paleo~", "palaeo~", "hominin~",
              "neanderthal", "ancient dna", "mammoth", "trilobite", "amber",
              "skeleton", "species", "lineage", "ancestor"),
}

# ★홍보·행정 기사 — 노드3 audience.yaml 이 「거의 틀리지 않는다」고 한 것
#   「예산 확보·기관 개소·전시 개막」
PROMO = ("celebrat", "ribbon-cutting", "anniversary", "award", "appoint", "hire",
         "internship", "career", "workforce", "budget request", "groundbreaking ceremony",
         "exhibition opens", "names new", "announces leadership")


def _rx(kw):
    """★단어 «경계»를 본다 — 부분 문자열로 세면 엉뚱한 데 매치된다.

    1차 실측에서 나온 것:
      「Half-billion-year-old fossils rewrite the origin story of **star**fish」
      ⇒ `star` 가 매치돼 PALEO 기사가 SPACE 로 재배정됐다.

    ★어제 search_product 에서 본 것과 «같은 함정»이다 —
      「한 글자만 겹쳐도 완전 일치와 같은 1점」.
      그때는 점수를 가중해 고쳤고, 여기서는 «경계»로 고친다.

    끝에 ~ 가 붙은 것은 «접두사»로 본다 (archaeolog~ → archaeology, archaeological).
    """
    if kw.endswith("~"):
        return re.compile(r"\b" + re.escape(kw[:-1]), re.I)
    return re.compile(r"\b" + re.escape(kw) + r"\b", re.I)


RX = {rt: [_rx(k) for k in kws] for rt, kws in TOPIC.items()}


def score_routes(a):
    """★라우트를 «내용»으로 다시 판정한다 — 소스 그룹은 «힌트»일 뿐이다.

    1차 실측에서 드러난 것:
      · Sci.News(group=고생물) 가 CERN·VISTA·Venus 기사를 낸다 → PALEO 로 잘못 표시
      · Phys.org 고고학 피드에 공룡 기사가 온다               → ARCHAEO 로 잘못 표시
    라우트가 틀리면 «그 라우트의 주제어»를 대보므로 **두 겹으로 틀린다.**
    ⇒ 세 라우트의 주제어를 «전부» 대보고 가장 많이 맞는 곳으로 보낸다.
    """
    text = a["title"] + " " + a["summary"]
    return {rt: sum(1 for r in rxs if r.search(text)) for rt, rxs in RX.items()}


def topical(a):
    """어느 라우트든 주제어가 «하나라도» 맞는가."""
    return max(score_routes(a).values()) > 0


PROMO_RX = [_rx(k) for k in PROMO]


def promo(a):
    text = a["title"] + " " + a["summary"]
    return any(r.search(text) for r in PROMO_RX)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--src", default="store/articles.json")
    args = ap.parse_args()

    d = json.loads((HERE / args.src).read_text(encoding="utf-8"))
    arts = d["articles"]

    keep, drop, moved = [], [], []
    for a in arts:
        sc = score_routes(a)
        top = max(sc.values())
        if top == 0:
            drop.append((a, "주제 밖"))
            continue
        if promo(a):
            drop.append((a, "홍보·행정"))
            continue
        # ★동점이면 «재배정하지 않는다» — 소스 그룹을 믿는다.
        #   max() 는 딕셔너리 순서상 첫 번째를 고른다. 그래서 동점일 때
        #   ARCHAEO 가 PALEO 를 «이겨» 「털코뿔소」·「1억2500만년 화석」이 잘못 갔다.
        #   ⇒ 어제 search_v2 에서 «동점은 애매로 처리»한 것과 같은 자리다.
        winners = [rt for rt, v in sc.items() if v == top]
        best = winners[0] if len(winners) == 1 else a["route"]
        # ★라우트 재배정 — 소스 그룹과 다르면 «내용»을 따른다
        if best != a["route"]:
            moved.append((a["route"], best, a["title"][:50]))
            a["route_src"] = a["route"]
            a["route"] = best
        # ★요약이 비어도 «버리지 않는다» — 제목에 주제어가 있으면 살린다.
        #   다만 그라운딩 재료가 얇으므로 표시해 둔다.
        a["thin"] = len(a["summary"]) < 40
        keep.append(a)

    print("=== 지식원 필터 — 원본 %d건 ===" % len(arts))
    print("   남김 %d건 · 버림 %d건 (%.0f%%)"
          % (len(keep), len(drop), 100 * len(drop) / max(1, len(arts))))
    print()
    print("[라우트별]")
    kc, dc = Counter(a["route"] for a in keep), Counter(a["route"] for a, _ in drop)
    for rt in ("SPACE", "ARCHAEO", "PALEO"):
        print("   %-8s 남김 %2d · 버림 %2d" % (rt, kc[rt], dc[rt]))
    print()
    if moved:
        print("[★라우트 재배정 %d건 — 소스 그룹이 «틀렸던» 것]" % len(moved))
        for src, dst, t in moved[:12]:
            print("   %-8s → %-8s %s" % (src, dst, t))
        if len(moved) > 12:
            print("   … 외 %d건" % (len(moved) - 12))
        print()
    thin = sum(1 for a in keep if a.get("thin"))
    print("   ※ 요약이 얇은 것 %d건 — 버리지 않고 표시만 한다(제목에 주제어가 있다)" % thin)
    print()
    print("[버린 이유]")
    for why, n in Counter(w for _, w in drop).most_common():
        print("   %-12s %d건" % (why, n))

    # ★★버린 것을 «전부» 찍는다 — 과하게 버리는지 «눈으로» 본다
    print()
    print("[★버린 기사 — 이 목록이 아까우면 필터가 과한 것이다]")
    for a, why in drop:
        print("   %-10s %-8s %s" % (why, a["route"], a["title"][:64]))

    if not args.write:
        print()
        print("   (미리보기입니다. 저장하려면 --write)")
        return

    out = HERE / "store/knowledge.json"
    out.write_text(json.dumps({
        "collected_at": d["collected_at"],
        "window_hours": d["window_hours"],
        "kept": len(keep), "dropped": len(drop),
        "articles": keep,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print()
    print("   ✅ %d건 → %s" % (len(keep), out))
    raw = out.read_bytes()
    print("   [자기검사] 제어문자 %d개"
          % len([1 for b in raw if b < 9 or (13 < b < 32)]))


if __name__ == "__main__":
    main()
