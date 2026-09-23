# -*- coding: utf-8 -*-
"""★배정 도면 — 측정값을 «숫자»가 아니라 «기하»로 그린다. 이 화면의 주인공.

왜 만드나
  「중복률 33%」는 숫자일 뿐 ★«무엇이 겹쳤는지»를 안 보여 준다.
  사이드바 + 지표 4칸 + 탭은 어느 대시보드에나 있는 틀이고 주제를 말하지 않는다.

무엇을 그리나 — 이 시스템이 «실제로 하는 일» 그대로
    왼쪽   코퍼스 42건. 막대 길이 = 글자 수(log). 안 읽힌 것은 흐리다
    가운데 ★선 — 어느 조사관이 어느 문서를 읽었나
    오른쪽 조사관 4명. 각자 자기 «구역»

  겹치면 중복 · 몰리면 편중 · 흐리면 읽고 안 씀. ★눈에 보인다.

★도면 문법 (DESIGN.md)
  ⛔조사관을 «색»으로 안 가른다 — 선 모양(실선/파선/점선/일점쇄선)으로 가른다.
    도면 범례가 원래 그렇고, ★색맹에게도 갈린다(규칙 color-not-only).
  유채색은 «단 하나» — 인용된 근거에만 쓴다. 색 = 근거.
  ⛔그림자·그라디언트 없음.

⛔차트 라이브러리를 안 쓴다 — 좌표를 우리가 쥐어야 «구역»을 그릴 수 있다.
"""
import math

import ui

C = ui.C
DASH = ui.DASH
DASH_이름 = ui.DASH_이름


def _e(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def 도면(docs, sections, 실인용맵, W=1180, 행=12, 격리=None):
    제목들 = sorted(docs, key=lambda t: -len(docs[t]))
    n = len(제목들)
    T, B = 26, (86 if 격리 else 44)
    H = T + n * 행 + B
    X0, X1 = 292, 806
    LANE = 58
    gap = ((H - T - B - LANE * len(sections)) / max(1, len(sections) - 1)
           if len(sections) > 1 else 0)
    최대 = math.log(max(len(v) for v in docs.values()) + 1)

    읽힘 = {}
    for i, s in enumerate(sections):
        cited = set(실인용맵.get(s["절"], []))
        for d in s["읽음"]:
            읽힘.setdefault(d, []).append((i, d in cited))

    def ly(i):
        return T + i * (LANE + gap)

    o = ['<svg viewBox="0 0 %d %d" width="100%%" '
         'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="'
         '배정 도면 — 문서 %d건 중 %d건이 조사관 %d명에게 나뉘었다">'
         % (W, H, n, len(읽힘), len(sections))]
    o.append('<defs><style>'
             '.s{font:11px "IBM Plex Sans KR",sans-serif}'
             '.m{font:10px "IBM Plex Mono",monospace}'
             '.ttl{font:600 13px "IBM Plex Sans KR",sans-serif;fill:%s}'
             '.sub{font:11px "IBM Plex Sans KR",sans-serif;fill:%s}'
             '</style></defs>' % (C["ink"], C["ink60"]))

    # 머리 — ⛔올캡스 안 씀
    for x, t in ((0, "코퍼스 %d건" % n), (X0 + 26, "배정"),
                 (X1, "조사관 %d명" % len(sections))):
        o.append('<text x="%d" y="11" class="s" fill="%s">%s</text>'
                 % (x, C["ink40"], t))
    o.append('<line x1="0" y1="17" x2="%d" y2="17" stroke="%s"/>'
             % (W, C["rule"]))

    # 왼쪽 — 문서
    y_of = {}
    for k, t in enumerate(제목들):
        y = T + k * 행 + 행 / 2
        y_of[t] = y
        w = 6 + (math.log(len(docs[t]) + 1) / 최대) * 118
        정보 = 읽힘.get(t)
        쓴것 = bool(정보) and any(c for _, c in 정보)
        col = C["mark"] if 쓴것 else (C["ink"] if 정보 else C["rule"])
        op = "1" if 쓴것 else (".5" if 정보 else ".75")
        o.append('<rect x="%.0f" y="%.1f" width="%.0f" height="4" '
                 'fill="%s" opacity="%s"><title>%s · %s자%s</title></rect>'
                 % (X0 - 22 - w, y - 2, w, col, op, _e(t),
                    format(len(docs[t]), ","),
                    "" if 정보 else " — 아무도 안 읽음"))
        if 정보:
            o.append('<text x="%.0f" y="%.1f" class="s" text-anchor="end" '
                     'fill="%s">%s</text>'
                     % (X0 - 26 - w, y + 4, C["ink60"], _e(t[:12])))
            if len(정보) > 1:      # ★두 명 이상 = 중복. 도면의 «검토 표시»
                o.append('<path d="M%d %.1f l4 4 m0 -4 l-4 4" stroke="%s" '
                         'stroke-width="1.3"><title>%d명이 같이 읽었다 — 중복'
                         '</title></path>' % (X0 - 14, y - 2, C["mark"],
                                              len(정보)))

    # 가운데 — 선. ★조사관은 «선 모양»으로 갈린다
    for t, 정보 in 읽힘.items():
        y0 = y_of[t]
        for lane, cited in 정보:
            y1 = ly(lane) + LANE / 2
            d = DASH[lane % 4]
            o.append('<path d="M%d %.1f C%d %.1f,%d %.1f,%d %.1f" fill="none" '
                     'stroke="%s" stroke-width="%s" opacity="%s"%s>'
                     '<title>%s → %d %s (%s)</title></path>'
                     % (X0, y0, X0 + 175, y0, X1 - 175, y1, X1, y1,
                        C["mark"] if cited else C["ink"],
                        "1.5" if cited else "1",
                        ".9" if cited else ".3",
                        "" if d == "none" else ' stroke-dasharray="%s"' % d,
                        _e(t), lane + 1, _e(sections[lane]["절"][:16]),
                        "인용함" if cited else "★읽고 안 씀"))

    # 오른쪽 — 조사관. ⛔왼쪽 컬러 보더 안 씀. 괘선 + 선 견본
    for i, s in enumerate(sections):
        y = ly(i)
        cited = set(실인용맵.get(s["절"], []))
        버림 = len(s["읽음"]) - len(cited)
        o.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s"/>'
                 % (X1, y, W, y, C["rule"]))
        o.append('<text x="%d" y="%.1f" class="m" fill="%s">%d</text>'
                 % (X1, y + 20, C["ink40"], i + 1))
        o.append('<text x="%d" y="%.1f" class="ttl">%s</text>'
                 % (X1 + 20, y + 20, _e(s["절"][:24])))
        o.append('<text x="%d" y="%.1f" class="sub">%s</text>'
                 % (X1 + 20, y + 37, _e(s["역할"])))
        # 선 견본 — 범례를 «그 자리에»
        o.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" '
                 'stroke-width="1.4"%s/>'
                 % (X1 + 20, y + 47, X1 + 56, y + 47, C["ink"],
                    "" if DASH[i % 4] == "none"
                    else ' stroke-dasharray="%s"' % DASH[i % 4]))
        o.append('<text x="%d" y="%.1f" class="m" fill="%s">'
                 '읽음 %d · 인용 %d%s</text>'
                 % (X1 + 64, y + 51, C["ink40"], len(s["읽음"]), len(cited),
                    " · 버림 %d" % 버림 if 버림 else ""))

    # ★격리 — 조사관이 «읽은» 양과 위로 «올린» 양을 나란히.
    #   맨 아래 표 3줄로만 두면 「원문이 아래에 남는다」가 그림으로 안 보인다.
    if 격리:
        읽은, 올린 = 격리
        if 읽은:
            bw = 150
            ow = max(2, bw * 올린 / max(1, 읽은))
            by = H - 58
            o.append('<text x="%d" y="%d" class="s" fill="%s">'
                     '조사관이 읽은 글자</text>' % (X1, by - 6, C["ink40"]))
            o.append('<rect x="%d" y="%d" width="%d" height="7" fill="%s" '
                     'opacity=".35"><title>%s자 — 조사관 안에서 끝난다</title>'
                     '</rect>' % (X1, by, bw, C["ink"], format(읽은, ",")))
            o.append('<rect x="%d" y="%d" width="%.1f" height="7" fill="%s">'
                     '<title>%s자만 코디에게 올라간다</title></rect>'
                     % (X1, by + 12, ow, C["mark"], format(올린, ",")))
            o.append('<text x="%d" y="%d" class="m" fill="%s">'
                     '위로 올라간 것 %s자 (%.1f%%)</text>'
                     % (X1 + bw + 10, by + 19, C["ink60"],
                        format(올린, ","), 올린 / max(1, 읽은) * 100))

    # 범례 — ⛔색으로만 말하지 않는다
    ly2 = H - 18
    o.append('<line x1="0" y1="%d" x2="%d" y2="%d" stroke="%s"/>'
             % (ly2 - 16, W, ly2 - 16, C["rule"]))
    o.append('<line x1="0" y1="%d" x2="26" y2="%d" stroke="%s" '
             'stroke-width="1.5"/>' % (ly2 - 4, ly2 - 4, C["mark"]))
    o.append('<text x="32" y="%d" class="s" fill="%s">인용한 문서</text>'
             % (ly2, C["ink60"]))
    o.append('<line x1="128" y1="%d" x2="154" y2="%d" stroke="%s" '
             'opacity=".3"/>' % (ly2 - 4, ly2 - 4, C["ink"]))
    o.append('<text x="160" y="%d" class="s" fill="%s">읽고 안 쓴 문서</text>'
             % (ly2, C["ink60"]))
    o.append('<path d="M288 %d l4 4 m0 -4 l-4 4" stroke="%s" '
             'stroke-width="1.3"/>' % (ly2 - 6, C["mark"]))
    o.append('<text x="300" y="%d" class="s" fill="%s">두 명 이상이 읽음</text>'
             % (ly2, C["ink60"]))
    o.append('<rect x="416" y="%d" width="20" height="4" fill="%s"/>'
             % (ly2 - 6, C["rule"]))
    o.append('<text x="442" y="%d" class="s" fill="%s">'
             '아무도 안 읽은 문서 %d건</text>'
             % (ly2, C["ink60"], n - len(읽힘)))
    o.append('<text x="%d" y="%d" class="s" fill="%s">'
             '조사관은 «선 모양»으로 갈립니다 — %s</text>'
             % (X1, ly2, C["ink40"],
                " · ".join(DASH_이름[:len(sections)])))
    o.append("</svg>")
    return "".join(o)


def 판독(docs, sections, 실인용맵, m):
    """★도면에서 «읽어야 할 것»을 문장으로. ⛔스탯 배너 줄 대신 이것을 쓴다."""
    읽힘 = {}
    for i, s in enumerate(sections):
        for d in s["읽음"]:
            읽힘.setdefault(d, []).append(i)
    중복 = [d for d, v in 읽힘.items() if len(v) > 1]
    cited_all = [c for s in sections for c in 실인용맵.get(s["절"], [])]
    버림 = [d for d in 읽힘 if d not in set(cited_all)]

    줄 = [("코퍼스 <b>%d건</b> 가운데 <b class='num'>%d건</b>에만 손이 닿았습니다."
          % (len(docs), len(읽힘)),
          "예산이 절수 × 깊이로 묶여 있어서입니다. 나머지 %d건은 이번 질문에서 "
          "아무도 열지 않았습니다 — 도면 왼쪽의 흐린 막대가 그것입니다."
          % (len(docs) - len(읽힘)))]
    if 중복:
        줄.append(("<b class='num'>%d건</b>을 두 명 이상이 같이 읽었습니다." % len(중복),
                 "%s. 구역을 나눠 줬는데도 겹친 자리이고, 도면에 «×» 로 찍힙니다. "
                 "중복률 <b class='num'>%.1f%%</b> 가 이 숫자입니다."
                 % (", ".join("«%s»" % d for d in 중복[:3]), m["중복률"] * 100)))
    if 버림:
        줄.append(("<b class='num'>%d건</b>은 읽고 쓰지 않았습니다." % len(버림),
                 "%s. 예산을 쓰고 버린 것이라 «배정 품질»의 신호입니다 — "
                 "도면에서 흐린 선이 그 자리입니다."
                 % ", ".join("«%s»" % d for d in 버림[:3])))
    if cited_all:
        최다 = max(set(cited_all), key=cited_all.count)
        if cited_all.count(최다) > 1:
            줄.append(("인용이 «%s»에 <b class='num'>%d번</b> 몰렸습니다."
                     % (최다, cited_all.count(최다)),
                     "편중 <b class='num'>%.1f%%</b> — 높으면 다들 유명 문서로 "
                     "갑니다. 그 문서로 선이 모이는 것이 보입니다."
                     % (m["편중"] * 100)))
    return 줄


def 표제(docs, n절=4, W=1180, H=104):
    """★표제 도면 — 장식 이미지가 아니라 «코퍼스 그 자체»를 그린다.

    주영님 지적 —「헤드에 임팩트 있게. 무슨 주제인지 직관적으로 보이게」
      ⛔스톡 이미지·그라디언트 배너를 깔지 않는다. 그건 AI 표식이고,
        무엇보다 ★이 화면과 아무 상관이 없다.
      ✅문서 42건이 넷으로 갈렸다가 한 편으로 모이는 그림을 그린다.
        막대 하나하나가 «실제 문서»이고 길이가 «실제 글자 수»다.
        ⇒ 보는 순간 「많은 자료를 나눠 읽어 한 편으로 만든다」가 읽힌다.
    """
    제목들 = sorted(docs, key=lambda t: -len(docs[t]))
    n = len(제목들)
    최대 = math.log(max(len(v) for v in docs.values()) + 1)
    L, M, R = 8, 470, 980
    o = ['<svg viewBox="0 0 %d %d" width="100%%" '
         'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="'
         '문서 %d건이 조사관 %d명에게 나뉘었다가 보고서 한 편으로 모인다">'
         % (W, H, n, n절)]

    # 왼쪽 — 문서 42건을 «격자»로. 실제 길이를 쓴다
    col, row = 6, math.ceil(n / 6)
    for k, t in enumerate(제목들):
        cx = L + (k % col) * 74
        cy = 22 + (k // col) * ((H - 44) / max(1, row - 1))
        w = 10 + (math.log(len(docs[t]) + 1) / 최대) * 52
        o.append('<rect x="%.0f" y="%.1f" width="%.0f" height="3" fill="%s" '
                 'opacity=".55"><title>%s · %s자</title></rect>'
                 % (cx, cy, w, C["ink"], _e(t), format(len(docs[t]), ",")))

    # 가운데 — 넷으로 갈린다
    for i in range(n절):
        y = 22 + i * ((H - 44) / max(1, n절 - 1))
        o.append('<path d="M%d 52 C%d 52,%d %.1f,%d %.1f" fill="none" '
                 'stroke="%s" stroke-width="1"%s opacity=".55"/>'
                 % (L + 440, M - 40, M - 10, y, M + 30, y, C["ink"],
                    "" if DASH[i % 4] == "none"
                    else ' stroke-dasharray="%s"' % DASH[i % 4]))
        o.append('<rect x="%d" y="%.1f" width="86" height="3" fill="%s"/>'
                 % (M + 30, y - 1, C["ink"]))
        # 오른쪽 — 한 편으로 모인다
        o.append('<path d="M%d %.1f C%d %.1f,%d 52,%d 52" fill="none" '
                 'stroke="%s" stroke-width="1.2" opacity=".85"/>'
                 % (M + 116, y, M + 190, y, R - 60, R, C["mark"]))

    o.append('<rect x="%d" y="24" width="5" height="56" fill="%s"/>'
             % (R, C["mark"]))
    o.append('<text x="%d" y="46" font-size="12" fill="%s" '
             'font-family="IBM Plex Sans KR,sans-serif">보고서 한 편</text>'
             % (R + 16, C["ink"]))
    o.append('<text x="%d" y="64" font-size="11" fill="%s" '
             'font-family="IBM Plex Mono,monospace">4절 · 근거 포함</text>'
             % (R + 16, C["ink40"]))
    for x, t in ((L, "자료 %d건 — 한 번에 못 읽는다" % n),
                 (M + 30, "넷이 나눠 읽는다")):
        o.append('<text x="%d" y="12" font-size="11" fill="%s" '
                 'font-family="IBM Plex Sans KR,sans-serif">%s</text>'
                 % (x, C["ink40"], t))
    o.append("</svg>")
    return "".join(o)
