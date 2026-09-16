# -*- coding: utf-8 -*-
"""★12강 한계 ① — 엔티티 링킹을 고친다. (키 불필요 · 모델 호출 0)

12강이 한계로 적은 첫 번째:
  「**엔티티 링킹이 얕습니다.** `search_product` 는 **토큰 겹침**으로만 찾습니다.
   "요일팬티 세트"가 "브라·팬티 세트"와 **동점**이 되는 문제가 남아 있어요.」

★원본의 실제 결함 — 코드를 읽어야 보인다
```python
n = sum(1 for t in qt if t in flat or any(t in x or x in t for x in nt))
                                          ^^^^^^^^^^^^^^^^^^^^^^^^
```
`t in x or x in t` — **한 글자만 겹쳐도 «완전 일치»와 같은 1점**을 준다.
그래서 「팬티」가 「요일팬티」와도 「브라·팬티」와도 만점이 되고, **동점이 된다.**
그리고 점수는 `n / len(qt)` 라 **«질의어 기준»** 이다 —
상품명이 길든 짧든 분모가 같아, 짧은 이름이 유리해지지도 불리해지지도 않는다.

★고치는 방법 — 가중 점수
```
완전 일치(토큰이 같다)        1.0
포함(한쪽이 다른 쪽을 품는다)   0.5   ← 여기가 원래 1.0 이었다
그 외                        0
```
그리고 **분모를 «질의어 토큰 수»와 «상품명 토큰 수»의 평균**으로 둔다.
⇒ 질의어의 모든 토큰을 맞혀도 **상품명에 남는 토큰이 많으면 감점**된다.
  (「팬티」로 「요일팬티 세트」를 찾으면, 「요일」·「세트」가 안 맞았다는 사실이 점수에 남는다)

  ⚠ 원본 `tools.py` 는 «한 줄도» 고치지 않는다. 여기서 다시 정의하고 전후를 나란히 잰다.

  python 13_search_v2.py
"""
import re
import sys

from config import ensure_data

sys.stdout.reconfigure(encoding="utf-8")
ensure_data()

from tools import PRODUCTS, search_product as search_v1   # noqa: E402


def toks(s):
    return [t for t in re.split(r"[\s·()]+", s) if t]


def search_v2(query: str) -> dict:
    """★가중 점수 — 완전 일치 1.0 · 포함 0.5 · 그 외 0."""
    qt = toks(query)
    if not qt:
        return {"query": query, "candidates": []}
    hits = []
    for pid, p in PRODUCTS.items():
        name = p["name"]
        nt = toks(name)
        got = 0.0
        for t in qt:
            if t in nt:                                    # 토큰이 «그대로» 있다
                got += 1.0
            elif any(t in x or x in t for x in nt):        # 한쪽이 다른 쪽을 «품는다»
                got += 0.5
        if got <= 0:
            continue
        # ★분모 = (질의어 토큰 수 + 상품명 토큰 수) / 2
        #   질의어를 다 맞혀도 상품명에 «남는 토큰»이 많으면 감점된다
        denom = (len(qt) + len(nt)) / 2
        hits.append({"product_id": pid, "name": name, "category": p["category"],
                     "price": p["price"], "score": round(got / denom, 3)})
    hits.sort(key=lambda h: -h["score"])
    top = [h for h in hits if abs(h["score"] - hits[0]["score"]) < 1e-9] if hits else []
    return {"query": query, "candidates": hits[:5],
            "resolved_product_id": top[0]["product_id"] if len(top) == 1 else None,
            "ambiguous": len(top) > 1,
            "note": ("후보가 여러 개입니다. 어느 상품인지 고객에게 확인하십시오."
                     if len(top) > 1 else None)}


# ★정답셋의 tool_args 에서 «정답 상품 ID» 를 끌어와 채점한다 — 내가 정하지 않는다
def gold_pairs():
    import json
    from config import BASE
    g = json.loads((BASE / "answer_goldenset_multiturn.json").read_text(encoding="utf-8"))
    out = []
    for c in g["conversations"]:
        # ★«첫» expect 턴의 product_id 를 쓴다. 질문도 «첫» 고객 발화이기 때문이다.
        #   처음엔 «마지막» 것을 가져왔다가 C-011 을 오답으로 잡았다 —
        #   C-011 은 턴이 둘(P1001 → P2002)인데 질문은 첫 턴이라 정답이 «어긋났다».
        #   ⇒ 질문과 정답은 «같은 턴»에서 와야 한다.
        want = None
        for t in c["turns"]:
            e = t.get("expect") or {}
            for tool, args in (e.get("tool_args") or {}).items():
                pid = args.get("product_id")
                if pid and want is None:
                    want = pid
            if want:
                break
        if not want:
            continue
        q = next((t["text"] for t in c["turns"] if t["role"] == "customer"), "")
        out.append((c["conv_id"], q, want))
    return out


if __name__ == "__main__":
    print("=== ★12강이 든 그 예시 ===")
    for q in ["요일팬티 세트", "팬티", "캔버스화", "세트"]:
        a, b = search_v1(q), search_v2(q)
        print("  질의 %r" % q)
        for tag, r in (("v1", a), ("★v2", b)):
            cands = ", ".join("%s(%.2f)" % (c["name"], c["score"]) for c in r["candidates"][:3])
            print("     %-4s ambiguous=%-5s  %s" % (tag, r["ambiguous"], cands or "없음"))
        print()

    print("=== 정답셋으로 채점 — 상품 ID 를 «맞히는가» ===")
    pairs = gold_pairs()
    print("   product_id 가 붙은 대화 %d건" % len(pairs))
    print()
    for tag, fn in (("v1 (원본)", search_v1), ("★v2 (가중)", search_v2)):
        hit = amb = 0
        miss = []
        for cid, q, want in pairs:
            r = fn(q)
            if r.get("resolved_product_id") == want:
                hit += 1
            elif r.get("ambiguous"):
                amb += 1
                miss.append((cid, q[:30], "애매(동점 %d개)"
                             % sum(1 for c in r["candidates"]
                                   if abs(c["score"] - r["candidates"][0]["score"]) < 1e-9)))
            else:
                miss.append((cid, q[:30], "틀림→%s" % r.get("resolved_product_id")))
        print("   %-12s 정확히 특정 %2d/%d · 애매 %d" % (tag, hit, len(pairs), amb))
        for cid, q, why in miss[:6]:
            print("        %-7s %-32s %s" % (cid, q, why))
        print()
    print("   ※ «애매»는 틀린 것이 아니다 — 8강대로 «되물으면» 맞는 응대다.")
    print("     다만 되묻는 만큼 턴이 늘고, 채점기는 첫 턴만 본다.")
