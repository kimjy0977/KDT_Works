# -*- coding: utf-8 -*-
"""★회차를 쌓고 «나란히» 견준다 — 이 프로젝트의 과업은 «비교»다.

왜 만드나 (UX 결함을 고치는 것)
  앞 판은 «한 회차»만 보여 줬다. 사이드바에 스위치를 달아 놓고
  「끄고 견주라」고 해 놓고 정작 ★견줄 수가 없었다 —
  다시 돌리면 앞 결과가 덮였다(session_state 한 칸).

  이 프로젝트의 결론은 전부 「A vs B」다.
    팀 vs solo · 배정 켬/끔 · 축 주제/문화권
  ⇒ 화면이 «비교»를 못 하면 결론을 지지하지 못한다.

★그리고 잡음을 «결과 옆»에서 말한다
  근거율 67.6% 만 뜨면 사람은 그걸 믿는다. 같은 설정 12회가
  57.5~72.5% 로 흩어졌다는 사실이 «그 자리»에 없으면 소용없다.
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


# ★«완전히 같은 설정»인 조건 이름 — 여기가 유일한 출처다.
#   sync_numbers.py 와 redteam.py 가 «각자» 들고 있다가 갈렸다
#   (축 실험을 고치며 이름이 바뀌었는데 한쪽만 고쳤다).
#   ⇒ 같은 것을 두 군데서 정하지 않는다. 이 프로젝트에서 세 번째 같은 사고였다.
같은설정 = ("전부 켬 (기준선)", "★기준선 (재측정)", "축 A(명단만) — 주제",
         "★축 A — 주제 (우리 설정)")      # 옛 이름 — 지난 기록과 호환


def 같은설정_원시값(rows):
    """조건 이름이 바뀌어도 «지금 파일에 있는 것»만 모은다."""
    return [x["근거율"] for r in rows if r["조건"] in 같은설정
            for x in r.get("_회차별", [])]


def 잡음범위():
    """★같은 설정 여러 회차의 «실제 흩어짐». ablation.json 에서 잰다.

    없으면 None — ⛔「모르는 것을 아는 척」하지 않는다.
    """
    p = os.path.join(HERE, "output/ablation.json")
    if not os.path.exists(p):
        return None
    a = json.load(io.open(p, encoding="utf-8"))
    pool = 같은설정_원시값(a["rows"])
    if len(pool) < 4:
        return None
    return {"최소": min(pool), "최대": max(pool), "n": len(pool),
            "평균": sum(pool) / len(pool)}


def 띠(값, 범위, W=300, H=44, C=None):
    """★잡음 띠 — 이 값이 «읽을 수 있는 차이인가»를 그 자리에서 말한다.

    회색 띠 = 같은 설정을 여러 번 돌렸을 때 나온 범위.
    바늘이 그 안에 있으면 ★이 값만으로는 아무것도 못 읽는다.
    """
    C = C or {"ink": "#16171A", "ink40": "#8A8C92", "rule": "#D8D4C9",
              "mark": "#A33420", "rule2": "#EBE8E0"}
    lo, hi = 범위["최소"], 범위["최대"]
    pad = (hi - lo) * .55 + .02
    a, b = max(0, lo - pad), min(1, hi + pad)

    def x(v):
        return 4 + (v - a) / max(1e-9, b - a) * (W - 8)

    안쪽 = lo <= 값 <= hi
    o = ['<svg viewBox="0 0 %d %d" width="%d" height="%d" '
         'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="'
         '근거율 %.1f%% · 같은 설정 %d회 범위 %.1f~%.1f%% 안에 %s">'
         % (W, H, W, H, 값 * 100, 범위["n"], lo * 100, hi * 100,
            "들어 있다" if 안쪽 else "벗어난다")]
    o.append('<line x1="4" y1="22" x2="%d" y2="22" stroke="%s"/>'
             % (W - 4, C["rule"]))
    o.append('<rect x="%.1f" y="16" width="%.1f" height="12" fill="%s"/>'
             % (x(lo), x(hi) - x(lo), C["rule2"]))
    for v in (lo, hi):
        o.append('<line x1="%.1f" y1="14" x2="%.1f" y2="30" stroke="%s"/>'
                 % (x(v), x(v), C["rule"]))
    o.append('<text x="%.1f" y="11" font-size="9.5" text-anchor="middle" '
             'fill="%s" font-family="IBM Plex Mono,monospace">%.1f</text>'
             % (x(lo), C["ink40"], lo * 100))
    o.append('<text x="%.1f" y="11" font-size="9.5" text-anchor="middle" '
             'fill="%s" font-family="IBM Plex Mono,monospace">%.1f</text>'
             % (x(hi), C["ink40"], hi * 100))
    o.append('<line x1="%.1f" y1="10" x2="%.1f" y2="34" stroke="%s" '
             'stroke-width="2"/>' % (x(값), x(값), C["mark"]))
    o.append('<text x="%.1f" y="43" font-size="10" text-anchor="middle" '
             'fill="%s" font-family="IBM Plex Mono,monospace">%.1f</text>'
             % (min(W - 14, max(14, x(값))), C["mark"], 값 * 100))
    o.append("</svg>")
    return "".join(o), 안쪽


def 요약(st):
    """회차 하나를 목록에 쓸 «한 줄»로 줄인다."""
    m = st["metrics"]
    s = st.get("설정") or {}
    끈것 = [k for k in ("배정", "구역", "역할", "재위임") if s.get(k) is False]
    return {
        "라벨": ("전부 켬" if not 끈것 else " · ".join("%s 끔" % k for k in 끈것)),
        "축": st.get("축", "주제"),
        "근거율": m["근거율"], "편중": m["편중"], "중복률": m["중복률"],
        "격리율": m["격리율"], "읽은문서수": m["읽은문서수"],
        "경보": sum((len(m[k]) if isinstance(m.get(k), list) else (m.get(k) or 0))
                   for k in ("허위인용", "표기흔들림", "인용0절", "꺾쇠안닫힘")),
        "절수": len(st["sections"]), "초": st.get("sec", 0),
    }


def 견줌표(A, B, C):
    """두 회차의 «차이»를 잡음과 나란히 놓는다 — 차이가 잡음보다 작으면 말한다."""
    r = 잡음범위()
    잡음폭 = (r["최대"] - r["최소"]) if r else None
    행 = []
    for k, 이름 in (("근거율", "근거율"), ("편중", "편중"), ("중복률", "중복률"),
                  ("격리율", "격리율")):
        d = B[k] - A[k]
        읽나 = ("—" if 잡음폭 is None else
              ("읽을 수 있다" if abs(d) > 잡음폭 else "★잡음 안"))
        행.append((이름, A[k], B[k], d, 읽나))
    return 행, 잡음폭
