# -*- coding: utf-8 -*-
"""★② 답변 생성 — 조회하고, «확실성 등급»과 함께 답한다.

노드4 에서 배운 것을 «처음부터» 넣는다
  1. ★2단계 분리 — 도구 선택(짧은 지침) / 답변 작성(정책 + 조회결과)
     어제 7,227자 프롬프트에서 «도구 호출이 사라졌다». 9강의 「모델이 스스로 조회」는
     큰 모델을 전제한다.
  2. ★MAX_TOOL_TURNS = 5 — 3 이면 조회가 막혀 이관으로 떨어진다
  3. ★답변 규칙에 「숫자를 그대로」·「미루지 마라」·「그 단어를 써라」
     어제 이 세 줄이 18.8% → 31.2% 를 벌었다.

★이 프로젝트만의 것 — 확실성 등급
  모두몰은 「배송비 2,500원」이 확정값이라 그냥 말하면 됐다.
  여기서는 **맞는 숫자를 «틀린 확신»으로 말하는 것**이 더 자주 일어난다.
  ⇒ [신설]을 「밝혀졌습니다」라고 쓰는 순간 [정설]로 둔갑한다.

  python 30_answer.py --ask "공룡은 언제 멸종했나요"
  python 30_answer.py --eval          # 골든셋 전체 채점
"""
import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent
ROOT = HERE.parent

MAX_TOOL_TURNS = 5          # ★설정값 한 줄이 프롬프트 여러 줄보다 셌다

# ── 1단계: 도구 선택 — «짧은» 지침 ──────────────────────────
PICK_GUIDE = """너는 과학 질문 데스크의 조회 담당이다. 답하려면 무엇을 조회해야 하는지 판단해
필요한 도구를 «전부» 부른다. 답변 문장은 쓰지 않는다.

- 널리 알려진 사실·용어·연대를 묻는다 → get_fact 또는 get_term
- 「최근」·「새로」·「이번에」가 있거나 시의성이 있다 → search_article
- search_article 결과에서 자세히 볼 것이 있으면 get_article 로 본문을 본다
- 분야 전체의 최신 동향을 묻는다 → list_recent
- 점성술·의학상담·투자조언 같은 범위 밖이면 «아무 도구도 부르지 않는다»

★★「최근」·「새로」·「이번에」 같은 «시의성 표현»이 없으면 search_article 을 «부르지 않는다».
  널리 알려진 사실을 묻는데 최신 기사를 섞으면 [신설]이 답변을 오염시킨다.
  (실측: 「공룡은 언제 멸종했나요」에 search_article 을 섞었더니
   모델이 「확실하지 않습니다」라고 답했다. [정설]인데도.)

★★네가 «안다»고 생각해도 반드시 조회한다. 조회 없이 답하면 근거가 없다.
  (실측: 「프리프린트는 논문과 뭐가 다른가요」에 도구를 «하나도» 안 부르고
   「이 주제에 대해선 아직 논문이 발표되지 않았습니다」라는 엉뚱한 답을 냈다.)

⇒ 요약: **조회는 «반드시» 하되, «필요한 것만» 한다.**"""

# ── 2단계: 답변 작성 ────────────────────────────────────────
ANSWER_RULES = """너는 「발견 데스크」다. 우주·고고학·고생물 질문에 답한다.
아래 [조회 결과]에만 근거해 답한다. 조회 결과에 없는 것은 «만들어내지 않는다».

★가장 중요한 규칙 — 확실성 등급을 «빼먹지 않는다»
조회 결과의 certainty 값이 무엇인지 보고, 그에 맞게 말한다.

[정설]  널리 합의된 것. 그대로 말해도 된다. 다만 「약」·「경」을 빼지 않는다
[추정]  오차가 있다. 숫자에 「약」을 붙이고, 오차가 있으면 함께 말한다
[논쟁]  학계가 갈린다. ★양쪽을 말하고 «어느 한쪽을 답으로 고르지 않는다»
[신설]  최근 발표다. ★세 가지를 «반드시» 붙인다:
        ① 언제 발표됐나  ② 어디서(출처)  ③ 「아직 검증되지 않았다」
        ⛔「밝혀졌습니다」 금지 → 「발표됐습니다」
          그 한 단어가 [신설]을 [정설]로 바꾼다

★숫자 규칙 (조회 결과에 값이 있을 때)
- 조회 결과의 숫자는 «그대로» 쓴다. 「○○년」 같은 자리표시를 쓰지 않는다
- 이미 조회했으면 「확인해 보겠습니다」라고 미루지 않는다. 값을 바로 말한다
- 조회 결과에 적힌 «그 단어»를 쓴다 (「논쟁 중」을 「아직 모른다」로 바꾸지 않는다)

★답하면 «안 되는» 것 — 조회 결과가 비었거나 범위 밖이면
- 의학적 조언, 미래 단정, 유사과학 판정, 개인 투자·진로 조언은 하지 않는다
- 판정하지 말고 «왜 이 데스크가 답할 수 없는지»를 말한다
  예) 「저는 관측·발굴·화석 연구에서 나온 자료로만 답합니다. 그 주제는 다루지 않습니다.」

★조회 결과에 caution 이나 limit 이 있으면 «반드시» 답변에 반영한다.
  그게 이 답변에서 가장 틀리기 쉬운 자리를 알려주는 것이다.

★반드시 «한국어만» 쓴다. 중국어·영어 문장을 섞지 않는다.
  (기준선 측정에서 답변 한가운데에 중국어가 섞여 나왔다 — qwen 계열의 알려진 버릇이다.
   고유명사와 학명은 괄호 안에 원어를 적어도 된다.)

한국어 «존댓말»로 2~4문장. 간결하게.
(1차 시험에서 반말로 답했다 — 지침에 없으면 모델이 정하지 않는다)"""


def build_graph(model):
    from langchain.tools import tool
    from langchain_ollama import ChatOllama
    from langgraph.graph import START, StateGraph
    from langgraph.graph.message import add_messages
    from langgraph.prebuilt import ToolNode, tools_condition
    from typing import Annotated, TypedDict

    import tools_desk

    lc_tools = [tool(fn) for fn in tools_desk.TOOLS.values()]

    class S(TypedDict, total=False):
        messages: Annotated[list, add_messages]

    kw = dict(model=model, temperature=0, num_predict=700)
    if model.startswith("qwen3"):
        kw["reasoning"] = False
    pick = ChatOllama(**kw).bind_tools(lc_tools)
    write = ChatOllama(**kw)

    g = StateGraph(S)
    g.add_node("agent", lambda st: {"messages": [pick.invoke(st["messages"])]})
    g.add_node("tools", ToolNode(lc_tools))
    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", tools_condition)
    g.add_edge("tools", "agent")
    return g.compile(), write, tools_desk


def answer(question, graph, write, tools_desk):
    """1단계 조회 → 2단계 작성. 조회 결과를 «그대로» 넘긴다."""
    from langgraph.errors import GraphRecursionError
    used = {}
    try:
        out = graph.invoke(
            {"messages": [("system", PICK_GUIDE), ("human", question)]},
            {"recursion_limit": 2 * MAX_TOOL_TURNS + 1})
    except GraphRecursionError:
        out = None
    except Exception as exc:                       # noqa: BLE001
        return "", {}, type(exc).__name__

    if out:
        for m in out["messages"]:
            if getattr(m, "name", None) in tools_desk.TOOLS:
                try:
                    used[m.name] = json.loads(m.content)
                except json.JSONDecodeError:
                    used[m.name] = m.content

    ctx = json.dumps(used or {}, ensure_ascii=False, indent=1)
    sys_prompt = "%s\n\n===== 조회 결과 =====\n%s\n" % (ANSWER_RULES, ctx)
    try:
        txt = write.invoke([("system", sys_prompt), ("human", question)]).content
    except Exception as exc:                       # noqa: BLE001
        return "", used, type(exc).__name__
    return txt, used, ""


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ask", help="한 건만 물어본다")
    ap.add_argument("--model", default="qwen2.5:7b")
    ap.add_argument("--eval", action="store_true", help="골든셋 전체 채점")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()

    graph, write, td = build_graph(args.model)

    if args.ask:
        txt, used, err = answer(args.ask, graph, write, td)
        print("=== 질문 ===")
        print("   %s" % args.ask)
        print()
        print("=== 부른 도구 ===")
        for k, v in used.items():
            brief = json.dumps(v, ensure_ascii=False)[:150]
            print("   %-16s %s" % (k, brief))
        if not used:
            print("   (없음)")
        print()
        print("=== 답변 ===")
        print(txt or ("⛔ 실패: %s" % err))
        sys.exit(0)

    if args.eval:
        from concurrent.futures import ThreadPoolExecutor
        import time
        gold = json.loads((HERE / "golden.json").read_text(encoding="utf-8"))["cases"]
        if args.limit:
            gold = gold[:args.limit]
        print("=== ② 답변 채점 — %d건 · %s ===" % (len(gold), args.model))
        t0 = time.perf_counter()

        def run(c):
            txt, used, err = answer(c["question"], graph, write, td)
            return c, txt, used, err

        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            rows = list(ex.map(run, gold))
        secs = time.perf_counter() - t0

        import score_desk
        score_desk.report(rows, secs)
