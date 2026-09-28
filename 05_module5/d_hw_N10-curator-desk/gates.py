# -*- coding: utf-8 -*-
"""★관문 — 「어느 일에서 얼마나 멈출까」를 «계산»한다.

  python gates.py            data/enriched.json 을 재서 관문별 적중을 찍는다
  python gates.py --조합 B1   기준 조합을 바꿔 가며 (비교표는 compare.py)

★설계 원칙 넷
  ① 갈래마다 다른 기준     — 되돌릴 수 없는 «정도»가 다르니까
  ② 전부 계산 가능        — 루브릭 ② 가 「계산 가능한 승인 기준」을 명시
  ③ ★코드는 «한 벌»       — 기준이 15개여도 판정기는 한 함수. 갈래는 인자다
  ④ ⛔여기서 «처분»하지 않는다 — 걸렸다/안 걸렸다만 낸다. 멈출지는 그래프가 정한다

★「정답」을 «기계»가 만든다 — 이 주제를 고른 진짜 이유
  놓침·헛멈춤을 세려면 「사람이 봤어야 했나」의 정답이 필요하다.
  보통은 사람이 전 건을 손으로 라벨해야 해서 수십 건이 한계다.
  여기서는 라이선스는 API 가 · 정밀도는 위키데이터가 · 태그는 정규식이
  · 화가 여부는 위키백과가 «정답»을 만든다. ⇒ 전 건에 정답을 붙인다.
  A3(민감 어휘)만 사람 라벨이다.
"""
import argparse
import io
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(io.open(os.path.join(HERE, "config.json"), encoding="utf-8"))
G = CFG["_관문"]
갈래목록 = [k for k in CFG["_갈래"] if not k.startswith("_")]

_B1 = G["B1_표시의무위반"]
표시의무 = [s.lower() for s in _B1["표시의무"]]
불명표현 = [s.lower() for s in _B1["불명표현"] if s]
민감어휘 = G["A3_민감장면"]["민감어휘"]

TAG = re.compile(r"<[^>]*>")
연도쓰기 = re.compile(r"(\d{3,4})\s*년")
숫자 = re.compile(r"\d+")
근거표 = re.compile(r"\[(\d+)\]")
파일명작가 = re.compile(r"^(?:\d{2,4}\s+)?([A-Z][A-Za-zÀ-ÿ.'-]+(?:\s+"
                    r"(?:van|von|de|della|di|del|le|la|the|da)\s+)?"
                    r"(?:[A-Z][A-Za-zÀ-ÿ.'-]+\s*){0,3})\s+-\s+")


# ── 낱개 판정 — ⛔전부 «계산 가능». 사람 눈이 필요한 건 A3 뿐 ──────────

def _불명(이름):
    t = (이름 or "").strip().lower()
    return (not t) or any(k in t for k in 불명표현)


def _조회(m):
    return m.get("작가조회") or {"상태": "미조회"}


def _원문숫자(m, 갈래):
    """★그 갈래가 «읽은» 자료의 숫자만 모은다.

    ⛔전에는 작품 자료만 모아 놓고 해설+작가소개를 «뭉쳐» 대조했다.
      그래서 작가 생몰년(1743·1809)과 위키데이터 Q번호(Q5322166 의 숫자)가
      ★「원문에 없는 숫자」로 세어져 A1 이 60% 를 잡았다.
      해설«만» 대조하면 1/40 이었다 — ★58건이 전부 헛멈춤이었다.
    ⇒ 갈래가 내보내는 글과, 그 글이 읽은 자료를 «짝지어» 본다.
    """
    작품자료 = [m.get("설명") or "", m.get("_원문", {}).get("연도") or "",
              m.get("제목") or "", m.get("연도표기") or "",
              str((m.get("연도") or {}).get("이른") or ""),
              str((m.get("연도") or {}).get("늦은") or "")]
    if 갈래 != "작가":
        return set(숫자.findall(" ".join(작품자료)))
    r = m.get("작가조회") or {}
    작가자료 = [json.dumps(r, ensure_ascii=False)]     # 조회 원문 통째로
    return set(숫자.findall(" ".join(작품자료 + 작가자료)))


def A1_미확인수치(m, 글, 갈래="발행"):
    """그 갈래가 «내보낼 글»의 숫자가 읽은 자료에 없다.

    ⛔원문에 있는 숫자만 허용 — 「1500년」처럼 정밀도를 만들어 낸 것도 여기서 걸린다.
    """
    if not 글:
        return False
    있는숫자 = _원문숫자(m, 갈래)
    쓴숫자 = set(숫자.findall(re.sub(r"\[\d+\]", "", 글)))   # 근거표시 [1] 제외
    새로쓴 = {x for x in 쓴숫자 if len(x) >= 3 and x not in 있는숫자}
    return bool(새로쓴)


def A2_근거0(m, 글):
    """해설에 근거 표시가 하나도 없다."""
    return bool(글) and not 근거표.search(글)


def A3_민감장면(m, 글=None):
    """민감 어휘. ★유일하게 «사람이 라벨»해야 정답이 나오는 기준."""
    t = ((m.get("설명") or "") + " " + (m.get("제목") or "")
         + " " + (글 or ""))
    return any(w in t for w in 민감어휘)


def B1_표시의무위반(m, 글=None):
    """표시의무(CC BY)인데 표시할 저작자가 없다 → ★그 자체가 라이선스 위반."""
    lic = (m.get("라이선스") or "").lower()
    return any(k in lic for k in 표시의무) and _불명(m.get("작가"))


def B2_현대물(m, 글=None):
    """★P571 을 «정밀도와 함께» 읽어 연 단위이고 1900년 이후.

    ⛔DateTimeOriginal 을 쓰지 않는다 — 그건 «사진 촬영일시»다(실측 50%에 초 단위).
    """
    y = m.get("연도") or {}
    return y.get("정밀도") == 9 and (y.get("값") or 0) >= 1900


def C1_이름오염(m, 글=None):
    """★세탁을 «하고도» 태그가 남았다. 세탁 실패는 판단거리다."""
    return bool(TAG.search(m.get("작가") or ""))


def C2_작가불명(m, 글=None):
    return _불명(m.get("작가"))


def C3_생몰년미확인(m, 글=None):
    """★화가로 «확인된» 사람 중에서 생몰년이 없거나 몰년이 없다(생존 가능).

    ⛔조회 실패를 여기서 잡지 않는다 — 그건 C5 의 몫이다.
      전에는 둘 다 「조회 실패 → True」라서 ★C3 와 C5 가 «완전히 같았다»
      (교집합 19 · 차집합 0). 같은 것을 두 기준으로 세면
      비교표에서 「기준을 하나 더해도 개입률이 안 는다」로만 보이고
      ★무엇이 무엇을 잡는지 알 수 없다.
    """
    r = _조회(m)
    if r.get("화가인가") is not True:
        return False                     # C5 가 이미 잡는다
    return not r.get("생") or not r.get("몰")


def _이름꼴(s):
    """비교용 정규화 — 악센트·대소문자·구두점을 지운다.

    ★Adolf Hiremy-Hirschl 과 Adolf Hirémy-Hirschl 은 «다른 사람이 아니다».
    """
    t = unicodedata.normalize("NFKD", (s or "").strip().lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def C4_이름충돌(m, 글=None):
    """★Commons 작가명 ≠ 위키데이터 «영어» 레이블.

    ⛔ko 레이블과 비교하지 않는다 — 「Nicolai Abildgaard ≠ 니콜라이 아빌고르」는
      ★충돌이 아니라 «번역»이다. 그렇게 세어 11건이 나왔고 대부분이 헛것이었다.
    ⛔악센트 차이도 충돌이 아니다.
    """
    r = _조회(m)
    lab = r.get("레이블en")
    if not lab:
        return False                     # 비교할 것이 없다 — C5 가 맡는다
    a, b = _이름꼴(lab), _이름꼴(m.get("작가"))
    if not a or not b:
        return False
    if a == b:
        return False
    # ★한쪽이 다른 쪽을 «품으면» 충돌이 아니다 (「Rembrandt」 vs 「Rembrandt van Rijn」)
    return not (a in b or b in a)


def C5_그린사람아님(m, 글=None):
    """★위키백과가 «화가»라고 확인해 주지 못했다.

    ⛔「계정명처럼 보인다」로 판정하지 않는다 — 그 규칙은
      Sailko 를 못 잡고 Rembrandt 를 잡는다(실측).
    """
    return _조회(m).get("화가인가") is not True


def D1_출처충돌(m, 글=None):
    """★Artist 필드의 «성»이 파일명 어디에도 없다 — 두 출처가 어긋난다.

    ⛔전에는 「파일명 앞부분에서 작가를 뽑아」 비교했다. 그 정규식은
      ★40건 중 4건(10%)만 «뽑았고», 나머지 36건은 판정조차 못 했다.
      그런데 결과는 「0건」으로 찍혔다 — 「충돌 없음」처럼 보였다.
      ★0건이 «없음»인지 «못 읽음»인지 갈라야 한다(§F-8-D-3).

    ⇒ 뒤집었다. 파일명에서 «뽑지» 않고, Artist 의 성이 파일명에 «있는가»를 묻는다.
      이러면 ★40건 전부 판정된다.

    ★왜 이게 진짜 신호인가
      Commons 파일명은 거의 작품명·작가명이다. Artist 필드가 파일명과
      전혀 안 겹치면 그 필드는 «업로더/사진가»일 공산이 크다.
      실물 — 파일명 「Bartholomäus Spranger, …」 · Artist 「Sailko」
      ⇒ C5(위키백과가 화가로 확인 못 함)와 «독립된» 두 번째 출처가 된다.
    """
    아 = _이름꼴(m.get("작가"))
    if not 아:
        return False                     # 이름이 없다 — C2 가 맡는다
    제 = _이름꼴(m.get("제목"))
    if not 제:
        return False
    토막 = [w for w in 아.split() if len(w) >= 3]
    if not 토막:
        return False
    return not any(w in 제 for w in 토막)


def D2_연도오염(m, 글=None):
    """★세탁을 «하고도» 연도에 태그가 남았다."""
    return bool(TAG.search((m.get("연도") or {}).get("원문") or ""))


def D3_중복등재(m, 글=None, 카탈로그=None):
    return bool(카탈로그) and m.get("슬러그") in 카탈로그


def D4_연도정밀도(m, 글=None):
    """★「N년」이라 «적으려는데» 정밀도가 연이 아니거나 못 읽었다.

    ⛔못 읽은 것을 «전부» 멈추지 않는다 — 그러면 70%가 멈춘다.
      연도를 «쓸 때만» 문제다. 안 쓰면 문제가 아니다.  (A1 과 같은 꼴)
    """
    y = m.get("연도") or {}
    쓴다 = bool(글 and 연도쓰기.search(글))
    if not 쓴다:
        return False
    return y.get("정밀도") != 9


def D5_레코드깨짐(m, 글=None):
    """구조화 데이터의 속성 이름이 «빈» 것 (QS:P, 꼴). 파서가 조용히 건너뛴다."""
    return bool((m.get("연도") or {}).get("속성깨짐"))


판정기 = {
    "A1_미확인수치": A1_미확인수치, "A2_근거0": A2_근거0,
    "A3_민감장면": A3_민감장면,
    "B1_표시의무위반": B1_표시의무위반, "B2_현대물": B2_현대물,
    "C1_이름오염": C1_이름오염, "C2_작가불명": C2_작가불명,
    "C3_생몰년미확인": C3_생몰년미확인, "C4_이름충돌": C4_이름충돌,
    "C5_그린사람아님": C5_그린사람아님,
    "D1_출처충돌": D1_출처충돌, "D2_연도오염": D2_연도오염,
    "D3_중복등재": D3_중복등재, "D4_연도정밀도": D4_연도정밀도,
    "D5_레코드깨짐": D5_레코드깨짐,
}


# ── ★한 함수 — 갈래는 «인자»다. 기준이 15개여도 코드는 한 벌 ────────

def 내보낼글(m, 갈래):
    """★갈래가 «실제로 바깥에 내보내는» 글. 판정은 이것을 봐야 한다.

    ⛔해설과 작가소개를 뭉쳐 넘기면 A1·D4 가 엉뚱한 것을 잡는다(실측 60% → 2.5%).
      작가 갈래가 내보내는 건 «작가소개»지 해설이 아니다.
    """
    return {
        "발행": m.get("해설"),
        "작가": m.get("작가소개"),
        "카탈로그": m.get("해설"),
        "이미지": None,                   # 이미지는 «글»을 안 내보낸다
    }.get(갈래)


def 잰다(m, 갈래, 켠기준=None, 글=None, 카탈로그=None):
    """작품 하나를 한 갈래로 재서 «걸린 기준 목록»을 낸다.

    글 = None 이면 ★갈래에 맞는 글을 «스스로» 고른다.
         부르는 쪽이 갈래별 규칙을 알아야 하면 한 군데서 틀리면 다 틀린다.
    켠기준 = None 이면 그 갈래의 «전부». 비교표는 여기에 부분집합을 넣는다.
    ⛔처분하지 않는다 — 목록만 낸다.
    """
    if 갈래 == "정정":
        return ["정정_항상"]              # ★기준을 두지 않는 것이 기준이다
    if 글 is None:
        글 = 내보낼글(m, 갈래)
    후보 = CFG["_갈래"][갈래]["기준"]
    if 켠기준 is None:
        # ★compare.py 가 «재서 정한» 조합을 쓴다. 측정만 하고 안 쓰면 장식이다.
        켠기준 = set(CFG.get("_권장조합", {}).get(갈래, 후보))
    쓸것 = [k for k in 후보 if k in 켠기준]
    걸린 = []
    for k in 쓸것:
        f = 판정기[k]
        try:
            if k == "D3_중복등재":
                hit = f(m, 글, 카탈로그)
            elif k == "A1_미확인수치":
                hit = f(m, 글, 갈래)      # ★대조할 «원문»이 갈래마다 다르다
            else:
                hit = f(m, 글)
        except Exception as e:            # ⛔조용히 통과시키지 않는다
            걸린.append(k + "_판정오류:" + str(e)[:30])
            continue
        if hit:
            걸린.append(k)
    return 걸린


def 멈추나(m, 갈래, 켠기준=None, 글=None, 카탈로그=None):
    return bool(잰다(m, 갈래, 켠기준, 글, 카탈로그))


def 이유문(걸린):
    """★승인 화면에 띄울 «사람 말». 코드만 보여 주면 10초 안에 못 읽는다."""
    out = []
    for k in 걸린:
        g = G.get(k)
        코드 = k.split("_")[0]
        if not g:
            out.append((코드, k, ""))
            continue
        out.append((코드, g.get("판정", k), g.get("막는 위험", "")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--입력", default="data/enriched.json")
    a = ap.parse_args()
    p = os.path.join(HERE, a.입력)
    if not os.path.exists(p):
        print("  ⛔%s 가 없습니다. normalize.py → enrich.py 순서로" % a.입력)
        return 1
    작품 = json.load(io.open(p, encoding="utf-8"))["작품"]
    n = len(작품)
    모드 = json.load(io.open(p, encoding="utf-8")).get("모드")

    # ⛔★해설을 «넘기는» 것을 잊으면 A1·A2·D4 가 항상 0 이 된다.
    #   실사고 2026-09-28 — 여기서 글을 안 넘겨 「0건 — 있으나 마나」로 찍혔다.
    #   ★0건이 «기준이 무른 것»인지 «내가 안 준 것»인지 갈라야 한다(§F-8-D-3).
    있는글 = sum(1 for m in 작품 if m.get("해설"))
    print("═══ 관문 — %d점%s ═══"
          % (n, (" · 작성 «%s»" % 모드) if 모드 else ""))
    print("  해설이 «있는» 건 %d/%d — 없으면 A1·A2·D4 는 잴 수 없다"
          % (있는글, n))
    print()
    for 갈래 in 갈래목록:
        if 갈래 == "정정":
            continue
        걸린수 = {}
        멈춘 = 0
        for m in 작품:
            g = 잰다(m, 갈래)   # ★글은 잰다()가 갈래에 맞게 고른다
            if g:
                멈춘 += 1
            for k in g:
                걸린수[k] = 걸린수.get(k, 0) + 1
        print("  ── %s ── 멈춤 %d/%d  (%4.1f%%)"
              % (갈래, 멈춘, n, 멈춘 / n * 100))
        for k in CFG["_갈래"][갈래]["기준"]:
            c = 걸린수.get(k, 0)
            표 = ""
            if c == 0:
                표 = "  ⛔0건 — 있으나 마나(3강)"
            elif c / n > 0.8:
                표 = "  ⚠80%% 넘음 — 전부 막기와 같아진다"
            print("      %-18s %3d건  (%4.1f%%)%s" % (k, c, c / n * 100, 표))
        print()

    무사 = sum(1 for m in 작품
              if not any(잰다(m, g)
                         for g in 갈래목록 if g != "정정"))
    print("  ★어느 갈래에도 안 걸린 작품  %d/%d (%4.1f%%)"
          % (무사, n, 무사 / n * 100))
    if not 있는글:
        print("  ⚠해설이 없어 A1·A2·D4 는 «잰 적이 없다» —")
        print("    python write.py 뒤에 다시 재야 완전한 수치가 된다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
