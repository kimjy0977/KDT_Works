# -*- coding: utf-8 -*-
"""★비교용 보고서 3편을 «같은 질문»으로 만든다 — 사람이 직접 읽으려고.

  python make_compare.py

요건: 「같은 질문으로 보고서 여러 편을 만듭니다 — 기본 · 장치를 하나 끈 것 ·
      혼자 하는 대조군. ★나란히 놓고 직접 읽습니다.」

ablation 은 «숫자»만 남기고 보고서를 버린다. 사람이 읽으려면 글이 있어야 한다.
⇒ 축 A · 축 B · solo 셋을 output/reports/_비교_*.md 로 남긴다.
"""
import io
import json
import os

import graph as agent
from baseline import solo

HERE = os.path.dirname(os.path.abspath(__file__))
Q = json.load(io.open(os.path.join(HERE, "data/questions.json"),
                      encoding="utf-8"))["주질문"]["text"]
OUT = os.path.join(HERE, "output/reports")
os.makedirs(OUT, exist_ok=True)


def save(name, st, 머리):
    p = os.path.join(OUT, "_비교_%s.md" % name)
    m = st["metrics"]
    head = ["# %s" % 머리, "",
            "> 질문: %s" % st["question"], "",
            "```",
            "근거율 %.1f%% · 허위 %d · 표기흔들림 %d · 편중 %.1f%% · 중복률 %.1f%%"
            % (m["근거율"] * 100, m["허위인용"], m["표기흔들림"],
               m["편중"] * 100, m["중복률"] * 100),
            "읽은 문서 %d건 · 인용 %d건 · %d자"
            % (m["읽은문서수"], m["인용수"], m["보고서자수"]),
            "```", "", "---", ""]
    # ★절마다 «누가 무엇을 읽었나»를 글 옆에 남긴다 — 읽을 때 추적하려고
    tail = ["", "---", "", "## ★절별 — 누가 · 무엇을 읽고 · 무엇을 인용했나", ""]
    last = {}
    for s in sorted(st["sections"], key=lambda x: x.get("바퀴", 0)):
        old = last.get(s["절"])
        if old is None or len(s["인용"]) >= len(old["인용"]):
            last[s["절"]] = s
    for 절, s in last.items():
        tail.append("**%s** — `%s`" % (절, s["역할"]))
        tail.append("- 읽음: %s" % " · ".join("«%s»" % x for x in s["읽음"]))
        tail.append("- 인용: %s" % (" · ".join("«%s»" % x for x in s["인용"])
                                  or "(없음)"))
        안쓴 = [x for x in s["읽음"] if x not in s["인용"]]
        if 안쓴:
            tail.append("- ⬜읽고 안 씀: %s" % " · ".join(안쓴))
        tail.append("")
    io.open(p, "w", encoding="utf-8", newline="").write(
        "\n".join(head) + st["report"] + "\n".join(tail))
    print("   → %s  (근거율 %.1f%% · %d자)"
          % (os.path.basename(p), m["근거율"] * 100, m["보고서자수"]))


def main():
    print("■ 비교용 보고서 3편 — 같은 질문 · 같은 예산")
    print("   %s\n" % Q)

    base = list(agent.ROSTER)

    print("   ▶ 축 A — 주제 (창조·홍수·저승·영웅)")
    agent.ROSTER = base
    save("축A_주제", agent.run(Q, quiet=True),
         "축 A — 주제로 나눈 보고서 (우리 설정)")

    print("   ▶ 축 B — 문화권 (메소포타미아·그리스·이집트·북유럽)")
    agent.ROSTER = agent.ROSTER_ALT
    save("축B_문화권", agent.run(Q, quiet=True),
         "축 B — 문화권으로 나눈 보고서 (대조)")
    agent.ROSTER = base

    print("   ▶ solo — 혼자 (예산 12건 동일)")
    save("solo", solo(Q), "solo — 혼자 쓴 보고서 (대조군)")

    print("\n   ★이제 «사람이» 읽습니다. 지표는 명백한 실패만 거릅니다.")


if __name__ == "__main__":
    main()
