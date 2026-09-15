#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""파생값 동행 검사 — 원본을 고치면 파생값도 «같은 커밋»에 있나 (A-1).

  python 00_log/파생값-동행검사.py        # 스테이지를 검사. 경고만 출력
  종료코드 0 = 통과 또는 경고(차단 안 함) · 2 = 검사 자체를 못 했다

왜 있나 (토론 TH-20260915-SCOPE · E-5 · 실측 2026-09-15):
  규칙(A-1)도 도구(`진도숫자-동기.py`)도 문서도 있었는데
  **섹션 수가 변한 커밋 3건 중 2건에서 허브를 안 고쳤다.**
    685cfba 09-11  271→283  허브 X   ★위반
    6c25a54 09-14  283→297  허브 O   준수
    a787dad 09-15  297→305  허브 X   ★위반  ← 「어긴 건 나다」라고 적은 당일
  ⇒ 「튜터 소관」이라고 더 적는 것은 의미가 없다. **커밋이 물어봐야 한다.**
  ⇒ §F-8-D 3단계(시점 기반) — 범위를 기억하지 않고 «만지는 그 순간» 검사한다.

★판정 대상은 «파일 변경»이 아니라 «파생값 변화»다.
  실측 6건 중 섹션 수가 실제로 변한 건 3건뿐이었다(나머지는 오타·문구).
  파일 기준이면 헛경고가 «절반»이고, **절반이 헛경고면 경고를 안 읽게 된다.**
  그 순간 훅은 없는 것과 같다.

★세는 자는 `진도숫자-동기.py` 와 «같은» 정규식이다.
  다른 자로 재면 또 어긋난다 — 2026-09-15 하루에 네 번 그렇게 어긋났다.

★차단하지 않는다(경고만).
  차단하면 `--no-verify` 가 습관이 되고, 그러면 훅 전체가 무력해진다.
"""
import re
import subprocess
import sys

# ★윈도 git 훅은 콘솔이 cp949 라 «⚠·«»» 를 못 찍고 UnicodeEncodeError 로 죽는다.
#   그러면 **경고해야 할 바로 그 순간에 아무 말도 안 나온다** — 이 검사기가
#   막으려는 바로 그 실패 방식이다. 실측 2026-09-15: 케이스2 시험에서 그대로 났다.
#   ⇒ utf-8 로 바꾸고, 그것도 안 되면 못 찍는 글자를 «버리고라도» 출력한다.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        try:
            _s.reconfigure(errors="replace")
        except Exception:
            pass

NOTE = "00_log/강의노트-모두연.html"
HUB = "00_log/index.html"
# ★`진도숫자-동기.py` 와 동일 — 한쪽만 고치면 두 도구가 다른 값을 말한다
PAT = re.compile(r'id="((?:adn|m1n|m2n|m3n|m4n|m5n|m6n)[0-9]+-[0-9]+)"')


def run(*args):
    p = subprocess.run(list(args), capture_output=True)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def staged_files():
    code, out = run("git", "-c", "core.quotepath=false",
                    "diff", "--cached", "--name-only")
    return set(out.split("\n")) if code == 0 else set()


def count(ref):
    """ref 시점의 강의노트 섹션 수. 파일이 없으면 None."""
    code, out = run("git", "show", "%s:%s" % (ref, NOTE))
    if code != 0:
        return None
    return len(set(PAT.findall(out)))


def main():
    files = staged_files()
    if NOTE not in files:
        return 0                      # 강의노트를 안 건드렸다 — 할 말 없음

    now = count("")                   # "":NOTE = 스테이지(인덱스)
    was = count("HEAD")
    if now is None or was is None:
        print("[동행검사] 검사를 «못 했다» — 강의노트를 읽지 못함", file=sys.stderr)
        return 2                      # ★조용히 통과시키지 않는다

    if now == was:
        return 0                      # 파생값이 안 변했다 — 경고할 것 없음
    if HUB in files:
        return 0                      # 같은 커밋에 있다 — A-1 준수

    print("")
    print("[동행검사] ⚠ 강의노트 섹션 수가 %d → %d 로 «변했는데»" % (was, now))
    print("           %s 가 이 커밋에 없습니다." % HUB)
    print("")
    print("  A-1 — 원본을 고치는 «그 커밋»에서 파생값도 같이 간다.")
    print("  (규칙·도구·문서가 다 있었는데 3건 중 2건을 빠뜨린 자리입니다)")
    print("")
    print("  고치려면:")
    print("      python 00_log/진도숫자-동기.py --write")
    print("      git add 00_log/index.html")
    print("")
    print("  섹션 수 변화가 «의도한 것이 아니면» 무엇이 늘었는지 먼저 보세요.")
    print("")
    return 0                          # ★경고만. 차단하지 않는다


if __name__ == "__main__":
    sys.exit(main())
