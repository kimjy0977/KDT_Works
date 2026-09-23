# -*- coding: utf-8 -*-
"""코퍼스 수집 — 세계 신화 위키백과 클러스터 (두 축이 가로지르는 코퍼스).

노드8(한국 근대사)에서 쓴 수집기를 주제만 바꿔 다시 쓴다.
강의가 요구하는 코퍼스 조건 셋은 그대로다.
  ① 한 질문에 여러 문서가 필요할 것
  ② ★문서끼리 «링크»로 이어져 있을 것
  ③ 정답을 셀 수 있을 것  (단, 정답표는 ★쓰지 않는다)

★노드8 코퍼스와 «다르게» 고른 점 — 축이 둘이다
  근대사는 «시간»이라는 축 하나였다. 절을 나누면 대체로 시기가 갈렸다.
  신화는 «주제»(창조·홍수·저승·영웅·트릭스터)와 «문화권»이 가로지른다.
    절을 주제로 나누면   → 조사관이 문화권을 가로질러 읽어야 한다
    절을 문화권으로 나누면 → 주제를 가로질러 읽어야 한다
  ⇒ 같은 예산으로 «나누는 방식»을 바꿔 가며 견줄 수 있다.
    노드8 에서 못 한 `--full`(폭 vs 깊이)이 여기서는 의미를 갖는다.

★MYTH 프로젝트 자료를 안 쓴 이유 (디렉터에게 보고한 판단)
  그 자료는 «수집된 것»이 아니라 «쓰인 것»이다 — 참고문헌·다국어 인용·
  비교 항목까지 이미 정리돼 있어서, ★에이전트가 할 일이 이미 끝나 있다.
  노드8 의 제일 큰 결과가 「혼자 21.7% vs 팀 72.3%」였는데
  자료가 정리돼 있으면 혼자서도 잘한다 — 그 대조가 죽는다.
  (그리고 타 프로젝트 자산을 공개 레포에 싣게 된다 — 하네스 §B-2)
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
UA = "KDT-m5-myth-research/1.0 (study project; contact via github kimjy0977)"
CHUNK = 20          # extracts 는 exlimit 최대 20

SEED = [ "창조신화", "홍수 신화", "영웅", "트릭스터", "저승", "비교신화학", "신화", "원형 (심리학)",
    "영웅의 여정", "그리스 신화", "로마 신화", "북유럽 신화", "이집트 신화", "메소포타미아 신화", "일본 신화",
    "중국 신화", "한국 신화", "힌두 신화", "켈트 신화", "마야 신화", "길가메시 서사시", "길가메시",
    "에누마 엘리시", "대홍수", "노아의 방주", "데우칼리온", "하데스", "오시리스", "이자나미", "이자나기",
    "바리데기", "단군", "주몽", "헤라클레스", "오디세이아", "로키", "헤르메스", "프로메테우스", "라그나로크",
    "오딘", "이슈타르", "페르세포네", "조지프 캠벨", "제임스 조지 프레이저", "황금가지", "클로드 레비스트로스",
    "카를 융",

    # ── ★probe_titles.py 로 «찾아서» 더한 것 ────────────────────
    #   한국어 위키는 「주제」 문서가 얇고(창조 신화 2천자·트릭스터 2천자)
    #   내용은 「문화권·개별 신·인물」 문서에 있다. 추측 말고 API 로 쟀다.
    "대홍수 신화", "오시리스 신화", "고대 이집트 종교", "노르드 신화", "영웅", "호루스", "게르만 신화의 신 목록",
    "융의 원형", "분석심리학", "이집트 창조 신화", "수메르 창조신화", "창조 신화", "인도 신화", "바리공주",
    "명계", "저승사자", "동명성왕", "내세",
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
