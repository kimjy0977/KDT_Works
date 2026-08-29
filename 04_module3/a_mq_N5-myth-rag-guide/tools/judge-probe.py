# -*- coding: utf-8 -*-
"""판정기(LLM-as-a-Judge)를 통제 조건에서 두드려 본다 — 모듈3 노드5 · 8강 2바퀴

왜 필요했나
  1바퀴(A/B)와 2바퀴 기준선(A2)을 비교했더니, **같은 세팅인데 문항 점수가 평균 48.4점**
  움직였다. 그러면 A→B 의 -34.8 점을 «세팅 차이» 로 읽을 수 없다. 잡음이 더 크다.
  그래서 프롬프트를 더 만지기 전에 **자(尺)부터 검사**했다.

무엇을 재나
  ① 결정성   같은 입력을 5회 넣어 판정이 흔들리는지
  ② 방해 민감도  답변을 고정하고 «무관한 근거 조각» 수만 늘려 점수가 변하는지

쓰는 법
    python tools/judge-probe.py determinism
    python tools/judge-probe.py distractors
전제: ollama 가 떠 있고 qwen3.5:2b 가 받아져 있어야 한다.
"""
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
CHUNKS = os.path.join(HERE, "..", "data", "chunks.json")
OLLAMA = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen3.5:2b"

Q = "프로세르피나의 납치는 누가 그렸어?"
ANS = ("제공해주신 자료 [ID: greek-011d6bf12a#meta]에 따르면, 프로세르피나의 납치 작품은 "
       "**페테르 파울 루벤스**가 그렸습니다.")

# judge.ts 의 grounded 루브릭 프롬프트를 그대로 옮긴 것 — 앱과 같은 자로 재기 위해서다.
def build(src):
    return "\n".join([
        "당신은 RAG 챗봇 답변의 평가자입니다. 아래 [질문], [근거자료], [답변]을 읽고 다음 기준 하나만으로 채점합니다.",
        "기준 (근거 충실성): 답변의 모든 사실 주장이 [근거자료]에서 나왔는가. "
        "근거와 무관하거나 모순되는 주장이 섞일수록 감점.",
        "이 기준 외의 다른 품질(문체, 완결성 등)은 보지 않습니다.",
        "score: 0-100 정수, comment: 한 문장 평어(한국어)",
        '출력 형식: {"score":0,"comment":"..."} — JSON 외 텍스트 금지.',
        "", "[질문] " + Q, "", "[근거자료] " + src, "", "[답변] " + ANS,
    ])


def call(prompt, num_ctx=None):
    """앱의 judgeWithOllama 와 같은 옵션(stream:false, think:false, format:json, temp 0)"""
    opts = {"temperature": 0}
    if num_ctx:
        opts["num_ctx"] = num_ctx
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False, "think": False, "format": "json", "options": opts,
    }).encode("utf-8")
    req = urllib.request.Request(OLLAMA, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as res:
        payload = json.loads(res.read())
    return payload["message"]["content"], payload.get("prompt_eval_count")


def load_chunks():
    data = json.load(io.open(os.path.normpath(CHUNKS), encoding="utf-8"))
    target = next(c for c in data
                  if c["id"].startswith("greek-011d6bf12a") and c["id"].endswith("#meta"))
    return target, [c for c in data if c["id"] != target["id"]]


def source_of(target, others, n):
    picked = [target] + others[: n - 1]
    return "\n".join("[{}] {}".format(c["id"], c["text"]) for c in picked)


def determinism():
    """같은 입력 5회 — 판정 자체가 흔들리는지"""
    target, others = load_chunks()
    src = source_of(target, others, 1)
    print("같은 입력 5회 (근거 1조각)")
    for i in range(5):
        raw, toks = call(build(src))
        obj = json.loads(raw)
        print("  {}회 · score={!r} ({}) · 입력토큰 {}".format(
            i + 1, obj.get("score"), type(obj.get("score")).__name__, toks))
    print("\n→ 결과가 모두 같으면 판정기는 결정적이다. 그러면 실행 간 점수 차이의 원인은")
    print("  판정이 아니라 **답변 생성**(temperature 기본값)에 있다.")


def distractors():
    """답변 고정 · 무관한 조각 수만 증가 — 점수가 답변 외의 것에 반응하는지"""
    target, others = load_chunks()
    print("답변은 고정, 근거 조각 수만 늘린다")
    print("조각수 | 입력토큰 | score")
    for n in (1, 5, 10, 15):
        raw, toks = call(build(source_of(target, others, n)))
        print("{:5d}  | {:8} | {}".format(n, toks, json.loads(raw).get("score")))
    # 맥락 창이 원인인지 분리 — 넓혀도 같으면 잘림 문제가 아니다
    raw, toks = call(build(source_of(target, others, 15)), num_ctx=8192)
    print("   15  | {:8} | {}  (num_ctx=8192)".format(toks, json.loads(raw).get("score")))
    print("\n→ 답변이 그대로인데 점수가 움직이면, 이 지표는 «답변 품질» 말고 다른 것도 재고 있다.")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "determinism"
    {"determinism": determinism, "distractors": distractors}[mode]()
