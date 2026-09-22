# -*- coding: utf-8 -*-
"""딥리서치 에이전트 — 코디네이터 1 + 서브에이전트 N (LangGraph)

여섯 노드 (강의 노드8 구조를 그대로)
    ① plan       기획   — 카드를 보고 목차를 짜고 절마다 역할·시작문서를 배정
    ② dispatch   배치   — Send 로 팬아웃. 각자에게 «남의 구역»을 들려 보낸다
    ③ researcher 조사   — ★노드 «안»에 루프가 있다. 읽고 → 다음 후보 고르고 → 원고
    ④ review     점검   — 자기신고를 모아 빈 칸을 찾고 재위임. LLM 호출 0회
    ⑤ compose    종합   — 절을 이어 붙이고 머리말·맺음말
    ⑥ evaluate   평가   — ★정답표 없이 잰다 (metrics.py)

★이 구조의 요점 — 「구조가 «질문이 도착한 뒤»에 정해진다」
    라우팅   코드 짤 때 굳는다
    GraphRAG 인덱싱할 때 굳는다
    여기     ★질문이 온 뒤에 굳는다 — 목차·인원·배정이 질문마다 다르다
    늦게 정할수록 질문에 잘 맞고, 늦게 정할수록 비싸다.

★컨텍스트 격리 — 원문은 read_one() «안»에서 끝난다.
    코퍼스 463,673자(≈232k 토큰) > 창 128k. 격리가 없으면 상한이 창 하나다.
    격리하면 상한이 «조사관 수»만큼 곱해진다.
"""
import io
import json
import operator
import os
import re
import time
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from openai import OpenAI

HERE = os.path.dirname(os.path.abspath(__file__))

# ── 설정 — ★섹션 15의 절제 실험이 이 손잡이를 하나씩 끈다 ──────────────
설정 = {
    "절수": 4,          # 폭 — 6강 ④ 「4절 × 3건」
    "예산": 3,          # 깊이 (한 «바퀴»에 새로 읽을 건수)
    "최대바퀴": 2,      # ★예산 기준 종료 조건 (내용 기준과 «이중»으로 건다)
    "카드": 250,        # 4강 ② 「제목 + 앞 250자」 — 코퍼스의 약 1.7%
    "배정": True,       # 코디네이터가 시작 문서를 정해 준다
    "구역": True,       # 7강 — 남의 구역을 알려 줘 중복을 막는다
    "역할": True,       # 5강 — 「시간순 담당」 같은 이름이 프롬프트 첫 줄이 된다
    "재위임": True,     # 10·11강 — 자기신고로 루프를 연다
    "모델": "gpt-4o-mini",
}

# ★명단 — 역할은 «프롬프트 한 줄»이지 별도의 코드가 아니다.
#   같은 문서를 읽어도 시간순 담당은 날짜를, 인물 담당은 사람을 뽑는다.
ROSTER = ["시간순 담당", "인물 담당", "원인·배경 담당", "결과·영향 담당",
          "큰그림 담당", "쟁점 담당"]

_usage = {"in": 0, "out": 0, "calls": 0}
_client = None


def client():
    global _client
    if _client is None:
        p = os.path.join(HERE, ".env")
        if os.path.exists(p):
            for line in io.open(p, encoding="utf-8"):
                if line.strip().startswith("OPENAI_API_KEY"):
                    os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()
        # ★설정이 잘못됐으면 «쓰기 전에» 죽는 편이 낫다 (5강).
        #   키 없이 여덟 단계를 지나가 엉뚱한 노드가 범인으로 지목되는 것보다.
        k = os.environ.get("OPENAI_API_KEY", "")
        assert k.startswith("sk-"), "★OPENAI_API_KEY 를 못 찾았습니다 (.env 확인)"
        _client = OpenAI()
    return _client


def ask(prompt, system="", max_tokens=1200):
    m = ([{"role": "system", "content": system}] if system else []) + \
        [{"role": "user", "content": prompt}]
    r = client().chat.completions.create(
        model=설정["모델"], messages=m, temperature=0, max_tokens=max_tokens)
    _usage["in"] += r.usage.prompt_tokens
    _usage["out"] += r.usage.completion_tokens
    _usage["calls"] += 1
    return r.choices[0].message.content or ""


# ── 코퍼스 ───────────────────────────────────────────────────────────
_C = json.load(io.open(os.path.join(HERE, "data/corpus.json"), encoding="utf-8"))
DOCS, LINKS = _C["docs"], _C["links"]


def cards():
    """4강 ② — 제목 + 앞 250자. 코퍼스 전체의 약 1.7%."""
    n = 설정["카드"]
    return "\n".join("- %s: %s" % (t, DOCS[t][:n].replace("\n", " "))
                     for t in sorted(DOCS))


class S(TypedDict, total=False):
    question: str
    toc: list
    # ★리듀서 — 조사관 넷이 «동시에» 같은 칸에 쓴다.
    #   없으면 마지막에 끝난 조사관 것만 남고 나머지는 사라진다.
    sections: Annotated[list, operator.add]
    visited: Annotated[list, operator.add]
    log: Annotated[list, operator.add]
    wheel: int
    report: str
    metrics: dict
    종료: str


# ── ① 기획 ───────────────────────────────────────────────────────────
def plan(st: S) -> S:
    n = 설정["절수"]
    roster = ROSTER[:n] if 설정["역할"] else ["담당"] * n
    p = ("다음은 한국 근대사 문서 %d건의 «제목 + 앞부분»입니다.\n\n%s\n\n"
         "질문: %s\n\n"
         "이 질문에 답하는 장문 보고서의 목차를 %d개 절로 짜세요.\n"
         "★목차는 반드시 «내용 단위»로 나누세요. "
         "'개요·연표·인물·결론' 같은 형식 단위로 나누면 조사관들이 같은 문서를 "
         "중복해서 읽습니다.\n"
         "절마다 ①제목 ②그 절을 쓸 사람에게 줄 지시 ③역할(%s 중 하나) "
         "④시작문서(위 목록에 «있는» 제목 하나, 절끼리 겹치지 않게)를 정하세요.\n\n"
         'JSON 만: {"목차":[{"절":"","지시":"","역할":"","시작문서":""}]}'
         % (len(DOCS), cards(), st["question"], n, "·".join(roster)))
    raw = ask(p, "너는 리서치 팀의 코디네이터다. JSON 만 출력한다.", 1500)

    # ★코드가 «형식»을 한 번 더 검사한다 — 모델은 없는 제목을 자연스럽게 지어낸다.
    #   「조일수호조규 속약」처럼 있을 법한 이름을 만들면 사람 눈으로는 안 걸리고,
    #   그대로 DOCS[제목] 에 들어가 KeyError 로 터진다.
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        toc = json.loads(m.group(0))["목차"] if m else []
    except Exception:
        toc = []
    titles = sorted(DOCS)
    used, out = set(), []
    for i, t in enumerate(toc[:n]):
        절 = (t.get("절") or "%d절" % (i + 1)).strip()
        역할 = t.get("역할") if t.get("역할") in roster else roster[i % len(roster)]
        시작 = t.get("시작문서")
        if not 설정["배정"] or 시작 not in DOCS or 시작 in used:
            # 겹치거나 목록에 없으면 코드가 «다른 것»으로 바꿔 준다
            시작 = next((x for x in titles if x not in used), titles[i % len(titles)])
        used.add(시작)
        out.append({"절": 절, "지시": (t.get("지시") or 절).strip(),
                    "역할": 역할, "시작문서": 시작 if 설정["배정"] else None,
                    "예산": 설정["예산"], "번호": i})
    while len(out) < n:          # 모델이 모자라게 줬을 때의 «물러날 자리»
        i = len(out)
        시작 = next((x for x in titles if x not in used), titles[i])
        used.add(시작)
        out.append({"절": "%d절" % (i + 1), "지시": st["question"],
                    "역할": roster[i % len(roster)], "시작문서": 시작,
                    "예산": 설정["예산"], "번호": i})
    return {"toc": out, "wheel": 0,
            "log": ["① 기획  목차 %d절 · 배정 %s"
                    % (len(out), " / ".join(x["시작문서"] or "-" for x in out))]}


# ── ② 배치 ───────────────────────────────────────────────────────────
def fanout(st: S):
    """★Send 리스트의 «길이»가 인원이다. 그 길이는 plan 이 정한다."""
    idxs = st.get("_배차") or list(range(len(st["toc"])))
    if not idxs:
        return "review"                      # 보낼 절이 없으면 그냥 통과
    done = {s["절"]: s for s in st.get("sections", [])}
    sends = []
    for i in idxs:
        t = dict(st["toc"][i])
        남의구역 = set()
        if 설정["구역"]:
            남의구역 = {x["시작문서"] for j, x in enumerate(st["toc"])
                      if j != i and x["시작문서"]}
            남의구역 |= set(st.get("visited", []))   # 이미 읽힌 것도 피한다
            남의구역.discard(t["시작문서"])
        t["피하기"] = sorted(남의구역)
        sends.append(Send("researcher",
                          {"question": st["question"], "task": t,
                           "prior": done.get(t["절"], {})}))
    return sends


def dispatch(st: S) -> S:
    idxs = st.get("_배차") or list(range(len(st["toc"])))
    return {"log": ["② 배치  %d바퀴 · 서브에이전트 %d명 동시 파견"
                    % (st.get("wheel", 0) + 1, len(idxs))]}


# ── ③ 조사관 — ★노드 «안»에 에이전트가 하나 들어 있다 ─────────────────
def read_one(title, question, 지시):
    """★격리의 경계선 — 이 함수 «안»으로 원문 만 자가 들어가고
       밖으로 몇백 자가 나온다. 원문은 이 함수 밖으로 나가지 않는다."""
    body = DOCS[title][:12000]
    p = ("질문: %s\n지시: %s\n\n문서 «%s»:\n%s\n\n"
         "이 문서에서 «질문·지시에 쓸 수 있는 것»만 여섯 문장 이내로 요약하세요.\n"
         "★쓸 것이 없으면 «관련 없음» 이라고만 답하세요. "
         "어설프게 요약하느니 빈손이 낫습니다."
         % (question, 지시, title, body))
    return ask(p, "너는 자료를 읽고 요약하는 조사관이다.", 500)


def 후보목록(read, 피하기):
    """읽은 문서의 «링크»가 다음 후보다 — 읽기 전에는 이 목록이 없었다.
    ★막히면 두 겹으로 물러난다: 링크 → 전체 → 구역 해제."""
    c = [x for t in read for x in LINKS.get(t, [])
         if x not in read and x not in 피하기]
    if not c:
        c = [x for x in DOCS if x not in read and x not in 피하기]
    if not c:
        c = [x for x in DOCS if x not in read]      # 구역까지 푼다
    return sorted(set(c))


def researcher(st) -> S:
    t, question = st["task"], st["question"]
    prior = st.get("prior") or {}
    read = list(prior.get("읽음", []))
    memo = list(prior.get("메모", []))
    피하기 = set(t.get("피하기") or [])

    for _ in range(t["예산"]):           # ★상한은 «코드»다 — 모델이 못 어긴다
        nxt = None
        if t["시작문서"] and t["시작문서"] not in read:
            nxt = t["시작문서"]
        else:
            c = 후보목록(read, 피하기)
            if not c:
                break
            pick = ask("질문: %s\n지시: %s\n\n후보:\n%s\n\n"
                       "가장 도움이 될 문서 «제목 하나»만 그대로 출력."
                       % (question, t["지시"], "\n".join("- " + x for x in c[:40])),
                       "제목 하나만 출력한다.", 40).strip().strip("«»\"' ")
            # ★고른 것이 이미 읽은 것이면 «멈추지 말고» 다음 후보를 집는다.
            #   전에는 아래에서 break 했더니 예산 3건인데 1건만 읽고 끝났다.
            nxt = pick if (pick in DOCS and pick not in read) else c[0]
        if nxt in read:
            continue
        s = read_one(nxt, question, t["지시"])
        read.append(nxt)
        if "관련 없음" not in s[:20]:
            memo.append("«%s» %s" % (nxt, s))

    역할 = t["역할"] if 설정["역할"] else "담당"
    # ★쓸 수 있는 «실제 제목»을 목록으로 준다.
    #   전에는 "«문서명» 을 붙이세요"라고만 써서 한 조사관이 문장 끝에
    #   리터럴 「문서명」을 적어 올렸고, 나머지는 꺾쇠를 안 붙여 근거율 0.0% 였다.
    출처들 = [x for x in read if any(("«%s»" % x) in mm for mm in memo)] or read
    p = ("너는 «%s»다.\n질문: %s\n맡은 절: %s\n지시: %s\n\n"
         "읽은 메모:\n%s\n\n"
         "이 메모«만»으로 절 원고를 여섯~열두 문장으로 쓰세요.\n"
         "\n★인용 규칙 (반드시 지킬 것)\n"
         "  쓸 수 있는 출처는 아래 %d개뿐입니다 — %s\n"
         "  근거가 있는 문장은 «끝에» 그 출처 제목을 꺾쇠에 넣어 붙입니다.\n"
         "  ★한 문장에 하나씩, 자료에서 온 문장 «대부분»에 붙이세요 — 한 절에 한 번만 붙이면 안 됩니다.\n"
         "  예) 농민군은 부패 척결을 요구하였다 «%s».\n"
         "  ⛔«문서명» 이라고 «그 글자 그대로» 쓰지 마세요.\n"
         "메모에 없는 것은 쓰지 마세요.\n\n"
         'JSON 만: {"원고":"", "충분":true/false, "부족":"무엇이 비었는지 한 문장"}'
         % (역할, question, t["절"], t["지시"],
            "\n\n".join(memo) if memo else "(없음)",
            len(출처들), " / ".join("«%s»" % x for x in 출처들),
            출처들[0] if 출처들 else "문서 제목"))
    raw = ask(p, "너는 서브에이전트다. JSON 만 출력한다.", 1600)
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        d = json.loads(m.group(0)) if m else {}
    except Exception:
        d = {}
    원고 = (d.get("원고") or "").strip() or "(원고 없음)"
    인용 = [x for x in re.findall(r"«([^»]+)»", 원고) if x != "문서명"]
    # ★자기가 «안 읽은» 문서를 인용했는지 — 모델 판정이 아니라 «집합 연산»
    허위 = [c for c in set(인용) if c not in read]

    sec = {"절": t["절"], "번호": t["번호"], "역할": 역할, "원고": 원고,
           "읽음": read, "메모": memo, "인용": 인용, "허위인용": 허위,
           "충분": bool(d.get("충분", True)), "부족": (d.get("부족") or "").strip(),
           "바퀴": st.get("wheel", 0)}
    return {"sections": [sec], "visited": read,
            "log": ["   ③ 조사관 «%s»(%s) %d건 읽고 %d자 · 인용 %d곳%s"
                    % (t["절"], 역할, len(read), len(원고), len(set(인용)),
                       " · ★허위 %d" % len(허위) if 허위 else "")]}


# ── ④ 점검 — LLM 호출 0회. 하는 일은 «판단»이 아니라 «집계와 배차» ──────
def review(st: S) -> S:
    # 리듀서가 계속 덧붙이므로 재위임된 절은 두 벌 쌓인다 → 마지막 것만
    latest = {}
    for s in sorted(st.get("sections", []), key=lambda x: x.get("바퀴", 0)):
        latest[s["절"]] = s
    빈칸 = [s for s in latest.values() if not s["충분"]]
    wheel = st.get("wheel", 0) + 1

    # ★종료 «이중» 통제 — 예산 기준을 «바깥»에, 내용 기준을 «안»에.
    #   모델의 판단만으로는 안 멈춘다. 예산만으로 멈추면 늘 최대치를 태운다.
    if not 설정["재위임"] or wheel >= 설정["최대바퀴"] or not 빈칸:
        why = ("재위임 꺼짐" if not 설정["재위임"]
               else "바퀴 소진" if wheel >= 설정["최대바퀴"] else "빈 칸 없음")
        return {"wheel": wheel, "_배차": [], "종료": why,
                "log": ["④ 점검  %d절 중 빈 칸 %d개 · 종료(%s)"
                        % (len(latest), len(빈칸), why)]}

    toc = [dict(x) for x in st["toc"]]
    배차 = []
    for s in 빈칸:
        i = s["번호"]
        배차.append(i)
        # ★«겨냥» — 이 문장이 없으면 2바퀴가 1바퀴와 같은 선택을 한다
        toc[i]["지시"] = ("%s (재위임: 지난번에 %s 를 읽었지만 %s. "
                          "그쪽을 겨냥해 새 문서를 읽어라.)"
                          % (st["toc"][i]["지시"],
                             " / ".join("«%s»" % x for x in s["읽음"]),
                             s["부족"] or "근거가 모자랐다"))
        toc[i]["시작문서"] = None          # 배정은 1바퀴만. 이제 스스로 고른다
    return {"wheel": wheel, "toc": toc, "_배차": 배차, "종료": "",
            "log": ["④ 점검  %d절 중 빈 칸 %d개 → %d명 재위임"
                    % (len(latest), len(빈칸), len(배차))]}


def route(st: S):
    return "dispatch" if st.get("_배차") else "compose"


# ── ⑤ 종합 ───────────────────────────────────────────────────────────
def compose(st: S) -> S:
    latest = {}
    for s in sorted(st.get("sections", []), key=lambda x: x.get("바퀴", 0)):
        latest[s["절"]] = s
    secs = sorted(latest.values(), key=lambda x: x["번호"])
    본문 = "\n\n".join("## %s\n\n%s" % (s["절"], s["원고"]) for s in secs)
    p = ("질문: %s\n\n아래는 조사관들이 쓴 절 원고입니다.\n\n%s\n\n"
         "이 보고서의 ①제목 한 줄 ②머리말 3~4문장 ③맺음말 3~4문장을 쓰세요.\n"
         "★절 원고는 고치지 마세요. 없는 사실을 새로 쓰지 마세요.\n\n"
         'JSON 만: {"제목":"", "머리말":"", "맺음말":""}'
         % (st["question"], 본문))
    raw = ask(p, "너는 편집자다. JSON 만 출력한다.", 900)
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        d = json.loads(m.group(0)) if m else {}
    except Exception:
        d = {}
    report = "# %s\n\n%s\n\n%s\n\n## 맺음말\n\n%s" % (
        d.get("제목") or st["question"], d.get("머리말") or "", 본문,
        d.get("맺음말") or "")
    return {"report": report,
            "log": ["⑤ 종합  %d절 → 보고서 %d자" % (len(secs), len(report))]}


# ── ⑥ 평가 ───────────────────────────────────────────────────────────
def evaluate(st: S) -> S:
    from metrics import score
    m = score(st)
    return {"metrics": m,
            "log": ["⑥ 평가  근거율 %.1f%% · 허위인용 %d · 읽고안쓴 %d건 "
                    "· 편중 %.1f%% · 중복률 %.1f%%"
                    % (m["근거율"] * 100, m["허위인용"], len(m["읽고안쓴"]),
                       m["편중"] * 100, m["중복률"] * 100)]}


def build():
    g = StateGraph(S)
    for name in ("plan", "dispatch", "researcher", "review", "compose", "evaluate"):
        g.add_node(name, globals()[name])
    g.add_edge(START, "plan")
    g.add_conditional_edges("plan", lambda s: "dispatch", ["dispatch"])
    # ★갈림길의 «도착 가능한 곳»을 리스트로 준다 — 몇 명 갈지가 아니다
    g.add_conditional_edges("dispatch", fanout, ["researcher", "review"])
    g.add_edge("researcher", "review")
    g.add_conditional_edges("review", route, ["dispatch", "compose"])
    g.add_edge("compose", "evaluate")
    g.add_edge("evaluate", END)
    return g.compile()


def run(question, quiet=False):
    _usage.update({"in": 0, "out": 0, "calls": 0})
    t0 = time.time()
    st = build().invoke({"question": question, "sections": [], "visited": [],
                         "log": [], "wheel": 0},
                        {"recursion_limit": 60})
    st["usage"] = dict(_usage)
    st["sec"] = round(time.time() - t0, 2)
    if not quiet:
        print("\n".join(st["log"]))
        print("\n   호출 %d회 · 입력 %d토큰 · 출력 %d토큰 · %.1f초"
              % (_usage["calls"], _usage["in"], _usage["out"], st["sec"]))
    return st
