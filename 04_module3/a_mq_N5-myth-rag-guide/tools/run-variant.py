# -*- coding: utf-8 -*-
"""모듈3 노드5 · 8강 3바퀴 — 통제 조건에서 생성 세팅을 비교한다

왜 이 도구가 생겼나
  1·2바퀴는 브라우저로 쟀다. 그러면 질문 하나마다 검색과 생성이 **둘 다** 다시 돈다.
  2바퀴에서 같은 세팅을 재실행했더니 문항 점수가 평균 48.4점 움직였고,
  1바퀴가 본 세팅 차이(-34.8점)가 그 잡음보다 작았다. 그 자로는 아무 결론도 못 낸다.

  그래서 두 가지를 고정했다.
    ① 검색을 한 번만 돌려 **같은 근거 조각을 모든 세팅에 그대로** 쓴다
       (tools/eval-hits.json — 앱의 retrieve()로 뽑은 실제 결과)
    ② 생성에 **temperature 0** 을 준다. 앱 기본값은 온도를 지정하지 않아
       매번 새로 뽑기 때문이다.
  이제 세팅 사이의 차이는 «바꾼 것» 때문만 남는다.

무엇을 비교하나 (세팅 하나당 변수 하나 — 8강)
  base   현행 그대로 (근거 15조각 · 현행 근거 원칙 문구 · qwen3.5:2b)
  prompt 근거 원칙 문구만 교체 — 부당한 거부를 줄이려는 시도
  topk5  프롬프트에 넣는 조각만 15 → 5 (검색 자체는 그대로)
  big    모델만 교체 (--model 로 지정)

쓰는 법
    python tools/run-variant.py base
    python tools/run-variant.py prompt
    python tools/run-variant.py topk5
    python tools/run-variant.py big --model qwen3.5:7b
결과: tools/variant-{이름}.json  (실패한 답도 그대로 남긴다)
"""
import argparse
import io
import json
import os
import sys
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
HITS = os.path.join(HERE, "eval-hits.json")
OLLAMA = "http://127.0.0.1:11434/api/chat"

# ── 앱과 같은 시스템 지시 (App.tsx) ─────────────────────────────────────
SYSTEM = (
    "당신은 신화 명화 아카이브 'MYTH GALLERY'의 안내 도우미입니다. "
    "주어진 자료에 근거한 내용만 답하고, 자료에 없는 정보는 '제가 가진 자료에는 없습니다'라고 답합니다. "
    "근거 조각의 [ID]를 답에 표시합니다. 이 갤러리는 그리스·로마, 북유럽, 이집트, 메소포타미아, 힌두, 중국 "
    "여섯 신화만 다루며, 지금 실린 자료는 그리스·로마 작품입니다. 다루지 않는 신화나 작품을 물으면 "
    "넓혀서 답하지 말고 범위 밖임을 밝힙니다. 작품의 저작권·이용 가부·가격은 판정하지 않고 "
    "갤러리 담당자 문의를 안내합니다."
)

# ── 근거 원칙 문구 (rag.ts buildPrompt) ────────────────────────────────
RULE_BASE = "자료에 근거한 내용만 답하고, 자료에 없으면 없다고 말합니다."

# 바꿔 볼 문구 — 거부의 **조건을 좁힌다**.
# 2바퀴에서 관찰한 실패는 "근거가 있는데도 없다고 자르는" 쪽이었다. 근거를 못 쓰게 막는 대신
# 근거가 있을 때 반드시 쓰라고 먼저 말하고, 거부는 정말 없을 때로 한정한다.
RULE_FIX = (
    "자료에 있는 내용은 반드시 그 자료로 답합니다. "
    "질문의 일부만 자료에 있으면 그 부분을 답하고 나머지만 없다고 말합니다. "
    "질문과 관련된 자료가 하나도 없을 때에만 '제가 가진 자료에는 없습니다'라고 답합니다."
)
RULE_WEAK = ("주의: 검색된 조각의 유사도가 낮습니다. 질문과 완전히 맞는 근거가 아닐 수 있으니, "
             "근거에 있는 내용만 짧게 답하고 자료에 없는 부분은 없다고 말합니다.")

# 판정 루브릭 (judge.ts) — 앱과 같은 기준으로 재야 비교가 성립한다
RUBRICS = [
    ("grounded", "근거 충실성",
     "답변의 모든 사실 주장이 [근거자료]에서 나왔는가. 근거와 무관하거나 모순되는 주장이 섞일수록 감점."),
    ("noHalluc", "환각 통제",
     "[근거자료]에 없는 정보(날짜·숫자·이름·규칙)를 지어내지 않았는가. 지어낸 내용이 하나라도 있으면 0에 가깝게."),
    ("cited", "출처 표시",
     "답변 안에 근거 조각의 [ID] 표시가 있는가. 주장마다 표시했으면 100, 일부만이면 그 비율, 없으면 0."),
]


def call(model, messages, fmt_json=False, temperature=0):
    opts = {"temperature": temperature}
    payload = {"model": model, "messages": messages, "stream": False,
               "think": False, "options": opts}
    if fmt_json:
        payload["format"] = "json"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as res:
        return json.loads(res.read())["message"]["content"]


def build_prompt(question, hits, rule, now="2026년 8월 30일 토요일 오후 12:00"):
    """rag.ts buildPrompt 와 같은 순서 — 자료 소개 → 근거 원칙 → [ID] 요구 → KST → 자료 → 질문"""
    best = hits[0]["score"] if hits else 0
    note = RULE_WEAK if best < 0.55 else rule
    ctx = "\n\n".join("[{} | {}] {}".format(h["id"], h["section"], h["text"]) for h in hits)
    return "\n".join([
        "다음 자료는 신화 명화 아카이브 'MYTH GALLERY'의 공개 작품 페이지에서 뽑은 조각입니다.",
        note,
        "근거가 된 조각의 [ID]를 답 안에서 표시합니다.",
        "현재 시각은 {}(한국 표준시 KST)입니다. '지금', '올해', '다음 주' 같은 상대 표현은 이 시각을 기준으로 해석합니다.".format(now),
        "", "[자료]", ctx, "", "[질문]", question,
    ])


def parse_json(text):
    i, j = text.find("{"), text.rfind("}")
    if i < 0 or j < 0:
        raise ValueError("JSON 없음")
    return json.loads(text[i:j + 1])


def to100(v):
    s = v if isinstance(v, (int, float)) else 0
    if s <= 5:
        s = (s / 5) * 100
    return max(0, min(100, round(s)))


def judge(model, question, hits, answer):
    src = "\n".join("[{}] {}".format(h["id"], h["text"]) for h in hits)
    out = {}
    for rid, name, crit in RUBRICS:
        p = "\n".join([
            "당신은 RAG 챗봇 답변의 평가자입니다. 아래 [질문], [근거자료], [답변]을 읽고 다음 기준 하나만으로 채점합니다.",
            "기준 ({}): {}".format(name, crit),
            "이 기준 외의 다른 품질(문체, 완결성 등)은 보지 않습니다.",
            "score: 0-100 정수, comment: 한 문장 평어(한국어)",
            '출력 형식: {"score":0,"comment":"..."} — JSON 외 텍스트 금지.',
            "", "[질문] " + question, "", "[근거자료] " + src, "", "[답변] " + answer,
        ])
        try:
            j = parse_json(call(model, [{"role": "user", "content": p}], True))
            out[rid + "_s"] = to100(j.get("score"))
            out[rid + "_c"] = str(j.get("comment", ""))[:200]
        except Exception as e:
            out[rid + "_s"] = None
            out[rid + "_c"] = "판정 실패: {}".format(e)
    p = "\n".join([
        "아래 [질문], [근거자료], [답변]을 읽고 판정합니다.",
        "refusal: [근거자료]에 답이 없어서 답변이 '없다/찾을 수 없다'고 답한 경우 true, 그 외 false.",
        '출력 형식: {"refusal":false} — JSON 외 텍스트 금지.',
        "", "[질문] " + question, "", "[근거자료] " + src, "", "[답변] " + answer,
    ])
    try:
        out["refusal"] = parse_json(call(model, [{"role": "user", "content": p}], True)).get("refusal") is True
    except Exception:
        out["refusal"] = None
    got = [out[r + "_s"] for r, _, _ in RUBRICS if out.get(r + "_s") is not None]
    out["score"] = round(sum(got) / len(got)) if got else None
    return out


CITED = __import__("re").compile(r"greek-[0-9a-f]{10}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variant", choices=["base", "prompt", "topk5", "big", "combo"])
    ap.add_argument("--model", default="qwen3.5:2b")
    ap.add_argument("--judge-model", default="qwen3.5:2b")
    args = ap.parse_args()

    rows = json.load(io.open(HITS, encoding="utf-8"))
    # combo = prompt + topk5. 변수 둘을 함께 바꾸므로 «단일 변수 실험»이 아니라
    # 앞의 두 결과를 받아 만든 **후보 설정**이다. 해석할 때 이 점을 잊지 않는다.
    rule = RULE_FIX if args.variant in ("prompt", "combo") else RULE_BASE
    ntop = 5 if args.variant in ("topk5", "combo") else 15

    out = []
    for r in rows:
        hits = r["hits"][:ntop]
        prompt = build_prompt(r["q"], hits, rule)
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
        try:
            ans = call(args.model, msgs, temperature=0)
        except Exception as e:
            ans = "(생성 실패: {})".format(e)
        v = judge(args.judge_model, r["q"], hits, ans)
        out.append({"id": r["id"], "kind": r["kind"], "q": r["q"],
                    "answer": ans, "n_hits": len(hits), "judge": v,
                    "cited": bool(CITED.search(ans))})
        print("  {} {:4} score={} refusal={} cited={} | {}".format(
            r["id"], r["kind"], v.get("score"), v.get("refusal"),
            out[-1]["cited"], ans.replace("\n", " ")[:60]))

    path = os.path.join(HERE, "variant-{}.json".format(args.variant))
    io.open(path, "w", encoding="utf-8", newline="\n").write(
        json.dumps({"variant": args.variant, "model": args.model,
                    "judge_model": args.judge_model, "n_top": ntop, "rows": out},
                   ensure_ascii=False, indent=1))
    ok = [r for r in out if r["judge"].get("score") is not None]
    print("\n세팅 {} · 모델 {} · 조각 {} → 평균 {}점 · 거부 {}건 · 인용 {}건 ({}문항)".format(
        args.variant, args.model, ntop,
        round(sum(r["judge"]["score"] for r in ok) / max(1, len(ok)), 1),
        sum(1 for r in out if r["judge"].get("refusal")),
        sum(1 for r in out if r["cited"]), len(out)))


if __name__ == "__main__":
    main()
