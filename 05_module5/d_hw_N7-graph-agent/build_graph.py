# -*- coding: utf-8 -*-
"""①추출 + ②정제·병합 → 지식 그래프 (요건 §필수구현 ③)

  python build_graph.py            # 80건 추출 (캐시 있으면 건너뜀)
  python build_graph.py --limit 5  # 먼저 5건만
  python build_graph.py --stats    # 추출 안 하고 현황만

★temperature=0 이 «반드시» 필요하다 — 추출은 재현 가능해야 한다(루브릭 ①).
  그래서 gpt-5 계열을 쓰지 않는다. 그 모델들은 temperature=0 을 안 받는다.
★sorted() 없이 set 을 돌리면 실행마다 순서가 달라진다 (노드6 실사고).
"""
import argparse
import io
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(io.open(os.path.join(HERE, "config.json"), encoding="utf-8"))
CACHE = os.path.join(HERE, "cache")
OUT = os.path.join(HERE, "output")

sys.path.insert(0, HERE)
from probe_extract import SCHEMA, USD_IN, USD_OUT, KRW      # noqa: E402


def clean_title(fname):
    """★파일명이 아니라 «제목»을 넘긴다.

    `1987_(2017년_영화).md` → `1987`
    실측 — 파일명 그대로 넘기면 모델이 그걸 영화 제목으로 쓴다(gpt-5.4-mini).
    """
    t = os.path.splitext(fname)[0]
    t = re.sub(r"_?\((?:\d{4}년\s*)?(?:영화|드라마|소설)?\)$", "", t)
    return t.replace("_", " ").strip()


def docs(limit=None):
    """★채택 기준을 통과한 «영화 작품»만 넘긴다 (요건 ①).

    왜 여기서 거르나 — 코퍼스 80건에 기업 10 · 인물 28 · 시상식 7 이 섞여 있다.
      ① 그대로 돌리면 추출비의 절반이 «버릴 문서»에 나간다
      ② ★「대종상」이 (예술적 가치 ↔ 대중적 인기) 를 냈다. 틀린 건 아니지만
        ASKS 의 s 가 영화가 아니라 스키마 위반이다 — 애초에 안 넣는 게 맞다
    기준은 fetch_docs.py 에 «한 군데» 둔다. 두 곳에 적으면 갈라진다.
    """
    from fetch_docs import MIN_CHARS, NOT_WORK, WORK_CAT

    d = os.path.join(HERE, CFG["corpus"]["docs"])
    out, dropped = [], []
    for f in sorted(os.listdir(d)):                              # ★sorted
        if not f.endswith(".md"):
            continue
        t = io.open(os.path.join(d, f), encoding="utf-8",
                    errors="replace").read()
        m = re.search(r"^분류:\s*(.+)$", t, re.M)
        cats = [c.strip() for c in m.group(1).split(",")] if m else []
        film = any(WORK_CAT.search(c) and not NOT_WORK.search(c) for c in cats)
        if not film:
            dropped.append((f[:-3], "영화 작품 아님"))
        elif len(t) < MIN_CHARS:
            dropped.append((f[:-3], "%d자 — 줄거리 없음" % len(t)))
        else:
            out.append((clean_title(f), os.path.join(d, f)))
    io.open(os.path.join(OUT, "dropped_docs.json"), "w",
            encoding="utf-8", newline="").write(json.dumps(
                {"기준": {"분류": "…영화 (단 영화제·영화상·감독·제작사·배우 제외)",
                         "최소 길이": MIN_CHARS,
                         "_근거": "500자 미만 2건은 삼중항 0개 · 500자 이상 31건은 실패 0"},
                 "채택": len(out), "탈락": len(dropped),
                 "탈락_목록": [{"문서": a, "이유": b} for a, b in dropped]},
                ensure_ascii=False, indent=1))
    print("채택 %d건 · ★탈락 %d건 (output/dropped_docs.json)"
          % (len(out), len(dropped)), flush=True)
    return out[:limit] if limit else out


def cached(title):
    p = os.path.join(CACHE, "%s.json" % re.sub(r"[\\/:*?\"<>|]", "_", title))
    if os.path.exists(p):
        try:
            return json.load(io.open(p, encoding="utf-8"))
        except Exception:
            return None
    return None


def save_cache(title, obj):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, "%s.json" % re.sub(r"[\\/:*?\"<>|]", "_", title))
    io.open(p, "w", encoding="utf-8", newline="").write(
        json.dumps(obj, ensure_ascii=False, indent=1))


def one(cl, title, path, model):
    hit = cached(title)
    if hit:
        return title, hit["triples"], hit.get("in", 0), hit.get("out", 0), True

    body = io.open(path, encoding="utf-8",
                   errors="replace").read()[:CFG["model"]["doc_chars"]]
    for attempt in (1, 2):
        try:
            r = cl.chat.completions.create(
                model=model, temperature=0,
                messages=[{"role": "system", "content": SCHEMA},
                          {"role": "user",
                           "content": "영화 제목: %s\n\n%s" % (title, body)}])
            raw = r.choices[0].message.content or ""
            m = re.search(r"\[.*\]", raw, re.S)
            rows = json.loads(m.group(0)) if m else []
            # ★스키마 밖 관계는 «여기서» 버린다. 버린 수를 센다.
            keep = [x for x in rows if isinstance(x, dict)
                    and x.get("r") in CFG["relations"]
                    and x.get("s") and x.get("o")]
            save_cache(title, {"triples": keep, "raw_n": len(rows),
                               "in": r.usage.prompt_tokens,
                               "out": r.usage.completion_tokens,
                               "model": model})
            return (title, keep, r.usage.prompt_tokens,
                    r.usage.completion_tokens, False)
        except Exception as exc:
            if attempt == 2:
                print("  ★실패 %s — %s" % (title, str(exc)[:80]), flush=True)
                return title, [], 0, 0, False
            time.sleep(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--model", default=CFG["model"]["extract"])
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args()

    ds = docs(args.limit)
    os.makedirs(OUT, exist_ok=True)

    if args.stats:
        n = sum(1 for t, _ in ds if cached(t))
        print("문서 %d건 · 캐시 %d건 · 남은 %d건" % (len(ds), n, len(ds) - n))
        return

    from dotenv import load_dotenv
    from openai import OpenAI
    load_dotenv(os.path.join(HERE, ".env"))
    cl = OpenAI()

    print("=" * 72)
    print("추출 %d건 · %s · 병렬 %d · 문서 앞 %d자"
          % (len(ds), args.model, args.workers, CFG["model"]["doc_chars"]))
    print("=" * 72, flush=True)

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        res = list(ex.map(lambda a: one(cl, a[0], a[1], args.model), ds))

    triples, tin, tout, hits = [], 0, 0, 0
    per = {}
    for title, rows, i_, o_, hit in res:
        for x in rows:
            x["origin"] = title
        triples += rows
        tin += i_
        tout += o_
        hits += 1 if hit else 0
        per[title] = len(rows)

    dt = time.time() - t0
    cost = tin / 1e6 * USD_IN + tout / 1e6 * USD_OUT

    by = {}
    for x in triples:
        by[x["r"]] = by.get(x["r"], 0) + 1

    print("\n" + "-" * 72)
    print("삼중항 %d개 · %.1f초 · 캐시적중 %d" % (len(triples), dt, hits))
    for r_ in CFG["relations"]:
        print("  %-16s %4d" % (r_, by.get(r_, 0)))
    print("토큰 입력 %d / 출력 %d  →  $%.3f (약 %d원)"
          % (tin, tout, cost, cost * KRW))

    # ★한 건도 못 뽑은 문서 — 탈락 후보다. 요건 ①이 «기준과 목록»을 요구한다
    empty = sorted(t for t, n in per.items() if n == 0)
    print("\n★삼중항 0개 문서 %d건 — 탈락 후보" % len(empty))
    for t in empty[:12]:
        print("    %s" % t)
    if len(empty) > 12:
        print("    … 외 %d건" % (len(empty) - 12))

    io.open(os.path.join(OUT, "triples_raw.json"), "w",
            encoding="utf-8", newline="").write(json.dumps(
                {"n_docs": len(ds), "model": args.model,
                 "tokens": {"in": tin, "out": tout}, "usd": round(cost, 4),
                 "empty_docs": empty, "per_doc": per,
                 "triples": triples}, ensure_ascii=False, indent=1))
    print("\n저장 · output/triples_raw.json")


main()
