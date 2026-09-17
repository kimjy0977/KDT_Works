# -*- coding: utf-8 -*-
"""★조회 도구 — 노드4 의 「어드민 조회」에 대응한다.

모두몰은 주문·상품 데이터가 «주어졌다». 내 도메인은 내가 모았다:
  store/knowledge.json   기사 72건 — 전부 [신설]. 72시간 이내
  facts_base.json        기준 사실 카드 25장 — [정설]·[추정]·[논쟁]

★어제 배운 것을 «처음부터» 넣는다
  1. 검색 점수는 «가중»한다 — 완전 일치 1.0 · 부분 0.5
     (어제 search_product 는 「한 글자만 겹쳐도 1점」이라 동점이 났다)
  2. 단어 «경계»를 본다 — 오늘 아침 star 가 starfish 에 매치돼 라우트가 틀렸다
  3. 동점이면 «애매»로 돌려준다 — 고르지 않고 되묻게 한다
"""
import json
import re
from pathlib import Path

from ko_en import expand_query, unmapped

HERE = Path(__file__).parent

_KB = json.loads((HERE / "store/knowledge.json").read_text(encoding="utf-8"))
ARTICLES = _KB["articles"]
FACTS = json.loads((HERE / "facts_base.json").read_text(encoding="utf-8"))["facts"]

_STOP = {"무엇", "뭐", "뭘", "어떻게", "왜", "언제", "어디", "누가", "인가요", "있나요",
         "하나요", "되나요", "건가요", "나요", "가요", "요", "은", "는", "이", "가",
         "을", "를", "의", "에", "에서", "로", "으로", "와", "과", "도", "만"}


def _toks(s):
    """한글·영문·숫자 토큰. 조사·의문사는 뺀다."""
    raw = re.findall(r"[A-Za-z]+|[가-힣]+|\d+", s or "")
    out = []
    for t in raw:
        for st in sorted(_STOP, key=len, reverse=True):
            if t.endswith(st) and len(t) > len(st):
                t = t[: -len(st)]
                break
        if len(t) >= 2 and t not in _STOP:
            out.append(t)
    return out


def _score(qt, text, weights=None):
    """★가중 점수 — 완전 일치 1.0 · 부분 포함 0.5. 분모는 질의어 수.

    weights: 토큰별 «신뢰도». 사전으로 «불린» 확장어는 원본보다 낮게 준다.
      실측: 「달 탐사」의 확장어 `mission` 이 NASA 기사 대부분에 있어
            「NFL Fans in Baltimore」까지 걸렸다(42건).
      ⇒ 확장어는 «추측»이므로 원본과 같은 표를 주면 안 된다.
    """
    if not qt:
        return 0.0
    tt = _toks(text)
    got = tot = 0.0
    for i, t in enumerate(qt):
        w = 1.0 if weights is None else weights[i]
        tot += w
        if t in tt:
            got += w
        elif any(t in x or x in t for x in tt):
            got += w * 0.5
    return got / tot if tot else 0.0


# ──────────────────────────────────────────────────────────
def get_fact(topic: str) -> dict:
    """기준 사실 카드를 찾는다 — [정설]·[추정]·[논쟁] 은 여기 있다.

    Args:
        topic: 찾을 주제어. 예) "공룡 멸종", "광년", "탄소 연대측정"
    """
    qt = _toks(topic)
    hits = []
    for f in FACTS:
        s = max(_score(qt, f["topic"]), _score(qt, f["claim"]) * 0.8)
        if s > 0:
            hits.append((s, f))
    hits.sort(key=lambda x: -x[0])
    if not hits:
        return {"found": False, "note": "기준 사실 카드에 없습니다. 기사 검색을 쓰십시오."}
    top = [f for s, f in hits if abs(s - hits[0][0]) < 1e-9]
    if len(top) > 1:
        return {"found": False, "ambiguous": True,
                "candidates": [f["topic"] for f in top[:4]],
                "note": "주제가 여럿입니다. 어느 것인지 확인하십시오."}
    f = top[0]
    return {"found": True, "id": f["id"], "topic": f["topic"], "claim": f["claim"],
            "value": f.get("value"), "error": f.get("error"),
            "certainty": f["certainty"], "basis": f.get("basis"),
            "caution": f.get("caution")}


def search_article(query: str) -> dict:
    """최근 발표된 기사를 찾는다 — 여기서 나오는 것은 «전부 [신설]»이다.

    Args:
        query: 찾을 말. 예) "폼페이 발굴", "달 탐사선"
    """
    # ★지식원이 영어라 한국어 질의는 «그대로는» 한 건도 안 걸린다(실측).
    #   사전으로 영어 대응어를 «더한다». 원본 토큰은 지우지 않는다.
    qt0 = _toks(query)
    ens, hit_keys = expand_query(query)
    hits = []
    for a in ARTICLES:
        text = a["title"] + " " + a["summary"]
        low = text.lower()
        # 축 1 — 한국어 토큰 (지식원에 한글이 섞이면 여기서 잡힌다)
        s_ko = _score(qt0, text) if qt0 else 0.0
        # 축 2 — 영어 대응어를 «원문 문자열»에서 찾는다 (공백 포함 그대로)
        n_en = sum(1 for e in ens if e in low)
        s_en = (n_en / len(ens)) ** 0.5 if ens else 0.0   # 하나만 맞아도 어느 정도 인정
        s = max(s_ko, s_en * 0.85)
        if s > 0.30:
            hits.append((s, a))
    hits.sort(key=lambda x: -x[0])
    miss = unmapped(qt0, hit_keys)
    return {"query": query, "count": len(hits),
            "window_hours": _KB["window_hours"],
            "unmapped_terms": miss or None,
            "results": [{"id": a["id"], "title": a["title"], "source": a["source"],
                         "published": a["published"], "certainty": a["certainty"],
                         "route": a["route"], "thin": a.get("thin", False),
                         "score": round(s, 2)}
                        for s, a in hits[:5]],
            "note": ("검색 결과는 최근 %d시간 이내 발표입니다. "
                     "전부 [신설]이며 아직 검증되지 않았습니다." % _KB["window_hours"])
            if hits else "해당 기간에 관련 발표가 없습니다."}


def get_article(article_id: str) -> dict:
    """기사 본문 요약과 출처를 가져온다.

    Args:
        article_id: search_article 이 돌려준 id. 예) "A0012"
    """
    for a in ARTICLES:
        if a["id"] == article_id:
            return {"found": True, "id": a["id"], "title": a["title"],
                    "summary": a["summary"], "source": a["source"],
                    "link": a["link"], "published": a["published"],
                    "certainty": a["certainty"],
                    "thin": a.get("thin", False),
                    "caution": "★[신설]입니다. 「밝혀졌다」가 아니라 「발표됐다」로 씁니다."}
    return {"found": False}


def get_term(term: str) -> dict:
    """용어·방법의 정의와 «한계»를 가져온다.

    Args:
        term: 용어. 예) "방사성 탄소 연대측정", "적색편이", "프리프린트"
    """
    qt = _toks(term)
    hits = [(max(_score(qt, f["topic"]), _score(qt, f["claim"]) * 0.8), f)
            for f in FACTS if f["route"] == "CONCEPT"]
    hits = [(s, f) for s, f in hits if s > 0]
    hits.sort(key=lambda x: -x[0])
    if not hits:
        return {"found": False, "note": "용어 사전에 없습니다."}
    f = hits[0][1]
    return {"found": True, "term": f["topic"], "definition": f["claim"],
            "certainty": f["certainty"], "basis": f.get("basis"),
            "limit": f.get("caution"),
            "note": "★정의만 말하지 말고 «한계»를 함께 말하십시오."}


def list_recent(route: str, limit: int = 5) -> dict:
    """특정 분야의 최근 발표를 훑는다.

    Args:
        route: SPACE · ARCHAEO · PALEO 중 하나
        limit: 최대 건수
    """
    sel = [a for a in ARTICLES if a["route"] == route.upper()]
    sel.sort(key=lambda a: a["published"] or "", reverse=True)
    return {"route": route.upper(), "count": len(sel),
            "window_hours": _KB["window_hours"],
            "results": [{"id": a["id"], "title": a["title"], "source": a["source"],
                         "published": a["published"], "certainty": a["certainty"]}
                        for a in sel[:limit]],
            "note": "전부 [신설]입니다. 아직 검증되지 않았습니다."}


TOOLS = {f.__name__: f for f in
         (get_fact, search_article, get_article, get_term, list_recent)}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("=== 도구 %d개 · 기사 %d건 · 사실카드 %d장 ==="
          % (len(TOOLS), len(ARTICLES), len(FACTS)))
    print()
    for q in ("공룡 멸종", "광년", "티라노사우루스 깃털"):
        r = get_fact(q)
        print("get_fact(%r)" % q)
        print("   → %s" % (("[%s] %s" % (r["certainty"], r["claim"][:56]))
                           if r.get("found") else r.get("note", r)))
    print()
    for q in ("달 탐사", "폼페이", "화석"):
        r = search_article(q)
        print("search_article(%r) → %d건" % (q, r["count"]))
        for x in r["results"][:2]:
            print("   %.2f  %s" % (x["score"], x["title"][:62]))
    print()
    r = get_term("방사성 탄소 연대측정")
    print("get_term → %s" % (r.get("definition", r.get("note"))))
    print("   한계: %s" % r.get("limit", "—"))
