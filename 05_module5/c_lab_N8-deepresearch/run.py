# -*- coding: utf-8 -*-
"""질문 하나를 돌려 보고서와 계기판을 낸다.

  python run.py                      기본 질문
  python run.py "물어볼 것"          내 질문
"""
import io
import json
import os
import sys

import agent

HERE = os.path.dirname(os.path.abspath(__file__))
Q = "1894년에 일어난 주요 사건들은 무엇이고 각각의 원인은 무엇인가?"


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else Q
    print("■ 질문: %s" % q)
    print("   코퍼스 %d건 · %d자\n" % (len(agent.DOCS),
                                  sum(len(v) for v in agent.DOCS.values())))
    st = agent.run(q)

    os.makedirs(os.path.join(HERE, "output"), exist_ok=True)
    io.open(os.path.join(HERE, "output/report.md"), "w",
            encoding="utf-8", newline="").write(st["report"])
    keep = {k: v for k, v in st.items() if k not in ("_배차",)}
    io.open(os.path.join(HERE, "output/run.json"), "w",
            encoding="utf-8", newline="").write(
        json.dumps(keep, ensure_ascii=False, indent=1, default=str))

    m = st["metrics"]
    print("\n■ 계기판 — ★정답표 없이 잰 값")
    print("   근거율      %5.1f%%   (문장 %d개 중 «문서명» 붙은 것)"
          % (m["근거율"] * 100, m["문장수"]))
    print("   ★허위 인용  %5d     ← 경보. 0이어야 한다" % m["허위인용"])
    print("   읽고 안 쓴  %5d건    %s" % (len(m["읽고안쓴"]),
                                      ", ".join(m["읽고안쓴"][:4])))
    print("   최다 편중   %5.1f%%   (인용이 한 문서에 몰린 비율)" % (m["편중"] * 100))
    print("   중복률      %5.1f%%   (두 절 이상이 읽은 문서 비율)" % (m["중복률"] * 100))
    print("   ★격리율     %5.1f%%   (코디가 본 글자 ÷ 팀이 읽은 글자)"
          % (m["격리율"] * 100))
    print("   인용 0곳 절 %5d개    %s" % (len(m["인용0절"]), m["인용0절"]))
    print("   읽은 문서 %d건 · 인용 %d건 · 보고서 %d자 · %d바퀴(%s)"
          % (m["읽은문서수"], m["인용수"], m["보고서자수"], m["바퀴"], m["종료"]))
    u = st["usage"]
    print("\n   호출 %d회 · 입력 %d · 출력 %d 토큰 · %.1f초 · 약 $%.4f"
          % (u["calls"], u["in"], u["out"], st["sec"],
             u["in"] / 1e6 * 0.15 + u["out"] / 1e6 * 0.60))
    print("   → output/report.md · output/run.json")


main()
