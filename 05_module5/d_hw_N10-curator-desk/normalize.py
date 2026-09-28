# -*- coding: utf-8 -*-
"""★세탁 — 관문 «앞»에 선다. 기계가 고칠 수 있는 것은 사람에게 안 보낸다.

  python normalize.py        data/corpus.json → data/clean.json

★왜 이 단계가 생겼나 (실측 2026-09-28)
  정규화 없이 관문을 걸었더니 40점 중 ★39점(97.5%)이 멈췄다.
  강의 3강은 「기준이 너무 낮으면 있으나 마나」를 경고했는데,
  ★반대쪽도 똑같이 무너진다 — 97.5%가 멈추면 사람이 전 건을 보는 것이고
  그건 선택지 ①(전부 막기)이지 자동화가 아니다.

  멈춤의 대부분이 HTML 태그였다:
    저작자 = span title=ancient Egyptian…   (태그가 섞이고 잘림)
    연도   = 19<sup>th</sup> century
    작가   = Unknown authorUnknown author   ★같은 말이 두 번
  ⇒ 이건 «판단거리»가 아니라 «세탁거리»다.
    사람에게 보내면 ★사람이 태그를 지우고 있게 된다.

  세탁 후: 97.5% → ★42.5%.  C1 35→0 · D2 22→0.

⛔그래도 관문은 남긴다 — 세탁을 «하고도» 태그가 남으면 그때는 멈춘다(C1·D2).
  세탁 «실패»는 판단거리다.

★연도는 «값»이 아니라 «값+정밀도»다 — 여기서 같이 푼다
  between 1677 and 1720 date QS:P571,+1500-...Z/6, P1319,+1677.../9, P1326,+1720.../9
    P571  제작연도  값 1500  ★정밀도 6 = 천년기  → 「1500년」이 아니다
    P1319 이른 쪽 1677 (정밀도 9 = 연)
    P1326 늦은 쪽 1720
  ★값만 읽으면 220년 틀린다.
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(io.open(os.path.join(HERE, "config.json"), encoding="utf-8"))

TAG = re.compile(r"<[^>]*>")
WS = re.compile(r"\s+")
ENT = [("&amp;", "&"), ("&nbsp;", " "), ("&quot;", '"'),
       ("&#39;", "'"), ("&lt;", "<"), ("&gt;", ">")]

# ★위키데이터 정밀도 — 값과 «함께» 와야 뜻이 산다
정밀도이름 = {6: "천년기", 7: "세기", 8: "10년", 9: "연", 10: "월", 11: "일"}
P571 = re.compile(r"QS:P571,\+?(-?\d{1,4})-[^/,]*/(\d+)")
P1319 = re.compile(r"P1319,\+?(-?\d{1,4})-")   # 이른 쪽
P1326 = re.compile(r"P1326,\+?(-?\d{1,4})-")   # 늦은 쪽
빈속성 = re.compile(r"QS:P,")                   # ★속성 이름이 «빈» 깨진 레코드
# ⛔★지웠다 — 쓰이지 않는데 \b 를 쓰고 있었다.
#   \b 는 「1721년」에서 경계를 «안 만든다»(1 과 년 이 둘 다 \w).
#   compare.py 에서 같은 꼴이 ★정답을 0건으로 만들었다.
#   안 쓰는 채로 두면 나중에 누가 «맞는 줄 알고» 가져다 쓴다.


def 태그벗기기(s):
    """HTML 을 벗기고 엔티티를 되돌린다. ⛔판정하지 않는다 — 씻기만 한다."""
    t = TAG.sub(" ", s or "")
    for a, b in ENT:
        t = t.replace(a, b)
    return WS.sub(" ", t).strip()


def 중복접기(s):
    """「같은 말이 두 번」을 한 번으로.

    ★실물 두 꼴을 다 본다
      UnknownauthorUnknownauthor    붙어 있다 → 길이 반으로 갈라 비교
      Unknown author Unknown author 띄어 있다 → 낱말 수 반으로 갈라 비교
    ⛔한 꼴만 보면 샌다 — 태그를 벗기면 공백이 «생겨서» 꼴이 바뀐다.
    """
    t = (s or "").strip()
    if not t:
        return t
    n = len(t)
    if n >= 6 and n % 2 == 0 and t[: n // 2] == t[n // 2:]:
        return t[: n // 2].strip()
    w = t.split()
    if len(w) >= 2 and len(w) % 2 == 0:
        h = len(w) // 2
        if w[:h] == w[h:]:
            return " ".join(w[:h])
    return t


def 연도읽기(원문):
    """연도를 «값 + 정밀도 + 범위»로 읽는다.

    반환 = {값, 정밀도, 정밀도이름, 이른, 늦은, 속성깨짐, 출처}
      값이 None  = ★「없다」가 아니라 «모른다». 둘을 섞지 않는다.
    """
    y = 태그벗기기(원문)
    r = {"원문": y, "값": None, "정밀도": None, "정밀도이름": None,
         "이른": None, "늦은": None, "속성깨짐": bool(빈속성.search(y)),
         "출처": None}

    h = P571.search(y)
    if h:
        r["값"] = int(h.group(1))
        r["정밀도"] = int(h.group(2))
        r["정밀도이름"] = 정밀도이름.get(r["정밀도"], "?")
        r["출처"] = "P571"
    e, l = P1319.search(y), P1326.search(y)
    if e:
        r["이른"] = int(e.group(1))
    if l:
        r["늦은"] = int(l.group(1))
    # ★범위가 있으면 그게 «더 정확»하다 — P571 은 천년기일 수 있다
    if r["이른"] and r["늦은"]:
        r["값"] = (r["이른"] + r["늦은"]) // 2
        r["정밀도"] = 9
        r["정밀도이름"] = "연(범위 중앙)"
        r["출처"] = "P1319~P1326"
    return r


def 표기연도(r):
    """★사람에게 보일 연도 문자열. «없는 정밀도»를 만들지 않는다."""
    if r["이른"] and r["늦은"]:
        return "%d~%d년" % (r["이른"], r["늦은"])
    if r["값"] is None:
        return "제작연도 미상"
    p = r["정밀도"]
    if p == 9:
        return "%d년" % r["값"]
    if p == 8:
        return "%d년대" % (r["값"] // 10 * 10)
    if p == 7:
        return "%d세기" % (r["값"] // 100 + 1)
    if p == 6:
        return "%d천년기" % (r["값"] // 1000 + 1)
    return "%d년[정밀도 %s]" % (r["값"], p)


def 슬러그(제목):
    t = re.sub(r"^File:", "", 제목 or "")
    t = re.sub(r"\.(jpg|jpeg|png|tif|tiff|webp)$", "", t, flags=re.I)
    t = re.sub(r"[^A-Za-z0-9가-힣]+", "-", t).strip("-").lower()
    return t[:60] or "untitled"


def 씻는다(m):
    """작품 한 건을 씻는다. ⛔원문을 «버리지» 않는다 — 관문이 대조한다."""
    작가 = 중복접기(태그벗기기(m.get("저작자원문")))
    설명 = 태그벗기기(m.get("설명원문"))
    출처 = 태그벗기기(m.get("출처원문"))
    연 = 연도읽기(m.get("연도원문"))
    제목 = re.sub(r"^File:", "", m.get("제목") or "")
    제목 = re.sub(r"\.(jpg|jpeg|png|tif|tiff|webp)$", "", 제목, flags=re.I)
    return {
        "슬러그": 슬러그(m.get("제목")),
        "제목": 제목,
        "갈래주제": m.get("갈래"),
        "url": m.get("url"),
        "가로": m.get("가로"), "세로": m.get("세로"),
        "라이선스": (m.get("라이선스원문") or "").strip(),
        "작가": 작가,
        "설명": 설명,
        "출처": 출처,
        "연도": 연,
        "연도표기": 표기연도(연),
        # ★원문은 그대로 남긴다 — C1·D2 가 «세탁 실패»를 보려면 필요하다
        "_원문": {
            "저작자": (m.get("저작자원문") or ""),
            "연도": (m.get("연도원문") or ""),
            "설명": (m.get("설명원문") or ""),
        },
    }


def main():
    p_in = os.path.join(HERE, "data/corpus.json")
    if not os.path.exists(p_in):
        print("  ⛔data/corpus.json 이 없습니다. 먼저 python fetch_art.py")
        return 1
    작품 = json.load(io.open(p_in, encoding="utf-8"))["작품"]
    깬 = [씻는다(m) for m in 작품]

    # ★센다 — 세탁이 «무엇을 지웠나». 안 세면 효과를 말할 수 없다.
    n = len(깬)
    태그전 = sum(1 for m in 작품
                if "<" in (m.get("저작자원문") or "")
                or "<" in (m.get("연도원문") or ""))
    태그후 = sum(1 for c in 깬 if "<" in c["작가"] or "<" in c["연도"]["원문"])
    접힘 = sum(1 for m, c in zip(작품, 깬)
              if 태그벗기기(m.get("저작자원문")) != c["작가"])
    연읽음 = sum(1 for c in 깬 if c["연도"]["값"] is not None)
    연단위 = sum(1 for c in 깬 if c["연도"]["정밀도"] == 9)
    깨짐 = sum(1 for c in 깬 if c["연도"]["속성깨짐"])

    print("═══ 세탁 — %d점 ═══" % n)
    print()
    print("  HTML 태그가 있던 건      %2d건  (%4.1f%%)" % (태그전, 태그전 / n * 100))
    print("  ★씻고도 남은 건          %2d건  ← 남으면 C1·D2 가 멈춘다"
          % 태그후)
    print("  「같은 말 두 번」 접은 건  %2d건" % 접힘)
    print()
    print("  ── 연도 ──")
    print("  제작연도를 «읽은» 건      %2d건  (%4.1f%%)"
          % (연읽음, 연읽음 / n * 100))
    print("  그중 정밀도가 «연»        %2d건  ← 「N년」이라 적어도 되는 것"
          % 연단위)
    print("  ★못 읽은 건               %2d건  ← 「없다」가 아니라 「모른다」"
          % (n - 연읽음))
    print("  ★속성 이름이 빈 레코드    %2d건  (QS:P, 꼴)" % 깨짐)

    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    p_out = os.path.join(HERE, "data/clean.json")
    io.open(p_out, "w", encoding="utf-8", newline="").write(
        json.dumps({"작품": 깬, "수": n}, ensure_ascii=False, indent=1))
    print()
    print("  → data/clean.json  %d점" % n)

    # ★§F-8-D 3단계 ① — 방금 쓴 그 파일을 «그 자리에서» 검사한다.
    #   범위를 기억하지 않는다. 만진 것만 본다.
    s = io.open(p_out, encoding="utf-8").read()
    bad = [i for i, c in enumerate(s) if ord(c) < 32 and c != "\n"]
    if bad:
        print("  ⛔제어문자 %d개 — 위치 %s" % (len(bad), bad[:5]))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
