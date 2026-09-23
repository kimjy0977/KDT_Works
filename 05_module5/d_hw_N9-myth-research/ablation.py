# -*- coding: utf-8 -*-
"""★절제 실험 — 만든 장치를 하나씩 «꺼» 보고 무엇이 실제로 값을 하는지 잰다.

강의 15강. 로그가 바쁘게 돌아가는 것만 봐서는 부분이 일하는지 알 수 없다.
끄고 나서 «무엇을 보고 나빠졌다고 말할 것인가»를 먼저 정해 둔 것이 metrics.py 다.

★지표가 어느 장치에 붙는지 (14강)
    편중 · 중복률    → 배정 · 구역의 계기
    읽고 안 쓴 문서  → 배정 «품질»의 계기
    근거율           → 깊이 · 재위임의 계기
    허위 인용        → 계기가 아니라 ★경보 (0이어야 한다)

그래서 끌 때마다 «어느 숫자가 먼저 움직이는지»를 본다.
종합 점수 하나로는 범인을 못 찾는다.

  python ablation.py            기본 5개 조건
  python ablation.py --full     + 폭·깊이 비교까지
"""
import io
import json
import os
import sys
import time

import graph as agent
from baseline import solo, 공정성표

HERE = os.path.dirname(os.path.abspath(__file__))
# ★질문도 «파일»이 출처다 — 코드에 박으면 questions.json 과 갈린다
Q = json.load(io.open(os.path.join(HERE, "data/questions.json"),
                     encoding="utf-8"))["주질문"]["text"]

# 조건 — (이름, 바꿀 설정, 무엇을 보려는 것인가)
CASES = [
    ("전부 켬 (기준선)", {}, "비교의 기준"),
    ("배정 끔", {"배정": False}, "코디가 시작문서를 안 정해 준다 → 편중·읽고안쓴이 뛸 것"),
    ("구역 끔", {"구역": False}, "남의 구역을 안 알려 준다 → ★중복률이 먼저 뛸 것"),
    ("역할 끔", {"역할": False}, "「시간순 담당」 같은 이름을 뗀다 → 절이 비슷해질 것"),
    ("재위임 끔", {"재위임": False}, "루프를 닫는다 → 근거율이 내려갈 것"),
    # ★★기준선을 «한 번 더» 돌린다 — 설정이 첫 줄과 «완전히 같다».
    #   장치를 끈 것이 아니라 ★«잡음 그 자체»를 재는 조건이다.
    #   요건이 이름 붙인 흔한 사고 ③ —「같은 설정도 시행마다 십몇 %p 움직인다」.
    #   ⇒ 이 두 줄의 차이보다 «작은» 차이는 읽지 않는다. 그것이 잣대다.
    ("★기준선 (재측정)", {}, "첫 줄과 «같은 설정». 이 둘의 차이가 ★잡음의 크기다"),
]
# ★★축 바꾸기 — 이 프로젝트의 «고유» 실험
#   요건: 「목차의 축이 곧 분업이고, 분업이 곧 결과물의 모양이다」
#   A(주제)  창조·홍수·저승·영웅   → 조사관이 «문화권»을 가로질러 읽는다
#   B(문화권) 메소포타미아·그리스·이집트·북유럽 → «주제»를 가로질러 읽는다
#   ⇒ 같은 예산·같은 코퍼스. 바뀌는 것은 «나누는 기준» 하나뿐이다.
AXIS = [
    ("★축 A — 주제 (우리 설정)", {}, "창조·홍수·저승·영웅"),
    ("★축 B — 문화권", {"_축B": True},
     "메소포타미아·그리스·이집트·북유럽 — 각자 «자기 문화권»만 읽는다"),
]
WIDE = [
    ("2절 × 4건 (좁고 깊게)", {"절수": 2, "예산": 4}, "총 8건"),
    ("4절 × 2건 (넓고 얕게)", {"절수": 4, "예산": 2}, "총 8건 — ★예산이 같다"),
    ("4절 × 3건 (우리 설정)", {"절수": 4, "예산": 3}, "총 12건"),
]


# ★solo 는 baseline.py 에 있다 — 여기서 다시 구현하지 않는다.
#   두 벌로 두면 「같은 도구」가 아니게 되고 한쪽만 고치는 사고가 난다.
def row(name, st, note=""):
    m, u = st["metrics"], st["usage"]
    return {"조건": name, "근거율": m["근거율"], "허위인용": m["허위인용"],
            "읽고안쓴": len(m["읽고안쓴"]), "편중": m["편중"],
            "중복률": m["중복률"], "격리율": m["격리율"],
            "읽은문서": m["읽은문서수"], "보고서자수": m["보고서자수"],
            "인용0절": len(m["인용0절"]), "호출": u["calls"],
            "입력토큰": u["in"], "초": st["sec"], "비고": note}


def show(rows):
    print("\n%-22s %7s %5s %5s %7s %7s %7s %6s %6s"
          % ("조건", "근거율", "허위", "안쓴", "편중", "중복률", "격리율", "호출", "자수"))
    print("-" * 82)
    for r in rows:
        w = r.get("근거율_폭")
        print("%-22s %6.1f%%%-5s %3.0f %4.1f %6.1f%% %6.1f%% %6.1f%% %5.0f %6.0f"
              % (r["조건"], r["근거율"] * 100,
                 ("±%.0f" % (w * 100 / 2)) if w is not None else "",
                 r["허위인용"], r["읽고안쓴"], r["편중"] * 100,
                 r["중복률"] * 100, r["격리율"] * 100,
                 r["호출"], r["보고서자수"]))


def runs_arg():
    """★몇 회 돌릴까 — 1회로 재고 «성능»이라 부르지 않는다.
    절제 실험은 «조건 사이의 차이»를 보는 것이라 더 그렇다 —
    차이가 십몇 %p 인데 잡음이 그만큼이면 아무것도 못 본다."""
    for k, a in enumerate(sys.argv):
        if a == "--runs" and k + 1 < len(sys.argv):
            return int(sys.argv[k + 1])
    return 1


KEYS = ("근거율", "편중", "중복률", "격리율", "읽고안쓴", "호출",
        "보고서자수", "허위인용", "읽은문서", "인용0절", "입력토큰", "초")


def agg(rs):
    """같은 조건의 여러 회차를 «평균과 폭»으로. 폭이 차이보다 크면 못 읽는 것이다.

    ★회차별 «원시값»도 함께 남긴다. 평균·폭만 남기면 분포를 다시 못 본다 —
      노드8 에서 3회 결론이 ★4회차에 깨졌는데, 원시값이 없어 왜인지 못 봤다.
    """
    out = {"조건": rs[0]["조건"], "비고": rs[0]["비고"], "회차": len(rs)}
    for k in KEYS:
        v = [r[k] for r in rs]
        out[k] = sum(v) / len(v)
        out[k + "_폭"] = max(v) - min(v)
    out["_회차별"] = [{k: r[k] for k in KEYS} for r in rs]   # ★원시값
    return out


def main():
    base = dict(agent.설정)
    _ROSTER0 = list(agent.ROSTER)     # ★되돌릴 원본
    rows = []
    N = runs_arg()
    cases = CASES[:]
    if "--axis" in sys.argv or "--all" in sys.argv:
        cases += AXIS
    if "--full" in sys.argv or "--all" in sys.argv:
        cases += WIDE

    print("■ 절제 실험 — 질문: %s" % Q)
    print("   ★끌 때마다 «어느 숫자가 먼저 움직이는지»를 본다.\n")
    for name, patch, why in cases:
        agent.설정.update(base)
        # ★축 B — ROSTER 를 통째로 바꾼다. 설정 키가 아니라 «명단»이 바뀌는 것이다.
        agent.ROSTER = _ROSTER0
        if patch.pop("_축B", False):
            agent.ROSTER = agent.ROSTER_ALT
        agent.설정.update(patch)
        print("   ▶ %-22s %s" % (name, why))
        reps = []
        for _i in range(N):
            _st = agent.run(Q, quiet=True)
            reps.append(row(name, _st, why))
            print("       [%d/%d] 근거율 %.1f%% · 편중 %.1f%% · 중복 %.1f%% · 호출 %d"
                  % (_i + 1, N, reps[-1]["근거율"] * 100, reps[-1]["편중"] * 100,
                     reps[-1]["중복률"] * 100, reps[-1]["호출"]))
        rows.append(agg(reps))
    agent.설정.update(base)          # ★되돌린다 — 안 되돌리면 뒤가 엉뚱해진다
    agent.ROSTER = _ROSTER0

    print("\n   ▶ %-22s %s" % ("혼자 하는 오케스트레이터", "팬아웃·격리 없이 한 명이"))
    reps = []
    for _i in range(N):
        _st = solo(Q)
        reps.append(row("★solo (대조군)", _st, "혼자 읽고 혼자 씀"))
        print("       [%d/%d] 근거율 %.1f%% · 안쓴 %d · 호출 %d"
              % (_i + 1, N, reps[-1]["근거율"] * 100, reps[-1]["읽고안쓴"],
                 reps[-1]["호출"]))
    rows.append(agg(reps))
    r = rows[-1]
    print("       근거율 %.1f%% · 편중 %.1f%% · 격리율 %.1f%% · 호출 %d"
          % (r["근거율"] * 100, r["편중"] * 100, r["격리율"] * 100, r["호출"]))
    # ★대조군이 «묶이지 않았는지»를 표로 찍는다 — 주장하지 않는다
    팀읽음 = int(rows[0]["읽은문서"])
    print(공정성표(_st["공정성"], 팀읽음))

    show(rows)
    io.open(os.path.join(HERE, "output/ablation.json"), "w",
            encoding="utf-8", newline="").write(
        json.dumps({"question": Q, "runs": N, "rows": rows}, ensure_ascii=False, indent=1))
    tok = sum(r["입력토큰"] for r in rows)
    print("\n   총 입력 %d토큰 · 약 $%.3f · → output/ablation.json"
          % (tok, tok / 1e6 * 0.15))


# ★모듈로 import 될 때는 돌지 않는다 — 없으면 import 하는 순간 LLM 호출이 나간다.
#   실사고 2026-09-23: ablation 을 import 해 배선만 확인하려다 «실험이 돌아» 타임아웃.
if __name__ == "__main__":
    main()
