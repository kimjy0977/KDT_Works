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

import agent

HERE = os.path.dirname(os.path.abspath(__file__))
Q = "1894년에 일어난 주요 사건들은 무엇이고 각각의 원인은 무엇인가?"

# 조건 — (이름, 바꿀 설정, 무엇을 보려는 것인가)
CASES = [
    ("전부 켬 (기준선)", {}, "비교의 기준"),
    ("배정 끔", {"배정": False}, "코디가 시작문서를 안 정해 준다 → 편중·읽고안쓴이 뛸 것"),
    ("구역 끔", {"구역": False}, "남의 구역을 안 알려 준다 → ★중복률이 먼저 뛸 것"),
    ("역할 끔", {"역할": False}, "「시간순 담당」 같은 이름을 뗀다 → 절이 비슷해질 것"),
    ("재위임 끔", {"재위임": False}, "루프를 닫는다 → 근거율이 내려갈 것"),
]
WIDE = [
    ("2절 × 4건 (좁고 깊게)", {"절수": 2, "예산": 4}, "총 8건"),
    ("4절 × 2건 (넓고 얕게)", {"절수": 4, "예산": 2}, "총 8건 — ★예산이 같다"),
    ("4절 × 3건 (우리 설정)", {"절수": 4, "예산": 3}, "총 12건"),
]


def solo(question):
    """★대조군 — 혼자 일하는 오케스트레이터.

    팬아웃도 격리도 없이 «한 명»이 문서를 읽고 보고서를 통째로 쓴다.
    읽는 건수는 팀과 같게 맞춘다(절수 × 예산). 공정한 비교를 위해서다.
    ⇒ 이게 없으면 「멀티 에이전트가 좋다」가 그냥 주장이 된다.
    """
    n = agent.설정["절수"] * agent.설정["예산"]
    t0 = time.time()
    agent._usage.update({"in": 0, "out": 0, "calls": 0})
    titles = sorted(agent.DOCS)
    pick = agent.ask(
        "질문: %s\n\n문서 목록:\n%s\n\n"
        "이 질문에 답하려면 어느 문서 %d건을 읽어야 할까요? 제목만 줄바꿈으로."
        % (question, agent.cards(), n), "제목만 출력한다.", 300)
    read = [x.strip().strip("-«» ") for x in pick.split("\n")]
    read = [x for x in read if x in agent.DOCS][:n]
    read = read or titles[:n]
    memo = []
    for t in read:
        s = agent.read_one(t, question, question)
        if "관련 없음" not in s[:20]:
            memo.append("«%s» %s" % (t, s))
    rep = agent.ask(
        "질문: %s\n\n읽은 메모:\n%s\n\n"
        "이 메모«만»으로 네 개 절로 나뉜 장문 보고서를 쓰세요.\n"
        "★근거가 있는 문장 끝에 출처 제목을 «꺾쇠»에 넣어 붙이세요 — "
        "자료에서 온 문장 대부분에 붙입니다.\n"
        "쓸 수 있는 출처: %s"
        % (question, "\n\n".join(memo), " / ".join("«%s»" % x for x in read)),
        "너는 혼자 일하는 리서처다.", 2200)
    import re
    인용 = [x for x in re.findall(r"«([^»]+)»", rep) if x != "문서명"]
    st = {"question": question, "report": rep, "wheel": 1, "종료": "solo",
          "sections": [{"절": "전체", "번호": 0, "역할": "혼자", "원고": rep,
                        "읽음": read, "메모": memo, "인용": 인용,
                        "허위인용": [c for c in set(인용) if c not in read],
                        "충분": True, "부족": "", "바퀴": 0}]}
    from metrics import score
    st["metrics"] = score(st)
    st["usage"] = dict(agent._usage)
    st["sec"] = round(time.time() - t0, 2)
    return st


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
    """같은 조건의 여러 회차를 «평균과 폭»으로. 폭이 차이보다 크면 못 읽는 것이다."""
    out = {"조건": rs[0]["조건"], "비고": rs[0]["비고"], "회차": len(rs)}
    for k in KEYS:
        v = [r[k] for r in rs]
        out[k] = sum(v) / len(v)
        out[k + "_폭"] = max(v) - min(v)
    return out


def main():
    base = dict(agent.설정)
    rows = []
    N = runs_arg()
    cases = CASES + (WIDE if "--full" in sys.argv else [])

    print("■ 절제 실험 — 질문: %s" % Q)
    print("   ★끌 때마다 «어느 숫자가 먼저 움직이는지»를 본다.\n")
    for name, patch, why in cases:
        agent.설정.update(base)
        agent.설정.update(patch)
        print("   ▶ %-22s %s" % (name, why))
        reps = []
        for _i in range(N):
            _st = agent.run(Q, quiet=True)
            reps.append(row(name, _st, why))
            print("       [%d/%d] 근거율 %.1f%% · 편중 %.1f%% · 중복 %.1f%% · 호출 %d"
                  % (_i + 1, N, reps[-1]["근거율"] * 100, reps[-1]["편중"] * 100,
                     reps[-1]["중복률"] * 100, reps[-1]["호출"]))
        rows.append(agg(reps) if N > 1 else reps[0])
    agent.설정.update(base)          # ★되돌린다 — 안 되돌리면 뒤가 엉뚱해진다

    print("\n   ▶ %-22s %s" % ("혼자 하는 오케스트레이터", "팬아웃·격리 없이 한 명이"))
    reps = []
    for _i in range(N):
        _st = solo(Q)
        reps.append(row("★solo (대조군)", _st, "혼자 읽고 혼자 씀"))
        print("       [%d/%d] 근거율 %.1f%% · 안쓴 %d · 호출 %d"
              % (_i + 1, N, reps[-1]["근거율"] * 100, reps[-1]["읽고안쓴"],
                 reps[-1]["호출"]))
    rows.append(agg(reps) if N > 1 else reps[0])
    r = rows[-1]
    print("       근거율 %.1f%% · 편중 %.1f%% · 격리율 %.1f%% · 호출 %d"
          % (r["근거율"] * 100, r["편중"] * 100, r["격리율"] * 100, r["호출"]))

    show(rows)
    io.open(os.path.join(HERE, "output/ablation.json"), "w",
            encoding="utf-8", newline="").write(
        json.dumps({"question": Q, "runs": N, "rows": rows}, ensure_ascii=False, indent=1))
    tok = sum(r["입력토큰"] for r in rows)
    print("\n   총 입력 %d토큰 · 약 $%.3f · → output/ablation.json"
          % (tok, tok / 1e6 * 0.15))


main()
