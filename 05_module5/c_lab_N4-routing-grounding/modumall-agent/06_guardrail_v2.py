# -*- coding: utf-8 -*-
"""★10강 「더 해보기」 1 — 확답 금지 패턴을 잡는다. (키 불필요 · 모델 호출 0회)

10강이 정직하게 인정한 가드레일의 첫 번째 한계:
  「**숫자가 아닌 오류는 잡지 못한다.** "개별 구매 가능합니다" 라고 잘못 답한 경우
   숫자가 없으므로 통과한다.」

그리고 10강 퀴즈가 그 실물을 든다 —
  「'재입고 예정일은 9월 15일입니다' 가 가드레일을 통과했다면?」
  → 날짜 숫자는 조회 결과에 있으니 **출처가 있다.** 문제는 값이 아니라 **«단정했다»** 는 것.
  → 매뉴얼 §2.5: `is_confirmed` 가 false 면 **예정일을 확답하면 안 된다.**

  ⇒ 그래서 «확답 패턴»을 정규식으로 잡고, 조회 결과의 플래그와 대조한다.

  ★그런데 10강이 같은 자리에서 경고한다 —
   「규칙을 하나 추가할 때마다 **오탐이 늘어나는 교환 관계**도 함께 관찰하게 됩니다.」
   ⇒ 그래서 이 파일은 **정상 답변(모범답안)에서 오탐이 나는지 반드시 함께 센다.**

  python 06_guardrail_v2.py
"""
import re
import sys

from config import ensure_data
from evaluate import AUTO_ACTIONS, load_cases
from guardrail import guardrail

sys.stdout.reconfigure(encoding="utf-8")

# ★확답 패턴 — 「언제 온다/된다」를 단정하는 말투
CONFIRM_PAT = [
    (r"(예정일|입고일|재입고).{0,12}(은|는|이|가)?\s*\d+[월일]", "재입고일 확답"),
    (r"\d+\s*월\s*\d+\s*일(에|까지)?\s*(입고|재입고|도착|배송)", "날짜 확답"),
    (r"(입고|재입고)(됩니다|될 예정입니다|예정입니다)", "입고 확답"),
]
# ★귀책·상태를 단정하는 말투 (검품 전에는 쓰면 안 된다 — 매뉴얼 §6.4)
BLAME_PAT = [
    (r"(고객님|고객)\s*(부담|책임)(입니다|이십니다|하셔야)", "귀책 단정"),
    (r"(배송비|반품비).{0,10}(무료|면제)(입니다|됩니다)", "비용 단정"),
    (r"(배송|출고)\s*(완료|됐습니다|되었습니다)", "상태 단정"),
]


def guardrail_v2(answer, tool_results=None, min_check=1000):
    """기존 가드레일 + 확답 패턴. 원본 guardrail.py 는 «건드리지 않는다»."""
    res = guardrail(answer, tool_results, min_check)
    res = {**res, "violations": list(res["violations"])}
    tr = tool_results or {}

    # ① 재입고 확답 — is_confirmed 가 False 인데 날짜를 말했나
    restock = tr.get("get_restock_info") or {}
    if isinstance(restock, dict) and restock.get("is_confirmed") is False:
        for pat, label in CONFIRM_PAT:
            if re.search(pat, answer):
                res["violations"].append(
                    {"type": "확답 금지 위반", "detail": "%s — is_confirmed=false" % label})
                break

    # ② 귀책·상태 단정 — 검품 결과가 아직 null 인데 단정했나
    ret = tr.get("get_return_status") or {}
    if isinstance(ret, dict) and "inspection_result" in ret and ret.get("inspection_result") is None:
        for pat, label in BLAME_PAT:
            if re.search(pat, answer):
                res["violations"].append(
                    {"type": "미확정 단정", "detail": "%s — inspection_result=null" % label})
                break

    res["ok"] = not res["violations"]
    return res


if __name__ == "__main__":
    ensure_data()

    print("=== ① 10강 퀴즈의 그 문장을 실제로 잡는가 ===")
    ans = "재입고 예정일은 9월 15일입니다. 그때 다시 확인해 주세요."
    tr_unconfirmed = {"get_restock_info": {"product_id": "P4002", "is_confirmed": False,
                                           "expected_date": "2026-09-15"}}
    a = guardrail(ans, tr_unconfirmed)
    b = guardrail_v2(ans, tr_unconfirmed)
    print("   답변: %s" % ans)
    print("   기존 가드레일: %s" % ("통과 ← 10강이 지적한 «못 잡는» 자리" if a["ok"] else "차단"))
    print("   ★확장 가드레일: %s" % ("통과" if b["ok"] else
                                "차단 — " + b["violations"][-1]["detail"]))
    print()

    print("=== ② 확정된 건은 «통과»해야 한다 — 오탐 점검 ===")
    tr_confirmed = {"get_restock_info": {"product_id": "P4001", "is_confirmed": True,
                                         "expected_date": "2026-09-15"}}
    c = guardrail_v2(ans, tr_confirmed)
    print("   같은 문장 · is_confirmed=true → %s" % ("✅ 통과(정상)" if c["ok"] else "❌ 오탐"))
    print()

    print("=== ③ 검품 전 귀책 단정 ===")
    ans2 = "확인해 보니 배송비는 고객님 부담입니다."
    tr_null = {"get_return_status": {"return_id": "R-2001", "inspection_result": None,
                                     "fault_party": None}}
    d = guardrail(ans2, tr_null)
    e = guardrail_v2(ans2, tr_null)
    print("   답변: %s" % ans2)
    print("   기존: %s · ★확장: %s"
          % ("통과" if d["ok"] else "차단",
             "통과" if e["ok"] else "차단 — " + e["violations"][-1]["detail"]))
    print()

    print("=== ★④ 오탐 교환 관계 — 10강이 경고한 자리 ===")
    print("   「규칙을 하나 추가할 때마다 오탐이 늘어나는 교환 관계도 함께 관찰하게 됩니다」")
    print()
    cases = [c for c in load_cases() if c["expect"]["action"] in AUTO_ACTIONS]
    # 모범 답안 + 「조회 결과가 다 확정된 상태」로 걸어 본다 → 여기서 걸리면 «오탐»
    ok_ctx = {"get_restock_info": {"is_confirmed": True},
              "get_return_status": {"inspection_result": "하자 확인"}}
    fp_old = [c["conv_id"] for c in cases if not guardrail(c["expect"]["reference"], ok_ctx)["ok"]]
    fp_new = [c["conv_id"] for c in cases if not guardrail_v2(c["expect"]["reference"], ok_ctx)["ok"]]
    print("   모범답안 %d건 · 조회 결과가 «확정»인 맥락에서:" % len(cases))
    print("      기존 가드레일 위반 %d건" % len(fp_old))
    print("      ★확장 가드레일 위반 %d건" % len(fp_new))
    added = [x for x in fp_new if x not in fp_old]
    print("      ⇒ 확장으로 «새로» 걸린 것 %d건 %s" % (len(added), added if added else ""))
    if not added:
        print("      ✅ 오탐이 늘지 않았다 — 플래그를 함께 보기 때문이다.")
        print("         («확답 패턴»만 보면 정상 답변도 걸린다. 조회 결과와 «대조»해야 한다)")
    print()

    print("=== ⑤ 그래도 남는 한계 ===")
    print("   · 숫자도 날짜도 없는 오류 — 「개별 구매 가능합니다」 는 여전히 못 잡는다")
    print("   · 패턴을 늘릴수록 오탐 위험이 는다 ⇒ 10강 결론대로 «차단»보다")
    print("     «경고 후 재생성 또는 이관»으로 쓰는 것이 안전하다")
