# -*- coding: utf-8 -*-
"""★「몇 점이면 넉넉한가」를 «잰다» — 많을수록 좋다고 말하지 않는다.

판정 = 「표본을 줄였다 늘렸다 할 때 ★수치가 아직 «흔들리는가»」
  흔들리면 부족하다. 가라앉으면 그만하면 된다.

방법 — 같은 코퍼스에서 n점을 «여러 번» 뽑아 개입률을 잰다.
  뽑을 때마다 값이 크게 달라지면 그 n 은 모자란 것이다.
⛔Math.random 을 쓰되 «씨앗을 고정»한다 — 다시 돌려도 같은 답이 나와야 한다.
"""
import io
import json
import os
import random
import statistics
import sys

D = os.path.dirname(os.path.abspath(__file__))
os.chdir(D)
sys.path.insert(0, D)
import gates  # noqa: E402
import compare as CP  # noqa: E402

작품 = json.load(io.open("data/written_소박.json", encoding="utf-8"))["작품"]
N = len(작품)
갈래들 = ("발행", "이미지", "작가", "카탈로그")
반복 = 60

print("  전체 %d점 · 각 크기마다 %d번 뽑아 잰다" % (N, 반복))
print()
print("  %-8s %6s   %s" % ("갈래", "표본", "개입률 (평균 ± 표준편차) · 폭"))
print("  " + "-" * 68)

흔들림 = {}
for 갈래 in 갈래들:
    print("  ── %s ──" % 갈래)
    for n in (10, 20, 30, 40, 60, 80, 120, N):
        if n > N:
            continue
        rnd = random.Random(20260928)      # ★씨앗 고정 — 다시 돌려도 같다
        값 = []
        for _ in range(반복):
            표본 = rnd.sample(작품, n)
            멈 = sum(1 for m in 표본 if gates.잰다(m, 갈래))
            값.append(멈 / n * 100)
        평 = statistics.mean(값)
        편 = statistics.pstdev(값)
        폭 = max(값) - min(값)
        표 = ""
        if 편 >= 8:
            표 = "  ⛔아직 크게 흔들린다"
        elif 편 >= 4:
            표 = "  ⚠흔들린다"
        else:
            표 = "  ✅가라앉았다"
        print("  %-8s %4d점   %5.1f%% ± %4.1f%%p · 폭 %4.1f%%p%s"
              % ("", n, 평, 편, 폭, 표))
        흔들림.setdefault(갈래, {})[n] = 편
    print()

print("  ── ★한 눈에 — 표준편차가 «얼마나 줄었나» ──")
ks = sorted({k for d in 흔들림.values() for k in d})
print("  %-10s" % "갈래" + "".join("%8s" % ("%d점" % k) for k in ks))
for 갈래 in 갈래들:
    d = 흔들림[갈래]
    print("  %-10s" % 갈래 + "".join("%7.1f%%" % d.get(k, 0) for k in ks))

print()
print("  ── ★희귀한 것은 «몇 점»에서 나타나나 ──")
print("     드문 위험은 표본이 작으면 ★한 건도 안 나온다.")
희귀 = [("B1_표시의무위반", "이미지"), ("B2_현대물", "이미지"),
       ("D5_레코드깨짐", "카탈로그"), ("A3_민감장면", "발행"),
       ("C2_작가불명", "작가"), ("D4_연도정밀도", "카탈로그")]
for k, g in 희귀:
    전체적중 = sum(1 for m in 작품 if gates.잰다(m, g, 켠기준={k}))
    비율 = 전체적중 / N
    # 표본 n 에서 «한 건도 안 나올» 확률 ≈ (1-p)^n
    필요 = None
    for n in range(5, 2001):
        if (1 - 비율) ** n < 0.05 if 비율 else False:
            필요 = n
            break
    print("     %-16s 전체 %2d건 (%4.1f%%) → ★95%% 확률로 «한 건은» 보려면 %s점"
          % (k, 전체적중, 비율 * 100,
             ("%d" % 필요) if 필요 else "—(0건이라 계산 불가)"))
