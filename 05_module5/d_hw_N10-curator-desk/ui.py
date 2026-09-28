# -*- coding: utf-8 -*-
"""★디자인 시스템 v2 — 「전시 도록 · 큐레이토리얼 심사대」

이 파일은 DESIGN.md 를 «코드로 옮긴 것»뿐이다.
값을 여기서 «정하지» 않는다 — 정하려면 DESIGN.md 를 고치고 옮긴다.

★v1 을 왜 버렸나 — 주영님 지적(2026-09-28)
  「저번이랑 똑같네. 서비스 느낌도 안 나고, 임팩트 있는 헤드가 없다」

  ⛔맞는 지적이었다. v1 은 노드9 의 토큰을 «그대로» 이어받고,
    REPORT 에 「같은 사람의 산출물이라는 표시」라고 ★정당화까지 해 뒀다.
    그게 「똑같다」의 원인이다. 이어받은 게 아니라 ★안 바꾼 것이다.
  그리고 ★«헤드»가 없었다. h1 이 25px 이었다 — 그건 제목 한 줄이지 헤드가 아니다.

★레퍼런스를 «실제로 열어» 봤다 (kdt-origin.vercel.app)
  ORIGIN(모듈1 메인퀘)은 같은 도메인(미술 아카이브)이고 훨씬 잘 돼 있다.
  ORIGIN 의 DESIGN-v2.md 는 8곳을 리서치했다 —
  Are.na · Google Arts&Culture · Design Reviewed · Public Domain Review ·
  Cosmos · Fonts In Use · Letterform · Cooper Hewitt.

  ★거기서 읽어 낸 «에디토리얼 헤드»의 문법
    ① 아이브로우   작은 대문자 · 자간 .16em · 흐린 색
    ② 거대 두 줄   같은 크기인데 ★무게·색이 다르다 (900 잉크 / 300 강조색)
    ③ lede        여러 줄 · 흐린 잉크
    ④ 메타줄      ★숫자는 크고 진하게 · 라벨은 작은 대문자 · 세로 구분선
    ⑤ 섹션마다 «아이브로우 + 헤드» 3단이 반복 — 리듬이 된다
    ⑥ 가는 가로선으로 구역을 나눈다

★그런데 «그대로» 베끼지 않는다 — 그러면 또 「똑같다」가 된다
  ORIGIN   따뜻한 베이지(#f5f2ea) + 테라코타(#b4522b)  · 종이 전체
  노드9     찬 백(#FCFCFA) + 벽돌(#A33420)            · 괘선 도면
  ★노드10   ★먹빛 남색 헤드 + 미색 작업면 + ★금빛 황토
           헤드를 «어둡게» 깐다 — 심사대의 무게. 둘 다와 겹치지 않는다.

★그리고 이건 «브라우즈 사이트»가 아니라 «작업 도구»다
  ORIGIN 은 헤드가 화면을 가득 채워도 된다 — 한 번 보고 들어가니까.
  ⛔여기는 251건을 처리하는 화면이다. 헤드가 매번 화면을 먹으면 안 된다.
  ⇒ ★헤드는 «압축된 에디토리얼». 크되 낮다. 작업 영역이 바로 이어진다.

★접근성 — 규칙 이름 그대로 (redteam.py 가 «실제로» 잰다)
  color-contrast · color-not-only · touch-target-size · focus-states
  progressive-disclosure · reduced-motion · deep-linking · empty-states
"""

# ── 토큰 — DESIGN.md §토큰 그대로 ─────────────────────────────────
C = {
    # 작업면 — 미색. ⛔순백 아님
    "paper": "#F7F4EC",
    "paper2": "#EFEAE0",     # 가라앉은 면 (조작면)
    "paper3": "#E4DED1",     # 더 가라앉은 면

    # ★먹빛 «남색» — ORIGIN 의 갈빛 잉크, 노드9 의 중성 먹과 다르다
    "ink": "#14181F",
    "ink70": "#3D4550",
    "ink50": "#636C7A",
    "ink30": "#8C95A2",

    "line": "#D5CEBF",
    "line2": "#E7E1D4",

    # ★금빛 황토 — «강조». ORIGIN 테라코타·노드9 벽돌과 겹치지 않는다
    "gold": "#7E5912",
    "goldbg": "#F2E9D4",

    # ★멈춤(위험) 전용 — 이유·결과 예고에만. 강조색과 «역할»이 다르다
    "stop": "#98311A",
    "stopbg": "#F7E6E0",

    "ok": "#2B5A42",         # 자동 처리
    # 조작요소 «경계» — WCAG 1.4.11 (3:1). redteam 이 잰다
    "edge": "#8B8270",
}

# Pretendard — 한글 모던 그로테스크. ★900 까지 있어 «무게 대비»를 줄 수 있다.
#   ORIGIN 도 같은 서체다 — ⛔서체까지 억지로 다르게 하지 않는다.
#   한글 본문에 맞는 선택지는 많지 않고, «배치»가 다르면 충분히 다른 물건이 된다.
FONTS = ("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/"
         "dist/web/static/pretendard-dynamic-subset.css")
MONO = ("https://fonts.googleapis.com/css2?"
        "family=IBM+Plex+Mono:wght@400;500;600&display=swap")


def css():
    return """
<style>
@import url('%(fonts)s');
@import url('%(mono)s');

:root{
  --paper:%(paper)s; --paper2:%(paper2)s; --paper3:%(paper3)s;
  --ink:%(ink)s; --ink70:%(ink70)s; --ink50:%(ink50)s; --ink30:%(ink30)s;
  --line:%(line)s; --line2:%(line2)s;
  --gold:%(gold)s; --goldbg:%(goldbg)s;
  --stop:%(stop)s; --stopbg:%(stopbg)s;
  --ok:%(ok)s; --edge:%(edge)s;
  --wrap:1280px;
}

/* ⛔그림자 0 · 그라디언트 0 · 글로우 0 */
*{box-shadow:none!important;text-shadow:none!important}
.stApp{background:var(--paper);color:var(--ink)}
html,body,[class*="css"],.stMarkdown,p,div,span,li,td,th,button,input,textarea{
  font-family:'Pretendard','Pretendard Variable','Apple SD Gothic Neo',
    system-ui,sans-serif;
  -webkit-font-smoothing:antialiased}
.block-container{padding-top:0!important;padding-bottom:88px;
  max-width:var(--wrap)}
h1,h2,h3,h4{color:var(--ink)!important;letter-spacing:-.02em}
.num{font-family:'IBM Plex Mono',monospace;font-variant-numeric:tabular-nums;
  font-feature-settings:"tnum" 1}

/* ══ ★헤드 — «잉크»로 깐다. 심사대의 무게 ═══════════════════════
   ⛔ORIGIN 처럼 화면을 가득 채우지 않는다 — 여기는 251건을 «처리»하는
     화면이다. 크되 «낮다». 작업 영역이 바로 이어진다.            */
/* ⛔위를 안 띄우면 Streamlit 툴바(높이 ~46px)가 아이브로우를 «자른다».
     실제로 잘렸다 — 캡처로 확인했다. */
.masthead{background:var(--ink);color:var(--paper);
  margin:0 -50vw 10px -50vw;padding:62px 50vw 26px 50vw}
.masthead .in{max-width:var(--wrap);margin:0 auto}

/* ① 아이브로우 — 작은 대문자 · 자간 넓게 */
.eyebrow{font-family:'IBM Plex Mono',monospace;font-size:11px;
  letter-spacing:.22em;text-transform:uppercase;color:var(--ink30);
  margin:0 0 12px}
.masthead .eyebrow{color:#A6B0BD}

/* ② ★거대 두 줄 — 같은 크기, «다른 무게와 색». 이 대비가 리듬이다 */
/* ⛔Streamlit 이 h1 에 «자기 padding(20/16px)»과 ★앵커 링크 span(16px)을 얹는다.
     그래서 두 줄(106px)인데 실제 높이가 ★195px 이었다 — 재서 찾았다.
     추측으로 margin 을 만지다 놓칠 자리다. */
.mast-title{font-size:clamp(30px,4.4vw,52px);line-height:1.02;
  letter-spacing:-.035em;margin:0!important;padding:0!important;
  text-wrap:balance}
.masthead h1>span:last-child:not(.a):not(.b){display:none!important}
.masthead [data-testid="stHeaderActionElements"]{display:none!important}
.mast-title .a{font-weight:900;display:block;color:var(--paper)}
.mast-title .b{font-weight:300;display:block;color:#DFAF4E}

/* ③ lede */
/* ⛔Streamlit 이 <p> 에 자기 margin 을 얹어 제목 아래가 «너무» 벌어졌다 */
.masthead p{margin:0}
.mast-lede{margin:16px 0 0!important;font-size:14.5px;line-height:1.7;
  color:#AEB7C3;max-width:58ch}
.mast-lede b{color:var(--paper);font-weight:600}

/* ④ ★메타줄 — 숫자는 크고 진하게 · 라벨은 작은 대문자 · 세로 구분선 */
/* ★라벨이 한글이라 자간을 «거의» 안 준다. 영문은 .en 으로 따로. */
.mast-meta{margin:20px 0 0;display:flex;flex-wrap:wrap;align-items:baseline;
  font-size:11.5px;font-weight:600;letter-spacing:.01em;color:#98A2AF}
.mast-meta .en{font-family:'IBM Plex Mono',monospace;font-size:10px;
  font-weight:500;letter-spacing:.16em;text-transform:uppercase}
.mast-meta span{padding-right:20px;margin-right:20px;
  border-right:1px solid rgba(247,244,236,.2);line-height:1.5}
.mast-meta span:last-child{border-right:0;margin-right:0;padding-right:0}
.mast-meta b{color:var(--paper);font-weight:700;font-size:17px;
  letter-spacing:0;margin-right:6px;font-variant-numeric:tabular-nums}
.mast-meta b.hot{color:#DFAF4E}

/* ══ ★진행 ═══════════════════════════════════════════════════ */
.prog{margin:0 0 6px}
.prog .bar{height:6px;background:var(--paper3)}
.prog .bar i{display:block;height:6px;background:var(--gold)}
.prog .t{font-size:12px;color:var(--ink50);margin-top:7px;line-height:1.6;
  font-family:'IBM Plex Mono',monospace;letter-spacing:.04em}
.prog .t b{color:var(--ink);font-weight:600}

/* ══ ⑤ 섹션 3단 리듬 — 아이브로우 + 헤드 + 부제 ═══════════════ */
.sec{margin:24px 0 10px;padding-top:15px;border-top:1px solid var(--line)}
.sec h2{font-size:clamp(17px,2vw,22px);font-weight:800;margin:0;
  letter-spacing:-.025em}
.sec .sub{font-size:12.5px;color:var(--ink50);line-height:1.7;margin-top:5px;
  max-width:78ch}
.sec .sub b{color:var(--ink);font-weight:600}

/* ══ 대기열 — ★막대로 «보인다». 숫자만 있으면 크기가 안 읽힌다 ═══ */
.q{border-top:2px solid var(--ink);padding-top:12px;margin-top:6px}
/* ★한글 줄과 영문 줄을 «나눈다» — 자간 규칙이 다르다 */
.q .h{font-size:11.5px;font-weight:700;color:var(--ink30);
  margin-bottom:11px;line-height:1.75;letter-spacing:.01em}
.q .h .en{display:block;font-family:'IBM Plex Mono',monospace;
  font-size:10px;font-weight:500;letter-spacing:.16em;
  text-transform:uppercase;margin-top:2px}
.qrow{padding:7px 0;border-bottom:1px solid var(--line2)}
.qrow .t{display:flex;justify-content:space-between;align-items:baseline;
  font-size:13px;margin-bottom:5px;color:var(--ink70)}
.qrow .t b{font-family:'IBM Plex Mono',monospace;font-weight:600;
  font-variant-numeric:tabular-nums;color:var(--ink)}
.qrow .g{height:4px;background:var(--paper3)}
.qrow .g i{display:block;height:4px;background:var(--ink70)}
.qrow.on .g i{background:var(--gold)}
.qrow.on .t{color:var(--ink);font-weight:700}

/* ══ 갈래 표식 — ★글자가 먼저. 테두리 «모양»이 거든다 ══════════ */
.tag{display:inline-block;font-family:'IBM Plex Mono',monospace;
  font-size:11.5px;font-weight:600;line-height:1;padding:7px 11px;
  border:1px solid var(--ink);color:var(--ink);background:transparent;
  letter-spacing:.1em;white-space:nowrap}
.tag.t-발행{border-style:solid}
.tag.t-이미지{border-style:double;border-width:3px;padding:5px 9px}
.tag.t-작가{border-style:dashed}
.tag.t-카탈로그{border-style:dotted}

/* ══ ★도켓 — 한 건. ⛔왼쪽 컬러 보더 아님 ══════════════════════ */
.dk{border-top:2px solid var(--ink);padding:14px 0 0;margin:4px 0 0}
.dk .top{display:flex;align-items:center;gap:12px;flex-wrap:wrap;
  margin-bottom:14px}
.dk .pos{font-family:'IBM Plex Mono',monospace;font-size:12px;
  color:var(--ink30);letter-spacing:.06em}
.ttl{font-size:clamp(19px,2.3vw,25px);font-weight:800;line-height:1.28;
  margin:0 0 5px;letter-spacing:-.028em;text-wrap:balance}
.by{font-size:13px;color:var(--ink50)}
.by b{color:var(--ink);font-weight:600}

.thumb{display:block;width:100%%;border:1px solid var(--line)}
.cap{font-family:'IBM Plex Mono',monospace;font-size:10.5px;
  color:var(--ink30);line-height:1.8;margin-top:8px;letter-spacing:.02em}
.cap b{color:var(--ink50);font-weight:500}

/* ══ ★① 왜 멈췄나 — 이 화면에서 «제일 큰» 것 ═══════════════════ */
.why{border-top:1px solid var(--ink);padding-top:13px;margin:15px 0 15px}
.why .h{font-size:13.5px;font-weight:800;color:var(--ink);margin-bottom:9px;
  letter-spacing:-.01em}
.why .it{display:flex;gap:13px;align-items:baseline;padding:9px 0;
  border-bottom:1px solid var(--line2)}
.why .it:last-child{border-bottom:0}
.why .c{font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:600;
  color:var(--stop);flex:none;min-width:28px;letter-spacing:.04em}
.why .w{font-size:15px;line-height:1.6;color:var(--ink);font-weight:500}
.why .w .r{display:block;font-size:12.5px;color:var(--ink50);margin-top:4px;
  font-weight:400}

/* ══ ★② 통과시키면 — 버튼 «바로 위». 강의 1강 ══════════════════ */
.cons{background:var(--stopbg);padding:13px 16px;margin:0 0 14px}
.cons .h{font-size:11.5px;letter-spacing:.01em;color:var(--stop);
  font-weight:800;margin-bottom:5px}
.cons .irr{display:block;color:var(--ink50);font-size:12.5px;margin-top:6px}

/* 나갈 글 */
.body{font-size:14.5px;line-height:1.9;color:var(--ink);max-width:78ch;
  padding:11px 0;border-top:1px solid var(--line2);margin-top:4px}
/* ⛔전에는 여기가 `.body .q` 였다 — v2 에서 대기열 상자를 `.q` 로 지으면서 «겹쳤다».
     최상위 `.q{border-top:2px …;padding-top:12px}` 가 본문의 근거 표시 [1][2] 에도
     걸려 ★인용마다 위에 짧은 먹선이 떴다(2026-09-29 캡처에서 찾음). ⇒ 이름을 가른다. */
.body .cite{color:var(--gold);font-weight:600}
/* ⛔★한글 라벨에 «영문 자간»을 주면 「나 갈 글」로 벌어진다.
     UPPERCASE + letter-spacing .18em 은 ★라틴 문자 문법이다(ORIGIN 도 영문이다).
     한글은 자간을 거의 주지 않고, «무게와 색»으로 라벨임을 말한다. */
.lbl{font-size:11.5px;font-weight:700;letter-spacing:.01em;
  color:var(--ink30);margin:16px 0 3px}
/* 영문·숫자 라벨만 넓은 자간 + 대문자 */
.lbl.en,.eyebrow{font-family:'IBM Plex Mono',monospace;font-size:11px;
  font-weight:500;letter-spacing:.2em;text-transform:uppercase}

/* 자동 처리 — 안 보이면 «놓침»을 영영 못 찾는다 */
.auto{font-size:12.5px;color:var(--ink50);padding:8px 0;
  border-bottom:1px solid var(--line2);display:flex;gap:12px;
  align-items:baseline}
.auto .ok{color:var(--ok);font-weight:700;flex:none;font-size:11.5px;
  letter-spacing:.01em}

/* 빈 화면 — ⛔공백으로 두지 않는다 */
.empty{border-top:2px solid var(--ink);padding:30px 0;font-size:14.5px;
  color:var(--ink50);line-height:1.9}
.empty b{color:var(--ink);font-weight:800;display:block;
  font-size:clamp(19px,2.2vw,24px);margin-bottom:8px;letter-spacing:-.025em}

/* ══ Streamlit 위젯 ═══════════════════════════════════════════ */
.stButton>button{background:var(--paper2);color:var(--ink);
  border:1px solid var(--edge);border-radius:0;font-weight:600;
  font-size:13.5px;padding:12px 18px;min-height:46px;width:100%%;
  letter-spacing:-.01em;cursor:pointer;
  transition:background .12s linear,border-color .12s linear}
.stButton>button:hover{border-color:var(--ink);background:var(--paper3)}
.stButton>button:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
.stButton>button:disabled{opacity:.42;cursor:not-allowed}
/* ★으뜸 하나 — 「보통 무엇을 하나」를 말한다 */
button[data-testid="stBaseButton-primary"]{background:var(--ink)!important;
  color:var(--paper)!important;border-color:var(--ink)!important;
  font-weight:700!important}
button[data-testid="stBaseButton-primary"]:hover{
  background:var(--stop)!important;border-color:var(--stop)!important}

section[data-testid="stSidebar"]{background:var(--paper);
  border-right:1px solid var(--line)}
div[data-testid="stExpander"]{border:0;border-top:1px solid var(--line);
  border-radius:0;background:transparent;margin-top:10px}
div[data-testid="stExpander"] summary{font-family:'IBM Plex Mono',monospace;
  font-size:11.5px;letter-spacing:.08em;color:var(--ink50);padding-left:0}
div[data-testid="stExpander"] summary:hover{color:var(--gold)}
[data-baseweb="select"]>div,.stTextInput input,.stTextArea textarea{
  border-radius:0!important;background:var(--paper2)!important;
  border:1px solid var(--edge)!important;font-size:13.5px}
[data-baseweb="select"]>div:hover,.stTextInput input:hover,
.stTextArea textarea:hover{border-color:var(--ink)!important}
[data-baseweb="select"]>div:focus-within,.stTextInput input:focus,
.stTextArea textarea:focus{border-color:var(--gold)!important;
  outline:2px solid var(--gold);outline-offset:1px}
.stRadio [role="radiogroup"]{background:var(--paper2);
  border:1px solid var(--edge);padding:10px 14px;display:flex;gap:18px;
  flex-wrap:wrap}
.stRadio [role="radiogroup"]:hover{border-color:var(--ink)}
.stRadio label{cursor:pointer}
label[data-testid="stWidgetLabel"] p{font-size:11.5px!important;
  font-weight:700!important;letter-spacing:.01em!important;
  color:var(--ink30)!important}
hr{border-color:var(--line)}
code{font-family:'IBM Plex Mono',monospace;background:transparent;
  color:var(--ink50);font-size:.9em;padding:0}
.stCaption,[data-testid="stCaptionContainer"]{color:var(--ink30)!important;
  font-size:12px!important}
div[data-testid="stDataFrame"]{border:1px solid var(--line)}

@media (prefers-reduced-motion: reduce){*{transition:none!important}}
@media(max-width:860px){
  .masthead{padding:26px 50vw 20px 50vw}
  .mast-meta span{padding-right:13px;margin-right:13px}
}
</style>
""" % dict(C, fonts=FONTS, mono=MONO)


# ── 조각 ────────────────────────────────────────────────────────

def 헤드(관문수, 체크포인터, 작성모드, dry, 전체, 대기):
    """★마스트헤드 — «한 st.markdown» 으로 낸다.

    ⛔Streamlit 은 markdown 블록마다 따로 감싼다. 헤드를 여러 번 나눠 부르면
      배경이 끊긴다. 통째로 한 번에 낸다.
    """
    자동 = 전체 - 대기
    return (
        '<div class="masthead"><div class="in">'
        '<div class="eyebrow">Curator&#39;s Desk · 모듈5 노드10</div>'
        '<h1 class="mast-title"><span class="a">사람이 승인하는</span>'
        '<span class="b">큐레이션 데스크</span></h1>'
        '<p class="mast-lede">신화·역사 회화를 새벽에 혼자 큐레이션합니다. '
        '바깥으로 나가는 일이 <b>넷</b>이고 '
        '<b>되돌릴 수 없는 정도가 달라서</b>, 위험한 건만 멈춰 '
        '승인을 받습니다.</p>'
        '<div class="mast-meta">'
        '<span><b>%d</b>올림</span>'
        '<span><b>%d</b>자동</span>'
        '<span><b class="hot">%d</b>대기</span>'
        '<span><b>%d</b>기준</span>'
        '<span><b>4</b>갈래</span>'
        '<span class="en">%s</span>'
        '<span>작성기 %s</span>'
        '<span class="en">DRY_RUN %s</span>'
        '</div></div></div>'
        % (전체, 자동, 대기, 관문수, _e(체크포인터),
           _e(작성모드 or "?"), dry))


def 절(제목, 부제=None, 눈썹=None):
    """★섹션 3단 — 아이브로우 + 헤드 + 부제. 이 리듬이 반복된다."""
    e = '<div class="eyebrow">%s</div>' % _e(눈썹) if 눈썹 else ""
    s = '<div class="sub">%s</div>' % 부제 if 부제 else ""
    return '<div class="sec">%s<h2>%s</h2>%s</div>' % (e, _e(제목), s)


def 진행(남음, 전체):
    끝 = 전체 - 남음
    pc = (끝 / 전체 * 100) if 전체 else 100
    return ('<div class="prog"><div class="bar"><i style="width:%.1f%%">'
            '</i></div><div class="t"><b>%d</b> / %d 처리 · 남은 <b>%d</b>'
            '</div></div>' % (pc, 끝, 전체, 남음))


def 대기열(갈래수, 고른갈래, 전체대기):
    """★막대로 «보인다» — 숫자만 있으면 크기가 안 읽힌다.

    ORIGIN 의 타임라인처럼, 기능적 시각화는 «장식»이 아니다.
    「어디가 밀려 있나」가 한눈에 들어와야 한다.
    """
    큰 = max(갈래수.values()) if 갈래수 else 1
    줄 = []
    for g, n in 갈래수.items():
        on = " on" if 고른갈래 == g else ""
        줄.append('<div class="qrow%s"><div class="t"><span>%s</span>'
                  '<b>%d</b></div><div class="g"><i style="width:%.0f%%">'
                  '</i></div></div>'
                  % (on, _e(g), n, (n / 큰 * 100) if 큰 else 0))
    return ('<div class="q"><div class="h">승인 대기 %d건'
            '<span class="en">판정 = snapshot.next</span></div>%s</div>'
            % (전체대기, "".join(줄)))


def 왜멈췄나(물음):
    it = "".join(
        '<div class="it"><div class="c">%s</div><div class="w">%s'
        '<span class="r">막는 위험 — %s</span></div></div>'
        % (_e(c), _e(p), _e(r)) for c, p, r in 물음)
    return '<div class="why"><div class="h">왜 멈췄나</div>%s</div>' % it


def 통과시키면(문장, 되돌릴수없는것):
    return ('<div class="cons"><div class="h">통과시키면</div>%s'
            '<span class="irr">되돌릴 수 없는 것 — %s</span></div>'
            % (_e(문장), _e(되돌릴수없는것)))


def 태그(갈래):
    return '<span class="tag t-%s">%s</span>' % (갈래, 갈래)


def 본문(글):
    import re
    s = _e(글 or "")
    s = re.sub(r"(\[\d+\])", r'<span class="cite">\1</span>', s)
    return '<div class="body">%s</div>' % s


def _e(s):
    return (str(s or "").replace("&", "&amp;")
            .replace("<", "&lt;").replace(">", "&gt;"))
