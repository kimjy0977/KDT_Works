# -*- coding: utf-8 -*-
"""★8강 — 코퍼스 80건 전체를 삼중항으로 뽑는다.

노드가 시키는 셋을 다 한다:
  ① 비용을 «미리» 추정한다   — 02_extract_probe.py 에서 이미 쟀다
  ② 병렬로 돌린다             — ThreadPoolExecutor
  ③ 결과를 «캐시»한다         — graph/cache/<문서>.json · 두 번 부르지 않는다

★캐시가 있는 이유 — 뒤 단계(정규화·커뮤니티)를 고칠 때마다 80건을 다시 뽑으면
  돈도 시간도 버린다. 추출은 «한 번»이고 그 뒤는 전부 로컬 작업이다.

    python 03_extract_all.py
    python 03_extract_all.py --force        # 캐시 무시하고 다시
    python 03_extract_all.py --limit 5      # 5건만 (시험용)
"""
import argparse
import collections
import concurrent.futures as cf
import glob
import io
import json
import os
import sys
import threading
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "data", "cinephile_kb_80", "docs")
GOLD = os.path.join(HERE, "data", "cinephile_goldenset.json")
CACHE = os.path.join(HERE, "graph", "cache")
OUT = os.path.join(HERE, "graph", "triples.json")

sys.path.insert(0, HERE)
from importlib import import_module            # noqa: E402
_probe = import_module("02_extract_probe")     # 프롬프트·스키마를 «한 곳»에서 가져온다
SYS, REL_DESC, SCHEMA = _probe.SYS, _probe.REL_DESC, _probe.SCHEMA

_lock = threading.Lock()
_usage = {"in": 0, "out": 0}


def extract_one(client, model, name, maxchars, force):
    """문서 한 건 → 삼중항. 캐시가 있으면 LLM 을 «부르지 않는다»."""
    cpath = os.path.join(CACHE, name + ".json")
    if not force and os.path.exists(cpath):
        d = json.load(io.open(cpath, encoding="utf-8"))
        return name, d["triples"], True

    body = io.open(os.path.join(DOCS, name + ".md"), encoding="utf-8").read()[:maxchars]
    rels = _probe.relations()
    sys_prompt = SYS.format(rels="\n".join("- " + REL_DESC.get(r, r) for r in rels))

    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": sys_prompt},
                  {"role": "user", "content": body}],
        response_format={"type": "json_schema",
                         "json_schema": {"name": "triples", "strict": True, "schema": SCHEMA}},
        temperature=0,
    )
    tri = json.loads(r.choices[0].message.content)["triples"]
    with _lock:
        _usage["in"] += r.usage.prompt_tokens
        _usage["out"] += r.usage.completion_tokens
    # ★origin 을 여기서 박는다 — 9강이 요구하는 「어느 사실이 어디서 왔나」
    for t in tri:
        t["origin"] = name
    io.open(cpath, "w", encoding="utf-8", newline="").write(
        json.dumps({"doc": name, "triples": tri}, ensure_ascii=False, indent=1))
    return name, tri, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.environ.get("EXTRACT_MODEL", "gpt-4.1-mini"))
    ap.add_argument("--maxchars", type=int, default=6000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    os.makedirs(CACHE, exist_ok=True)
    from dotenv import load_dotenv
    load_dotenv(os.path.join(HERE, ".env"))
    from openai import OpenAI
    client = OpenAI()

    names = [os.path.basename(p)[:-3] for p in sorted(glob.glob(os.path.join(DOCS, "*.md")))]
    if args.limit:
        names = names[: args.limit]

    print("=" * 70)
    print("8강 전체 추출 — 문서 %d건 · %s · 앞 %s자 · 병렬 %d"
          % (len(names), args.model, format(args.maxchars, ","), args.workers))
    print("=" * 70)

    t0 = time.perf_counter()
    all_tri, cached_n, done = [], 0, 0
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(extract_one, client, args.model, n, args.maxchars, args.force): n
                for n in names}
        for fut in cf.as_completed(futs):
            name, tri, was_cached = fut.result()
            all_tri += tri
            cached_n += was_cached
            done += 1
            if done % 10 == 0 or done == len(names):
                print("  %3d/%d  삼중항 누적 %d" % (done, len(names), len(all_tri)))
    sec = time.perf_counter() - t0

    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps({"model": args.model, "maxchars": args.maxchars,
                    "n_docs": len(names), "triples": all_tri},
                   ensure_ascii=False, indent=1))

    print("-" * 70)
    print("삼중항 %s개 · %.1f초 · 캐시 적중 %d/%d"
          % (format(len(all_tri), ","), sec, cached_n, len(names)))
    print("토큰: 입력 %s · 출력 %s  (캐시 적중분은 0)"
          % (format(_usage["in"], ","), format(_usage["out"], ",")))
    c = collections.Counter(t["r"] for t in all_tri)
    print()
    print("관계별:")
    for r, n in c.most_common():
        print("  %-28s %4d" % (r, n))
    ents = {t["s"] for t in all_tri} | {t["o"] for t in all_tri}
    print()
    print("고유 엔티티 %s개 (정규화 «전» — 9강에서 줄어든다)" % format(len(ents), ","))
    print("저장: graph/triples.json")


if __name__ == "__main__":
    main()
