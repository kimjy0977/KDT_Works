# -*- coding: utf-8 -*-
"""★산출물을 «전수 검사»한다 — 만들면서 계속 돌린다.

왜 도구로 만드나
  어제(노드4) README §8「안 한 것」이 **실제와 어긋나 있었다** —
  이미 한 항목이 「⚠ 안 함」으로 남아 있었고, 자가검토에는 「11/11 완료」라 적혀 있었다.
  **두 문서가 다른 말을 하면 읽는 사람은 «둘 다» 못 믿는다.**
  눈으로 하는 점검은 «빠진다». 그래서 도구로 만든다.

★§F-8-D 3단계 — 범위를 «기억»으로 정하지 않는다
  폴더를 통째로 훑고, 확장자는 «바이너리 제외»로 뒤집는다.
  어제 점검기가 「폴더 열거 + 확장자 열거」를 두 겹 해서
  815개를 안 보면서 「0건」이라 보고한 적이 있다.

  python 99_audit.py
"""
import csv
import io
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent
ROOT = HERE.parent

BIN_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".exe", ".dll",
           ".pyc", ".so", ".woff", ".woff2", ".ico", ".mp4", ".webp"}

FAIL, WARN, OK = [], [], []


def _nq(s):
    """질문 정규화 — 공백·문장부호를 지운다. 겹침 판정의 «유일한 기준»."""
    return re.sub(r"[\s?.!、，,]+", "", s or "")


def _seed_rows():
    """평가셋 행 + «채점 대상» 수.

    ★example 행은 지침(프롬프트)에 쓰는 예시지 평가용이 아니다.
      이 구분을 두 곳에 나눠 적었다가 한 곳만 고친 적이 있다 — 그래서 한 곳에 둔다.
    """
    rows = list(csv.DictReader(io.open(ROOT / "03_평가셋_씨앗.csv", encoding="utf-8")))
    return rows, len([r for r in rows if r["split"] != "example"])


def chk(cond, msg, level="fail"):
    (OK if cond else (FAIL if level == "fail" else WARN)).append(msg)
    return cond


# ─────────────────────────────────────────────────────────
# 1. 제어문자 — 범위를 «세서» 정한다
# ─────────────────────────────────────────────────────────
def audit_control_chars():
    seen = skipped = bad_files = 0
    for f in sorted(ROOT.rglob("*")):
        if not f.is_file() or ".venv" in f.parts or "__pycache__" in f.parts:
            continue
        if f.suffix.lower() in BIN_EXT:
            skipped += 1
            continue
        raw = f.read_bytes()
        if b"\x00" in raw[:512]:          # 확장자에 없는 바이너리는 «내용»으로 가린다
            skipped += 1
            continue
        seen += 1
        bad = [b for b in raw if b < 9 or (13 < b < 32)]
        if bad:
            bad_files += 1
            FAIL.append("제어문자 %d개 — %s (0x%02x)"
                        % (len(bad), f.relative_to(ROOT), bad[0]))
    print("[1] 제어문자   검사 %d · 건너뜀 %d · 오염 %d" % (seen, skipped, bad_files))
    if not bad_files:
        OK.append("제어문자 0건 (검사 %d파일)" % seen)


# ─────────────────────────────────────────────────────────
# 2. 데이터 정합성 — 문서에 «정의된 것»만 쓰였나
# ─────────────────────────────────────────────────────────
ROUTES = {"SPACE", "ARCHAEO", "PALEO", "CONCEPT", "OTHER"}
CERT = {"정설", "추정", "논쟁", "신설", "최근", "미상"}


def audit_data():
    # 사실 카드
    facts = json.loads((HERE / "facts_base.json").read_text(encoding="utf-8"))["facts"]
    ids = [f["id"] for f in facts]
    chk(len(ids) == len(set(ids)), "사실카드 id 중복 없음")
    for f in facts:
        chk(f["route"] in ROUTES, "사실카드 %s 라우트 정의됨(%s)" % (f["id"], f["route"]))
        chk(f["certainty"] in CERT, "사실카드 %s 확실성 정의됨(%s)" % (f["id"], f["certainty"]))
        chk(bool(f.get("caution")), "사실카드 %s 주의사항 있음" % f["id"], "warn")
        chk(bool(f.get("basis")), "사실카드 %s 근거 있음" % f["id"], "warn")

    # 지식원
    kb = json.loads((HERE / "store/knowledge.json").read_text(encoding="utf-8"))
    arts = kb["articles"]
    aids = [a["id"] for a in arts]
    chk(len(aids) == len(set(aids)), "기사 id 중복 없음")
    for a in arts[:9999]:
        chk(a["route"] in ROUTES, "기사 %s 라우트 정의됨" % a["id"])
        chk(a["certainty"] in CERT, "기사 %s 확실성 정의됨" % a["id"])
    chk(kb["kept"] == len(arts), "knowledge.json 의 kept(%d)와 실제 건수(%d) 일치"
        % (kb["kept"], len(arts)))

    # 라우팅 평가셋
    seed, n_scored = _seed_rows()
    qs = [r["question"] for r in seed]
    chk(len(qs) == len(set(qs)), "평가셋 질문 중복 없음")
    for r in seed:
        chk(r["route"] in ROUTES, "평가셋 라우트 정의됨(%s)" % r["route"])
        chk(r["split"] in ("eval", "outscope", "example"),
            "평가셋 split 정의됨(%s)" % r["split"])
    # ★eval 에 OTHER 가 섞이면 «퍼실 구조»와 달라진다 — 의도한 것인지 확인
    ev_other = [r for r in seed if r["split"] == "eval" and r["route"] == "OTHER"]
    chk(not ev_other, "eval 에 OTHER 없음 (퍼실 구조와 같게 — outscope 로 분리)")

    # 검색 평가셋 — ★참조하는 기사 id 가 «실재»하는가
    es = list(csv.DictReader(io.open(HERE / "eval_search.csv", encoding="utf-8")))
    aset = set(aids)
    for r in es:
        for k in ("must_ids", "must_not_ids"):
            for x in (r[k] or "").split(";"):
                if x:
                    chk(x in aset, "검색평가셋 %s 의 %s 가 지식원에 실재" % (r["query"][:14], x))
    print("[2] 데이터     사실카드 %d · 기사 %d · 라우팅(채점) %d · 검색 %d"
          % (len(facts), len(arts), n_scored, len(es)))


# ─────────────────────────────────────────────────────────
# 3. 도구가 «실제로» 도는가 — import 만 보지 않는다
# ─────────────────────────────────────────────────────────
def audit_tools():
    import tools_desk as T
    chk(len(T.TOOLS) == 5, "도구 5개 등록됨(%d)" % len(T.TOOLS))
    for name, fn in T.TOOLS.items():
        chk(bool(fn.__doc__), "도구 %s 설명문 있음" % name)
        chk("Args:" in (fn.__doc__ or ""), "도구 %s 인자 설명 있음" % name, "warn")
    # 실제 호출
    r = T.get_fact("광년")
    chk(r.get("found"), "get_fact('광년') 이 찾음")
    r = T.search_article("화석")
    chk(r["count"] > 0, "search_article('화석') 이 결과를 냄")
    r = T.get_term("적색편이")
    chk(r.get("found"), "get_term('적색편이') 가 찾음")
    r = T.list_recent("PALEO")
    chk(r["count"] > 0, "list_recent('PALEO') 가 결과를 냄")
    r = T.get_article("A0002")
    chk(r.get("found"), "get_article('A0002') 가 찾음")
    print("[3] 도구       5개 전부 호출 성공")


# ─────────────────────────────────────────────────────────
# 4. ★문서와 실제가 «어긋나지» 않는가 — 어제 README §8 의 실수
# ─────────────────────────────────────────────────────────
def audit_docs():
    prog = (ROOT / "01_진행상황.md").read_text(encoding="utf-8")
    facts = json.loads((HERE / "facts_base.json").read_text(encoding="utf-8"))["facts"]
    kb = json.loads((HERE / "store/knowledge.json").read_text(encoding="utf-8"))
    seed, n_scored = _seed_rows()

    pairs = [("기사", len(kb["articles"]), r"지식원 \(기사\) \| \*\*(\d+)건"),
             ("사실카드", len(facts), r"기준 사실 카드 \| \*\*(\d+)장"),
             ("라우팅평가셋", n_scored, r"라우팅 평가셋 \| (\d+)건")]
    for label, actual, pat in pairs:
        m = re.search(pat, prog)
        if not m:
            WARN.append("진행상황.md 에서 %s 수치를 못 찾음 (패턴 변경?)" % label)
            continue
        chk(int(m.group(1)) == actual,
            "진행상황.md %s 수치 일치 (문서 %s · 실제 %d)" % (label, m.group(1), actual))

    # 파일 목록이 실제와 맞나
    listed = re.findall(r"^\s*[├└]── (\S+)", prog, re.M)
    for name in listed:
        if name.endswith("/"):
            continue
        exists = (ROOT / name).exists() or (HERE / name).exists() \
            or (HERE / "store" / name).exists()
        chk(exists, "진행상황.md 에 적힌 %s 가 실재" % name)
    # ★플레이스홀더가 «남아 있으면» 실패로 잡는다.
    #   어제 README §8 이 실제와 어긋난 채로 커밋됐다. 사람 눈으로는 빠진다.
    for name in ("README.md", "REPORT.md", "01_진행상황.md"):
        f = ROOT / name
        if not f.exists():
            WARN.append("%s 가 아직 없다" % name)
            continue
        txt = f.read_text(encoding="utf-8")
        holes = re.findall(r"__[A-Z0-9_]+__", txt)
        chk(not holes, "%s 에 채우지 않은 자리표시 없음 %s"
            % (name, sorted(set(holes)) if holes else ""))

    # ★README·REPORT 의 «주요 수치»가 실제 측정과 맞는가
    gold_n = len(json.loads((HERE / "golden.json").read_text(encoding="utf-8"))["cases"])
    n_example = len([r for r in seed if r["split"] == "example"])
    for name, pat, actual in (
            ("REPORT.md", r"지식원 기사 (\d+)건", len(kb["articles"])),
            ("REPORT.md", r"기준 사실 카드 (\d+)장", len(facts)),
            ("REPORT.md", r"라우팅 평가셋 (\d+)건", n_scored),
            ("REPORT.md", r"답변 정답셋 (\d+)건", gold_n),
            # ★README 도 «실제로» 본다 — 여기가 None 이라 검사가 안 돌았다
            ("README.md", r"사실 카드 (\d+)장", len(facts)),
            ("README.md", r"기사 (\d+)건", len(kb["articles"])),
            ("README.md", r"정답셋 \*\*(\d+)건\*\*", gold_n),
            ("README.md", r"`example` (\d+)", n_example)):
        f = ROOT / name
        if not f.exists() or actual is None:
            continue
        m = re.search(pat, f.read_text(encoding="utf-8"))
        if m:
            chk(int(m.group(1)) == actual,
                "%s 의 수치 일치 (문서 %s · 실제 %d)" % (name, m.group(1), actual))

    # ★문서가 «없는 파일»을 가리키지 않는가
    #   30_answer.py 를 agent.py 로 갈아 놓고 README 는 옛 이름을 가리키고 있었다.
    for name in ("README.md", "REPORT.md"):
        f = ROOT / name
        if not f.exists():
            continue
        for mentioned in set(re.findall(r"`(desk/[\w./-]+\.\w+)`",
                                        f.read_text(encoding="utf-8"))):
            chk((ROOT / mentioned).exists(),
                "%s 가 가리키는 %s 가 실재" % (name, mentioned))

    print("[4] 문서       진행상황·README·REPORT 의 수치·자리표시 대조")


# ─────────────────────────────────────────────────────────
# 5. ★골든셋 + 채점기 + 가드레일 — «다른 검사기»를 여기서 부른다
# ─────────────────────────────────────────────────────────
ACTIONS = {"ANSWER", "ASK", "REFUSE", "ESCALATE"}


def audit_golden():
    import tools_desk
    gold = json.loads((HERE / "golden.json").read_text(encoding="utf-8"))["cases"]
    ids = [c["id"] for c in gold]
    chk(len(ids) == len(set(ids)), "골든셋 id 중복 없음")
    for c in gold:
        chk(c["action"] in ACTIONS, "%s action 정의됨(%s)" % (c["id"], c["action"]))
        chk(c["route"] in ROUTES, "%s route 정의됨" % c["id"])
        chk(bool(c.get("reference")), "%s 모범 답안 있음" % c["id"])
        chk(bool(c.get("why")), "%s 왜 이 문항인지 적혀 있음" % c["id"], "warn")
        # ★tool_args 의 도구가 «실재»하고 «tools 와 일치»하나
        ta = c.get("tool_args") or {}
        for t in ta:
            chk(t in tools_desk.TOOLS, "%s tool_args 의 %s 가 실재" % (c["id"], t))
        chk(set(ta) == set(c.get("tools", [])),
            "%s tools 와 tool_args 가 «같은 도구»를 가리킴" % c["id"])
        # ★must 가 모범 답안에 «실제로» 있나 — 없으면 도달 불가 문항이다
        #   ⚠ must 항목은 «문자열» 또는 «동의어 목록»이다(요건: 표현이 아니라 사실).
        #     채점기를 고치고 여기를 «안 고쳐» 한 번 터졌다.
        #     한 곳을 고치면 «같은 가정을 한 코드»가 또 어디 있나를 세야 한다.
        import score_desk
        ref = score_desk.norm(c["reference"])
        for m in c.get("must", []):
            alts = m if isinstance(m, list) else [m]
            chk(any(score_desk.norm(a) in ref for a in alts),
                '%s must "%s" 가 모범 답안에 있음' % (c["id"], "|".join(alts)))
        for f in c.get("forbid", []):
            alts = f if isinstance(f, list) else [f]
            chk(not any(score_desk.norm(a) in ref for a in alts),
                '%s forbid "%s" 가 모범 답안에 «없음»' % (c["id"], "|".join(alts)))
    print("[5] 골든셋     %d건 · action·tool_args·must/forbid 정합" % len(gold))


def audit_selfcheck():
    """★채점기·가드레일의 «자기 검증»을 여기서도 돌린다 — 빠뜨리지 않으려고."""
    import contextlib
    import score_desk
    import guard_desk
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc1 = score_desk.self_check()
    chk(rc1 == 0, "★채점기 자기검증 통과 (모범답안이 실제 판정 경로를 지난다)")
    buf2 = io.StringIO()
    with contextlib.redirect_stdout(buf2):
        rc2 = guard_desk.audit()
    chk(rc2 == 0, "★가드레일 두 축 통과 (오탐 0 · 재현율 100%)")
    if rc1 or rc2:
        FAIL.append("   ↳ 자세한 내용: python score_desk.py --self / python guard_desk.py --audit")
    print("[6] 자기검증   채점기 %s · 가드레일 %s"
          % ("OK" if rc1 == 0 else "★실패", "OK" if rc2 == 0 else "★실패"))


def audit_evalset_agreement():
    """★두 평가셋이 «같은 말»을 하는가 — 규칙 라우터로 대조한다.

    실측: 같은 주제가 두 곳에서 «다른 라우트»를 가리키고 있었다.
      03_평가셋_씨앗.csv  「피라미드는 외계인이 지었다던데」 → OTHER
      golden.json  G10   「피라미드는 외계인이 지었나요」   → ARCHAEO
    policy 안에서도 모순이었다(§6은 외계인설을 OTHER 로, §3은 근거 제시로).
    ⇒ 눈으로는 «또» 놓친다. 그래서 검사로 만든다.
    """
    import importlib.util as _u
    sp = _u.spec_from_file_location("_r", HERE / "20_router.py")
    rt = _u.module_from_spec(sp)
    argv, sys.argv = sys.argv, ["x"]
    sp.loader.exec_module(rt)
    sys.argv = argv

    gold = json.loads((HERE / "golden.json").read_text(encoding="utf-8"))["cases"]
    bad = 0
    for c in gold:
        got, _, _ = rt.rule_classify(c["question"])
        # ★규칙이 틀릴 수도 있으므로 «경고»다. 다만 OTHER 와 비-OTHER 가
        #   엇갈리는 것은 «경계 정의»가 어긋난 것이라 실패로 본다.
        if (got == "OTHER") != (c["route"] == "OTHER"):
            FAIL.append("골든셋 %s: policy 경계와 어긋남 (규칙 %s ↔ 골든 %s) — %s"
                        % (c["id"], got, c["route"], c["question"][:24]))
            bad += 1
        elif got != c["route"]:
            WARN.append("골든셋 %s: 규칙 %s ↔ 골든 %s (규칙의 한계일 수 있음)"
                        % (c["id"], got, c["route"]))
    print("[8] 평가셋 정합  골든셋 %d건을 규칙 라우터로 대조 · 경계 불일치 %d" % (len(gold), bad))


def audit_consistency():
    """★policy 와 «코드»가 같은 말을 하나 — 어제 README §8 이 어긋났던 자리."""
    pol = (ROOT / "01_policy_초안.md").read_text(encoding="utf-8")
    router = (HERE / "20_router.py").read_text(encoding="utf-8")
    # CONCEPT 경계 — policy 가 「대상이 있나」로 가르는데 코드도 그런가
    chk("대상이 있나" in pol, "policy 에 CONCEPT 경계 기준이 있음")
    chk('hit["CONCEPT"] = 0' in router,
        "★라우터가 policy 의 「대상이 있으면 CONCEPT 아님」을 구현함")
    chk("«대상이 없이»" in router,
        "★LLM 지침이 policy 와 «같은 말»을 함 (§H-4 — 규칙 고치면 예시도)")
    # 확실성 등급 이름이 세 곳에서 «같은가»
    guard = (HERE / "guard_desk.py").read_text(encoding="utf-8")
    facts = json.loads((HERE / "facts_base.json").read_text(encoding="utf-8"))["facts"]
    used_cert = {f["certainty"] for f in facts}
    for c in used_cert:
        chk(c in pol, "확실성 «%s» 가 policy 에 정의됨" % c)
    chk("신설" in guard and "논쟁" in guard,
        "가드레일이 policy 의 확실성 등급 이름을 그대로 씀")
    print("[7] 일관성     policy ↔ 라우터 ↔ 가드레일 이 «같은 말»을 하는가")


# ─────────────────────────────────────────────────────────
# 9. ★프롬프트 오염 — 지침 예시가 «평가셋 문항»이면 점수가 부풀려진다
# ─────────────────────────────────────────────────────────
def audit_prompt_leak():
    """★퍼실 지시 「평가셋을 프롬프트에 절대 넣지 마세요」를 «기계»가 지킨다.

    1차에는 GUIDE_V1 의 예시 8개가 전부 평가셋 문항이었다 —
    골든셋 18건 중 2건, 라우팅 55건 중 6건이 «글자까지» 같았다.
    적어 두는 것으로는 안 막혔다. 그래서 검사로 만든다.

    ⚠ GUIDE_V1 은 «일부러» 남긴 오염본이다(전후 비교용) — 검사에서 뺀다.
    """
    import ast
    rows = list(csv.DictReader(io.open(ROOT / "03_평가셋_씨앗.csv", encoding="utf-8")))
    scored = {_nq(r["question"]) for r in rows if r["split"] in ("eval", "outscope")}
    examples = {_nq(r["question"]) for r in rows if r["split"] == "example"}
    gold = json.loads((HERE / "golden.json").read_text(encoding="utf-8"))["cases"]
    scored |= {_nq(c["question"]) for c in gold}

    EXEMPT = {"GUIDE_V1", "PICK_GUIDE_V1"}          # 비교용으로 남긴 오염본
    leaks = unreg = checked = 0
    for fn in ("20_router.py", "agent.py"):
        tree = ast.parse((HERE / fn).read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            name = getattr(node.targets[0], "id", "")
            if not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, str):
                continue
            if not any(k in name for k in ("GUIDE", "RULES", "PROMPT")):
                continue
            if name in EXEMPT:
                continue
            checked += 1
            for ex in re.findall("「([^」]+)」", node.value.value):
                n = _nq(ex)
                if len(n) < 6 or not re.search(
                        "(나요|인가요|습니까|는가|뭔가요|까요)$", n):
                    continue
                if any(n == s or n in s or s in n for s in scored):
                    FAIL.append("%s:%s 예시가 «채점 문항»과 겹침 — 「%s」" % (fn, name, ex))
                    leaks += 1
                elif n not in examples:
                    WARN.append("%s:%s 예시가 평가셋에 등록 안 됨 — 「%s」" % (fn, name, ex))
                    unreg += 1
    chk(leaks == 0, "★지침 %d개의 예시가 채점 문항과 겹치지 않음" % checked)
    print("[9] 프롬프트   지침 %d개 검사 · 오염 %d · 미등록 %d (GUIDE_V1 은 비교용이라 제외)"
          % (checked, leaks, unreg))


if __name__ == "__main__":
    print("=== 산출물 감사 ===")
    audit_control_chars()
    audit_data()
    audit_tools()
    audit_docs()
    audit_golden()
    audit_selfcheck()
    audit_evalset_agreement()
    audit_consistency()
    audit_prompt_leak()
    print()
    print("══ 결과 ══")
    print("   통과 %d · 경고 %d · ★실패 %d" % (len(OK), len(WARN), len(FAIL)))
    if WARN:
        print()
        print("[경고]")
        for w in WARN[:12]:
            print("   ⚠ %s" % w)
        if len(WARN) > 12:
            print("   … 외 %d건" % (len(WARN) - 12))
    if FAIL:
        print()
        print("[★실패 — 고쳐야 한다]")
        for f in FAIL:
            print("   ⛔ %s" % f)
        sys.exit(1)
    print()
    print("   ✅ 실패 없음")
