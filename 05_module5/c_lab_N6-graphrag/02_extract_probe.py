# -*- coding: utf-8 -*-
"""★5강 시험 — 문서 몇 건에서 삼중항이 제대로 나오는가. 그리고 «80건이면 얼마인가».

노드가 시키는 것: *"코퍼스 전체를 그래프로 만들면서 «비용을 미리 추정하고»,
병렬로 돌리고, 결과를 캐시합니다."* (8강)

⛔80건을 바로 돌리지 않는다. 토큰의 8할이 그 단계에서 나간다고 노드가 경고했다.
  ⇒ 몇 건으로 «실제 토큰»을 재고, 거기서 80건을 역산한다.

★스키마는 «질문에서 역산»한다 — 골든셋이 실제로 쓰는 관계 7종만 뽑는다.
  (goldenset.json 의 stats.relations_used 에서 «읽어 온다». 손으로 적지 않는다)

    python 02_extract_probe.py
    python 02_extract_probe.py --docs 기생충_(영화) 봉준호 --model gpt-4.1-mini
"""
import argparse
import collections
import io
import json
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "data", "cinephile_kb_80", "docs")
GOLD = os.path.join(HERE, "data", "cinephile_goldenset.json")

SYS = """너는 한국어 위키백과 문서에서 «사실 관계»를 뽑는 추출기다.

주어진 문서에서 아래 관계 «만» 찾아 삼중항 (주어, 관계, 목적어) 으로 적는다.

{rels}

규칙
- 문서에 «적혀 있는 것»만 뽑는다. 아는 것을 보태지 않는다.
- 주어·목적어는 문서에 나온 «표기 그대로» 쓴다. 풀어 쓰거나 줄이지 않는다.
- 위 목록에 없는 관계는 «버린다». 비슷해 보여도 만들어 내지 않는다.
- 확실하지 않으면 뽑지 않는다. 적게 뽑는 편이 낫다.
"""

REL_DESC = {
    "DIRECTED":                   "(사람, DIRECTED, 영화) — 연출했다",
    # ★1차 시험에서 기생충 문서의 ACTED_IN 이 «0개»였다. 잘려서가 아니라 —
    #   캐스팅이 「송강호: 김기택 역 - 설명」 «목록»이라 «출연했다»는 문장이 없었다.
    #   ⇒ 목록 형식을 명시한다. (한 번에 한 군데만 바꾼다)
    "ACTED_IN":                   ("(사람, ACTED_IN, 영화) — 출연했다. "
                                   "★「등장 인물」·「캐스팅」 아래의 «배우이름: 배역 역» 목록도 "
                                   "출연이다. 이때 주어는 «배우 이름», 목적어는 «그 문서의 영화»다"),
    "HAS_GENRE":                  "(영화, HAS_GENRE, 장르) — 장르가 무엇인가",
    "HAS_THEME":                  "(영화, HAS_THEME, 주제) — 무엇을 다루는가",
    "SET_IN":                     "(영화, SET_IN, 시대·장소) — 어디/언제를 배경으로 하는가",
    "WON_AWARD":                  "(영화 또는 사람, WON_AWARD, 상) — 수상했다",
    "PRODUCED_OR_DISTRIBUTED_BY": "(영화, PRODUCED_OR_DISTRIBUTED_BY, 회사) — 제작·배급사",
}

SCHEMA = {
    "type": "object",
    "properties": {
        "triples": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "s": {"type": "string"},
                    "r": {"type": "string"},
                    "o": {"type": "string"},
                },
                "required": ["s", "r", "o"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["triples"],
    "additionalProperties": False,
}


def relations():
    """★손으로 적지 않는다 — 골든셋이 실제로 쓰는 관계를 «읽어 온다»."""
    g = json.load(io.open(GOLD, encoding="utf-8"))
    return g["stats"]["relations_used"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", nargs="*", default=["기생충_(영화)", "봉준호", "JK필름"])
    ap.add_argument("--model", default=os.environ.get("EXTRACT_MODEL", "gpt-4.1-mini"))
    ap.add_argument("--maxchars", type=int, default=6000,
                    help="문서 앞 N자만 쓴다. HBO(55k자) 같은 곁가지 문서 때문에 필요하다")
    args = ap.parse_args()

    from dotenv import load_dotenv
    load_dotenv(os.path.join(HERE, ".env"))
    from openai import OpenAI
    client = OpenAI()

    rels = relations()
    sys_prompt = SYS.format(rels="\n".join("- " + REL_DESC.get(r, r) for r in rels))
    print("★관계 %d종 (골든셋에서 읽어 옴): %s" % (len(rels), ", ".join(rels)))
    print("★모델: %s · 문서 앞 %s자만" % (args.model, format(args.maxchars, ",")))
    print("=" * 70)

    tot_in = tot_out = 0
    all_triples = []
    for name in args.docs:
        path = os.path.join(DOCS, name + ".md")
        if not os.path.exists(path):
            print("  ⚠ 없는 문서: %s" % name)
            continue
        raw = io.open(path, encoding="utf-8").read()
        body = raw[: args.maxchars]

        t0 = time.perf_counter()
        r = client.chat.completions.create(
            model=args.model,
            messages=[{"role": "system", "content": sys_prompt},
                      {"role": "user", "content": body}],
            response_format={"type": "json_schema",
                             "json_schema": {"name": "triples", "strict": True,
                                             "schema": SCHEMA}},
            temperature=0,
        )
        sec = time.perf_counter() - t0
        data = json.loads(r.choices[0].message.content)
        tri = data["triples"]
        u = r.usage
        tot_in += u.prompt_tokens
        tot_out += u.completion_tokens
        all_triples += [(name, t) for t in tri]

        print("[%s] 원문 %s자 → 입력 %s자 · 삼중항 %d개 · %s/%s토큰 · %.1f초"
              % (name[:22], format(len(raw), ","), format(len(body), ","),
                 len(tri), format(u.prompt_tokens, ","), format(u.completion_tokens, ","), sec))
        c = collections.Counter(t["r"] for t in tri)
        print("      관계별: %s" % dict(c))
        for t in tri[:4]:
            print("      · (%s, %s, %s)" % (t["s"], t["r"], t["o"]))
        if len(tri) > 4:
            print("      … 외 %d개" % (len(tri) - 4))
        print()

    n = len([d for d in args.docs if os.path.exists(os.path.join(DOCS, d + ".md"))])
    if not n:
        return
    print("=" * 70)
    print("문서 %d건 실측: 입력 %s · 출력 %s 토큰" % (n, format(tot_in, ","), format(tot_out, ",")))
    print("  문서당 평균: 입력 %s · 출력 %s" % (format(tot_in // n, ","), format(tot_out // n, ",")))
    print()
    print("★80건 역산: 입력 %s · 출력 %s 토큰"
          % (format(tot_in // n * 80, ","), format(tot_out // n * 80, ",")))
    print("  ⚠ 앞 %s자만 쓴 값이다. 잘라내지 않으면 훨씬 커진다" % format(args.maxchars, ","))
    print("  ⚠ 관계 없는 문서(HBO·IMDb·KT)도 같은 비용이 든다 — 8강에서 걸러야 할 자리")


if __name__ == "__main__":
    main()
