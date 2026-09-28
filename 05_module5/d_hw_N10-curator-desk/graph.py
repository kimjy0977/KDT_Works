# -*- coding: utf-8 -*-
"""★HITL 파이프라인 — 멈추고, 기다리고, 이어서 실행한다.

  python graph.py --올린다        대기 건을 만든다 (전 작품 × 네 갈래)
  python graph.py --목록          ★대기 목록 (snapshot.next 로 판정)
  python graph.py --답 <id> 발행  한 건을 이어서 실행
  python graph.py --청소          체크포인트·색인을 지운다

★구조 — 갈래가 넷이어도 그래프는 «하나»다
    START → 준비 → 판정 → [관문] → 실행 → END
                            ↑ interrupt() 는 «걸렸을 때만»

  갈래는 «인자»다. thread_id 에 실어 보낸다 — "슬러그:갈래".
  ⇒ 한 작품이 «이미지»와 «작가»로 동시에 대기할 수 있고, 서로 간섭하지 않는다.

★강의 2강 — 멈춘 «단계»가 처음부터 다시 실행된다
  체크포인트는 「어느 «단계»에서 멈췄나」만 적는다. 몇 번째 «줄»인지는 모른다.
  ⇒ ⛔관문 노드 «안»에서 바깥으로 나가면 재개할 때 두 번 나간다.
    그래서 실행은 ★별도 노드다. 관문은 묻기만 한다.

★강의 4강 — 「승인을 기다리는 시간은 초 단위가 아니다」
  ⇒ SqliteSaver. InMemorySaver 는 껐다 켜면 대기 건이 사라진다.
"""
import argparse
import datetime
import io
import json
import os
import sqlite3
import sys
from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from langgraph.checkpoint.sqlite import SqliteSaver

import gates

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(io.open(os.path.join(HERE, "config.json"), encoding="utf-8"))

# ★.env 를 읽는다 — 키를 여기 두는 것이 이 프로젝트의 규약이다.
#   ⛔"키를 .env 에 넣으세요"라고 문서에 적어 놓고 «안 읽으면»
#     그것도 「말한 것과 하는 것이 다른 것」이다. 실제로 그랬다.
def _env():
    p = os.path.join(HERE, ".env")
    if not os.path.exists(p):
        return
    for line in io.open(p, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


_env()

DB = os.path.join(HERE, CFG["_체크포인터"]["경로"])
색인경로 = os.path.join(HERE, "output/threads.json")
발행로그 = os.path.join(HERE, "output/published.jsonl")
갈래목록 = [k for k in CFG["_갈래"] if not k.startswith("_")]
응답들 = CFG["_응답"]
DRY_RUN = (CFG["_발행"]["DRY_RUN 기본값"]
           and not os.environ.get("DISCORD_WEBHOOK"))
대기한도 = int(CFG["_운영규칙"]["대기 한도(일)"])


class 상태(TypedDict):
    """★상태에는 «가리키는 것»만 담는다 — 실물은 담지 않는다.

    ⛔전에는 작품 레코드(2.3KB)를 통째로 실었다. 체크포인터는 «단계마다»
      상태를 직렬화하므로, thread 하나가 ★179KB 가 되고
      160 thread 에 ★29.4MB 였다.
      노드9 에서 벡터스토어 26MB 가 커밋에 딸려가 .git 이 148→167MB 가 된
      사고(`54ff1e5`)와 «같은 꼴»이다 — 큰 것을 작은 그릇에 담았다.
    ⇒ 슬러그만 싣고, ★준비 노드가 «실제로 준비»한다.
      준비는 부작용이 없어 재실행돼도 같은 결과다(강의 2강).
    """
    슬러그: str
    갈래: str
    제목: Optional[str]
    작가: Optional[str]
    걸린: List[str]
    결정: Optional[str]
    메모: Optional[str]
    결과: Optional[str]
    # ★「다시 해설」 고리용 — 몇 번 다시 썼나, 무엇으로 바뀌었나
    다시횟수: Optional[int]
    다시쓴글: Optional[str]


# ── 작품 창고 — ★상태 밖에 둔다 ──────────────────────────────────

_창고 = None


def 창고(입력=None):
    """슬러그 → 작품. ★한 번 읽어 두고 상태에는 «슬러그»만 싣는다."""
    global _창고
    if _창고 is None or 입력:
        for f in (입력, "data/written_소박.json", "data/written_조심.json",
                  "data/enriched.json"):
            if not f:
                continue
            p = os.path.join(HERE, f)
            if os.path.exists(p):
                d = json.load(io.open(p, encoding="utf-8"))
                _창고 = {m["슬러그"]: m for m in d["작품"]}
                break
        else:
            _창고 = {}
    return _창고


def _작품(s):
    """⛔없으면 «조용히 빈 것»을 주지 않는다 — 판정이 통째로 무너진다."""
    m = 창고().get(s["슬러그"])
    if m is None:
        raise KeyError("작품 «%s» 를 창고에서 못 찾았습니다 — "
                       "python write.py 를 먼저 돌렸습니까?" % s["슬러그"])
    return m


# ── 노드 ────────────────────────────────────────────────────────

def 준비(s: 상태) -> Dict[str, Any]:
    """★슬러그로 작품을 «찾아 온다». ⛔부작용 없음 — 재실행돼도 같은 결과."""
    m = _작품(s)
    return {"제목": m.get("제목"), "작가": m.get("작가")}


def 판정(s: 상태) -> Dict[str, Any]:
    """★관문을 «계산»한다. 여기서 처분하지 않는다 — 목록만 낸다.

    ⛔글을 «여기서» 고르지 않는다. gates.잰다() 가 갈래에 맞게 고른다.
      실사고 2026-09-28 — 여기서 해설+작가소개를 뭉쳐 넘겨
      gates 에서 고친 규칙을 ★무효화했다. 발행 A1 이 4건이어야 하는데 24건이 됐다.
      규칙을 한 군데서 고치면 «그 규칙을 우회하는 자리»가 없는지 본다(§H-4).
    """
    # ★다시 썼으면 «그 글»을 잰다 — 원본을 재면 다시 쓴 보람이 없다
    걸린 = gates.잰다(_작품(s), s["갈래"], 글=s.get("다시쓴글"),
                    카탈로그=_카탈로그())
    return {"걸린": 걸린}


def 관문(s: 상태) -> Dict[str, Any]:
    """★멈추는 자리. 걸린 게 없으면 그냥 지나간다(자동 처리).

    ⛔여기서 바깥으로 나가지 않는다 — 재개하면 이 노드가 «처음부터» 다시 돈다.
      실행은 다음 노드의 몫이다.
    """
    if not s["걸린"]:
        return {"결정": "자동통과", "메모": None}

    m = _작품(s)
    답 = interrupt({
        "갈래": s["갈래"],
        "대상": m.get("제목"),
        "작가": m.get("작가"),
        "왜 멈췄나": gates.이유문(s["걸린"]),
        "통과시키면": _결과문(s["갈래"], m),
        "고를 수 있는 답": 응답들,
    })
    if isinstance(답, dict):
        return {"결정": 답.get("결정"), "메모": 답.get("메모")}
    return {"결정": 답, "메모": None}


def 실행(s: 상태) -> Dict[str, Any]:
    """★바깥으로 나가는 «유일한» 자리. 관문 밖이라 두 번 나가지 않는다."""
    d = s.get("결정")
    if d in ("반려", "포기"):
        return {"결과": "안 나감 — %s" % d}
    m = _작품(s)
    글 = s.get("다시쓴글") or gates.내보낼글(m, s["갈래"]) or m.get("제목") or ""
    if d == "수정 후 발행" and s.get("메모"):
        글 = s["메모"]
    _적는다({
        "시각": datetime.datetime.now().isoformat(timespec="seconds"),
        "슬러그": s["슬러그"], "갈래": s["갈래"], "결정": d,
        "걸린": s["걸린"], "DRY_RUN": DRY_RUN, "내용": 글[:400],
    })
    # ★카탈로그 갈래는 «실제로 등재»한다.
    #   ⛔전에는 「등재됩니다」라고 말만 하고 catalog.json 을 안 썼다.
    #     그래서 D3(중복등재)가 ★영원히 0건이었다 — 전수검사가 잡았다.
    #     「0건」이 «없음»인지 «일어날 수 없음»인지 가른 자리다.
    if s["갈래"] == "카탈로그":
        _등재한다(s["슬러그"], m)
    보낸결과 = _보낸다(s["갈래"], m, 글)
    return {"결과": "%s → %s" % (_결과문(s["갈래"], m), 보낸결과)}


def _보낸다(갈래, m, 글):
    """★바깥으로 «실제로» 보낸다 — 웹훅이 있으면.

    ⛔전에는 이 코드가 «아예 없었다». DRY_RUN=False 여도 아무 데도 안 갔는데
      README·REPORT 는 「DISCORD_WEBHOOK 이 있으면 실제 발행」이라 말했다.
      ★문서가 거짓말을 하고 있었다 — 전수검사가 잡았다.
      「없는 기능을 말하는 것」이 이 프로젝트가 막으려는 바로 그 일이다.
    """
    훅 = os.environ.get("DISCORD_WEBHOOK", "").strip()
    if DRY_RUN or not 훅:
        return "DRY_RUN(output/published.jsonl 에만)"
    몸 = {"content": "**%s** — %s\n%s"
          % (갈래, (m.get("제목") or "")[:120], (글 or "")[:1600])}
    try:
        import urllib.request
        req = urllib.request.Request(
            훅, data=json.dumps(몸).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "User-Agent": "KDT-curator-desk/0.1"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return "Discord 전송 %s" % r.status
    except Exception as e:
        # ⛔조용히 «성공»으로 넘기지 않는다 — 안 나갔으면 안 나갔다고 적는다
        return "★Discord 전송 실패 — %s" % str(e)[:60]


def 재작성(s: 상태) -> Dict[str, Any]:
    """★「다시 해설」을 «진짜로» 다시 쓴다 — 그리고 판정으로 되돌아간다.

    ⛔전에는 「반려」와 «완전히 같았다». 이름만 달랐다.
      응답을 넷으로 둔 근거(강의 4강 — 둘만 두면 「이 문구만 고쳐서」를 전부
      반려하게 되어 자동화가 무너진다)가 ★실제로는 셋이었다.
      전수검사가 잡았다 — 「말한 것」과 「하는 것」이 달랐다.

    ★다시 쓸 때는 «다른 작성기»를 쓴다. 같은 걸로 다시 쓰면 같은 글이 나온다.
      소박 → 조심. 정밀도를 지켜 쓰므로 D4·A1 이 줄어든다.
    ⛔무한히 돌지 않는다 — 다시판정 상한(config)을 넘으면 포기하고 안 내보낸다.
    """
    import write
    m = _작품(s)
    n = (s.get("다시횟수") or 0) + 1
    상한 = int(CFG["_운영규칙"]["다시판정 상한"])
    if n > 상한:
        return {"다시횟수": n, "결정": "포기",
                "결과": "안 나감 — 다시 쓰기가 상한(%d)을 넘었습니다" % 상한}
    새글 = (write.작가소개_조심(m) if s["갈래"] == "작가"
          else write.해설_조심(m))
    return {"다시횟수": n, "다시쓴글": 새글, "결정": None, "걸린": []}


def _결과문(갈래, m):
    """★「통과시키면 무슨 일이 일어나나」 — 강의 1강이 짚은 그 문장."""
    t = m.get("제목") or "이 건"
    return {
        "발행": "#큐레이터-데스크 에 「%s」 해설 카드가 올라갑니다" % t,
        "이미지": "「%s」 썸네일이 내려받아져 재배포됩니다" % t,
        "작가": "「%s」 작가 소개가 게시됩니다" % (m.get("작가") or "작자 미상"),
        "카탈로그": "catalog.json 에 「%s」 가 등재되고 ★다음 주 큐레이션이 "
                 "이 값을 씁니다" % t,
        "정정": "이미 나간 카드가 수정·삭제됩니다 — ★읽은 사람이 있습니다",
    }.get(갈래, "바깥으로 나갑니다")


def _적는다(rec):
    os.makedirs(os.path.dirname(발행로그), exist_ok=True)
    with io.open(발행로그, "a", encoding="utf-8", newline="") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


카탈로그경로 = os.path.join(HERE, "output/catalog.json")


def _카탈로그():
    if not os.path.exists(카탈로그경로):
        return set()
    return set(json.load(io.open(카탈로그경로, encoding="utf-8"))
               .get("슬러그", []))


def _등재한다(슬러그, m):
    """★카탈로그에 «실제로» 올린다 — 이게 없으면 D3 가 죽은 기준이 된다.

    카탈로그는 ★다음 주 큐레이션이 «읽는» 것이다.
    그래서 이 갈래의 되돌릴 수 없는 것이 「고착」이다.
    """
    d = {"슬러그": [], "항목": {}}
    if os.path.exists(카탈로그경로):
        d = json.load(io.open(카탈로그경로, encoding="utf-8"))
    if 슬러그 not in d["슬러그"]:
        d["슬러그"].append(슬러그)
    d["항목"][슬러그] = {
        "제목": m.get("제목"), "작가": m.get("작가"),
        # ★연도는 «표기»를 쓴다 — 값만 쓰면 없는 정밀도를 만든다(D4)
        "연도": m.get("연도표기"),
        "라이선스": m.get("라이선스"),
        "등재": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    os.makedirs(os.path.dirname(카탈로그경로), exist_ok=True)
    io.open(카탈로그경로, "w", encoding="utf-8", newline="").write(
        json.dumps(d, ensure_ascii=False, indent=1))


# ── 그래프 · 체크포인터 ──────────────────────────────────────────

_앱 = None


def 만든다():
    """★compile 은 한 번만. sqlite 연결을 열어 둔 채 쓴다.

    ⛔`with SqliteSaver.from_conn_string(...)` 를 쓰면 블록을 나갈 때 연결이 닫혀
      Streamlit 처럼 «오래 사는» 프로세스에서 다음 요청이 죽는다.
    """
    global _앱
    if _앱 is not None:
        return _앱
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    conn = sqlite3.connect(DB, check_same_thread=False)
    g = StateGraph(상태)
    g.add_node("준비", 준비)
    g.add_node("판정", 판정)
    g.add_node("관문", 관문)
    g.add_node("재작성", 재작성)
    g.add_node("실행", 실행)
    g.add_edge(START, "준비")
    g.add_edge("준비", "판정")
    g.add_edge("판정", "관문")
    # ★「다시 해설」은 «되돌아간다» — 실행으로 안 간다.
    #   ⛔전에는 관문 → 실행 하나뿐이라 「다시 해설」이 반려와 같았다.
    g.add_conditional_edges(
        "관문",
        lambda s: "재작성" if s.get("결정") == "다시 해설" else "실행",
        {"재작성": "재작성", "실행": "실행"})
    # 재작성 → 판정 → 관문 … 고리. 상한은 재작성 안에서 건다.
    g.add_conditional_edges(
        "재작성",
        lambda s: "실행" if s.get("결정") == "포기" else "판정",
        {"실행": "실행", "판정": "판정"})
    g.add_edge("실행", END)
    _앱 = g.compile(checkpointer=SqliteSaver(conn))
    return _앱


def _cfg(tid):
    return {"configurable": {"thread_id": tid}}


# ── 색인 — 어떤 thread 를 만들었나 ────────────────────────────────

def 색인읽기():
    if not os.path.exists(색인경로):
        return {}
    return json.load(io.open(색인경로, encoding="utf-8"))


def 색인쓰기(d):
    os.makedirs(os.path.dirname(색인경로), exist_ok=True)
    io.open(색인경로, "w", encoding="utf-8", newline="").write(
        json.dumps(d, ensure_ascii=False, indent=1))


# ── 바깥에서 쓰는 세 가지 ────────────────────────────────────────

def 올린다(작품들, 갈래들=None):
    """작품 × 갈래로 thread 를 만들어 «관문까지» 굴린다.

    ★상태에는 «슬러그»만 싣는다 — 작품 실물은 창고에 있다.
      체크포인터가 단계마다 상태를 직렬화하므로, 실물을 실으면 DB 가 커진다.
    """
    app = 만든다()
    창고()                                  # 먼저 읽어 둔다
    갈래들 = 갈래들 or [g for g in 갈래목록 if g != "정정"]
    색인 = 색인읽기()
    멈춤 = 자동 = 0
    for m in 작품들:
        for 갈래 in 갈래들:
            tid = "%s:%s" % (m["슬러그"], 갈래)
            r = app.invoke({"슬러그": m["슬러그"], "갈래": 갈래,
                            "제목": None, "작가": None,
                            "걸린": [], "결정": None, "메모": None,
                            "결과": None}, _cfg(tid))
            대기 = bool(app.get_state(_cfg(tid)).next)
            색인[tid] = {
                "슬러그": m["슬러그"], "갈래": 갈래,
                "제목": m.get("제목"), "작가": m.get("작가"),
                "올린때": datetime.datetime.now().isoformat(timespec="seconds"),
            }
            if 대기:
                멈춤 += 1
            else:
                자동 += 1
                색인[tid]["끝남"] = r.get("결과")
    색인쓰기(색인)
    return 멈춤, 자동


def 대기목록():
    """★판정은 «snapshot.next» 가 한다 — 비어 있지 않으면 대기 중.

    ⛔색인 파일이 «대기 여부»의 근거가 아니다. 색인은 「어떤 thread 가 있나」만 안다.
      실제 상태는 체크포인터에 있다.
    """
    app = 만든다()
    out = []
    for tid, meta in 색인읽기().items():
        st = app.get_state(_cfg(tid))
        if not st.next:
            continue
        iv = None
        try:
            t = st.tasks[0] if st.tasks else None
            if t and getattr(t, "interrupts", None):
                iv = t.interrupts[0].value
        except Exception:
            iv = None
        out.append({"id": tid, **meta, "다음단계": list(st.next),
                    "물음": iv, "경과일": _경과일(meta.get("올린때"))})
    out.sort(key=lambda x: (x["갈래"], x["id"]))
    return out


def _경과일(iso):
    if not iso:
        return 0
    try:
        t = datetime.datetime.fromisoformat(iso)
    except Exception:
        return 0
    return (datetime.datetime.now() - t).days


def 답한다(tid, 결정, 메모=None):
    """★Command(resume=) 로 이어 간다. 멈춘 «단계»부터 다시 돈다."""
    app = 만든다()
    r = app.invoke(Command(resume={"결정": 결정, "메모": 메모}), _cfg(tid))
    색인 = 색인읽기()
    if tid in 색인:
        색인[tid]["끝남"] = r.get("결과")
        색인[tid]["결정"] = 결정
        색인[tid]["답한때"] = datetime.datetime.now().isoformat(
            timespec="seconds")
        색인쓰기(색인)
    return r


def 묵은건반려(한도=None):
    """대기 N일 경과 → ★자동 반려. 기본값을 «안 내보내기» 쪽으로.

    ⛔전에는 이 함수를 «아무도 안 불렀다». config 에 규칙을 적고 함수도
      만들어 놓고 호출부가 없어 ★죽은 기능이었다 — 전수검사가 잡았다.
      `--묵은것` 으로 부르고, 화면에서도 부른다.
    """
    한도 = 한도 if 한도 is not None else 대기한도
    친 = []
    for w in 대기목록():
        if w["경과일"] >= 한도:
            답한다(w["id"], "반려", "대기 %d일 경과 — 자동 반려" % w["경과일"])
            친.append((w["id"], w["경과일"]))
    return 친


# ── CLI ────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--올린다", action="store_true")
    ap.add_argument("--목록", action="store_true")
    ap.add_argument("--답", nargs=2, metavar=("THREAD", "결정"))
    ap.add_argument("--청소", action="store_true")
    ap.add_argument("--묵은것", action="store_true",
                    help="★대기 N일 경과 건을 자동 반려한다 (config _운영규칙)")
    ap.add_argument("--입력", default="data/written_소박.json")
    ap.add_argument("--n", type=int, default=0)
    a = ap.parse_args()

    if a.청소:
        잠김 = []
        for p in (DB, 색인경로, 발행로그,
                  os.path.join(HERE, "output/catalog.json")):
            if not os.path.exists(p):
                continue
            try:
                os.remove(p)
                print("  지움  %s" % os.path.relpath(p, HERE))
            except PermissionError:
                # ⛔★조용히 죽지 않는다 — «무엇이» 잡고 있는지 말해 준다.
                #   streamlit 이 떠 있으면 checkpoints.sqlite 를 쥐고 있다.
                #   전에는 여기서 트레이스백만 나서 「코드가 깨졌나」로 읽혔다.
                잠김.append(os.path.relpath(p, HERE))
        if 잠김:
            print()
            print("  ⚠다른 프로세스가 쥐고 있어 못 지웠습니다: %s"
                  % " · ".join(잠김))
            print("    streamlit 이 떠 있으면 먼저 끄세요 (Ctrl+C).")
            print("    ★지우지 못해도 --올린다 는 «이어서» 씁니다 — "
                  "같은 thread_id 는 덮어씁니다.")
            return 2                      # 0 도 1 도 아니다 — «부분 성공»
        return 0

    if a.올린다:
        p = os.path.join(HERE, a.입력)
        if not os.path.exists(p):
            print("  ⛔%s 가 없습니다. python write.py 먼저" % a.입력)
            return 1
        작품 = json.load(io.open(p, encoding="utf-8"))["작품"]
        if a.n:
            작품 = 작품[: a.n]
        멈춤, 자동 = 올린다(작품)
        전체 = 멈춤 + 자동
        print("═══ 올림 — 작품 %d × 갈래 4 = %d건 ═══" % (len(작품), 전체))
        print()
        print("  ★멈춰서 대기   %3d건  (%4.1f%%)" % (멈춤, 멈춤 / max(1, 전체) * 100))
        print("  자동 처리      %3d건  (%4.1f%%)" % (자동, 자동 / max(1, 전체) * 100))
        print()
        print("  체크포인터 %s → %s"
              % (CFG["_체크포인터"]["쓸 것"], CFG["_체크포인터"]["경로"]))
        print("  ⛔DRY_RUN=%s — 실제 발행은 DISCORD_WEBHOOK 이 있을 때만"
              % DRY_RUN)
        return 0

    if a.묵은것:
        친 = 묵은건반려()
        print("═══ 묵은 건 자동 반려 — 한도 %d일 ═══" % 대기한도)
        print()
        if not 친:
            print("  한도를 넘은 건이 없습니다.")
            print("  ⛔「0건」은 «규칙이 없다»가 아닙니다 — 오늘 올린 것이라 "
                  "아직 0일입니다.")
        for tid, 일 in 친:
            print("  반려  %-52s %d일" % (tid, 일))
        print()
        print("  왜 — %s" % CFG["_운영규칙"]["왜"])
        return 0

    if a.목록:
        w = 대기목록()
        print("═══ 승인 대기 %d건 — ★판정은 snapshot.next ═══" % len(w))
        print()
        갈 = {}
        for x in w:
            갈[x["갈래"]] = 갈.get(x["갈래"], 0) + 1
        for k, v in sorted(갈.items()):
            print("  %-8s %3d건" % (k, v))
        print()
        for x in w[:14]:
            이유 = "·".join(c for c, _, _ in
                          gates.이유문(x["물음"] and [] or [])) if False else ""
            코드 = ""
            if x["물음"]:
                코드 = "·".join(c for c, _, _ in x["물음"]["왜 멈췄나"])
            print("  [%-6s] %-34s %-14s next=%s"
                  % (x["갈래"], (x.get("제목") or "")[:32], 코드,
                     ",".join(x["다음단계"])))
        if len(w) > 14:
            print("  … 그리고 %d건 더" % (len(w) - 14))
        return 0

    if a.답:
        tid, 결정 = a.답
        if 결정 not in 응답들:
            print("  ⛔결정은 %s 중 하나" % " / ".join(응답들))
            return 1
        r = 답한다(tid, 결정)
        print("  %s → %s" % (tid, r.get("결과")))
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
