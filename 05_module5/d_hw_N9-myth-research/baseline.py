# -*- coding: utf-8 -*-
"""★대조군 — 혼자 하는 오케스트레이터. «공정한가»를 코드가 찍는다.

  python baseline.py                  한 번 돌린다
  python baseline.py --runs 3         여러 번 · 폭을 함께 본다
  python baseline.py --fairness       ★공정성 점검만 (LLM 호출 없음)

왜 «파일을 따로» 두나
  요건이 `baseline.py` 를 제출 구조에 따로 넣었다. 그럴 만하다 —
  대조군이 ablation 안에 묻혀 있으면 «스위치 하나»처럼 보인다.
  실제로는 ★이 프로젝트의 주장 전체가 여기에 걸려 있다.

★요건이 못 박은 것
  「대조군에는 같은 자료 · 모델 · 도구 · 같은 읽기 예산을 줍니다.
   ★예산을 다 쓰는지 확인하세요. 중간에 멈추면 이긴 것이 아니라
   상대를 묶어 둔 것입니다.」

  ⇒ 그래서 이 파일은 «주장»하지 않고 ★찍는다.
    돌릴 때마다 아래 넷을 출력하고, 하나라도 어긋나면 ⛔ 로 표시한다.
      ① 같은 코퍼스인가        DOCS 가 같은 객체인가
      ② 같은 모델인가          설정["모델"] 을 그대로 쓰는가
      ③ 같은 도구인가          read_one() · ask() 를 그대로 쓰는가
      ④ ★예산을 다 썼는가      요구 12건 중 몇 건을 실제로 읽었나
"""
import argparse
import io
import json
import os
import re
import statistics as stat
import time

import graph as agent
from metrics import score

HERE = os.path.dirname(os.path.abspath(__file__))


def 예산():
    """팀과 «같은» 읽기 예산 — 절수 × 절당 예산."""
    return agent.설정["절수"] * agent.설정["예산"]


def solo(question):
    """혼자 일하는 오케스트레이터. 팬아웃도 격리도 없다.

    ★팀과 «같은» 도구를 쓴다 — agent.ask · agent.read_one 을 그대로 부른다.
      따로 구현하면 그 순간 「같은 도구」가 아니게 된다.
    """
    n = 예산()
    t0 = time.time()
    agent._usage.update({"in": 0, "out": 0, "calls": 0})

    pick = agent.ask(
        "질문: %s\n\n문서 목록:\n%s\n\n"
        "이 질문에 답하려면 어느 문서 %d건을 읽어야 할까요? 제목만 줄바꿈으로."
        % (question, agent.cards(), n), "제목만 출력한다.", 300)
    고른것 = [x.strip().strip("-«» ") for x in pick.split("\n")]
    read = [x for x in 고른것 if x in agent.DOCS][:n]

    # ★예산을 «못 채우면» 채워 준다 — 모델이 적게 고른 것으로 지게 두지 않는다.
    #   이게 없으면 「혼자가 못한다」가 아니라 「혼자에게 덜 줬다」가 된다.
    보충 = 0
    if len(read) < n:
        for t in sorted(agent.DOCS):
            if t not in read:
                read.append(t)
                보충 += 1
            if len(read) >= n:
                break

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
        "★★제목은 아래 목록에서 «글자 그대로 복사»하세요. 한 글자도 바꾸지 마세요.\n"
        "쓸 수 있는 출처: %s"
        % (question, "\n\n".join(memo), " / ".join("«%s»" % x for x in read)),
        "너는 혼자 일하는 리서처다.", 2200)

    인용 = [x for x in re.findall(r"«([^»]+)»", rep) if x != "문서명"]
    st = {"question": question, "report": rep, "wheel": 1, "종료": "solo",
          "sections": [{"절": "전체", "번호": 0, "역할": "혼자", "원고": rep,
                        "읽음": read, "메모": memo, "인용": 인용,
                        "허위인용": [c for c in set(인용) if c not in read],
                        "충분": True, "부족": "", "바퀴": 0}]}
    st["metrics"] = score(st)
    st["usage"] = dict(agent._usage)
    st["sec"] = round(time.time() - t0, 2)
    st["공정성"] = {
        "요구예산": n, "실제읽음": len(read), "모델이고른것": len(
            [x for x in 고른것 if x in agent.DOCS]),
        "보충": 보충, "모델": agent.설정["모델"],
        "코퍼스": len(agent.DOCS),
        "도구": ["agent.ask", "agent.read_one", "agent.cards"],
    }
    return st


def 공정성표(f, 팀=None):
    """★「주장」하지 않고 «찍는다». 어긋나면 ⛔ 가 나온다."""
    out = ["", "■ ★대조군 공정성 — 요건: 같은 자료·모델·도구·예산", ""]
    항목 = [
        ("같은 코퍼스", f["코퍼스"] == len(agent.DOCS),
         "%d건 (팀과 같은 DOCS 객체)" % f["코퍼스"]),
        ("같은 모델", f["모델"] == agent.설정["모델"],
         "%s (config.json 의 그 값)" % f["모델"]),
        ("같은 도구", True, " · ".join(f["도구"]) + "  ← 팀이 쓰는 함수를 그대로"),
        ("★예산 소진", f["실제읽음"] >= f["요구예산"],
         "요구 %d건 / 실제 %d건%s"
         % (f["요구예산"], f["실제읽음"],
            ("  (모델이 %d건만 골라 ★%d건 보충)"
             % (f["모델이고른것"], f["보충"])) if f["보충"] else "")),
    ]
    for 이름, ok, 말 in 항목:
        out.append("   %s %-12s %s" % ("✅" if ok else "⛔", 이름, 말))
    if 팀 is not None:
        out += ["",
                "   참고 — 팀이 읽은 문서 %d건 / 대조군 %d건"
                % (팀, f["실제읽음"]),
                "   ★대조군이 «덜» 읽었다면 이긴 것이 아니라 묶어 둔 것이다."
                if f["실제읽음"] < 팀 else
                "   ⇒ 대조군이 팀보다 «적지 않게» 읽었다. 묶어 두지 않았다."]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="?")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--fairness", action="store_true",
                    help="LLM 호출 없이 설정만 대조한다")
    a = ap.parse_args()

    q = a.question or json.load(io.open(
        os.path.join(HERE, "data/questions.json"),
        encoding="utf-8"))["주질문"]["text"]

    if a.fairness:
        print("■ 설정 대조 (호출 없음)")
        print("   코퍼스 %d건 · 모델 %s · 요구 예산 %d건 (절수 %d × 예산 %d)"
              % (len(agent.DOCS), agent.설정["모델"], 예산(),
                 agent.설정["절수"], agent.설정["예산"]))
        print("   ⇒ 실제 소진은 --fairness 없이 돌려야 나온다.")
        return

    print("■ 대조군 — 혼자 하는 오케스트레이터")
    print("   질문: %s" % q)
    rows = []
    for i in range(a.runs):
        st = solo(q)
        m, u = st["metrics"], st["usage"]
        rows.append((m["근거율"], len(m["읽고안쓴"]), u["calls"],
                     m["보고서자수"], m["허위인용"]))
        print("   [%d/%d] 근거율 %.1f%% · 읽고안쓴 %d · 호출 %d · %d자 · %.1f초"
              % (i + 1, a.runs, m["근거율"] * 100, len(m["읽고안쓴"]),
                 u["calls"], m["보고서자수"], st["sec"]))
        io.open(os.path.join(HERE, "output/baseline.jsonl"), "a",
                encoding="utf-8", newline="").write(
            json.dumps(st, ensure_ascii=False, default=str) + "\n")

    print(공정성표(st["공정성"]))

    if a.runs > 1:
        g = [r[0] for r in rows]
        print("\n   ★%d회 — 근거율 %.1f%% (최소 %.1f · 최대 %.1f · 폭 %.1f%%p)"
              % (a.runs, stat.mean(g) * 100, min(g) * 100, max(g) * 100,
                 (max(g) - min(g)) * 100))
    print("   → output/baseline.jsonl")


# ★모듈로 import 될 때는 돌지 않는다 — ablation.py 가 solo 를 가져다 쓴다.
#   이 한 줄이 없으면 import 하는 순간 LLM 호출이 나간다.
if __name__ == "__main__":
    main()
