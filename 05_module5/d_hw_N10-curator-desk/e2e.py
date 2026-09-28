# -*- coding: utf-8 -*-
"""★전 과정을 «실제로» 돌린다 — 「된다」를 말이 아니라 기록으로 남긴다.

  python e2e.py            수집은 건너뛰고(캐시) 세탁→조회→작성→관문→그래프
  python e2e.py --수집     위키미디어부터 다시 (느리고 429 를 만날 수 있다)

⛔「통과」를 «출력»으로 판정하지 않는다 — 종료코드로 판정한다.
  노드9 피어리뷰 지적 — 경고만 찍고 0 으로 끝나면 e2e 가 통과로 센다.
  ★그리고 파이프 뒤에서 종료코드를 보지 않는다(§A-8) — 여기서 직접 받는다.
"""
import argparse
import io
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
실패 = []
기록 = []


def 돈다(이름, args, 필수=True):
    t0 = time.time()
    r = subprocess.run([PY] + args, cwd=HERE, capture_output=True,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    초 = time.time() - t0
    out = (r.stdout or b"").decode("utf-8", "replace")
    err = (r.stderr or b"").decode("utf-8", "replace")
    ok = r.returncode == 0
    print("  %-26s %s  %5.1f초  (exit %d)"
          % (이름, "OK  " if ok else "⛔FAIL", 초, r.returncode))
    if not ok:
        print("      " + (err.strip().splitlines() or ["(빈 오류)"])[-1][:120])
        if 필수:
            실패.append(이름)
    기록.append({"단계": 이름, "명령": " ".join(args), "종료코드": r.returncode,
               "초": round(초, 1), "끝줄": (out.strip().splitlines() or [""])[-1][:120]})
    return ok, out


def 본다(이름, 조건, 설명=""):
    print("  %-26s %s  %s" % (이름, "OK  " if 조건 else "⛔FAIL", 설명))
    if not 조건:
        실패.append(이름)


def _j(rel):
    p = os.path.join(HERE, rel)
    return json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--수집", action="store_true")
    a = ap.parse_args()

    print("═══ e2e — 전 과정 ═══")
    print()
    if a.수집:
        돈다("① 수집", ["fetch_art.py"])
    else:
        본다("① 수집 (캐시 사용)", os.path.exists(os.path.join(HERE, "data/corpus.json")),
           "--수집 으로 다시 받을 수 있습니다")

    돈다("② 세탁", ["normalize.py"])
    돈다("③ 작가 조회", ["enrich.py"])
    돈다("④ 작성 — 소박", ["write.py"])
    돈다("⑤ 작성 — 조심", ["write.py", "--조심"])
    돈다("⑥ 관문", ["gates.py", "--입력", "data/written_소박.json"])
    돈다("⑦ 비교표", ["compare.py"])
    # ★청소 실패는 «치명»이 아니다 — streamlit 이 sqlite 를 쥐고 있으면
    #   못 지운다. 올림은 같은 thread_id 를 덮어써서 이어 간다.
    ok청소, _ = 돈다("⑧ 그래프 청소", ["graph.py", "--청소"], 필수=False)
    if not ok청소:
        print("      (streamlit 이 떠 있으면 정상입니다 — 이어서 씁니다)")
    ok, out = 돈다("⑨ 그래프 올림", ["graph.py", "--올린다"])
    돈다("⑩ 대기 목록", ["graph.py", "--목록"])

    print()
    print("── 결과가 «말이 되는가» ──")

    깬 = _j("data/clean.json")
    본다("세탁 결과가 있다", bool(깬) and 깬["수"] > 0)
    e = _j("data/enriched.json")
    본다("작가 조회가 붙었다",
       bool(e) and all("작가조회" in m for m in e["작품"]))
    미 = sum(1 for m in (e or {}).get("작품", [])
           if (m.get("작가조회") or {}).get("상태") == "미조회")
    본다("미조회 0건", 미 == 0, "%d건 — 429 였다면 enrich.py 를 다시" % 미)

    소 = _j("data/written_소박.json")
    조 = _j("data/written_조심.json")
    본다("두 작성기 결과가 다르다",
       bool(소) and bool(조)
       and any(x["해설"] != y["해설"] for x, y in zip(소["작품"], 조["작품"])),
       "같으면 비교표에 쓸 것이 없다")

    c = _j("output/compare.json")
    본다("비교표가 두 모드를 다 담았다",
       bool(c) and set(c["모드별"]) == {"소박", "조심"})

    if c:
        # ★기준을 다 켜면 «놓침이 0» 이어야 한다. 아니면 기준이 못 잡는 위험이 있다.
        for 모드 in c["모드별"]:
            for 갈래, d in c["모드별"][모드]["갈래별"].items():
                전부 = max(d["행"], key=lambda r: len(r["기준"]))
                본다("%s/%s — 전부 켜면 놓침 0" % (모드, 갈래),
                   전부["놓침"] == 0, "놓침 %d건" % 전부["놓침"])
        # ★그리고 «아무것도 안 켜면» 놓쳐야 한다 — 아니면 정답이 비어 있다는 뜻
        빈판 = [(모드, 갈래)
              for 모드 in c["모드별"]
              for 갈래, d in c["모드별"][모드]["갈래별"].items()
              if d["정답_멈춰야할것"] == 0]
        print("  %-26s %s  정답이 0 인 칸 %d개 — 그 갈래는 비교가 무의미하다"
              % ("정답이 실재하는가", "OK  " if len(빈판) <= 2 else "⚠WARN",
                 len(빈판)))

    색인 = _j("output/threads.json")
    본다("thread 가 «작품 × 갈래» 로 생겼다",
       bool(색인) and len(색인) > 0
       and all(":" in k for k in 색인))
    대기 = sum(1 for v in (색인 or {}).values() if "끝남" not in v)
    본다("자동 처리와 대기가 «둘 다» 있다",
       0 < 대기 < len(색인 or {1: 1}),
       "대기 %d / 전체 %d — 한쪽이 0 이면 기준이 무르거나 빡빡하다"
       % (대기, len(색인 or {})))
    본다("체크포인터가 «파일»에 있다",
       os.path.exists(os.path.join(HERE, "output/checkpoints.sqlite")),
       "SqliteSaver — 껐다 켜도 대기 건이 남는다")

    # ★재개가 «실제로» 되는지 한 건 돌려 본다
    print()
    print("── 재개 (interrupt → Command(resume=)) ──")
    sys.path.insert(0, HERE)
    import graph
    graph._앱 = None
    w = graph.대기목록()
    본다("대기 판정이 snapshot.next 로 나온다", bool(w),
       "%d건" % len(w))
    if w:
        전 = len(w)
        r = graph.답한다(w[0]["id"], "반려", "e2e 시험")
        후 = len(graph.대기목록())
        본다("답하면 대기가 하나 준다", 후 == 전 - 1, "%d → %d" % (전, 후))
        본다("반려는 «바깥으로 안 나간다»",
           "안 나감" in (r.get("결과") or ""), r.get("결과"))

    # ★재개 시험이 «한 건을 처리»해서 대기 수가 바뀌었다.
    #   문서 수치를 다시 찍고 나서 레드팀을 친다 —
    #   안 그러면 e2e 가 «자기가 바꾼 것» 때문에 자기 검사에 걸린다.
    #   (검사가 제대로 도는 증거이기도 하다 — 실제로 한 번 걸렸다)
    돈다("⑪ 수치 동기화", ["sync_numbers.py"])
    돈다("⑫ 레드팀", ["redteam.py"])

    os.makedirs(os.path.join(HERE, "output"), exist_ok=True)
    io.open(os.path.join(HERE, "output/e2e.json"), "w",
            encoding="utf-8", newline="").write(
        json.dumps({"단계": 기록, "실패": 실패,
                    "python": sys.version.split()[0]},
                   ensure_ascii=False, indent=1))

    print()
    print("═" * 60)
    print("  실패 %d" % len(실패))
    if 실패:
        print("  ⛔" + " · ".join(실패[:6]))
    print("  → output/e2e.json")
    return 1 if 실패 else 0


if __name__ == "__main__":
    sys.exit(main())
