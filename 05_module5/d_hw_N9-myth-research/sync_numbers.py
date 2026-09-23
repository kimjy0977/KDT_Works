# -*- coding: utf-8 -*-
"""★수치를 «손으로 옮기지 않는다» — ablation.json 에서 찍어낸다.

노드7 에서 배운 것을 그대로 가져왔다.
  같은 표를 README 와 REPORT 에 «손으로» 두 번 적었더니 갈렸다.
  다시 돌린 뒤 본문만 고치고 표를 안 고쳐, 같은 문서가 두 점수를 말했다.

그리고 이번에 «또» 그럴 뻔했다 — run.json 을 덮어써서 1회차를 잃고
fixlog.md 에 ★손으로 옮겨 적었다. 그 파일에 「손으로 옮긴 값」이라고 적어 뒀다.

  python sync_numbers.py           찍어서 보여만 준다
  python sync_numbers.py --write   README.md · REPORT.md 의 표식 사이를 갈아 끼운다

표식
  <!-- ABL:START -->  …  <!-- ABL:END -->     절제 실험 표
  <!-- CORPUS:START --> … <!-- CORPUS:END -->  코퍼스 수치
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NL = chr(10)
A0, A1 = "<!-- ABL:START -->", "<!-- ABL:END -->"
C0, C1 = "<!-- CORPUS:START -->", "<!-- CORPUS:END -->"
E0, E1 = "<!-- E2E:START -->", "<!-- E2E:END -->"
R0, R1 = "<!-- RED:START -->", "<!-- RED:END -->"


def _j(name):
    return json.load(io.open(os.path.join(HERE, name), encoding="utf-8"))


def 절제표():
    a = _j("output/ablation.json")
    rows = a["rows"]
    n = rows[0].get("회차", 1)

    # ★목록은 compare.py 한 곳에만 있다 — 두 곳에 두니 갈렸다
    from compare import 같은설정, 같은설정_원시값
    pool = 같은설정_원시값(rows)

    out = [A0, "", "```"]
    out.append("조건                     근거율        편중      중복률   안쓴  호출   자수")
    for r in rows:
        star = "★" if ("solo" in r["조건"] or "축" in r["조건"]
                       or "재측정" in r["조건"]) else " "
        out.append("%s%-22s %5.1f%%±%-4.1f %5.1f%%   %5.1f%%  %3.1f   %2.0f  %5.0f"
                   % (star, r["조건"].replace("★", "")[:22],
                      r["근거율"] * 100, r["근거율_폭"] * 100,
                      r["편중"] * 100, r["중복률"] * 100,
                      r["읽고안쓴"], r["호출"], r["보고서자수"]))
    out.append("```")
    out.append("")

    if len(pool) >= 6:
        평균들 = [r["근거율"] for r in rows if "solo" not in r["조건"]]
        잡음 = max(pool) - min(pool)
        차이 = max(평균들) - min(평균들)
        solo = [r for r in rows if "solo" in r["조건"]]
        sp = [x["근거율"] for x in solo[0].get("_회차별", [])] if solo else []

        out.append("### ★잣대 — 「전부 켬」·「기준선(재측정)」·「축 A」는 "
                   "**완전히 같은 설정**입니다")
        out.append("")
        out.append("```")
        out.append("같은 설정 %d회 «원시값»" % len(pool))
        out.append("  " + " · ".join("%.1f" % (v * 100) for v in sorted(pool)))
        out.append("  최소 %.1f%%  최대 %.1f%%   →  ★잡음 폭 %.1f%%p"
                   % (min(pool) * 100, max(pool) * 100, 잡음 * 100))
        out.append("")
        out.append("장치를 바꾼 조건들의 «평균» 범위   %.1f ~ %.1f%%  →  차이 %.1f%%p"
                   % (min(평균들) * 100, max(평균들) * 100, 차이 * 100))
        out.append("")
        if 잡음 > 차이:
            out.append("⇒ ★잡음(%.1f)이 차이(%.1f)보다 «크다».""" % (잡음 * 100, 차이 * 100))
            out.append("  이 지표로는 ★어떤 장치도 가를 수 없다.")
        else:
            out.append("⇒ 차이(%.1f)가 잡음(%.1f)보다 크다." % (차이 * 100, 잡음 * 100))
        if sp:
            겹침 = max(sp) > min(pool)
            out.append("")
            out.append("단 하나 예외 — solo")
            out.append("  solo  " + " · ".join("%.1f" % (v * 100) for v in sorted(sp)))
            out.append("  solo 최대 %.1f%%  vs  팀 최소 %.1f%%   →  %s"
                       % (max(sp) * 100, min(pool) * 100,
                          "겹친다" if 겹침 else "★겹치지 않는다"))
        out.append("```")
        out.append("")
        # ⚠옛 판은 「0.6%%p」를 ★손으로 박아 뒀다 — 회차가 바뀌자 거짓말이 됐다.
        #   ★찍어내는 블록 안에 «손으로 쓴 수치»를 두면 안 된다.
        _평균들 = [r["근거율"] for r in rows if r["조건"] in 같은설정]
        out.append("★**평균끼리 견주면 잡음이 «사라진 것처럼» 보입니다** — "
                   "같은 설정 세 묶음의 평균은 %s 로 %.1f%%p 안이었습니다. "
                   "원시값(%.1f%%p)을 펴야 보입니다."
                   % (" / ".join("%.1f" % (v * 100) for v in _평균들),
                      (max(_평균들) - min(_평균들)) * 100, 잡음 * 100))
        out.append("")

    out.append("*이 블록은 `output/ablation.json` 에서 `sync_numbers.py` 가 "
               "찍어냅니다 — 손으로 옮기지 않습니다. %d회 평균 ± 폭.*" % n)
    out.append("")
    out.append(A1)
    return NL.join(out)

def 코퍼스표():
    c = _j("config.json")["_코퍼스"]
    b = _j("data/corpus.json")
    docs, links = b["docs"], b["links"]
    n = sum(len(v) for v in docs.values())
    zero = [k for k in docs if not links.get(k)]
    out = [C0, "", "```"]
    out.append("문서 %d건 · %s자 (≈%s 토큰) = 창 128k 의 ★%.2f배"
               % (len(docs), format(n, ","), format(n // 2, ","), n / 2 / 128000))
    out.append("내부 링크 %d개 · 문서당 평균 %.1f"
               % (sum(len(v) for v in links.values()),
                  sum(len(v) for v in links.values()) / len(docs)))
    가장긴 = max(docs.items(), key=lambda kv: len(kv[1]))
    out.append("가장 긴 문서 «%s» %s자" % (가장긴[0], format(len(가장긴[1]), ",")))
    out.append("★링크 0개 %d건 — %s" % (len(zero), " · ".join(zero)))
    out.append("   ⇒ 링크를 타고는 «절대» 못 닿는다. 코디네이터가 카드를 보고")
    out.append("     직접 배정해야만 닿는 문서다.")
    out.append("```")
    out.append("")
    out.append("*`config.json` · `data/corpus.json` 에서 찍어냅니다.*")
    out.append("")
    out.append(C1)
    return NL.join(out)



def e2e표():
    """★엔드투엔드 기록 — 「돌아갑니다」가 아니라 «돌린 기록»."""
    e = _j("output/e2e.json")
    out = [E0, "", "```"]
    out.append("%-20s %-26s %7s  %s"
               % ("단계", "명령", "걸린 시간", "산출물"))
    for x in e["단계"]:
        out.append("%s %-18s python %-19s %6.1f초  %s"
                   % ("OK  " if x["통과"] else "★실패", x["단계"][:18],
                      x["명령"], x["초"], x["산출물"] or "-"))
    out.append("")
    out.append("총 %.1f초 · ★%d / %d 단계 통과%s"
               % (sum(x["초"] for x in e["단계"]), e["통과"], e["전체"],
                  "  (코퍼스부터 새로)" if e.get("fresh") else
                  "  (코퍼스는 캐시 · --fresh 로 전부 새로)"))
    out.append("```")
    out.append("")
    out.append("*`output/e2e.json` 에서 찍어냅니다 — 손으로 옮기지 않습니다.*")
    out.append("")
    out.append(E1)
    return NL.join(out)


def red표():
    """레드팀 결과 — ★돌려서 나온 값만 적는다."""
    import subprocess
    import sys as _s
    r = subprocess.run([_s.executable, os.path.join(HERE, "redteam.py")],
                       cwd=HERE, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    t = (r.stdout or "").strip().splitlines()
    합계 = next((l for l in t if l.startswith("합계")), "(못 읽음)")
    bad = [l.strip() for l in t if l.strip() and "  " in l
           and t.index(l) > 0]
    out = [R0, "", "```"]
    # BAD/WARN 구간만 옮긴다 — OK 48줄은 파일에 있다
    쓰기 = False
    for l in t:
        if l.startswith("── ★BAD") or l.startswith("── WARN"):
            쓰기 = True
            out.append(l)
            continue
        if l.startswith("── OK"):
            쓰기 = False
        if 쓰기 and l.strip():
            out.append(l)
    if len(out) == 3:
        out.append("★BAD 0 · WARN 0 — 50항목 전부 통과")
    out.append("")
    out.append(합계)
    out.append("```")
    out.append("")
    out.append("*`redteam.py` 를 «실제로 돌려» 찍습니다.*")
    out.append("")
    out.append(R1)
    return NL.join(out)

def main():
    blocks = [(A0, A1, 절제표()), (C0, C1, 코퍼스표()),
              (E0, E1, e2e표()), (R0, R1, red표())]
    if "--write" not in sys.argv:
        for _a, _b, t in blocks:
            print(t)
            print()
        print("(표시만 했습니다. 넣으려면 --write)")
        return
    for name in ("README.md", "REPORT.md"):
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            print("  없음   %s" % name)
            continue
        s = io.open(p, encoding="utf-8").read()
        n0, hit = len(s), []
        for a, b, t in blocks:
            i, j = s.find(a), s.find(b)
            if i < 0 or j < 0:
                continue
            s = s[:i] + t + s[j + len(b):]
            hit.append(a[5:].split(":")[0])
        if not hit:
            print("  건너뜀 %s — 표식 없음" % name)
            continue
        io.open(p, "w", encoding="utf-8", newline="").write(s)
        print("  갱신   %s  [%s]  %d -> %d자"
              % (name, chr(183).join(hit), n0, len(s)))


if __name__ == "__main__":
    main()
