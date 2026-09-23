# -*- coding: utf-8 -*-
"""★엔드투엔드 — 루브릭 ③ 「전체 워크플로우가 오류 없이 실행되는가」에 «증거»로 답한다.

  python e2e.py            수집은 캐시를 쓴다 (기본)
  python e2e.py --fresh    ★코퍼스를 «지우고» 위키부터 다시 (약 3분 · 키 불필요)

왜 만드나
  「돌아갑니다」는 말이지 증거가 아니다. 레드팀이 먼저 칠 자리다 —
  ★채점자는 «자기 기계»에서 돌린다. 내 기계에서 됐다는 것은 아무 보증이 아니다.
  ⇒ 명령을 «순서대로 실제로» 돌리고, 걸린 시간과 나온 파일을 찍는다.

⛔실패하면 «실패로» 찍는다. 넘어가지 않는다.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
FRESH = "--fresh" in sys.argv

단계 = [
    ("① 코퍼스 수집", ["fetch_corpus.py"], "data/corpus.json",
     "위키 API · 키 불필요"),
    ("② 질문 하나 실행", ["run.py"], "output/run.json",
     "6노드 파이프라인 → 보고서"),
    ("③ 대조군 공정성", ["baseline.py", "--fairness"], None,
     "호출 없이 설정만 대조"),
    ("④ 대조군 실행", ["baseline.py"], "output/baseline.jsonl",
     "혼자 하는 오케스트레이터"),
    ("⑤ 비교 보고서 3편", ["make_compare.py"], "output/reports",
     "축A · 축B · solo — 사람이 읽을 것"),
    ("⑥ 표 찍어내기", ["sync_numbers.py"], None,
     "README·REPORT 의 수치는 여기서 나온다"),
    ("⑦ 레드팀", ["redteam.py"], None, "제출물 자체를 친다"),
]


def main():
    if FRESH:
        for p in ("data/corpus.json", "data/_cache.json"):
            q = os.path.join(HERE, p)
            if os.path.exists(q):
                os.remove(q)
        print("  ★코퍼스를 지웠습니다 — 위키부터 다시 모읍니다\n")

    print("═══ 엔드투엔드 — 루브릭 ③ 「오류 없이 실행되는가」 ═══")
    print("   %s\n" % ("★fresh — 코퍼스부터 새로" if FRESH else "캐시 사용 (--fresh 로 전부 새로)"))

    기록, t_all = [], time.time()
    for 이름, cmd, 산출, 설명 in 단계:
        t0 = time.time()
        r = subprocess.run([PY] + [os.path.join(HERE, cmd[0])] + cmd[1:],
                           cwd=HERE, capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        dt = time.time() - t0
        ok = r.returncode == 0
        있다 = (산출 is None) or os.path.exists(os.path.join(HERE, 산출))
        판정 = "OK  " if (ok and 있다) else "★실패"
        print("  %s %-16s %6.1f초  %s" % (판정, 이름, dt, 설명))
        if not ok:
            print("        ⛔종료코드 %d" % r.returncode)
            for l in (r.stderr or r.stdout or "").strip().splitlines()[-4:]:
                print("        | %s" % l[:100])
        elif 산출 and not 있다:
            print("        ⛔산출물이 안 생겼다: %s" % 산출)
        기록.append({"단계": 이름, "명령": " ".join(cmd), "초": round(dt, 1),
                   "종료코드": r.returncode, "산출물": 산출, "통과": ok and 있다})
        # ★단계마다 «즉시» 적는다 — 마지막에 몰아 쓰면 ⑦ 레드팀이 이 파일을
        #   찾을 때 아직 «없다». 내가 만든 순환이었다(첫 실행에서 실패로 찍혔다).
        io.open(os.path.join(HERE, "output/e2e.json"), "w",
                encoding="utf-8", newline="").write(json.dumps(
                    {"fresh": FRESH, "단계": 기록,
                     "통과": sum(1 for x in 기록 if x["통과"]),
                     "전체": len(단계)}, ensure_ascii=False, indent=1))

    print("\n  총 %.1f초" % (time.time() - t_all))
    n = sum(1 for x in 기록 if x["통과"])
    print("  ★%d / %d 단계 통과" % (n, len(기록)))

    io.open(os.path.join(HERE, "output/e2e.json"), "w",
            encoding="utf-8", newline="").write(
        json.dumps({"fresh": FRESH, "단계": 기록,
                    "통과": n, "전체": len(기록)},
                   ensure_ascii=False, indent=1))
    print("  → output/e2e.json")
    sys.exit(0 if n == len(기록) else 1)


if __name__ == "__main__":
    main()
