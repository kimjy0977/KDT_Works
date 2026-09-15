"""내 분야는 «몇 칸»이고 «먹고 살 만한가» — 4강 방법을 내 관심사에 그대로 적용.

  python 02_probe_interests.py           # 24h · 7d 건수까지
  python 02_probe_interests.py --g1      # 본문 추출까지 (느림)

★교안 13강: 「구조는 그대로 두고 «내용만» 바꿔도 완전히 다른 뉴스레터가 된다」
  이 스크립트가 그 «내용»을 바꿔도 되는지 먼저 재 본다.
"""
import sys
import time
from datetime import datetime, timezone

import feedparser
import requests

UA = {"User-Agent": "Mozilla/5.0 (newsletter-agent; KDT study)"}
BODY_MIN = 600

TOPICS = {
    "우주": [
        ("NASA Breaking", "https://www.nasa.gov/rss/dyn/breaking_news.rss", 1),
        ("ESA Space News", "https://www.esa.int/rssfeed/Our_Activities/Space_News", 1),
        ("SpaceNews", "https://spacenews.com/feed/", 2),
        ("Space.com", "https://www.space.com/feeds/all", 2),
        ("Universe Today", "https://www.universetoday.com/feed", 2),
        ("Phys.org Space", "https://phys.org/rss-feed/space-news/", 2),
        
        
    ],
    "고고학": [
        # ★2026-09-14 1차 측정에서 4곳이 404/403/0건으로 떨어졌다.
        #   그중 둘은 «주소가 틀린 것»이었다 — 4강 G3(접근) 은 「막혔나」뿐 아니라
        #   「내가 주소를 잘못 알고 있나」도 같이 본다.
        ("Phys.org 고고학", "https://phys.org/rss-feed/science-news/archaeology/", 2),   # 주소 정정
        ("Nature 고고학", "https://www.nature.com/subjects/archaeology.rss", 1),          # 새로 찾음
        ("ScienceDaily 고고학", "https://www.sciencedaily.com/rss/fossils_ruins/archaeology.xml", 2),
        ("The Past", "https://the-past.com/feed/", 2),
        ("Live Science", "https://www.livescience.com/feeds/all", 2),   # ⚠전체 피드 — 주제 필터 필요
        # 탈락 확정 (UA 바꿔 재시도해도 실패):
        #   Archaeology Mag  404 · HeritageDaily 200이지만 항목 0
        #   Ancient Origins  403 · Smithsonian 404 · Sky&Telescope 403
    ],
}


def strip_tags(s):
    import re
    return re.sub(r"<[^>]+>", "", s or "").strip()


def at_of(e):
    t = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
    return datetime(*t[:6], tzinfo=timezone.utc) if t else None


def probe(name, url, tier):
    row = {"name": name, "tier": tier, "url": url}
    t0 = time.time()
    try:
        r = requests.get(url, headers=UA, timeout=20)
        row["http"] = r.status_code
        d = feedparser.parse(r.content)
    except Exception as exc:
        row["http"] = "ERR"
        row["err"] = str(exc)[:50]
        return row
    row["sec"] = round(time.time() - t0, 1)
    es = d.entries
    row["n"] = len(es)
    if not es:
        return row
    lens = [len(strip_tags(getattr(e, "summary", ""))) for e in es[:20]]
    row["sumlen"] = int(sum(lens) / len(lens)) if lens else 0
    now = datetime.now(timezone.utc)
    ats = [a for a in (at_of(e) for e in es) if a]
    row["dated"] = len(ats)
    if ats:
        row["age_h"] = round((now - max(ats)).total_seconds() / 3600, 1)
        row["d1"] = sum(1 for a in ats if (now - a).total_seconds() <= 86400)
        row["d7"] = sum(1 for a in ats if (now - a).days <= 7)
    return row


def g1(name, url):
    import trafilatura
    try:
        r = requests.get(url, headers=UA, timeout=20)
        d = feedparser.parse(r.content)
    except Exception as exc:
        return name, "피드실패", str(exc)[:30]
    ok = tried = 0
    rl = []
    for e in d.entries[:3]:
        rl.append(len(strip_tags(getattr(e, "summary", ""))))
        link = getattr(e, "link", None)
        if not link:
            continue
        tried += 1
        try:
            body = trafilatura.extract(requests.get(link, headers=UA, timeout=25).text) or ""
            if len(body) >= BODY_MIN:
                ok += 1
        except Exception:
            pass
    avg = int(sum(rl) / len(rl)) if rl else 0
    return name, "RSS요약 %d자" % avg, "원문추출 %d/%d" % (ok, tried)


def main():
    print("=" * 96)
    print("관심사 소스 측정 — 4강 「소스를 재고 고르기」 / %s"
          % datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 96)
    keep_all = {}
    for topic, cands in TOPICS.items():
        print()
        print("### %s" % topic)
        print("%-22s %5s %6s %6s %8s %8s %6s %6s" %
              ("소스", "tier", "HTTP", "건수", "요약길이", "최신(h)", "24h", "7일"))
        print("-" * 96)
        rows = []
        for name, url, tier in cands:
            r = probe(name, url, tier)
            rows.append(r)
            print("%-22s %5s %6s %6s %8s %8s %6s %6s" % (
                name, r.get("tier", "-"), r.get("http", "-"), r.get("n", "-"),
                r.get("sumlen", "-"), r.get("age_h", "-"),
                r.get("d1", "-"), r.get("d7", "-")))
            if r.get("err"):
                print("    └ %s" % r["err"])
        keep = [r for r in rows if r.get("http") == 200 and r.get("n") and r.get("d7", 0) >= 1]
        drop = [r for r in rows if r not in keep]
        d1 = sum(r.get("d1", 0) for r in keep)
        d7 = sum(r.get("d7", 0) for r in keep)
        print("-" * 96)
        print("  채택 후보 %d곳 / 탈락 %d곳   ·   24시간 합 %d건 · 7일 합 %d건"
              % (len(keep), len(drop), d1, d7))
        for r in drop:
            why = "HTTP %s" % r.get("http") if r.get("http") != 200 else \
                  ("항목 0건" if not r.get("n") else "7일 내 %d건" % r.get("d7", 0))
            print("    탈락  %-22s %s" % (r["name"], why))
        # 판정
        if d1 >= 30:
            v = "★24시간 창으로 충분하다 (AI 분야와 같은 설계 그대로)"
        elif d1 >= 10:
            v = "24시간도 되지만 «적게 발행되는 날»이 잦을 것 — 48h 권장"
        elif d7 >= 20:
            v = "★24시간은 부족하다 — «7일 창 + 주 1~2회 발행»으로 바꿔야 한다"
        else:
            v = "⚠ 소스가 모자라다 — 소스를 더 찾거나 주제를 넓혀야 한다"
        print("  판정: %s" % v)
        keep_all[topic] = (keep, d1, d7)

    if "--g1" in sys.argv:
        print()
        print("=" * 96)
        print("G1 본문 관문 (소스마다 기사 3건)")
        print("=" * 96)
        for topic, (keep, _, _) in keep_all.items():
            print("### %s" % topic)
            for r in keep:
                a, b, c = g1(r["name"], r["url"])
                print("  %-22s %-18s %s" % (a, b, c))


if __name__ == "__main__":
    main()
