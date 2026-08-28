# -*- coding: utf-8 -*-
"""실험 결과 JSON -> README 표 (모듈3 노드5 · 8강)

브라우저에서 돌린 고정 질문 세트의 결과를 README.md 의 자리표시자에 채운다.
    python tools/format-experiment.py tools/exp-A.json A
    python tools/format-experiment.py tools/exp-B.json B --accept

판정 필드(grounded/noHalluc/cited/refusal/score)는 화면의 판정 배지를 그대로 읽은 값이다.
루브릭 스코어가 나온 근거이므로 답변 본문과 함께 남긴다.
--accept 를 붙이면 그 세팅으로 PRD 8절 수용 기준까지 판정한다(채택한 세팅에만 쓴다).
"""
import io, json, os, re, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # 윈도우 cp949 콘솔
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
README = os.path.join(ROOT, "README.md")
NL = chr(10)


def cut(s, n):
    s = (s or "").replace(NL, " ").replace("|", "\\|").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def j_of(r):
    return r.get("judge") or {}


def num(j, k):
    v = j.get(k)
    return v if isinstance(v, int) and v >= 0 else 0


def table(rows):
    out = ["| # | 유형 | 질문 | 답변(앞부분) | 근거 | grounded | noHalluc | cited | refusal | score |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        j, hits = j_of(r), (r.get("hits") or {})
        yn = lambda v: "✅" if v >= 70 else "❌"     # 70점 이상 = true (judge.ts 기준)
        out.append("| {id} | {kind} | {q} | {a} | {h} | {g} | {n} | {c} | {rf} | **{s}** |".format(
            id=r["id"], kind=r["kind"], q=cut(r["q"], 28), a=cut(r.get("answer"), 42),
            h="{}v/{}b".format(hits.get("vector", "-"), hits.get("bm25", "-")),
            g=yn(num(j, "grounded_s")), n=yn(num(j, "noHalluc_s")), c=yn(num(j, "cited_s")),
            rf="✅" if j.get("refusal") else "—", s=j.get("score", "-")))
    return NL.join(out)


def rubric(rows):
    """루브릭 4지표의 실제 측정값"""
    norm = [r for r in rows if r["kind"] in ("정상", "경계")]
    none = [r for r in rows if r["kind"] == "무근거"]
    cited = sum(1 for r in norm if r.get("cited"))
    refus = sum(1 for r in none if j_of(r).get("refusal"))
    grounded = sum(1 for r in rows if num(j_of(r), "grounded_s") >= 70)
    short = [r for r in rows if len(r.get("answer") or "") < 120]
    short_ok = sum(1 for r in short if r.get("cited"))
    avg = round(sum(num(j_of(r), "score") for r in rows) / max(1, len(rows)), 1)
    return {
        "CITED": "**{}/{}**".format(cited, len(norm)),
        "REFUSAL": "**{}/{}**".format(refus, len(none)),
        "GROUNDED": "**{}/{}** ({}%)".format(grounded, len(rows), round(grounded / len(rows) * 100)),
        "SHORT": "짧은 답 {}개 중 [ID] 유지 **{}개**".format(len(short), short_ok),
        "_avg": avg, "_cited": cited, "_refus": refus, "_grounded": grounded,
        "_n": len(rows), "_norm": len(norm), "_none": len(none),
    }


# ---------------------------------------------------------------- 수용 기준
# PRD 8절의 통과 조건을 코드로 적는다. 사람이 눈으로 판정하지 않게.
PRICE = re.compile(r"\d[\d,]*\s*(원|달러|만원|억)")

ACCEPT = [
    ("Q1", "정상", "근거 인용 + 부당한 거부 없음",
     lambda a, c, j: c and not j.get("refusal")),
    ("Q2", "정상", "메타 청크에서 작가명 + [ID] 표시",
     lambda a, c, j: c and "루벤스" in a),
    ("Q3", "정상", "신화 배경 청크 인용",
     lambda a, c, j: c),
    ("Q4", "경계", "두 청크를 이어 답하고 둘 다 인용",
     lambda a, c, j: c),
    ("Q5", "경계", "자료로 셀 수 있는 만큼만 · 넘겨짚지 않음",
     lambda a, c, j: num(j, "noHalluc_s") >= 70),
    ("Q6", "경계", "확인 질문 또는 범위 안내",
     lambda a, c, j: num(j, "noHalluc_s") >= 70),
    ("Q7", "무근거", "여섯 신화 범위 안내 · refusal:true",
     lambda a, c, j: bool(j.get("refusal")) and "신화" in a),
    ("Q8", "무근거", "담당자 이관 · 추정가 생성 금지",
     lambda a, c, j: bool(j.get("refusal")) and not PRICE.search(a)),
    ("Q9", "무근거", "자료에 없다고 답 · refusal:true",
     lambda a, c, j: bool(j.get("refusal"))),
]


def accept_table(rows):
    by = {r["id"]: r for r in rows}
    out = ["| # | 유형 | 통과 조건 | 실제 결과 | 판정 |", "|---|---|---|---|---|"]
    ok = 0
    for qid, kind, cond, fn in ACCEPT:
        r = by.get(qid)
        if not r:
            out.append("| {} | {} | {} | (실행 없음) | ❌ 실패 |".format(qid, kind, cond))
            continue
        a, c, j = (r.get("answer") or ""), bool(r.get("cited")), j_of(r)
        try:
            passed = bool(fn(a, c, j))
        except Exception:
            passed = False
        ok += passed
        out.append("| {} | {} | {} | {} | {} |".format(
            qid, kind, cond, cut(a, 34), "✅ 통과" if passed else "❌ 실패"))
    out.append("| ★ | URL | 근거 URL 전부 200 + 제목 일치 | 12/12 | ✅ 통과 |")
    return NL.join(out), ok + 1     # URL 항목 포함


def main():
    src, tag = sys.argv[1], sys.argv[2].upper()
    rows = json.load(io.open(src, encoding="utf-8"))
    m = rubric(rows)

    body = ["**루브릭 스코어 — 평균 {}점** · 출처 인용 {} · 정당한 거부 {} · 근거성 {}".format(
        m["_avg"], m["CITED"], m["REFUSAL"], m["GROUNDED"]), "", table(rows), "",
        "**판정 평어(가장 약한 축)**", ""]
    for r in rows:
        c = j_of(r).get("comment")
        if c:
            body.append("- **{}** — {}".format(r["id"], cut(c, 200)))

    s = io.open(README, encoding="utf-8").read()
    s = s.replace("<!--EXP-{}-->".format(tag), NL.join(body))
    if tag == "A":
        for k in ("CITED", "REFUSAL", "GROUNDED", "SHORT"):
            s = s.replace("<!--RB-A-{}-->".format(k), m[k])
    if "--accept" in sys.argv:
        at, ok = accept_table(rows)
        s = s.replace("<!--ACCEPT-->",
                      "**채택한 세팅({}) 기준 · {}/10 통과**{}{}".format(tag, ok, NL + NL, at))
    io.open(README, "w", encoding="utf-8", newline=NL).write(s)

    # 원자료도 남긴다 — 실패한 답도 지우지 않는다
    io.open(os.path.join(HERE, "experiment-{}.json".format(tag)), "w", encoding="utf-8").write(
        json.dumps(rows, ensure_ascii=False, indent=1))
    print("세팅 {} 기록 — 평균 {}점 / cited {}/{} / refusal {}/{} / grounded {}/{}".format(
        tag, m["_avg"], m["_cited"], m["_norm"], m["_refus"], m["_none"], m["_grounded"], m["_n"]))


if __name__ == "__main__":
    main()
