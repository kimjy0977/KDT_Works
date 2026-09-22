# -*- coding: utf-8 -*-
"""코퍼스 수집 — 위키백과에서 «영화 작품» 문서만 모은다 (요건 ①)

  python fetch_docs.py --stats          # 지금 몇 건인지 센다
  python fetch_docs.py --target 60      # 60건이 될 때까지 넓힌다
  python fetch_docs.py --dry            # 무엇을 받을지만 보여준다

★왜 필요한가 — cinephile_kb_80 은 노드6 «사실 관계»용이라
  기업 10 · 인물 28 · 시상식 7 이 섞여 있다. 실제 영화는 29건뿐이다.
  요건은 「개체가 문서 사이에 겹치는 코퍼스 50건 이상」을 요구한다.

★채택·탈락 기준을 코드로 «박아» 둔다 — 요건 ①이 기준을 남기라고 했다.
"""
import argparse
import io
import json
import os
import re
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "data", "docs")
API = "https://ko.wikipedia.org/w/api.php"
UA = "KDT-node7-graph-agent/1.0 (study project)"

# ── 채택·탈락 기준 (요건 ①) ─────────────────────────────────────────
#   ★열거가 아니라 «패턴»으로 쓴다. 분류 이름은 계속 늘어난다(§F-8-D).
#   ★채택 판정을 «세 번» 고쳤다. 그 과정을 남긴다 — 요건 ①이 기준을 남기라고 했다.
#     1차  `'영화' in c`            → 75건. JK필름·각본가·로튼 토마토까지 잡혔다
#     2차  `^\d{4}년 영화$`         → 31건. 「2019년 컴퓨터 애니메이션 영화」가 빠졌다
#     3차  `영화$` + 제외 목록       → 51건. ★「베를린의 영화」가 새 버렸다
#     ⇒ ★4차 — 제외를 넓히는 경주를 그만두고 «허용»을 패턴으로 쓴다(§F-8-D).
#       위키 작품 분류는 «연도»나 «작품»을 반드시 단다. 장소·주제 분류는 안 단다.
#         「2019년 영화」 「2019년 컴퓨터 애니메이션 영화」 「대한민국의 영화 작품」  ○
#         「베를린의 영화」 「구마를 소재로 한 영화」                                ✗
WORK_CAT = re.compile(r"(^\d{4}년(?:\s\S+)* 영화$|의 영화 작품$)")
NOT_WORK = re.compile(r"(영화제|영화상|수상자)")   # 허용이 좁아져 제외는 최소로 남긴다

#   ★MIN_CHARS 는 «실측으로» 정했다 (2026-09-22 · 영화 33건)
#       0~500자    2건 → 삼중항 ★전부 0개
#     500~1000     1건 → 평균 6.0
#    1000~2000    12건 → 평균 6.3
#    2000~5000    10건 → 평균 6.2
#    5000~         8건 → 평균 6.0
#     ⇒ 500자를 넘으면 «하나도» 실패하지 않았다. 눈대중이 아니라 경계를 쟀다.
MIN_CHARS = 500
DROP_TITLE = re.compile(r"(목록$|영화제$|영화상$|시상식$|위키|분류:)")


def api(params):
    q = dict(params)
    q.update({"format": "json", "formatversion": "2", "utf8": "1"})
    url = API + "?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def page(title):
    """문서 본문과 분류를 한 번에 받는다."""
    d = api({"action": "query", "prop": "extracts|categories",
             "titles": title, "explaintext": "1", "cllimit": "60"})
    ps = d.get("query", {}).get("pages", [])
    if not ps or ps[0].get("missing"):
        return None
    p = ps[0]
    cats = [c["title"].replace("분류:", "")
            for c in p.get("categories", [])]
    return {"title": p["title"], "text": p.get("extract", ""), "cats": cats}


def is_film_work(pg):
    """★채택 판정 — 「…영화」 분류가 있고, «사람·행사»를 가리키지 않는다."""
    return any(WORK_CAT.search(c) and not NOT_WORK.search(c)
               for c in pg["cats"])


def links_in(title, limit=200):
    """그 문서가 «가리키는» 문서들 — 2홉 확장용."""
    d = api({"action": "query", "prop": "links", "titles": title,
             "plnamespace": "0", "pllimit": str(limit)})
    ps = d.get("query", {}).get("pages", [])
    if not ps:
        return []
    return [l["title"] for l in ps[0].get("links", [])]


def fname(title):
    return re.sub(r"[\\/:*?\"<>|]", "_", title).replace(" ", "_") + ".md"


def have():
    return set(os.path.splitext(f)[0] for f in os.listdir(DOCS)
               if f.endswith(".md"))


def write_doc(pg):
    body = "# %s\n\n분류: %s\n\n%s\n" % (
        pg["title"], ", ".join(pg["cats"]), pg["text"])
    io.open(os.path.join(DOCS, fname(pg["title"])), "w",
            encoding="utf-8", newline="").write(body)


def stats():
    """★지금 «쓸 수 있는» 문서가 몇 건인지 센다 — 기억으로 정하지 않는다."""
    ok, short, notfilm = [], [], []
    for f in sorted(os.listdir(DOCS)):
        if not f.endswith(".md"):
            continue
        t = io.open(os.path.join(DOCS, f), encoding="utf-8",
                    errors="replace").read()
        m = re.search(r"^분류:\s*(.+)$", t, re.M)
        cats = [c.strip() for c in m.group(1).split(",")] if m else []
        name = f[:-3]
        if not any(WORK_CAT.search(c) and not NOT_WORK.search(c) for c in cats):
            notfilm.append(name)
        elif len(t) < MIN_CHARS:
            short.append(name)
        else:
            ok.append(name)
    return ok, short, notfilm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=60)
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--seeds", nargs="*", default=[
        "기생충 (영화)", "올드보이", "살인의 추억", "버닝 (영화)",
        "아가씨 (영화)", "밀양 (영화)", "시 (영화)", "괴물 (2006년 영화)",
        "마더 (2009년 영화)", "박하사탕",
    ])
    args = ap.parse_args()

    ok, short, notfilm = stats()
    print("=" * 72)
    print("★현재 코퍼스 — 기준으로 «센» 값")
    print("  ✅쓸 수 있음 (영화 작품 · %d자 이상)   %d건" % (MIN_CHARS, len(ok)))
    print("  ⚠짧아서 탈락 (줄거리 없음)            %d건" % len(short))
    print("  ⚠영화 작품 아님 (인물·기업·시상식)     %d건" % len(notfilm))
    print("  요건 「50건 이상」 → %s"
          % ("충족" if len(ok) >= 50 else "★%d건 부족" % (50 - len(ok))))
    print("=" * 72)
    if args.stats:
        print("\n탈락 — 짧음 %d건:\n  %s" % (len(short), " · ".join(short[:20])))
        print("\n탈락 — 영화 아님 %d건:\n  %s" % (len(notfilm), " · ".join(notfilm[:20])))
        return

    need = max(0, args.target - len(ok))
    if not need:
        print("\n목표 %d건 달성 — 받을 것 없다" % args.target)
        return
    print("\n목표 %d건 · ★%d건 더 받는다" % (args.target, need))

    seen = have()
    cand, added, checked = [], 0, 0

    # ★1홉 — 시드 자체
    for s in args.seeds:
        cand.append(s)
    # ★2홉 — 시드가 가리키는 문서
    for s in args.seeds:
        if added + len(cand) > need * 6:
            break
        try:
            cand += [t for t in links_in(s) if not DROP_TITLE.search(t)]
        except Exception as exc:
            print("  링크 실패 %s — %s" % (s, str(exc)[:50]))

    # ★sorted + dedup — 순서가 실행마다 달라지면 코퍼스가 재현되지 않는다
    seq = []
    for t in cand:
        if t not in seq:
            seq.append(t)

    for t in seq:
        if added >= need:
            break
        if fname(t)[:-3] in seen:
            continue
        checked += 1
        try:
            pg = page(t)
        except Exception:
            continue
        if not pg or not pg["text"]:
            continue
        if not is_film_work(pg):
            continue
        if len(pg["text"]) < MIN_CHARS:
            continue
        if args.dry:
            print("  [받을 것] %-34s %d자" % (pg["title"], len(pg["text"])))
        else:
            write_doc(pg)
            print("  +%-34s %d자" % (pg["title"], len(pg["text"])))
        added += 1
        time.sleep(0.15)

    print("\n%s %d건 · 확인 %d건"
          % ("받을 것" if args.dry else "★받았다", added, checked))
    if not args.dry:
        ok2, _, _ = stats()
        print("⇒ 쓸 수 있는 문서 %d → ★%d건" % (len(ok), len(ok2)))


if __name__ == "__main__":
    main()
