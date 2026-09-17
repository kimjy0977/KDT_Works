# -*- coding: utf-8 -*-
"""★채점기 — 그리고 «채점기 자신»을 검증한다.

어제 배운 것 (노드4)
  · 정답셋 32건 중 **2건이 «무엇을 해도 통과 불가»**였다(C-009·C-034)
  · 조 공유에서 채점기 버그가 넷 나왔다 — 둘씩 서로 다른 것이었다
  · 11강의 자기 검증이 그걸 «못 잡은» 이유 — expect 의 tools·action 을
    «정답 그대로» 넣어 채점해서 **action 판정 로직을 안 거쳤다**
  ⇒ 그래서 여기서는 **모범 답안을 «실제 판정 경로»로** 통과시킨다.

  python score_desk.py --self     # ★채점기 자기 검증
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent

# ★되묻기 판정 — 「물음표로 판정하면 클로저에 오판된다」는 지적이 있었다.
#   「추가로 궁금한 점이 있으신가요?」 같은 마무리 문장을 «먼저» 걷어낸다.
CLOSER = re.compile(
    r"(추가로|더|다른)\s*(궁금|문의|질문)[^.!?]*[?？]|"
    r"도움이\s*되셨[^.!?]*[?？]|"
    r"더\s*알고\s*싶[^.!?]*[?？]")
ASK_PAT = re.compile(r"[?？]|어느\s|무엇을\s*말씀|구체적으로\s*알려")
REFUSE_PAT = re.compile(r"다루지\s*않|답(변)?(을|드리지)?\s*(드리지\s*)?않|"
                        r"드리지\s*않습니다|답할\s*수\s*없")


ESCALATE_PAT = __import__("re").compile(
    r"확인되지\s*않|자료에\s*없|근거가\s*없|찾을\s*수\s*없")


def judge_action(text, used):
    """★행동 판정 — 답변 «문장»과 «부른 도구»로 정한다.

    순서가 중요하다:
      REFUSE    «다루지 않는» 주제라 거절     — 먼저 본다
      ESCALATE  다루는 주제인데 «자료에 없다» — 그 다음
      ASK       되묻는다
      ANSWER    답한다

    ★REFUSE 와 ESCALATE 를 «합치면» 「안 하는 것」과 「모르는 것」이 섞인다.
      고칠 방법이 다르다 — ESCALATE 가 많으면 «지식원을 늘려야» 하고,
      REFUSE 가 적으면 «경계가 샌» 것이다.
    """
    body = CLOSER.sub(" ", text or "")          # ★클로저를 먼저 걷어낸다
    if REFUSE_PAT.search(body):
        return "REFUSE"
    if ESCALATE_PAT.search(body):
        return "ESCALATE"
    if not used and ASK_PAT.search(body):
        return "ASK"
    return "ANSWER"


def norm(s):
    """★«표현»이 아니라 «사실»을 보게 만든다 (노드5 요건).

    요건: 「표현이 같을 필요는 없으니 채점기에 «표현이 아니라 사실»을 보라고 명시한다」

    실측으로 드러난 세 가지 (통합 파이프라인 1차):
      · must 「동료평가」  vs 답변 「동료 평가」    → ★띄어쓰기
        (어제 조 공유에서도 「배송완료 vs 배송 완료」로 같은 것이 나왔다)
      · must 「6,600만」   vs 답변 「6600만」       → 콤마
      · 전각·반각, 대소문자

    ⇒ 공백·콤마를 걷고 소문자로 맞춘 뒤 비교한다.
      ⚠ 공백을 걷으면 «다른 낱말이 붙어» 우연히 맞을 수 있다.
        그래서 must 는 짧은 토막(2자 이하)을 쓰지 않는다 — 골든셋 작성 규칙이다.
    """
    t = re.sub(r"(?<=\d),(?=\d)", "", s or "")
    return re.sub(r"\s+", "", t).lower()


def score_case(case, text, used):
    """4축 — action · tools · must · forbid. 하나라도 틀리면 통과가 아니다.

    ★도구 호출은 «집합이 정확히 일치»해야 한다 (노드5 요건).
      「실제로 호출한 도구 집합이 기대 도구와 정확히 일치하면 1점.
       필요한 근거를 안 읽은 것, **관련 없는 근거를 훑은 것**,
       넘겨야 하는데 지어낸 것이 이 하나로 다 걸린다」

      ⚠ 1차 채점기는 «미호출»만 봤다. 그래서 **조회 과잉이 안 걸렸다** —
        오늘 최대 실패 원인이 바로 그것이었는데(get_fact+search_article+get_article 을
        셋 다 불러 [신설]이 답변을 오염시켰다) 점수에 잡히지 않았다.
    """
    fails = []
    act = judge_action(text, used)
    if act != case["action"]:
        fails.append("action: 기대 %s != 실제 %s" % (case["action"], act))
    want, got = set(case.get("tools", [])), set(used)
    for t in sorted(want - got):
        fails.append("tools 미호출: %s" % t)
    for t in sorted(got - want):
        fails.append("tools 과잉호출: %s" % t)
    nt = norm(text)
    # ★must 항목은 «문자열» 또는 «동의어 목록»이다.
    #   목록이면 하나라도 있으면 통과한다 — 「논쟁」과 「확정되지 않았다」는 같은 사실이다.
    for m in case.get("must", []):
        alts = m if isinstance(m, list) else [m]
        if not any(norm(a) in nt for a in alts):
            fails.append('must 누락: "%s"' % (alts[0] if len(alts) == 1
                                              else "|".join(alts)))
    for f in case.get("forbid", []):
        alts = f if isinstance(f, list) else [f]
        hit = [a for a in alts if norm(a) in nt]
        if hit:
            fails.append('forbid 위반: "%s"' % hit[0])
    return (not fails), fails, act


def report(rows, secs):
    """rows = [(case, text, used, err), ...]"""
    import guard_desk
    ok_n = 0
    kinds = Counter()
    acts = Counter()
    guards = Counter()
    fail_rows = []
    for case, text, used, err in rows:
        ok, fails, act = score_case(case, text, used)
        ok_n += ok
        acts[(case["action"], act)] += 1
        for f in fails:
            kinds[f.split(":")[0]] += 1
        g = guard_desk.check(text, used)
        guards["ok" if g["ok"] else g["violations"][0]["type"]] += 1
        if not ok or not g["ok"]:
            fail_rows.append((case, text, used, fails, g))

    n = len(rows)
    print()
    print("   ⇒ 통과 %d / %d  (%.1f%%) · %.1f초" % (ok_n, n, 100 * ok_n / n, secs))
    print()
    print("[행동 판정]  기대 → 실제")
    for (exp, got), c in sorted(acts.items()):
        mark = "  " if exp == got else "★"
        print("   %s%-12s → %-12s %d건" % (mark, exp, got, c))
    print()
    print("[실패 유형]")
    for k, v in kinds.most_common():
        print("   %-14s %d건" % (k, v))
    if not kinds:
        print("   없음")
    print()
    print("[가드레일]")
    for k, v in guards.most_common():
        print("   %-18s %d건" % (k, v))
    if fail_rows:
        print()
        print("[실패 사례]")
        for case, text, used, fails, g in fail_rows[:8]:
            print("  %s %s" % (case["id"], case["question"][:38]))
            print("      도구: %s" % (",".join(used) or "(없음)"))
            if fails:
                print("      실패: %s" % "; ".join(fails))
            if not g["ok"]:
                print("      ★가드레일: %s" % g["violations"][0]["detail"][:70])
            print("      답변: %s" % (text or "")[:110].replace("\n", " "))


# ─────────────────────────────────────────────────────────
# ★채점기 «자기 검증» — 어제 최대 교훈
# ─────────────────────────────────────────────────────────
def self_check():
    """모범 답안이 «실제 판정 경로»를 통과하는가.

    ⚠ expect 의 tools·action 을 «정답 그대로» 넣으면 안 된다.
      어제 11강 검증이 그렇게 해서 **action 판정 로직을 안 거쳤고**,
      그 결과 「무엇을 해도 통과 불가」인 문항 2건을 놓쳤다.
    ⇒ 여기서는 tools 는 정답을 쓰되(도구 호출은 모델 몫이라 재현할 수 없다),
      **action 은 «모범 답안 문장으로» 판정**해 실제 로직을 거치게 한다.
    """
    import guard_desk
    gold = json.loads((HERE / "golden.json").read_text(encoding="utf-8"))["cases"]
    print("=== ★채점기 자기 검증 — 모범 답안 %d건 ===" % len(gold))
    print("   모범 답안은 «사람이 쓴 맞는 답»이다. 여기서 걸리면 «채점기»가 틀린 것이다.")
    print()
    bad = 0
    import tools_desk
    for c in gold:
        ref = c["reference"]
        # ★«실제로» 도구를 부른다 — 빈 dict 를 넣으면 가드레일이 데이터를 못 본다.
        #   1차에 그렇게 해서 「출처 불명 수치」 오탐이 5건 났다.
        #   어제 11강 자기검증이 실패한 것과 «같은 구조»였다 —
        #   정답을 형식적으로만 넣고 «실제 판정 경로»를 안 거쳤다.
        used = {}
        for t, kw in (c.get("tool_args") or {}).items():
            fn = tools_desk.TOOLS.get(t)
            if fn:
                try:
                    used[t] = fn(**kw)
                except Exception as e:                  # noqa: BLE001
                    used[t] = {"_error": str(e)}
        ok, fails, act = score_case(c, ref, used)       # ★action 은 «문장으로» 판정된다
        g = guard_desk.check(ref, used)
        if not ok or not g["ok"]:
            bad += 1
            print("   ⛔ %s %s" % (c["id"], c["question"][:34]))
            for f in fails:
                print("        %s" % f)
            if not g["ok"]:
                print("        ★가드레일 오탐: %s" % g["violations"][0]["detail"][:60])
    print()
    if bad:
        print("   ★%d건이 걸렸다 — «정답셋이나 채점기»를 고쳐야 한다." % bad)
        print("     모범 답안이 통과 못 하면 모델은 «절대» 통과 못 한다.")
        return 1
    print("   ✅ %d건 전부 통과 — 도달 가능한 정답셋이다." % len(gold))
    return 0


if __name__ == "__main__":
    if "--self" in sys.argv:
        sys.exit(self_check())
    print("사용법: python score_desk.py --self")
