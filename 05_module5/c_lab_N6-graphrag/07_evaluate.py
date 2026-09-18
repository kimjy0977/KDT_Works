# -*- coding: utf-8 -*-
"""★14강 — 골든셋 15문항 채점. 그리고 실패를 «색인·검색·생성»으로 가른다.

노드가 시키는 것: *"골든셋으로 채점하고, 실패 원인을 색인·검색·생성으로 갈라
무엇을 고쳐야 하는지 숫자로 지목합니다."*

★왜 «갈라야» 하나 — 「70점」만 알면 무엇을 고칠지 모른다.
  같은 실패라도 고칠 자리가 다르다.

    색인 실패   정답 삼중항이 «그래프에 없다»       → 8·9강(추출·보강)을 고친다
    검색 실패   그래프엔 있는데 «근거로 안 왔다»    → 12강(탐색)을 고친다
    생성 실패   근거엔 왔는데 «답에 안 썼다»        → 프롬프트·모델을 고친다

  세 자리는 서로 다른 사람이 고친다. 뭉뚱그리면 엉뚱한 데를 고친다.

    python 07_evaluate.py
"""
import collections
import io
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
GOLD = os.path.join(HERE, "data", "cinephile_goldenset.json")
sys.path.insert(0, HERE)
from importlib import import_module           # noqa: E402
_agent = import_module("06_agent")
key = _agent.key

EXPECT = {"단순": "local", "추천": "path", "전역": "global"}

# reference 에서 «채점할 말»을 뽑는다 — 한국어 조사·군더더기를 걷어낸다.
_STOP = {"등", "및", "그리고", "다른", "작품", "영화", "감독", "배우", "수상",
         "출연", "중심", "조합", "있다", "없다", "이", "그", "저"}


def keywords(ref):
    """정답 문자열에서 «고유명사에 가까운» 조각만 남긴다.

    ★1차 채점이 틀렸다 — 전역-15 는 답을 «정확히» 했는데 17% 로 찍혔다.
      reference 가 「봉준호–송강호, 박찬욱–송강호/최민식 …」인데
      en dash(–) 로 안 쪼개서 「봉준호–송강호」를 통째로 찾았고,
      답변은 「봉준호 감독과 송강호 배우가」라 문자열이 안 맞았다.
      ⇒ 점수를 올리려는 수정이 아니라 «잘못 재던 자»를 고치는 것이다.
    """
    parts = re.split(r"[,·/()–—~]|\s·\s|\s및\s|\s등\s", ref or "")
    out = []
    for p in parts:
        p = p.strip()
        # 「…중심의 저예산 예술영화군」 같은 서술은 앞의 «이름»만 남긴다
        p = re.sub(r"\s*(중심의|중심으로).*$", "", p)
        p = re.sub(r"(의|는|은|이|가|을|를|과|와|에서|으로|로)$", "", p)
        p = re.sub(r"\s*(감독|배우|본인도|등)$", "", p).strip()
        if len(p) >= 2 and p not in _STOP and not p.isdigit():
            out.append(p)
    # 중복 제거 (「송강호」가 여러 쌍에 나온다)
    seen, uniq = set(), []
    for p in out:
        k = key(p)
        if k in seen:
            continue
        seen.add(k)
        uniq.append(p)
    return uniq[:12]


def main():
    gold = json.load(io.open(GOLD, encoding="utf-8"))
    kb = _agent.KB()
    app = _agent.build()

    gkeys = {(key(t["s"]), t["r"], key(t["o"])) for t in kb.triples}

    rows = []
    route_ok = ans_ok = 0
    cause = collections.Counter()
    for it in gold["items"]:
        q, kind = it["user_input"], it["kind"]
        s = app.invoke({"q": q})
        got_route = s.get("route")
        ok_route = (got_route == EXPECT[kind])
        route_ok += ok_route

        ans = s.get("answer") or ""
        ctx = s.get("context") or ""
        kws = keywords(it.get("reference") or "")
        hit = [k for k in kws if key(k) in key(ans)]
        score = len(hit) / len(kws) if kws else 0.0
        ok_ans = score >= 0.4          # 정답 조각의 4할 이상이 답에 있으면 통과
        ans_ok += ok_ans

        # ── ★실패 원인 가르기 ────────────────────────────
        why = ""
        if not ok_ans:
            want = it.get("reference_contexts") or []
            missing_idx = [w for w in want
                           if (key(w[0]), w[1], key(w[2])) not in gkeys]
            in_ctx = [k for k in kws if key(k) in key(ctx)]
            if want and missing_idx:
                why = "색인"          # 그래프에 아예 없다
            elif not in_ctx:
                why = "검색"          # 그래프엔 있는데 근거로 안 왔다
            else:
                why = "생성"          # 근거엔 있는데 답에 안 썼다
            cause[why] += 1

        rows.append((it["id"], kind, got_route, ok_route, score, ok_ans, why, hit, kws))

    n = len(rows)
    print("=" * 74)
    print("14강 골든셋 채점 — %d문항" % n)
    print("=" * 74)
    for rid, kind, route, okr, sc, oka, why, hit, kws in rows:
        print("%-8s %-4s 경로 %-6s %s   답변 %3.0f%% %s %s"
              % (rid, kind, route, "✅" if okr else "❌(기대 %s)" % EXPECT[kind],
                 sc * 100, "✅" if oka else "❌", ("← %s 실패" % why) if why else ""))
        if not oka:
            miss = [k for k in kws if k not in hit]
            print("         못 담은 것: %s" % " · ".join(miss[:6]))
    print("-" * 74)
    print("  경로 적절성  %2d/%d = %5.1f%%" % (route_ok, n, route_ok / n * 100))
    print("  답변 적절성  %2d/%d = %5.1f%%" % (ans_ok, n, ans_ok / n * 100))
    if cause:
        print()
        print("  ★실패 %d건의 원인:" % sum(cause.values()))
        for w in ("색인", "검색", "생성"):
            if cause[w]:
                print("     %s %d건" % (w, cause[w]))
    print("=" * 74)
    print()
    print("※ 7강 BM25 베이스라인은 «문서를 찾아왔는가»(Recall@5)를 쟀다 — 단순 86.7% · 추천 51.8%.")
    print("  여기 숫자는 «답했는가»라 잣대가 다르다. 같이 놓고 볼 수 있는 것은")
    print("  «멀티홉에서 무너지는가»뿐이고, 그 답이 위 «추천» 행들이다.")


if __name__ == "__main__":
    main()
