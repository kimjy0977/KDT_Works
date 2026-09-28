# -*- coding: utf-8 -*-
"""★수치를 «찍어낸다» — 손으로 적지 않는다.

  python sync_numbers.py           표식 구간을 «갱신»한다 (문서를 고친다)
  python sync_numbers.py --검사     ★고치지 «않고» 어긋난 곳만 알린다

★⛔`--검사` 를 왜 만들었나 — 실사고 2026-09-28
  `e2e.py` 가 이 스크립트를 «인자 없이» 불렀다. 그런데 `e2e` 는 시험하면서
  ★대기 건을 실제로 처리한다(266 → 261). 그 상태에서 갱신이 돌아
  **문서에 「261건 대기」가 박혔다.** 시험이 문서를 «자기 시험 중 상태»로 덮어썼다.
  ⇒ 채점자가 `e2e.py` 를 한 번 돌리면 README 수치가 틀어진다.
  ★더 나빴던 것 — 내가 `--write` 를 넘기고 있었는데 **파싱조차 안 했다.**
    있는 줄 알았던 플래그가 없었고, 그래서 «항상» 쓰고 있었다.
  ⇒ 시험은 «보기»만 한다. 고치는 것은 사람이 부를 때만.

★왜 — 노드9 에서 실제로 새어 나갔다
  같은 프로젝트가 «두 점수»를 말했다. 골든셋을 고쳐 다시 돌린 뒤
  본문만 고치고 표를 안 고쳐서, ★한 문서 안에서 표는 85.7% 본문은 100%.
  그리고 피어리뷰(김만정님)가 ★%BASE% 같은 «치환 안 된 자리표시자»를
  「잡음을 넘었다」고 선언한 «유일한» 표에서 찾아냈다.

⇒ 규칙 둘
  ① 수치는 output/*.json 에서 «읽어» 찍는다
  ② ★찍고 나서 «남은 자리표시자»를 센다. 0 이 아니면 종료코드 1.
     (만정님 제안 그대로 — 「다음에도 안 놓친다」)
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _j(rel):
    p = os.path.join(HERE, rel)
    return json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else None


CFG = _j("config.json")
깬 = _j("data/clean.json")
E = _j("data/enriched.json")
C = _j("output/compare.json")
색인 = _j("output/threads.json") or {}


def 값들():
    """★모든 수치의 «유일한» 출처. 문서는 여기서만 가져간다."""
    v = {}
    n = (깬 or {}).get("수") or 0
    v["N"] = str(n)
    v["관문수"] = str(len([k for k in CFG["_관문"] if not k.startswith("_")]))
    v["갈래수"] = str(len([k for k in CFG["_갈래"] if not k.startswith("_")]))

    작품 = (E or {}).get("작품") or []
    태그전 = sum(1 for m in 작품
               if "<" in (m.get("_원문", {}).get("저작자") or "")
               or "<" in (m.get("_원문", {}).get("연도") or ""))
    v["세탁전태그"] = str(태그전)
    v["세탁후태그"] = str(sum(1 for m in 작품 if "<" in (m.get("작가") or "")))
    연읽음 = sum(1 for m in 작품 if (m.get("연도") or {}).get("값") is not None)
    v["연도읽음"] = str(연읽음)
    v["연도못읽음"] = str(n - 연읽음)
    v["연단위"] = str(sum(1 for m in 작품
                      if (m.get("연도") or {}).get("정밀도") == 9))
    v["화가확인"] = str(sum(1 for m in 작품
                       if (m.get("작가조회") or {}).get("화가인가") is True))

    전체 = len(색인)
    대기 = sum(1 for x in 색인.values() if "끝남" not in x)
    v["스레드"] = str(전체)
    v["대기"] = str(대기)
    v["자동"] = str(전체 - 대기)
    v["자동률"] = "%.1f%%" % ((전체 - 대기) / 전체 * 100) if 전체 else "—"
    return v


def 표_관문():
    """갈래별 개입률·놓침·헛멈춤 — «전부 켠» 판과 «권장» 판."""
    if not C or "소박" not in C["모드별"]:
        return "_(비교표가 아직 없습니다 — python compare.py)_"
    권 = CFG.get("_권장조합", {})
    줄 = ["| 갈래 | 되돌릴 수 없는 것 | 정답 | 전부 켜면 | 권장 조합 |",
         "|---|---|---|---|---|"]
    for 갈래 in ("발행", "이미지", "작가", "카탈로그"):
        d = C["모드별"]["소박"]["갈래별"][갈래]
        전부set = set(CFG["_갈래"][갈래]["기준"])
        권set = set(권.get(갈래, 전부set))
        f = lambda s: next((r for r in d["행"] if set(r["기준"]) == s), None)
        a, b = f(전부set), f(권set)
        fm = lambda r: ("%.1f%% · 놓침 %d · 헛멈춤 %d"
                        % (r["개입률"] * 100, r["놓침"], r["헛멈춤"])
                        if r else "—")
        줄.append("| **%s** | %s | %d건 | %s | %s |"
                  % (갈래, CFG["_갈래"][갈래]["되돌릴 수 없는 것"][:28],
                     d["정답_멈춰야할것"], fm(a), fm(b)))
    return "\n".join(줄)


def 표_빼기():
    """★「하나 빼기」 — 「이 기준이 밥값을 하나」의 직접 답."""
    if not C or "소박" not in C["모드별"]:
        return "_(비교표가 아직 없습니다)_"
    줄 = ["| 갈래 | 조합 | 개입률 | ★놓침 | 헛멈춤 |", "|---|---|---|---|---|"]
    for 갈래 in ("작가", "카탈로그"):
        d = C["모드별"]["소박"]["갈래별"][갈래]
        전부 = CFG["_갈래"][갈래]["기준"]
        행 = next((r for r in d["행"] if set(r["기준"]) == set(전부)), None)
        if 행:
            줄.append("| **%s** | 전부 | %.1f%% | %d건 | %d건 |"
                      % (갈래, 행["개입률"] * 100, 행["놓침"], 행["헛멈춤"]))
        for k in 전부:
            r = next((x for x in d["행"] if set(x["기준"]) == set(전부) - {k}),
                     None)
            if r:
                줄.append("| | 전부 − %s | %.1f%% | %d건 | %d건 |"
                          % (k.split("_")[0], r["개입률"] * 100,
                             r["놓침"], r["헛멈춤"]))
    return "\n".join(줄)


def 표_작성기():
    """★같은 기준으로 «작성기»를 잰다."""
    if not C or len(C["모드별"]) < 2:
        return "_(두 모드가 다 필요합니다 — python write.py / --조심)_"
    줄 = ["| 갈래 | 작성기 | 개입률 | ★놓침 | 헛멈춤 |", "|---|---|---|---|---|"]
    모드들 = [m for m in ("소박", "조심", "llm") if m in C["모드별"]]
    for 갈래 in ("발행", "작가", "카탈로그"):
        for 모드 in 모드들:
            d = C["모드별"][모드]["갈래별"][갈래]
            r = next((x for x in d["행"]
                      if set(x["기준"]) == set(CFG["_갈래"][갈래]["기준"])), None)
            if r:
                줄.append("| %s | %s | %.1f%% | %d건 | %d건 |"
                          % (갈래 if 모드 == 모드들[0] else "", 모드,
                             r["개입률"] * 100, r["놓침"], r["헛멈춤"]))
    return "\n".join(줄)


def 요약():
    """★한 줄 요약도 «블록»으로 둔다.

    ⛔%자리표시자% 는 «한 번 치환되면 사라진다» — 다시 돌려도 안 고쳐진다.
      실사고 2026-09-28: 재측정으로 자동 처리가 128→127 로 바뀌었는데
      README 는 그대로 128 을 말하고 있었다. ★sync 가 막으려던 바로 그 일이다.
      (노드9 — 같은 프로젝트가 «두 점수»를 말했다)
    ⇒ 다시 찍혀야 하는 수치는 전부 START/END 블록 안에 둔다.
      자리표시자는 «한 번 적고 안 바뀌는 것»에만 쓴다.
    """
    v = 값들()
    return ("올린 **%s**건(작품 %s × 갈래 4) 중 **%s**건이 자동 처리되고 "
            "**%s**건이 대기했습니다 — 자동 **%s**."
            % (v["스레드"], v["N"], v["자동"], v["대기"], v["자동률"]))


def 세탁표():
    v = 값들()
    return ("| | 세탁 전 | 세탁 후 |\n|---|---|---|\n"
            "| 작가명·연도에 HTML 태그 | **%s건** | ★**%s건** |"
            % (v["세탁전태그"], v["세탁후태그"]))


def 한바퀴():
    """★「대기 N건을 한 건씩 보면 몇 분인가」 — §0 의 근거 수치.

    ⛔전에는 «손»으로 적었다. 그래서 표본이 172점으로 늘고 슬러그 충돌을
      고쳐 대기가 251→266 으로 바뀌었을 때, ★문서 네 곳이 251 을 말하고 있었다.
      §6-10 그대로 — 성능 수치를 두 문서에 «손»으로 적으면 갈린다.
    """
    v = 값들()
    n = int(v["대기"])
    return ("대기 **%d건**을 한 건씩 보면 — 한 건 30초면 **%d분**, "
            "10초로 줄여도 **%d분**입니다."
            % (n, round(n * 30 / 60), round(n * 10 / 60)))


블록 = {"관문표": 표_관문, "빼기표": 표_빼기, "작성기표": 표_작성기,
       "요약": 요약, "세탁표": 세탁표, "한바퀴": 한바퀴}


def main():
    # ★「고친다」와 「본다」를 가른다. 시험은 «본다»만 한다.
    검사만 = "--검사" in sys.argv
    v = 값들()
    빠짐 = False
    어긋남 = []
    # ★§F-8-D — 파일 «목록»을 적지 않는다. 목록은 자란다.
    #   ⛔실사고 2026-09-28 — 여기가 ("README.md", "REPORT.md") 열거였다.
    #     DESIGN.md 를 쓰면서 §0 에 수치를 적었는데 ★아무도 안 갱신했다.
    #     문서가 셋이 된 것을 «이 줄»은 몰랐다.
    #   ⇒ 「어떤 파일인가」가 아니라 ★「블록 표식이 있는가」로 고른다.
    #     새 문서를 써도 표식만 넣으면 자동으로 들어온다.
    대상 = sorted(f for f in os.listdir(HERE)
                if f.endswith(".md")
                and ":START -->" in io.open(os.path.join(HERE, f),
                                            encoding="utf-8").read())
    print("  대상 %d개 — %s" % (len(대상), " · ".join(대상)))
    for name in 대상:
        p = os.path.join(HERE, name)
        s = io.open(p, encoding="utf-8").read()
        n0 = len(s)
        hit = []

        for k, f in 블록.items():
            pat = re.compile(r"(<!-- %s:START -->).*?(<!-- %s:END -->)"
                             % (k, k), re.S)
            if pat.search(s):
                s = pat.sub(lambda m: m.group(1) + "\n" + f() + "\n"
                            + m.group(2), s)
                hit.append(k)

        for k, val in v.items():
            if "%" + k + "%" in s:
                s = s.replace("%" + k + "%", val)
                hit.append(k)

        원본 = io.open(p, encoding="utf-8").read()
        if 검사만:
            if s != 원본:
                어긋남.append(name)
            print("  %-4s %-12s [%s]"
                  % ("⛔다름" if s != 원본 else "OK", name,
                     "·".join(sorted(set(hit))[:8])))
        else:
            io.open(p, "w", encoding="utf-8", newline="").write(s)
            print("  갱신  %-12s [%s]  %d -> %d자"
                  % (name, "·".join(sorted(set(hit))[:8]), n0, len(s)))

        # ⛔★남은 자리표시자를 «센다» — 0 이 아니면 실패로 끝낸다
        남은 = re.findall(r"%[A-Z가-힣_]{2,}%", s)
        남은 += re.findall(r"<!-- (\w+):START -->\s*<!-- \w+:END -->", s)
        if 남은:
            print("    ⛔치환 안 된 자리 %d개: %s"
                  % (len(남은), sorted(set(남은))[:6]))
            빠짐 = True

    if 빠짐:
        return 1
    if 검사만 and 어긋남:
        print("  ⛔문서 수치가 «낡았습니다» — %s" % " · ".join(어긋남))
        print("    python sync_numbers.py  로 갱신하세요")
        return 1
    print("  ★남은 자리표시자 0%s" % ("  (검사만 — 문서를 고치지 않았습니다)"
                                 if 검사만 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
