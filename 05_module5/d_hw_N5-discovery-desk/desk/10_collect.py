# -*- coding: utf-8 -*-
"""★지식원을 «모은다» — 노드3 수집기를 재사용하되 «저장»한다.

노드3(뉴스레터)은 수집 → 선별 → 발행 후 **기사를 버렸다**(store 에 metrics 만 남는다).
발행이 목적이었으니 맞다. 그런데 노드5 는 **질문에 답해야** 하므로 **지식원이 남아야** 한다.

★이것이 노드4 의 「어드민 조회」에 대응한다
  모두몰은 주문·상품 데이터가 **주어졌다**(mockdata_modumall.json).
  내 도메인에는 그런 게 없다. **내가 모아야 한다.**
  그리고 모으는 순간 **확실성 등급이 «실물로» 생긴다** — 48시간 이내면 [신설]이다.

  python 10_collect.py                 # 48시간
  python 10_collect.py --hours 168     # 일주일 (문항을 더 모으려면)
"""
import argparse
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests
import yaml

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent
UA = {"User-Agent": "Mozilla/5.0 (discovery-desk; KDT study)"}

# ★settings.yaml 의 group 을 내 라우트로 옮긴다
GROUP_TO_ROUTE = {"우주": "SPACE", "고고": "ARCHAEO", "고생물": "PALEO"}


def clean(s):
    """HTML 태그와 연속 공백을 턴다."""
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", s).strip()


def parse_when(e):
    for k in ("published_parsed", "updated_parsed"):
        t = e.get(k)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    return None


def certainty(published, now):
    """★확실성 등급을 «발표 시점»으로 1차 판정한다.

    여기서 나오는 건 [신설] 하나뿐이다 — 나머지(정설·추정·논쟁)는
    **본문을 읽어야** 알 수 있고 그건 다음 단계(11_factcard)의 일이다.
    ⇒ 이 함수가 하는 일은 「이건 «갓 나온» 것이다」를 표시하는 것뿐이다.
    """
    if not published:
        return "미상"
    age = (now - published).total_seconds() / 3600
    return "신설" if age <= 72 else "최근"


def main():
    ap = argparse.ArgumentParser(description="지식원 수집")
    ap.add_argument("--hours", type=int, default=48)
    ap.add_argument("--per-source", type=int, default=12, help="소스당 상한")
    ap.add_argument("--out", default="store/articles.json")
    args = ap.parse_args()

    cfg = yaml.safe_load((HERE / "settings.yaml").read_text(encoding="utf-8"))
    sources = cfg["sources"]
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=args.hours)

    print("=== 지식원 수집 — 소스 %d곳 · 최근 %d시간 ===" % (len(sources), args.hours))
    arts, seen = [], set()
    per_source = {}

    for s in sources:
        t0 = time.perf_counter()
        try:
            r = requests.get(s["url"], headers=UA, timeout=15)
            d = feedparser.parse(r.content)
        except Exception as e:                       # noqa: BLE001
            print("  %-16s ⛔ %s" % (s["name"], type(e).__name__))
            per_source[s["name"]] = 0
            continue

        n = 0
        for e in d.entries:
            if n >= args.per_source:
                break
            when = parse_when(e)
            if when and when < cutoff:
                continue
            link = (e.get("link") or "").split("?")[0]   # 추적 파라미터 제거
            if not link or link in seen:
                continue
            seen.add(link)
            arts.append({
                "id": "A%04d" % (len(arts) + 1),
                "title": clean(e.get("title")),
                "summary": clean(e.get("summary") or e.get("description"))[:900],
                "link": link,
                "source": s["name"],
                "tier": s.get("tier", 2),
                "route": GROUP_TO_ROUTE.get(s.get("group"), "OTHER"),
                "published": when.isoformat() if when else None,
                "certainty": certainty(when, now),
            })
            n += 1
        per_source[s["name"]] = n
        print("  %-16s %2d건  (%.1f초)" % (s["name"], n, time.perf_counter() - t0))

    out = HERE / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "collected_at": now.isoformat(),
        "window_hours": args.hours,
        "articles": arts,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    print()
    print("=== 요약 ===")
    from collections import Counter
    rc = Counter(a["route"] for a in arts)
    cc = Counter(a["certainty"] for a in arts)
    print("   총 %d건 → %s" % (len(arts), out))
    print("   라우트별  " + " · ".join("%s %d" % (k, v) for k, v in rc.most_common()))
    print("   확실성    " + " · ".join("%s %d" % (k, v) for k, v in cc.most_common()))
    dead = [k for k, v in per_source.items() if v == 0]
    print("   ★0건인 소스 %d곳: %s" % (len(dead), ", ".join(dead) if dead else "없음"))
    print()
    print("   ※ 라우트가 «소스 그룹»에서 왔다 — 기사 내용이 아니다.")
    print("     이건 지식원의 «출처 표시»일 뿐, ①의 정답으로 쓰지 않는다.")
    print("     (평가셋은 내가 «따로» 쓴다. 섞으면 채점이 자기 자신을 채점하게 된다)")

    # ★§F-8-D 3단계 — 방금 쓴 파일을 «지금» 검사한다
    raw = out.read_bytes()
    bad = len([1 for b in raw if b < 9 or (13 < b < 32)])
    print("   [자기검사] 제어문자 %d개" % bad)


if __name__ == "__main__":
    main()
