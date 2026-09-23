# -*- coding: utf-8 -*-
"""★디자인 시스템 — 「측량 도면」. 결정의 출처는 DESIGN.md 다.

이 파일은 DESIGN.md 를 «코드로 옮긴 것»뿐이다.
값을 여기서 «정하지» 않는다 — 정하려면 DESIGN.md 를 고치고 옮긴다.
(config.json 이 도메인 값의 유일한 출처인 것과 같은 이유)

★앞 판을 왜 버렸나
  2판 「성좌 필사본」은 다크 + 명조 + 금박 + 올캡스 라벨이었다.
  2026 AI 생성 UI 표식 16개 중 ★9개를 밟았다 —
  다크모드+올캡스(#5) · 그라디언트(#7) · 글로우(#8) · H1 위 배지(#10)
  · ★카드 왼쪽 컬러 보더(#11, 가장 확실한 표식) · 동일 카드 반복(#12)
  · 1·2·3 번호 단계(#13) · 스탯 배너 줄(#14) · 올캡스 제목(#16)
  그리고 「안티-슬롭」 조언 자체가 새 클리셰가 됐다(크림+세리프+세이지).

⇒ 「무엇을 피하나」가 아니라 ★「이 내용에 무엇이 맞나」로 정했다.
  이 시스템이 하는 일은 «자료를 구역으로 나눠 맡기고 추적하는 것» — 그건 측량이다.
"""

# ── 토큰 — DESIGN.md §토큰 그대로 ─────────────────────────────────
C = {
    "paper": "#FAF9F5",    # 미색. ⛔순백 아님 · 베이지도 아님
    "ink": "#16171A",      # 본문. ⛔순흑 아님
    "ink60": "#5B5D63",
    "ink40": "#8A8C92",
    "rule": "#DDD9CE",     # ★괘선 — 주 구조 요소
    "rule2": "#EFECE5",
    "mark": "#A33420",     # ★강조 «단 하나» — 근거·경보·검토 표시
    "markbg": "#FBEAE5",
}

# IBM Plex — 엔지니어링 도큐먼트용 서체. ⛔Inter·Geist·Space Grotesk 안 씀
FONTS = ("https://fonts.googleapis.com/css2?"
         "family=IBM+Plex+Mono:wght@400;500;600&"
         "family=IBM+Plex+Sans+KR:wght@300;400;500;600;700&display=swap")

# ★조사관 구분 — 색이 아니라 «선 모양». 도면의 범례 문법이고,
#   색맹에게도 갈린다(규칙 color-not-only).
DASH = ["none", "5 3", "1.5 3", "7 3 1.5 3"]
DASH_이름 = ["실선", "긴 파선", "점선", "일점쇄선"]


def css():
    return """
<style>
@import url('%(fonts)s');

:root{
  --paper:%(paper)s; --ink:%(ink)s; --ink60:%(ink60)s; --ink40:%(ink40)s;
  --rule:%(rule)s; --rule2:%(rule2)s; --mark:%(mark)s; --markbg:%(markbg)s;
}

/* ⛔그림자 0 · 그라디언트 0 · 글로우 0 — 도면에는 없다 */
.stApp{background:var(--paper);color:var(--ink)}
html,body,[class*="css"],.stMarkdown,p,div,span,li,td,th{
  font-family:'IBM Plex Sans KR','Apple SD Gothic Neo',sans-serif}
.block-container{padding-top:26px;padding-bottom:90px;max-width:1240px}
*{box-shadow:none!important;text-shadow:none!important}

h1,h2,h3,h4{font-family:'IBM Plex Sans KR',sans-serif!important;
  color:var(--ink)!important;font-weight:600!important;letter-spacing:-.02em}

.num{font-family:'IBM Plex Mono',monospace;font-variant-numeric:tabular-nums;
  font-feature-settings:"tnum" 1;font-weight:500}

/* ── 머리 — ⛔가운데 정렬 없음 · ⛔배지 없음 ───────────────────── */
.hd{border-bottom:1px solid var(--ink);padding-bottom:14px;margin-bottom:22px}
.hd h1{font-size:28px;margin:0 0 6px;line-height:1.25}
.hd .meta{font-size:12.5px;color:var(--ink60);line-height:1.7}
.hd .meta b{color:var(--ink);font-weight:500}
.hd .meta .num{color:var(--ink)}

/* ── ★괘선 — 카드 대신 이것으로 나눈다 ────────────────────────── */
.rule{border-top:1px solid var(--rule);margin:30px 0 16px;padding-top:14px}
.rule .cap{font-size:12px;color:var(--ink40);margin-bottom:2px}
.rule h2{font-size:17px;margin:0 0 4px}
.rule .sub{font-size:13px;color:var(--ink60);line-height:1.8;max-width:78ch}

/* ── ★판독 — 수치를 «문장 안»에. ⛔스탯 배너 줄 없음 ──────────── */
.read{border-left:0;padding:0;margin:14px 0 0}
.read li{list-style:none;padding:9px 0 9px 22px;position:relative;
  border-bottom:1px solid var(--rule2);font-size:14px;line-height:1.75;
  max-width:88ch}
.read li:last-child{border-bottom:0}
.read li::before{content:"";position:absolute;left:4px;top:17px;
  width:9px;height:1px;background:var(--ink40)}
.read li b{font-weight:600}
.read li .why{display:block;color:var(--ink60);font-size:12.5px;margin-top:3px}

/* ── 경보 — ⛔왼쪽 컬러 보더 아님. 바탕으로 표시 ───────────────── */
.alarm{background:var(--markbg);padding:12px 16px;margin:14px 0;
  font-size:13.5px;line-height:1.8}
.alarm .h{font-weight:600;color:var(--mark);margin-bottom:4px}
.alarm ul{margin:0;padding-left:18px;color:var(--ink)}
.clear{font-size:13px;color:var(--ink60);padding:10px 0;
  border-top:1px solid var(--rule2);border-bottom:1px solid var(--rule2)}

/* ── 절 원고 — ⛔카드 아님. 본문 조판 ─────────────────────────── */
.sec{margin:26px 0 0;padding-top:16px;border-top:1px solid var(--rule)}
.sec .top{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;
  margin-bottom:10px}
.sec .idx{font-family:'IBM Plex Mono',monospace;font-size:12px;
  color:var(--ink40)}
.sec .ttl{font-size:16.5px;font-weight:600;letter-spacing:-.01em}
.sec .who{font-size:12px;color:var(--ink60)}
.sec .body{display:grid;grid-template-columns:1fr 250px;gap:34px;
  align-items:start}
@media(max-width:980px){.sec .body{grid-template-columns:1fr}}
.sec .draft{font-size:14.5px;line-height:1.95;max-width:74ch;color:var(--ink)}
.sec .draft .q{color:var(--mark);font-weight:500}   /* ★근거 = 강조색 */
.aside{font-size:12px;color:var(--ink60);line-height:1.7}
.aside .t{color:var(--ink40);margin-bottom:6px}
.aside .d{padding:4px 0;border-bottom:1px solid var(--rule2);
  display:flex;gap:8px;align-items:baseline}
.aside .d:last-child{border-bottom:0}
.aside .d .n{flex:1}
.aside .d.used .n{color:var(--ink)}
.aside .d .sz{font-family:'IBM Plex Mono',monospace;
  font-variant-numeric:tabular-nums;color:var(--ink40);font-size:11px}
.aside .d .mk{color:var(--mark);font-size:11px;width:8px}

/* ── 격리 단면 ───────────────────────────────────────────────── */
.cut{margin:16px 0;border-top:1px solid var(--ink);
  border-bottom:1px solid var(--ink)}
.cut .row{display:flex;align-items:baseline;gap:14px;padding:11px 0;
  font-size:13px}
.cut .row+.row{border-top:1px dashed var(--rule)}
.cut .k{width:190px;color:var(--ink60);flex:none}
.cut .v{font-family:'IBM Plex Mono',monospace;
  font-variant-numeric:tabular-nums;font-size:17px}
.cut .n{color:var(--ink40);font-size:12px}

/* ── Streamlit 위젯 — 도면 문법에 맞춘다 ──────────────────────── */
.stButton>button{background:var(--ink);color:var(--paper);border:0;
  border-radius:0;font-weight:500;font-size:13.5px;padding:11px 26px;
  min-height:44px;font-family:'IBM Plex Sans KR',sans-serif;cursor:pointer;
  transition:background .12s linear}
.stButton>button:hover{background:var(--mark)}
.stButton>button:focus-visible{outline:2px solid var(--mark);outline-offset:2px}
section[data-testid="stSidebar"]{background:var(--paper);
  border-right:1px solid var(--rule)}
div[data-testid="stExpander"]{border:0;border-top:1px solid var(--rule2);
  border-radius:0;background:transparent}
div[data-testid="stExpander"] summary{font-size:12.5px;color:var(--ink60);
  padding-left:0}
div[data-testid="stExpander"] summary:hover{color:var(--mark)}
[data-baseweb="select"]>div{border-radius:0;border-color:var(--rule);
  background:transparent}
.stSlider [data-baseweb="slider"] div[role="slider"]{background:var(--ink)}
hr{border-color:var(--rule)}
code{font-family:'IBM Plex Mono',monospace;background:transparent;
  color:var(--ink60);font-size:.9em;padding:0}
.stCaption,[data-testid="stCaptionContainer"]{color:var(--ink40)!important}

/* ── ★표제 도면 — 장식이 아니라 «코퍼스 그 자체» ──────────────── */
.hero{margin:0 0 4px}
.hero svg{display:block;width:100%%;height:auto}

/* ── ★띠 — 각 칸이 «무엇을 하는 칸인지» 말한다 ──────────────────
   처음 온 사람은 「설정」이 왜 있는지 모른다. 이름만 두면 안 된다. */
.bar{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;
  border-top:1px solid var(--ink);padding-top:9px;margin:30px 0 10px}
.bar .lbl{font-size:14px;font-weight:600;flex:none}
.bar .hint{font-size:12.5px;color:var(--ink60);line-height:1.65;max-width:76ch}
.bar .hint b{color:var(--ink);font-weight:500}

/* ── 조건 칸 — ⛔글 덩어리 대신 «칸» ─────────────────────────── */
.chk{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));
  gap:1px;background:var(--rule);border:1px solid var(--rule);margin:10px 0}
.chk .c{background:var(--paper);padding:10px 13px}
.chk .q{font-size:12px;color:var(--ink60);line-height:1.5;margin-bottom:5px}
.chk .a{font-size:13px;font-weight:600;line-height:1.45}
.note{font-size:12px;color:var(--ink40);line-height:1.7;margin:6px 0 0;
  max-width:92ch}
.note b{color:var(--ink60);font-weight:500}

/* ── 지금 값 한 줄 ─────────────────────────────────────────── */
.sum{font-size:12.5px;color:var(--ink60);line-height:1.8;margin:12px 0 0;
  padding:9px 0;border-top:1px dashed var(--rule)}
.sum b{color:var(--ink);font-weight:600}
.mini{font-size:12px;color:var(--ink60);margin-bottom:6px;line-height:1.6}
.mini b{color:var(--ink);font-weight:500}

/* ── 사용법 — 처음 온 사람을 위한 세 걸음 ───────────────────────── */
.how{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
  gap:1px;background:var(--rule);border:1px solid var(--rule);margin:14px 0 0}
.how .s{background:var(--paper);padding:11px 14px}
.how .n{font-family:'IBM Plex Mono',monospace;font-size:11px;
  color:var(--mark);margin-bottom:4px}
.how .t{font-size:13px;font-weight:600;margin-bottom:3px}
.how .d{font-size:12px;color:var(--ink60);line-height:1.6}

@media (prefers-reduced-motion: reduce){*{transition:none!important}}
</style>
""" % dict(C, fonts=FONTS)
