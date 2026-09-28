# -*- coding: utf-8 -*-
"""★해설·작가소개를 «쓴다» — 그리고 관문이 그걸 잡는다.

  python write.py              소박한 작성기 (기본)
  python write.py --조심       정밀도를 지키는 작성기
  python write.py --llm        OPENAI_API_KEY 가 있으면 모델로

★왜 «소박한» 작성기가 기본인가 — 이게 설계의 핵심이다
  작성기가 처음부터 완벽하면 A1·A2·D4 가 ★0건이 되고,
  「기준이 있으나 마나」(강의 3강)가 된다. 비교표에 쓸 것이 없어진다.

  그런데 여기서 «일부러 틀리게» 만들면 그건 조작이다.
  ⇒ ★그럴 필요가 없다. LLM 이든 사람이든 «자연스럽게» 하는 실수가 있다:

      연도 필드에 1500 이 있으니 「1500년作」이라 쓴다
        ← 정밀도가 «천년기»인 줄 모른다. ★220년 틀린다
      설명이 비었는데도 그럴듯한 문장을 만든다
        ← 근거 표시를 달 데가 없다
      원문에 없는 숫자를 덧붙인다
        ← 「17세기 중반」 같은 말이 숫자로 굳는다

  소박한 작성기는 «이 실수를 그대로» 한다. 조작이 아니라 재현이다.
  --조심 은 같은 자료로 정밀도를 지켜 쓴다 ⇒ ★둘을 비교표에 나란히 둔다.

★근거 표시 규약
  [1] 설명  [2] 라이선스·저작자  [3] 연도  [4] 위키데이터 작가 문서
  근거가 0개면 A2 가 잡는다 — 「지어낸 글」의 기계적 정의다.
"""
import argparse
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(io.open(os.path.join(HERE, "config.json"), encoding="utf-8"))


def _잘라(s, n):
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def _읽은직업(r):
    """★«이름을 아는» 직업만 남긴다.

    ⛔Q5322166 처럼 사전에 없는 Q번호를 그대로 쓰면
      ①사람이 못 읽고 ②그 «숫자»가 A1 의 「원문에 없는 숫자」로 세어진다.
      실측 — A1 이 60%를 잡은 원인 중 하나였다.
    """
    return [d for d in (r.get("직업") or []) if not d.startswith("Q")]

# ── 소박한 작성기 — ★LLM 이 하듯 «값을 그대로» 쓴다 ─────────────────

def 해설_소박(m):
    설 = _잘라(m.get("설명"), 220)
    연 = (m.get("연도") or {}).get("값")
    줄 = []
    if 연:
        # ⛔★정밀도를 안 본다. 값이 1500 이면 「1500년作」.
        #   D4 가 여기를 잡는다 — 그게 이 기준이 있는 이유다.
        줄.append("%s, %d년作." % (m.get("제목") or "무제", 연))
    else:
        줄.append("%s." % (m.get("제목") or "무제"))
    if 설:
        줄.append("%s [1]" % 설)
    작 = m.get("작가")
    if 작 and 작.lower() not in ("unknown author", "anonymous"):
        줄.append("작가는 %s. [2]" % 작)
    lic = m.get("라이선스")
    if lic:
        줄.append("이 이미지는 %s 로 배포된다. [2]" % lic)
    return " ".join(줄)


def 작가소개_소박(m):
    r = m.get("작가조회") or {}
    이 = m.get("작가") or "작자 미상"
    줄 = ["%s." % 이]
    if r.get("상태") == "조회됨":
        생 = (r.get("생") or {}).get("연")
        몰 = (r.get("몰") or {}).get("연")
        if 생 and 몰:
            줄.append("%d년에 나 %d년에 졌다. [4]" % (생, 몰))
        elif 생:
            # ⛔★몰년이 없는데 「활동 중」이라고 «단정»한다 — C3 가 잡는다
            줄.append("%d년생이며 지금도 활동 중이다. [4]" % 생)
        직 = _읽은직업(r)
        if 직:
            줄.append("직업은 %s. [4]" % "·".join(직[:3]))
    else:
        # 조회가 안 됐는데도 «그럴듯하게» 쓴다 — 근거가 없다 ⇒ A2 가 잡는다
        줄.append("바로크 시대를 대표하는 거장으로 평가받는다.")
    return " ".join(줄)


# ── 조심하는 작성기 — 같은 자료로 «정밀도를 지켜» 쓴다 ───────────────

def 해설_조심(m):
    설 = _잘라(m.get("설명"), 220)
    줄 = ["%s, %s. [3]" % (m.get("제목") or "무제",
                          m.get("연도표기") or "제작연도 미상")]
    if 설:
        줄.append("%s [1]" % 설)
    작 = m.get("작가")
    r = m.get("작가조회") or {}
    if 작 and r.get("화가인가") is True:
        줄.append("작가는 %s. [2]" % 작)
    elif 작:
        # ★확인 못 한 이름을 「작가」라고 «부르지 않는다»
        줄.append("Commons 의 저작자 항목에는 %s 가 적혀 있다. [2]" % 작)
    lic = m.get("라이선스")
    if lic:
        줄.append("이 이미지는 %s 로 배포된다. [2]" % lic)
    return " ".join(줄)


def 작가소개_조심(m):
    r = m.get("작가조회") or {}
    이 = m.get("작가") or "작자 미상"
    if r.get("상태") != "조회됨":
        # ★「모른다」도 «근거 있는» 진술이다 — 조회 결과가 근거다.
        #   ⛔[4] 를 안 달면 A2 가 이걸 「지어낸 글」로 센다(실측 18건).
        #     그런데 이 문장은 지어낸 게 아니라 ★지어내기를 «거부»한 것이다.
        return ("%s — 위키백과에서 이 이름을 확인하지 못했습니다(%s). [4] "
                "확인 전에는 작가로 소개하지 않습니다." % (이, r.get("상태")))
    생 = (r.get("생") or {}).get("연")
    몰 = (r.get("몰") or {}).get("연")
    줄 = ["%s (%s)." % (r.get("레이블") or 이,
                       "%s~%s" % (생 or "?", 몰 or "?"))]
    if 생 and 몰:
        줄.append("%d년에 나 %d년에 졌다. [4]" % (생, 몰))
    elif 생:
        줄.append("%d년생. ★몰년이 확인되지 않았습니다. [4]" % 생)
    직 = _읽은직업(r)
    if 직:
        줄.append("위키데이터가 기록한 직업은 %s. [4]"
                  % "·".join(직[:3]))
    return " ".join(줄)


# ── LLM — 키가 있으면. ⛔없으면 «조용히» 소박으로 안 떨어진다 ────────

def _llm(prompt):
    from openai import OpenAI
    c = OpenAI()
    r = c.chat.completions.create(
        model="gpt-4o-mini", temperature=0.4,
        messages=[
            {"role": "system", "content":
             "너는 미술관 큐레이터다. ★주어진 자료에 «있는 것만» 쓴다. "
             "문장 끝에 근거를 [1][2][3][4] 로 단다. "
             "[1]=설명 [2]=라이선스·저작자 [3]=연도 [4]=작가 문서. "
             "3문장 이내, 한국어 존대 없이 설명체."},
            {"role": "user", "content": prompt}])
    return (r.choices[0].message.content or "").strip()


def 해설_llm(m):
    자 = json.dumps({
        "제목": m.get("제목"), "설명": m.get("설명"),
        "연도원문": (m.get("연도") or {}).get("원문"),
        "연도표기": m.get("연도표기"),
        "라이선스": m.get("라이선스"), "저작자": m.get("작가"),
    }, ensure_ascii=False, indent=1)
    return _llm("이 작품의 해설을 써라.\n" + 자)


def 작가소개_llm(m):
    자 = json.dumps(m.get("작가조회") or {}, ensure_ascii=False, indent=1)
    return _llm("이 작가의 소개를 써라. 자료에 없는 일화는 쓰지 마라.\n" + 자)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--조심", action="store_true",
                    help="정밀도를 지키는 작성기")
    ap.add_argument("--llm", action="store_true",
                    help="OPENAI_API_KEY 로 모델 호출")
    ap.add_argument("--n", type=int, default=0, help="앞 N점만 (0=전부)")
    a = ap.parse_args()

    p_in = os.path.join(HERE, "data/enriched.json")
    if not os.path.exists(p_in):
        print("  ⛔data/enriched.json 이 없습니다. normalize.py → enrich.py")
        return 1
    작품 = json.load(io.open(p_in, encoding="utf-8"))["작품"]
    if a.n:
        작품 = 작품[: a.n]

    if a.llm and not os.environ.get("OPENAI_API_KEY"):
        # ⛔★조용히 «소박»으로 떨어지지 않는다 —
        #   그러면 「LLM 으로 돌렸다」고 착각한 채 수치를 적게 된다.
        print("  ⛔--llm 인데 OPENAI_API_KEY 가 없습니다.")
        print("    .env.example 을 .env 로 복사해 키를 넣거나, --llm 을 빼세요.")
        return 1

    if a.llm:
        모드, 해설f, 작가f = "llm", 해설_llm, 작가소개_llm
    elif a.조심:
        모드, 해설f, 작가f = "조심", 해설_조심, 작가소개_조심
    else:
        모드, 해설f, 작가f = "소박", 해설_소박, 작가소개_소박

    print("═══ 작성 — %s · %d점 ═══" % (모드, len(작품)))
    for m in 작품:
        m["해설"] = 해설f(m)
        m["작가소개"] = 작가f(m)
        m["작성모드"] = 모드

    글자 = sum(len(m["해설"]) + len(m["작가소개"]) for m in 작품)
    근거0 = sum(1 for m in 작품 if "[" not in m["해설"])
    연쓴 = sum(1 for m in 작품 if "년作" in m["해설"] or "년." in m["해설"])
    print("  평균 길이   해설+소개 %d자" % (글자 // max(1, len(작품))))
    print("  근거 표시 0개인 해설      %2d건  ← A2 가 잡을 것" % 근거0)
    print("  「N년」이라 «적은» 해설    %2d건  ← D4 가 정밀도를 볼 것" % 연쓴)

    p_out = os.path.join(HERE, "data/written_%s.json" % 모드)
    io.open(p_out, "w", encoding="utf-8", newline="").write(
        json.dumps({"작품": 작품, "모드": 모드, "수": len(작품)},
                   ensure_ascii=False, indent=1))
    print()
    print("  → %s" % os.path.relpath(p_out, HERE).replace(os.sep, "/"))

    # ★§F-8-D 3단계 ① — 방금 쓴 파일을 그 자리에서 검사
    s = io.open(p_out, encoding="utf-8").read()
    bad = [i for i, ch in enumerate(s) if ord(ch) < 32 and ch != "\n"]
    if bad:
        print("  ⛔제어문자 %d개" % len(bad))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
