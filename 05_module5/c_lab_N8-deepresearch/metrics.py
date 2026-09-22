# -*- coding: utf-8 -*-
"""⑥ 평가 — ★정답표도 판정 모델도 쓰지 않는다 (강의 14강).

왜 정답표를 안 쓰나
    절제 실험(설정을 하나씩 꺼 보기)을 하려면 «잣대가 안 변해야» 한다.
    그런데 설정을 바꾸면 시스템이 다루는 범위가 달라진다 —
    정답표를 그대로 두면 불공정하고, 조건마다 새로 만들면 이미 같은 잣대가 아니다.
    ⇒ 정답표가 «필요 없는» 지표를 쓴다.

왜 모델 채점을 안 쓰나
    같은 글에 같은 점수가 안 나온다. 절제로 보려는 차이는 십몇 %p 인데
    판정 잡음이 그만큼이면 아무것도 못 본다.

★계기판의 조건 셋
    ① 설정을 바꿔도 잣대 자체는 안 바뀔 것
    ② 같은 입력에 같은 값을 낼 것 (전부 코드로 센다 — 결정적이다)
    ③ ★어느 장치가 고장 났는지 «가리킬» 것 — 종합 점수 하나로는 범인을 못 찾는다

지표가 어느 장치에 붙나
    편중 · 중복률   → 배정 · 구역 분할의 계기
    읽고 안 쓴 문서 → 배정 «품질»의 계기
    근거율          → 깊이 · 재위임의 계기
    ★허위 인용      → 계기가 «아니라 경보». 0이어야 한다. 0이 아니면 그 보고서는 탈락.

★이 지표가 «말해 주지 않는» 것 — 글이 좋은지는 모른다.
    근거를 촘촘히 달고 고르게 인용한 «형편없는» 보고서가 얼마든지 가능하다.
    ⇒ 그물(자동으로 거른다)과 잣대(사람이 고른다)는 다른 일이다.
      여기 있는 것은 전부 «그물»이다.
"""
import collections
import re


def 절모음(sections):
    """리듀서가 덧붙인 것 중 «절마다 마지막 것»만."""
    out = {}
    for s in sorted(sections, key=lambda x: x.get("바퀴", 0)):
        out[s["절"]] = s
    return out


def score(st):
    secs = 절모음(st.get("sections", []))
    report = st.get("report") or ""

    # 근거율 — 문장 중 «문서명» 이 붙은 비율
    본문 = re.sub(r"^#.*$", "", report, flags=re.M)
    문장 = [x for x in re.split(r"(?<=[.!?。])\s+|\n+", 본문) if len(x.strip()) > 10]
    근거문장 = [x for x in 문장 if "«" in x]
    근거율 = len(근거문장) / max(1, len(문장))

    # 인용·읽음 집계
    인용 = [c for s in secs.values() for c in s["인용"]]
    읽음 = [d for s in secs.values() for d in s["읽음"]]
    허위 = sum(len(s["허위인용"]) for s in secs.values())

    # 읽고 안 쓴 문서 — 예산을 쓰고 버린 것. 많으면 배정이 엉뚱했다는 뜻
    읽고안쓴 = sorted(set(읽음) - set(인용))

    # 최다 문서 편중 — 인용이 한 문서에 몰렸나
    c = collections.Counter(인용)
    편중 = (c.most_common(1)[0][1] / len(인용)) if 인용 else 0.0

    # 중복률 — 같은 문서를 두 절 이상이 읽은 비율
    읽은절수 = collections.Counter()
    for s in secs.values():
        for d in set(s["읽음"]):
            읽은절수[d] += 1
    겹친 = [d for d, n in 읽은절수.items() if n > 1]
    중복률 = len(겹친) / max(1, len(읽은절수))

    # 인용 0곳인 절 — 자료 없이 쓴 절. 전체 근거율로는 안 보이는 구멍
    인용0 = [s["절"] for s in secs.values() if not s["인용"]]

    # ★격리율 — 코디네이터가 «본» 글자 ÷ 팀 전체가 «읽은» 글자
    #   한 자릿수 %여야 한다. 30%를 넘으면 격리가 무너지는 중이다.
    from agent import DOCS
    팀이읽은 = sum(len(DOCS.get(d, "")[:12000]) for d in 읽음)
    코디가본 = sum(len(s["원고"]) for s in secs.values())
    격리율 = 코디가본 / max(1, 팀이읽은)

    return {
        "근거율": round(근거율, 4),
        "문장수": len(문장),
        "허위인용": 허위,                      # ★그물 — 0이어야 한다
        "읽고안쓴": 읽고안쓴,
        "편중": round(편중, 4),
        "중복률": round(중복률, 4),
        "인용0절": 인용0,
        "격리율": round(격리율, 4),
        "읽은문서수": len(set(읽음)),
        "인용수": len(set(인용)),
        "보고서자수": len(report),
        "절수": len(secs),
        "바퀴": st.get("wheel", 0),
        "종료": st.get("종료", ""),
    }
