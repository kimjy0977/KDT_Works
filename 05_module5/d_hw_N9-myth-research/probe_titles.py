# -*- coding: utf-8 -*-
"""★SEED 에 적은 제목이 «실제로 있는지» 먼저 찾아본다.

왜 만드나
  첫 수집에서 47개 중 17개가 빠졌다. 「없다」가 아니라 대부분
  «이름이 다르거나 넘겨주기»였다 (주몽 → 동명성왕, 저승 → 내세).
  ⛔여기서 「아마 노르드 신화겠지」로 «메우면» 안 된다 —
    하네스 §6 의 「번호가 규칙적으로 보인다고 빈칸을 추측으로 채우지 말 것」과
    같은 자리다. **찾아서 «잰다».**

쓰는 법
  python probe_titles.py 제목1 제목2 ...
  python probe_titles.py --missing        SEED 중 코퍼스에 없는 것만
"""
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://ko.wikipedia.org/w/api.php"
UA = "KDT-m5-myth-research/1.0 (study project; contact via github kimjy0977)"


def api(params):
    params = dict(params, format="json", formatversion="2")
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(API, data=data, headers={"User-Agent": UA})
    for i in range(6):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except Exception:
            if i == 5:
                raise
            time.sleep(2.0 * (2 ** i))


def missing():
    src = io.open(os.path.join(HERE, "fetch_corpus.py"), encoding="utf-8").read()
    i = src.index("SEED = [")
    seed = re.findall(r'"([^"]+)"', src[i:src.index("]", i)])
    p = os.path.join(HERE, "data/corpus.json")
    if not os.path.exists(p):
        return seed
    c = json.load(io.open(p, encoding="utf-8"))
    docs = c.get("docs", c) if isinstance(c, dict) else c
    return [t for t in seed if t not in docs]


def main():
    want = missing() if "--missing" in sys.argv else sys.argv[1:]
    if not want:
        print("  볼 것이 없습니다"); return
    print("═══ %d개 제목을 찾습니다 ═══" % len(want))
    for t in want:
        r = api({"action": "query", "list": "search", "srsearch": t,
                 "srlimit": 3, "srprop": "size"})
        hits = r.get("query", {}).get("search", [])
        if not hits:
            print("  %-16s ⛔검색 결과 없음" % t)
            continue
        # 정확히 같은 제목이 있나 — 넘겨주기까지 확인
        r2 = api({"action": "query", "titles": t, "redirects": 1,
                  "prop": "info"})
        pg = (r2.get("query", {}).get("pages") or [{}])[0]
        real = pg.get("title")
        miss = pg.get("missing")
        head = "⛔없음" if miss else ("→ %s" % real if real != t else "✅그대로")
        print("  %-16s %-14s  후보: %s"
              % (t, head, " · ".join("%s(%d자)" % (h["title"], h["size"])
                                     for h in hits)))


main()
