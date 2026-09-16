# -*- coding: utf-8 -*-
"""★제출본을 만든다 — 원본 실행 폴더는 «그대로» 두고 사본을 뜬다.

§6-10 (제출물 규율):
  「제출용 사본을 만들 때 — 원본 실행 폴더는 그대로 두고 «사본»을 만든다.
   ⛔「원문을 제외한다」는 이유로 실패 시행·불리한 점수 행을 삭제하지 않는다.
   제외한 «경로와 이유», «원본을 다시 준비하는 방법»을 목록으로 남긴다.」

★무엇을 빼는가 — 이유와 함께
    .env               키. 절대 금지. (.gitignore 에 있지만 복사 단계에서도 막는다)
    .venv/             환경. requirements 로 재현한다
    data/              퍼실 배포 데이터 — ensure_data() 가 공개 저장소에서 받아온다
    *.zip              퍼실 배포 원본
    modumall-agent-data/  위 zip 을 푼 것 (data/ 와 같은 내용)
    __pycache__ ·*.pyc  빌드 산출물

★무엇을 «남기는가» — 불리한 것도 그대로
    측정/ 전부         ★실패한 시행도 뺀다 없이 남긴다.
                      「20/20 형식 실패」·「ASK 0/8」·「가설 두 번 기각」이 여기 있다.
    원본 코드 그대로     router.py·answer.py 등은 «한 줄도» 안 고쳤음을 보이기 위해 포함

  python 99_제출본만들기.py            # 미리보기
  python 99_제출본만들기.py --write    # 실제 복사
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SRC = Path(__file__).parent
DST_DEFAULT = (SRC.parents[3] / "00_shared" / "repos" / "KDT_Works"
               / "05_module5" / "c_lab_N4-routing-grounding")

# (패턴, 왜 빼는가)
EXCLUDE = [
    (".env", "★API 키. 절대 금지"),
    (".venv", "가상환경 — requirements.txt 로 재현"),
    ("__pycache__", "빌드 산출물"),
    (".pyc", "빌드 산출물"),
    ("modumall-agent-data.zip", "퍼실 배포 원본"),
    ("modumall-agent-src.zip", "퍼실 배포 원본"),
    ("modumall-agent-data/", "위 zip 을 푼 것 — data/ 와 동일"),
    ("/data/", "퍼실 배포 데이터 — ensure_data() 가 받아온다"),
]


def excluded(rel):
    s = "/" + rel.replace("\\", "/")
    for pat, _ in EXCLUDE:
        if pat.startswith("/") or pat.endswith("/"):
            if pat in s + "/":
                return pat
        elif ("/" + pat) in s or s.endswith(pat):
            return pat
    return None


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="제출본 만들기")
    ap.add_argument("--write", action="store_true", help="실제로 복사한다")
    ap.add_argument("--dst", default=str(DST_DEFAULT))
    args = ap.parse_args()
    dst = Path(args.dst)

    keep, drop = [], {}
    for p in sorted(SRC.rglob("*")):
        if p.is_dir():
            continue
        rel = str(p.relative_to(SRC))
        why = excluded(rel)
        if why:
            drop.setdefault(why, []).append(rel)
        else:
            keep.append((rel, p.stat().st_size))

    print("=== 제출본 ===")
    print("   원본 %s" % SRC)
    print("   대상 %s" % dst)
    print()
    print("[남기는 것 %d개 · %.0fKB]" % (len(keep), sum(s for _, s in keep) / 1024))
    for rel, size in keep:
        print("   %8d  %s" % (size, rel))
    print()
    print("[★빼는 것 — 이유와 함께]")
    for why, files in drop.items():
        print("   %-28s %2d개  ← %s"
              % (why, len(files), dict(EXCLUDE).get(why, "")))
        for f in files[:3]:
            print("        %s" % f)
        if len(files) > 3:
            print("        … 외 %d개" % (len(files) - 3))
    print()
    print("[원본을 다시 준비하는 법]")
    print("   1) python -m venv .venv")
    print("   2) .venv/Scripts/python -m pip install -r modumall-agent/requirements.txt \\")
    print("      langchain-ollama python-dotenv streamlit")
    print("   3) ollama pull qwen3.5:2b qwen2.5:7b")
    print("   4) data/ 는 첫 실행 때 ensure_data() 가 자동으로 받는다")
    print("   5) OpenAI 로 돌리려면 modumall-agent/.env 에 OPENAI_API_KEY 를 채운다")
    print()

    # ★키가 섞여 나가지 않는지 «마지막에 한 번 더» 확인한다
    leak = [rel for rel, _ in keep
            if any(k in rel for k in (".env", "key", "secret", "token"))]
    print("[안전 점검] 이름에 키/토큰이 들어간 파일: %s" % (leak if leak else "없음 ✅"))

    if not args.write:
        print()
        print("   (미리보기입니다. 실제로 복사하려면 --write)")
        sys.exit(0)

    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for rel, _ in keep:
        t = dst / rel
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SRC / rel, t)
        n += 1
    print()
    print("   ✅ %d개 복사 완료 → %s" % (n, dst))

    # ★복사본에 키가 없는지 «내용»으로 확인 — 이름만 보면 놓친다
    import re
    bad = []
    for p in dst.rglob("*"):
        if p.is_file() and p.suffix in (".py", ".md", ".txt", ".json", ".csv", ".example"):
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if re.search(r"sk-(proj-)?[A-Za-z0-9_-]{30,}", t):
                bad.append(str(p.relative_to(dst)))
    print("   [내용 점검] 실제 키 문자열이 든 파일: %s" % (bad if bad else "없음 ✅"))
