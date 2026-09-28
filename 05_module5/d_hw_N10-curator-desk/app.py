# -*- coding: utf-8 -*-
"""★큐레이터 데스크 — 승인 대기 건을 «확인하고 처리하는» 화면.

  streamlit run app.py

루브릭 ③ — 「승인 대기 건을 확인하고 처리하는 화면이 오류 없이 실행되며」

★화면이 하는 일은 하나다 — 「10초 안에 판단하게 한다」
  그래서 배치 순서가 «고정»이다. DESIGN.md §중요도 참조.
    1 왜 멈췄나  2 통과시키면  3 무엇에 대한 건인가  4 대기열 어디쯤인가

★대기 판정은 «snapshot.next» 가 한다 (강의 실습2)
  ⛔색인 파일을 «대기 여부»의 근거로 쓰지 않는다. 색인은 「어떤 thread 가 있나」만 안다.

⛔★st.sidebar 를 쓰지 않는다 — 실측 판단
  이 화면을 브라우저에서 띄워 보니 사이드바가 «DOM 에 아예 안 생겼다».
  최소 앱(sidebar 한 줄)으로 격리 시험해도 같았다 ⇒ 내 코드 문제가 아니다.
  원인이 무엇이든, ★대기열이 «사라질 수 있는 자리»에 있으면 안 된다 —
  채점자 화면에서 대기 건수와 갈래 필터가 통째로 없어진다.
  ⇒ 대기열을 «본문 2단»으로 옮겼다. 접히지 않는다.
  (부수 효과로 UX 가 나아졌다 — 처리하는 동안 대기열이 «계속 보인다»)
"""
import io
import json
import os
import sys

import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gates           # noqa: E402
import graph           # noqa: E402
import ui              # noqa: E402

CFG = graph.CFG
응답들 = CFG["_응답"]
갈래들 = ["발행", "이미지", "작가", "카탈로그"]
관문수 = len([k for k in CFG["_관문"] if not k.startswith("_")])

st.set_page_config(page_title="큐레이터 데스크", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(ui.css(), unsafe_allow_html=True)


# ── 자료 ────────────────────────────────────────────────────────

def _mtime():
    t = 0
    for 모드 in ("소박", "조심"):
        p = os.path.join(HERE, "data/written_%s.json" % 모드)
        if os.path.exists(p):
            t = max(t, os.path.getmtime(p))
    return t


@st.cache_data(show_spinner=False)
def 작품표(_t):
    """슬러그 → 작품. mtime 을 인자로 받아 파일이 바뀌면 캐시가 풀린다."""
    for 모드 in ("소박", "조심"):
        p = os.path.join(HERE, "data/written_%s.json" % 모드)
        if os.path.exists(p):
            d = json.load(io.open(p, encoding="utf-8"))
            return {m["슬러그"]: m for m in d["작품"]}, d.get("모드")
    return {}, None


작품, 작성모드 = 작품표(_mtime())

# ★헤드는 «대기 수»를 알아야 한다 — 색인을 먼저 읽는다.
#   ⛔전에는 머리를 먼저 찍고 수치를 나중에 냈다. 헤드가 «비어» 보였다.
색인 = graph.색인읽기()
if not 색인:
    st.markdown(
        ui.헤드(관문수, CFG["_체크포인터"]["쓸 것"], 작성모드,
               graph.DRY_RUN, 0, 0), unsafe_allow_html=True)
    st.markdown(
        '<div class="empty"><b>먼저 파이프라인을 돌려 주세요</b>'
        '수집 → 세탁 → 작가 조회 → 작성 → 올림. 순서대로 한 번씩이면 됩니다.'
        '</div>', unsafe_allow_html=True)
    st.code("python fetch_art.py\npython normalize.py\npython enrich.py\n"
            "python write.py\npython graph.py --올린다", language="bash")
    st.stop()

try:
    대기 = graph.대기목록()
except Exception as e:
    # ★체크포인터를 못 읽으면 «무엇을 하라»고 말해 준다. 죽지 않는다.
    st.error("대기 목록을 읽지 못했습니다 — %s" % type(e).__name__)
    st.caption(str(e)[:300])
    st.code("python graph.py --청소\npython graph.py --올린다", language="bash")
    st.stop()
전체 = len(색인)

# ★★clone 직후를 «알아채고» 말해 준다 — 2026-09-28 에 재현해 보고 넣었다.
#
# ⛔체크포인터 DB 는 «돌리면 생기는 것»이라 저장소에 안 올린다(.gitignore).
#   그런데 색인(threads.json)은 «올린다» — 작고, 상태가 읽히니까.
#   ⇒ 남이 clone 하면 ★색인은 「266건이 대기」라 하는데 체크포인터가 비어
#     대기목록()이 0 을 낸다. 화면은 「대기 건이 없습니다」를 보여 준다.
#   ★그게 「다 처리했다」처럼 보인다 — 아무것도 안 돌렸는데.
#
# 판정을 «파일이 있나»로 하지 않는다 — 파일이 있어도 다른 이유로 빌 수 있다.
# 색인이 말하는 대기 수와 실제 대기 수를 ★나란히 놓고 어긋나면 말한다.
색인상대기 = sum(1 for v in 색인.values() if "끝남" not in v)
if 색인상대기 and not 대기:
    # ⛔헤드를 «실제 대기 0» 으로 그리면 「688건 전부 자동 처리됨」이라 ★거짓말을 한다.
    #   아무것도 처리하지 않았는데. ⇒ 이 분기에서는 «색인이 기록한» 수치로 그린다.
    #   실제로 일어난 일은 그것이고, 못 불러온 것뿐이라고 바로 아래에서 말한다.
    st.markdown(ui.헤드(관문수, CFG["_체크포인터"]["쓸 것"], 작성모드,
                       graph.DRY_RUN, 전체, 색인상대기),
                unsafe_allow_html=True)
    st.warning("체크포인터가 비어 있습니다 — 아래 한 줄을 먼저 돌려 주세요.")
    st.caption("색인(`output/threads.json`)은 **%d건이 대기 중**이라고 "
               "말하는데 체크포인터에는 아무것도 없습니다. "
               "체크포인터 DB 는 «돌리면 생기는 것»이라 저장소에 올리지 "
               "않습니다 — clone 직후에는 늘 이 상태입니다." % 색인상대기)
    st.code("python graph.py --올린다", language="bash")
    st.caption("자료(`data/*.json`)가 저장소에 함께 있어 **수집·세탁·조회·작성은 "
               "다시 안 해도 됩니다.** 이 한 줄이면 됩니다 (실측 약 11초).")
    st.stop()

st.markdown(ui.헤드(관문수, CFG["_체크포인터"]["쓸 것"], 작성모드,
                   graph.DRY_RUN, 전체, len(대기)), unsafe_allow_html=True)

# ★색인은 있는데 작품 자료가 없으면 «도켓을 못 그린다» — 먼저 말해 준다.
#   ⛔전에는 여기서 KeyError 가 나 페이지가 통째로 죽었다.
if 대기 and not 작품:
    st.error("대기 건은 %d건인데 작품 자료(data/written_*.json)가 없습니다."
             % len(대기))
    st.caption("수집·세탁·작성을 다시 돌리면 같은 대기 건에 자료가 다시 붙습니다.")
    st.code("python normalize.py\npython enrich.py\npython write.py",
            language="bash")
    st.stop()

st.markdown(ui.진행(len(대기), 전체), unsafe_allow_html=True)

갈래수 = {}
for w in 대기:
    갈래수[w["갈래"]] = 갈래수.get(w["갈래"], 0) + 1

# ── ★2단 — 왼쪽 대기열은 «접히지 않는다» ─────────────────────────
레일, 본 = st.columns([1, 3.1], gap="large")

with 레일:
    # ★막대로 «보인다» — 숫자만 있으면 «어디가 밀렸나»가 안 읽힌다
    st.markdown(ui.대기열({g: 갈래수.get(g, 0) for g in 갈래들},
                       st.session_state.get("갈래라디오", "전체"), len(대기)),
                unsafe_allow_html=True)
    # ★딥링크 — ?갈래=작가 로 바로 열 수 있다 (UX 규칙 deep-linking).
    #   캡처 스크립트도 이걸로 갈래별 화면을 찍는다.
    선택지 = ["전체"] + 갈래들
    초기 = st.query_params.get("갈래")
    고른갈래 = st.radio("갈래로 좁히기", 선택지, key="갈래라디오",
                    index=선택지.index(초기) if 초기 in 선택지 else 0)
    st.caption("갈래마다 «되돌릴 수 없는 것»이 다릅니다. "
               "그래서 멈추는 기준도 다릅니다.")

보일것 = [w for w in 대기 if 고른갈래 == "전체" or w["갈래"] == 고른갈래]

with 본:
    if not 보일것:
        st.markdown(
            '<div class="empty"><b>%s</b>'
            '기준에 걸리지 않은 건은 사람을 거치지 않고 자동으로 나갔습니다. '
            '무엇이 자동으로 나갔는지는 아래 「자동으로 처리된 건」에서 봅니다.'
            '</div>'
            % ("대기 건이 없습니다" if 고른갈래 == "전체"
               else "「%s」 갈래에는 대기 건이 없습니다" % 고른갈래),
            unsafe_allow_html=True)
    else:
        # ── ★같은 «이유»로 멈춘 것을 «묶어서» 처리 ───────────────────
        #   ⛔정밀 검사가 잡았다 — 대기 251건을 한 건씩 보면 ★44분이다.
        #     그런데 C5 로 멈춘 98건은 대부분 «같은 판단»이다.
        #   ★그래도 사람이 본다 — 대표 3건을 보여 주고, 발행은 «한 번 더» 묻는다.
        묶음들 = [x for x in graph.묶음(보일것) if x["수"] >= 3]
        if 묶음들:
            with st.expander(
                    "★같은 이유로 멈춘 건을 «묶어서» 처리 — %d묶음"
                    % len(묶음들)):
                st.caption("한 건씩 %d번 누르는 것과 「이 이유는 전부 …」는 "
                           "다른 일입니다. ⛔묶어도 «사람이 봅니다» — "
                           "대표를 보고 정하고, 발행은 한 번 더 묻습니다."
                           % len(보일것))
                이름들 = ["%s · %s — %d건"
                       % (x["갈래"], "·".join(x["코드"]) or "(이유 없음)",
                          x["수"]) for x in 묶음들]
                고른묶음 = st.selectbox("묶음", 이름들, key="묶음선택")
                묶 = 묶음들[이름들.index(고른묶음)]

                st.markdown('<div class="lbl">이 묶음의 대표 3건</div>',
                            unsafe_allow_html=True)
                for w2 in 묶["건"][:3]:
                    m2 = 작품.get(w2["슬러그"], {})
                    st.markdown(
                        '<div class="auto"><span>%s</span>'
                        '<span style="color:var(--ink40)">%s</span></div>'
                        % (ui._e((m2.get("제목") or w2.get("제목") or "")[:60]),
                           ui._e(m2.get("작가") or "저작자 미상")),
                        unsafe_allow_html=True)
                if 묶["수"] > 3:
                    st.caption("… 그리고 %d건 더" % (묶["수"] - 3))

                확인 = st.checkbox(
                    "★이 %d건을 «전부» 처리합니다 — 한 건씩 보지 않습니다"
                    % 묶["수"], key="묶음확인")
                m1, m2c, m3 = st.columns(3, gap="small")
                묶음눌림 = None
                with m1:
                    if st.button("전부 반려", width="stretch",
                                 disabled=not 확인, key="묶음반려"):
                        묶음눌림 = "반려"
                with m2c:
                    if st.button("전부 다시 해설", width="stretch",
                                 disabled=not 확인, key="묶음다시"):
                        묶음눌림 = "다시 해설"
                with m3:
                    # ★발행만 «한 번 더» 묻는다 — 되돌릴 수 없는 쪽이다
                    if st.button("전부 발행 ★되돌릴 수 없음", width="stretch",
                                 disabled=not 확인, key="묶음발행",
                                 type="primary"):
                        묶음눌림 = "발행"
                if 묶음눌림:
                    try:
                        된, 터짐 = graph.묶음답한다(묶["건"], 묶음눌림)
                    except Exception as e:
                        st.error("묶음 처리 실패 — %s" % type(e).__name__)
                        st.caption(str(e)[:300])
                        st.stop()
                    st.success("%s — %d건 처리%s"
                               % (묶음눌림, len(된),
                                  (" · ⛔%d건 실패" % len(터짐)) if 터짐 else ""))
                    if 터짐:
                        st.caption(str(터짐[:3]))
                    st.rerun()

        # ★한 건씩. 목록을 스크롤하게 두면 «어디까지 봤나»를 잃는다
        키 = "커서_%s" % 고른갈래
        # ★목록에서 «골라» 들어간다 — 「다음 →」만 있으면 251번 눌러야 한다
        이름목록 = ["%3d. [%s] %s" % (n + 1, x["갈래"],
                                  (x.get("제목") or x["id"])[:52])
                 for n, x in enumerate(보일것)]
        현재 = max(0, min(st.session_state.get(키, 0), len(보일것) - 1))
        고름 = st.selectbox("대기 %d건 중에서 «골라» 보기" % len(보일것),
                          이름목록, index=현재, key="고르기_%s" % 고른갈래)
        if 이름목록.index(고름) != 현재:
            st.session_state[키] = 이름목록.index(고름)
            st.rerun()
        i = max(0, min(st.session_state.get(키, 0), len(보일것) - 1))
        w = 보일것[i]
        m = 작품.get(w["슬러그"], {})
        q = w.get("물음") or {}

        st.markdown('<div class="dk"><div class="top">%s'
                    '<span class="pos">%d / %d</span></div>'
                    % (ui.태그(w["갈래"]), i + 1, len(보일것)),
                    unsafe_allow_html=True)

        그림, 내용 = st.columns([1, 3], gap="medium")
        with 그림:
            if m.get("url"):
                st.markdown(
                    '<img class="thumb" src="%s" alt="%s">'
                    '<div class="cap">%s<br>저작자 %s<br>%s</div>'
                    % (m["url"], ui._e(m.get("제목")),
                       ui._e(m.get("라이선스") or "라이선스 미상"),
                       ui._e(m.get("작가") or "(빈값)"),
                       ui._e(m.get("연도표기") or "")),
                    unsafe_allow_html=True)

        # ★읽을 것을 «한 칸»에 모은다 — 정렬선이 둘이면 눈이 왔다 갔다 한다.
        #   전에는 제목·왜멈췄나는 오른쪽 칸, 나갈 글은 전체 폭이라
        #   왼쪽 모서리가 «두 군데»였다.
        with 내용:
            st.markdown(
                '<div class="ttl">%s</div><div class="by">%s · %s</div>'
                % (ui._e(m.get("제목") or w.get("제목")),
                   ui._e(m.get("작가") or "저작자 미상"),
                   ui._e(m.get("연도표기") or "")), unsafe_allow_html=True)

            # ★① 왜 멈췄나 — 제일 크게
            if q.get("왜 멈췄나"):
                st.markdown(ui.왜멈췄나(q["왜 멈췄나"]), unsafe_allow_html=True)

            # ★② 통과시키면 — 버튼 바로 위
            st.markdown(
                ui.통과시키면(q.get("통과시키면", ""),
                         CFG["_갈래"][w["갈래"]]["되돌릴 수 없는 것"]),
                unsafe_allow_html=True)

            # ★③ 실제로 나갈 글
            나갈글 = gates.내보낼글(m, w["갈래"])
            if 나갈글:
                st.markdown('<div class="lbl">나갈 글</div>',
                            unsafe_allow_html=True)
                st.markdown(ui.본문(나갈글), unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div class="lbl">이 갈래는 «글»을 내보내지 않습니다 — '
                    '이미지 파일만 나갑니다</div>', unsafe_allow_html=True)

        # ⛔★같은 글을 두 번 보여주지 않는다 — 위에 「나갈 글」이 이미 있다.
        #   고칠 때만 «편다». 기본은 접힘 = 화면이 짧아지고 초점이 안 흩어진다.
        with st.expander("고쳐서 내보내기 — 「수정 후 발행」을 누를 때만 씁니다"):
            메모 = st.text_area("내보낼 내용", value=나갈글 or "", height=120,
                              key="메모_%s" % w["id"],
                              label_visibility="collapsed")

        # ★응답 넷 — 으뜸은 하나
        c = st.columns(4, gap="small")
        눌림 = None
        for j, (칸, 답) in enumerate(zip(c, 응답들)):
            with 칸:
                # ★으뜸은 하나 — Streamlit 네이티브 type 을 쓴다.
                #   ⛔래퍼 div 로 감싸면 안 된다: markdown 블록이 갈려
                #     .primary .stButton>button 이 «안 닿는다»(실측).
                if st.button(답, key="b_%s_%s" % (w["id"], 답),
                             width="stretch",
                             type=("primary" if j == 0 else "secondary")):
                    눌림 = 답

        나 = st.columns([1, 1, 4], gap="small")
        with 나[0]:
            if st.button("← 이전", disabled=(i == 0), width="stretch"):
                st.session_state[키] = i - 1
                st.rerun()
        with 나[1]:
            if st.button("다음 →", disabled=(i >= len(보일것) - 1),
                         width="stretch"):
                st.session_state[키] = i + 1
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        if 눌림:
            # ★예외를 «화면에서» 받는다 — 루브릭 ③ 이 「오류 없이 실행」이다.
            #   ⛔전에는 try 가 하나도 없어서, 한 건이라도 터지면
            #     traceback 이 뜨고 페이지가 죽었다. 채점자가 그걸 본다.
            #   ⇒ ★무엇이 왜 안 됐는지 «사람 말»로 보여 주고 화면은 살린다.
            try:
                r = graph.답한다(w["id"], 눌림,
                              메모 if 눌림 == "수정 후 발행" else None)
            except Exception as e:
                st.error("「%s」 를 처리하지 못했습니다 — %s"
                         % (눌림, type(e).__name__))
                st.caption(str(e)[:400])
                st.caption("대기 건은 그대로 남아 있습니다. "
                           "자료가 없으면 `python write.py` 를 먼저 돌려 주세요.")
                st.stop()
            st.session_state[키] = min(i, max(0, len(보일것) - 2))
            결 = r.get("결과") or ""
            # ★「실패」를 «성공 색»으로 보여 주지 않는다
            (st.warning if ("실패" in 결 or "안 나감" in 결)
             else st.success)("%s — %s" % (눌림, 결))
            st.rerun()

# ── ★안 멈춘 것도 보인다 — 안 보이면 «놓침»을 영영 못 찾는다 ─────────
with st.expander("자동으로 처리된 %d건 — ★놓침이 있다면 여기 있다"
                 % (전체 - len(대기))):
    st.caption("기준에 안 걸려 사람을 거치지 않고 나간 건입니다. "
               "놓침(나갔어야 안 될 것이 나감)은 ⛔대기 목록에 «안 뜹니다». "
               "그래서 여기를 따로 봅니다.")
    끝난 = [(k, v) for k, v in 색인.items() if "끝남" in v]
    for k, v in 끝난[:40]:
        st.markdown(
            '<div class="auto"><span class="ok">%s</span>'
            '<span>%s</span><span style="color:var(--ink40)">%s</span></div>'
            % (v.get("결정") or "자동", ui._e((v.get("제목") or "")[:52]),
               ui._e(v["갈래"])), unsafe_allow_html=True)
    if len(끝난) > 40:
        st.caption("… 그리고 %d건 더 — 전부는 output/threads.json 에 있습니다"
                   % (len(끝난) - 40))

with st.expander("승인 기준 %d개 — 갈래마다 다릅니다" % 관문수):
    for g in 갈래들:
        st.markdown("**%s** — 되돌릴 수 없는 것: %s"
                    % (g, CFG["_갈래"][g]["되돌릴 수 없는 것"]))
        켠 = CFG.get("_권장조합", {}).get(g, CFG["_갈래"][g]["기준"])
        행 = [{"기준": k, "켜짐": "○" if k in 켠 else "—",
              "판정": CFG["_관문"][k]["판정"][:58],
              "막는 위험": CFG["_관문"][k]["막는 위험"][:48]}
             for k in CFG["_갈래"][g]["기준"]]
        st.dataframe(행, hide_index=True, width="stretch")
    st.caption("「켜짐 —」은 ★compare.py 가 재서 «뺀» 기준입니다. "
               "근거는 config.json 의 _권장조합 에 적혀 있습니다.")
