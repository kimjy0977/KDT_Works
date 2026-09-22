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
GSTART = "<!-- GRAPH:START -->"
GEND = "<!-- GRAPH:END -->"
NL = chr(10)
ORDER = ["1홉", "2홉", "4홉", "거절"]


def _pct(x):
    return "—" if x is None else "%.1f%%" % (x * 100)


def _bold(s):
    return "**%s**" % s if s == "100.0%" else s


def _base_overall(ev):
    """★basic RAG 전체 — eval.json 에 `overall` 키가 없다.

    by_kind 와 문항 수로 «계산»한다. 손으로 적지 않는다.
    ⛔안 쟀으면 0.0% 가 아니라 None — 「0점」과 「안 쟀다」는 다르다.
      (전에는 `.get("overall", 0.0)` 이라 --baseline 없이 돌려도
       표가 「0.0%」라고 «측정한 척» 했다.)
    """
    b = ev.get("baseline") or {}
    if "overall" in b:
        return b["overall"]
    bk = b.get("by_kind")
    if not bk:
        return None
    n = ev["n_runs"]
    ks = [k for k in bk if k in ev["by_kind"]]
    tot = sum(ev["by_kind"][k]["n"] // n for k in ks)
    if not tot:
        return None
    return sum(bk[k] * (ev["by_kind"][k]["n"] // n) for k in ks) / tot


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
                  _pct(_base_overall(ev))))
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


def build_graph():
    """★그래프 수치도 «찍어낸다» — graph_stats.json · values.json 이 출처.

    오재호님 지적(이슈 #1 B-1) — 같은 것을 세는 줄이 문서마다 달랐다.
      §6      다리 1→5 · 미분류 28     ← 56건 코퍼스 시절 값이 남았다
      §2·README  다리 2→6

    ★그런데 「미분류」는 숫자만 틀린 게 아니었다 —
      한 단어가 «세 가지 다른 것»을 세고 있었다.
      ⇒ 숫자를 맞추는 것으로는 부족하다. «이름을 가른다».
      (하네스 §5 — 두 값이 다르면 「어느 쪽이 틀렸나」가 아니라
       「각각 무엇을 재는 값인가」를 먼저 묻는다)
    """
    g = json.load(io.open(os.path.join(HERE, "output/graph_stats.json"),
                          encoding="utf-8"))
    v = json.load(io.open(os.path.join(HERE, "values.json"), encoding="utf-8"))
    b, a = g["before"], g["after"]

    out = [GSTART, "", "```"]
    out.append("★정규화 전  두 편 이상이 함께 부르는 가치 «다리»  %d개  (가치 쌍 %d)"
               % (b["multi"], b["pairs"]))
    out.append("★정규화 후  〃                                  %d개  (축·극 쌍 %d)"
               % (a["multi"], a["pairs"]))
    out.append("")
    out.append("노드 %d · 엣지 %d · 삼중항 %d · 문서 %d"
               % (g["nodes"], g["edges"], g["n_triples"], g["n_docs"]))
    out.append("축을 가로지르는 충돌 %d건 · 같은 극이라 버린 쌍 %d건"
               % (len(g["cross_axis"]), len(g["same_pole_dropped"])))
    out.append("```")
    out.append("")
    out.append("★**「미분류」는 세 가지를 가리킵니다** — 세는 대상이 다릅니다.")
    out.append("")
    out.append("| 이름 | 값 | 무엇을 세나 | 출처 |")
    out.append("|---|---|---|---|")
    out.append("| 충돌 쌍 미분류 | **%d** | 축 8개에 안 담긴 «대립 쌍» | `graph_stats.unmapped` |"
               % len(g["unmapped"]))
    out.append("| 사전 미분류 | **%d** | 사전에 남긴 «가치 이름» | `values.json._미분류` |"
               % len(v["_미분류"]))
    out.append("| 배정 회차 미분류 | §2 참조 | «마지막 배정 한 회차» 기록 | `values.json._배정기록` |")
    out.append("")
    out.append("*이 블록은 `output/graph_stats.json` · `values.json` 에서 "
               "`sync_numbers.py` 가 찍어냅니다 — 손으로 옮기지 않습니다.*")
    out.append("")
    out.append(GEND)
    return NL.join(out)


def main():
    blocks = [(START, END, build()), (GSTART, GEND, build_graph())]
    write = "--write" in sys.argv
    if not write:
        for _a, _b, t in blocks:
            print(t)
            print()
        print("(표시만 했습니다. 파일에 넣으려면 --write)")
        return
    for name in ("README.md", "REPORT.md"):
        p = os.path.join(HERE, name)
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


main()
