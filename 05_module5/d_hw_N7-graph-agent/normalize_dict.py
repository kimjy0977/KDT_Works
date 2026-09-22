# -*- coding: utf-8 -*-
"""★정규화 사전 확장 — 「같은 개체를 하나로 합치는 기준」 (루브릭 ②)

  python normalize_dict.py --dry     # 무엇을 물을지만 본다
  python normalize_dict.py           # 새 가치를 축·극에 배정해 values.json 갱신

★무엇을 푸나 — 추출된 가치 183개 중 내 사전에 있는 건 «1개»였다.
  「진실과 정의 6 · 정의와 복수 4 · 정의 실현 4 · 사회 정의 3」처럼
  같은 것을 네 이름으로 부른다. 이대로는 영화 사이에 다리가 안 생긴다.

★어떻게 합치나 — «이름»이 아니라 «축과 극»으로 합친다.
  축 8개는 고정하고, 새 가치가 어느 축의 어느 극인지 배정한다.
  ⛔어느 축에도 안 맞으면 «미분류»로 남기고 목록을 낸다. 억지로 넣지 않는다.
    이유 — 「좋은 결과」를 [동의·남의 설계] 로 억지로 넣었더니
    (좋은 결과 ↔ 동의 없는 개입) 이 «같은 극»이 되어 ★충돌이 증발했다(2026-09-20 실측).

★두 가치를 붙여 쓴 것은 «쪼갠다» — 「진실과 정의」는 가치 하나가 아니라 둘이다.
"""
import argparse
import collections
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
VALS = os.path.join(HERE, "values.json")
RAW = os.path.join(HERE, "output", "triples_raw.json")

PROMPT = """너는 «가치 이름»을 정해진 축과 극에 배정하는 분류기다.

축과 극은 아래 8개뿐이다. 새로 만들지 마라.
%s

규칙
- 한 가치가 여러 축에 속할 수 있다. 그럴 땐 여러 개 적는다.
- ★어느 축에도 안 맞으면 axes 를 빈 배열로 둔다. 억지로 넣지 마라.
  잘못 넣으면 서로 부딪치던 두 가치가 «같은 극»이 되어 충돌이 사라진다.
- ★「진실과 정의」처럼 두 가치가 붙어 있으면 split 에 쪼갠 이름을 적는다.
  쪼갠 각각을 다시 축에 배정한다.
- 극을 고를 때 «어느 쪽에 가까운가»를 본다. 애매하면 axes 를 비운다.

예
  {"name":"정의 실현","axes":[["앎","밝힘"]],"split":[]}
  {"name":"가족애","axes":[["생명","한 사람"]],"split":[]}
  {"name":"진실과 정의","axes":[],"split":["진실","정의 실현"]}
  {"name":"분위기","axes":[],"split":[]}

JSON 배열로만 답한다. 설명·코드펜스 없이.
아래 가치들을 전부 배정하라. 하나도 빠뜨리지 마라.
%s
"""


def load():
    v = json.load(io.open(VALS, encoding="utf-8"))
    raw = json.load(io.open(RAW, encoding="utf-8"))
    return v, raw["triples"]


def used_values(triples):
    c = collections.Counter()
    for x in triples:
        if x["r"] == "CONFLICTS_WITH":
            c[x["s"]] += 1
            c[x["o"]] += 1
        elif x["r"] == "INVOKES_VALUE":
            c[x["o"]] += 1
    return c


def axes_block(v):
    return "\n".join("  %-6s  %s  ↔  %s" % (ax, p[0], p[1])
                     for ax, p in v["축"].items())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--model", default="gpt-4.1-mini")
    ap.add_argument("--batch", type=int, default=60)
    args = ap.parse_args()

    v, triples = load()
    cnt = used_values(triples)
    todo = sorted((x for x in cnt if x not in v["가치"]),
                  key=lambda x: (-cnt[x], x))          # ★sorted — 재현 가능하게
    print("가치 %d개 · 사전에 있음 %d · ★배정할 것 %d개"
          % (len(cnt), len(cnt) - len(todo), len(todo)))
    if args.dry:
        print("\n" + axes_block(v))
        print("\n앞 20개:", " · ".join(todo[:20]))
        return
    if not todo:
        print("배정할 것 없다")
        return

    from dotenv import load_dotenv
    from openai import OpenAI
    load_dotenv(os.path.join(HERE, ".env"))
    cl = OpenAI()

    got, tin, tout = [], 0, 0
    for i in range(0, len(todo), args.batch):
        chunk = todo[i:i + args.batch]
        lines = "\n".join("- %s (%d회)" % (x, cnt[x]) for x in chunk)
        r = cl.chat.completions.create(
            model=args.model, temperature=0,
            messages=[{"role": "user",
                       "content": PROMPT % (axes_block(v), lines)}])
        tin += r.usage.prompt_tokens
        tout += r.usage.completion_tokens
        m = re.search(r"\[.*\]", r.choices[0].message.content or "", re.S)
        try:
            got += json.loads(m.group(0)) if m else []
        except Exception as exc:
            print("  ★파싱 실패 (묶음 %d) — %s" % (i // args.batch + 1, str(exc)[:60]))
        print("  묶음 %d/%d — 누적 %d개"
              % (i // args.batch + 1, (len(todo) - 1) // args.batch + 1, len(got)),
              flush=True)

    # ── 반영 ─────────────────────────────────────────────────────────
    poles = {ax: set(p) for ax, p in v["축"].items()}
    added, unmapped, splits, bad = 0, [], {}, []
    for it in got:
        nm = (it or {}).get("name")
        if not nm:
            continue
        axes = [a for a in (it.get("axes") or [])
                if isinstance(a, list) and len(a) == 2
                and a[0] in poles and a[1] in poles[a[0]]]
        # ★모델이 없는 축·극을 지어내면 «버린다». 스키마 밖은 넣지 않는다
        if len(axes) != len(it.get("axes") or []):
            bad.append(nm)
        sp = [s for s in (it.get("split") or []) if isinstance(s, str)]
        if sp:
            splits[nm] = sp
        if axes:
            v["가치"][nm] = axes
            added += 1
        elif not sp:
            unmapped.append(nm)

    v["_배정기록"] = {
        "일시": "2026-09-22", "모델": args.model,
        "대상": len(todo), "배정됨": added,
        "쪼갠 것": len(splits), "미분류": len(unmapped),
        "★스키마 밖 축을 지어낸 건": len(bad),
        "미분류_목록": sorted(unmapped),
        "쪼갠_목록": splits,
        "_기준": [
            "이름이 아니라 «축과 극»으로 합친다.",
            "어느 축에도 안 맞으면 미분류로 남긴다 — 억지로 넣으면 충돌이 증발한다.",
            "두 가치가 붙은 이름은 쪼개 각각 배정한다.",
        ],
    }
    v["_split"] = splits
    io.open(VALS, "w", encoding="utf-8", newline="").write(
        json.dumps(v, ensure_ascii=False, indent=2))

    cost = tin / 1e6 * 0.40 + tout / 1e6 * 1.60
    print("\n" + "-" * 72)
    print("★배정 %d개 · 쪼갠 이름 %d개 · 미분류 %d개 · 스키마밖 %d건"
          % (added, len(splits), len(unmapped), len(bad)))
    print("사전 %d → ★%d개 · 토큰 %d/%d → $%.4f (약 %d원)"
          % (len(cnt) - len(todo), len(v["가치"]), tin, tout, cost, cost * 1400))
    print("\n★미분류 (억지로 안 넣었다) %d개:" % len(unmapped))
    print("  " + " · ".join(sorted(unmapped)[:24]))


if __name__ == "__main__":
    main()
