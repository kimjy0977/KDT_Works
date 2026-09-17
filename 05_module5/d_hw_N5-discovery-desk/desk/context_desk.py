# -*- coding: utf-8 -*-
"""★카테고리별 «근거 조립» — 문서 전체가 아니라 필요한 부분만.

요건(노드5)
  필수구현 1: 「각 카테고리를 근거 문서의 «어느 부분»과 연결할지 **매핑표**를 만든다.
              이 매핑이 다음 단계의 근거 조립에 그대로 쓰인다」
  필수구현 3: 「근거 문서 «전체»가 아니라 카테고리별로 «필요한 부분만» 프롬프트에 넣는다」

★어제(노드4)에서 배운 것
  7,227자 프롬프트에서 **도구 호출이 사라졌다.** 매뉴얼을 쪼갰는데도 길었다.
  ⇒ 짧게 넣는 것은 «토큰 아끼기»가 아니라 **동작 여부**의 문제다.

★매핑표는 «코드가 곧 표»다
  문서에 표를 그려 두고 코드가 다르게 동작하면 둘이 어긋난다(§H-4).
  그래서 여기 MAPPING 하나만 두고, 문서는 이것을 «출력»해서 만든다.

  python context_desk.py            # 매핑표를 찍는다 (REPORT 에 붙일 것)
  python context_desk.py --check    # 연결 안 된 카테고리가 있는지 검사
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent
POLICY = HERE.parent / "01_policy_초안.md"

# ★매핑표 — 카테고리 → (근거 문서의 어느 절, 어느 도구, 어느 사실카드 라우트)
MAPPING = {
    "SPACE": {
        "policy_sections": ["0. 기본 원칙", "1. 질문 유형 분류", "2. 우주 (SPACE)"],
        "tools": ["get_fact", "search_article", "get_article", "list_recent"],
        "facts_route": "SPACE",
        "why": "거리·크기는 [정설]이나 측정 오차가 있고, 탐사 일정은 [추정]이라 "
               "«유효숫자»와 «연기 가능성»을 다루는 절이 따로 필요하다",
    },
    "ARCHAEO": {
        "policy_sections": ["0. 기본 원칙", "1. 질문 유형 분류", "3. 고고학 (ARCHAEO)"],
        "tools": ["get_fact", "search_article", "get_article", "list_recent"],
        "facts_route": "ARCHAEO",
        "why": "탄소연대의 «보정 여부»와 «오차 ±», 그리고 용도 해석이 대개 [논쟁]이라 "
               "「무엇에 쓰였나」를 단정하지 않는 규칙이 여기에만 있다",
    },
    "PALEO": {
        "policy_sections": ["0. 기본 원칙", "1. 질문 유형 분류", "4. 고생물 (PALEO)"],
        "tools": ["get_fact", "search_article", "get_article", "list_recent"],
        "facts_route": "PALEO",
        "why": "외형 복원(색·깃털)과 계통이 [추정]·[논쟁]이라 "
               "「A가 B의 조상인가」를 단정하지 않는 규칙이 필요하다",
    },
    "CONCEPT": {
        "policy_sections": ["0. 기본 원칙", "1. 질문 유형 분류", "5. 개념·용어 (CONCEPT)"],
        "tools": ["get_term", "get_fact"],
        "facts_route": "CONCEPT",
        "why": "정의는 [정설]로 답해도 되지만 «한계»를 함께 말해야 한다. "
               "기사 검색은 필요 없다 — 용어의 뜻은 최신 발표와 무관하다",
    },
    "OTHER": {
        "policy_sections": ["0. 기본 원칙", "6. 범위 밖 (OTHER)"],
        "tools": [],
        "facts_route": None,
        "why": "★조회하지 않는다. 판정하지 말고 «왜 답할 수 없는지»만 말한다. "
               "도구를 부르면 그럴듯한 근거가 생겨 오히려 답하게 된다",
    },
}


def _split_policy():
    """policy 를 «## 절» 단위로 쪼갠다."""
    txt = POLICY.read_text(encoding="utf-8")
    parts, cur, buf = {}, None, []
    for line in txt.split("\n"):
        m = re.match(r"^##\s+(.+)$", line)
        if m:
            if cur:
                parts[cur] = "\n".join(buf).strip()
            cur, buf = m.group(1).strip(), []
        else:
            buf.append(line)
    if cur:
        parts[cur] = "\n".join(buf).strip()
    return parts


SECTIONS = _split_policy()


def build_context(route):
    """★그 카테고리에 «필요한 부분만» 이어 붙인다."""
    m = MAPPING.get(route) or MAPPING["OTHER"]
    out = []
    for name in m["policy_sections"]:
        body = SECTIONS.get(name)
        if body:
            out.append("## %s\n%s" % (name, body))
    return "\n\n".join(out)


def allowed_tools(route):
    return list((MAPPING.get(route) or MAPPING["OTHER"])["tools"])


def mapping_table():
    """★REPORT 에 붙일 매핑표 — 코드가 «곧» 표다."""
    rows = ["| 카테고리 | 근거 문서의 어느 부분 | 쓸 수 있는 도구 | 왜 그렇게 연결했나 |",
            "|---|---|---|---|"]
    for rt, m in MAPPING.items():
        rows.append("| `%s` | %s | %s | %s |" % (
            rt,
            " · ".join("§" + s.split(".")[0] for s in m["policy_sections"]),
            ", ".join("`%s`" % t for t in m["tools"]) or "**없음**",
            m["why"]))
    return "\n".join(rows)


def check():
    """★연결 안 된 카테고리가 있는지 — 요건: 「없으면 다시 나누거나 문서를 보강한다」"""
    bad = 0
    print("=== 매핑 검사 ===")
    for rt, m in MAPPING.items():
        missing = [s for s in m["policy_sections"] if s not in SECTIONS]
        ctx = build_context(rt)
        ok = not missing and len(ctx) > 200
        print("   %-9s 절 %d개 · %5d자 · 도구 %d개  %s"
              % (rt, len(m["policy_sections"]), len(ctx), len(m["tools"]),
                 "✅" if ok else "⛔"))
        if missing:
            print("        ⛔ policy 에 없는 절: %s" % missing)
            bad += 1
        elif not ok:
            print("        ⛔ 근거가 너무 짧다 — 문서를 보강해야 한다")
            bad += 1
    print()
    full = len(POLICY.read_text(encoding="utf-8"))
    avg = sum(len(build_context(r)) for r in MAPPING) / len(MAPPING)
    print("   문서 전체 %d자 → 카테고리 평균 %d자 (%.0f%%)" % (full, avg, 100 * avg / full))
    print("   ※ 어제 7,227자에서 «도구 호출이 사라졌다». 짧게 넣는 건 토큰이 아니라 동작 문제다.")
    return bad


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(check())
    print("=== 카테고리 ↔ 근거 문서 매핑표 ===")
    print()
    print(mapping_table())
    print()
    print("※ 이 표는 `context_desk.MAPPING` 을 출력한 것입니다.")
    print("  문서와 코드가 어긋나지 않도록 «코드를 원본»으로 둡니다.")
