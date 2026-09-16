# -*- coding: utf-8 -*-
"""★역방향 가드레일 — 「출처에 있는데 답변에 없는 숫자」를 잡는다. (모델 호출 0회)

출처: 같은 기수 이정은님(M1) 회고의 «남은 개선 아이디어»
  「(C) "요약하다 숫자가 증발하는" 문제는 프롬프트 지시만으로는 100% 안 잡힌다
   → 답변 생성 후 "조회 결과에 등장한 핵심 숫자 중 답변에 안 쓰인 게 있는지" 검사하는
   **역방향 가드레일**(지금 것은 "답변에 있는데 출처가 없는 숫자"만 잡지,
   "출처에 있는데 답변에 없는 숫자"는 안 잡는다)을 추가하면 이 클래스의 실패를
   기계적으로 잡을 수 있다.」

  이정은님은 **아이디어로만** 남겼다. 여기서 만들어 «검증»한다.

★내 ② 실패의 최대 유형이 정확히 이것이다 — 7B 측정에서 **must 누락 15건**.
  tools 미호출은 9건인데 must 누락이 15건이다. 즉 **조회는 했는데 안 쓴다.**

★그런데 그냥 만들면 «오탐 폭발»한다
  조회 결과에는 상품 ID · 날짜 · 재고 수량 등 **질문과 무관한 숫자가 훨씬 많다.**
  전부 요구하면 맞는 답변도 걸린다. 10강 더해보기 1 에서 배운 그대로 —
  **가드레일은 «오탐 0건»을 먼저 보여야 쓸 수 있다.**

★그래서 검증을 «모범 답안»으로 한다 (모델 호출 0회)
  정답셋의 reference 는 **사람이 쓴 «맞는» 답변**이다.
  거기에 가드레일을 걸어 «걸리면» 그건 전부 오탐이다.
  ⇒ 오탐률이 낮은 «추출 규칙»을 찾는 것이 이 파일의 일이다.

  python 14_reverse_guardrail.py
"""
import json
import re
import sys
from collections import Counter

from config import BASE, ensure_data

sys.stdout.reconfigure(encoding="utf-8")
ensure_data()

from tools import TOOLS  # noqa: E402

# ─────────────────────────────────────────────────────────────
# 숫자를 뽑는 규칙 — «넓게»부터 «좁게»까지 세 가지를 나란히 잰다
# ─────────────────────────────────────────────────────────────
NUM = re.compile(r"\d[\d,]*")

# ★제외할 «키» — 이건 답변에 쓸 값이 아니다
SKIP_KEYS = {
    "product_id", "order_id", "return_id", "id", "sku",
    "score", "candidates", "query", "resolved_product_id",
}

# ★★필드 ↔ 답변에 나타날 «한국어 말»
#   「답변이 배송비 얘기를 하면서 조회된 배송비 숫자를 안 썼다」만 잡는다.
#   조회 결과 «전체»를 요구하면 오탐이 폭발한다(아래 all/nokey/money 가 그 증거).
#   ⇒ 가드레일이 질문을 이해할 수는 없지만, **답변이 무엇을 말하는지는 볼 수 있다.**
FIELD_KEYWORDS = {
    "free_shipping_threshold": ("무료배송", "무료 배송", "무료"),
    "shortfall":               ("부족", "더 담", "더 구매", "추가로"),
    "shipping_fee":            ("배송비",),
    "base_shipping_fee":       ("배송비",),
    "return_fee":              ("반품비", "반품 배송비", "왕복"),
    "return_window_days":      ("반품 가능", "이내", "기간"),
    "refund_amount":           ("환불",),
    "order_amount":            ("주문 금액", "결제 금액", "주문금액"),
    "price":                   ("가격", "정가", "판매가"),
    "stock":                   ("재고", "남아", "품절"),
    "qty":                     ("수량", "개"),
    "expected_ship_date":      ("출고", "발송"),
    "expected_completion":     ("완료", "예정"),
    "expected_date":           ("예정", "입고"),
    "tracking_no":             ("송장", "운송장", "운송"),
}


def walk(obj, key=None):
    """조회 결과 JSON 을 훑어 (키, 값) 쌍을 낸다."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, k)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v, key)
    else:
        yield key, obj


def extract(results, mode, text=""):
    """조회 결과에서 «답변에 쓰여야 할» 숫자를 뽑는다.

    mode = "all"     모든 숫자 (가장 넓다 — 오탐이 얼마나 나는지 보려고)
           "nokey"   ID 류 키를 뺀 것
           "money"   금액·기간처럼 «단위가 붙는» 값만
           "linked"  ★답변이 «그 항목을 말했을 때»만 그 필드 값을 요구 (가장 좁다)
    """
    got = set()
    for k, v in walk(results):
        if v is None or isinstance(v, bool):
            continue
        key = (k or "").lower()
        if mode == "linked":
            kws = FIELD_KEYWORDS.get(key)
            if not kws or not any(w in text for w in kws):
                continue        # 답변이 그 얘기를 «안 했으면» 요구하지 않는다
        elif mode != "all" and any(s in key for s in SKIP_KEYS):
            continue
        s = str(v)
        # ★날짜는 «조각내지» 않는다 — 2026-08-24 를 2026·08·24 세 숫자로 세면
        #   답변이 「8월 24일」이라 써도 «안 썼다»가 된다. 내 1차 규칙의 결함이었다.
        if mode in ("money", "linked") and re.search(r"\d{4}-\d{2}-\d{2}", s):
            continue
        for m in NUM.findall(s):
            digits = m.replace(",", "")
            if not digits.isdigit():
                continue
            if mode == "linked" and len(digits) > 8:
                continue        # 송장번호 같은 «식별자»는 답변에 쓸 값이 아니다
            if mode == "money":
                # ★금액·일수로 쓰일 만한 것만 — 4자리 이상(금액) 또는 1~2자리(일수)
                #   그리고 «날짜 문자열 안의» 숫자는 뺀다 (2026-08-20 → 2026·08·20)
                if re.search(r"\d{4}-\d{2}-\d{2}", s):
                    continue
                if not (len(digits) >= 4 or len(digits) <= 2):
                    continue
            got.add(digits)
    return got


# ★값이 0 일 때 답변이 쓰는 «말» — 숫자 대신 이렇게 적는 게 «맞다»
ZERO_WORDS = ("품절", "없습니다", "없음", "무료", "발생하지 않", "부과되지 않",
              "들지 않", "면제", "0원")


def in_answer(num, text):
    """답변이 그 숫자를 «썼는가» — 콤마 표기(50,000)와 맨숫자(50000) 둘 다 본다."""
    # ★0 은 «말»로 쓰는 것이 맞다 — stock:0 → 「품절」 · return_fee:0 → 「발생하지 않습니다」
    #   실측에서 오탐 5건 중 3건이 이것이었다. 숫자를 요구하면 «맞는 답»을 막는다.
    if num == "0" and any(w in text for w in ZERO_WORDS):
        return True
    if num in text.replace(",", ""):
        return True
    # 5만원 같은 «한국어 축약»도 쓴 것으로 본다 (채점기 must 는 못 보지만
    # 여기서는 «사람이 읽기에 썼는가»를 판정한다 — 오탐을 줄이려고)
    if len(num) >= 5 and num.endswith("0000"):
        man = num[:-4]
        if re.search(man + r"\s*만", text):
            return True
    return False


def load_gold():
    p = BASE / "answer_goldenset_multiturn.json"
    return json.loads(p.read_text(encoding="utf-8"))["conversations"]


def call_tools(expect):
    """expect 의 tool_args 로 도구를 «실제로» 부른다 — 조회 결과를 얻으려고."""
    out = {}
    for name, args in (expect.get("tool_args") or {}).items():
        fn = TOOLS.get(name)
        if not fn:
            continue
        try:
            out[name] = fn(**args)
        except Exception as e:                       # noqa: BLE001
            out[name] = {"_error": str(e)}
    return out


if __name__ == "__main__":
    convs = load_gold()

    # ★첫 턴만 — ② 지표가 첫 턴 32건을 쓰기 때문이다
    cases = []
    for c in convs:
        for t in c["turns"]:
            e = t.get("expect")
            if e and t.get("role") != "customer":
                cases.append((c["conv_id"], e))
                break
            if e:
                cases.append((c["conv_id"], e))
                break
    cases = [(cid, e) for cid, e in cases if e.get("tool_args")]

    print("=== ★역방향 가드레일 — 모범 답안으로 «오탐»을 먼저 잰다 ===")
    print("   출처: 이정은님(M1) 회고의 「남은 개선 아이디어」 — 아이디어로만 남아 있던 것")
    print("   대상: 정답셋 첫 턴 중 «조회가 필요한» %d건" % len(cases))
    print()
    print("   ★논리: reference 는 «사람이 쓴 맞는 답변»이다.")
    print("     거기 걸리는 건 «전부 오탐»이다. 오탐이 많은 규칙은 쓸 수 없다.")
    print()

    rows = []
    for mode in ("all", "nokey", "money", "linked"):
        hit_cases = 0
        total_missing = 0
        detail = []
        for cid, e in cases:
            res = call_tools(e)
            ref = e.get("reference") or ""
            want = extract(res, mode, ref)
            missing = sorted(n for n in want if not in_answer(n, ref))
            if missing:
                hit_cases += 1
                total_missing += len(missing)
                detail.append((cid, missing[:6]))
        rows.append((mode, hit_cases, total_missing, detail))

    print("%-8s %-14s %-14s %s" % ("규칙", "걸린 대화", "빠졌다는 숫자", "판정"))
    print("─" * 66)
    for mode, hc, tm, _ in rows:
        verdict = ("✅ 쓸 수 있다" if hc == 0
                   else ("⚠ 오탐 %d건" % hc if hc <= 3 else "⛔ 오탐 폭발"))
        print("%-8s %2d/%-11d %-14d %s" % (mode, hc, len(cases), tm, verdict))
    print()

    for mode, hc, tm, detail in rows:
        if not detail:
            continue
        print("[%s] 모범 답안이 «안 쓴» 숫자 — 이게 전부 오탐이다" % mode)
        for cid, ms in detail[:8]:
            print("   %-7s %s" % (cid, ", ".join(ms)))
        if len(detail) > 8:
            print("   … 외 %d건" % (len(detail) - 8))
        print()

    # ★그래서 무엇을 쓸 수 있나
    best = min(rows, key=lambda r: (r[1], r[2]))
    print("══ 결론 ══")
    print("   가장 좁은 규칙(%s)에서도 오탐 %d/%d건이 난다."
          % (best[0], best[1], len(cases)))
    if best[1] == 0:
        print("   ⇒ ★오탐 0건 — 이 규칙은 «답변 재생성 트리거»로 쓸 수 있다.")
    else:
        print("   ⇒ ★오탐이 남는다. 이대로 «차단»에 쓰면 맞는 답변을 막는다.")
        print("     10강이 말한 그대로 — 가드레일은 «막는 것»보다 «안 막는 것»이 어렵다.")
        print("     ⇒ 차단이 아니라 **경고**로 쓰고, 재생성 «한 번»만 유도하는 게 맞다.")
    print()
    print("   ※ 이 검증을 «모델 답변»이 아니라 «모범 답안»으로 한 이유 —")
    print("     모델 답변으로 재면 «모델이 못 쓴 것»과 «규칙이 과한 것»이 섞여 못 가린다.")
