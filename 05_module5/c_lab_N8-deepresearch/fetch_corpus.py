# -*- coding: utf-8 -*-
"""코퍼스 수집 — 한국 근대사(1876~1910) 위키백과 클러스터.

강의(노드8)가 요구하는 코퍼스 조건 셋을 그대로 따른다.
  ① 한 질문에 여러 문서가 필요할 것 — 한 문서로 끝나면 나눌 일이 없다
  ② ★문서끼리 «링크»로 이어져 있을 것 — 조사관이 읽고 나서 다음 후보를 찾는 길
  ③ 정답을 셀 수 있을 것  (단, 정답표는 ★쓰지 않는다 — 14강)

★링크가 왜 중요한가 — 조사관은 «읽은 문서의 링크»에서 다음 후보를 만든다.
  링크가 0개인 문서는 «링크를 타고는 절대 못 닿는다». 코디네이터가 카드를 보고
  직접 배정해야만 닿는다. 강의 코퍼스의 «거문도 사건»이 그 자리였다.
  ⇒ 우리 코퍼스에도 그런 문서가 있는지 «세어서» 남긴다.

★★실사고 2026-09-22 — 한 건씩 치다가 429(Too Many Requests)로 두 번 죽었다.
  지수 백오프를 붙여도 또 죽었다. «기다리는 법»을 고치는 게 아니라
  «치는 횟수»를 고쳐야 했다. MediaWiki 는 한 요청에 제목을 여러 개 받는다
  (titles=A|B|C). 34회 → 4회로 줄이니 한 번에 통과했다.
  ⇒ 속도 제한은 «대기»가 아니라 «묶기»로 푼다.
"""
import io
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://ko.wikipedia.org/w/api.php"
UA = "KDT-m5n8-deepresearch/1.0 (study project; contact via github kimjy0977)"
CHUNK = 20          # extracts 는 exlimit 최대 20

SEED = [
    "운요호 사건", "강화도 조약", "조미수호통상조약", "위정척사파",
    "임오군란", "별기군", "통리기무아문",
    "갑신정변", "김옥균", "개화파", "거문도 사건",
    "동학 농민 혁명", "전봉준", "청일 전쟁", "갑오개혁", "군국기무처",
    "을미사변", "명성황후", "단발령", "아관파천", "대한제국",
    "독립협회", "고종 (대한제국)", "흥선대원군",
    "러일 전쟁", "을사조약", "이완용", "헤이그 특사 사건",
    "정미조약", "한일 병합 조약", "안중근", "최익현",
    "을미의병", "애국계몽운동",
]
CACHE = os.path.join(HERE, "data/_cache.json")


def api(params, tries=7):
    params = dict(params, format="json", formatversion="2")
    data = urllib.parse.urlencode(params).encode()      # ★POST — URL 길이 제한 회피
    req = urllib.request.Request(API, data=data,
                                 headers={"User-Agent": UA})
    wait = 2.0
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or i == tries - 1:
                raise
            print("      (%d) %d — %.0f초 쉬고 다시" % (i + 1, e.code, wait))
            time.sleep(wait)
            wait = min(wait * 2, 60)
            req = urllib.request.Request(API, data=data,
                                         headers={"User-Agent": UA})
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(wait)
            wait = min(wait * 2, 60)
            req = urllib.request.Request(API, data=data,
                                         headers={"User-Agent": UA})


def load_cache():
    if os.path.exists(CACHE):
        return json.load(io.open(CACHE, encoding="utf-8"))
    return {"docs": {}, "links": {}}


def save_cache(c):
    io.open(CACHE, "w", encoding="utf-8", newline="").write(
        json.dumps(c, ensure_ascii=False))


def chunks(xs, n):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def fetch_extracts(titles, cache=None):
    """본문은 ★한 건씩 받는다.

    ⛔묶어서 받으려 했는데 안 된다 — MediaWiki 는 exlimit>1 일 때
      «exintro(도입부)» 만 준다. 전문을 받으려면 한 요청에 한 건이다.
      (묶어 보냈더니 첫 건만 오고 나머지가 «0자»로 와서 알았다.)
    ⇒ 대신 ①간격을 두고 ②받는 즉시 캐시에 적어 중간에 죽어도 이어받는다.
    """
    out = {}
    for i, t in enumerate(titles, 1):
        d = api({"action": "query", "prop": "extracts", "explaintext": 1,
                 "redirects": 1, "titles": t})
        pages = d.get("query", {}).get("pages", [])
        body = "" if not pages or pages[0].get("missing") else (pages[0].get("extract") or "")
        name = t if not pages else pages[0].get("title", t)
        out[name] = body
        print("   [%2d/%2d] %-22s %6d자" % (i, len(titles), name, len(body)))
        if cache is not None and len(body) >= 800:
            cache["docs"][name] = body
            save_cache(cache)
        time.sleep(1.5)
    return out


def fetch_links(titles):
    """링크도 묶어서. pllimit=max 라 continue 를 돌려야 한다."""
    out = {t: [] for t in titles}
    for part in chunks(titles, CHUNK):
        cont = {}
        while True:
            d = api(dict({"action": "query", "prop": "links", "pllimit": "max",
                          "plnamespace": 0, "redirects": 1,
                          "titles": "|".join(part)}, **cont))
            for p in d.get("query", {}).get("pages", []):
                if p.get("missing"):
                    continue
                out.setdefault(p["title"], [])
                out[p["title"]] += [l["title"] for l in p.get("links", [])]
            if "continue" in d:
                cont = d["continue"]
                time.sleep(0.8)
                continue
            break
        print("   %d건 링크 수집" % len(part))
        time.sleep(1.0)
    return out


def main():
    cache = load_cache()
    docs = dict(cache["docs"])

    need = [s for s in SEED
            if not any(s.replace(" ", "") in t.replace(" ", "") for t in docs)]
    print("■ 본문 — 이미 %d건 · 더 받을 것 %d건" % (len(docs), len(need)))
    if need:
        got = fetch_extracts(need, cache)
        for t, body in got.items():
            if len(body) < 800:
                print("   건너뜀 %-20s (%d자)" % (t, len(body)))
                continue
            # 각주·같이 보기·외부 링크는 조사관에게 잡음이다 — 잘라 낸다
            body = re.split(
                r"\n==+ *(?:각주|주석|같이 보기|외부 링크|참고 문헌)", body)[0]
            docs[t] = body.strip()
        cache["docs"] = docs
        save_cache(cache)

    titles = sorted(docs)
    print("\n■ 내부 링크 — ★코퍼스 «안»의 문서만 남긴다")
    links = dict(cache["links"])
    need_l = [t for t in titles if t not in links]
    if need_l:
        raw = fetch_links(need_l)
        inside = set(titles)
        for t in need_l:
            links[t] = sorted({x for x in raw.get(t, [])
                               if x in inside and x != t})
        cache["links"] = links
        save_cache(cache)

    links = {t: links.get(t, []) for t in titles}
    zero = [t for t in titles if not links[t]]
    total = sum(len(v) for v in docs.values())
    n_links = sum(len(v) for v in links.values())

    io.open(os.path.join(HERE, "data/corpus.json"), "w",
            encoding="utf-8", newline="").write(
        json.dumps({"docs": docs, "links": links}, ensure_ascii=False, indent=1))

    print("\n■ 요약")
    print("   문서 %d건 · %d자 (약 %d 토큰)" % (len(docs), total, total // 2))
    print("   내부 링크 %d개 · 문서당 평균 %.1f"
          % (n_links, n_links / max(1, len(docs))))
    big = max(docs.items(), key=lambda kv: len(kv[1]))
    print("   가장 긴 문서 «%s» %d자" % (big[0], len(big[1])))
    print("   ★링크 0개(아무도 안 거는 문서) %d건 — %s"
          % (len(zero), ", ".join(zero) if zero else "없음"))
    print("\n   ⇒ 링크 0개 문서는 «링크를 타고는 못 닿는다».")
    print("     코디네이터가 카드를 보고 «직접 배정»해야만 닿는다 (강의 9강).")


main()
