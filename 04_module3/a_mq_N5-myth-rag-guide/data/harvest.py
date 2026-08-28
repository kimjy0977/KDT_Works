# -*- coding: utf-8 -*-
"""
MYTH GALLERY 청크 수집기 — 모듈3 노드5 메인 퀘스트

하는 일
  1) 신화별 작품 목록에서 작품 주소를 모은다
  2) 각 작품 페이지를 실제로 받아본다 (200 을 받은 것만 남긴다)
  3) 페이지에 이미 나뉘어 있는 섹션(메타·해설·신화배경·감상포인트)을 그대로 청크로 만든다
  4) 청크마다 url 을 넣는다. url 이 비면 버린다.

원칙
  - 열어 보지 못한 주소는 만들지 않는다. 모든 url 은 이 스크립트가 200 을 확인한 것이다.
  - 신화 코드만 바꾸면 6종 전부 돈다. 확장 시 구조를 다시 짜지 않는다.

실행: python harvest.py
      python harvest.py --myth norse --limit 20
"""
import argparse, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

BASE = "https://myth-gallery.vercel.app"
MYTHS = {   # 신화 코드 -> (경로, 표시 이름).  코드만 늘리면 6종 전부 돈다
    "greek":   ("greek",   "greco-roman"),
    "norse":   ("norse",   "norse"),
    "egypt":   ("egypt",   "egyptian"),
    "meso":    ("meso",    "mesopotamian"),
    "hindu":   ("hindu",   "hindu"),
    "chinese": ("chinese", "chinese"),
}
MIN_CHUNK, MAX_CHUNK = 120, 600
UA = {"User-Agent": "KDT-study-harvester/1.0 (aiffel kdt coursework)"}


# ------------------------------ 받기 ------------------------------
def fetch(url, retry=2):
    """실제로 받아본다. 성공하면 (200, 본문), 실패하면 (코드, None)."""
    for i in range(retry + 1):
        try:
            with urlopen(Request(url, headers=UA), timeout=20) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except HTTPError as e:
            return e.code, None
        except URLError:
            if i == retry:
                return 0, None
            time.sleep(1.2 * (i + 1))
    return 0, None


# ------------------------------ 파싱 ------------------------------
def strip_tags(s):
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    for a, b in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                 ("&quot;", '"'), ("&#39;", "'"), ("&nbsp;", " ")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def parse_work(html, url, slug, myth_label):
    """작품 페이지 하나를 구조화한다. 페이지가 이미 섹션으로 나뉘어 있어 그대로 쓴다."""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    title = strip_tags(m.group(1)) if m else ""

    m = re.search(r'<p class="orig"[^>]*>(.*?)</p>', html, re.S)
    title_en = strip_tags(m.group(1)) if m else ""

    meta = {}
    for dt, dd in re.findall(r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", html, re.S):
        k, v = strip_tags(dt), strip_tags(dd)
        if k and v:
            meta[k] = v

    sections = {}
    for body in re.findall(r'<section class="prose[^"]*"[^>]*>(.*?)</section>', html, re.S):
        hm = re.search(r"<h2[^>]*>(.*?)</h2>", body, re.S)
        if not hm:
            continue
        head = strip_tags(hm.group(1))
        text = strip_tags(re.sub(r"(?s)<h2[^>]*>.*?</h2>", " ", body))
        if head and text:
            sections[head] = text

    people = [strip_tags(t) for t in re.findall(
        r'<a class="ent" href="/ko/[^/]+/people/[^"]*"[^>]*>(.*?)</a>', html, re.S)]

    return {
        "slug": slug, "url": url, "title": title, "title_en": title_en,
        "mythology": myth_label, "meta": meta, "sections": sections,
        "people": people,
        "artist": meta.get("작가", ""), "era": meta.get("사조", ""),
    }


# ------------------------------ 선정 ------------------------------
NEEDED = ("해설", "신화 배경", "감상 포인트")


def pick(works, limit):
    """선정 기준 (PRD 3-2)
       1) 서사가 있는 장면화 -- 등장 인물이 2명 이상
       2) 해설/신화 배경/감상 포인트 세 항목이 다 채워진 작품
       3) 서로 다른 이야기 -- 같은 인물 조합/같은 작가를 반복해 채우지 않는다
    """
    ok = [w for w in works
          if all(w["sections"].get(k) for k in NEEDED) and len(w["people"]) >= 2]
    ok.sort(key=lambda w: -sum(len(v) for v in w["sections"].values()))

    chosen, seen_story, seen_artist = [], set(), {}
    for w in ok:
        story = frozenset(w["people"][:3])          # 주요 등장인물 조합 = 이야기 서명
        if story in seen_story:
            continue
        if seen_artist.get(w["artist"], 0) >= 2:    # 한 작가가 3점 이상 차지하지 않게
            continue
        chosen.append(w)
        seen_story.add(story)
        seen_artist[w["artist"]] = seen_artist.get(w["artist"], 0) + 1
        if len(chosen) >= limit:
            break
    return chosen


# ------------------------------ 청킹 ------------------------------
SEC_KEY = {"해설": "description", "신화 배경": "myth", "감상 포인트": "insight"}


def split_long(text):
    """MAX_CHUNK 를 넘으면 문장 경계에서 나눈다. 문장 중간을 자르지 않는다."""
    if len(text) <= MAX_CHUNK:
        return [text]
    parts, buf = [], ""
    for sent in re.split(r"(?<=[.!?。])\s+", text):
        if buf and len(buf) + len(sent) + 1 > MAX_CHUNK:
            parts.append(buf.strip())
            buf = sent
        else:
            buf = (buf + " " + sent).strip()
    if buf:
        parts.append(buf.strip())
    return parts


def meta_sentence(w):
    """메타데이터를 검색 가능한 한 문장으로 만든다 (표는 임베딩이 잘 못 읽는다)."""
    m = w["meta"]
    head = "「" + w["title"] + "」"
    if w["title_en"]:
        head += "(원제 " + w["title_en"] + ")"
    bits = [head]
    if m.get("작가"):     bits.append(m["작가"] + "의 작품")
    if m.get("제작연도"): bits.append("제작 시기는 " + m["제작연도"])
    if m.get("매체"):     bits.append("매체는 " + m["매체"])
    if m.get("크기"):     bits.append("크기는 " + m["크기"])
    if m.get("소장처"):   bits.append(m["소장처"] + "에 소장되어 있다")
    if m.get("사조"):     bits.append("사조는 " + m["사조"])
    if w["people"]:       bits.append("등장 인물은 " + ", ".join(dict.fromkeys(w["people"])))
    return ". ".join(bits) + "."


def build_chunks(w):
    out, pending = [], ""
    ordered = [("meta", meta_sentence(w))] + \
              [(SEC_KEY[k], w["sections"][k]) for k in NEEDED if w["sections"].get(k)]

    for sec, text in ordered:
        text = (pending + " " + text).strip() if pending else text
        if len(text) < MIN_CHUNK:      # 너무 짧으면 다음 섹션에 붙인다 (조각난 청크 방지)
            pending = text
            continue
        pending = ""
        for i, piece in enumerate(split_long(text)):
            out.append({
                "id": w["slug"] + "#" + sec + ("-%d" % (i + 1) if i else ""),
                "text": piece,
                "url": w["url"],
                "title": w["title"],
                "artist": w["artist"],
                "mythology": w["mythology"],
                "section": sec,
            })
    if pending and out:                # 남은 꼬리는 마지막 청크에 붙인다
        out[-1]["text"] += " " + pending
    return out


# ------------------------------ 실행 ------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--myth", default="greek", choices=list(MYTHS))
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--scan", type=int, default=120, help="후보로 실제 받아볼 작품 수")
    ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
    a = ap.parse_args()

    try:                                   # 콘솔이 cp949 여도 한글이 깨지지 않게
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    path, label = MYTHS[a.myth]
    log = []

    def say(s):
        log.append(s)
        try:
            print(s, flush=True)
        except UnicodeEncodeError:   # 윈도우 cp949 콘솔
            sys.stdout.write(s.encode("ascii", "backslashreplace").decode("ascii") + chr(10))

    say("[1] 목록 받기 -- %s/ko/%s/works" % (BASE, path))
    st, html = fetch(BASE + "/ko/" + path + "/works")
    if st != 200:
        sys.exit("목록을 받지 못했다 (HTTP %s)." % st)
    slugs = sorted(set(re.findall(r"/ko/%s/works/(%s-[a-z0-9]+)" % (path, path), html)))
    say("    작품 주소 %d개 발견" % len(slugs))

    cand = slugs[: a.scan]
    say("[2] 후보 %d점 실제로 받아보기 (200 인 것만 남긴다)" % len(cand))

    def grab(slug):
        url = BASE + "/ko/" + path + "/works/" + slug
        st, h = fetch(url)
        if st != 200 or not h:
            return None, (slug, st)
        return parse_work(h, url, slug, label), (slug, 200)

    works, status = [], []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for w, s in ex.map(grab, cand):
            status.append(s)
            if w:
                works.append(w)
    bad = [s for s in status if s[1] != 200]
    say("    200: %d점 / 실패: %d점 %s" % (len(works), len(bad), bad[:5] if bad else ""))

    say("[3] 선정 -- 세 섹션이 다 있고 등장인물 2명 이상, 이야기/작가 중복 제외")
    chosen = pick(works, a.limit)
    say("    %d점 선정" % len(chosen))
    for i, w in enumerate(chosen, 1):
        say("    %2d. %s -- %s" % (i, w["title"], w["artist"] or "작가 미상"))

    say("[4] 청크 만들기")
    chunks = []
    for w in chosen:
        chunks += build_chunks(w)

    dropped = [c for c in chunks if not c["url"]]   # url 없는 청크는 색인에 넣지 않는다
    chunks = [c for c in chunks if c["url"]]
    lens = [len(c["text"]) for c in chunks]
    say("    청크 %d개 (버림 %d개)" % (len(chunks), len(dropped)))
    say("    길이 최소 %d / 평균 %d / 최대 %d" % (min(lens), sum(lens) // len(lens), max(lens)))

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "chunks.json"), "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=1)
    with open(os.path.join(a.out, "works.json"), "w", encoding="utf-8") as f:
        json.dump([{k: w[k] for k in ("slug", "url", "title", "artist", "era", "people")}
                   for w in chosen], f, ensure_ascii=False, indent=1)
    with open(os.path.join(a.out, "harvest-report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    say("[5] 저장 완료 -- chunks.json / works.json / harvest-report.txt")


if __name__ == "__main__":
    main()
