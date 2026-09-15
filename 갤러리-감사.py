#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""갤러리 감사 — 산출물 폴더와 루트 index.html 카드를 대조한다.

왜 있나 (2026-09-14 실사고):
  산출물 폴더 26개 vs 갤러리 링크를 «손으로» 대조했더니 미등재가 4건으로 잡혔다.
  그런데 3건은 «외부 URL 로» 이미 걸려 있었다 —
    a_mq_L7-origin      -> kdt-origin.vercel.app   (Vercel 배포)
    d_hw_N5-pose-image  -> Colab 노트북
    opening-trainer     -> /static/ 하위 경로
  진짜 누락은 c_lab_N7-cardnews 하나였다.
  ⇒ 폴더 경로만 찾으면 «가짜 누락 3건»이 뜬다. 사람이 하나씩 열어봐야 했다.
  ⇒ 그 판별을 기계에 옮긴다.

★이 스크립트의 자리 (TH-20260915-SCOPE 매니저 발언)
  카드 «등재»는 만든 쪽이 한다. 매니저는 «누락 감사»를 진다.
  감사는 판정이 아니라 «그물»이다 — 누가 옳은지 가리는 게 아니라 빠진 걸 줍는다.

쓰는 법
  python 갤러리-감사.py          # 미등재만 출력
  python 갤러리-감사.py --all    # 어떻게 걸려 있는지 전부 출력
"""
import io
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.html")
# ★2026-09-15 추가 — README 도 «보여주는 자리»다(C-1 의 «그릇»).
#   튜터 지적: 이 도구가 index.html «만» 봐서 README 미언급 13건을 못 봤다.
#   감사기가 «자기가 보는 것»만 본다 — §F-8-A ⑪ 의 사촌.
README = os.path.join(HERE, "README.md")

# 산출물 폴더로 세는 최상위 (00_log 는 학습 허브라 갤러리 대상이 아니다)
TOP = re.compile(r"^((?:0[0-9]|9[0-9])_[^/]+/[^/]+)/")
SKIP_TOP = ("00_log/",)


def works():
    """git 이 아는 파일에서 «산출물 폴더»를 뽑는다. 작업트리가 아니라 인덱스 기준."""
    out = subprocess.run(["git", "ls-files"], cwd=HERE, capture_output=True,
                         text=True, encoding="utf-8", errors="replace").stdout
    found = set()
    for p in out.splitlines():
        if p.startswith(SKIP_TOP):
            continue
        m = TOP.match(p)
        if m:
            found.add(m.group(1))
    return sorted(found)


def how_linked(html, folder):
    """그 폴더가 «어떤 형태로» 갤러리에 걸려 있는지 돌려준다.

    ★경로만 보면 «가짜 누락»이 뜬다. 네 가지를 다 본다.
    """
    leaf = folder.split("/")[-1]

    # ① 상대경로 — ./05_module4/c_lab_N7-cardnews/ 또는 그 하위
    if re.search(r'href="\./%s[/"]' % re.escape(folder), html):
        return ("상대경로", folder + "/")
    if re.search(r'href="\./%s/' % re.escape(folder), html):
        return ("상대경로(하위)", folder + "/...")

    # ② GitHub 소스 트리
    m = re.search(r'href="(https://github\.com/[^"]*%s[^"]*)"' % re.escape(folder), html)
    if m:
        return ("GitHub", m.group(1))

    # ③ 외부 배포 — 폴더 이름(잎)이 앵커 텍스트나 근처에 나오는 외부 링크
    #    예: a_mq_L7-origin -> kdt-origin.vercel.app
    for m in re.finditer(r'href="(https?://[^"]+)"', html):
        url = m.group(1)
        if "github.com" in url:
            continue
        ctx = html[max(0, m.start() - 400):m.end() + 400]
        # 잎 이름에서 접두사(a_mq_ 등)와 노드번호를 떼고 핵심 낱말만 본다
        core = re.sub(r"^[a-z]_[a-z]+_", "", leaf)
        core = re.sub(r"^[A-Z]?[0-9]+-", "", core)
        if core and (core.lower() in url.lower() or core.lower() in ctx.lower()):
            return ("외부URL", url)

    # ④ 잎 이름이 본문 어디엔가 언급됨 (링크는 아님)
    if leaf in html:
        return ("언급만", "링크 아님 — 확인 필요")

    return (None, None)


def main():
    show_all = "--all" in sys.argv
    if not os.path.exists(INDEX):
        print("★갤러리가 없다: %s" % INDEX)
        return 2

    html = io.open(INDEX, encoding="utf-8", errors="replace").read()
    rm = io.open(README, encoding="utf-8", errors="replace").read() if os.path.exists(README) else ""
    ws = works()

    linked, missing, unsure = [], [], []
    for w in ws:
        kind, where = how_linked(html, w)
        if kind is None:
            missing.append(w)
        elif kind == "언급만":
            unsure.append((w, where))
        else:
            linked.append((w, kind, where))

    rm_miss = [w for w in ws if w not in rm and w.split("/")[-1] not in rm]

    print("═══ 갤러리 감사 %s ═══" % os.path.basename(HERE))
    print("  산출물 폴더 %d개 · 걸림 %d · ★미등재 %d · 확인필요 %d"
          % (len(ws), len(linked), len(missing), len(unsure)))
    print("  ★README 미언급 %d개  (갤러리와 «따로» 센다 — 둘 다 «그릇»이다)" % len(rm_miss))

    if show_all:
        print()
        print("  ── 걸려 있는 것 (형태별)")
        for w, kind, where in linked:
            print("     %-11s %-42s %s" % (kind, w, str(where)[:52]))

    if unsure:
        print()
        print("  ⚠️ 이름은 나오는데 링크가 아니다 — 눈으로 볼 것")
        for w, why in unsure:
            print("     %-42s %s" % (w, why))

    print()
    if rm_miss:
        print()
        print("  ★README 에 «없는» 것 %d개:" % len(rm_miss))
        for w in rm_miss:
            print("     %s" % w)

    if not missing and not rm_miss:
        print()
        print("  ✅ 미등재 0. 갤러리·README 가 산출물을 전부 덮는다.")
        return 0
    if not missing:
        print()
        print("  ⚠ 갤러리는 전부 덮는다. ★README 만 낡았다.")
        return 1

    print("  ★미등재 %d건 — 카드가 없다:" % len(missing))
    for w in missing:
        print("     %s" % w)
    print()
    print("  ⇒ 만든 쪽이 카드를 넣는다(TH-20260915-SCOPE).")
    print("     링크 전에 «루트가 200인지» 확인할 것 — demo/ 나 static/ 인 경우가 있다.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
