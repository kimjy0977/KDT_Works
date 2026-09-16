# -*- coding: utf-8 -*-
"""★채점기를 «채점한다» — 11강 자기 검증의 구멍을 메운다. (키 불필요)

11강이 넣어 둔 자기 검증은 이렇게 생겼다:

    score_turn(expect, expect["reference"], expect["tools"], expect["action"])
                                            ^^^^^^^^^^^^^^  ^^^^^^^^^^^^^^^^
                                            정답 그대로      정답 그대로

즉 **「모범 답안 문장이 must/forbid 를 만족하는가」**만 본다.
그런데 실제 채점은 그 사이에 **action 판정 로직**이 하나 더 있다:

    if   get_order_status.is_external_channel -> OUT_OF_SCOPE
    elif not results and 되묻는 문장          -> ASK
    else                                     -> ANSWER

**expect 가 요구하는 대로 «행동»했을 때, 이 로직이 expect["action"] 을 돌려주는가?**
그걸 아무도 안 본다. 안 돌려주면 그 문항은 **무엇을 해도 통과할 수 없다.**

  python 02_scorer_audit.py
"""
import re
import sys

import json

from config import BASE, ensure_data
from evaluate import AUTO_ACTIONS, load_cases, score_turn

sys.stdout.reconfigure(encoding="utf-8")

ASK_PAT = r"\?|주시겠|알려주|말씀해"

ensure_data()
_MD = json.loads((BASE / "mockdata_modumall.json").read_text(encoding="utf-8"))
ORDERS = {o["order_id"]: o for o in _MD.get("orders", [])}


def judge(tools_called, answer, external=False):
    """evaluate.py run_case() 의 판정 로직을 «그대로» 옮긴 것."""
    if external:
        return "OUT_OF_SCOPE"
    if not tools_called and re.search(ASK_PAT, answer):
        return "ASK"
    return "ANSWER"


def is_external(e):
    """★도구를 부르면 «실제로» is_external_channel=true 가 오는가 — 목데이터로 판정한다.

    처음엔 이 값을 False 로 «고정»해 두었다가 C-008 을 오탐으로 잡았다.
    O-1009 는 실제로 외부 채널 주문이라 정상 통과하는 문항이었다.
    ⇒ 노드3에서 겪은 것과 같은 자리 — **«아니다»를 판정하는 검사가 정상을 떨어뜨린다.**
    """
    if "get_order_status" not in e.get("tools", []):
        return False
    oid = (e.get("tool_args", {}).get("get_order_status", {}) or {}).get("order_id")
    if not oid:
        return False
    return bool(ORDERS.get(oid, {}).get("is_external_channel"))


def audit(case):
    """이 문항은 «expect 대로 완벽히 행동해도» 통과하는가."""
    e = case["expect"]
    ref = e["reference"]
    need = e.get("tools", [])
    ext = is_external(e)

    # expect 가 요구하는 대로 도구를 부른 «모범 시행»
    act = judge(need, ref, external=ext)
    ok, fails = score_turn(e, ref, need, act)
    if ok:
        return None

    # 통과 못 했다면 — 도구를 안 부르는 쪽은 어떤가(둘 다 막히면 «구조적 불가»)
    act2 = judge([], ref)   # 도구를 안 불렀으니 외부채널 판정도 발동하지 않는다
    ok2, fails2 = score_turn(e, ref, [], act2)
    return {"conv": case["conv_id"], "expect": e["action"],
            "with_tools": (act, ok, fails), "no_tools": (act2, ok2, fails2),
            "impossible": not ok2, "question": case["question"]}


if __name__ == "__main__":
    ensure_data()
    cases = load_cases()
    scored = [c for c in cases if c["expect"]["action"] in AUTO_ACTIONS]

    print("=== 채점기 «행동 재현» 감사 ===")
    print("   대상 %d건 (자동 채점 대상 · 전체 %d건 중)" % (len(scored), len(cases)))
    print("   묻는 것: 「expect 대로 «행동»했을 때 채점을 통과하는가」")
    print()

    bad = [r for r in (audit(c) for c in scored) if r]
    impossible = [r for r in bad if r["impossible"]]

    print("   ⚠ 모범 시행으로도 통과 못 하는 문항  %d건" % len(bad))
    print("   ⛔ ★두 경로 «모두» 막힌 문항(구조적 불가)  %d건" % len(impossible))
    print()

    for r in bad:
        mark = "⛔ 구조적 불가" if r["impossible"] else "⚠ 한쪽만 막힘"
        print("── %s  %s  (기대 %s)" % (r["conv"], mark, r["expect"]))
        print("   Q: %s" % r["question"][:64])
        a, ok, f = r["with_tools"]
        print("   · 도구를 «부르면»   판정=%-13s %s" % (a, "통과" if ok else "; ".join(f)[:70]))
        a2, ok2, f2 = r["no_tools"]
        print("   · 도구를 «안 부르면» 판정=%-13s %s" % (a2, "통과" if ok2 else "; ".join(f2)[:70]))
        print()

    n = len(scored)
    print("=" * 64)
    if impossible:
        top = n - len(impossible)
        print("★도달 가능한 최고 점수 = %d/%d (%.1f%%)" % (top, n, 100 * top / n))
        print("  퍼실 제시 기준선 18/32 (56%%) 에는 이 %d건이 «이미 실패로» 들어가 있다."
              % len(impossible))
        print()
        print("★11강의 자기 검증이 이걸 못 잡은 이유")
        print("  자기 검증은 tools·action 을 «정답 그대로» 넣어 채점한다.")
        print("  그래서 «문장이 must/forbid 를 만족하는가»는 보지만,")
        print("  «그렇게 행동했을 때 action 판정이 기대와 같은가»는 «안 본다».")
        print("  ⇒ 검사는 있었는데, 검사가 «보는 자리»가 한 겹 얕았다.")
    else:
        print("✅ 모든 문항이 모범 시행으로 통과한다 — 채점기에 구조적 모순이 없다.")
