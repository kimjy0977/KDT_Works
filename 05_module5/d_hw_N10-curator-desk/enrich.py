# -*- coding: utf-8 -*-
"""★작가를 «조회»한다 — C3·C4·C5 의 정답출처.

  python enrich.py            data/clean.json → data/enriched.json
  python enrich.py --nocache  캐시 무시하고 다시 조회

⛔냄새로 판정하지 않는다
  「공백 없는 한 낱말이면 계정명」 같은 규칙은
  ★Sailko 를 못 잡고 Rembrandt 를 잡는다. (실측 — 계정꼴 규칙이 1건만 골랐다)
  ⇒ 판정은 «조회»가 한다. 위키백과에 «화가»로 있는가를 묻는다.

★두 단계로 묻는다
  ① 위키백과  en.wikipedia.org  제목 → wikibase_item (Q번호)
  ② 위키데이터 wikidata.org     Q번호 → P106(직업) · P569(생) · P570(몰) · 레이블

★「못 찾음」과 「없음」을 섞지 않는다
  조회 실패(네트워크·429)는 ★"미조회" 로 남긴다. "없다"로 적지 않는다.
  관문은 미조회를 «멈춤»으로 다루되, 화면 문구를 다르게 적는다.
"""
import argparse
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
WP = "https://en.wikipedia.org/w/api.php"
WD = "https://www.wikidata.org/w/api.php"
UA = {"User-Agent": "KDT-curator-desk/0.1 (study project; contact via github)"}
CACHE = os.path.join(HERE, "data/wiki_cache.json")

# ★「화가·미술가」로 치는 직업 Q번호.
#   ⛔목록을 «고정»으로 보지 않는다 — 모자라면 여기 한 줄 더한다(§F-8-D).
#   그리고 ★목록에 없다고 「화가가 아니다」라고 «단정»하지 않는다 —
#   관문은 「확인 못 했다」로 멈춘다.
미술직업 = {
    "Q1028181": "화가",
    "Q483501": "예술가",
    "Q1281618": "조각가",
    "Q15296811": "삽화가",
    "Q329439": "판화가",
    "Q11569986": "회화 제작자",
    "Q42973": "건축가",
    "Q33231": "사진가",        # ★있으면 «사진가»라고 말해 준다 — 화가와 다르다
}
화가류 = {"Q1028181", "Q483501", "Q1281618", "Q15296811",
         "Q329439", "Q11569986"}


def 부른다(base, params, 재시도=5):
    """★429 를 만나면 «쉬었다» 다시. 0건과 못 받은 것을 섞지 않으려고."""
    쉼 = 2.0
    for i in range(재시도):
        q = urllib.parse.urlencode(dict(params, format="json"))
        try:
            req = urllib.request.Request(base + "?" + q, headers=UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == 재시도 - 1:
                raise
            print("    ↻ 429 — %.0f초 쉬고 다시" % 쉼)
            time.sleep(쉼)
            쉼 *= 2
    raise RuntimeError("재시도 소진")


def _연도(claim):
    """위키데이터 시간값에서 연도. ★정밀도가 낮으면 None 이 아니라 표시한다."""
    try:
        v = claim[0]["mainsnak"]["datavalue"]["value"]
        t, p = v["time"], v.get("precision", 9)
        y = int(t[1:5]) * (-1 if t[0] == "-" else 1)
        return {"연": y, "정밀도": p}
    except Exception:
        return None


def 작가조회(이름):
    """이름 하나를 조회한다. 반환 dict — ⛔실패를 «없음»으로 바꾸지 않는다."""
    # ★레이블을 «언어별로» 담는다.
    #   ⛔한 칸에 ko 를 넣었더니 「Nicolai Abildgaard ≠ 니콜라이 아빌고르」가
    #     ★«이름 충돌»로 세어졌다(11건). 그건 충돌이 아니라 «번역»이다.
    #     Commons 의 Artist 는 로마자라 ★en 과 비교해야 한다.
    r = {"질의": 이름, "상태": "미조회", "Q": None,
         "레이블": None, "레이블ko": None, "레이블en": None,
         "직업": [], "화가인가": None, "생": None, "몰": None,
         "위키문서": None}
    if not (이름 or "").strip():
        r["상태"] = "이름없음"
        return r

    try:
        d = 부른다(WP, {"action": "query", "titles": 이름,
                      "prop": "pageprops", "ppprop": "wikibase_item",
                      "redirects": 1})
    except Exception as e:
        r["오류"] = str(e)[:80]
        return r                      # ★"미조회" 그대로 — 없다고 하지 않는다

    pages = (d.get("query") or {}).get("pages") or {}
    page = next(iter(pages.values()), {})
    if "missing" in page:
        r["상태"] = "문서없음"        # ★조회는 «됐고» 문서가 없다 — 다른 말이다
        return r
    r["위키문서"] = page.get("title")
    q = (page.get("pageprops") or {}).get("wikibase_item")
    if not q:
        r["상태"] = "위키데이터없음"
        return r
    r["Q"] = q

    try:
        d2 = 부른다(WD, {"action": "wbgetentities", "ids": q,
                       "props": "claims|labels", "languages": "ko|en"})
    except Exception as e:
        r["오류"] = str(e)[:80]
        return r

    ent = (d2.get("entities") or {}).get(q) or {}
    lab = ent.get("labels") or {}
    r["레이블ko"] = (lab.get("ko") or {}).get("value")
    r["레이블en"] = (lab.get("en") or {}).get("value")
    r["레이블"] = r["레이블ko"] or r["레이블en"]   # 화면에 보일 이름
    cl = ent.get("claims") or {}

    for c in cl.get("P106", []):
        try:
            qq = c["mainsnak"]["datavalue"]["value"]["id"]
        except Exception:
            continue
        r["직업"].append(미술직업.get(qq, qq))
        if qq in 화가류:
            r["화가인가"] = True
    if r["직업"] and r["화가인가"] is None:
        r["화가인가"] = False          # 직업을 «읽었는데» 미술직업이 없다

    if cl.get("P569"):
        r["생"] = _연도(cl["P569"])
    if cl.get("P570"):
        r["몰"] = _연도(cl["P570"])
    r["상태"] = "조회됨"
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nocache", action="store_true")
    a = ap.parse_args()

    p_in = os.path.join(HERE, "data/clean.json")
    if not os.path.exists(p_in):
        print("  ⛔data/clean.json 이 없습니다. 먼저 python normalize.py")
        return 1
    작품 = json.load(io.open(p_in, encoding="utf-8"))["작품"]

    캐시 = {}
    if os.path.exists(CACHE) and not a.nocache:
        캐시 = json.load(io.open(CACHE, encoding="utf-8"))

    이름들 = sorted({c["작가"] for c in 작품 if (c["작가"] or "").strip()})
    print("═══ 작가 조회 — 서로 다른 이름 %d개 (작품 %d점) ═══"
          % (len(이름들), len(작품)))
    print()
    새로 = 0
    for i, nm in enumerate(이름들, 1):
        # ⛔★«미조회»를 캐시에 남기면 다시 돌려도 영영 안 채워진다.
        #   실패는 캐시하지 않는다 — 「못 받았다」는 답이 아니다.
        if nm in 캐시 and 캐시[nm].get("상태") != "미조회" and not a.nocache:
            continue
        캐시[nm] = 작가조회(nm)
        새로 += 1
        s = 캐시[nm]
        표 = s["상태"]
        if s["상태"] == "조회됨":
            표 = "%s · %s · %s~%s" % (
                s["레이블"] or "?",
                "화가" if s["화가인가"] else ("·".join(s["직업"][:2]) or "직업?"),
                (s["생"] or {}).get("연", "?"),
                (s["몰"] or {}).get("연", "생존?"))
        print("  %2d/%d  %-32s %s" % (i, len(이름들), nm[:32], 표))
        time.sleep(0.8)

    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    io.open(CACHE, "w", encoding="utf-8", newline="").write(
        json.dumps(캐시, ensure_ascii=False, indent=1))

    for c in 작품:
        c["작가조회"] = 캐시.get(c["작가"], {"상태": "이름없음", "질의": c["작가"]})

    # ★센다 — 이 수치가 그대로 C3·C5 의 개입률이다
    n = len(작품)
    상태 = {}
    for c in 작품:
        상태[c["작가조회"]["상태"]] = 상태.get(c["작가조회"]["상태"], 0) + 1
    화가 = sum(1 for c in 작품 if c["작가조회"].get("화가인가") is True)
    몰없음 = sum(1 for c in 작품
                if c["작가조회"].get("상태") == "조회됨"
                and not c["작가조회"].get("몰"))
    이름다름 = sum(1 for c in 작품
                 if c["작가조회"].get("레이블")
                 and c["작가조회"]["레이블"].lower() != c["작가"].lower())

    print()
    print("  ── 조회 결과 (작품 %d점 기준) ──" % n)
    for k, v in sorted(상태.items(), key=lambda x: -x[1]):
        print("    %-14s %2d건  (%4.1f%%)" % (k, v, v / n * 100))
    print()
    print("    ★위키데이터가 «화가»라 함   %2d건  (%4.1f%%)"
          % (화가, 화가 / n * 100))
    print("    ★화가 확인 안 됨 → C5      %2d건  (%4.1f%%)"
          % (n - 화가, (n - 화가) / n * 100))
    print("    ★몰년 없음(생존?) → C3     %2d건" % 몰없음)
    print("    ★Commons≠위키데이터 → C4   %2d건" % 이름다름)
    print("    (새로 조회 %d개 · 캐시 %d개)" % (새로, len(캐시) - 새로))

    p_out = os.path.join(HERE, "data/enriched.json")
    io.open(p_out, "w", encoding="utf-8", newline="").write(
        json.dumps({"작품": 작품, "수": n}, ensure_ascii=False, indent=1))
    print()
    print("  → data/enriched.json  %d점" % n)

    # ★§F-8-D 3단계 ① — 방금 쓴 파일을 그 자리에서 검사
    s = io.open(p_out, encoding="utf-8").read()
    bad = [i for i, ch in enumerate(s) if ord(ch) < 32 and ch != "\n"]
    if bad:
        print("  ⛔제어문자 %d개" % len(bad))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
