# -*- coding: utf-8 -*-
"""★12강 「더 해보기」 2 — 두 축(능력·안전)을 «한 화면»에. (키 불필요 · 로그만 읽는다)

12강이 시킨 것:
  「라우팅 macro F1·자동화율(Day 1)과 must 통과율·forbid 위반 수·가드레일 차단 수(Day 2)를
   한 표로 묶어 시각화하고, 설정별로 비교합니다.
   ⇒ 에이전트 품질을 «한 숫자»가 아니라 «여러 축»으로 보고하는 습관이 생깁니다.」

★그리고 11강이 말한 두 축:
  능력 — 필요한 사실을 담아 답하는가   tools · must      실패하면 «답을 못 받는다»
  안전 — 하지 말아야 할 것을 안 하는가  forbid · action=ASK  실패하면 «틀린 답을 받는다»

  ⚠ 숫자를 여기서 «다시 계산하지 않는다.» 측정/ 의 로그를 «읽어서» 모은다.
     계산을 두 번 하면 두 값이 갈릴 때 어느 쪽이 맞는지 못 가린다.

  python 07_report.py            # 표
  python 07_report.py --md       # 마크다운 (문서에 붙이기)
"""
import argparse
import io
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
LOG = Path(__file__).parent / "측정"

# (표시 이름, 파일, 비고)
RUNS = [
    ("규칙 라우터", "00_규칙라우터_20260916.txt", "4강 · 모델 호출 0"),
    ("Ollama 지침만", "01_ollama_기본_20260916.txt", "6강 그대로"),
    ("+ fewshot", "02_ollama_fewshot_20260916.txt", "6강 더해보기 1"),
    ("v2 (SHIPPING+OTHER억제)", "04_ollama_v2shipping_20260916.txt", "혼동행렬이 지목"),
    ("v3 (SHIPPING만)", "05_ollama_v3_shipping만_20260916.txt", "가설① 분리검증"),
    ("v4 (금지→포함)", "06_ollama_v4_금지→포함_20260916.txt", "가설② 분리검증"),
    ("★v4 + fewshot", "07_ollama_v4+fewshot_20260916.txt", "최고점"),
]
ANSWER_RUNS = [
    ("2단계 · 적극 조회", "08_ollama_답변_2단계_20260916.txt"),
    ("2단계 · 덜 조회", "09_ollama_답변_ASK살리기_20260916.txt"),
]


def read(name):
    p = LOG / name
    return io.open(p, encoding="utf-8").read() if p.exists() else ""


def pick(text, pat, cast=float, default=None):
    # ★re.M 이 빠져 있어 «^» 가 문자열 처음만 맞았다 — SHIPPING f1 이 전부 «—» 로 나왔다.
    #   숫자를 못 읽은 것을 «없는 것»으로 표시하면, 표를 보는 사람은 측정을 안 한 줄 안다.
    m = re.search(pat, text, re.M)
    return cast(m.group(1)) if m else default


def collect_router():
    rows = []
    for name, f, note in RUNS:
        t = read(f)
        if not t:
            continue
        acc = pick(t, r"정확도 ([\d.]+)")
        f1 = pick(t, r"macro F1 ([\d.]+)")
        osc = pick(t, r"OTHER 로 제대로 보낸 것 \d+건 \(([\d.]+)%\)")
        fail = pick(t, r"구조화 출력 실패 (\d+)건", int, 0)
        ship = pick(t, r"^\s*SHIPPING\s+[\d.]+\s+[\d.]+\s+([\d.]+)", float)
        rows.append({"name": name, "acc": acc, "f1": f1, "osc": osc,
                     "fail": fail, "ship": ship, "note": note})
    return rows


def collect_answer():
    rows = []
    for name, f in ANSWER_RUNS:
        t = read(f)
        if not t:
            continue
        tot = pick(t, r"통과 (\d+) / (\d+)", int)
        m = re.search(r"통과 (\d+) / (\d+)\s+\(([\d.]+)%\)", t)
        ans = re.search(r"ANSWER\s+(\d+)\s+(\d+)\s", t)
        ask = re.search(r"ASK\s+(\d+)\s+(\d+)\s", t)
        tools = pick(t, r"tools 미호출\s+(\d+)", int, 0)
        must = pick(t, r"must 누락\s+(\d+)", int, 0)
        act = pick(t, r"^action\s+(\d+)", int, 0)
        gr = pick(t, r"출처 불명 수치\s+(\d+)", int, 0)
        # ★위험한 실패 = 기대 ASK 인데 실제 ANSWER (11강)
        risky = None
        cm = re.search(r"기대\s*\n(.*?)\n\n", t, re.S)
        mm = re.search(r"^ASK\s+(\d+)\s+(\d+)\s*$", t, re.M)
        if mm:
            risky = int(mm.group(1))
        rows.append({"name": name,
                     "pass": int(m.group(1)) if m else None,
                     "n": int(m.group(2)) if m else None,
                     "rate": float(m.group(3)) if m else None,
                     "ans": ans.group(2) if ans else "-",
                     "ask": ask.group(2) if ask else "-",
                     "tools": tools, "must": must, "action": act,
                     "guard": gr, "risky": risky})
    return rows


def show(md=False):
    r1, r2 = collect_router(), collect_answer()
    bar = (lambda v, hi=1.0, w=18:
           "█" * int(round(w * (v or 0) / hi)) + "·" * (w - int(round(w * (v or 0) / hi))))

    if md:
        print("### ① 의도 분류 — 능력 축과 «안전 축»을 같이 본다\n")
        print("| 설정 | 정확도 | macro F1 | SHIPPING f1 | outscope | 형식실패 | 비고 |")
        print("|---|---|---|---|---|---|---|")
        for r in r1:
            print("| %s | %.3f | **%.3f** | %s | %s | %d | %s |" % (
                r["name"], r["acc"], r["f1"],
                ("%.3f" % r["ship"]) if r["ship"] is not None else "—",
                ("%.1f%%" % r["osc"]) if r["osc"] is not None else "—",
                r["fail"], r["note"]))
        print("\n### ② 1턴 답변 — 총점이 같아도 «성격»이 다르다\n")
        print("| 설정 | 통과 | ANSWER | ASK | ★위험한 실패 | tools 미호출 | must 누락 | 가드레일 차단 |")
        print("|---|---|---|---|---|---|---|---|")
        for r in r2:
            print("| %s | **%d/%d (%.1f%%)** | %s/22 | %s/8 | **%s** | %d | %d | %d |" % (
                r["name"], r["pass"], r["n"], r["rate"], r["ans"], r["ask"],
                r["risky"] if r["risky"] is not None else "—",
                r["tools"], r["must"], r["guard"]))
        return

    print("═" * 78)
    print("  ① 의도 분류 — «능력»(eval)과 «안전»(범위 밖)을 나란히")
    print("═" * 78)
    print("  %-24s %7s %8s  %-20s %8s" % ("설정", "정확도", "macroF1", "macro F1", "범위밖"))
    for r in r1:
        print("  %-24s %7.3f %8.3f  %s %7s" % (
            r["name"], r["acc"], r["f1"], bar(r["f1"]),
            ("%.1f%%" % r["osc"]) if r["osc"] is not None else "—"))
    print()
    print("  ★SHIPPING f1 만 따로 — 혼동 행렬이 지목한 자리가 실제로 올랐나")
    for r in r1:
        if r["ship"] is not None:
            print("  %-24s %6.3f  %s" % (r["name"], r["ship"], bar(r["ship"])))
    print()
    print("═" * 78)
    print("  ② 1턴 답변 — 11강의 두 축")
    print("═" * 78)
    print("  %-20s %14s %8s %8s %12s" % ("설정", "통과", "능력축", "안전축", "★위험한실패"))
    print("  %-20s %14s %8s %8s %12s" % ("", "", "tools미호출", "가드레일", "ASK→ANSWER"))
    for r in r2:
        print("  %-20s %5d/%d (%4.1f%%) %7d %8d %11s" % (
            r["name"], r["pass"], r["n"], r["rate"], r["tools"], r["guard"],
            r["risky"] if r["risky"] is not None else "—"))
    print()
    print("  ⇒ 두 설정의 «총점이 같다». 그런데 위험한 실패 수가 다르다.")
    print("    11강: 「지표를 «하나로» 합치면 이 구분이 사라진다」")
    print("    ⇒ 점수로는 못 고른다. «어느 실패를 감수할지»로 고른다(12강: 도메인이 정한다).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="두 축을 한 화면에 (12강 더해보기 2)")
    ap.add_argument("--md", action="store_true", help="마크다운으로 출력")
    show(ap.parse_args().md)
