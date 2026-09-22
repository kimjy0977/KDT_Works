# -*- coding: utf-8 -*-
"""추출 프롬프트 «검증기» — 한 건만 돌려 사람이 읽어 본다.

왜 있나 — 80건을 돌리기 전에 프롬프트가 쓸 만한지 본다.
  data/_probe_gold/ 7편은 내가 물음·가치를 «명시해 쓴» 문서다.
  거기서 뽑히는 것과 내가 쓴 것을 대조해 프롬프트를 고친다.
  ⚠단 그 7편은 ★코퍼스에 넣지 않는다 — 적힌 것을 베끼면 성능이 부풀려진다.

쓰기
  python probe_extract.py "data/docs/1987_(2017년_영화).md"
  python probe_extract.py "data/_probe_gold/오펜하이머.md" --gold
"""
import argparse
import io
import json
import os
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(io.open(os.path.join(HERE, "config.json"), encoding="utf-8"))

SCHEMA = """너는 영화 문서에서 «그 영화가 던지는 물음과 가치»를 뽑는 추출기다.

뽑을 것은 세 종류뿐이다.
  ASKS            s=★영화 제목(그대로)   o=그 영화가 던지는 물음(문장)
  INVOKES_VALUE   s=위에서 쓴 물음       o=그 물음이 불러내는 가치(명사구)
  CONFLICTS_WITH  s=가치                o=부딪치는 다른 가치

★s 에 사건·인물·단체를 쓰지 마라. ASKS 의 s 는 «반드시» 영화 제목이다.

★★CONFLICTS_WITH 가 제일 중요하고 제일 틀리기 쉽다.
  ○ 맞는 예 — 둘 다 «옳은데» 한쪽을 택해야 한다
      (전쟁 종식, 생명 존중)      빨리 끝내려면 사람이 죽는다
      (개인의 양심, 국가의 요구)  나라가 시키는 일이 내 양심에 걸린다
      (기밀 유지, 경고할 의무)    알리면 사람을 살리지만 비밀이 깨진다
  ✗ 틀린 예 — ★이렇게 쓰면 안 된다
      (민주주의, 독재)   ← 한쪽이 «나쁜 것»이다. 선악 대립은 딜레마가 아니다
      (정의, 불의)       ← 같은 이유로 틀렸다
      (사랑, 미움)       ← 감정의 반대말일 뿐이다
  ⇒ 스스로 물어라 — **「둘 다 지키고 싶은데 못 지키는가?」**
    한쪽을 버려도 아깝지 않으면 그건 딜레마가 아니다. 넣지 마라.

- 물음은 «~인가?» 로 끝나는 문장으로 쓴다.
- 가치는 2~10자 명사구. 「국가의 요구」「눈앞의 한 사람」처럼.
- ★문서에 근거가 없으면 뽑지 마라. 일반론으로 채우지 마라.
- 등장인물 이름·감독·수상 연도는 뽑지 마라. 이 추출기의 일이 아니다.
- 각 종류를 최소 2건씩 찾아라. 문서에서 못 찾으면 그 종류는 비워 둔다.

JSON 배열로만 답한다. 설명·코드펜스 없이.
아래는 «형식» 예시다. ★이 값을 그대로 베끼지 마라. 문서에서 찾아 채워라.
[{"s":"영화제목","r":"ASKS","o":"…인가?"},
 {"s":"…인가?","r":"INVOKES_VALUE","o":"가치이름"},
 {"s":"가치이름","r":"CONFLICTS_WITH","o":"다른가치"}]
"""

USD_IN, USD_OUT = 0.40, 1.60      # gpt-4.1-mini · 1M 토큰당. 바뀌면 이 줄만 고친다
KRW = 1400


def client():
    from dotenv import load_dotenv
    from openai import OpenAI
    load_dotenv(os.path.join(HERE, ".env"))
    return OpenAI()


def extract(cl, title, body, model):
    t0 = time.time()
    r = cl.chat.completions.create(
        model=model, temperature=0,
        messages=[{"role": "system", "content": SCHEMA},
                  {"role": "user",
                   "content": "영화 제목: %s\n\n%s" % (title, body)}])
    raw = r.choices[0].message.content or ""
    m = re.search(r"\[.*\]", raw, re.S)
    try:
        rows = json.loads(m.group(0)) if m else []
    except Exception:
        rows = []
    return rows, raw, r.usage, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--model", default=CFG["model"]["extract"])
    ap.add_argument("--gold", action="store_true",
                    help="내가 쓴 문서 — 난이도 대조군. ★코퍼스가 아니다")
    args = ap.parse_args()

    title = os.path.splitext(os.path.basename(args.path))[0]
    body = io.open(args.path, encoding="utf-8",
                   errors="replace").read()[:CFG["model"]["doc_chars"]]

    rows, raw, u, dt = extract(client(), title, body, args.model)

    print("=" * 72)
    print("%s  ·  %s  ·  %.1f초  ·  입력 %d자%s"
          % (title, args.model, dt, len(body), "  [gold·대조군]" if args.gold else ""))
    if u:
        one = u.prompt_tokens / 1e6 * USD_IN + u.completion_tokens / 1e6 * USD_OUT
        print("토큰 입력 %d · 출력 %d  →  1건 $%.5f · ★80건 $%.3f (약 %d원)"
              % (u.prompt_tokens, u.completion_tokens, one, one * 80, one * 80 * KRW))
    print("=" * 72)

    if not rows:
        print("★파싱 실패 — 원문 앞 400자:\n%s" % raw[:400])
        return

    by = {}
    for x in rows:
        if isinstance(x, dict) and x.get("r"):
            by.setdefault(x["r"], []).append(x)
    for r_ in CFG["relations"]:
        got = by.get(r_, [])
        print("\n[%s] %d건" % (r_, len(got)))
        for x in got:
            print("   %s  →  %s" % (str(x.get("s"))[:34], str(x.get("o"))[:44]))
    extra = [k for k in by if k not in CFG["relations"]]
    if extra:
        print("\n⚠스키마 밖 관계 %d종: %s" % (len(extra), " · ".join(extra)))

    print("\n" + "-" * 72)
    print("삼중항 %d개 · ★사람이 읽어서 «말이 되나»를 본다. 숫자로는 못 판정한다." % len(rows))

    out = os.path.join(HERE, "output", "probe_%s.json" % title)
    io.open(out, "w", encoding="utf-8", newline="").write(
        json.dumps({"title": title, "model": args.model, "sec": round(dt, 1),
                    "triples": rows}, ensure_ascii=False, indent=2))
    print("저장 · %s" % os.path.relpath(out, HERE))


# ★가드가 «반드시» 있어야 한다 — build_graph.py 가 이 파일에서 SCHEMA 를 import 한다.
#   가드 없이 두면 import 하는 순간 이 main() 이 돌아 argparse 가 남의 인자를 먹는다.
if __name__ == "__main__":
    main()
