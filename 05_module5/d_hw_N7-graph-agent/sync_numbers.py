# -*- coding: utf-8 -*-
"""★성능표를 «손으로 옮기지 않는다» — output/eval.json 에서 찍어낸다.

왜 이걸 만드나
  README 와 REPORT 에 같은 표를 «손으로» 두 번 적었더니 갈렸다.
  골든셋을 고쳐 다시 돌린 뒤 본문은 「→ 100%」로 고쳤는데 **표만 85.7% 로 남았다.**
  같은 문서 안에서 표와 본문이 다른 말을 했다.

  ⇒ §F-8-D 3단계 — «범위를 기억»하지 말고 «만질 때 검사»한다.
    여기서는 한 걸음 더 — «옮겨 적지» 말고 «찍어낸다».
    evaluate.py 를 다시 돌리면 이것도 같이 돌린다.

쓰는 법
  python sync_numbers.py           표를 찍어 보여만 준다 (기본)
  python sync_numbers.py --write   README.md · REPORT.md 의 표를 갈아 끼운다

표는 아래 두 표식 «사이»에만 들어간다. 표식이 없으면 건드리지 않는다.
  <!-- PERF:START -->  …  <!-- PERF:END -->
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
START = "<!-- PERF:START -->"
END = "<!-- PERF:END -->"
ORDER = ["1홉", "2홉", "4홉", "거절"]


def _pct(x):
    return "—" if x is None else "%.1f%%" % (x * 100)


def _bold(s):
    return "**%s**" % s if s == "100.0%" else s


def build():
    ev = json.load(io.open(os.path.join(HERE, "output/eval.json"),
                           encoding="utf-8"))
    rows = [json.loads(l) for l
            in io.open(os.path.join(HERE, "output/runs.jsonl"),
                       encoding="utf-8") if l.strip()]

    # 평균 초 — runs.jsonl 에서 «센다». eval.json 에 없다.
    secs = {}
    for r in rows:
        secs.setdefault(r["kind"], []).append(r.get("sec") or 0.0)

    base = (ev.get("baseline") or {}).get("by_kind") or {}
    n_runs = ev["n_runs"]

    out = [START, ""]
    out.append("| 구분 | 문항×회 | 답변 정확 | 경로 재현 | 평균 초 "
               "| basic RAG(BM25) |")
    out.append("|---|---|---|---|---|---|")
    for k in ORDER:
        d = ev["by_kind"].get(k)
        if not d:
            continue
        s = secs.get(k) or [0.0]
        b = base.get(k)
        bt = "—" if b is None else _pct(b)
        if k == "거절" and b == 0.0:
            bt = "★0.0% (구조적)"
        out.append("| %s | %d×%d | %s | %s | %.1f | %s |"
                   % ("★거절" if k == "거절" else k,
                      d["n"] // n_runs, n_runs,
                      _bold(_pct(d["answer_acc"])),
                      _pct(d.get("path_recall")),
                      sum(s) / len(s), bt))
    allsec = [x for v in secs.values() for x in v]
    out.append("| 전체 | %d | %s | | %.1f | %s |"
               % (ev["n_items"] * n_runs,
                  _bold(_pct(ev["overall_answer_acc"])),
                  sum(allsec) / len(allsec),
                  _pct((ev.get("baseline") or {}).get("overall", 0.0))))
    out.append("")

    # 문항별 통과 횟수 — «평균이 숨긴 것»
    per = ev["per_item_pass"]
    shaky = [k for k, v in per.items()
             if 0 < int(v.split("/")[0]) < int(v.split("/")[1])]
    dead = [k for k, v in per.items() if int(v.split("/")[0]) == 0]
    solid = [k for k, v in per.items()
             if int(v.split("/")[0]) == int(v.split("/")[1])]
    out.append("```")
    out.append("★흔들림     %d개 / %d개   %s"
               % (len(shaky), len(per),
                  ", ".join(shaky) if shaky
                  else "— 모든 문항이 회차마다 «같은» 결과를 낸다"))
    out.append("★구조적 실패 %d개          %s"
               % (len(dead), ", ".join(dead) if dead else "— 항상 실패하는 문항이 없다"))
    out.append("안정        %d개          %d/%d"
               % (len(solid), n_runs, n_runs))
    out.append("```")
    out.append("")
    out.append("*위 표와 이 블록은 `output/eval.json` 에서 "
               "`sync_numbers.py` 가 찍어냅니다 — 손으로 옮기지 않습니다.*")
    out.append("")
    out.append(END)
    return "\n".join(out)


def main():
    table = build()
    write = "--write" in sys.argv
    if not write:
        print(table)
        print("\n(표시만 했습니다. 파일에 넣으려면 --write)")
        return
    for name in ("README.md", "REPORT.md"):
        p = os.path.join(HERE, name)
        s = io.open(p, encoding="utf-8").read()
        i, j = s.find(START), s.find(END)
        if i < 0 or j < 0:
            print("  건너뜀 %s — 표식 없음" % name)
            continue
        s2 = s[:i] + table + s[j + len(END):]
        if s2 == s:
            print("  같음   %s" % name)
            continue
        io.open(p, "w", encoding="utf-8", newline="").write(s2)
        print("  갱신   %s (%d→%d자)" % (name, len(s), len(s2)))


main()
