# -*- coding: utf-8 -*-
"""★「모르겠으면 넘기기」 — 카테고리 «선택»과 «넘길지»를 분리한다.

요건(노드5)이 명시한 것
  구조도:  입력 → ① 판정 → ② 근거 조립 → ③ 답변 → ④ 검증
                    ↓
              모르겠으면 넘기기
  필수구현 3: 「카테고리를 고르는 일과, 확신이 없을 때 넘기는 판단을 «분리»한다」

★왜 «별도 파일»인가 — 어제 노드4 에서 본 것 때문이다
  노드4 는 이 둘이 router.py 안에 섞여 있었고, 게다가:
```
    router.py:16   from config import CONF_THRESHOLD   # 가져오고
    router.py:50   CONF_THRESHOLD = 0.5                # ★바로 아래서 덮어쓴다
```
  config.py 주석은 「여기 값만 바꿔도 동작이 달라진다」고 되어 있었지만
  **손잡이가 끊겨 있었다.** 임계값을 조정해 본 사람은 «효과가 없었던 게 아니라
  바뀐 적이 없는» 것이었다.
  ⇒ 그래서 여기서는 **임계값을 «인자로» 받는다.** 모듈 전역에 두지 않는다.
    덮어쓸 자리가 없으면 끊길 수도 없다.

★네 갈래로 나눈 이유 — 고칠 방법이 «다르기» 때문이다
```
  CONTINUE  그대로 답한다
  REFUSE    이 데스크가 «다루지 않는» 주제다      → 경계가 새면 라우터를 고친다
  ESCALATE  다루는 주제인데 «자료에 없다»         → 많아지면 «지식원»을 늘린다
  ASK       후보가 여럿이라 «되묻는다»            → 많아지면 «질문을 좁히게» 유도한다
```
  넷을 합치면 **「안 하는 것」·「모르는 것」·「못 정한 것」이 섞인다.**
  ⚠ 1차에는 ASK 가 없어서 `get_fact("공룡 멸종")` 의 «동점»을 «없음»으로 보고
    넘겨 버렸다. 자료는 있는데 어느 것인지 못 정했을 뿐이었다.
"""

DEFAULT_THRESHOLD = 0.55


def _ambiguous(r):
    """후보가 여럿이라 «못 정한» 상태인가."""
    return isinstance(r, dict) and bool(r.get("ambiguous"))


def _is_empty(r):
    """조회 결과가 «사실상 비었나». ★애매(ambiguous)는 «비었다»가 아니다."""
    if not isinstance(r, dict):
        return not r
    if r.get("ambiguous"):
        return False                 # 자료는 있다. 어느 것인지 못 정했을 뿐이다
    if r.get("found") is False:
        return True
    if "count" in r and not r["count"]:
        return True
    if "results" in r and not r["results"]:
        return True
    return False


def gate(route, conf, used=None, threshold=DEFAULT_THRESHOLD):
    """어떻게 처리할지 정한다. ★임계값은 «인자»다 — 전역에 두지 않는다.

    Args:
        route: 라우터가 고른 카테고리
        conf:  라우터의 확신도 0~1
        used:  조회 결과. None 이면 «아직 조회 전»이라는 뜻
        threshold: 이 값 «미만»이면 넘긴다

    Returns:
        (결정, 이유). 결정은 CONTINUE · REFUSE · ESCALATE · ASK 중 하나.
        이유는 «무엇을 고쳐야 하는지»를 가리켜야 한다.
    """
    if route == "OTHER":
        return "REFUSE", "범위 밖 — 이 데스크가 다루지 않는 주제다"
    if conf < threshold:
        return "ESCALATE", ("확신도 %.2f < %.2f — 어느 카테고리인지 못 정했다"
                            % (conf, threshold))
    if used is None:
        return "CONTINUE", ""            # 아직 조회 전이다
    if not used:
        return "ESCALATE", "근거 없음 — 도구를 부르지 못했다"
    if any(_ambiguous(v) for v in used.values()):
        return "ASK", "후보가 여럿 — 어느 것인지 되묻는다"
    if all(_is_empty(v) for v in used.values()):
        return "ESCALATE", "근거 없음 — 조회했으나 자료에 없다"
    return "CONTINUE", ""


def candidates(used):
    """ASK 할 때 보여 줄 후보 목록."""
    out = []
    for v in (used or {}).values():
        if isinstance(v, dict):
            out.extend(v.get("candidates") or [])
    return [c if isinstance(c, str) else c.get("name", "") for c in out][:4]


ESCALATE_REPLY = (
    "자료에서 확인되지 않습니다. 저는 수집한 최근 발표와 기준 사실 카드로만 답하며, "
    "이 문의는 두 곳 모두에 근거가 없습니다.")

REFUSE_REPLY = (
    "저는 관측·발굴·화석 연구에서 나온 자료로만 답합니다. 그 주제는 다루지 않습니다.")


def ask_reply(used):
    cs = candidates(used)
    tail = (" 후보: %s" % ", ".join(cs)) if cs else ""
    return "어느 쪽을 말씀하시는지 알려주시면 정확히 답해 드리겠습니다.%s" % tail


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("=== 판단 — 경우별 ===")
    cases = [
        ("PALEO", 0.9, {"get_fact": {"found": True, "claim": "x"}}, "정상"),
        ("OTHER", 0.9, {}, "범위 밖"),
        ("SPACE", 0.3, {"get_fact": {"found": True}}, "확신도 낮음"),
        ("SPACE", 0.9, {}, "도구를 아예 안 부름"),
        ("SPACE", 0.9, {"search_article": {"count": 0, "results": []}}, "조회 0건"),
        ("ARCHAEO", 0.9, {"get_fact": {"found": False}}, "사실카드에 없음"),
        ("PALEO", 0.9, {"get_fact": {"found": False, "ambiguous": True,
                                     "candidates": ["공룡 멸종 시점", "공룡 멸종 원인"]}},
         "★후보가 여럿"),
    ]
    for rt, cf, us, name in cases:
        dec, why = gate(rt, cf, us)
        print("   %-16s → %-9s %s" % (name, dec, why))
    print()
    print("   ★임계값은 «인자»다. 바꿔 보면:")
    for th in (0.3, 0.55, 0.95):
        dec, _ = gate("SPACE", 0.5, {"get_fact": {"found": True}}, threshold=th)
        print("      threshold=%.2f · conf=0.50 → %s" % (th, dec))
    print("   ⇒ 손잡이가 «실제로» 돈다. 어제 노드4 는 이게 끊겨 있었다.")
