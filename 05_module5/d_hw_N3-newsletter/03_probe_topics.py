"""관심사 «후보군» 전수 측정 — 무엇으로 뉴스레터를 만들지 «숫자로» 고른다.

주영님 말: 「우주랑 고고학은 뭔가 «새롭게 발견한 것들»이잖아」
→ 그 축(발견)과, 다른 축(예술·디자인)을 나란히 놓고 잰다.
→ 그리고 어제 문제였던 «한국어 소스 0곳»도 따로 잰다.

  python 03_probe_topics.py
  python 03_probe_topics.py --g1
"""
import sys
import time
from datetime import datetime, timezone

import feedparser
import requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"}
BODY_MIN = 600

GROUPS = {
    "A. 우주·천문": [
        ("NASA Breaking", "https://www.nasa.gov/rss/dyn/breaking_news.rss", 1),
        ("ESA Space News", "https://www.esa.int/rssfeed/Our_Activities/Space_News", 1),
        ("Space.com", "https://www.space.com/feeds/all", 2),
        ("Universe Today", "https://www.universetoday.com/feed", 2),
        ("Phys.org Space", "https://phys.org/rss-feed/space-news/", 2),
        ("SpaceNews", "https://spacenews.com/feed/", 2),
    ],
    "B. 고고학·유적": [
        ("Phys.org 고고학", "https://phys.org/rss-feed/science-news/archaeology/", 2),
        ("Nature 고고학", "https://www.nature.com/subjects/archaeology.rss", 1),
        ("ScienceDaily 고고", "https://www.sciencedaily.com/rss/fossils_ruins/archaeology.xml", 2),
        ("The Past", "https://the-past.com/feed/", 2),
    ],
    "C. 고생물·인류 (발견 축 보강)": [
        ("Nature 고생물", "https://www.nature.com/subjects/palaeontology.rss", 1),
        ("Phys.org 진화", "https://phys.org/rss-feed/biology-news/evolution/", 2),
        ("ScienceDaily 화석", "https://www.sciencedaily.com/rss/fossils_ruins.xml", 2),
        ("Sci.News", "https://www.sci.news/feed", 2),
        ("Smithsonian SmartNews", "https://www.smithsonianmag.com/rss/smart-news/", 2),
    ],
    "D. 예술·미술": [
        ("Hyperallergic", "https://hyperallergic.com/feed/", 2),
        ("ARTnews", "https://www.artnews.com/feed/", 2),
        ("Artnet News", "https://news.artnet.com/feed", 2),
        ("The Art Newspaper", "https://www.theartnewspaper.com/rss", 2),
        ("Colossal", "https://www.thisiscolossal.com/feed/", 2),
    ],
    "E. 디자인·건축": [
        ("Dezeen", "https://www.dezeen.com/feed/", 2),
        ("designboom", "https://www.designboom.com/feed/", 2),
        ("Core77", "https://www.core77.com/blog/rss.php", 2),
        ("It's Nice That", "https://www.itsnicethat.com/rss", 2),
        ("ArchDaily", "https://www.archdaily.com/rss/", 2),
    ],
    "F. ★한국어 (어제 0곳이었다)": [
        ("사이언스타임즈", "https://www.sciencetimes.co.kr/feed/", 2),
        ("한겨레 과학", "https://www.hani.co.kr/rss/science/", 2),
        ("경향 과학", "https://www.khan.co.kr/rss/rssdata/kh_science.xml", 2),
        ("동아사이언스 m", "https://m.dongascience.com/rss.php", 2),
        ("연합뉴스 문화", "https://www.yna.co.kr/rss/culture.xml", 2),
        ("한겨레 문화", "https://www.hani.co.kr/rss/culture/", 2),
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
    try:
        r = requests.get(url, headers=UA, timeout=20)
        row["http"] = r.status_code
        d = feedparser.parse(r.content)
    except Exception as exc:
        row["http"] = "ERR"
        row["err"] = str(exc)[:45]
        return row
    es = d.entries
    row["n"] = len(es)
    if not es:
        return row
    lens = [len(strip_tags(getattr(e, "summary", ""))) for e in es[:20]]
    row["sumlen"] = int(sum(lens) / len(lens)) if lens else 0
    now = datetime.now(timezone.utc)
    ats = [a for a in (at_of(e) for e in es) if a]
    if ats:
        row["age_h"] = round((now - max(ats)).total_seconds() / 3600, 1)
        row["d1"] = sum(1 for a in ats if (now - a).total_seconds() <= 86400)
        row["d7"] = sum(1 for a in ats if (now - a).days <= 7)
    else:
        row["nodate"] = True
    return row


def g1(url):
    import trafilatura
    try:
        d = feedparser.parse(requests.get(url, headers=UA, timeout=20).content)
    except Exception:
        return 0, 0
    ok = tried = 0
    for e in d.entries[:3]:
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
    return ok, tried


def main():
    print("=" * 100)
    print("관심사 후보군 전수 측정 — 4강 방식 / %s" % datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 100)
    totals = {}
    keeps = {}
    for g, cands in GROUPS.items():
        print()
        print("### %s" % g)
        print("%-22s %4s %6s %6s %7s %7s %5s %5s" %
              ("소스", "tier", "HTTP", "건수", "요약", "최신h", "24h", "7일"))
        print("-" * 100)
        rows = []
        for name, url, tier in cands:
            r = probe(name, url, tier)
            rows.append(r)
            print("%-22s %4s %6s %6s %7s %7s %5s %5s" % (
                name, r.get("tier", "-"), r.get("http", "-"), r.get("n", "-"),
                r.get("sumlen", "-"), r.get("age_h", "-"),
                r.get("d1", "-"), r.get("d7", "-")))
            if r.get("err"):
                print("    └ %s" % r["err"])
        keep = [r for r in rows if r.get("http") == 200 and r.get("n") and r.get("d7", 0) >= 1]
        d1 = sum(r.get("d1", 0) for r in keep)
        d7 = sum(r.get("d7", 0) for r in keep)
        totals[g] = (len(keep), len(rows), d1, d7)
        keeps[g] = keep
        print("-" * 100)
        print("  채택 %d / %d곳   ·   24시간 %d건 · 7일 %d건" % (len(keep), len(rows), d1, d7))

    print()
    print("=" * 100)
    print("%-32s %8s %10s %10s   %s" % ("묶음", "채택", "24시간", "7일", "판정"))
    print("-" * 100)
    for g, (k, n, d1, d7) in totals.items():
        if d1 >= 20:
            v = "★단독으로 매일 발행 가능"
        elif d1 >= 8:
            v = "48h 창이면 매일 가능"
        elif d7 >= 20:
            v = "주 1~2회 (7일 창) 또는 «다른 묶음과 합치기»"
        else:
            v = "⚠ 단독 불가"
        print("%-32s %5d/%-2d %9d건 %9d건   %s" % (g, k, n, d1, d7, v))

    if "--g1" in sys.argv:
        print()
        print("=" * 100)
        print("G1 본문 관문 — 채택분만 (소스마다 기사 3건)")
        print("=" * 100)
        for g, keep in keeps.items():
            print("### %s" % g)
            for r in keep:
                ok, tried = g1(r["url"])
                mark = "OK " if tried and ok == tried else "★확인"
                print("  %s %-22s RSS요약 %4s자 → 원문추출 %d/%d"
                      % (mark, r["name"], r.get("sumlen", "-"), ok, tried))


if __name__ == "__main__":
    main()
