# -*- coding: utf-8 -*-
"""★비교표 — 기준을 바꿔 가며 개입률·놓침·헛멈춤을 «잰다».

  python compare.py            output/compare.json + 표를 찍는다

> 강의 3강 — 「프로젝트에서 이 비교표를 직접 만듭니다」

★정답을 «기준»으로 만들면 안 된다 — 그러면 동어반복이다
  「전부 켠 기준 = 정답」으로 두면 전부 켠 설정이 «정의상» 만점이 된다.
  재는 것이 아니라 «자기를 자기로» 재는 것이다.

  ⇒ 아래 정답_* 는 ★기준과 «독립된» 도메인 사실이다.
    기준은 이 사실을 «근사»하려는 시도고, 표는 어느 조합이 얼마나 가까운지 본다.
    강의 실습3 의 should_stop 과 같은 자리다.

★세 수치
  개입률   멈춘 비율.                높으면 사람이 다 본다(자동화 아님)
  놓침     ★나갔어야 안 될 것이 나갔다.  ⛔대기 목록에 «안 뜬다» — 제일 비싸다
  헛멈춤   안 나가도 될 것을 멈췄다.    사람 시간을 버린다
"""
import io
import itertools
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gates  # noqa: E402

CFG = gates.CFG
# ⛔★낱말 경계(\b)를 쓰지 않는다 — 「1721년」에서 «1721» 과 «년» 이 둘 다
#   \w 라 경계가 «안 생긴다». 그래서 해설의 연도를 하나도 못 잡고
#   ★정답이 0건으로 나왔다 — 「기준이 잡을 게 없다」처럼 보였다.
#   ⇒ 「0건」이 «없음»인지 «못 읽음»인지 갈라야 한다. 이 프로젝트에서 ★세 번째다
#     (① D1 정규식이 10%만 매치 ② gates CLI 가 글을 안 넘김 ③ 여기).
연4 = re.compile(r"(?<!\d)(1[0-9]{3}|20[0-9]{2})(?!\d)")


# ── ★정답 — 기준과 «독립». 「나가면 실제로 해로운가」만 본다 ──────────

def 정답_발행(m):
    """발행하면 해로운 두 가지 — ①틀린 연도 ②★작품 이야기가 «한 줄도» 없는 카드.

    ⛔①만 두면 A4 가 «부당하게» 벌을 받는다. 실측 —
      전부 46.3%·헛멈춤 21  vs  전부−A4 13.0%·헛멈춤 3.
      A4 가 막는 위험이 ★정답에 없어서 전부 헛멈춤으로 세어졌다.
      ⇒ ★기준을 더했으면 «그 기준이 막는 위험»도 정답에 있어야 한다.
        없으면 표가 「쓸모없다」고 말하는데, 실은 «재지 않은» 것이다.

    ⛔그래도 동어반복은 아니다 — 재는 «대상»이 다르다.
      정답은 ★나갈 «글»을 본다 (작품 문장이 한 줄이라도 있나)
      A4 는   ★«원천»을 본다 (설명 원문 + 근거 표시 [1])
      기준은 정답을 «근사»하려는 시도다.
    """
    글 = m.get("해설") or ""
    if not 글:
        return False

    # ① 원문에 없는 4자리 연도 — 사실 오류
    원 = " ".join([m.get("설명") or "", m.get("_원문", {}).get("연도") or "",
                  m.get("제목") or "", m.get("연도표기") or ""])
    있 = set(연4.findall(원))
    y = m.get("연도") or {}
    for k in ("이른", "늦은"):
        if y.get(k):
            있.add(str(y[k]))
    if {x for x in 연4.findall(글)} - 있:
        return True

    # ② ★「해설 카드」인데 작품 이야기가 한 줄도 없다
    #    제목·연도·작가·라이선스를 뺀 «남는 말»이 거의 없으면 빈 카드다.
    남 = 글
    for 뺄것 in (m.get("제목") or "", m.get("작가") or "",
               m.get("연도표기") or "", m.get("라이선스") or ""):
        if 뺄것:
            남 = 남.replace(뺄것, " ")
    남 = re.sub(r"[\[\]\d년作.,·\s]+", " ", 남).strip()
    남 = re.sub(r"(작가는|이 이미지는|로 배포된다|무제)", " ", 남).strip()
    if len(남) < 12:
        return True

    # ③ ★★원천에 «작품 설명이 없는데» 작품 이야기를 «한다» = 지어내기
    #
    #   ⛔이 줄이 없을 때 실제로 난 일 — 진짜 모델(gpt-4o-mini)로 54점을 쓰게 하니
    #     ★정답이 «0건» 이 나왔다. 「LLM 은 해롭지 않다」는 뜻이 아니라
    #     ★내 정답이 «내가 만든 작성기»에만 맞게 짜여 있었다는 뜻이다.
    #     소박 작성기는 설명이 없으면 «그 줄을 안 쓴다» ⇒ ①②에 안 걸린다.
    #     LLM 은 설명이 없어도 ★«묘사한다» — 「신화의 이야기를 표현하였다」.
    #
    #   ★A4 와 다르다 — A4 는 «원천»만 본다(설명이 있나).
    #     여기는 «원천이 없는데 출력이 말을 하는가»를 본다. 둘의 곱이다.
    설 = (m.get("설명") or "").strip()
    원천있나 = len(re.sub(r"\W+", "", 설)) >= 12 and 설.lower() not in (
        (m.get("제목") or "").lower(), (m.get("작가") or "").lower())
    return (not 원천있나) and len(남) >= 25


def 정답_이미지(m):
    """퍼블릭도메인·CC0 가 아닌데 «표시할 저작자»가 없다 → 법적으로 재배포 불가."""
    lic = (m.get("라이선스") or "").lower()
    표시불요 = any(k in lic for k in
                ["public domain", "pd-", "cc0", "pd "])
    if 표시불요 or not lic:
        return False
    return gates._불명(m.get("작가"))


def 정답_작가(m):
    """Artist 가 «그림을 그린 사람»이라고 확인되지 않았다 → 엉뚱한 사람 소개."""
    return (m.get("작가조회") or {}).get("화가인가") is not True


def 정답_카탈로그(m):
    """카탈로그에 실릴 연도 표기가 «실제 정밀도보다 좁다» → 없는 정밀도 생성.

    ⛔기준 D4 와 다르다 — D4 는 「해설에 N년이라 썼나」를 본다.
      정답은 「카탈로그 «값»이 실제보다 좁은가」다.
    """
    y = m.get("연도") or {}
    if y.get("속성깨짐"):
        return True
    글 = m.get("해설") or ""
    h = re.search(r"(\d{3,4})\s*년(?!대)", 글)
    if not h:
        return False
    return y.get("정밀도") != 9


정답 = {"발행": 정답_발행, "이미지": 정답_이미지,
       "작가": 정답_작가, "카탈로그": 정답_카탈로그}


# ── 재기 ────────────────────────────────────────────────────────

def 한판(작품, 갈래, 켠기준):
    """⚠켠기준을 «반드시» 넘긴다 — None 이면 잰다()가 권장조합을 쓴다.
    그러면 표가 «자기가 정한 것»을 재게 되어 동어반복이 된다."""
    """한 조합으로 전 건을 재서 개입률·놓침·헛멈춤을 낸다."""
    n = len(작품)
    멈춤 = 놓침 = 헛멈춤 = 0
    for m in 작품:
        섰다 = bool(gates.잰다(m, 갈래, 켠기준=켠기준))
        서야 = 정답[갈래](m)
        if 섰다:
            멈춤 += 1
            if not 서야:
                헛멈춤 += 1
        elif 서야:
            놓침 += 1
    return {"기준": sorted(켠기준), "개입률": 멈춤 / n, "멈춤": 멈춤,
            "놓침": 놓침, "헛멈춤": 헛멈춤,
            "놓침률": 놓침 / n, "헛멈춤률": 헛멈춤 / n}


def 조합들(갈래):
    """★없음 → 쌓기 → 단독 → ★하나 빼기.

    「하나 빼기」가 제일 쓸모 있다 — 「이 기준이 «밥값»을 하나」의 직접 답이다.
    쌓기만 보면 나중에 켠 기준이 다 잘하는 것처럼 보인다(순서 탓).
    """
    전부 = CFG["_갈래"][갈래]["기준"]
    out = [set()]
    쌓 = set()
    for k in 전부:
        쌓 = 쌓 | {k}
        out.append(set(쌓))
    for k in 전부:                      # 하나만 켠 판 — 각 기준의 «단독» 힘
        out.append({k})
    if len(전부) > 1:
        for k in 전부:                  # ★하나 빼기 — 빼도 그대로면 군더더기다
            out.append(set(전부) - {k})
    보 = []
    for s in out:
        if s not in 보:
            보.append(s)
    return 보


def 이름(s, 전부):
    if not s:
        return "없음(전부 자동)"
    if set(s) == set(전부):
        return "전부"
    빠진 = set(전부) - set(s)
    if len(빠진) == 1 and len(전부) > 2:
        return "전부 − " + list(빠진)[0].split("_")[0]
    return "+".join(k.split("_")[0] for k in 전부 if k in s)


def main():
    결과 = {"모드별": {}}
    for 모드 in ("소박", "조심", "llm"):
        p = os.path.join(HERE, "data/written_%s.json" % 모드)
        if not os.path.exists(p):
            print("  ⚠data/written_%s.json 없음 — 건너뜀" % 모드)
            continue
        작품 = json.load(io.open(p, encoding="utf-8"))["작품"]
        n = len(작품)
        결과["모드별"][모드] = {"수": n, "갈래별": {}}

        print("╔" + "═" * 74)
        print("║  작성 «%s» · %d점" % (모드, n))
        print("╚" + "═" * 74)
        for 갈래 in ("발행", "이미지", "작가", "카탈로그"):
            전부 = CFG["_갈래"][갈래]["기준"]
            서야할것 = sum(1 for m in 작품 if 정답[갈래](m))
            rows = [한판(작품, 갈래, s) for s in 조합들(갈래)]
            결과["모드별"][모드]["갈래별"][갈래] = {
                "정답_멈춰야할것": 서야할것, "행": rows}
            print()
            print("  ── %s ── ★정답: %d/%d 가 멈췄어야 한다 (%4.1f%%)"
                  % (갈래, 서야할것, n, 서야할것 / n * 100))
            print("     %-26s %8s %8s %8s"
                  % ("기준 조합", "개입률", "★놓침", "헛멈춤"))
            print("     " + "-" * 54)
            for r, s in zip(rows, 조합들(갈래)):
                print("     %-26s %7.1f%% %6d건 %6d건"
                      % (이름(s, 전부)[:26], r["개입률"] * 100,
                         r["놓침"], r["헛멈춤"]))
        print()

    # ★모드 간 비교 — 같은 기준으로 «작성기»를 잰다
    if len(결과["모드별"]) >= 2:
        print("╔" + "═" * 74)
        print("║  ★작성기를 바꾸면 — 같은 «전부» 기준으로")
        print("╚" + "═" * 74)
        print("     %-12s %-10s %8s %8s %8s"
              % ("갈래", "작성기", "개입률", "★놓침", "헛멈춤"))
        print("     " + "-" * 54)
        모드들 = [m for m in ("소박", "조심", "llm") if m in 결과["모드별"]]
        for 갈래 in ("발행", "이미지", "작가", "카탈로그"):
            for 모드 in 모드들:
                rs = 결과["모드별"][모드]["갈래별"][갈래]["행"]
                r = next((x for x in rs
                          if set(x["기준"]) == set(CFG["_갈래"][갈래]["기준"])),
                         None)
                if not r:
                    continue
                print("     %-12s %-10s %7.1f%% %6d건 %6d건"
                      % (갈래 if 모드 == 모드들[0] else "", 모드,
                         r["개입률"] * 100, r["놓침"], r["헛멈춤"]))
        print()

    os.makedirs(os.path.join(HERE, "output"), exist_ok=True)
    p = os.path.join(HERE, "output/compare.json")
    io.open(p, "w", encoding="utf-8", newline="").write(
        json.dumps(결과, ensure_ascii=False, indent=1))
    print("  → output/compare.json")

    # ★§F-8-D 3단계 ① — 방금 쓴 파일을 그 자리에서 검사
    s = io.open(p, encoding="utf-8").read()
    if [i for i, ch in enumerate(s) if ord(ch) < 32 and ch != "\n"]:
        print("  ⛔제어문자 있음")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
