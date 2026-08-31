# -*- coding: utf-8 -*-
"""화면 목록 생성기 — app/src/works.ts 를 만든다 (모듈3 노드5)

왜 생성기인가.
  works.ts 는 «화면에 보여 줄 대표 작품»과 «챗봇이 아는 범위(CORPUS·MYTHS)»를 담는다.
  이 숫자는 벡터스토어가 바뀔 때마다 따라와야 하는데, 손으로 고치면 안 따라온다.
  실제로 자료를 43점→982점으로 늘렸을 때 화면은 «43점»을 계속 말하고 있었고,
  힌두·중국·메소포타미아는 전부 실렸는데 «수록 0점»이라고 안내하고 있었다.
  수록됐는데 0점이라고 하면 방문자는 물어보지도 않는다.

입력
  data/chunks.json          제목·작가·URL (harvest.py 산출)
  myth-docs-index.json      실제 벡터스토어에 든 양 (build-vectors.mjs 산출)
출력
  app/src/works.ts

선정 규칙
  신화당 대표 12점. 982장을 한 화면에 깔 수 없다.
  · 조각이 많은 작품 우선 — 물어볼 거리가 많은 작품이 대표로 적합하다
  · 같은 작가가 한 신화에서 3점 이상 차지하지 않게 (한 사람 전시가 되지 않게)
  · 썸네일이 실제로 200 인 것만 (열어 보지 못한 주소를 화면에 쓰지 않는다 — 3강)

실행: python tools/build-works.py
"""
import io, json, os, re, sys
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
CHUNKS = os.path.join(ROOT, "data", "chunks.json")
INDEX = os.path.join(ROOT, "myth-docs-index.json")
OUT = os.path.join(ROOT, "app", "src", "works.ts")

PER_MYTH = 12
MAX_PER_ARTIST = 2          # 한 작가가 한 신화에서 3점 이상 차지하지 않게
THUMB = "https://myth-gallery.vercel.app/img/works/thumb/{}.webp"
UA = {"User-Agent": "KDT-works-builder/1.0 (aiffel kdt coursework)"}

MYTH_NAME = {
    "greek": "그리스·로마", "norse": "북유럽", "egypt": "이집트",
    "meso": "메소포타미아", "hindu": "힌두", "chinese": "중국",
}


def head_ok(url):
    """실제로 받아본다. 200 이 아니면 화면에 쓰지 않는다."""
    try:
        with urlopen(Request(url, headers=UA), timeout=15) as r:
            return r.status == 200
    except (HTTPError, URLError, OSError):
        return False


def era_of(meta_text):
    """meta 청크 본문에서 사조를 꺼낸다 — «사조는 X.» 형태로 들어 있다."""
    m = re.search(r"사조는\s+(.+?)(?:\.\s|\.$)", meta_text)
    return m.group(1).strip() if m else ""


def main():
    chunks = json.load(io.open(CHUNKS, encoding="utf-8"))
    index = json.load(io.open(INDEX, encoding="utf-8"))

    # 작품 단위로 모은다
    works = {}
    for c in chunks:
        slug = c["id"].split("#")[0]
        w = works.setdefault(slug, {
            "slug": slug, "url": c["url"], "title": c.get("title", ""),
            "artist": c.get("artist", ""), "code": slug.split("-")[0],
            "chunks": 0, "era": "",
        })
        w["chunks"] += 1
        if c["section"] == "meta" and not w["era"]:
            w["era"] = era_of(c["text"])
    print(f"작품 {len(works)}점 / 청크 {len(chunks)}개")

    # 신화별로 후보를 고른다 (썸네일 확인 전)
    picked, cand = {}, {}
    for w in works.values():
        cand.setdefault(w["code"], []).append(w)
    for code, lst in cand.items():
        lst.sort(key=lambda w: (-w["chunks"], w["title"]))

    # 썸네일 확인은 느리므로 필요한 만큼만, 병렬로
    for code, lst in cand.items():
        chosen, by_artist = [], {}
        pool = lst[: PER_MYTH * 4]                      # 넉넉히 뽑아 확인
        with ThreadPoolExecutor(max_workers=8) as ex:
            oks = list(ex.map(lambda w: head_ok(THUMB.format(w["slug"])), pool))
        for w, ok in zip(pool, oks):
            if not ok:
                continue                                 # 썸네일 없는 작품은 화면에 안 싣는다
            a = w["artist"] or "(미상)"
            if by_artist.get(a, 0) >= MAX_PER_ARTIST:
                continue
            chosen.append(w)
            by_artist[a] = by_artist.get(a, 0) + 1
            if len(chosen) >= PER_MYTH:
                break
        picked[code] = chosen
        print(f"  {code:<8} 후보 {len(lst):>4} → 확인 {len(pool):>3} → 선정 {len(chosen):>2}")

    # 화면 순서 = 벡터스토어가 큰 신화부터 (index 의 shards 순서를 따른다)
    order = [s["myth"] for s in index["shards"]]
    flat = [w for code in order for w in picked.get(code, [])]

    myths = [{"name": MYTH_NAME.get(s["myth"], s["myth"]), "code": s["myth"],
              "works": s["works"], "covered": s["works"]} for s in index["shards"]]
    corpus = {"works": sum(s["works"] for s in index["shards"]),
              "chunks": index["built"],
              "archive": sum(s["works"] for s in index["shards"])}

    # ── 출력 ────────────────────────────────────────────────────────────
    L = []
    L.append("// 안내 화면이 쓰는 목록. ⚠️ **손으로 고치지 말 것** — `python tools/build-works.py` 로 만든다.")
    L.append("//    입력 = data/chunks.json + myth-docs-index.json. 벡터스토어가 바뀌면 다시 돌린다.")
    L.append("// ⚠️ 여기 실린 것은 **화면에 보여 줄 대표 작품**이지 챗봇이 아는 범위가 아니다.")
    L.append("//    챗봇이 아는 범위 = myth-docs-*.json (아래 CORPUS).")
    L.append("")
    L.append("export type Work = {")
    L.append("  slug: string; url: string; title: string;")
    L.append("  artist: string; era: string; chunks: number; myth: string; code: string;")
    L.append("};")
    L.append("")
    L.append("export const THUMB = (slug: string) =>")
    L.append("  `https://myth-gallery.vercel.app/img/works/thumb/${slug}.webp`;")
    L.append("")
    L.append("export const WORKS: Work[] = [")
    for w in flat:
        esc = lambda s: (s or "").replace("\\", "\\\\").replace('"', '\\"')
        L.append("  {")
        L.append(f'    slug: "{esc(w["slug"])}",')
        L.append(f'    url: "{esc(w["url"])}",')
        L.append(f'    title: "{esc(w["title"])}",')
        L.append(f'    artist: "{esc(w["artist"])}",')
        L.append(f'    era: "{esc(w["era"])}",')
        L.append(f'    chunks: {w["chunks"]},')
        L.append(f'    myth: "{esc(MYTH_NAME.get(w["code"], w["code"]))}",')
        L.append(f'    code: "{esc(w["code"])}",')
        L.append("  },")
    L.append("];")
    L.append("")
    L.append("/** 아카이브 전체와 그중 챗봇이 아는 만큼 — 화면 문구가 이 숫자를 쓴다 */")
    L.append("export const MYTHS = [")
    for m in myths:
        L.append(f'  {{ name: "{m["name"]}", code: "{m["code"]}", '
                 f'works: {m["works"]}, covered: {m["covered"]} }},')
    L.append("];")
    L.append("")
    L.append("/** 벡터스토어에 실제로 든 양 — 화면 문구가 이 숫자를 쓴다 */")
    L.append(f'export const CORPUS = {{ works: {corpus["works"]}, '
             f'chunks: {corpus["chunks"]}, archive: {corpus["archive"]} }};')
    L.append("")
    io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L))

    print(f"\n저장 — {OUT}")
    print(f"  WORKS {len(flat)}점 (신화 {len(picked)}종)")
    print(f"  CORPUS {corpus}")


if __name__ == "__main__":
    main()
