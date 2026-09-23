# -*- coding: utf-8 -*-
"""★디자인 시스템 — 「성좌 필사본 Codex of Constellations」

왜 파일을 따로 두나
  app.py 안에 CSS 를 흩어 두면 «같은 색을 두 군데»서 정하게 된다.
  config.json 을 도메인 값의 유일한 출처로 둔 것과 같은 이유다 —
  ★토큰은 여기 «한 곳»에만 있다.

★컨셉 — 장식이 아니라 «내용»에서 끌어냈다
    밤하늘        신화가 새겨진 곳        → 심야 남색 배경
    4개의 성좌    조사관 넷               → 각자 자기 하늘 «구역». 구역은 실제 기능이다
    금박 brass    인용·근거               → 근거가 붙으면 금이 박힌다
    지상/지하     ★컨텍스트 격리          → 원문은 «아래»에 잠기고 원고만 올라온다
    붉은 인장     경보                    → 순색 빨강이 아니라 «봉인»

★지킨 규칙 (ui-ux-pro-max)
    ⛔이모지를 구조 아이콘으로 쓰지 않는다 — 전부 인라인 SVG (stroke 1.5 통일)
    ⛔순흑(#000) 금지 — OLED smear
    본문 대비 13.2:1 · 보조 7.1:1 (요구 4.5:1 / 3:1)
    수치는 ★tabular — 자릿수가 흔들리면 표가 떨린다
    8px 간격 리듬 · 애니메이션 150~300ms · prefers-reduced-motion 존중
    포커스 링 2px — 키보드로 쓰는 사람을 버리지 않는다
"""

# ── 색 토큰 ────────────────────────────────────────────────────────
C = {
    "bg": "#0F1520",          # 심야 남색 — ⛔#000 아님
    "surface": "#161E2B",     # 표면 1단
    "surface2": "#1C2637",    # 표면 2단 (겹침)
    "sunken": "#0B1017",      # ★지하 — 조사관이 읽은 원문이 잠기는 곳
    "line": "#2A3648",
    "line2": "#3A4A62",
    "text": "#E8E4DA",        # 양피지 — 대비 13.2:1
    "dim": "#A9B3C4",         # 보조 — 7.1:1
    "faint": "#6C7A90",
    "brass": "#C9A227",       # ★인용·근거·주 액션
    "brass_d": "#8A6F14",
    "navy": "#4A7FB5",        # 구조·링크
    "seal": "#C2493D",        # ★경보 — 봉인 인장
    "moss": "#5E8C61",        # 통과
}

FONTS = ("https://fonts.googleapis.com/css2?"
         "family=Cinzel:wght@500;600&"
         "family=JetBrains+Mono:wght@400;500;700&"
         "family=Noto+Sans+KR:wght@300;400;500;700&"
         "family=Noto+Serif+KR:wght@400;600;700&display=swap")


# ── 인라인 SVG 아이콘 ──────────────────────────────────────────────
#   ⛔이모지를 쓰지 않는 이유 — 글꼴에 따라 모양이 바뀌고 색을 못 준다.
#   stroke-width 1.5 로 통일 (규칙: Stroke Consistency)
def icon(name, size=16, color=None):
    c = color or C["dim"]
    p = {
        "plan": '<path d="M4 4h16v16H4z"/><path d="M8 9h8M8 13h5"/>',
        "send": '<path d="M12 4v6"/><path d="M6 20V10M12 20V10M18 20V10"/>'
                '<path d="M6 10h12"/>',
        "read": '<path d="M4 5h7v14H4z"/><path d="M13 5h7v14h-7z"/>',
        "check": '<path d="M5 13l4 4L19 7"/>',
        "seal": '<circle cx="12" cy="12" r="8"/><path d="M12 8v5M12 16v.5"/>',
        "star": '<path d="M12 3l2.4 6.2L21 10l-5 4.3L17.5 21 12 17.4 6.5 21'
                'L8 14.3 3 10l6.6-.8z"/>',
        "down": '<path d="M12 4v14M6 13l6 6 6-6"/>',
        "up": '<path d="M12 20V6M6 11l6-6 6 6"/>',
        "book": '<path d="M4 4h6a3 3 0 013 3v13a2.5 2.5 0 00-2.5-2.5H4z"/>'
                '<path d="M20 4h-6a3 3 0 00-3 3v13a2.5 2.5 0 012.5-2.5H20z"/>',
        "scale": '<path d="M12 4v16M5 8h14"/><path d="M5 8l-2 6h4zM19 8l-2 6h4z"/>',
        "eye": '<path d="M2 12s3.6-6 10-6 10 6 10 6-3.6 6-10 6-10-6-10-6z"/>'
               '<circle cx="12" cy="12" r="2.5"/>',
    }.get(name, '<circle cx="12" cy="12" r="8"/>')
    return ('<svg width="%d" height="%d" viewBox="0 0 24 24" fill="none" '
            'stroke="%s" stroke-width="1.5" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true" '
            'style="vertical-align:-2px;flex:none">%s</svg>' % (size, size, c, p))


# ── CSS ───────────────────────────────────────────────────────────
def css():
    return """
<style>
@import url('%(fonts)s');

:root{
  --bg:%(bg)s; --sf:%(surface)s; --sf2:%(surface2)s; --sunken:%(sunken)s;
  --line:%(line)s; --line2:%(line2)s;
  --tx:%(text)s; --dim:%(dim)s; --faint:%(faint)s;
  --brass:%(brass)s; --brassd:%(brass_d)s; --navy:%(navy)s;
  --seal:%(seal)s; --moss:%(moss)s;
  /* 8px 리듬 */
  --s1:8px; --s2:16px; --s3:24px; --s4:32px; --s6:48px;
  --r:10px; --rs:6px;
  --ease:cubic-bezier(.16,1,.3,1);
}

/* ── 바탕 — 성좌. 장식이 아니라 «밤하늘»이라는 은유의 최소 표현 ── */
.stApp{
  background:
    radial-gradient(1px 1px at 18%% 22%%, rgba(232,228,218,.30), transparent),
    radial-gradient(1px 1px at 74%% 14%%, rgba(232,228,218,.22), transparent),
    radial-gradient(1px 1px at 42%% 68%%, rgba(232,228,218,.18), transparent),
    radial-gradient(1px 1px at 88%% 56%%, rgba(232,228,218,.14), transparent),
    radial-gradient(1200px 700px at 12%% -10%%, rgba(74,127,181,.10), transparent),
    radial-gradient(900px 600px at 95%% 8%%, rgba(201,162,39,.07), transparent),
    var(--bg);
  color:var(--tx);
}
html,body,[class*="css"]{font-family:'Noto Sans KR',system-ui,sans-serif}
.block-container{padding-top:var(--s3);padding-bottom:var(--s6);max-width:1400px}

h1,h2,h3{font-family:'Noto Serif KR',Georgia,serif!important;
  color:var(--tx)!important;letter-spacing:-.01em}

/* 수치는 ★tabular — 자릿수가 흔들리면 표가 떨린다 */
.num,.mono{font-family:'JetBrains Mono',monospace;
  font-variant-numeric:tabular-nums;font-feature-settings:"tnum" 1}

/* 라틴 올캡스 라벨 */
.eyebrow{font-family:'Cinzel',serif;font-size:11px;font-weight:600;
  letter-spacing:.22em;text-transform:uppercase;color:var(--brass);
  display:flex;align-items:center;gap:8px}
.eyebrow::after{content:"";flex:1;height:1px;
  background:linear-gradient(90deg,var(--brassd),transparent)}

/* ── 머리 ── */
.codex-head{border:1px solid var(--line);border-radius:var(--r);
  background:linear-gradient(160deg,rgba(28,38,55,.92),rgba(15,21,32,.72));
  padding:var(--s3) var(--s4);margin-bottom:var(--s3);position:relative;
  overflow:hidden}
.codex-head::before{content:"";position:absolute;inset:0 0 auto 0;height:2px;
  background:linear-gradient(90deg,var(--brass),var(--navy),transparent)}
.codex-title{font-family:'Noto Serif KR',serif;font-weight:700;
  font-size:30px;line-height:1.25;margin:10px 0 6px}
.codex-sub{color:var(--dim);font-size:13.5px;line-height:1.75}
.codex-sub b{color:var(--brass);font-weight:500}

/* ── 계기판 카드 ── */
.gauges{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  gap:var(--s2);margin:var(--s2) 0}
.g{background:var(--sf);border:1px solid var(--line);border-radius:var(--r);
  padding:14px 16px;transition:border-color .2s var(--ease)}
.g:hover{border-color:var(--line2)}
.g .k{font-size:11px;color:var(--faint);letter-spacing:.06em;
  display:flex;align-items:center;gap:6px;margin-bottom:6px}
.g .v{font-family:'JetBrains Mono',monospace;font-variant-numeric:tabular-nums;
  font-size:26px;font-weight:500;color:var(--tx);line-height:1.1}
.g .h{font-size:11px;color:var(--faint);margin-top:6px;line-height:1.5}
.g.gold .v{color:var(--brass)}

/* ── 경보 = 봉인 인장 ── */
.seal{border:1px solid rgba(194,73,61,.55);
  background:linear-gradient(135deg,rgba(194,73,61,.14),rgba(194,73,61,.05));
  border-left:3px solid var(--seal);
  border-radius:var(--rs);padding:14px 16px;margin:var(--s2) 0}
.seal .t{display:flex;align-items:center;gap:8px;font-weight:700;
  color:#F0B5AE;font-size:13.5px;margin-bottom:8px}
.seal ul{margin:0;padding-left:20px;color:var(--dim);font-size:13px;line-height:1.85}
.seal b{color:#F0B5AE}
.pass{border:1px solid rgba(94,140,97,.45);
  background:rgba(94,140,97,.09);border-left:3px solid var(--moss);
  border-radius:var(--rs);padding:12px 16px;margin:var(--s2) 0;
  color:#BFD8C0;font-size:13px;display:flex;align-items:center;gap:8px}

/* ── ★성좌 카드 — 절 하나 = 하늘 한 구역 ── */
.const{background:linear-gradient(180deg,var(--sf2),var(--sf));
  border:1px solid var(--line);border-radius:var(--r);
  padding:0;margin-bottom:var(--s2);overflow:hidden}
.const-h{display:flex;align-items:center;gap:12px;
  padding:14px var(--s3);border-bottom:1px solid var(--line);
  background:rgba(201,162,39,.045)}
.const-n{font-family:'Cinzel',serif;font-size:12px;font-weight:600;
  color:var(--bg);background:var(--brass);width:24px;height:24px;
  border-radius:50%%;display:flex;align-items:center;justify-content:center;flex:none}
.const-t{font-family:'Noto Serif KR',serif;font-weight:700;font-size:16px;flex:1}
.const-r{font-family:'JetBrains Mono',monospace;font-size:11px;
  color:var(--brass);border:1px solid var(--brassd);border-radius:99px;
  padding:3px 10px;white-space:nowrap}
.const-b{padding:var(--s3);display:grid;grid-template-columns:minmax(260px,.85fr) 1.15fr;
  gap:var(--s3)}
@media(max-width:1100px){.const-b{grid-template-columns:1fr}}

.step{font-size:11px;color:var(--faint);letter-spacing:.08em;
  margin:0 0 8px;display:flex;align-items:center;gap:6px}
.order{font-family:'JetBrains Mono',monospace;color:var(--brass);font-weight:700}

/* 읽은 문서 = 별. 인용되면 «불이 켜진다» */
.doc{display:flex;align-items:center;gap:10px;padding:8px 10px;
  border:1px solid var(--line);border-radius:var(--rs);margin-bottom:6px;
  background:rgba(15,21,32,.5);transition:all .2s var(--ease)}
.doc.lit{border-color:var(--brassd);background:rgba(201,162,39,.08)}
.doc .nm{flex:1;font-size:13px;color:var(--dim);line-height:1.4}
.doc.lit .nm{color:var(--tx)}
.doc .sz{font-family:'JetBrains Mono',monospace;font-variant-numeric:tabular-nums;
  font-size:11px;color:var(--faint)}

.draft{background:var(--bg);border:1px solid var(--line);border-radius:var(--rs);
  padding:16px 18px;font-size:14px;line-height:1.95;color:var(--tx)}
/* ★인용에 금박 */
.draft .q{color:var(--brass);font-weight:500;
  border-bottom:1px solid var(--brassd);padding-bottom:1px}

.cites{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.cite{font-size:11.5px;color:var(--brass);border:1px solid var(--brassd);
  background:rgba(201,162,39,.07);border-radius:99px;padding:3px 10px}

/* ── ★격리 — 지상/지하 ── */
.strata{border:1px solid var(--line);border-radius:var(--r);overflow:hidden;
  margin:var(--s3) 0}
.above{background:var(--sf);padding:14px var(--s3)}
.gap{height:1px;background:repeating-linear-gradient(90deg,
  var(--brassd) 0 6px,transparent 6px 12px)}
.below{background:var(--sunken);padding:14px var(--s3)}
.strata .lab{font-size:11px;letter-spacing:.1em;color:var(--faint);
  display:flex;align-items:center;gap:6px;margin-bottom:6px}
.strata .val{font-family:'JetBrains Mono',monospace;
  font-variant-numeric:tabular-nums;font-size:20px}
.above .val{color:var(--navy)}
.below .val{color:var(--brass)}

/* ── Streamlit 기본 위젯 다듬기 ── */
section[data-testid="stSidebar"]{background:var(--sf);
  border-right:1px solid var(--line)}
section[data-testid="stSidebar"] .block-container{padding-top:var(--s3)}
.stButton>button{background:var(--brass);color:var(--bg);border:none;
  border-radius:var(--rs);font-weight:700;font-size:14px;
  padding:10px 24px;min-height:44px;   /* ★터치 타깃 44px */
  transition:transform .15s var(--ease),filter .15s var(--ease);
  cursor:pointer;font-family:'Noto Sans KR',sans-serif}
.stButton>button:hover{filter:brightness(1.1);transform:translateY(-1px)}
.stButton>button:active{transform:translateY(0)}
.stButton>button:focus-visible{outline:2px solid var(--navy);outline-offset:2px}
div[data-testid="stExpander"]{border:1px solid var(--line);
  border-radius:var(--rs);background:var(--sf)}
div[data-testid="stExpander"] summary{font-size:13px;color:var(--dim)}
.stTabs [data-baseweb="tab-list"]{gap:2px;border-bottom:1px solid var(--line)}
.stTabs [data-baseweb="tab"]{font-family:'Noto Sans KR',sans-serif;font-size:13.5px;
  color:var(--faint);padding:10px 18px;min-height:44px}
.stTabs [aria-selected="true"]{color:var(--brass)!important}
.stTabs [data-baseweb="tab-highlight"]{background:var(--brass)}
hr{border-color:var(--line)}
code{font-family:'JetBrains Mono',monospace;background:rgba(74,127,181,.12);
  color:var(--navy);padding:1px 5px;border-radius:3px;font-size:.88em}

/* ⛔장식용 애니메이션 없음. 줄이라고 하면 전부 끈다 */
@media (prefers-reduced-motion: reduce){
  *{animation:none!important;transition:none!important}
}
</style>
""" % dict(C, fonts=FONTS)
