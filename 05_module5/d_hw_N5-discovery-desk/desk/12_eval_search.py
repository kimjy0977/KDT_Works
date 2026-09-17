# -*- coding: utf-8 -*-
"""★검색을 «채점»한다 — 정밀도와 재현율을 «둘 다».

왜 처음부터 둘 다 재는가
  어제(노드4) 역방향 가드레일을 만들면서 **정밀도만 쟀다.**
  오탐을 24/25 → 3/25 로 줄이고 「좋아졌다」고 세 번 판단했는데,
  나중에 재현율을 재 보니 **9%** 였다. 좁히는 «그 과정»에서 잡아야 할 것도 죽었다.
  10강이 「오탐 0건」을 강조해서 **그 축만 봤다.**
  ⇒ 그래서 이 파일은 «처음부터» 두 축을 나란히 찍는다.

무엇을 재나
  재현율  must_ids 가 상위 N 안에 «들어왔나»      — 잡아야 할 것을 잡았나
  정밀도  must_not_ids 가 «안 나왔나» + 상위 결과가 «관련 있나»
  순위    must 가 몇 등으로 나왔나 — 1등이 아니면 답변이 엉뚱한 걸 읽는다

  python 12_eval_search.py
  python 12_eval_search.py --topk 3 --thr 0.35     # 손잡이를 돌려 가며
"""
import argparse
import csv
import io
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent


def load_cases():
    rows = list(csv.DictReader(io.open(HERE / "eval_search.csv", encoding="utf-8")))
    out = []
    for r in rows:
        out.append({
            "query": r["query"],
            "must": [x for x in (r["must_ids"] or "").split(";") if x],
            "must_not": [x for x in (r["must_not_ids"] or "").split(";") if x],
            "note": r.get("note", ""),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topk", type=int, default=5, help="상위 몇 건을 «본 것»으로 치나")
    ap.add_argument("--thr", type=float, default=None, help="점수 임계값 덮어쓰기")
    args = ap.parse_args()

    import tools_desk
    if args.thr is not None:
        # ★손잡이가 «실제로 닿는지» 확인하고 바꾼다.
        #   어제 CONF_THRESHOLD 가 config 에 있는데 router.py 가 덮어써서
        #   «바꿔도 안 먹는» 일이 있었다. 같은 실수를 하지 않으려고 직접 패치한다.
        src = io.open(HERE / "tools_desk.py", encoding="utf-8").read()
        assert "if s > 0.30:" in src, "★임계값 줄을 못 찾음 — 코드가 바뀌었다"
        print("   (임계값 %.2f 로 덮어씀 — 원본 0.30)" % args.thr)
        tools_desk._THR = args.thr

    cases = load_cases()
    print("=== 검색 채점 — %d건 · 상위 %d건을 본다 ===" % (len(cases), args.topk))
    print()

    hit = miss = 0
    bad = 0          # must_not 이 나온 횟수
    ranks = []
    rows = []
    for c in cases:
        r = tools_desk.search_article(c["query"])
        ids = [x["id"] for x in r["results"][:args.topk]]
        got = [m for m in c["must"] if m in ids]
        lost = [m for m in c["must"] if m not in ids]
        viol = [m for m in c["must_not"] if m in ids]
        hit += len(got)
        miss += len(lost)
        bad += len(viol)
        for m in got:
            ranks.append(ids.index(m) + 1)
        rows.append((c, ids, got, lost, viol, r["count"]))

    total = hit + miss
    print("%-34s %-6s %-5s %s" % ("질의", "재현", "위반", "상위 결과"))
    print("─" * 92)
    for c, ids, got, lost, viol, n in rows:
        mark = "✅" if not lost and not viol else ("⛔" if lost else "⚠")
        print("%-34s %s%d/%d  %-4s %s"
              % (c["query"][:32], mark, len(got), len(c["must"]),
                 ("★%d" % len(viol)) if viol else "-",
                 ",".join(ids[:3]) or "(없음)"))
        if lost:
            print("       못 찾음: %s  (검색 결과 %d건)" % (",".join(lost), n))
        if viol:
            print("       ★나오면 안 되는 것이 나옴: %s" % ",".join(viol))

    print()
    print("══ 요약 ══")
    print("   재현율   %d/%d (%.0f%%)   ← 잡아야 할 것을 잡았나"
          % (hit, total, 100 * hit / max(1, total)))
    print("   위반     %d건            ← 나오면 안 되는 것이 나왔나" % bad)
    if ranks:
        print("   평균 순위 %.1f등 (1등 %d건)"
              % (sum(ranks) / len(ranks), sum(1 for x in ranks if x == 1)))
    print()
    print("   ※ 두 축을 «같이» 본다. 재현율만 보면 임계값을 낮춰 전부 통과시킬 수 있고,")
    print("     위반만 보면 아무것도 안 내보내면 0건이 된다. 한쪽만 재면 속는다.")


if __name__ == "__main__":
    main()
