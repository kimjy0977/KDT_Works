# -*- coding: utf-8 -*-
"""질문 하나를 돌려 보고서와 계기판을 낸다.

  python run.py                      기본 질문
  python run.py "물어볼 것"          내 질문
"""
import io
import json
import os
import sys
import time

import graph as agent

HERE = os.path.dirname(os.path.abspath(__file__))
# ★기본 질문도 «파일»이 출처다 — 코드에 박아 두면 questions.json 과 갈린다
Q = json.load(io.open(os.path.join(HERE, "data/questions.json"),
                     encoding="utf-8"))["주질문"]["text"]


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else Q
    print("■ 질문: %s" % q)
    print("   코퍼스 %d건 · %d자\n" % (len(agent.DOCS),
                                  sum(len(v) for v in agent.DOCS.values())))
    st = agent.run(q)

    # ★요건 폴더 구조 — output/runs.jsonl · reports/
    #   전에는 run.json 하나를 «덮어썼다». 그래서 1회차 결과를 잃고
    #   전후 비교를 ★손으로 옮겨 적어야 했다(노드7 에서 배운 것을 어겼다).
    #   ⇒ 회차는 «쌓고», 보고서는 시각으로 이름을 붙여 «남긴다».
    os.makedirs(os.path.join(HERE, "output/reports"), exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    io.open(os.path.join(HERE, "output/reports/%s.md" % stamp), "w",
            encoding="utf-8", newline="").write(st["report"])
    io.open(os.path.join(HERE, "output/report.md"), "w",
            encoding="utf-8", newline="").write(st["report"])   # 최신 사본
    keep = {k: v for k, v in st.items() if k not in ("_배차",)}
    keep["ts"] = stamp
    keep["설정"] = dict(agent.설정)      # ★어떤 설정으로 돌렸는지 같이 남긴다
    io.open(os.path.join(HERE, "output/runs.jsonl"), "a",
            encoding="utf-8", newline="").write(
        json.dumps(keep, ensure_ascii=False, default=str) + "\n")
    io.open(os.path.join(HERE, "output/run.json"), "w",
            encoding="utf-8", newline="").write(
        json.dumps(keep, ensure_ascii=False, indent=1, default=str))

    m = st["metrics"]
    print("\n■ 계기판 — ★정답표 없이 잰 값")
    print("   근거율      %5.1f%%   (문장 %d개 중 «문서명» 붙은 것)"
          % (m["근거율"] * 100, m["문장수"]))
    print("   ★허위 인용  %5d     ← ★경보. 0이어야 한다 (진짜 환각)"
          % m["허위인용"])
    print("   표기 흔들림 %5d     %s"
          % (m["표기흔들림"],
             ", ".join("%s→%s" % x for x in m["표기흔들림_목록"][:3])))
    print("   읽고 안 쓴  %5d건    %s" % (len(m["읽고안쓴"]),
                                      ", ".join(m["읽고안쓴"][:4])))
    print("   최다 편중   %5.1f%%   (인용이 한 문서에 몰린 비율)" % (m["편중"] * 100))
    print("   중복률      %5.1f%%   (두 절 이상이 읽은 문서 비율)" % (m["중복률"] * 100))
    print("   ★격리율     %5.1f%%   코디 %s자 ÷ 팀 %s자  ★원시값을 같이 적는다"
          % (m["격리율"] * 100, format(m["코디가본글자"], ","),
             format(m["팀이읽은글자"], ",")))
    print("   ★꺾쇠 안 닫힘 %3d     ← ★경보. 인용이 있는데 안 세어진다"
          % m["꺾쇠안닫힘"])
    print("   인용 0곳 절 %5d개    %s" % (len(m["인용0절"]), m["인용0절"]))
    print("   읽은 문서 %d건 · 인용 %d건 · 보고서 %d자 · %d바퀴(%s)"
          % (m["읽은문서수"], m["인용수"], m["보고서자수"], m["바퀴"], m["종료"]))
    u = st["usage"]
    print("\n   호출 %d회 · 입력 %d · 출력 %d 토큰 · %.1f초 · 약 $%.4f"
          % (u["calls"], u["in"], u["out"], st["sec"],
             u["in"] / 1e6 * 0.15 + u["out"] / 1e6 * 0.60))
    print("   → output/reports/%s.md · runs.jsonl 에 1줄 추가" % stamp)


# ★모듈로 import 될 때는 돌지 않는다 — 없으면 import 하는 순간 LLM 호출이 나간다.
#   실사고 2026-09-23: ablation 을 import 해 배선만 확인하려다 «실험이 돌아» 타임아웃.
if __name__ == "__main__":
    main()
