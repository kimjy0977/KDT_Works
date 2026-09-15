"""진입점 — graph.py 는 «불러오기만 해도» 안전해야 한다 (11강).

  python run.py                 # dry-run (기본 · 보내지 않음)
  python run.py --send          # 실제로 디스코드에 발행
  python run.py --hours 48      # 시간 창을 넓혀 본다
"""
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:
    pass

# ★프로필은 «import 전»에 정해야 한다 — graph.py 가 불러올 때 설정 파일을 읽기 때문이다.
#   (13강: 코드는 안 고치고 «설정 파일만» 갈아 끼운다)
#   --profile discovery  →  audience_discovery.yaml + settings_discovery.yaml
if "--profile" in sys.argv:
    os.environ["PROFILE"] = sys.argv[sys.argv.index("--profile") + 1]

from graph import run, llm_backend   # noqa: E402


def main():
    argv = sys.argv[1:]
    os.environ["DRY_RUN"] = "0" if "--send" in argv else "1"
    hours = None
    if "--hours" in argv:
        hours = argv[argv.index("--hours") + 1]

    print("=" * 74)
    print("뉴스레터 에이전트 · 프로필 %s · 백엔드 %s · %s"
          % (os.environ.get("PROFILE") or "기본(AI)", llm_backend(),
             "실제 발행" if os.environ["DRY_RUN"] == "0" else "dry-run"))
    print("=" * 74)

    out = run(hours=hours)

    print()
    print("─" * 74)
    for line in out["log"]:
        print(line)
    m = out["_metrics"]
    print("─" * 74)
    print("깔때기  수집 %d → 선별 %d → 취재 %d → 발행 %d   (%.1fs)"
          % (m["collected"], m["picked"], m["drafted"], m["published"], m["elapsed_s"]))
    if m["by_source"]:
        print("소스별  " + " · ".join("%s %d" % (k, v) for k, v in m["by_source"].items()))
    print("기록    store/metrics.jsonl 에 한 줄 추가")


if __name__ == "__main__":
    main()
