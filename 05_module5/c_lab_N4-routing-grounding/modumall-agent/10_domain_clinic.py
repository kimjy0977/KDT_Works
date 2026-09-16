# -*- coding: utf-8 -*-
"""★12강 「더 해보기」 3 — 다른 도메인으로 «전체»를 재현한다.

12강이 시킨 것:
  「금융·통신 등 다른 상담 데이터와 그 도메인의 공개 정책 문서를 구해, 라우트 정의부터
   정답셋 저작까지 이틀의 절차를 반복합니다. 매뉴얼에 [어드민 조회]에 해당하는 표시를
   직접 설계해 붙여 봅니다.
   ⇒ 이 파이프라인이 «도메인에 종속되지 않는다»는 것을 증명할 수 있습니다.」

무엇을 «그대로» 옮겼나 — 구조가 같으면 코드도 같아야 한다
    매뉴얼 §0 원칙 · §1 분류 · §1.1 판단기준 · §7.1 범위밖 · §8 응대태도
    [어드민 조회] 표기 → 도구 명세
    ★함정도 «같은 자리»에 심었다:
      모두몰  카테고리마다 무료배송 기준액이 다르다   → 하드코딩하면 «우연히 맞는다»
      하늘치과 부위마다 같은 이름의 진료비가 다르다    → 같은 함정
      모두몰  inspection_result = null            → 「아직 안 정해졌다」
      하늘치과 진단서 days = null                  → 같은 구조

무엇이 «달랐나» — 옮기면서 알게 된 것은 마지막 절에 적는다.

  python 10_domain_clinic.py            # 라우터 + 답변 + 채점
  python 10_domain_clinic.py --tools    # 도구만 확인(모델 호출 0)
"""
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Literal, Optional

from langchain.tools import tool
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from evaluate import score_turn

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent / "domain_clinic"
MD = json.loads((HERE / "mockdata_clinic.json").read_text(encoding="utf-8"))
POLICY = (HERE / "policy_clinic.md").read_text(encoding="utf-8")
GOLD = json.loads((HERE / "answer_goldenset_clinic.json").read_text(encoding="utf-8"))

ROUTES = ["BOOKING", "TREATMENT", "COST", "RECORDS", "OTHER"]
LABELS4 = ["BOOKING", "TREATMENT", "COST", "RECORDS"]
TREATMENTS = {t["code"]: t for t in MD["treatments"]}
APPTS = {a["appt_id"]: a for a in MD["appointments"]}
DOCS = {d["doc_type"]: d for d in MD["documents"]}


def clean(d):
    """★$ 로 시작하는 키는 제거한다 — 교육용 주석에 «정답»이 적혀 있다(8강)."""
    return {k: v for k, v in d.items() if not k.startswith("$")}


# ─────────── 조회 도구 — [어드민 조회] 표기에서 «그대로» 뽑았다 ───────────
def search_treatment(query: str) -> dict:
    """진료 이름으로 진료 코드를 찾는다. 부위가 갈리면 후보를 모두 돌려준다."""
    hits = [t for t in MD["treatments"] if t["name"] in query or query in t["name"]]
    if not hits:
        return {"error": "해당 진료를 찾을 수 없습니다", "query": query}
    if len(hits) > 1:
        return {"ambiguous": True, "candidates": [clean(h) for h in hits],
                "note": "부위에 따라 금액·보험이 다릅니다. 어느 부위인지 확인이 필요합니다."}
    return {"ambiguous": False, "resolved_code": hits[0]["code"], **clean(hits[0])}


def get_treatment_cost(code: str) -> dict:
    """진료 코드로 금액·보험 적용·소요 시간을 조회한다."""
    t = TREATMENTS.get(code)
    if not t:
        return {"error": "진료 코드를 찾을 수 없습니다", "code": code}
    out = clean(t)
    out["초진_진찰료"] = MD["fixed"]["초진_진찰료"]
    return out


def get_appointment(appt_id: str) -> dict:
    """예약번호로 예약 상태·변경 가능 시한·노쇼 횟수를 조회한다."""
    a = APPTS.get(appt_id)
    return clean(a) if a else {"error": "예약을 찾을 수 없습니다", "appt_id": appt_id}


def get_document_info(doc_type: str) -> dict:
    """서류 종류로 수수료·소요일을 조회한다. days 가 null 이면 «미확정»이다."""
    d = DOCS.get(doc_type)
    return clean(d) if d else {"error": "해당 서류를 찾을 수 없습니다", "doc_type": doc_type}


def get_available_slots(date: str) -> dict:
    """날짜로 예약 가능 시간대를 조회한다."""
    s = MD["slots"].get(date)
    if s is None:
        return {"error": "해당 날짜 정보가 없습니다", "date": date}
    return {"date": date, "slots": s, "available": len(s) > 0}


TOOLS = {f.__name__: f for f in
         [search_treatment, get_treatment_cost, get_appointment,
          get_document_info, get_available_slots]}
LC_TOOLS = [tool(f) for f in TOOLS.values()]

ROUTE_GUIDE = """\
너는 '하늘치과'의 상담 라우터다. 고객 문의 한 건을 읽고 아래 5개 중 하나로 분류한다.

[라우트 정의 — 매뉴얼 1장]
- BOOKING   : 예약 접수·변경·취소, 예약 가능 여부 (담당: 원무)
- TREATMENT : 진료 항목·소요 시간·통증·주의사항 (담당: 진료)
- COST      : 진료비, 보험 적용 여부, 비급여 금액 (담당: 수납)
- RECORDS   : 진단서·영수증·진료기록 발급 (담당: 원무)
- OTHER     : 응대 범위 밖

[분류 원칙 — 매뉴얼 1.1]
고객이 쓴 단어가 아니라, 고객이 원하는 «결과»로 판단한다.
BOOKING 과 TREATMENT 는 어휘가 거의 같다("스케일링 되나요"). 바로 예약을 잡으려는 의사가
보이면 BOOKING, 진료가 어떤 것인지 알아보려는 것이면 TREATMENT 다.

[분류 우선순위 — 매뉴얼 1.2]
1) 응대 범위 밖이면 OTHER
2) 이미 받은 진료의 «비용»에 관한 문의면 COST
3) 그 외는 위 네 유형

[범위 밖 — 매뉴얼 7.1]
하늘치과는 치과 단일 진료과다. 타 병원 예약·공단 업무·약국 문의·주차 정산은 OTHER 다.

[확신도 지침]
두 라우트 사이에서 결정하기 어려우면 confidence 를 0.5 미만으로 낮춰라.
"""

ANSWER_RULES = """\
너는 '하늘치과'의 상담원이다. 아래 [매뉴얼]과 [조회 결과]에만 근거해 답한다.

절대 규칙
1. 매뉴얼 본문에 값이 적힌 항목(초진 진찰료 18,000원 · 진단서 20,000원 · 영수증 무료 ·
   변경 시한 하루 전 18:00 · 노쇼 3회 제한)은 그 값으로 바로 답해도 된다.
2. [어드민 조회] 항목(진료비·보험 적용·소요 시간·예약 상태·서류 소요일)은
   [조회 결과]에 있는 값만 쓴다. 조회 결과에 없는 숫자를 쓰지 않는다.
3. 조회 결과가 null 인 항목은 "아직 확정되지 않았다"로 답한다.
4. ★같은 이름의 진료라도 «부위»에 따라 금액이 다르다. 부위를 모르면 되묻는다.
5. 존댓말로 간결하게 1~3문장.
"""


class RouteDecision(BaseModel):
    route: Literal["BOOKING", "TREATMENT", "COST", "RECORDS", "OTHER"]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


def build_prompt(question, route, results=None):
    ctx = ANSWER_RULES + "\n[매뉴얼]\n" + POLICY
    if results:
        ctx += "\n\n[조회 결과]\n" + json.dumps(results, ensure_ascii=False, indent=1)
    return ctx


def llm(model, tools=False):
    kw = dict(model=model, temperature=0, num_predict=700)
    if model.startswith("qwen3"):
        kw["reasoning"] = False
    m = ChatOllama(**kw)
    return m.bind_tools(LC_TOOLS) if tools else m


PICK = """\
너는 치과 상담 시스템의 조회 담당이다. 조회가 «꼭 필요할 때만» 도구를 부른다. 답변은 쓰지 않는다.
★어느 진료·어느 예약인지 특정할 수 없으면 아무 도구도 부르지 않는다.
  같은 진료 이름이라도 «부위»가 갈리면 특정된 것이 아니다.
"""


def run(question, route, model):
    msgs = [("system", PICK), ("human", question)]
    used = {}
    picker = llm(model, tools=True)
    for _ in range(3):
        r = picker.invoke(msgs)
        calls = getattr(r, "tool_calls", []) or []
        if not calls:
            break
        msgs.append(r)
        from langchain_core.messages import ToolMessage
        for c in calls:
            fn = TOOLS.get(c["name"])
            out = fn(**c["args"]) if fn else {"error": "unknown tool"}
            used[c["name"]] = out
            msgs.append(ToolMessage(content=json.dumps(out, ensure_ascii=False),
                                    tool_call_id=c["id"], name=c["name"]))
    text = llm(model).invoke(
        [("system", build_prompt(question, route, used or None)), ("human", question)]).content
    return text, used


def judge(text, used):
    if not used and re.search(r"\?|주시겠|알려주|말씀해|확인이 필요", text):
        return "ASK"
    # 범위 밖은 매뉴얼 §7.1 문구로 판정 (모두몰의 is_external_channel 자리)
    if re.search(r"직접 문의|확인해 드리기 어렵", text) and not used:
        return "OUT_OF_SCOPE"
    return "ANSWER"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="다른 도메인으로 재현 (12강 더해보기 3)")
    ap.add_argument("--model", default="qwen3.5:2b")
    ap.add_argument("--tools", action="store_true", help="도구만 확인(모델 호출 0)")
    args = ap.parse_args()

    print("=== ★도메인을 옮겼다 — 모두몰 → 하늘치과 ===")
    print("   매뉴얼 %d자 · 진료 %d · 예약 %d · 서류 %d · 도구 %d개"
          % (len(POLICY), len(MD["treatments"]), len(MD["appointments"]),
             len(MD["documents"]), len(TOOLS)))
    print()

    print("=== ① 도구가 «함정»을 제대로 드러내는가 (모델 호출 0) ===")
    r = search_treatment("스케일링")
    print("   search_treatment('스케일링') → ambiguous=%s · 후보 %d개"
          % (r.get("ambiguous"), len(r.get("candidates", []))))
    for c in r.get("candidates", []):
        print("      %s %s(%s) %,d원 · 보험 %s".replace(",d", "d")
              % (c["code"], c["name"], c["site"], c["price"], c["insured"]))
    print("   ⇒ ★모두몰의 「카테고리마다 무료배송 기준액이 다르다」와 «같은 자리»다.")
    print()
    d = get_document_info("진단서")
    print("   get_document_info('진단서') → fee=%s · days=%s" % (d["fee"], d["days"]))
    print("   ⇒ ★days=null — 「없다」가 아니라 「아직 안 정해졌다」")
    print()
    a = get_appointment("A-5003")
    print("   get_appointment('A-5003') → 노쇼 %d회 · 변경시한 %s"
          % (a["no_show_count"], a["changeable_until"]))
    print("   ⇒ ★2회다. 「제한됐다」고 단정하면 오답 — 3회부터다.")
    print()
    print("   ✅ $teaching_note 제거 확인:",
          all("$teaching_note" not in str(x) for x in
              [r, d, a, get_treatment_cost("T-101")]))
    if args.tools:
        sys.exit(0)

    print()
    print("=== ② 채점기를 «그대로» 쓴다 — score_turn 은 도메인을 모른다 ===")
    cases = []
    for c in GOLD["conversations"]:
        for t in c["turns"]:
            if t.get("expect"):
                q = next((x["text"] for x in c["turns"] if x["role"] == "customer"), "")
                cases.append({"conv": c["conv_id"], "route": c["route"],
                              "q": t.get("text") or q, "expect": t["expect"],
                              "question": q})
    # 채점기 자기 검증 — 모범답안은 전부 통과해야 한다(11강)
    bad = [c["conv"] for c in cases
           if not score_turn(c["expect"], c["expect"]["reference"],
                             c["expect"].get("tools", []), c["expect"]["action"])[0]]
    print("   [자기 검증] 모범답안 %d건 중 실패 %d건 %s"
          % (len(cases), len(bad), bad if bad else "✅"))
    print()

    print("=== ③ 실제로 돌려 채점 ===")
    ok_n = 0
    for c in cases:
        text, used = run(c["question"], c["route"], args.model)
        act = judge(text, used)
        ok, fails = score_turn(c["expect"], text, list(used), act)
        ok_n += ok
        print("   %-6s %-13s→%-13s %s" % (c["conv"], c["expect"]["action"], act,
                                          "✅" if ok else "; ".join(fails)[:52]))
        if not ok:
            print("        답변: %s" % text[:78].replace("\n", " "))
    print()
    print("   ⇒ %d/%d 통과 (%.0f%%)" % (ok_n, len(cases), 100 * ok_n / len(cases)))
    print()
    print("=== ★옮기면서 알게 된 것 ===")
    print("   · 매뉴얼 구조(§0·§1·§1.1·§7.1·§8)는 «그대로» 옮겨졌다 — 도메인 독립적이다")
    print("   · 채점기 score_turn 은 «한 줄도» 안 고쳤다 — action/tools/must/forbid 만 본다")
    print("   · ★고쳐야 했던 것은 judge() 하나다 —")
    print("     모두몰은 OUT_OF_SCOPE 를 is_external_channel 플래그로 판정했는데,")
    print("     치과에는 그런 플래그가 없어 «문구»로 판정해야 했다.")
    print("     ⇒ 11강이 「action 판정은 우리가 정한다」고 한 부분이 «도메인 종속»이다.")
