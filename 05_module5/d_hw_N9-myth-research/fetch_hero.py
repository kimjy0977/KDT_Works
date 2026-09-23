# -*- coding: utf-8 -*-
"""★표제 그림을 위키미디어 공용에서 가져온다 — 라이선스를 «확인해서».

  python fetch_hero.py --list        후보를 찾아 라이선스·크기만 본다
  python fetch_hero.py --get <파일>   내려받는다

왜 위키미디어인가
  ⛔스톡 이미지를 깔면 그건 장식이고 AI 표식이다.
  ✅코퍼스가 «위키백과»다. 같은 출처의 퍼블릭 도메인 그림이면
    장식이 아니라 ★«같은 자료»다.

★반드시 지키는 것
  ① 라이선스를 «확인»한다 — PD 또는 CC 만. 확인 못 하면 안 쓴다
  ② 출처와 저작자를 ★화면과 README 에 적는다
  ③ 파일 크기를 줄인다 — 저장소에 수 MB 를 넣지 않는다
"""
import argparse
import io
import json
import os
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://commons.wikimedia.org/w/api.php"
UA = "KDT-m5-myth-research/1.0 (study project; contact via github kimjy0977)"

후보 = [
    # ★가로로 «긴» 것만 — 파피루스·부조·프리즈는 원래 띠 모양이다
    "File:Great Papyrus of Hunefer.jpg",
    "File:Papyrus of Ani (Book of the Dead).jpg",
    "File:Hunefer weighing of the heart.jpg",
    "File:Book of the Dead of Hunefer sheet 3.jpg",
    "File:Ishtar Gate at Berlin Museum.jpg",
    "File:Lion of Babylon, Ishtar Gate, Pergamon Museum, Berlin.jpg",
    "File:Parthenon Frieze.jpg",
    "File:Gigantomachy Pergamon Altar.jpg",
    "File:Flood tablet, Epic of Gilgamesh.jpg",
    "File:Assyrian relief lion hunt British Museum.jpg",
]


def api(params):
    params = dict(params, format="json", formatversion="2")
    req = urllib.request.Request(
        API + "?" + urllib.parse.urlencode(params),
        headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def 정보(titles):
    r = api({"action": "query", "titles": "|".join(titles),
             "prop": "imageinfo",
             "iiprop": "url|size|extmetadata|mime",
             "iiurlwidth": 2000})
    out = []
    for p in r.get("query", {}).get("pages", []):
        if "imageinfo" not in p:
            out.append({"제목": p.get("title"), "★없음": True})
            continue
        i = p["imageinfo"][0]
        e = i.get("extmetadata", {})

        def g(k):
            return (e.get(k, {}).get("value") or "").replace("<br/>", " ")[:120]
        out.append({
            "제목": p["title"],
            "라이선스": g("LicenseShortName"),
            "저작자": __import__("re").sub("<[^>]+>", "", g("Artist")).strip(),
            "크기": "%dx%d" % (i["width"], i["height"]),
            "가로세로": round(i["width"] / max(1, i["height"]), 2),
            "url": i.get("thumburl") or i["url"],
            "설명페이지": i.get("descriptionurl"),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--get")
    ap.add_argument("--width", type=int, default=1800)
    a = ap.parse_args()

    if a.get:
        d = 정보([a.get])[0]
        if d.get("★없음"):
            raise SystemExit("★그런 파일이 없습니다")
        lic = d["라이선스"].lower()
        if not any(k in lic for k in ("public domain", "cc", "pd")):
            raise SystemExit("⛔라이선스를 확인 못 했습니다: %s" % d["라이선스"])
        url = d["url"].replace("/2000px-", "/%dpx-" % a.width)
        os.makedirs(os.path.join(HERE, "docs"), exist_ok=True)
        out = os.path.join(HERE, "docs/hero.jpg")
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=90) as r, \
                open(out, "wb") as f:
            f.write(r.read())
        메타 = {"파일": d["제목"], "라이선스": d["라이선스"],
               "저작자": d["저작자"], "출처": d["설명페이지"],
               "내려받은 폭": a.width}
        io.open(os.path.join(HERE, "docs/hero.json"), "w",
                encoding="utf-8", newline="").write(
            json.dumps(메타, ensure_ascii=False, indent=1))
        print("  OK docs/hero.jpg · %.0fKB" % (os.path.getsize(out) / 1024))
        print("  ★라이선스 %s · %s" % (d["라이선스"], d["저작자"][:60]))
        print("  → docs/hero.json 에 출처를 적었습니다 (화면·README 에 표기)")
        return

    print("═══ 표제 그림 후보 — ★라이선스를 확인합니다 ═══\n")
    for d in 정보(후보):
        if d.get("★없음"):
            print("  ⛔없음  %s" % d["제목"])
            continue
        print("  %-52s %s" % (d["제목"][:52], d["크기"]))
        print("     가로:세로 %.2f · %s · %s"
              % (d["가로세로"], d["라이선스"] or "★불명", d["저작자"][:46]))
    print("\n  ★가로로 긴 것(가로세로 2.0 이상)이 표제에 맞습니다.")


if __name__ == "__main__":
    main()
