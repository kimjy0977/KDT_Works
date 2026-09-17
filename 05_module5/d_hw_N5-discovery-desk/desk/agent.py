# -*- coding: utf-8 -*-
"""★파이프라인 — 판정 → 근거 조립 → 답변 → 검증을 «하나의 흐름»으로.

요건(노드5) 구조도를 그대로 옮긴 것:
```
    입력 하나  →  ① 카테고리 판정  →  ② 카테고리별 근거 조립  →  ③ 근거만으로 답변  →  ④ 검증
                        ↓
                  모르겠으면 넘기기
```

LangGraph 노드·상태 흐름
```
    START → classify → gate ──(넘김)──────────────────────────→ finish → END
                        │
                     (계속)
                        ↓
                    retrieve → gate2 ──(근거 없음)────────────→ finish
                        │
                     (계속)
                        ↓
                     compose → verify → finish → END
```

★어제(노드4)에서 가져온 것
  · 2단계 분리 — 도구 «선택»과 답변 «작성»을 나눈다
  · MAX_TOOL_TURNS = 5
  · 카테고리별 근거만 넣는다 (7,227자에서 도구 호출을 잃었다)

★노드5 요건이 새로 요구한 것
  · 「카테고리를 고르는 일과, 확신이 없을 때 넘기는 판단을 «분리»한다」 → escalate.py
  · 「근거 문서 전체가 아니라 카테고리별로 필요한 부분만」        → context_desk.py

  python agent.py --ask "공룡은 언제 멸종했나요"
  python agent.py --ask "2026년 노벨 물리학상 수상자는 누구인가요"   # 넘기기
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Annotated, TypedDict

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent

MAX_TOOL_TURNS = 5          # ★설정값 한 줄이 프롬프트 여러 줄보다 셌다


class DeskState(TypedDict, total=False):
    question: str
    history: list          # ★[(질문, 답변), ...] — 멀티턴. 평가에서는 비운다
    route: str
    conf: float
    decision: str
    reason: str
    context: str
    used: dict
    answer: str
    guard: dict


PICK_GUIDE_V2 = """너는 과학 질문 데스크의 조회 담당이다. 답하려면 무엇을 조회해야 하는지 판단해
필요한 도구를 «전부» 부른다. 답변 문장은 쓰지 않는다.

- 널리 알려진 사실·용어·연대를 묻는다 → get_fact 또는 get_term
- 「최근」·「새로」·「이번에」 같은 «시의성 표현»이 있을 때만 search_article 을 부른다
  (없는데 부르면 [신설]이 답변을 오염시킨다 — 실측으로 확인했다)
- 분야 전체의 최신 동향을 묻는다 → list_recent

★get_fact·get_term 에는 «질문에 나온 말을 그대로» 넣는다.
  ⚠ 한 주제에 카드가 «여럿»일 수 있다 — 시점 · 원인 · 방법처럼.
    그래서 «무엇을 묻는지»(언제 · 왜 · 어떻게 · 얼마나)까지 함께 넣는다.
    주제어만 넣으면 후보가 여럿이 되어 «되묻게» 된다 — 되물으면 답을 못 한 것이다.
  「빙하기는 언제 끝났나요」 → get_fact("빙하기 언제 끝")  (「빙하기」 만 넣지 않는다)

★★네가 «안다»고 생각해도 반드시 조회한다. 조회 없이 답하면 근거가 없다.
⇒ 요약: **조회는 «반드시» 하되, «필요한 것만» 한다.**"""

# ★v1 — 예시가 골든셋 G01 «그 문항»이었다. 비교용으로만 남긴다.
#   감사기 [9] 에서 제외 대상이다(의도된 오염본).
PICK_GUIDE_V1 = """너는 과학 질문 데스크의 조회 담당이다. 답하려면 무엇을 조회해야 하는지 판단해
필요한 도구를 «전부» 부른다. 답변 문장은 쓰지 않는다.

- 널리 알려진 사실·용어·연대를 묻는다 → get_fact 또는 get_term
- 「최근」·「새로」·「이번에」 같은 «시의성 표현»이 있을 때만 search_article 을 부른다
  (없는데 부르면 [신설]이 답변을 오염시킨다 — 실측으로 확인했다)
- 분야 전체의 최신 동향을 묻는다 → list_recent

★get_fact·get_term 에는 «질문에 나온 말을 그대로» 넣는다.
  「공룡은 언제 멸종했나요」 → get_fact("공룡 언제 멸종")
  너무 짧게 자르면(「공룡 멸종」) 후보가 여럿이 되어 되묻게 된다.

★★네가 «안다»고 생각해도 반드시 조회한다. 조회 없이 답하면 근거가 없다.
⇒ 요약: **조회는 «반드시» 하되, «필요한 것만» 한다.**"""

# ★v3 — 홀드아웃이 드러낸 «설계 결함»을 고친다.
#
#   v2 는 이렇게 적혀 있었다:  「사실·용어·연대를 묻는다 → get_fact «또는» get_term」
#   ⇒ 모델에게 «둘 중 아무거나»라고 말해 놓고, 채점은 「정확히 일치」를 요구했다.
#     모델이 틀린 게 아니라 «내가 규칙을 안 정해 준» 것이다.
#
#   홀드아웃 10건에서 실패 4건 중 3건이 이 자리였다(H05·H06·H07).
#   골든셋 25건에서는 2건(G04·G17)이라 「가끔 헤맨다」로 넘겼었다 —
#   ★적은 표본에서는 «구조적 결함»이 «산발적 실수»처럼 보인다.
PICK_GUIDE_V3 = PICK_GUIDE_V2.replace(
    "- 널리 알려진 사실·용어·연대를 묻는다 → get_fact 또는 get_term\n"
    "- 「최근」·「새로」·「이번에」 같은 «시의성 표현»이 있을 때만 search_article 을 부른다\n"
    "  (없는데 부르면 [신설]이 답변을 오염시킨다 — 실측으로 확인했다)",
    "★도구는 «묻는 것»으로 고른다. 「또는」은 없다 — 하나만 고른다.\n"
    "- «말·방법의 뜻»을 묻는다 (~이 뭔가요 · 무슨 뜻인가요 · 어떤 원리인가요) → get_term\n"
    "- 그 밖의 사실·연대·수치를 묻는다                                    → get_fact\n"
    "  ⚠ 둘이 «같은 카드»에 닿을 수도 있다. 그래도 «질문이 무엇을 묻는지»로 고른다 —\n"
    "    뜻을 물었는데 get_fact 를 부르면 그 용어의 «한계»를 빠뜨리기 쉽다.\n"
    "- 「최근」·「새로」·「이번에」 같은 «시의성 표현»이 있으면 → search_article\n"
    "  ⚠ 기준 사실 카드에는 «최근 것»이 없다. 시의성 질문에 get_fact 를 부르면\n"
    "    「자료에 없다」가 나오는데, 그건 «안 찾아본 것»이지 «없는 것»이 아니다.\n"
    "  (반대로 시의성이 없는데 부르면 [신설]이 답변을 오염시킨다 — 실측)")

# 기본은 v3. DESK_PICK=v1(오염본) · v2(또는-문제) 로 되돌려 비교할 수 있다.
_PICKS = {"v1": PICK_GUIDE_V1, "v2": PICK_GUIDE_V2, "v3": PICK_GUIDE_V3}
PICK_GUIDE = _PICKS.get(os.environ.get("DESK_PICK", "v3"), PICK_GUIDE_V3)


ANSWER_RULES = """너는 「발견 데스크」다. 아래 [업무 원칙]과 [조회 결과]에만 근거해 답한다.
둘에 없는 것은 «만들어내지 않는다».

★가장 중요한 규칙 — 확실성 등급을 «빼먹지 않는다»
조회 결과의 certainty 값을 보고 그에 맞게 말한다.

[정설]  그대로 말해도 된다. 다만 「약」·「경」을 빼지 않는다
[추정]  오차가 있다. 숫자에 「약」을 붙인다
[논쟁]  ★양쪽을 말하고 «어느 한쪽을 답으로 고르지 않는다»
[신설]  ★① 언제 발표됐나 ② 어디서 ③ 「아직 검증되지 않았다」를 «반드시» 붙인다
        ⛔「밝혀졌습니다」 금지 → 「발표됐습니다」

★숫자 규칙
- 조회 결과의 숫자는 «그대로» 쓴다. 「○○년」 같은 자리표시를 쓰지 않는다
- 이미 조회했으면 「확인해 보겠습니다」라고 미루지 않는다
- 조회 결과에 적힌 «그 단어»를 쓴다

★조회 결과의 caution·limit 은 «너에게 주는 주의»다.
  그 문장을 답변에 «그대로 옮기지 마라». 내용을 지키되 네 말로 쓴다.

★반드시 «한국어만» 쓴다. 중국어·영어 문장을 섞지 않는다.
한국어 존댓말로 2~4문장. 간결하게."""


def _load_env():
    """.env 를 찾아 환경변수로 올린다 — 이미 있으면 덮지 않는다.

    ★키는 «파일에만» 둔다. 코드에는 «경로»만 적는다.
      찾는 순서: desk/.env -> 프로젝트 루트
      ⛔키를 «코드에» 적지 않는다. 파일에만 둔다(.gitignore 에 있다).
    """
    import os
    here = Path(__file__).parent
    for p in (here / ".env", here.parent / ".env"):
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        return str(p)
    return ""


_ENV_FROM = _load_env()


# ★맥락 붙이기 — «한 곳»에서만 만든다.
#   판정·조회·답변이 «다른 질문»을 보면 서로 어긋난다.
HISTORY_TURNS = 3          # 최근 몇 턴까지 볼까 — 길면 근거가 프롬프트에서 밀린다


def with_history(st):
    """앞선 대화를 질문 앞에 붙인다. 이력이 없으면 원문 그대로."""
    h = st.get("history") or []
    if not h:
        return st["question"]
    lines = []
    for q, a in h[-HISTORY_TURNS:]:
        lines.append("사용자: %s" % q)
        lines.append("데스크: %s" % (a or "")[:200])
    joined = "\n".join(lines)
    return "앞선 대화:\n%s\n\n지금 질문: %s" % (joined, st["question"])


def build(model="qwen2.5:7b", threshold=None):
    from langchain.tools import tool
    from langchain_ollama import ChatOllama
    from langgraph.errors import GraphRecursionError
    from langgraph.graph import END, START, StateGraph
    from langgraph.graph.message import add_messages
    from langgraph.prebuilt import ToolNode, tools_condition

    import context_desk
    import escalate
    import guard_desk
    import tools_desk
    sys.path.insert(0, str(HERE))
    import importlib.util as _u
    _sp = _u.spec_from_file_location("_r", HERE / "20_router.py")
    _rt = _u.module_from_spec(_sp)
    _argv, sys.argv = sys.argv, ["x"]
    _sp.loader.exec_module(_rt)
    sys.argv = _argv

    thr = escalate.DEFAULT_THRESHOLD if threshold is None else threshold

    def mk(bind=None):
        """★모델 이름으로 provider 를 고른다 — 같은 파이프라인에 «모델만» 바꿔 끼운다.

        노드4 에서 「모델이 달라 비교 불가」가 계속 발목을 잡았다.
        여기서는 로컬 7B 와 gpt-5.6 을 «같은 코드»로 돌려 나란히 잰다.
        ⚠ gpt-5 계열은 max_tokens 대신 max_completion_tokens 를 쓰고,
          temperature 를 1 로 고정한다(실측: 0 을 주면 400).
        """
        if model.startswith(("gpt-", "o1", "o3", "o4")):
            from langchain_openai import ChatOpenAI
            # ★reasoning_effort="none" 이 «필수»다 — 안 주면 도구 호출이 400 난다.
            #   "Function tools with reasoning_effort are not supported ... in /v1/chat/completions"
            #   ⚠ 어제 qwen3 의 reasoning=False 와 «같은 함정·같은 해법»이다.
            #     추론 토큰을 켠 채로는 도구를 못 쓴다.
            m = ChatOpenAI(model=model, max_completion_tokens=1500,
                           reasoning_effort="none")
        else:
            k = dict(model=model, temperature=0, num_predict=700)
            if model.startswith("qwen3"):
                k["reasoning"] = False
            m = ChatOllama(**k)
        return m.bind_tools(bind) if bind else m

    kw = dict(model=model, temperature=0, num_predict=700)   # 하위 그래프용
    if model.startswith("qwen3"):
        kw["reasoning"] = False
    # ★기본은 v2(오염 제거). DESK_GUIDE=v1 로 «오염본»을 재현할 수 있다 —
    #   20_router.py 의 --guide 와 «같은 뜻»이다. 한쪽만 바꾸면 또 어긋난다.
    _g = "v1" if os.environ.get("DESK_GUIDE") == "v1" else "v2"
    llm_route = _rt.make_llm(model, _rt.GUIDES[_g])
    write = mk()

    # ── ① 카테고리 판정 ───────────────────────────────
    def classify(st):
        route, conf, err = llm_route(with_history(st))
        if route == "_PARSE_FAIL":
            return {"route": "OTHER", "conf": 0.0, "reason": "형식 실패: %s" % err}
        return {"route": route, "conf": conf}

    # ── 넘기기 판단 (①과 «분리»된 것) ──────────────────
    def gate(st):
        dec, why = escalate.gate(st["route"], st.get("conf", 0), None, thr)
        return {"decision": dec, "reason": why}

    # ── ② 카테고리별 근거 조립 + 도구 호출 ──────────────
    def retrieve(st):
        route = st["route"]
        ctx = context_desk.build_context(route)
        names = context_desk.allowed_tools(route)
        if not names:
            return {"context": ctx, "used": {}}
        # ★그 카테고리에 «허용된» 도구만 바인딩한다 — 매핑표가 여기서 쓰인다
        lc = [tool(tools_desk.TOOLS[n]) for n in names if n in tools_desk.TOOLS]
        pick = mk(lc)

        class S(TypedDict, total=False):
            messages: Annotated[list, add_messages]

        g = StateGraph(S)
        g.add_node("agent", lambda s: {"messages": [pick.invoke(s["messages"])]})
        g.add_node("tools", ToolNode(lc))
        g.add_edge(START, "agent")
        g.add_conditional_edges("agent", tools_condition)
        g.add_edge("tools", "agent")
        sub = g.compile()

        used = {}
        err = ""
        try:
            out = sub.invoke(
                {"messages": [("system", PICK_GUIDE), ("human", with_history(st))]},
                {"recursion_limit": 2 * MAX_TOOL_TURNS + 1})
            for m in out["messages"]:
                if getattr(m, "name", None) in tools_desk.TOOLS:
                    try:
                        used[m.name] = json.loads(m.content)
                    except json.JSONDecodeError:
                        used[m.name] = m.content
        except GraphRecursionError:
            err = "RECURSION"
        except Exception as exc:                        # noqa: BLE001
            # ★예외를 «삼키면» 왜 도구를 못 불렀는지 영영 모른다.
            #   실제로 한 번 그래서 「도구 미호출」로만 보였다 — 어제 배운
            #   「실패를 오답으로 뭉뚱그리지 마라」를 여기서 어겼다.
            err = "%s: %s" % (type(exc).__name__, exc)
            import os
            if os.environ.get("DESK_DEBUG"):
                import traceback
                traceback.print_exc()
        else:
            err = ""
        return {"context": ctx, "used": used, "reason": err or None}

    # ── 근거를 못 찾았으면 여기서도 넘긴다 ───────────────
    def gate2(st):
        dec, why = escalate.gate(st["route"], st.get("conf", 0), st.get("used", {}), thr)
        return {"decision": dec, "reason": why}

    # ── ③ 근거만으로 답변 ─────────────────────────────
    def compose(st):
        sys_prompt = "%s\n\n===== 업무 원칙 (%s) =====\n%s\n\n===== 조회 결과 =====\n%s\n" % (
            ANSWER_RULES, st["route"], st.get("context", ""),
            json.dumps(st.get("used", {}), ensure_ascii=False, indent=1))
        try:
            txt = write.invoke([("system", sys_prompt),
                                ("human", with_history(st))]).content
        except Exception as exc:                        # noqa: BLE001
            return {"answer": "", "reason": type(exc).__name__}
        return {"answer": txt}

    # ── ④ 검증 ──────────────────────────────────────
    def verify(st):
        return {"guard": guard_desk.check(st.get("answer", ""), st.get("used", {}))}

    def finish(st):
        dec = st.get("decision", "CONTINUE")
        if dec == "REFUSE":
            reply = escalate.REFUSE_REPLY
        elif dec == "ESCALATE":
            reply = escalate.ESCALATE_REPLY
        elif dec == "ASK":
            reply = escalate.ask_reply(st.get("used"))
        else:
            return {}
        return {"answer": reply, "guard": {"ok": True, "violations": []}}

    g = StateGraph(DeskState)
    for fn in (classify, gate, retrieve, gate2, compose, verify, finish):
        g.add_node(fn.__name__, fn)
    g.add_edge(START, "classify")
    g.add_edge("classify", "gate")
    g.add_conditional_edges(
        "gate",
        lambda s: "finish" if s.get("decision") != "CONTINUE" else "retrieve",
        {"finish": "finish", "retrieve": "retrieve"})
    g.add_edge("retrieve", "gate2")
    g.add_conditional_edges(
        "gate2",
        lambda s: "finish" if s.get("decision") != "CONTINUE" else "compose",
        {"finish": "finish", "compose": "compose"})
    g.add_edge("compose", "verify")
    g.add_edge("verify", "finish")
    g.add_edge("finish", END)
    return g.compile()


def ask(app, question):
    st = app.invoke({"question": question})
    return st


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ask", required=False)
    ap.add_argument("--model", default="qwen2.5:7b")
    ap.add_argument("--threshold", type=float, default=None)
    ap.add_argument("--eval", action="store_true")
    ap.add_argument("--set", default="golden", choices=["golden", "holdout"],
                    help="★holdout 은 «지침을 고칠 때 안 본» 문항이다. 한 번만 잰다")
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()

    app = build(args.model, args.threshold)

    if args.ask:
        st = ask(app, args.ask)
        print("=== 질문 ===")
        print("   %s" % args.ask)
        print()
        print("① 카테고리   %s (확신도 %.2f)" % (st.get("route"), st.get("conf", 0)))
        if st.get("decision") not in (None, "CONTINUE"):
            print("   ★%s — %s" % (st.get("decision"), st.get("reason")))
        print("② 근거       %s · %d자" % (st.get("route"), len(st.get("context") or "")))
        print("   도구       %s" % (", ".join(st.get("used") or {}) or "(없음)"))
        print("④ 검증       %s" % ("통과" if (st.get("guard") or {}).get("ok")
                                    else (st.get("guard") or {}).get("violations")))
        print()
        print("=== 답변 ===")
        print(st.get("answer") or "(없음)")
        sys.exit(0)

    if args.eval:
        from concurrent.futures import ThreadPoolExecutor
        import time
        import score_desk
        # ★어느 셋으로 재는지 «화면에 적는다» — 섞이면 숫자의 뜻이 달라진다
        _f = ((HERE / "golden.json") if args.set == "golden"
              else (HERE.parent / "data/holdout.json"))
        _d = json.loads(_f.read_text(encoding="utf-8"))
        gold = _d["cases"]
        print("=== ② 답변 채점 — %d건 · %s · 평가셋 %s ==="
              % (len(gold), args.model, args.set.upper()))
        if args.set == "holdout":
            print("   ★홀드아웃 — 지침을 고치는 동안 «한 번도 보지 않은» 문항입니다.")
            print("   ⛔이 결과를 보고 고치면 더는 홀드아웃이 아닙니다.")
        t0 = time.perf_counter()

        def run(c):
            st = ask(app, c["question"])
            return c, st.get("answer", ""), st.get("used", {}), ""

        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            rows = list(ex.map(run, gold))
        score_desk.report(rows, time.perf_counter() - t0)
