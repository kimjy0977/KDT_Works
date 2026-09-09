#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""진도 숫자 동기 — 강의노트에서 «세어서» 허브·트래커에 넣는다.

왜 있나 (2026-09-09 실사고 · 하루에 세 번):
  매니저가 강의 섹션을 재서 넣었는데
    07:40 재서 207 -> 10:24 튜터가 11강 추가로 218  (5분)
    09-09 265로 고침 -> 같은 날 튜터가 노드7 추가로 271  (몇 시간)
  ⇒ 사람이 파생값을 옮기는 한 항상 늦는다. §F-8-C(파생값을 근거로 쓰지 말 것)
  ⇒ 원본은 강의노트 하나뿐이다. 거기서 «세어» 넣는다.

쓰는 법
  python 00_log/진도숫자-동기.py           # 재기만 한다(안 고침)
  python 00_log/진도숫자-동기.py --write   # 허브 index.html 까지 고친다

누가 언제
  강의노트를 커밋하는 쪽(튜터)이 같은 커밋에서 --write 로 돌린다.
  매니저는 트래커 값을 이 출력에서 옮긴다(직접 세지 않는다).
"""
import os, re, sys, io, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
NOTE = os.path.join(HERE, "강의노트-모두연.html")
HUB = os.path.join(HERE, "index.html")
OPEN_DATE = datetime.date(2026, 7, 8)
PREFIX = "(adn|m1n|m2n|m3n|m4n|m5n|m6n)"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def measure():
    s = io.open(NOTE, encoding="utf-8", errors="replace").read()
    secs = sorted(set(re.findall(r'id="(%s[0-9]+-[0-9]+)"' % PREFIX, s)))
    nodes = sorted(set(re.findall(r'id="(%s[0-9]+)"' % PREFIX, s)))
    # findall 이 그룹을 돌려주므로 전체 문자열로 다시 뽑는다
    secs = sorted(set(re.findall(r'id="((?:adn|m1n|m2n|m3n|m4n|m5n|m6n)[0-9]+-[0-9]+)"', s)))
    nodes = sorted(set(re.findall(r'id="((?:adn|m1n|m2n|m3n|m4n|m5n|m6n)[0-9]+)"', s)))
    per = {}
    for x in secs:
        p = re.match(r"([a-z]+[0-9]*n?)", x).group(1)
        p = re.match(r"(adn|m[0-9]+n)", x).group(1)
        per.setdefault(p, {"sec": 0, "node": set()})
        per[p]["sec"] += 1
        per[p]["node"].add(x.split("-")[0])
    return secs, nodes, per


def main():
    write = "--write" in sys.argv
    secs, nodes, per = measure()
    today = datetime.date.today()
    week = (today - OPEN_DATE).days // 7 + 1

    print("═══ 강의노트 실측 %s ═══" % today)
    for p in sorted(per, key=lambda k: (k != "adn", k)):
        print("  %-5s 섹션 %3d · 노드 %2d" % (p, per[p]["sec"], len(per[p]["node"])))
    print("  ────────")
    print("  합계  섹션 %d · 노드 %d · 과정 %d주차" % (len(secs), len(nodes), week))

    if not os.path.exists(HUB):
        print("  ★허브 없음 — 재기만 함")
        return
    h = open(HUB, "rb").read()
    cur_node = re.search(rb"(\d+) / (\d+) \xeb\x85\xb8\xeb\x93\x9c", h)
    cur_sec = re.search(rb"(\d+)\xea\xb0\x9c \xeb\x85\xb8\xeb\x93\x9c (\d+)\xec\x84\xb9\xec\x85\x98", h)
    cur_wk = re.search(rb"\xea\xb3\xbc\xec\xa0\x95 (\d+)\xec\xa3\xbc\xec\xb0\xa8", h)

    print()
    print("═══ 허브 현재 표기 ═══")
    print("  노드 진도  %s" % (cur_node.group(0).decode("utf-8") if cur_node else "(못 찾음)"))
    print("  섹션 표기  %s" % (cur_sec.group(0).decode("utf-8") if cur_sec else "(못 찾음)"))
    print("  주차       %s" % (cur_wk.group(0).decode("utf-8") if cur_wk else "(못 찾음)"))

    want = [
        (cur_node, "%d / %d 노드" % (len(nodes), len(nodes))),
        (cur_sec, "%d개 노드 %d섹션" % (len(nodes), len(secs))),
        (cur_wk, "과정 %d주차" % week),
    ]
    stale = [(m, w) for m, w in want if m and m.group(0).decode("utf-8") != w]

    print()
    if not stale:
        print("  ✅ 허브가 실측과 일치한다. 고칠 것 없음.")
        return
    print("  ⚠️낡은 표기 %d건:" % len(stale))
    for m, w in stale:
        print("      %s   →   %s" % (m.group(0).decode("utf-8"), w))
    if not write:
        print()
        print("  (재기만 했다. 고치려면 --write)")
        return
    for m, w in stale:
        h = h.replace(m.group(0), w.encode("utf-8"))
    bad = [b for b in h if b < 32 and b not in (9, 10, 13)]
    if bad:
        print("  ★제어문자 발생 — 쓰지 않음")
        return
    open(HUB, "wb").write(h)
    print()
    print("  ✅ 허브 갱신 완료. 커밋에 같이 담을 것.")


main()
