# -*- coding: utf-8 -*-
"""★디자인 시스템 — 「결재 데스크」. 결정의 출처는 DESIGN.md 다.

이 파일은 DESIGN.md 를 «코드로 옮긴 것»뿐이다.
값을 여기서 «정하지» 않는다 — 정하려면 DESIGN.md 를 고치고 옮긴다.
(config.json 이 도메인 값의 유일한 출처인 것과 같은 이유)

★노드9 와 «무엇이 다른가» — 같은 서체, 다른 구조
  노드9 = 「측량 도면」. 읽는 것. 괘선으로 글을 나눈다. 상태가 거의 없다.
  노드10 = 「결재 데스크」. ★조작하는 것. 대기열이 있고 줄어든다.
  ⇒ 서체·색 토큰은 이어받는다(같은 사람의 산출물이라는 표시).
    ★배치는 새로 짠다 — 「읽는 화면」과 「처리하는 화면」은 다른 물건이다.

★이 화면이 하는 일은 하나다 — 「10초 안에 판단하게 한다」
  그래서 중요도 순서가 «고정»이다:
    1. 왜 멈췄나        ← 제일 크게. 이걸 모르면 판단을 못 한다
    2. 통과시키면 뭐가 일어나나 ← 버튼 «바로 위». 강의 1강이 짚은 그 문장
    3. 무엇에 대한 건인가 (그림·제목·작가)
    4. 대기열 어디쯤인가
  ⛔장식은 이 넷을 밀어내지 않는 자리에만 둔다.

★2026 AI 생성 UI 표식을 피한다 (노드9 에서 세어 둔 16개 중 해당하는 것)
  ⛔카드 왼쪽 컬러 보더(#11 — 가장 확실한 표식) ⛔그라디언트 ⛔글로우 ⛔그림자
  ⛔가운데 정렬 히어로 ⛔H1 위 배지 ⛔올캡스 라벨 ⛔4연속 스탯 배너
  ★대기 «건수»는 스탯 배너가 아니라 «목록의 머리»에 둔다 — 기능이지 장식이 아니다.

★접근성 — 규칙 이름 그대로 지킨다
  color-not-only   갈래를 «색»으로만 가르지 않는다. ★글자가 먼저다
  touch-target     버튼 최소 44px
  focus-states     focus-visible 링을 지운 적이 없다
  contrast         본문 4.5:1 · 조작요소 «경계» 3:1 (WCAG 1.4.11)
                   ⇒ redteam.py 가 «실제로 잰다»
  reduced-motion   prefers-reduced-motion 존중
"""

# ── 토큰 — DESIGN.md §토큰 그대로 ─────────────────────────────────
C = {
    "paper": "#FCFCFA",
    "ink": "#16171A",
    "ink60": "#5B5D63",
    "ink40": "#8A8C92",
    "rule": "#DDD9CE",
    "rule2": "#EFECE5",
    "mark": "#A33420",      # ★강조 «단 하나» — 멈춘 이유·결과 예고
    "markbg": "#FBEAE5",
    "field": "#F1EEE6",     # 조작면
    # ★WCAG 1.4.11 — 조작요소 «경계»는 3:1.
    #   ⛔#9A9281 은 paper 와는 3.01 이었지만 ★field(단추 바탕)와는
    #     «2.66» 이었다. 단추 테두리는 «단추 바탕 위»에 있다 —
    #     어느 바탕과 재야 하는지를 틀렸다. redteam 이 잡았다.
    "fieldline": "#8F8776",
    "ok": "#2F5D3A",        # 「자동 처리됨」 한 곳에만
}

FONTS = ("https://fonts.googleapis.com/css2?"
         "family=IBM+Plex+Mono:wght@400;500;600&"
         "family=IBM+Plex+Sans+KR:wght@300;400;500;600;700&display=swap")

# ★갈래 구분 — ⛔색이 아니다. «테두리 모양»이다.
#   도면의 범례 문법이고, 색맹에게도 갈린다(규칙 color-not-only).
#   그리고 «글자»가 먼저다 — 모양은 거들 뿐이다.
# ⛔★갈래테 dict 를 지웠다 — 테두리 «모양»은 CSS 에 직접 적혀 있고
#   이 dict 는 아무도 안 읽었다. 값이 두 군데 있으면 «갈린다».
#   (.tag.t-발행/이미지/작가/카탈로그 의 border-style 이 정본)


def css():
    return """
<style>
@import url('%(fonts)s');

:root{
  --paper:%(paper)s; --ink:%(ink)s; --ink60:%(ink60)s; --ink40:%(ink40)s;
  --rule:%(rule)s; --rule2:%(rule2)s; --mark:%(mark)s; --markbg:%(markbg)s;
  --field:%(field)s; --fieldline:%(fieldline)s; --ok:%(ok)s;
}

/* ⛔그림자 0 · 그라디언트 0 · 글로우 0 */
.stApp{background:var(--paper);color:var(--ink)}
html,body,[class*="css"],.stMarkdown,p,div,span,li,td,th{
  font-family:'IBM Plex Sans KR','Apple SD Gothic Neo',sans-serif}
.block-container{padding-top:22px;padding-bottom:80px;max-width:1300px}
*{box-shadow:none!important;text-shadow:none!important}
h1,h2,h3,h4{font-family:'IBM Plex Sans KR',sans-serif!important;
  color:var(--ink)!important;font-weight:600!important;letter-spacing:-.02em}
.num{font-family:'IBM Plex Mono',monospace;font-variant-numeric:tabular-nums;
  font-feature-settings:"tnum" 1;font-weight:500}

/* ── 머리 — ⛔가운데 정렬 없음 · ⛔배지 없음 ───────────────────── */
.hd{border-bottom:1px solid var(--ink);padding-bottom:12px;margin-bottom:6px}
.hd h1{font-size:25px;margin:0 0 5px;line-height:1.25}
.hd .meta{font-size:12.5px;color:var(--ink60);line-height:1.7}
.hd .meta b{color:var(--ink);font-weight:500}

/* ── ★진행 — 장식이 아니라 «얼마나 남았나»다 ────────────────────
   대기열은 «줄어드는 것»이다. 줄어드는 걸 안 보여 주면 끝이 안 보인다. */
.prog{margin:10px 0 2px}
.prog .bar{height:5px;background:var(--rule2);position:relative}
.prog .bar i{display:block;height:5px;background:var(--ink)}
.prog .t{font-size:12px;color:var(--ink60);margin-top:5px;line-height:1.6}
.prog .t b{color:var(--ink);font-weight:600}

/* ── 대기열 — ⛔카드 반복이 아니다. «목록»이다 ──────────────────── */
.qh{font-size:12px;color:var(--ink40);border-top:1px solid var(--ink);
  padding-top:8px;margin:16px 0 2px;line-height:1.7}
.qh b{color:var(--ink);font-weight:600;font-size:13px}
.qg{font-size:12px;color:var(--ink60);padding:3px 0;display:flex;
  justify-content:space-between;border-bottom:1px solid var(--rule2)}
.qg .n{font-family:'IBM Plex Mono',monospace;color:var(--ink)}

/* ── 갈래 표식 — ★글자가 먼저. 테두리 «모양»이 거든다 ───────────── */
/* ★작으면 «갈래»로 안 읽힌다 — 위치 표시(1/32)와 무게가 비슷하면
   둘 다 부수정보로 보인다. 갈래는 «무엇에 대한 판단인가»라 더 무겁다. */
.tag{display:inline-block;font-family:'IBM Plex Mono',monospace;
  font-size:13px;font-weight:600;line-height:1;padding:6px 10px;
  border:1px solid var(--ink);color:var(--ink);background:transparent;
  white-space:nowrap;letter-spacing:.02em}
.tag.t-발행{border-style:solid}
.tag.t-이미지{border-style:double;border-width:3px;padding:2px 5px}
.tag.t-작가{border-style:dashed}
.tag.t-카탈로그{border-style:dotted}

/* ── ★도켓 — 한 건. ⛔왼쪽 컬러 보더 아님. 위아래 실선이다 ──────── */
.dk{border-top:1px solid var(--ink);border-bottom:1px solid var(--ink);
  padding:14px 0 0;margin:6px 0 0}
.dk .top{display:flex;align-items:center;gap:10px;flex-wrap:wrap;
  margin-bottom:10px}
.dk .pos{font-family:'IBM Plex Mono',monospace;font-size:12px;
  color:var(--ink40)}
.dk .ttl{font-size:19px;font-weight:600;line-height:1.35;margin:0 0 3px;
  letter-spacing:-.01em}
.dk .by{font-size:13px;color:var(--ink60);margin-bottom:12px}
.dk .by b{color:var(--ink);font-weight:500}
/* ★후손 선택자를 쓰지 않는다 — Streamlit 은 markdown 블록마다 따로 감싼다.
   .dk img 로 쓰면 «같은 도켓 안»인데도 안 닿는다(실측). 클래스를 직접 붙인다. */
.thumb{display:block;width:100%%;border:1px solid var(--rule)}
.cap{font-size:11px;color:var(--ink40);line-height:1.6;margin-top:5px}

/* ── ★① 왜 멈췄나 — 이 화면에서 «제일 큰» 것 ────────────────────
   ⛔한 이름을 두 번 정의하지 않는다 — 뒤가 앞을 «조용히» 덮는다.
     여기서 .why 를 두 번 썼다가 margin-bottom 이 사라졌다(redteam 이 잡음).
   ★구역이 바뀐 것을 «선»으로 말한다 — 부제 바로 아래 회색 글자만으론
   「여기부터 다른 이야기」가 안 읽힌다.
   ⛔그리고 이 화면에서 «제일 중요한» 라벨이 «제일 작으면» 안 된다.
     12px 회색으로 뒀더니 부제보다도 약해서 눈이 그냥 지나갔다(캡처로 확인). */
.why{border-top:1px solid var(--ink);padding-top:12px;
  margin:10px 0 14px}
.why .h{font-size:13.5px;color:var(--ink);margin-bottom:8px;
  font-weight:600;letter-spacing:-.01em}
.why .it{display:flex;gap:11px;align-items:baseline;padding:8px 0;
  border-bottom:1px solid var(--rule2)}
.why .it:last-child{border-bottom:0}
.why .c{font-family:'IBM Plex Mono',monospace;font-size:13px;
  font-weight:600;color:var(--mark);flex:none;min-width:26px}
.why .w{font-size:14.5px;line-height:1.65;color:var(--ink)}
.why .w .r{display:block;font-size:12.5px;color:var(--ink60);margin-top:3px}

/* ── ★② 통과시키면 — 버튼 «바로 위». 강의 1강 ─────────────────── */
.cons{background:var(--markbg);padding:11px 14px;margin:0 0 12px;
  font-size:13.5px;line-height:1.7}
.cons .h{font-weight:600;color:var(--mark);margin-bottom:3px;font-size:12px}
.cons .irr{display:block;color:var(--ink60);font-size:12px;margin-top:4px}

/* 근거 있는 글 — 해설·작가소개 */
.body{font-size:14px;line-height:1.85;color:var(--ink);max-width:76ch;
  padding:10px 0;border-top:1px solid var(--rule2);margin-top:4px}
.body .q{color:var(--mark);font-weight:500}   /* 근거 표시 [1] */
.lbl{font-size:12px;color:var(--ink40);margin:14px 0 2px}

/* 자동 처리 — ★「안 멈춘 것도 보인다」. 안 보이면 놓침을 못 찾는다 */
.auto{font-size:12.5px;color:var(--ink60);padding:7px 0;
  border-bottom:1px solid var(--rule2);display:flex;gap:10px}
.auto .ok{color:var(--ok);font-weight:600;flex:none}

/* 빈 화면 — ⛔공백으로 두지 않는다 */
.empty{border-top:1px solid var(--ink);padding:26px 0;font-size:14px;
  color:var(--ink60);line-height:1.9}
.empty b{color:var(--ink);font-weight:600;display:block;font-size:16px;
  margin-bottom:6px}

/* ── Streamlit 위젯 ───────────────────────────────────────── */
.stButton>button{background:var(--field);color:var(--ink);
  border:1px solid var(--fieldline);border-radius:0;font-weight:500;
  font-size:13.5px;padding:11px 18px;min-height:44px;width:100%%;
  font-family:'IBM Plex Sans KR',sans-serif;cursor:pointer;
  transition:background .12s linear,border-color .12s linear}
.stButton>button:hover{border-color:var(--ink);background:var(--rule2)}
.stButton>button:focus-visible{outline:2px solid var(--mark);outline-offset:2px}
/* ★으뜸 단추 하나 — 「보통 무엇을 하나」를 말한다. 나머지는 대등하게.
   ⛔래퍼 클래스로 고르지 않는다 — Streamlit 이 블록을 갈라 안 닿는다.
     «버튼 자신»의 testid 로 고른다. */
button[data-testid="stBaseButton-primary"]{background:var(--ink)!important;
  color:var(--paper)!important;border-color:var(--ink)!important;
  font-weight:600!important}
button[data-testid="stBaseButton-primary"]:hover{
  background:var(--mark)!important;border-color:var(--mark)!important}

section[data-testid="stSidebar"]{background:var(--paper);
  border-right:1px solid var(--rule)}
div[data-testid="stExpander"]{border:0;border-top:1px solid var(--rule2);
  border-radius:0;background:transparent}
div[data-testid="stExpander"] summary{font-size:12.5px;color:var(--ink60);
  padding-left:0}
div[data-testid="stExpander"] summary:hover{color:var(--mark)}
[data-baseweb="select"]>div,.stTextInput input,.stTextArea textarea{
  border-radius:0!important;background:var(--field)!important;
  border:1px solid var(--fieldline)!important;
  font-family:'IBM Plex Sans KR',sans-serif}
[data-baseweb="select"]>div:hover,.stTextInput input:hover,
.stTextArea textarea:hover{border-color:var(--ink)!important}
[data-baseweb="select"]>div:focus-within,.stTextInput input:focus,
.stTextArea textarea:focus{border-color:var(--mark)!important;
  outline:2px solid var(--mark);outline-offset:1px}
.stRadio [role="radiogroup"]{background:var(--field);
  border:1px solid var(--fieldline);padding:9px 14px;display:flex;
  gap:18px;flex-wrap:wrap}
.stRadio [role="radiogroup"]:hover{border-color:var(--ink)}
.stRadio label{cursor:pointer}
label[data-testid="stWidgetLabel"] p{font-size:12px!important;
  font-weight:600!important;color:var(--ink60)!important}
hr{border-color:var(--rule)}
code{font-family:'IBM Plex Mono',monospace;background:transparent;
  color:var(--ink60);font-size:.9em;padding:0}
.stCaption,[data-testid="stCaptionContainer"]{color:var(--ink40)!important}
div[data-testid="stDataFrame"]{border:1px solid var(--rule)}

@media (prefers-reduced-motion: reduce){*{transition:none!important}}
</style>
""" % dict(C, fonts=FONTS)


# ── 조각 ────────────────────────────────────────────────────────

def 태그(갈래):
    return '<span class="tag t-%s">%s</span>' % (갈래, 갈래)


def 진행(남음, 전체):
    끝 = 전체 - 남음
    pc = (끝 / 전체 * 100) if 전체 else 100
    return ('<div class="prog"><div class="bar"><i style="width:%.1f%%">'
            '</i></div><div class="t">올린 <b class="num">%d</b>건 중 '
            '<b class="num">%d</b>건 처리 · 남은 <b class="num">%d</b>건'
            '</div></div>' % (pc, 전체, 끝, 남음))


def 왜멈췄나(물음):
    it = "".join(
        '<div class="it"><div class="c">%s</div><div class="w">%s'
        '<span class="r">막는 위험 — %s</span></div></div>'
        % (c, _e(p), _e(r)) for c, p, r in 물음)
    return '<div class="why"><div class="h">왜 멈췄나</div>%s</div>' % it


def 통과시키면(문장, 되돌릴수없는것):
    return ('<div class="cons"><div class="h">통과시키면</div>%s'
            '<span class="irr">되돌릴 수 없는 것 — %s</span></div>'
            % (_e(문장), _e(되돌릴수없는것)))


def 본문(글):
    import re
    s = _e(글 or "")
    s = re.sub(r"(\[\d+\])", r'<span class="q">\1</span>', s)
    return '<div class="body">%s</div>' % s


def _e(s):
    return (str(s or "").replace("&", "&amp;")
            .replace("<", "&lt;").replace(">", "&gt;"))
