# -*- coding: utf-8 -*-
"""★노드가 «일곱 곳» 전부에 등록됐는지 본다 — 가이드 §1-4b 의 자동 검사.

왜 만드나
  가이드에 「노드 하나를 추가하면 일곱 곳을 모두 고쳐야 한다.
  하나라도 빠지면 ★조용히 깨진다」고 적혀 있는데, 사람이 세면 빠진다.
  ★실제로 2026-09-22 전수검사에서 «넷»이 쌓여 있었다 —
    m5n5(섹션 자체 없음) · m5n6 · m5n7 · m5n8(목차·JS 미등록).
  내용은 파일에 있는데 목차에 항목이 없어 «클릭해서 갈 수 없었다».

★핵심 — 기존 「4집합 일치 검사」가 왜 못 잡았나
  4집합(coursehead·data-g·names·order)은 «등록된 것끼리» 맞는지만 본다.
  m5n6~8 은 애초에 네 집합 «전부»에서 빠져 있었으므로 — 일치했다.
  가이드 원문: 「검사가 보는 범위 밖이었기 때문이다.
  검사를 통과한 것이 「다 됐다」는 뜻이 아니다 — 검사는 «자기가 보는 것»만 본다.」

  ⇒ 그래서 이 검사기는 «집합끼리»가 아니라
    ★«파일에 실재하는 섹션»을 기준선으로 삼는다.
    id="{노드}-{무엇}" 인 섹션이 하나라도 있으면 그 노드는 «있는» 것이고,
    있는 노드는 일곱 곳에 다 있어야 한다.

쓰는 법
  python 노드등록-검사.py          검사만
  python 노드등록-검사.py --list   노드별 상세
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NOTE = os.path.join(HERE, "강의노트-모두연.html")
PREFIX = r"(?:adn|m[0-9]+n)[0-9]+"


def measure(s):
    # ★기준선 — 파일에 «실재하는» 노드. 하위 섹션이 있으면 그 노드는 있는 것이다.
    live = set(re.findall(r'<section[^>]*id="(%s)-[^"]*"' % PREFIX, s))
    live |= set(re.findall(r'<section[^>]*coursehead[^>]*id="(%s)"' % PREFIX, s))

    got = {
        "coursehead": set(re.findall(
            r'<section[^>]*class="[^"]*coursehead[^"]*"[^>]*id="(%s)"' % PREFIX, s)),
        "tochead": set(re.findall(r'class="tochead"[^>]*href="#(%s)"' % PREFIX, s)),
        "tocgroup": set(re.findall(r'data-g="(%s)"' % PREFIX, s)),
        "names": set(re.findall(r"'(%s)':'" % PREFIX, s)),
        "order": set(),
    }
    m = re.search(r"order\s*=\s*\[([^\]]*)\]", s)
    if m:
        got["order"] = {x.strip().strip("'\"") for x in m.group(1).split(",") if x.strip()}
    return live, got


def module_of(nid):
    return re.match(r"(adn|m[0-9]+n)", nid).group(1)


def main():
    s = io.open(NOTE, encoding="utf-8", errors="replace").read()
    live, got = measure(s)

    # ⑥⑦ 모듈이 새로 시작할 때만 필요한 둘
    quick = set(re.findall(r'<div class="quick">(.*?)</div>', s, re.S))
    quick_ids = set(re.findall(r'href="#(%s)"' % PREFIX, " ".join(quick)))
    mods = {}
    for nid in sorted(live, key=lambda x: (module_of(x), int(re.sub(r"\D", "", x.split("n")[-1]) or 0))):
        mods.setdefault(module_of(nid), []).append(nid)
    first_of_mod = {v[0] for v in mods.values()}

    print("═══ 노드 등록 검사 — 일곱 곳 ═══")
    print("  파일에 실재하는 노드 %d개\n" % len(live))

    bad = []
    for nid in sorted(live, key=lambda x: (module_of(x), len(x), x)):
        miss = [k for k in ("coursehead", "tochead", "tocgroup", "names", "order")
                if nid not in got[k]]
        if nid in first_of_mod and nid not in quick_ids:
            miss.append("quick(⑥)")
        if miss:
            bad.append((nid, miss))
        if "--list" in sys.argv:
            print("  %-7s %s" % (nid, "✅" if not miss else "★빠짐: " + ", ".join(miss)))

    print()
    if not bad:
        print("  ✅ 전부 등록됨 — 일곱 곳 모두")
    else:
        print("  ★%d개 노드가 «조용히 깨져» 있다" % len(bad))
        for nid, miss in bad:
            print("     %-7s 빠진 곳: %s" % (nid, ", ".join(miss)))
        print()
        print("  ⇒ 가이드 00_log/강의기록-가이드.md §1-4b 를 보고 채운다.")
        print("    목차에 없으면 «내용이 있어도 클릭해서 갈 수 없다».")

    # 참고 — 등록됐는데 섹션이 없는 것(반대 방향)
    ghost = (got["coursehead"] | got["tochead"]) - live
    if ghost:
        print("\n  ⚠ 등록은 됐는데 섹션이 «없는» 것: %s" % sorted(ghost))

    sys.exit(1 if bad else 0)


main()
