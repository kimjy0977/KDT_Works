# -*- coding: utf-8 -*-
"""★데모 대화를 «미리» 돌려 저장한다 — demo_runs.json.

왜 필요한가 (둘)
  1. 캡처   headless 브라우저는 LLM 응답(20~40초)을 기다려 주지 않는다.
            virtual-time 은 «빨리 감기»라 네트워크 대기를 건너뛴다 —
            그래서 1차 캡처가 전부 「파이프라인을 세우는 중…」에서 찍혔다.
  2. 공개    요건이 「API 키를 저장소에 올리지 마세요」라고 못박는다.
            키 없이 화면을 «돌려 볼 수» 있어야 남에게 보여 줄 수 있다.

⇒ 미리 돌린 결과를 담아 두고, app.py 가 ?demo=<이름> 이면 그것을 그린다.
  ⚠ 이건 «녹화»다. 데모 모드에서는 화면에 그렇게 «적는다» —
    실시간인 척하면 보는 사람을 속이는 것이다.

  python make_demo.py --model gpt-5.6-terra
"""
import argparse
import io
import json
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "demo_runs.json"

SCENES = [
    ("논쟁과_이어묻기",
     ["티라노사우루스에 깃털이 있었나요", "그럼 언제 밝혀졌나요"],
     "[논쟁] — 양쪽을 말하는지, 그리고 이어 물어도 맥락을 잇는지"),
    ("신설_검증전",
     ["최근에 발표된 공룡 화석 연구가 있나요"],
     "[신설] — 최근 발표라 «아직 검증되지 않았다»를 붙이는지"),
    ("넘기기와_거절",
     ["한국이 최근 발사한 위성의 현재 궤도 고도가 얼마인가요",
      "제 별자리 운세를 봐주세요"],
     "ESCALATE(모르는 것) 와 REFUSE(안 하는 것) 는 «다른» 판정이다"),
]

KEEP = ("question", "route", "conf", "decision", "reason",
        "context", "used", "answer", "guard", "_sec")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gpt-5.6-terra")
    args = ap.parse_args()

    import agent
    app = agent.build(args.model)

    out = {"model": args.model, "scenes": {}}
    for name, qs, note in SCENES:
        turns, history = [], []
        for q in qs:
            import time as _t
            _t0 = _t.perf_counter()
            s = app.invoke({"question": q, "history": list(history)})
            s["_sec"] = _t.perf_counter() - _t0   # ★화면의 「조사 완료 N초」
            slim = {k: s.get(k) for k in KEEP}
            slim["question"] = q
            turns.append(slim)
            history.append((q, s.get("answer", "")))
            print("  %-18s %-34s -> %s / %s"
                  % (name, q[:32], s.get("route"), s.get("decision")))
        out["scenes"][name] = {"note": note, "turns": turns}

    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(out, ensure_ascii=False, indent=1))
    print("저장:", OUT.name, "· 장면", len(out["scenes"]))

    raw = io.open(OUT, "rb").read()
    bad = len([i for i, b in enumerate(raw) if b < 9 or (13 < b < 32)])
    print("제어문자 %d건" % bad)


if __name__ == "__main__":
    main()
