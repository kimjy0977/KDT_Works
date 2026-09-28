# -*- coding: utf-8 -*-
"""★회화를 «라이선스와 함께» 모은다 — 위키미디어 공용.

  python fetch_art.py --list          후보만 훑는다 (저장 안 함 · 키 불필요)
  python fetch_art.py                 data/corpus.json 으로 저장
  python fetch_art.py --n 60          몇 점 모을지

★노드9 의 fetch_hero.py 와 «무엇이 다른가» — 이 프로젝트의 출발점이다
  노드9:  라이선스를 확인 «못 하면» → ⛔SystemExit. 그냥 멈춘다.
          = 강의가 말한 ★선택지 ①(전부 막기). 안전하지만 쓸 수 있는 게 확 준다.
  노드10: 확인 «못 한 것»도 ★일단 담는다. 대신 «표시»를 단다.
          그 표시가 나중에 G1 관문에서 «사람에게 보낼지»를 가른다.
          = ★선택지 ③(위험한 것만 사람에게).

  ⇒ 같은 API, 같은 필드, ★다른 처리. 이 차이가 과제의 전부다.

⛔여기서 «버리지» 않는다
  수집 단계에서 라이선스 불명을 버리면 ★관문이 볼 것이 없어진다.
  「놓침·헛멈춤을 센다」는 요건은 ★걸러진 것까지 남아 있어야 잴 수 있다.
"""
import argparse
import io
import json
import os
import re
import time
import urllib.parse
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "KDT-curator-desk/0.1 (study project; contact via github)"}

CFG = json.load(io.open(os.path.join(HERE, "config.json"), encoding="utf-8"))
# ★config 의 관문 이름을 «그대로» 읽는다 — 여기서 다시 정하지 않는다.
#   ⛔이 줄이 한 번 샜다(2026-09-28): config 에서 G1 을 고쳤는데
#     여기 「허용목록」이 남아 KeyError 로 죽었다. 그런데 «tail 뒤»라
#     종료코드가 0 으로 보여 한동안 몰랐다(§A-8).
_B1 = CFG["_관문"]["B1_표시의무위반"]
표시의무 = [s.lower() for s in _B1["표시의무"]]
불명표현 = [s.lower() for s in _B1["불명표현"] if s]

# ★관심사 그대로 — 미술사 × 신화 × 세계사·전쟁사
#   ⛔목록을 «고정»으로 보지 않는다. 모자라면 여기 한 줄 더한다.
# ★파일 수를 «재서» 골랐다 (2026-09-28). 이름이 그럴듯해도 파일이 없을 수 있다.
#   실측 — 「Paintings of {주제}」 꼴은 ★흔히 «파일 없는 상위 분류»다:
#     Venus 0 · Hercules 0 · Trojan War 0 · Ovid's Metamorphoses 0
#   ⇒ 넣기 «전»에 센다. 추측으로 목록에 넣지 않는다.
분류 = [
    ("신화", "Category:Paintings of Greek mythology"),      # 실측 62
    ("신화", "Category:Paintings of Roman mythology"),       # 실측 42
    ("신화", "Category:Paintings of Norse mythology"),       # 실측 80
    ("신화", "Category:Paintings of Diana"),                 # 실측 46
    ("역사", "Category:History paintings"),                  # 실측 200
    ("종교·신화", "Category:New Testament paintings"),         # 실측 12
    ("전쟁", "Category:Paintings of battles"),               # 실측 213
    ("종교·신화", "Category:Old Testament paintings"),          # 실측 4
    # ⛔★「Battle paintings」는 뺐다 — 두 번 재서 두 번 0건이었다.
    #   allcategories 로는 «존재»한다고 나온다 ⇒ 있긴 있고 «파일이 없는»
    #   상위 분류다. 위의 Venus·Hercules 와 같은 꼴이다.
    #   ⇒ 「비었다」가 아니라 ★「파일을 직접 담지 않는 분류다」가 맞는 말이다.
]


def 부른다(params, 재시도=6):
    """★429 를 «기다려서» 푼다 — 노드3 에서 겪은 그것이다.

    위키미디어는 빨리 부르면 429 로 막는다. 실제로 막혔다(2026-09-28).
    ⛔「실패」로 처리하고 넘어가면 ★수집이 조용히 비어서,
      나중에 「그 분류엔 작품이 없다」로 잘못 읽는다.
      「없다」와 「못 받았다」는 다르다.
    """
    q = dict(params)
    q.update({"format": "json", "formatversion": "2"})
    url = API + "?" + urllib.parse.urlencode(q)
    쉼 = 3.0                       # ★1초로는 모자랐다(실측)
    for i in range(재시도):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == 재시도 - 1:
                raise
            print("    ↻ 429 — %.0f초 쉬고 다시" % 쉼)
            time.sleep(쉼)
            쉼 *= 2
    raise RuntimeError("도달 불가")


def 목록(cat, n):
    """분류 안의 파일 이름을 가져온다."""
    out, cont = [], None
    while len(out) < n:
        p = {"action": "query", "list": "categorymembers", "cmtitle": cat,
             "cmtype": "file", "cmlimit": "50"}
        if cont:
            p["cmcontinue"] = cont
        d = 부른다(p)
        out += [m["title"] for m in d.get("query", {}).get("categorymembers", [])]
        cont = d.get("continue", {}).get("cmcontinue")
        if not cont:
            break
        time.sleep(1.5)          # ★0.6초로는 429 가 났다
    return out[:n]


def 메타(titles):
    """★라이선스·작가·연도를 «원문 그대로» 가져온다. 해석하지 않는다."""
    out = []
    for i in range(0, len(titles), 20):
        묶음 = titles[i:i + 20]
        # ⛔★여기에 재시도가 «없어서» 429 하나에 분류가 통째로 죽었다.
        #   목록()에는 붙여 놓고 메타()에는 안 붙였다 — §H-4 그대로다.
        #   한 묶음이 실패해도 «나머지는 살린다».
        try:
            d = 부른다({"action": "query", "titles": "|".join(묶음),
                      "prop": "imageinfo",
                      "iiprop": "url|size|extmetadata|mime"})
        except Exception as e:
            print("      ⚠메타 묶음 %d~%d 못 받음: %s"
                  % (i, i + len(묶음), str(e)[:40]))
            time.sleep(10)
            continue
        for pg in d.get("query", {}).get("pages", []):
            ii = (pg.get("imageinfo") or [{}])[0]
            e = ii.get("extmetadata", {})

            def g(k):
                return (e.get(k) or {}).get("value", "")

            out.append({
                "제목": pg.get("title", ""),
                "url": ii.get("url", ""),
                "가로": ii.get("width", 0), "세로": ii.get("height", 0),
                "mime": ii.get("mime", ""),
                # ★해석하지 않고 «원문 그대로». 판정은 관문이 한다.
                "라이선스원문": g("LicenseShortName"),
                "저작자원문": g("Artist"),
                "연도원문": g("DateTimeOriginal"),
                "설명원문": g("ImageDescription"),
                "출처원문": g("Credit"),
            })
        time.sleep(1.5)
    return out


def _불명인가(작가):
    """작가명이 «없거나 없다고 적혀 있는가»."""
    t = (작가 or "").strip().lower()
    return (not t) or any(k in t for k in 불명표현)


def 관문판정(m):
    """★수집 단계에서 «잴 수 있는» 관문만 판정한다. 여기서 버리지 않는다.

    ⛔판정과 처분을 섞지 않는다 — 버릴지 말지는 관문(그래프)이 정한다.
      수집에서 걸러 버리면 ★놓침·헛멈춤을 «셀» 수가 없다.

    여기서 재는 것은 원문만 보면 판정이 끝나는 것들이다.
    A1·A2(해설 대조)와 C3·C4·D1(위키백과 조회)은 뒤 단계에서 잰다.
    """
    걸린 = []
    lic = (m.get("라이선스원문") or "").strip().lower()
    작가 = (m.get("저작자원문") or "").strip()
    연도 = m.get("연도원문") or ""

    # B1 — ★표시 의무인데 «표시할 저작자»가 없다
    if any(k in lic for k in 표시의무) and _불명인가(작가):
        걸린.append("B1_표시의무위반")

    # B2 — 1900년 이후 (현대 스캔·사진 · 저작권이 살아 있을 수 있다)
    해 = re.search("(1[0-9]{3}|20[0-9]{2})", 연도)
    if 해 and int(해.group(1)) >= 1900:
        걸린.append("B2_현대물")

    # C1 — 작가명에 HTML 태그가 섞였다
    if "<" in 작가 and ">" in 작가:
        걸린.append("C1_이름오염")

    # C2 — 작가 불명
    if _불명인가(작가):
        걸린.append("C2_작가불명")

    # D2 — 연도 원문에 태그
    if "<" in 연도 and ">" in 연도:
        걸린.append("D2_연도오염")

    return 걸린


def _저장(작품):
    """★모은 만큼 «바로» 적는다 — 옆에 쓰고 갈아 끼운다(원자적)."""
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    p = os.path.join(HERE, "data/corpus.json")
    임시 = p + ".tmp"
    io.open(임시, "w", encoding="utf-8", newline="").write(
        json.dumps({"작품": 작품, "수집": len(작품)},
                   ensure_ascii=False, indent=1))
    os.replace(임시, p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="저장 없이 훑기만")
    ap.add_argument("--n", type=int, default=CFG["수집목표"])
    a = ap.parse_args()

    몫 = max(3, a.n // len(분류) + 1)
    작품 = []
    print("═══ 회화 수집 — ★라이선스를 «원문 그대로» 같이 담는다 ═══\n")
    for 갈래, cat in 분류:
        # ⛔429 로 «분류 하나를 통째로» 잃지 않는다.
        #   실측 2026-09-28 — 종교·신화가 통째로 빠져 목표 200 에 130 만 모였다.
        #   ★「못 받았다」를 「없다」로 만들지 않으려면 여기서 한 번 더 기다린다.
        ts = None
        for 시도 in range(3):
            try:
                ts = 목록(cat, 몫)
                break
            except Exception as e:
                쉼 = 8 * (시도 + 1)
                print("  ⚠%s — %s · %d초 쉬고 다시(%d/3)"
                      % (갈래, str(e)[:40], 쉼, 시도 + 1))
                time.sleep(쉼)
        if ts is None:
            print("  ⛔%s — 세 번 다 실패. ★«없다»가 아니라 «못 받았다»다." % 갈래)
            continue
        ms = 메타(ts)
        for m in ms:
            if not m["mime"].startswith("image"):
                continue
            m["갈래"] = 갈래
            m["걸린관문"] = 관문판정(m)
            작품.append(m)
        print("  %-10s %2d점  (%s)" % (갈래, len(ms), cat.replace("Category:", "")))
        time.sleep(1.2)          # ★분류 사이에 한 박자 — 429 를 덜 만난다
        if not a.list:
            # ★분류 하나 끝날 때마다 «바로» 저장한다.
            #   ⛔전에는 끝까지 가야 저장해서, 429 하나에 앞서 모은 것도 날아갔다.
            _저장(작품)

    # ★센다 — 「어느 관문이 몇 건을 잡나」가 곧 갈래별 개입률이다.
    #   ⛔여기서 «기준을 고쳐야 할지»가 드러난다. 0건이면 있으나 마나다(3강).
    from collections import Counter
    c = Counter()
    for x in 작품:
        for g in x["걸린관문"]:
            c[g] += 1
    n전체 = max(1, len(작품))
    print()
    print("  ── 관문별 적중 (전체 %d점) ──" % len(작품))
    for g in ("B1_표시의무위반", "B2_현대물",
              "C1_이름오염", "C2_작가불명", "D2_연도오염"):
        n = c.get(g, 0)
        표 = "  ⛔0건 — 있으나 마나" if n == 0 else ""
        print("    %-16s %3d건  (%4.1f%%)%s" % (g, n, n / n전체 * 100, 표))

    갈래별 = Counter()
    for x in 작품:
        for g in x["걸린관문"]:
            갈래별[CFG["_관문"][g]["갈래"]] += 1
    무사 = sum(1 for x in 작품 if not x["걸린관문"])
    print()
    print("  ── 갈래별로 «사람에게 갈» 건수 ──")
    for 갈래 in ("이미지", "작가", "카탈로그"):
        n = 갈래별.get(갈래, 0)
        print("    %-8s %3d건  (%4.1f%%)" % (갈래, n, n / n전체 * 100))
    print("    %-8s %3d건  (%4.1f%%)  ← 수집 단계 관문을 다 통과"
          % ("무사", 무사, 무사 / n전체 * 100))
    print()
    print("  ★노드9 였다면 라이선스 불명을 전부 버렸다 —"
          " 그게 선택지 ①(전부 막기)였다.")
    print("    여기서는 버리지 않는다. ⇒ 관문이 «사람에게 보낼지»를 가른다.")

    if a.list:
        print()
        for x in 작품[:12]:
            표 = ("·".join(g.split("_")[0] for g in x["걸린관문"])
                  or "무사")
            print("  %-8s %-44s %s"
                  % (x["갈래"], x["제목"].replace("File:", "")[:42], 표))
        print("\n  (--list 라 저장하지 않았습니다)")
        return

    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    p = os.path.join(HERE, "data/corpus.json")
    io.open(p, "w", encoding="utf-8", newline="").write(
        json.dumps({"작품": 작품, "수집": len(작품)},
                   ensure_ascii=False, indent=1))
    print("\n  → data/corpus.json  %d점" % len(작품))


if __name__ == "__main__":
    main()
