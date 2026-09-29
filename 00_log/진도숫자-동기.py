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
    # ⛔2026-09-29 실사고 — 섹션을 `m5n4-1` 처럼 «숫자» 꼬리만 셌다.
    #   모듈5 노드5~10 은 `m5n8-orch` · `m5n10-why` 처럼 «이름» 꼬리를 쓴다
    #   ⇒ 11섹션을 못 봤고(322 vs 실제 333), 모듈별 줄은 m5n 을 「노드 5」로 찍었다
    #     (섹션이 «숫자로» 붙은 노드만 셌다 — 실제 10).
    #   ★그런데 이 도구는 «자기가 덜 센 값»과 허브를 비교해 「✅ 일치」라 했다.
    #   「0건이 없음인가 못 읽음인가」 — 같은 날 세 번째(A3 글자 조각 · .q 겹침).
    #   ⇒ 꼬리는 무엇이든 센다. 노드 수는 «노드 id» 로 센다.
    #   (옛 첫 두 줄은 PREFIX 가 «그룹»이라 findall 이 접두사만 돌려줘 덮어쓰이던 죽은 줄 — 지움)
    P = r"(?:adn|m1n|m2n|m3n|m4n|m5n|m6n)"
    secs = sorted(set(re.findall(r'id="(%s[0-9]+-[^"\s]+)"' % P, s)))
    nodes = sorted(set(re.findall(r'id="(%s[0-9]+)"' % P, s)))
    per = {}
    for x in nodes:
        p = re.match(r"(adn|m[0-9]+n)", x).group(1)
        per.setdefault(p, {"sec": 0, "node": set()})
        per[p]["node"].add(x)
    for x in secs:
        p = re.match(r"(adn|m[0-9]+n)", x).group(1)
        per.setdefault(p, {"sec": 0, "node": set()})
        per[p]["sec"] += 1
    빈 = [n for n in nodes if not any(x.startswith(n + "-") for x in secs)]
    if 빈:
        print("  ⚠섹션이 하나도 없는 노드 %d: %s — «없음»인지 «못 읽음»인지 볼 것"
              % (len(빈), 빈[:6]))
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
